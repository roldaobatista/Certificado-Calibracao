"""Parser DETERMINÍSTICO do CSV de catálogo — US-CAT-004 (T-PPS-040). PURO.

Layout FIXO (ADV-PPS-06 — minimização): só as colunas abaixo são lidas;
qualquer coluna extra do arquivo é DESCARTADA no parse (célula fora do layout
NUNCA persiste). A leitura física do arquivo (encoding UTF-8/BOM, sniffer de
delimitador `;`/`,`, limite de linhas) reusa `clientes/csv_io.ler_csv_normalizado`
na borda infra (anti-retrabalho); a sanitização anti formula-injection
(`sanitizar_celula_csv`) também acontece na borda, ANTES deste parser.

Preço em dialeto BR (D-PPS-6): vírgula é o separador decimal canônico
("1.234,56" → 1234.56). Valor só com ponto é aceito apenas no shape decimal
en-US inequívoco (`123.45`, ≤2 casas); "1.234" (padrão milhar BR sem vírgula)
é AMBÍGUO → linha REJEITADA (preço errado silencioso é o pior outcome).

`kit` NÃO importa via CSV (composição não cabe em linha) → linha rejeitada.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Final

from src.domain.produtos_pecas_servicos.enums import StatusLinhaImportacao, TipoItem

# Colunas do layout fixo: nome do header (case-insensitive) → obrigatória?
LAYOUT_FIXO: Final[dict[str, bool]] = {
    "codigo_interno": True,
    "tipo": True,
    "nome": True,
    "unidade_medida": True,
    "preco_padrao": True,
    "categoria": False,
    "descricao": False,
    "codigo_fabricante": False,
}

_TIPOS_IMPORTAVEIS: Final[frozenset[str]] = frozenset(
    {TipoItem.PRODUTO.value, TipoItem.PECA.value, TipoItem.SERVICO.value}
)

_RE_DECIMAL_EN: Final[re.Pattern[str]] = re.compile(r"^\d+(\.\d{1,2})?$")
_RE_DECIMAL_BR: Final[re.Pattern[str]] = re.compile(r"^[\d.]+,\d{1,2}$")


class ErroLayoutCsvError(Exception):
    """Erro de ARQUIVO (não de linha): header sem coluna obrigatória (→ 400)."""


@dataclass(frozen=True)
class LinhaImportacaoParseada:
    """Resultado do parse de UMA linha — VALIDADA ou REJEITADA (com motivo)."""

    linha_numero: int  # 2-based (linha 1 = header)
    status: StatusLinhaImportacao
    codigo_interno: str = ""
    tipo: str = ""
    nome: str = ""
    unidade_medida: str = ""
    preco_padrao: Decimal | None = None
    categoria: str = ""
    descricao: str = ""
    codigo_fabricante: str = ""
    motivo_rejeicao: str = ""


def parse_preco_br(texto: str) -> Decimal:
    """Preço dialeto BR (vírgula decimal) com tolerância en-US inequívoca.

    Raises ValueError em vazio/ambíguo/não-numérico ("1.234" sem vírgula é
    padrão milhar BR → ambíguo → rejeita; fail-closed contra preço errado).
    """
    limpo = texto.strip().replace(" ", "").replace("R$", "")
    if not limpo:
        raise ValueError("preço vazio")
    if "," in limpo:
        if not _RE_DECIMAL_BR.match(limpo):
            raise ValueError(f"preço BR inválido: {texto!r}")
        normalizado = limpo.replace(".", "").replace(",", ".")
    else:
        if not _RE_DECIMAL_EN.match(limpo):
            raise ValueError(
                f"preço ambíguo/inválido: {texto!r} (use vírgula decimal — dialeto BR)"
            )
        normalizado = limpo
    try:
        return Decimal(normalizado)
    except InvalidOperation as exc:  # defesa extra (regex já filtra)
        raise ValueError(f"preço não-numérico: {texto!r}") from exc


def resolver_indices_layout(headers: tuple[str, ...]) -> dict[str, int]:
    """Mapeia campo do layout → índice da coluna (case-insensitive).

    Colunas do arquivo FORA do layout são simplesmente ignoradas (descartadas).
    Coluna obrigatória ausente → ErroLayoutCsvError (erro de arquivo, 400).
    """
    headers_lower = [h.lower().strip() for h in headers]
    indices: dict[str, int] = {}
    faltando: list[str] = []
    for campo, obrigatoria in LAYOUT_FIXO.items():
        if campo in headers_lower:
            indices[campo] = headers_lower.index(campo)
        elif obrigatoria:
            faltando.append(campo)
    if faltando:
        raise ErroLayoutCsvError(
            f"CSV sem coluna(s) obrigatória(s) do layout: {', '.join(faltando)}. "
            f"Layout fixo: {', '.join(LAYOUT_FIXO)}."
        )
    return indices


def parsear_linhas_catalogo(
    headers: tuple[str, ...],
    linhas: tuple[tuple[str, ...], ...],
) -> tuple[LinhaImportacaoParseada, ...]:
    """Valida linha a linha (determinístico — mesma entrada, mesma saída).

    Rejeições por LINHA (arquivo segue): campo obrigatório vazio; tipo fora de
    produto|peca|servico (kit não importa via CSV); preço inválido/≤0; código
    repetido no PRÓPRIO arquivo (1ª vence — dedup intra-arquivo explícito).
    """
    indices = resolver_indices_layout(headers)

    def _campo(linha: tuple[str, ...], campo: str) -> str:
        idx = indices.get(campo)
        if idx is None or idx >= len(linha):
            return ""
        return linha[idx].strip()

    resultado: list[LinhaImportacaoParseada] = []
    codigos_vistos: set[str] = set()
    for numero, linha in enumerate(linhas, start=2):  # linha 1 = header

        def _rejeitada(motivo: str, n: int = numero) -> LinhaImportacaoParseada:
            return LinhaImportacaoParseada(
                linha_numero=n,
                status=StatusLinhaImportacao.REJEITADA,
                motivo_rejeicao=motivo,
            )

        codigo = _campo(linha, "codigo_interno")
        tipo = _campo(linha, "tipo").lower()
        nome = _campo(linha, "nome")
        um = _campo(linha, "unidade_medida")
        preco_texto = _campo(linha, "preco_padrao")

        if not codigo or not nome or not um:
            resultado.append(
                _rejeitada("campo obrigatório vazio (codigo_interno/nome/unidade_medida).")
            )
            continue
        if tipo == TipoItem.KIT.value:
            resultado.append(
                _rejeitada("kit não importa via CSV — cadastre e monte pela tela (US-CAT-003).")
            )
            continue
        if tipo not in _TIPOS_IMPORTAVEIS:
            resultado.append(
                _rejeitada(f"tipo '{tipo}' inválido (aceitos: produto, peca, servico).")
            )
            continue
        try:
            preco = parse_preco_br(preco_texto)
        except ValueError as exc:
            resultado.append(_rejeitada(str(exc)))
            continue
        if preco <= 0:
            resultado.append(_rejeitada("preço deve ser > 0 (INV-PPS-PRECO-POSITIVO)."))
            continue
        if codigo in codigos_vistos:
            resultado.append(
                _rejeitada(f"código '{codigo}' repetido no arquivo (1ª ocorrência vence).")
            )
            continue
        codigos_vistos.add(codigo)
        resultado.append(
            LinhaImportacaoParseada(
                linha_numero=numero,
                status=StatusLinhaImportacao.VALIDADA,
                codigo_interno=codigo,
                tipo=tipo,
                nome=nome,
                unidade_medida=um,
                preco_padrao=preco,
                categoria=_campo(linha, "categoria"),
                descricao=_campo(linha, "descricao"),
                codigo_fabricante=_campo(linha, "codigo_fabricante"),
            )
        )
    return tuple(resultado)
