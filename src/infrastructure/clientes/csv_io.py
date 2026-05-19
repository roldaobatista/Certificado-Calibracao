"""Leitura normalizada de CSV de importacao (US-CLI-003 — R5/R6 tech-lead + R8/R9 advogado).

Decisoes cravadas no plano v2:
- Encoding aceito: UTF-8 com ou sem BOM. Latin-1 rejeita 400 com dica.
- Delimitador: `,` ou `;` com deteccao via `csv.Sniffer`.
- Linha 0 = header obrigatorio.
- Limite de linhas: 1000 (excluindo header).
- Heuristicas de mapeamento header -> campo destino + deteccao de colunas
  sensiveis (LGPD art. 5 II) + deteccao de colunas CPF-em-PJ.
"""

from __future__ import annotations

import csv
import io
import re
from dataclasses import dataclass
from typing import Any

from src.infrastructure.clientes.csv_safety import sanitizar_celula_csv

LIMITE_LINHAS = 1000
LIMITE_BYTES = 2 * 1024 * 1024  # espelha config/settings/base.py


class ErroCsvIo(Exception):
    """Erro durante leitura/normalizacao do CSV."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


# =============================================================
# Heuristicas de matching header -> campo do Cliente
# =============================================================

HEADER_HEURISTICAS: dict[str, tuple[str, ...]] = {
    "documento": ("cpf", "cnpj", "cpf/cnpj", "cpf_cnpj", "documento", "doc"),
    "nome": ("nome", "razao social", "razao_social", "cliente", "nome completo", "nome_completo"),
    "nome_fantasia": ("nome fantasia", "nome_fantasia", "fantasia", "apelido"),
    "email": ("email", "e-mail", "e_mail", "correio eletronico", "correio_eletronico"),
    "telefone": ("telefone", "fone", "celular", "whatsapp", "tel"),
}


# Heuristica: colunas de CPF de socio/responsavel em PJ (R8 advogado).
HEADERS_CPF_RESPONSAVEL = (
    "cpf_responsavel",
    "cpf responsavel",
    "cpf do responsavel",
    "cpf_socio",
    "cpf socio",
    "cpf do socio",
    "responsavel legal cpf",
    "responsavel_legal_cpf",
    "cpf_responsavel_legal",
)


# Heuristica: colunas com dados sensiveis (R9 advogado — LGPD art. 5 II).
# Regex case-insensitive em token completo.
REGEX_DADOS_SENSIVEIS = re.compile(
    r"\b("
    r"saude|saúde|cid|diagnostico|diagnóstico|"
    r"raca|raça|cor|"
    r"religiao|religião|"
    r"orientacao|orientação|sexual|"
    r"biometr|"
    r"dna|genetic|genético|"
    r"sindical|sindicato|"
    r"politic|político"
    r")\b",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class CsvNormalizado:
    """Resultado de `ler_csv_normalizado`."""

    delimitador: str
    encoding: str
    headers: tuple[str, ...]
    linhas: tuple[tuple[str, ...], ...]
    total_linhas: int


def ler_csv_normalizado(arquivo_bytes: bytes) -> CsvNormalizado:
    """Le bytes de CSV e devolve estrutura normalizada.

    Raises:
        ErroCsvIo: encoding invalido, arquivo vazio, sem header, linhas > 1000.
    """
    if not arquivo_bytes:
        raise ErroCsvIo("arquivo_vazio", "Arquivo CSV vazio.")
    if len(arquivo_bytes) > LIMITE_BYTES:
        raise ErroCsvIo(
            "arquivo_excede_limite",
            f"Arquivo excede {LIMITE_BYTES} bytes ({LIMITE_BYTES // 1024 // 1024} MiB).",
        )

    # --- Encoding ---
    # UTF-8 com BOM eh aceito (utf-8-sig strip transparente).
    texto: str
    encoding_detectado: str
    try:
        texto = arquivo_bytes.decode("utf-8-sig")
        encoding_detectado = "utf-8"
    except UnicodeDecodeError as e:
        raise ErroCsvIo(
            "encoding_invalido",
            (
                "Arquivo nao esta em UTF-8. Salve novamente como CSV UTF-8 "
                "(Excel: Salvar Como > CSV UTF-8)."
            ),
        ) from e

    # --- Delimitador via Sniffer (amostra dos 8 KiB iniciais) ---
    amostra = texto[:8192]
    try:
        dialeto = csv.Sniffer().sniff(amostra, delimiters=",;")
        delimitador = dialeto.delimiter
    except csv.Error:
        # Sniffer falha em arquivos com poucas linhas — default `,`.
        delimitador = ","

    # --- Leitura ---
    reader = csv.reader(io.StringIO(texto), delimiter=delimitador)
    linhas_brutas = list(reader)
    if not linhas_brutas:
        raise ErroCsvIo("sem_linhas", "CSV nao contem nenhuma linha.")

    header_raw = linhas_brutas[0]
    headers = tuple(h.strip() for h in header_raw)
    if not any(headers):
        raise ErroCsvIo("sem_header", "CSV sem header (linha 1 vazia).")

    linhas = tuple(tuple(c.strip() for c in linha) for linha in linhas_brutas[1:])
    total_linhas = len(linhas)
    if total_linhas > LIMITE_LINHAS:
        raise ErroCsvIo(
            "linhas_excedem_limite",
            (
                f"CSV tem {total_linhas} linhas; limite eh {LIMITE_LINHAS}. "
                f"Divida o arquivo em partes."
            ),
        )

    return CsvNormalizado(
        delimitador=delimitador,
        encoding=encoding_detectado,
        headers=headers,
        linhas=linhas,
        total_linhas=total_linhas,
    )


def sugerir_mapeamento(headers: tuple[str, ...]) -> dict[str, dict[str, Any]]:
    """Devolve mapeamento sugerido `campo_destino -> {coluna, confianca}`.

    Confianca:
    - "alta": header bate exatamente (case-insensitive) com heuristica
    - "media": header contem palavra-chave parcialmente
    - "baixa": nao mapeado
    - "inferida_por_documento": inferido sem header (ex: tipo_pessoa por len)
    """
    headers_lower = tuple(h.lower().strip() for h in headers)
    resultado: dict[str, dict[str, Any]] = {}
    for campo, padroes in HEADER_HEURISTICAS.items():
        coluna_alta = None
        coluna_media = None
        for idx, h in enumerate(headers_lower):
            if not h:
                continue
            if h in padroes:
                coluna_alta = headers[idx]
                break
            for p in padroes:
                if p in h or h in p:
                    coluna_media = headers[idx]
                    break
        if coluna_alta:
            resultado[campo] = {"coluna": coluna_alta, "confianca": "alta"}
        elif coluna_media:
            resultado[campo] = {"coluna": coluna_media, "confianca": "media"}
        else:
            resultado[campo] = {"coluna": None, "confianca": "baixa"}
    # tipo_pessoa nunca vem de header — sempre inferido por len(documento).
    resultado["tipo_pessoa"] = {"coluna": None, "confianca": "inferida_por_documento"}
    return resultado


def detectar_colunas_sensiveis(headers: tuple[str, ...]) -> tuple[str, ...]:
    """Retorna headers cujo nome casa com regex de dados sensiveis (R9 advogado)."""
    return tuple(h for h in headers if h and REGEX_DADOS_SENSIVEIS.search(h))


def detectar_colunas_cpf_responsavel(headers: tuple[str, ...]) -> tuple[str, ...]:
    """Retorna headers que parecem trazer CPF de socio/responsavel (R8 advogado)."""
    return tuple(h for h in headers if h and h.lower().strip() in HEADERS_CPF_RESPONSAVEL)


# Re-export pra simetria (view importa apenas csv_io).
__all__ = [
    "CsvNormalizado",
    "ErroCsvIo",
    "LIMITE_BYTES",
    "LIMITE_LINHAS",
    "HEADERS_CPF_RESPONSAVEL",
    "detectar_colunas_cpf_responsavel",
    "detectar_colunas_sensiveis",
    "ler_csv_normalizado",
    "sanitizar_celula_csv",
    "sugerir_mapeamento",
]
