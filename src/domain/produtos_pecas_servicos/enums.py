"""Enums do catálogo (T-PPS-010 — US-CAT-001..005).

Nota TL-PPS-14: `PRODUTO` × `PECA` são RÓTULOS de catálogo sem comportamento
distinto no núcleo — nenhuma regra deve ramificar entre eles. Só `KIT`
(composição, linha própria na tabela) e `SERVICO` (`controla_estoque=False`
default) têm regra própria.
"""

from __future__ import annotations

from enum import Enum


class TipoItem(str, Enum):
    """Tipo do item de catálogo (imutável pós-criação)."""

    PRODUTO = "produto"
    PECA = "peca"
    SERVICO = "servico"
    KIT = "kit"


class StatusItem(str, Enum):
    """Ciclo de vida do item (ADR-0031 — sem DELETE; inativa é terminal lógico)."""

    ATIVO = "ativo"
    INATIVO = "inativo"


class OrigemPreco(str, Enum):
    """Origem do preço resolvido pela porta (ADR-0081 §4 / ADV-PPS-08)."""

    MANUAL = "manual"
    SOMA_PARTES = "soma_partes"


class StatusLinhaImportacao(str, Enum):
    """Estado de cada linha do staging de importação (US-CAT-004 — INV-ECMC-007 molde)."""

    VALIDADA = "validada"
    REJEITADA = "rejeitada"
    ACEITA = "aceita"
