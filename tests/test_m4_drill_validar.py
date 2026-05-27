"""Tests T-CAL-159 — drill validar_m4_calibracao.

Roda as verificacoes estruturais sobre o test DB (que tem migrations
aplicadas via pytest-django). Cada categoria de check deve retornar
PASS quando o ambiente esta correto.
"""

from __future__ import annotations

import pytest


@pytest.mark.django_db
def test_drill_validar_m4_calibracao_pass() -> None:
    """Smoke: drill nao reporta nenhuma falha estrutural no test DB."""
    from src.infrastructure.calibracao.management.commands.validar_m4_calibracao import (
        rodar_todas_verificacoes,
    )

    resultados = rodar_todas_verificacoes()

    # Total estimado: 23 tabelas + 23 RLS + 7 checks individuais = 53 checks
    assert len(resultados) >= 50

    falhas = [r for r in resultados if not r.passou]
    if falhas:
        msg = "\n".join(str(f) for f in falhas)
        pytest.fail(f"Drill validar_m4_calibracao falhou em:\n{msg}")


@pytest.mark.django_db
def test_drill_23_tabelas_m4_existem() -> None:
    """Especifico: 23 tabelas-alvo do M4 estao presentes."""
    from src.infrastructure.calibracao.management.commands.validar_m4_calibracao import (
        TABELAS_M4,
        _verificar_tabelas_existem,
    )

    assert len(TABELAS_M4) == 23
    resultados = _verificar_tabelas_existem()
    assert len(resultados) == 23
    for r in resultados:
        assert r.passou, f"Tabela ausente: {r.nome}"


@pytest.mark.django_db
def test_drill_calibracao_revision_e_zona() -> None:
    """ADR-0065 (revision) + ADR-0024 revisado (zona_ilac_g8) presentes."""
    from src.infrastructure.calibracao.management.commands.validar_m4_calibracao import (
        _verificar_coluna_revision,
        _verificar_coluna_zona_ilac,
    )

    assert _verificar_coluna_revision().passou
    assert _verificar_coluna_zona_ilac().passou


@pytest.mark.django_db
def test_drill_cross_marco_atividade_grandeza() -> None:
    """ADR-0063 Opcao A — AtividadeDaOS.grandeza presente."""
    from src.infrastructure.calibracao.management.commands.validar_m4_calibracao import (
        _verificar_atividade_grandeza_cross_marco,
    )

    assert _verificar_atividade_grandeza_cross_marco().passou


@pytest.mark.django_db
def test_drill_sequence_global() -> None:
    """ADR-0056 — sequence global de numero_interno."""
    from src.infrastructure.calibracao.management.commands.validar_m4_calibracao import (
        _verificar_sequence_global,
    )

    assert _verificar_sequence_global().passou
