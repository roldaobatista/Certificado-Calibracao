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

    register_predicate(
        "cliente_nao_bloqueado", cliente_nao_bloqueado,
        actions={"os.", "orcamento.", "orcamentos.", "agenda.",
                 "chamado.", "chamados.", "certificado."},
    )

Como o provider consulta — `_decidir` chama `predicates_aplicaveis(action)`
(só os do escopo da ação corrente). Primeiro denied curto-circuita.
Ação sem predicate aplicável ⇒ ABAC neutro (segue RBAC), nunca deny.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable


PredicateFn = Callable[[dict[str, Any]], tuple[bool, str]]


@dataclass(frozen=True)
class _Predicate:
    """Predicate + ESCOPO declarado (T-FB-01 / AC-FB-006-2).

    O escopo é propriedade do predicate (quem o escreve sabe a que
    ações se aplica) — não índice externo. `actions` aceita ação exata
    (`"os.criar"`) ou prefixo de módulo terminando em `.`
    (`"os."` casa `os.criar`, `os.ler`, ...).
    """

    nome: str
    fn: PredicateFn
    actions: frozenset[str]

    def aplica(self, action: str) -> bool:
        return any(
            action == a or (a.endswith(".") and action.startswith(a))
            for a in self.actions
        )


_REGISTRY: dict[str, _Predicate] = {}


def register_predicate(
    nome: str, fn: PredicateFn, *, actions: frozenset[str] | set[str] | None = None
) -> None:
    """Registra um predicate COM escopo. Reregistrar mesmo nome substitui.

    FB-A1/BLOQ-1: predicate sem escopo declarado é proibido — erro em
    **import-time** (registro roda em `AppConfig.ready`), nunca global
    cego em runtime (era o bug: predicate de `cliente.*` rodava em
    `os.criar`).
    """
    if not actions:
        raise ValueError(
            f"predicate {nome!r} registrado sem escopo (actions) — proibido "
            "predicate global cego (FB-A1/T-FB-01). Declare as ações/prefixos."
        )
    _REGISTRY[nome] = _Predicate(nome, fn, frozenset(actions))


def predicates_aplicaveis(action: str) -> list[_Predicate]:
    """Predicates cujo escopo casa `action` (binding — T-FB-01).

    Lista vazia ⇒ ABAC neutro para essa ação (segue RBAC); NÃO deny.
    """
    return [p for p in _REGISTRY.values() if p.aplica(action)]


def get_predicates() -> dict[str, _Predicate]:
    """Cópia read-only do registry (nome → _Predicate)."""
    return dict(_REGISTRY)


def clear_registry() -> None:
    """Limpa registry — uso APENAS em testes."""
    _REGISTRY.clear()
