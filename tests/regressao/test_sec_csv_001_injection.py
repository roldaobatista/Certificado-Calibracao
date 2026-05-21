"""SEC-CSV-001 — anti-CSV-injection.

Spec Marco 1 §3 item 9 + §1: suíte anti-regressão.

SEC-CSV-001 (REGRAS-INEGOCIAVEIS): toda célula iniciando com `=`, `+`,
`-`, `@`, `\\t`, `\\r` (ou com espaços antes) é prefixada por `'`
(apóstrofo) via helper único `csv_safety.sanitizar_celula_csv`. OWASP
CSV Injection (CVE-2014-3524 família).
"""

from __future__ import annotations

import pytest
from src.infrastructure.clientes.csv_safety import sanitizar_celula_csv


@pytest.mark.parametrize(
    "valor_perigoso",
    [
        "=cmd|'/c calc'!A1",
        "+SUM(1+1)",
        "-1+1",
        "@evil",
        # Espaços/tabs/CR iniciais antes dos gatilhos (variante de evasão conhecida)
        "  =SUM(A1:A2)",
        " +cmd",
        "\t=cmd",
        "\r@evil",
    ],
)
def test_sec_csv_001_happy_celula_perigosa_recebe_apostrofo(valor_perigoso):
    saneado = sanitizar_celula_csv(valor_perigoso)
    assert saneado.startswith("'"), f"valor não saneado: {saneado!r}"


@pytest.mark.parametrize(
    "valor_seguro",
    [
        "valor normal",
        "12345",
        "Nome do Cliente",
        "abc@def.com",  # @ no MEIO, não no início (e-mail é seguro nesse contexto)
        "",  # vazio
    ],
)
def test_sec_csv_001_unhappy_celula_segura_nao_recebe_apostrofo(valor_seguro):
    saneado = sanitizar_celula_csv(valor_seguro)
    assert not saneado.startswith("'"), f"valor seguro foi alterado: {saneado!r}"
