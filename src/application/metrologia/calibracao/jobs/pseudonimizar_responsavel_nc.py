"""Job `nc-responsavel-pseudonimizacao` (T-CAL-117) — P-CAL-A2 advogado.

LGPD art. 16 + anti-stalking pos-retencao 25a:
  NaoConformidade.responsavel_acao_user_id eh "zona quente" UUID cru.
  Apos 90 dias da ACAO_EXECUTADA, zera o UUID cru (mantem
  responsavel_acao_user_id_hash — HashVersionado eh suficiente pra
  auditoria CGCRE; UUID cru permitiria stalking).

Funcao PURA — recebe snapshots de NC com responsavel_acao_user_id NOT NULL
+ `agora`. Retorna lista de NCs a pseudonimizar (caller adapter Django
faz UPDATE `responsavel_acao_user_id = NULL`).

Criterio (P-CAL-A2):
  - estado >= ACAO_EXECUTADA
  - responsavel_acao_user_id IS NOT NULL
  - acao_executada_em + 90 dias < agora

Idempotente: chamado 2x no mesmo dia retorna mesma lista (UUID ja
zerado nao aparece).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from uuid import UUID

from src.domain.metrologia.calibracao.entities import NaoConformidadeSnapshot
from src.domain.metrologia.calibracao.enums import EstadoNaoConformidade

# Estados pos-ACAO_EXECUTADA (inclusive) — todos elegiveis pra pseudonimizar
_ESTADOS_ELEGIVEIS: frozenset[EstadoNaoConformidade] = frozenset(
    {
        EstadoNaoConformidade.ACAO_EXECUTADA,
        EstadoNaoConformidade.EFICACIA_VERIFICADA,
        EstadoNaoConformidade.FECHADA,
        # REABERTA volta a CONTIDA — exclusive
    }
)

_PRAZO_PSEUDONIMIZACAO_DIAS = 90


@dataclass(frozen=True, slots=True)
class AcaoPseudonimizar:
    """Acao a executar — caller emite UPDATE SET responsavel_acao_user_id = NULL."""

    nc_id: UUID
    tenant_id: UUID
    responsavel_acao_user_id_anterior: UUID  # pra logging WORM
    responsavel_acao_user_id_hash: str  # confirma que hash existe (P-CAL-A2)
    acao_executada_em: datetime
    estado_atual: EstadoNaoConformidade
    dias_desde_execucao: int


def executar(
    *,
    ncs_com_responsavel: list[NaoConformidadeSnapshot],
    agora: datetime,
) -> list[AcaoPseudonimizar]:
    """Filtra NCs elegiveis pra pseudonimizacao do responsavel_acao_user_id.

    Args:
      ncs_com_responsavel: snapshots ja filtrados pelo caller
        (responsavel_acao_user_id IS NOT NULL).
      agora: timestamp atual (tz-aware).

    Returns:
      Lista de AcaoPseudonimizar (pode ser vazia).
    """
    if agora.tzinfo is None:
        raise ValueError(
            "pseudonimizar_responsavel_nc: agora exige datetime tz-aware "
            "(INV-VIG-004)"
        )

    corte = agora - timedelta(days=_PRAZO_PSEUDONIMIZACAO_DIAS)
    acoes: list[AcaoPseudonimizar] = []
    for snapshot in ncs_com_responsavel:
        if snapshot.responsavel_acao_user_id is None:
            continue
        # P-CAL-A2: hash SEMPRE presente; se vazio, configuracao incompleta
        # — caller deveria checar; aqui apenas defendemos.
        if not snapshot.responsavel_acao_user_id_hash:
            continue
        if snapshot.estado not in _ESTADOS_ELEGIVEIS:
            continue
        if snapshot.acao_executada_em is None:
            continue
        if snapshot.acao_executada_em > corte:
            # Ainda dentro do prazo de 90d
            continue
        dias = (agora - snapshot.acao_executada_em).days
        acoes.append(
            AcaoPseudonimizar(
                nc_id=snapshot.id,
                tenant_id=snapshot.tenant_id,
                responsavel_acao_user_id_anterior=snapshot.responsavel_acao_user_id,
                responsavel_acao_user_id_hash=snapshot.responsavel_acao_user_id_hash,
                acao_executada_em=snapshot.acao_executada_em,
                estado_atual=snapshot.estado,
                dias_desde_execucao=dias,
            )
        )
    return acoes
