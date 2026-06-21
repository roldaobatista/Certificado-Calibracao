"""Camada de aplicação do módulo caixa_tecnico (Fatia 2).

Contém os use cases que orquestram domínio, repositórios e ports.
Nenhum use case publica eventos — a view faz isso dentro do ``transaction.atomic``.

Use cases disponíveis:
- ``LancarDespesaUseCase``     — US-CT-002: lançamento de despesa com foto-comprovante.
- ``ReapresentarDespesaUseCase`` — US-CT-007: reapresentação após rejeição.
- ``ValidarDespesaUseCase``    — US-CT-003: validação pelo financeiro.
- ``RejeitarDespesaUseCase``   — US-CT-004: rejeição pelo financeiro com motivo.
- ``SolicitarAdiantamentoUseCase`` — US-CT-001: solicitação de adiantamento.
- ``AprovarAdiantamentoUseCase``   — US-CT-005: aprovação com verificação de alçada.
- ``RecusarAdiantamentoUseCase``   — US-CT-006: recusa com motivo.
- ``EntregarAdiantamentoUseCase``  — US-CT-008: registro de entrega do adiantamento.
- ``FecharPrestacaoUseCase``       — US-CT-009: fechamento da prestação de contas.
- ``SyncDespesasLoteUseCase``      — US-CT-010: sincronização offline em lote (≤20 itens).
"""

from .aprovar_adiantamento import AprovarAdiantamentoInput, AprovarAdiantamentoUseCase
from .entregar_adiantamento import EntregarAdiantamentoInput, EntregarAdiantamentoUseCase
from .fechar_prestacao import FecharPrestacaoInput, FecharPrestacaoUseCase
from .lancar_despesa import LancarDespesaInput, LancarDespesaOutput, LancarDespesaUseCase
from .reapresentar_despesa import ReapresentarDespesaInput, ReapresentarDespesaUseCase
from .recusar_adiantamento import RecusarAdiantamentoInput, RecusarAdiantamentoUseCase
from .rejeitar_despesa import RejeitarDespesaInput, RejeitarDespesaUseCase
from .solicitar_adiantamento import SolicitarAdiantamentoInput, SolicitarAdiantamentoUseCase
from .sync_despesas_lote import (
    ItemLote,
    ResultadoItem,
    SyncDespesasLoteUseCase,
    SyncLoteInput,
    SyncLoteOutput,
)
from .validar_despesa import ValidarDespesaInput, ValidarDespesaUseCase

__all__ = [
    # lancar_despesa
    "LancarDespesaInput",
    "LancarDespesaOutput",
    "LancarDespesaUseCase",
    # reapresentar_despesa
    "ReapresentarDespesaInput",
    "ReapresentarDespesaUseCase",
    # validar_despesa
    "ValidarDespesaInput",
    "ValidarDespesaUseCase",
    # rejeitar_despesa
    "RejeitarDespesaInput",
    "RejeitarDespesaUseCase",
    # solicitar_adiantamento
    "SolicitarAdiantamentoInput",
    "SolicitarAdiantamentoUseCase",
    # aprovar_adiantamento
    "AprovarAdiantamentoInput",
    "AprovarAdiantamentoUseCase",
    # recusar_adiantamento
    "RecusarAdiantamentoInput",
    "RecusarAdiantamentoUseCase",
    # entregar_adiantamento
    "EntregarAdiantamentoInput",
    "EntregarAdiantamentoUseCase",
    # fechar_prestacao
    "FecharPrestacaoInput",
    "FecharPrestacaoUseCase",
    # sync_despesas_lote
    "ItemLote",
    "ResultadoItem",
    "SyncLoteInput",
    "SyncLoteOutput",
    "SyncDespesasLoteUseCase",
]
