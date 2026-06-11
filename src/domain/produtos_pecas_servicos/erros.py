"""Erros de domínio do catálogo (T-PPS-014).

Mapeados a HTTP na camada REST. Todos com caller real nesta frente (lição da
2ª passada P9 da frente #1: exceção sem caller documenta enforcement do banco
no docstring; aqui o enforcement primário É o domínio/use case).
"""

from __future__ import annotations


class CatalogoError(Exception):
    """Base dos erros de domínio do catálogo."""


class CodigoDuplicadoError(CatalogoError):
    """INV-PPS-CODIGO-UNICO — código interno já existe no tenant (→ 409 PT).

    Enforcement em 2 camadas: use case consulta antes + UNIQUE no banco
    (IntegrityError→409 na view cobre a corrida).
    """

    reason = "CODIGO_DUPLICADO"


class VersaoRetroativaError(CatalogoError):
    """INV-PPS-PRECO-NAO-RETROATIVO (TL-PPS-08) — nova versão não pode truncar
    vigência já decorrida: `inicio_nova ≥ max(agora, inicio_da_vigente)`.
    Consulta histórica `preco_vigente_em(D)` NUNCA muda de resposta (→ 422).
    """

    reason = "VERSAO_RETROATIVA"


class KitComCicloError(CatalogoError):
    """INV-PPS-KIT-SEM-CICLO — kit não contém kit (1 nível, anti-ciclo estrutural) (→ 422)."""

    reason = "KIT_COM_CICLO"


class TabelaPadraoDuplicadaError(CatalogoError):
    """MVP: exatamente 1 TabelaPreco padrão por tenant (D-PPS-3 — UNIQUE parcial
    `eh_padrao`; schema já N-tabelas pra V2) (→ 422)."""

    reason = "TABELA_PADRAO_DUPLICADA"


class PrecoTabelaAusenteError(CatalogoError):
    """ADR-0081 — sem linha VIGENTE e NÃO-revogada na tabela padrão para o item
    na `data_referencia` (→ 422 na OS avulsa, US-OS-015). SEM fallback ao
    `preco_padrao` da lista (fail-closed). Kit sem linha PRÓPRIA também cai aqui
    (TL-PPS-09 — soma das partes nunca é resolução runtime).
    """

    reason = "PRECO_TABELA_AUSENTE"


class ItemInativoError(CatalogoError):
    """US-CAT-005 / AC-CAT-005-1 — item inativo não entra em seleção/venda nova (→ 422)."""

    reason = "ITEM_INATIVO"
