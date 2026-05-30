"""Motor DETERMINÍSTICO de extração de escopo CGCRE (M6 Fatia 4 — T-ECMC-050).

Converte uma tabela JÁ extraída do PDF (linhas de células de texto) em
`LinhaEscopoExtraida` candidatas — **staging**, nunca persiste vigente
(INV-ECMC-007). A conferência humana normaliza antes de virar `EscopoCMC`.

Princípios (ADR-0025 cl. 7.11 / GATE-ECMC-EXTRACT-ENGINE):
- **Determinístico**: mesma entrada → mesma saída (replay fixture é contrato).
- **NÃO IA**: leitor de tabela puro — NÃO ativa ADR-0059 (LLM). A etapa
  binário-PDF → linhas-de-células é uma PORTA trocável (`LeitorTabelaPdf`),
  implementada em infra; ESTE módulo só mapeia células → VO + confiança.
- **Puro**: Decimal (nunca float), sem Django, sem I/O.

`confianca` (0..1) sinaliza células de baixa certeza para a tela de conferência
destacar — NUNCA decide sozinho (humano confirma — T-ECMC-052).
"""

from __future__ import annotations

import re
from collections.abc import Sequence
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Protocol, runtime_checkable

from .entities import LinhaEscopoExtraida

# Token numérico pt-BR: "1.234,56" / "0,5" / "200" / "-30" / "1,5e-3".
# (sem \s — não atravessa espaços; cada número é um token isolado).
_NUMERO = re.compile(r"[-+]?\d[\d.]*(?:,\d+)?(?:[eE][-+]?\d+)?")


@runtime_checkable
class LeitorTabelaPdf(Protocol):
    """Porta trocável: binário do PDF CGCRE -> linhas de células de texto.

    Implementação concreta vive em infra (ex.: pdfplumber/camelot) — adapter
    determinístico, NÃO IA. Mantida fora deste módulo puro (ADR-0072).
    """

    def extrair_linhas(self, pdf_bytes: bytes) -> list[list[str]]: ...


@dataclass(frozen=True, slots=True)
class MapaColunas:
    """Índice (0-based) de cada papel de coluna na tabela extraída.

    `faixa` = coluna única com range textual ("0,5 a 200"); OU use
    `faixa_min`+`faixa_max` separados. `unidade`/`metodo` opcionais.
    """

    grandeza: int
    cmc: int
    faixa: int | None = None
    faixa_min: int | None = None
    faixa_max: int | None = None
    unidade: int | None = None
    metodo: int | None = None


def parsear_decimal_ptbr(texto: str) -> Decimal | None:
    """Decimal pt-BR determinístico. None se não-parseável (NUNCA levanta).

    Regra (determinística, documentada — cl. 7.11):
    - Extrai o 1º token numérico (tolera "(", ")", unidade colada).
    - COM vírgula → pt-BR: "." é milhar (removido), "," é decimal. "1.234,56"→1234.56.
    - SEM vírgula → "." é separador decimal (en-US): "1.000"→1.000 (=1), "0.5"→0.5.
      Milhar pt-BR sem decimal ("1.000"=mil) é AMBÍGUO — a conferência humana
      resolve (motor não adivinha; valor explícito "1000" ou "1.000,0" elimina).
    """
    if not texto:
        return None
    m = _NUMERO.search(texto)
    if m is None:
        return None
    t = m.group(0)
    if "," in t:
        t = t.replace(".", "").replace(",", ".")
    try:
        return Decimal(t)
    except InvalidOperation:
        return None


def _split_faixa(texto: str) -> tuple[Decimal | None, Decimal | None]:
    """Quebra "0,5 a 200" / "(-30 a 660)" / "(0,5 a 200) kg" -> (min, max).

    Determinístico por TOKENS: pega o 1º e o último número. 1 número só ->
    (v, v) (faixa pontual; conferência decide). Nenhum -> (None, None).
    """
    achados = _NUMERO.findall(texto or "")
    if len(achados) >= 2:
        return parsear_decimal_ptbr(achados[0]), parsear_decimal_ptbr(achados[-1])
    if len(achados) == 1:
        v = parsear_decimal_ptbr(achados[0])
        return v, v
    return None, None


def _celula(linha: Sequence[str], idx: int | None) -> str:
    if idx is None or idx < 0 or idx >= len(linha):
        return ""
    return (linha[idx] or "").strip()


def _parsear_linha(linha: Sequence[str], mapa: MapaColunas) -> LinhaEscopoExtraida:
    grandeza_texto = _celula(linha, mapa.grandeza)
    cmc_texto = _celula(linha, mapa.cmc)
    unidade = _celula(linha, mapa.unidade)
    metodo_texto = _celula(linha, mapa.metodo)

    if mapa.faixa is not None:
        fmin, fmax = _split_faixa(_celula(linha, mapa.faixa))
    else:
        fmin = parsear_decimal_ptbr(_celula(linha, mapa.faixa_min))
        fmax = parsear_decimal_ptbr(_celula(linha, mapa.faixa_max))

    # Escore de confiança determinístico — penaliza células ausentes/duvidosas.
    conf = Decimal("1")
    if not grandeza_texto:
        conf *= Decimal("0.3")
    if not cmc_texto:
        conf *= Decimal("0.3")
    if fmin is None or fmax is None:
        conf *= Decimal("0.5")  # faixa não reconhecida -> destacar pra revisão
    elif fmin >= fmax:
        conf *= Decimal("0.5")  # ordem suspeita (humano decide)
    if not unidade:
        conf *= Decimal("0.8")

    return LinhaEscopoExtraida(
        grandeza_texto=grandeza_texto,
        unidade=unidade,
        cmc_texto=cmc_texto,
        faixa_min=fmin,
        faixa_max=fmax,
        metodo_texto=metodo_texto,
        confianca=conf,
    )


def parsear_tabela(
    linhas: Sequence[Sequence[str]], mapa: MapaColunas
) -> tuple[LinhaEscopoExtraida, ...]:
    """Mapeia linhas de células -> LinhaEscopoExtraida (determinístico).

    Ignora linhas totalmente vazias (cabeçalho/rodapé já removidos pelo leitor).
    """
    if mapa.faixa is None and (mapa.faixa_min is None or mapa.faixa_max is None):
        raise ValueError(
            "MapaColunas: informe `faixa` (range) OU `faixa_min`+`faixa_max`."
        )
    resultado: list[LinhaEscopoExtraida] = []
    for linha in linhas:
        if not any((c or "").strip() for c in linha):
            continue
        resultado.append(_parsear_linha(linha, mapa))
    return tuple(resultado)
