"""Excecoes base de violacao de invariante.

Toda invariante critica do REGRAS-INEGOCIAVEIS.md vira metodo
assert_inv_NNN() no agregado correspondente. Quando violada, levanta
InvariantViolation com o ID — facilita observabilidade + auditoria.
"""

from __future__ import annotations


class InvariantViolation(Exception):
    """Levantada quando uma invariante de dominio nao se sustenta."""

    def __init__(self, inv_id: str, message: str) -> None:
        self.inv_id = inv_id
        self.message = message
        super().__init__(f"[{inv_id}] {message}")
