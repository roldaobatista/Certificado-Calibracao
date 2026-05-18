"""Sanitizacao contra CSV / formula injection (US-CLI-003 R2 tech-lead).

Atacante importa CSV com celula `=cmd|'/c calc'!A1` ou `@SUM(1+1)*cmd|...`.
Quando o operador exporta a lista pra Excel depois, o Excel interpreta como
formula e dispara RCE local. Vetor OWASP "Formula Injection".

Estrategia: prefixar com apostrofo `'` toda string que comece com um dos
caracteres de gatilho. O apostrofo neutraliza a formula sem destruir o dado
visual (Excel mostra a string literal).

Aplicado na ESCRITA (boundary de entrada). Export futuro (Wave A) repete
no boundary de saida — defesa em profundidade.
"""

from __future__ import annotations


# Caracteres que disparam interpretacao de formula no Excel/LibreOffice/Numbers.
GATILHOS_FORMULA = ("=", "+", "-", "@", "\t", "\r")


def sanitizar_celula_csv(valor: str | None) -> str:
    """Prefixa `'` se valor inicia com gatilho de formula.

    None e string vazia passam sem mudanca. Whitespace inicial e ignorado
    (atacante usa `  =cmd|...` pra burlar regex ingenua — apos lstrip o
    gatilho ainda eh detectado).
    """
    if valor is None:
        return ""
    if not valor:
        return ""
    # lstrip remove tab/space/newline iniciais (atacante usa pra burlar).
    sem_ws_ini = valor.lstrip(" \t\r\n")
    if sem_ws_ini.startswith(GATILHOS_FORMULA):
        # Apostrofo TEM que ficar colado no gatilho. Retornar "'" + valor
        # original deixaria "'  =cmd" (apostrofo antes do whitespace) e o
        # Excel ainda interpreta a formula. O whitespace inicial nao e dado
        # legitimo aqui — e o proprio vetor de evasao —, entao descarta-se.
        return "'" + sem_ws_ini
    return valor
