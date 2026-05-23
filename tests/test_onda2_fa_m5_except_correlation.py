"""F-A-M5 (Onda 2 saneamento — 2026-05-22) — teste de regressao do except
especifico em `_obter_correlation_id`.

INV-FA-002 — `except Exception` substituido por
`except (DatabaseError, OperationalError)`. Caso a captura nao cubra alguma
nova excecao de PG, o teste demonstra que (a) `DatabaseError` continua
sendo capturado e gera `logger.warning`, e (b) excecoes nao-DB **nao** sao
mascaradas (propagam — comportamento desejado).

Padrao TST-005: happy + 2 bordas explicitas.
"""

from __future__ import annotations

import logging
from unittest.mock import patch

import pytest
from django.db import DatabaseError, OperationalError
from src.infrastructure.audit.event_helpers import _obter_correlation_id


class TestObterCorrelationIdExceptEspecifico:
    """Comportamento esperado pos F-A-M5 (INV-FA-002)."""

    def test_database_error_retorna_none_e_loga_warning(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """`DatabaseError` (e subclasses) continua capturado — retorna None +
        warning logado. Isto preserva o caminho de degradacao gracioso quando
        PG ainda nao tem o setting `app.correlation_id` definido (legado M1/M2).
        """
        caplog.set_level(logging.WARNING, logger="src.infrastructure.audit.event_helpers")
        with patch("src.infrastructure.audit.event_helpers.connection") as mock_conn:
            mock_conn.cursor.side_effect = DatabaseError("setting nao definido")
            resultado = _obter_correlation_id()
        assert resultado is None
        assert any(
            "correlation_id indisponivel" in rec.message for rec in caplog.records
        )

    def test_operational_error_retorna_none_e_loga_warning(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """`OperationalError` (perda de conexao, timeout) tambem capturado."""
        caplog.set_level(logging.WARNING, logger="src.infrastructure.audit.event_helpers")
        with patch("src.infrastructure.audit.event_helpers.connection") as mock_conn:
            mock_conn.cursor.side_effect = OperationalError("connection lost")
            resultado = _obter_correlation_id()
        assert resultado is None
        assert any(
            "correlation_id indisponivel" in rec.message for rec in caplog.records
        )

    def test_inv_fa_002_excecao_nao_db_propaga(self) -> None:
        """INV-FA-002 — excecao **nao-DB** deve propagar (bug real, nao
        mascarar). Antes do conserto F-A-M5, `except Exception` engolia tudo;
        agora `KeyError`/`AttributeError`/`TypeError` levantam.
        """
        with patch("src.infrastructure.audit.event_helpers.connection") as mock_conn:
            mock_conn.cursor.side_effect = KeyError("bug real na config")
            with pytest.raises(KeyError, match="bug real na config"):
                _obter_correlation_id()

    def test_inv_fa_002_attribute_error_propaga(self) -> None:
        """Outra excecao real (AttributeError simulando bug em mock/teste mal
        configurado) precisa propagar.
        """
        with patch("src.infrastructure.audit.event_helpers.connection") as mock_conn:
            mock_conn.cursor.side_effect = AttributeError("connection morta")
            with pytest.raises(AttributeError, match="connection morta"):
                _obter_correlation_id()
