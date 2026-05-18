"""Predicate registry — ABAC extension da porta AuthorizationProvider.

TL2 do tech-lead US-CLI-004: utilidade `cliente_bloqueado_para_acao` fragmenta
authz. Solucao certa = registrar predicates ABAC nominais que o
`DjangoAuthorizationProvider.can()` consulta quando o resource bate.

Predicates retornam tupla `(allowed: bool, reason: str)`. Se `allowed=False`,
a decisao final vira denied com `reason` informado.

Como registrar (em runtime, no AppConfig.ready ou modulo carregado):

    from src.infrastructure.authz.predicates import register_predicate

    def cliente_nao_bloqueado(resource: dict) -> tuple[bool, str]:
        cliente_id = resource.get("cliente_id")
        if cliente_id is None:
            return True, ""
        ...

    register_predicate("cliente_nao_bloqueado", cliente_nao_bloqueado)

Como o provider consulta — extensao em DjangoAuthorizationProvider._decidir():
    pra cada predicate registrado, chama. Primeiro denied curto-circuita.
"""

from __future__ import annotations

from typing import Any, Callable


PredicateFn = Callable[[dict[str, Any]], tuple[bool, str]]

_REGISTRY: dict[str, PredicateFn] = {}


def register_predicate(nome: str, fn: PredicateFn) -> None:
    """Registra um predicate. Reregistrar com mesmo nome substitui."""
    _REGISTRY[nome] = fn


def get_predicates() -> dict[str, PredicateFn]:
    """Retorna copia do registry (read-only)."""
    return dict(_REGISTRY)


def clear_registry() -> None:
    """Limpa registry — uso APENAS em testes."""
    _REGISTRY.clear()
