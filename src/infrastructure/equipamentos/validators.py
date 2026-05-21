"""Validators anti-PII para o modulo equipamentos (T-EQP-005).

INV-EQP-LOC-001 (AC-EQP-001-4):
    `localizacao_fisica` e texto livre que NAO PODE conter PII direta —
    nem do tenant nem de terceiros. Razao: o campo aparece em listagem
    operacional e em scan de QR Code (US-EQP-003 ficha 360), visivel
    por tecnicos de campo de outros tenants (cessao temporaria) e por
    clientes finais via portal-cliente.

Padroes detectados (heuristica conservadora — best-effort, NAO
substitui revisao humana; LGPD art. 5º I + INV-EQP-LOC-001):

1. CPF: 11 digitos consecutivos ou com mascara (`123.456.789-01`,
   `12345678901`).
2. CNPJ: 14 digitos consecutivos ou com mascara
   (`12.345.678/0001-90`, `12345678000190`).
3. E-mail: `algo@algo.tld`.
4. Telefone BR: `(11) 9 9999-9999`, `11999999999`, `+5511999999999`.
5. ≥2 nomes proprios capitalizados consecutivos (`Joao Silva`,
   `Maria Santos da Costa`).

Falsos positivos esperados (aceitos como cost da defesa):
- Codigos internos com padrao 14 digitos (`SN-12345678901234`) —
  cliente reformula como `SN-LAB-001`.
- Marcas com capitalizacao (`Toledo Industrial`) — cliente reformula
  como `Sala Toledo` ou `Toledo - SP`.
"""

from __future__ import annotations

import re
from typing import Final

# CPF: 11 digitos com ou sem mascara.
_RE_CPF: Final[re.Pattern[str]] = re.compile(
    r"\b\d{3}[.\s]?\d{3}[.\s]?\d{3}[-\s]?\d{2}\b"
)

# CNPJ: 14 digitos com ou sem mascara.
_RE_CNPJ: Final[re.Pattern[str]] = re.compile(
    r"\b\d{2}[.\s]?\d{3}[.\s]?\d{3}[/\s]?\d{4}[-\s]?\d{2}\b"
)

# E-mail (RFC simplificado — basta detectar `x@y.z`).
_RE_EMAIL: Final[re.Pattern[str]] = re.compile(
    r"[a-z0-9._%+\-]+@[a-z0-9.\-]+\.[a-z]{2,}",
    re.IGNORECASE,
)

# Telefone BR: DDD (2 digitos) + 8 ou 9 digitos. Aceita parenteses,
# espacos, hifens, +55, etc.
_RE_TELEFONE: Final[re.Pattern[str]] = re.compile(
    r"(?:\+?55[\s\-]?)?(?:\(?\d{2}\)?[\s\-]?)?9?\d{4}[\s\-]?\d{4}"
)

# Nomes proprios consecutivos: 2 ou mais palavras comecando com letra
# maiuscula. Aceita preposicoes minusculas (`da`, `de`, `do`, `dos`,
# `das`) entre elas. Limita a janelas de ate 4 palavras pra reduzir
# falso positivo em texto comprido.
_RE_NOMES_CONSECUTIVOS: Final[re.Pattern[str]] = re.compile(
    r"\b[A-ZÁÉÍÓÚÂÊÎÔÛÃÕÇ][a-záéíóúâêîôûãõç]{2,}"
    r"(?:\s+(?:da|de|do|dos|das|von|van)\s+)?"
    r"\s+[A-ZÁÉÍÓÚÂÊÎÔÛÃÕÇ][a-záéíóúâêîôûãõç]{2,}\b"
)

LIMITE_LOCALIZACAO_FISICA: Final[int] = 200

MENSAGEM_REJEICAO_PII_DIRETA: Final[str] = (
    "LGPD art. 5º I + INV-EQP-LOC-001 — descreva sem nomes/documentos "
    "(detectada PII direta: CPF/CNPJ/e-mail/telefone/nomes próprios "
    "consecutivos)."
)

MENSAGEM_LIMITE_LOCALIZACAO: Final[str] = (
    f"localizacao_fisica nao pode passar de {LIMITE_LOCALIZACAO_FISICA} caracteres."
)


def conter_pii_direta(texto: str) -> bool:
    """True se o texto contiver CPF, CNPJ, e-mail, telefone ou >=2 nomes
    proprios consecutivos.

    Best-effort — heuristica conservadora documentada acima. NAO substitui
    revisao humana de PII em campo livre (LGPD art. 5º I).
    """
    if not texto:
        return False
    if _RE_CPF.search(texto):
        return True
    if _RE_CNPJ.search(texto):
        return True
    if _RE_EMAIL.search(texto):
        return True
    if _RE_TELEFONE.search(texto):
        return True
    if _RE_NOMES_CONSECUTIVOS.search(texto):
        return True
    return False


def validar_localizacao_fisica(valor: str) -> None:
    """Levanta ValueError com mensagem canonica se invalido.

    Usado em DRF serializer (.validate_localizacao_fisica) e em qualquer
    grava direta no modelo (Wave A pode usar em management commands).
    """
    if len(valor) > LIMITE_LOCALIZACAO_FISICA:
        raise ValueError(MENSAGEM_LIMITE_LOCALIZACAO)
    if conter_pii_direta(valor):
        raise ValueError(MENSAGEM_REJEICAO_PII_DIRETA)
