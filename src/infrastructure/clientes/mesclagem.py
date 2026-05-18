"""Constants + validacoes da mesclagem de clientes (US-CLI-005).

R2 do advogado: motivo livre vaza PII. Solucao: enum de 5 categorias +
campo `observacao` opcional com regex anti-PII (CPF/CNPJ/email/telefone)
limitado a 200 chars.
"""

from __future__ import annotations

import re


MOTIVO_DUPLICACAO_ATENDIMENTO = "duplicacao_atendimento"
MOTIVO_MIGRACAO_SISTEMA_LEGADO = "migracao_sistema_legado"
MOTIVO_ALTERACAO_PF_PJ = "alteracao_pf_pj"
MOTIVO_REORGANIZACAO_SOCIETARIA = "reorganizacao_societaria"
MOTIVO_OUTRO = "outro"

MOTIVOS_VALIDOS: tuple[str, ...] = (
    MOTIVO_DUPLICACAO_ATENDIMENTO,
    MOTIVO_MIGRACAO_SISTEMA_LEGADO,
    MOTIVO_ALTERACAO_PF_PJ,
    MOTIVO_REORGANIZACAO_SOCIETARIA,
    MOTIVO_OUTRO,
)


# Regex anti-PII pra observacao. Detecta:
# - CPF: 11 digitos com ou sem pontuacao
# - CNPJ: 14 alfanumericos com ou sem pontuacao
# - Email: padrao basico
# - Telefone: BR — 10/11 digitos com DDD
_RE_CPF = re.compile(r"\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b")
_RE_CNPJ = re.compile(r"\b[A-Z0-9]{2}\.?[A-Z0-9]{3}\.?[A-Z0-9]{3}/?[A-Z0-9]{4}-?\d{2}\b", re.IGNORECASE)
_RE_EMAIL = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
_RE_TELEFONE = re.compile(r"\b(?:\(?\d{2}\)?\s?)?\d{4,5}-?\d{4}\b")


def validar_observacao(texto: str) -> None:
    """Levanta ValueError se a observacao tem PII.

    Limite 200 chars; rejeita CPF, CNPJ, email, telefone — atendente que precisa
    contar a historia escreve em outro lugar (anotacao livre no Cliente — futuro)
    ou usa categoria + texto generico.
    """
    if len(texto) > 200:
        raise ValueError(
            "Observacao da mesclagem maior que 200 caracteres — "
            "use categoria + texto sucinto."
        )

    achados: list[str] = []
    if _RE_CPF.search(texto):
        achados.append("CPF")
    if _RE_CNPJ.search(texto):
        achados.append("CNPJ")
    if _RE_EMAIL.search(texto):
        achados.append("e-mail")
    if _RE_TELEFONE.search(texto):
        achados.append("telefone")

    if achados:
        raise ValueError(
            f"Observacao contem PII ({', '.join(achados)}). "
            "Nao escreva CPF, CNPJ, e-mail ou telefone do titular — "
            "use categoria + descricao generica (R2 advogado US-CLI-005)."
        )
