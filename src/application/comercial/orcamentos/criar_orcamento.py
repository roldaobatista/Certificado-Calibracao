"""Use case `criar_orcamento` — T-ORC-030 (Fatia 2 / Onda 2a).

Cria o orcamento em RASCUNHO + a `VersaoOrcamento` V1 corrente (snapshot={}),
reservando o numero via `SerieDocumento` (regime BURACOS_ACEITOS — D-FATIA2-A).

Pre-condicao de negocio (D-ORC-4): o cliente deve existir, estar ativo (nao
soft-deleted) e nao-bloqueado. A checagem e injetada via `verificar_cliente_fn`
(a infra le o model `Cliente` cross-modulo sob RLS) — o dominio permanece puro.

Numeracao (D-ORC-18 / D-FATIA2-A/B):
  - Provisionamento LAZY (D-FATIA2-B): a serie de orcamento do tenant pode nao
    existir (Wave A nao faz onboarding de series) — obtem-ou-cria idempotente.
  - Regime DERIVADO do tipo (ADR-0080): `TipoDocumento.ORCAMENTO` ->
    `BURACOS_ACEITOS` (D-FATIA2-A). Logo NAO ha `confirmar_numero` (reserva sem
    TTL; `reserva_id is None`). Buracos so ocorrem em rollback do atomic da
    criacao — na pratica a numeracao e sequencial limpa.

Caller (view) abre `transaction.atomic`; este use case NAO gerencia transacao.

Refs: spec §4; D-ORC-3/4/18; D-FATIA2-A/B; AC-ORC-001.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID, uuid4

from src.domain.comercial.orcamentos.entities import Orcamento, VersaoOrcamento
from src.domain.comercial.orcamentos.enums import EstadoOrcamento
from src.domain.comercial.orcamentos.erros import ClienteBloqueado
from src.domain.comercial.orcamentos.repository import OrcamentoRepository
from src.domain.comercial.orcamentos.value_objects import CondicoesPagamento
from src.domain.configuracoes_sistema.entities import SerieDocumento
from src.domain.configuracoes_sistema.enums import TipoDocumento
from src.domain.configuracoes_sistema.repository import SerieDocumentoRepository
from src.domain.shared.value_objects import Dinheiro, JanelaVigencia

_PREFIXO_SERIE_ORCAMENTO = "ORC"


@dataclass(frozen=True, slots=True)
class StatusCliente:
    """Snapshot da elegibilidade de um cliente para receber orcamento (D-ORC-4)."""

    existe: bool
    ativo: bool  # nao soft-deleted
    bloqueado: bool


VerificarClienteFn = Callable[[UUID, UUID], StatusCliente]
"""Callable(cliente_id, tenant_id) -> StatusCliente.

Implementacao na infra (view) le o model `Cliente` + property `bloqueado` sob RLS.
"""


@dataclass(frozen=True, slots=True)
class CriarOrcamentoInput:
    """Entradas do `criar_orcamento` (PII derivada server-side na view — D-ORC-4)."""

    tenant_id: UUID
    criado_por: UUID
    cliente_id: UUID
    cliente_referencia_hash: str  # HMAC server-side (ADR-0032)
    cliente_key_id: str
    condicoes_pagamento: CondicoesPagamento
    validade: JanelaVigencia
    agora: datetime  # tz-aware
    moeda: str = "BRL"
    template_id: UUID | None = None
    tabela_preco_id: UUID | None = None
    observacoes: str | None = None
    responsavel_id: UUID | None = None
    chamado_origem_id: UUID | None = None


@dataclass(frozen=True, slots=True)
class CriarOrcamentoOutput:
    orcamento: Orcamento
    versao: VersaoOrcamento


def _obter_ou_criar_serie_orcamento(
    tenant_id: UUID, *, repo_serie: SerieDocumentoRepository
) -> SerieDocumento:
    """Obtem-ou-cria (idempotente) a serie de orcamento do tenant (D-FATIA2-B).

    Regime/reset sao DERIVADOS do tipo dentro de `criar_serie` (ADR-0080) — nunca
    informados aqui. Trata corrida concorrente (`SerieJaExisteError` -> re-obtem).
    """
    from src.application.configuracoes_sistema import serie as uc_serie

    existente = repo_serie.obter(
        tenant_id=tenant_id,
        tipo=TipoDocumento.ORCAMENTO,
        prefixo=_PREFIXO_SERIE_ORCAMENTO,
        filial_id=None,
    )
    if existente is not None:
        return existente

    try:
        return uc_serie.criar_serie(
            uc_serie.CriarSerieInput(
                tenant_id=tenant_id,
                tipo=TipoDocumento.ORCAMENTO,
                prefixo=_PREFIXO_SERIE_ORCAMENTO,
                formato="{prefixo}-{seq}",
                padding=6,
                filial_id=None,
            ),
            repo=repo_serie,
        )
    except uc_serie.SerieJaExisteError:
        recuperada = repo_serie.obter(
            tenant_id=tenant_id,
            tipo=TipoDocumento.ORCAMENTO,
            prefixo=_PREFIXO_SERIE_ORCAMENTO,
            filial_id=None,
        )
        if recuperada is None:
            raise
        return recuperada


def criar_orcamento(
    inp: CriarOrcamentoInput,
    *,
    repo: OrcamentoRepository,
    repo_serie: SerieDocumentoRepository,
    verificar_cliente_fn: VerificarClienteFn,
) -> CriarOrcamentoOutput:
    """Cria orcamento RASCUNHO + versao corrente V1 (AC-ORC-001).

    Raises:
      ClienteBloqueado (422): cliente inexistente, inativo ou bloqueado (D-ORC-4).
    """
    status = verificar_cliente_fn(inp.cliente_id, inp.tenant_id)
    if not status.existe:
        raise ClienteBloqueado(
            f"cliente {inp.cliente_id} inexistente neste tenant (D-ORC-4).",
            cliente_id=str(inp.cliente_id),
        )
    if not status.ativo:
        raise ClienteBloqueado(
            f"cliente {inp.cliente_id} inativo/removido — nao pode receber orcamento (D-ORC-4).",
            cliente_id=str(inp.cliente_id),
        )
    if status.bloqueado:
        raise ClienteBloqueado(
            f"cliente {inp.cliente_id} bloqueado (US-CLI-004) — nao pode receber orcamento (D-ORC-4).",
            cliente_id=str(inp.cliente_id),
        )

    serie = _obter_ou_criar_serie_orcamento(inp.tenant_id, repo_serie=repo_serie)
    ano = inp.agora.year if serie.reset_anual else None
    reserva = repo_serie.reservar_numero(
        tenant_id=inp.tenant_id,
        serie_id=serie.id,
        ano=ano,
    )
    # BURACOS_ACEITOS: reserva ja consumida (reserva.reserva_id is None) — sem confirmar.

    zero = Dinheiro(0, inp.moeda)
    orcamento_id = uuid4()
    orcamento = Orcamento(
        id=orcamento_id,
        tenant_id=inp.tenant_id,
        cliente_atual_id=inp.cliente_id,
        cliente_referencia_hash=inp.cliente_referencia_hash,
        cliente_key_id=inp.cliente_key_id,
        numero=reserva.sequencial,
        estado=EstadoOrcamento.RASCUNHO,
        validade=inp.validade,
        total_bruto=zero,
        descontos=zero,
        impostos=zero,
        liquido=zero,
        comissao_prevista=zero,
        condicoes_pagamento=inp.condicoes_pagamento,
        criado_em=inp.agora,
        criado_por=inp.criado_por,
        template_id=inp.template_id,
        tabela_preco_id=inp.tabela_preco_id,
        observacoes=inp.observacoes,
        responsavel_id=inp.responsavel_id,
        chamado_origem_id=inp.chamado_origem_id,
    )
    orcamento = repo.salvar(orcamento)

    versao = VersaoOrcamento(
        id=uuid4(),
        orcamento_id=orcamento_id,
        tenant_id=inp.tenant_id,
        numero_versao=1,
        snapshot={},
        criada_em=inp.agora,
        criada_por=inp.criado_por,
    )
    versao = repo.salvar_versao(versao)

    return CriarOrcamentoOutput(orcamento=orcamento, versao=versao)
