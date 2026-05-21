"""Drill `validar_m1_clientes` — exercita o critério §3 item 5 da spec Marco 1.

O próprio drill é teste end-to-end de isolamento multi-tenant + integridade dos
fluxos (cadastro / importação / dedup / bloqueio). Aqui apenas garantimos que:
- ele roda sem exceção no banco descartável de teste,
- termina com exit code 0 (PASS),
- valida pelo menos um output esperado (tabela de resultados).
"""

from __future__ import annotations

import pytest
from django.core.management import call_command


@pytest.mark.django_db(transaction=True)
def test_drill_marco_1_clientes_passa_em_test_db(capsys):
    """Drill multi-tenant da Marco 1 — PASS esperado.

    Em PASS o handle não levanta SystemExit (sai naturalmente). Em FAIL
    chama `sys.exit(1)`. Em test_afere o guard `--em-banco-descartavel`
    é dispensado (NAME='test*').
    """
    try:
        call_command("validar_m1_clientes")
    except SystemExit as e:
        # SystemExit aceita: 0 ou None = PASS; outros = FAIL
        assert e.code in (0, None), f"Drill falhou com exit code {e.code}"

    captured = capsys.readouterr()
    out = captured.out
    # Tabela de resultados foi impressa
    assert "Drill Marco 1" in out
    # Todos os checks reportados com [PASS]
    assert "[FAIL]" not in out, f"Drill reportou FAIL em algum check:\n{out}"
    # Pelo menos uma linha esperada de check de isolamento
    assert "isolamento Cliente cross-tenant" in out
    assert "isolamento bus_outbox" in out
    assert "cadeia auditoria por tenant" in out
    assert "resolução canônica pós-mescla" in out
    assert "agendamentos_futuros" in out
    # E confirmação de sucesso
    assert "PASS" in out
