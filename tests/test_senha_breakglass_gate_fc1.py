"""Testes do validador de senha break-glass (GATE-FC1-CRIAR-RECOVERY-SENHA-COMPLEXA).

Conserto segurança-BAIXO-1 F-C1: complexidade + dicionario na senha inicial
da conta de privilegio maximo. Validador puro (sem DB) — testavel direto.
"""

from __future__ import annotations

import pytest
from src.infrastructure.usuario.senha_breakglass import validar_senha_breakglass

_EMAIL = "admin-recovery@afere.local"
_NOME = "Conta Recovery Roldao Batista"


class TestSenhaForteAprovada:
    def test_passphrase_aleatoria_longa_aprovada(self) -> None:
        # 4 categorias, sem dicionario, sem sequencia, alta entropia.
        validar_senha_breakglass(
            "Tr0vao#Verde!8xKplmZ", email=_EMAIL, nome=_NOME
        )  # nao levanta

    def test_outra_forte_aprovada(self) -> None:
        validar_senha_breakglass(
            "Gx7@wNq2&LrV9#tHbe", email=_EMAIL, nome=_NOME
        )


class TestReprovacoes:
    def test_curta_reprova(self) -> None:
        with pytest.raises(ValueError, match=">= 14"):
            validar_senha_breakglass("Ab1!xYz9#", email=_EMAIL, nome=_NOME)

    def test_falta_categoria_reprova(self) -> None:
        # 14+ chars mas sem simbolo (so 3 categorias).
        with pytest.raises(ValueError, match="4 categorias"):
            validar_senha_breakglass("Abcdef123456Xy", email=_EMAIL, nome=_NOME)

    def test_contem_email_reprova(self) -> None:
        with pytest.raises(ValueError, match="email"):
            validar_senha_breakglass(
                "Admin-Recovery#9Zk!", email=_EMAIL, nome=_NOME
            )

    def test_contem_nome_reprova(self) -> None:
        with pytest.raises(ValueError, match="nome"):
            validar_senha_breakglass(
                "Roldao#Forte99Zk!Qx", email=_EMAIL, nome=_NOME
            )

    def test_termo_dicionario_reprova(self) -> None:
        with pytest.raises(ValueError, match="dicionario"):
            validar_senha_breakglass(
                "Password#Forte99Zk!", email=_EMAIL, nome=_NOME
            )

    def test_sequencia_trivial_reprova(self) -> None:
        with pytest.raises(ValueError, match="sequencia trivial"):
            validar_senha_breakglass(
                "Mn1234#XyKplmZ!Qw", email=_EMAIL, nome=_NOME
            )

    def test_repeticao_baixa_entropia_reprova(self) -> None:
        # 14 chars mas dominado por 'a' — entropia baixa.
        with pytest.raises(ValueError, match="entropia"):
            validar_senha_breakglass(
                "Aaaaaaaaaaaa1!", email=_EMAIL, nome=_NOME
            )
