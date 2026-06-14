"""Use case `abrir_os_via_orcamento` — T-OS-041 (Fase 5).

Cobre AC-OS-001-1 a AC-OS-001-8 (PRD docs/dominios/operacao/modulos/os/prd.md):

- AC-OS-001-1: cria OS RASCUNHO + N AtividadeDaOS PENDENTE + evento `os_aberta`.
- AC-OS-001-2: orcamento sem itens -> 400 OrcamentoSemItensCarrinho.
- AC-OS-001-3: Idempotency-Key replay -> mesma OS (delegado ao caller / plug
  M2 `infrastructure/idempotencia/`; este use case eh puro).
- AC-OS-001-4: cross-tenant -> 422 OrcamentoCrossTenant (validado no consumer
  via tenant_context; INV-TENANT-001).
- AC-OS-001-5 (INV-OS-EQP-001): equipamento BAIXADO/DESCARTADO -> 422
  EquipamentoBaixadoEmOS (consumer pre-valida via query externa).
- AC-OS-001-6 (INV-OS-ANON-001): bloqueio de anonimizacao quando ha OS aberta
  (saga em consumer Cliente.Anonimizado, nao aqui).
- AC-OS-001-7 (P-OS-R2 / INV-OS-ANAL-001): analise_critica_id NULL -> 412
  OrcamentoSemAnaliseCritica.
- AC-OS-001-8 (P-OS-R4): OS de bancada exige equipamento_recebimento_id;
  ausente -> 412 EquipamentoSemRecebimentoRegistrado.

Camada APPLICATION pura: recebe `OSRepository` Protocol via DI. NUNCA importa
Django / PG. Consumer (Fase 4 placeholder) eh quem orquestra:
 1. Carrega payload do envelope `Orcamento.Aprovado`.
 2. Faz queries externas (equipamento estado; tipo_atividade_config p/ flag
    executa_em_campo de cada item).
 3. Monta `AbrirOSInput` e chama `abrir_os_via_orcamento(...)`.
 4. Em `transaction.atomic` chama `audit/event_helpers.publicar_evento(
    acao='OS.Aberta', ...)` pra atravessar o bus.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4

from src.domain.operacao.os.entities import (
    AtividadeSnapshot,
    EventoDeOSSnapshot,
    OSSnapshot,
)
from src.domain.operacao.os.repository import OSRepository
from src.domain.operacao.os.value_objects import (
    EstadoAtividade,
    EstadoOS,
    TipoAtividade,
    TipoEventoDeOS,
)

# =============================================================
# DTOs do use case
# =============================================================


@dataclass(frozen=True, slots=True)
class ItemOrcamento:
    """Item do orcamento aprovado (1 -> 1 atividade ou 1 item comercial).

    Quando `equipamento_id` for None o item nao corresponde a uma atividade
    tecnica — vira `ItemComercialOSSnapshot` (D-OSME-3). Quando for UUID,
    vira `AtividadeSnapshot` com aquele equipamento (AC-OSME-002-2).
    """

    tipo: TipoAtividade
    sequencia: int
    valor_unitario: Decimal
    requer_recebimento: bool
    """True quando o TipoAtividadeConfig do tenant tem `executa_em_campo=false`
    (i.e., OS de bancada — AC-OS-001-8 exige `equipamento_recebimento_id`)."""
    equipamento_id: UUID | None = None
    """None => item comercial (D-OSME-3); UUID => atividade tecnica daquele equipamento."""


@dataclass(frozen=True, slots=True)
class AbrirOSInput:
    """Entrada do use case — payload normalizado pelo consumer."""

    orcamento_id: UUID
    tenant_id: UUID
    cliente_id: UUID
    cliente_referencia_hash: str
    cliente_key_id: str
    equipamento_id: UUID
    equipamento_recebimento_id: UUID | None
    analise_critica_id: UUID | None
    analise_critica_snapshot_hash: str
    regra_decisao_acordada: str
    valor_total: Decimal
    itens: tuple[ItemOrcamento, ...]
    correlation_id: UUID
    abertura_at: datetime
    criada_por_user_id: UUID | None


@dataclass(frozen=True, slots=True)
class AtividadePlanejada:
    atividade_id: UUID
    tipo: str
    sequencia: int


@dataclass(frozen=True, slots=True)
class AbrirOSResultado:
    os_id: UUID
    numero_os: int
    atividades_planejadas: tuple[AtividadePlanejada, ...]
    correlation_id: UUID


# =============================================================
# Erros de regra
# =============================================================


class ErroAbrirOS(Exception):
    """Falha de regra ao abrir OS. Consumer mapeia codigo -> HTTP status."""

    def __init__(self, codigo: str, http_status: int, detalhe: str = "") -> None:
        super().__init__(f"{codigo}: {detalhe}" if detalhe else codigo)
        self.codigo = codigo
        self.http_status = http_status
        self.detalhe = detalhe


# =============================================================
# Use case
# =============================================================


def abrir_os_via_orcamento(
    *,
    payload: AbrirOSInput,
    repository: OSRepository,
) -> AbrirOSResultado:
    """Abre OS RASCUNHO + N AtividadeDaOS PENDENTE a partir de orcamento aprovado.

    Caller envolve em `transaction.atomic` + chama `publicar_evento` do helper
    de audit/outbox para atravessar o bus.

    Returns:
        AbrirOSResultado com `os_id`, `numero_os`, `atividades_planejadas`.

    Raises:
        ErroAbrirOS: regra violada. Atributos `.codigo` + `.http_status`.
    """
    # ---- Validacoes binarias ----
    if not payload.itens:
        # AC-OS-001-2
        raise ErroAbrirOS("OrcamentoSemItensCarrinho", 400)

    if payload.analise_critica_id is None:
        # AC-OS-001-7 (P-OS-R2 + INV-OS-ANAL-001)
        raise ErroAbrirOS("OrcamentoSemAnaliseCritica", 412)

    if (
        any(item.requer_recebimento for item in payload.itens)
        and payload.equipamento_recebimento_id is None
    ):
        # AC-OS-001-8 (P-OS-R4)
        raise ErroAbrirOS("EquipamentoSemRecebimentoRegistrado", 412)

    # ---- Construcao do agregado ----
    numero_os = repository.proximo_numero_os()
    os_id = uuid4()

    os_snapshot = OSSnapshot(
        id=os_id,
        tenant_id=payload.tenant_id,
        numero_os=numero_os,
        cliente_id=payload.cliente_id,
        cliente_referencia_hash=payload.cliente_referencia_hash,
        cliente_key_id=payload.cliente_key_id,
        equipamento_id=payload.equipamento_id,
        equipamento_recebimento_id=payload.equipamento_recebimento_id,
        orcamento_origem_id=payload.orcamento_id,
        os_origem_id=None,
        sucessao_societaria_id=None,
        estado=EstadoOS.RASCUNHO,
        tipo_predominante="",
        nao_conformidade_global=False,
        valor_total=payload.valor_total,
        valor_total_atualizado=payload.valor_total,
        analise_critica_id=payload.analise_critica_id,
        analise_critica_snapshot_hash=payload.analise_critica_snapshot_hash,
        regra_decisao_acordada=payload.regra_decisao_acordada,
        criada_em=payload.abertura_at,
        atualizada_em=payload.abertura_at,
        criada_por_user_id=payload.criada_por_user_id,
    )
    repository.salvar_os(os_snapshot)

    planejadas: list[AtividadePlanejada] = []
    for item in payload.itens:
        atividade_id = uuid4()
        atividade_snapshot = AtividadeSnapshot(
            id=atividade_id,
            tenant_id=payload.tenant_id,
            os_id=os_id,
            tipo=item.tipo,
            sequencia=item.sequencia,
            estado=EstadoAtividade.PENDENTE,
            tecnico_executor_id=None,
            agendada_para=None,
            iniciada_em=None,
            concluida_em=None,
            valor_unitario_snapshot=item.valor_unitario,
            link_modulo_tecnico_id=None,
            geo_lat=None,
            geo_long=None,
            geo_municipio_hash="",
            # Desnormalizados via trigger BEFORE INSERT (INV-OS-CONC-001 / ADR-0082):
            equipamento_id=None,
            tipo_bloqueia_concorrencia=False,
        )
        repository.salvar_atividade(atividade_snapshot)
        planejadas.append(
            AtividadePlanejada(
                atividade_id=atividade_id,
                tipo=item.tipo.value,
                sequencia=item.sequencia,
            )
        )

    # ---- EventoDeOS timeline (timeline local — bus eh do caller) ----
    payload_evento: dict[str, object] = {
        "orcamento_id": str(payload.orcamento_id),
        "numero_os": numero_os,
        "atividades_planejadas": [
            {
                "atividade_id": str(p.atividade_id),
                "tipo": p.tipo,
                "sequencia": p.sequencia,
            }
            for p in planejadas
        ],
    }
    payload_canonico = json.dumps(payload_evento, sort_keys=True, ensure_ascii=False)
    # Integrity-check do payload do evento (ja sanitizado, sem PII cru). NAO eh
    # hash discriminante de PII; salt por tenant nao se aplica.
    payload_hash = hashlib.sha256(payload_canonico.encode("utf-8")).hexdigest()  # audit-pii-salt: skip -- payload_evento ja sanitizado sem PII cru; integrity hash do envelope
    repository.publicar_evento(
        EventoDeOSSnapshot(
            id=uuid4(),
            tenant_id=payload.tenant_id,
            os_id=os_id,
            atividade_id=None,
            tipo=TipoEventoDeOS.OS_ABERTA,
            payload_hash=payload_hash,
            payload_data=payload_evento,
            correlation_id=payload.correlation_id,
            actor_user_id=payload.criada_por_user_id,
            occurred_at=payload.abertura_at,
            criado_em=payload.abertura_at,
        )
    )

    return AbrirOSResultado(
        os_id=os_id,
        numero_os=numero_os,
        atividades_planejadas=tuple(planejadas),
        correlation_id=payload.correlation_id,
    )
