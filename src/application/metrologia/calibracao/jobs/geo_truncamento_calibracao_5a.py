"""Job `geo_truncamento_calibracao_5a` (T-CAL-120) — P-CAL-A8 (paralelo P-OS-A8).

LGPD art. 9o + anti-stalking pos-retencao 25a — apos 5 anos da
`Calibracao.criada_em` (em estado APROVADA), trunca coordenadas geo
exatas do `snapshot_equipamento_json` (se presentes), substituindo por
hash do municipio ou regiao. UUID/IDs canonicos sao preservados.

Funcao PURA — recebe lista de calibracoes aprovadas + agora. Retorna
lista de AcaoTruncarGeo (caller faz UPDATE imutavel via trigger PG
especifico).

Chaves geo no snapshot_equipamento_json (heuristica conservadora):
  - "latitude", "longitude", "lat", "long", "lng" — coordenada exata
  - "endereco_completo", "cep", "complemento" — endereco rastreavel
Outros campos preservados (codigo equipamento, modelo, num_serie etc).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from uuid import UUID

from src.domain.metrologia.calibracao.entities import CalibracaoSnapshot
from src.domain.metrologia.calibracao.enums import EstadoCalibracao

_PRAZO_TRUNCAMENTO_ANOS = 5
_CHAVES_GEO_EXATAS = frozenset(
    {
        "latitude",
        "longitude",
        "lat",
        "long",
        "lng",
        "endereco_completo",
        "cep",
        "complemento",
    }
)


@dataclass(frozen=True, slots=True)
class AcaoTruncarGeo:
    """Acao a executar: UPDATE snapshot_equipamento_json sem chaves geo."""

    calibracao_id: UUID
    tenant_id: UUID
    snapshot_equipamento_json_novo: dict[str, object]  # sem campos geo
    chaves_removidas: tuple[str, ...]
    correlation_id: UUID


def _truncar(snapshot_json: dict[str, object]) -> tuple[dict[str, object], list[str]]:
    """Retorna copia do snapshot SEM chaves geo + lista chaves removidas."""
    novo: dict[str, object] = {}
    removidas: list[str] = []
    for k, v in snapshot_json.items():
        if k.lower() in _CHAVES_GEO_EXATAS:
            removidas.append(k)
            continue
        novo[k] = v
    return novo, removidas


def executar(
    *,
    calibracoes_aprovadas: list[CalibracaoSnapshot],
    agora: datetime,
) -> list[AcaoTruncarGeo]:
    """Filtra calibracoes APROVADA com criada_em > 5a e snapshot geo presente.

    Args:
      calibracoes_aprovadas: snapshots filtrados pelo caller
        (status=APROVADA + criada_em <= agora - 5a).
      agora: timestamp (tz-aware).

    Returns:
      Lista de AcaoTruncarGeo (apenas quando ha chaves geo a remover).
    """
    if agora.tzinfo is None:
        raise ValueError(
            "geo_truncamento_calibracao_5a: agora exige datetime tz-aware "
            "(INV-VIG-004)"
        )

    corte = agora - timedelta(days=365 * _PRAZO_TRUNCAMENTO_ANOS)

    acoes: list[AcaoTruncarGeo] = []
    for snap in calibracoes_aprovadas:
        if snap.status != EstadoCalibracao.APROVADA:
            continue
        if snap.criada_em > corte:
            continue
        # T-SAN-PERFIL-050 (Sprint 4 ADR-0067 / R10 plan.md / AC-005-6):
        # Perfil A (acreditado RBC) NUNCA trunca geo — CGCRE pode pedir
        # coordenadas exatas em supervisao retroativa (NIT-DICLA-016 +
        # ISO 17025 cl. 8.4.2). Perfis B/C/D trunca normalmente. Snapshot
        # `perfil_no_evento` (cravado no momento da calibracao via trigger
        # BEFORE INSERT) e o canonico — preserva contexto temporal.
        # Fallback (perfil_no_evento ausente — pre-saneamento) = trunca
        # como antes (estado pre-ADR-0067 nao tinha A em producao).
        perfil_no_momento = getattr(snap, "perfil_no_evento", None)
        if perfil_no_momento == "A":
            continue  # AC-005-6 — A jamais trunca
        novo_json, removidas = _truncar(snap.snapshot_equipamento_json)
        if not removidas:
            continue  # nada a truncar
        acoes.append(
            AcaoTruncarGeo(
                calibracao_id=snap.id,
                tenant_id=snap.tenant_id,
                snapshot_equipamento_json_novo=novo_json,
                chaves_removidas=tuple(removidas),
                correlation_id=snap.correlation_id,
            )
        )
    return acoes
