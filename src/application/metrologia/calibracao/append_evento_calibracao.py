"""Use case `append_evento_calibracao` — OBS-CAL-01 conserto P5 (ALTO).

Conserto causa-raiz do achado OBS-CAL-01 da 1a passada Familia 5 (2026-05-27):
> Trilha hash-chain WORM declarada mas NUNCA emitida (OBS-001). 23 tipos de
> evento na migration 0009 ficam letra morta; nenhum use case M4 chama
> EventoDeCalibracao.salvar_em_cadeia. Auditor CGCRE pede "quem aprovou
> Cal-2026/1234?" -> tabela vazia.

Use case PURO (ADR-0007 spec-as-source):
- Recebe Input frozen + EventoDeCalibracaoRepository Protocol.
- Sanitiza payload via `sanitizar_payload_evento_calibracao` (helper unico
  G2 dossie pre-M4 — INV-CAL-AUD-001).
- Deriva `actor_user_id_hash` server-side (ADR-0064 HashVersionado).
- Delega advisory lock + sequencia_local + hash-chain ao
  `repo.salvar_em_cadeia` (dentro do `transaction.atomic` do CALLER —
  rollback unificado com a operacao de negocio que disparou o evento).

Contrato com caller (view ou consumer):
- Caller DEVE estar dentro de `with transaction.atomic():` (mesmo bloco do
  use case de negocio que produziu o evento — ex: criar_calibracao,
  configurar_calibracao, aprovar_revisao, etc).
- Caller passa `finalidade` canonica pra rastreio CGCRE (ex: "recepcao",
  "configuracao", "aprovacao_revisao_1", ...).
- Caller obtem `tenant_id` e `actor_user_id` do contexto multitenant +
  auth — NUNCA aceita do body cliente (paralelo SEG-CAL-01 conserto).

Invariantes cobertas:
- OBS-001 / OBS-CAL-01: trilha hash-chain emitida em cada operacao critica.
- INV-CAL-AUD-001: payload sanitizado (sem PII cru, exceto hashes derivados).
- INV-CAL-AUD-002: ordem total por (tenant_id, calibracao_id) via advisory
  lock + trigger PG sequencia_local.
- INV-HMAC-001/002: evento_hash em formato canonico v<NN>$<base64>.
- ADR-0064: HMAC versionado VERSAO_HMAC_ATUAL rotacao anual.
- ADR-0065: advisory lock por calibracao + UPDATE-DELETE bloqueados trigger.

Nao-objetivos (NAO faz parte deste use case):
- Verificacao de cadeia (relpay determinístico ADR-0025) — use case separado.
- Re-derivacao de tenant_id/actor_user_id — caller obtem do contexto.
- Wrapping em transaction.atomic — caller envolve.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID, uuid4

from src.domain.metrologia.calibracao.entities import EventoDeCalibracaoSnapshot
from src.domain.metrologia.calibracao.repository import EventoDeCalibracaoRepository


@dataclass(frozen=True, slots=True)
class AppendEventoCalibracaoInput:
    """Payload para emitir 1 elo na trilha WORM (caller orquestra).

    `payload_raw` = dict cru da operacao de negocio (ex.: campos do snapshot
    persistido). Sera sanitizado antes do INSERT pelo helper unico
    `sanitizar_payload_evento_calibracao` (G2 dossie pre-M4 + INV-CAL-AUD-001).

    `finalidade` = string canonica pra rastreio CGCRE (>=5 chars). Catalogo
    sugerido (paralelo aos 23 TIPO_EVENTO_CALIBRACAO_CHOICES da migration
    0009): "recepcao", "configuracao", "leitura_registrada", "correcao_leitura",
    "incerteza_calculada", "conformidade_avaliada", "revisao_aprovada",
    "revisao_rejeitada", "segunda_conferencia_aprovada", "nc_aberta",
    "nc_resolvida", "calibracao_aprovada", "calibracao_rejeitada",
    "calibracao_cancelada", "subcontratada_para_lab", "recebida_do_lab",
    "ep_unacceptable_impacto", "condicoes_fora_override", "reclamacao_aberta",
    "reclamacao_respondida", "aceite_regra_decisao", "override_regra_decisao",
    "backup_executado".
    """

    tenant_id: UUID
    calibracao_id: UUID
    tipo: str  # uma das TIPO_EVENTO_CALIBRACAO_CHOICES (migration 0009)
    payload_raw: dict[str, object]
    finalidade: str  # canonica >=5 chars (rastreio CGCRE)
    actor_user_id: UUID
    occurred_at: datetime  # tz-aware
    correlation_id: UUID
    causation_id: UUID | None = None

    def __post_init__(self) -> None:
        if not self.tipo or self.tipo.strip() != self.tipo:
            raise ValueError(
                "append_evento_calibracao: tipo obrigatorio (uma das "
                "TIPO_EVENTO_CALIBRACAO_CHOICES da migration 0009)"
            )
        if not self.finalidade or len(self.finalidade) < 5:
            raise ValueError(
                "append_evento_calibracao: finalidade >=5 chars obrigatoria "
                "(rastreio CGCRE — INV-CAL-AUD-001)"
            )
        if self.occurred_at.tzinfo is None:
            raise ValueError(
                "append_evento_calibracao: occurred_at exige datetime tz-aware "
                "(INV-VIG-004)"
            )


@dataclass(frozen=True, slots=True)
class AppendEventoCalibracaoOutput:
    """Snapshot encadeado: sequencia_local + evento_hash populados."""

    snapshot: EventoDeCalibracaoSnapshot


def executar(
    inp: AppendEventoCalibracaoInput,
    repo: EventoDeCalibracaoRepository,
) -> AppendEventoCalibracaoOutput:
    """Emite 1 elo na trilha WORM da calibracao.

    Caller envolve em `transaction.atomic` (mesmo bloco do use case de
    negocio). Adapter aplica advisory lock por (tenant_id, calibracao_id),
    sanitiza payload, deriva actor_user_id_hash, calcula evento_hash
    encadeado, faz INSERT.
    """
    # Import local: helpers de infraestrutura. Importar no topo arrancaria
    # dependencia django pesada em pacote application (regra ADR-0007).
    from src.infrastructure.calibracao.lgpd import (
        derivar_hash_texto_canonicalizado,
        sanitizar_payload_evento_calibracao,
    )

    payload_sanitizado = sanitizar_payload_evento_calibracao(
        inp.payload_raw, finalidade=inp.finalidade
    )
    actor_hash = derivar_hash_texto_canonicalizado(
        texto=str(inp.actor_user_id), tenant_id=inp.tenant_id
    )

    snapshot_entrada = EventoDeCalibracaoSnapshot(
        id=uuid4(),
        tenant_id=inp.tenant_id,
        calibracao_id=inp.calibracao_id,
        tipo=inp.tipo,
        payload_sanitizado=payload_sanitizado,
        actor_user_id=inp.actor_user_id,
        actor_user_id_hash=actor_hash,
        occurred_at=inp.occurred_at,
        correlation_id=inp.correlation_id,
        causation_id=inp.causation_id,
        # Campos preenchidos pelo adapter dentro do advisory lock:
        sequencia_local=None,
        evento_anterior_hash="",
        evento_hash="",
    )
    snapshot_final = repo.salvar_em_cadeia(snapshot_entrada)
    return AppendEventoCalibracaoOutput(snapshot=snapshot_final)
