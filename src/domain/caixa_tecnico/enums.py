"""Enums fechados do domínio caixa_tecnico (Fatia 1a — T-CT-010).

str-mixin → serialização JSON nativa (mesmo padrão de ``agenda/enums.py``).
Domínio NÃO importa Django (ADR-0007).

Refs: D-CT-2/3/7/8; spec §4.
"""

from __future__ import annotations

from enum import Enum


class CategoriaDespesa(str, Enum):
    """Categoria da despesa do técnico de campo.

    ``combustivel``  — abastecimento de veículo.
    ``alimentacao``  — refeição em campo.
    ``pedagio``      — pedágio em rodovias.
    ``hospedagem``   — hospedagem em deslocamento fora da base.
    ``peca``         — peça ou material adquirido em campo.
    ``deslocamento`` — km rodado; valor calculado por ``valor_deslocamento`` (D-CT-9).
    """

    COMBUSTIVEL = "combustivel"
    ALIMENTACAO = "alimentacao"
    PEDAGIO = "pedagio"
    HOSPEDAGEM = "hospedagem"
    PECA = "peca"
    DESLOCAMENTO = "deslocamento"


class TipoDespesa(str, Enum):
    """Tipo da despesa — normal ou estorno.

    ``normal``  — lançamento comum.
    ``estorno`` — correção de despesa validada imutável (nova despesa referenciando a original).
    """

    NORMAL = "normal"
    ESTORNO = "estorno"


class EstadoDespesa(str, Enum):
    """Estado da despesa — máquina de estados (D-CT-3).

    Transições válidas (ver ``transicoes_despesa.py``):
        pendente  → validada | rejeitada | cancelada
        rejeitada → pendente  (reapresentação — US-CT-007)
        validada  → (terminal — imutável WORM)
        cancelada → (terminal)
    """

    PENDENTE = "pendente"
    VALIDADA = "validada"
    REJEITADA = "rejeitada"
    CANCELADA = "cancelada"


class EstadoAdiantamento(str, Enum):
    """Estado do adiantamento — máquina de estados (D-CT-7).

    Transições válidas (ver ``transicoes_adiantamento.py``):
        solicitado → aprovado | recusado | cancelado
        aprovado   → entregue
        entregue   → (terminal — AdiantamentoNaoCancelavel)
        recusado   → (terminal)
        cancelado  → (terminal)
    """

    SOLICITADO = "solicitado"
    APROVADO = "aprovado"
    ENTREGUE = "entregue"
    RECUSADO = "recusado"
    CANCELADO = "cancelado"


class MeioEntrega(str, Enum):
    """Meio de entrega do adiantamento (US-CT-001).

    ``pix``          — transferência PIX (liberação manual Wave A; automática Wave B — ADR-0050).
    ``transferencia``— TED/DOC bancário.
    ``dinheiro``     — entrega em espécie.
    """

    PIX = "pix"
    TRANSFERENCIA = "transferencia"
    DINHEIRO = "dinheiro"


class DirecaoPrestacao(str, Enum):
    """Direção do saldo ao fechar a prestação de contas (D-CT-8).

    ``tecnico_deve`` — técnico gastou mais do que adiantado; deve devolver.
    ``tenant_deve``  — tenant deve reembolsar o técnico (estado consultável — sem execução Wave A).
    ``quitado``      — saldo zerado; nada a pagar ou receber.
    """

    TECNICO_DEVE = "tecnico_deve"
    TENANT_DEVE = "tenant_deve"
    QUITADO = "quitado"
