"""Use case `abrir_os_via_orcamento` — T-OS-041 (Fase 5) + T-OSME-013 (Fatia 2).

Cobre AC-OS-001-1 a AC-OS-001-8 (PRD docs/dominios/operacao/modulos/os/prd.md)
e AC-OSME-002/006 (spec os-multi-equipamento §2):

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
- AC-OSME-002 (US-OSME-002): item com equipamento_id (proprio OU herdado do header
  legado) -> AtividadeSnapshot; item sem equipamento em nenhum dos dois ->
  ItemComercialOSSnapshot (D-OSME-3).
- AC-OSME-006-3: itens sem equipamento (proprio nem header) viram ItemComercialOS;
  itens com equipamento viram atividade tecnica (AC-006-3).

Camada APPLICATION pura: recebe `OSRepository` Protocol via DI. NUNCA importa
Django / PG. Consumer (Fase 4 placeholder) eh quem orquestra:
 1. Carrega payload do envelope `Orcamento.Aprovado`.
 2. Faz queries externas (equipamento estado; tipo_atividade_config p/ flag
    executa_em_campo de cada item).
 3. Monta `AbrirOSInput` e chama `abrir_os_via_orcamento(...)`.
 4. Em `transaction.atomic` chama `audit/event_helpers.publicar_evento(
    acao='OS.Aberta', ...)` pra atravessar o bus.

Decisao de design (T-OSME-013):
- Itens com equipamento_id proprio viram `AtividadeSnapshot` com aquele equipamento.
- Itens sem equipamento_id proprio herdam `payload.equipamento_id` (header legado v1)
  quando presente — viram `AtividadeSnapshot` com o equipamento do header.
- Itens sem equipamento proprio NEM header viram `ItemComercialOSSnapshot` (tipo OUTRO por default —
  o orcamento nao envia tipo comercial fino em Wave A; descricao_publica vem do tipo
  da atividade ou "Item comercial"). Esses itens sao persistidos via
  `repository.salvar_item_comercial(...)` e NAO aparecem em `atividades_planejadas`.
- `OSSnapshot.equipamento_id` fica NULL em OS multi-equipamento (D-OSME-2).
- Evento `os.aberta` (payload_data['atividades_planejadas']) inclui `equipamento_id`
  por atividade (string ou null) — TL-OSME-10 (v+1 aditivo). Itens comerciais vao
  em `itens_comerciais_count` (contagem, sem exposicao de dados comerciais no bus).
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
    ItemComercialOSSnapshot,
    OSSnapshot,
)
from src.domain.operacao.os.repository import OSRepository
from src.domain.operacao.os.value_objects import (
    EstadoAtividade,
    EstadoOS,
    TipoAtividade,
    TipoEventoDeOS,
    TipoItemComercial,
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
    equipamento_id: UUID | None
    """Header legado (fallback para itens sem equipamento proprio). None em OS multi-equip v2."""
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
    equipamento_id: UUID | None = None
    """Equipamento proprio da atividade (AC-OSME-002-2 / TL-OSME-10)."""


@dataclass(frozen=True, slots=True)
class AbrirOSResultado:
    os_id: UUID
    numero_os: int
    atividades_planejadas: tuple[AtividadePlanejada, ...]
    correlation_id: UUID
    itens_comerciais_count: int = 0
    """Quantidade de ItemComercialOS criados (D-OSME-3). Informativo."""


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
        # AC-OS-001-8 (P-OS-R4) — DEGENERACAO OS-level de INV-OSME-RCB-001 (ADR-0082).
        # Esta validacao é por OS (1 recebimento p/ a OS), válida enquanto a OS for
        # single-instrumento (cl. 7.4.3 — degenera: OS.equipamento_recebimento_id ≡ recebimento
        # da única atividade). O enforcement POR ATIVIDADE (recebimento NOT NULL por atividade +
        # `EquipamentoRecebimento.equipamento_id == AtividadeDaOS.equipamento_id` + NC parcial,
        # AC-007-2b/007-3) depende do seam de preenchimento = GATE-OSME-RECEBIMENTO-7.5: o produtor
        # `criar_recebimento` ainda não publica `atividade_id`, logo validar por atividade hoje
        # seria validar contra coluna vazia (parecer consultor-rbc 2026-06-14).
        raise ErroAbrirOS("EquipamentoSemRecebimentoRegistrado", 412)

    # ---- Construcao do agregado ----
    numero_os = repository.proximo_numero_os()
    os_id = uuid4()

    # Fallback header->item (contrato AbrirOSInput.equipamento_id): um item SEM
    # equipamento proprio herda o `payload.equipamento_id` do header (envelope v1
    # legado — 1 equipamento, N itens). Item COM equipamento proprio usa o seu
    # (envelope v2 multi-equipamento). Item sem equipamento em nenhum dos dois ->
    # ItemComercialOS (D-OSME-3 / AC-OSME-006-3). Esta regra mora no use case
    # (camada APPLICATION, spec-as-source) — o consumer apenas a espelha no
    # pre-check de equipamento baixado (INV-OS-EQP-001).
    def _equip_efetivo(item: ItemOrcamento) -> UUID | None:
        return (
            item.equipamento_id
            if item.equipamento_id is not None
            else payload.equipamento_id
        )

    # Determina se a OS e multi-equipamento. OS.equipamento_id fica NULL quando ha
    # >1 equipamento distinto entre as atividades (D-OSME-2); em single-equip
    # mantemos o equipamento no header da OS para compatibilidade.
    equip_ids_das_atividades = {
        _equip_efetivo(item)
        for item in payload.itens
        if _equip_efetivo(item) is not None
    }
    os_equipamento_id: UUID | None
    if len(equip_ids_das_atividades) > 1:
        # Multi-equipamento: OS.equipamento_id = NULL (D-OSME-2).
        os_equipamento_id = None
    elif len(equip_ids_das_atividades) == 1:
        # Single-equip via atividade: mantemos compatibilidade (OS.equipamento_id = equip).
        os_equipamento_id = next(iter(equip_ids_das_atividades))
    else:
        # Todos itens sao comerciais (sem equipamento proprio nem header).
        os_equipamento_id = None

    os_snapshot = OSSnapshot(
        id=os_id,
        tenant_id=payload.tenant_id,
        numero_os=numero_os,
        cliente_id=payload.cliente_id,
        cliente_referencia_hash=payload.cliente_referencia_hash,
        cliente_key_id=payload.cliente_key_id,
        equipamento_id=os_equipamento_id,
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
    itens_comerciais_criados = 0

    for item in payload.itens:
        equip_item = _equip_efetivo(item)
        if equip_item is not None:
            # AC-OSME-002-2: item com equipamento (proprio ou herdado do header) ->
            # atividade tecnica com equipamento proprio.
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
                # equipamento_id EFETIVO da atividade (proprio do item ou herdado do
                # header legado — ADR-0082 / INV-OS-ATIV-002). O adapter
                # `repositories.salvar_atividade` inclui este valor no INSERT (quando
                # != None); o trigger BEFORE INSERT usa COALESCE(NEW.equipamento_id,
                # OS.equipamento_id) — preserva o valor e so cai no fallback da OS
                # quando a atividade vem sem equipamento (OS single-equip legada). Em OS
                # multi-equip OS.equipamento_id e NULL, por isso o item traz o seu.
                equipamento_id=equip_item,
                tipo_bloqueia_concorrencia=False,
            )
            repository.salvar_atividade(atividade_snapshot)
            planejadas.append(
                AtividadePlanejada(
                    atividade_id=atividade_id,
                    tipo=item.tipo.value,
                    sequencia=item.sequencia,
                    equipamento_id=equip_item,
                )
            )
        else:
            # AC-OSME-006-3: item sem equipamento -> ItemComercialOS (D-OSME-3).
            # Tipo default OUTRO (orcamento Wave A nao envia tipo comercial fino).
            # descricao_publica derivada do tipo da atividade (ex: "Calibracao").
            item_comercial_id = uuid4()
            descricao = item.tipo.value.replace("_", " ").capitalize() if item.tipo else "Item comercial"
            item_comercial = ItemComercialOSSnapshot(
                id=item_comercial_id,
                tenant_id=payload.tenant_id,
                os_id=os_id,
                tipo=TipoItemComercial.OUTRO,
                descricao_publica=descricao,
                valor=item.valor_unitario,
                quantidade=1,
                origem_item_id=None,  # rastreio futuro quando modulo orcamentos existir
            )
            repository.salvar_item_comercial(item_comercial)
            itens_comerciais_criados += 1

    # ---- EventoDeOS timeline (timeline local — bus eh do caller) ----
    # TL-OSME-10: payload v+1 aditivo — cada atividade planejada ganha equipamento_id.
    # Itens comerciais vao apenas como contagem (sem exposicao de dados comerciais no bus).
    payload_evento: dict[str, object] = {
        "orcamento_id": str(payload.orcamento_id),
        "numero_os": numero_os,
        "atividades_planejadas": [
            {
                "atividade_id": str(p.atividade_id),
                "tipo": p.tipo,
                "sequencia": p.sequencia,
                "equipamento_id": str(p.equipamento_id) if p.equipamento_id else None,
            }
            for p in planejadas
        ],
        "itens_comerciais_count": itens_comerciais_criados,
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
        itens_comerciais_count=itens_comerciais_criados,
    )
