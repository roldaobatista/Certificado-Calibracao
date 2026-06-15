"""Use cases de Template de orçamento — CRUD + gate selo RBC (T-ORC-039 / US-ORC-005).

Gate D-ORC-13: ``selo_rbc=True`` só é permitido em tenant perfil A (ADR-0067 /
matriz feature×perfil). O perfil é resolvido server-side pela VIEW e passado aqui —
NUNCA vem do payload (mesmo molde de ``aprovar_orcamento`` / AJUSTE-3). Perfil
indeterminado com ``selo_rbc=True`` → fail-closed (``PerfilIndeterminado``).

Caller (view) abre ``transaction.atomic``. Refs: spec §D-ORC-13; AC-ORC-005;
INV-ORC-SELO-RBC.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from src.application.comercial.orcamentos.ciclo_vida import OrcamentoNaoEncontrado
from src.domain.comercial.orcamentos.entities import Template
from src.domain.comercial.orcamentos.erros import (
    PerfilIndeterminado,
    SeloRbcNaoPermitido,
)
from src.domain.comercial.orcamentos.repository import TemplateRepository

_PERFIS_VALIDOS = frozenset({"A", "B", "C", "D"})


def validar_selo_rbc_permitido(*, perfil: str, selo_rbc: bool) -> None:
    """Gate D-ORC-13: ``selo_rbc=True`` exige perfil A (server-side). Fail-closed.

    - ``selo_rbc=False`` → sempre permitido (qualquer perfil).
    - ``selo_rbc=True`` + perfil vazio/indeterminado → ``PerfilIndeterminado``.
    - ``selo_rbc=True`` + perfil ≠ A → ``SeloRbcNaoPermitido`` (422).
    - ``selo_rbc=True`` + perfil A → permitido.
    """
    if not selo_rbc:
        return
    perfil_norm = (perfil or "").strip().upper()
    if perfil_norm not in _PERFIS_VALIDOS:
        raise PerfilIndeterminado(
            "perfil regulatório indeterminado — selo RBC não pode ser concedido (D-ORC-13).",
            perfil=perfil_norm,
        )
    if perfil_norm != "A":
        raise SeloRbcNaoPermitido(
            f"template com selo RBC só é permitido em tenant perfil A "
            f"(perfil atual: {perfil_norm}) — D-ORC-13.",
        )


@dataclass(frozen=True, slots=True)
class CriarTemplateInput:
    """Entrada de ``criar_template`` — ``perfil`` resolvido server-side pela view."""

    tenant_id: UUID
    criado_por: UUID
    perfil: str
    nome: str
    tipo: str
    agora: datetime
    selo_rbc: bool = False
    itens_default: Sequence[dict[str, Any]] = field(default_factory=list)
    condicoes_default: dict[str, Any] = field(default_factory=dict)


def criar_template(inp: CriarTemplateInput, *, repo: TemplateRepository) -> Template:
    """Cria um template (gate selo RBC perfil A — D-ORC-13)."""
    validar_selo_rbc_permitido(perfil=inp.perfil, selo_rbc=inp.selo_rbc)
    template = Template(
        id=uuid4(),
        tenant_id=inp.tenant_id,
        nome=inp.nome,
        tipo=inp.tipo,
        itens_default=list(inp.itens_default),
        condicoes_default=dict(inp.condicoes_default),
        selo_rbc=inp.selo_rbc,
        criado_em=inp.agora,
        criado_por=inp.criado_por,
    )
    return repo.salvar(template)


@dataclass(frozen=True, slots=True)
class EditarTemplateInput:
    """Entrada de ``editar_template`` — substitui os campos editáveis."""

    tenant_id: UUID
    template_id: UUID
    perfil: str
    nome: str
    tipo: str
    selo_rbc: bool = False
    itens_default: Sequence[dict[str, Any]] = field(default_factory=list)
    condicoes_default: dict[str, Any] = field(default_factory=dict)


def editar_template(inp: EditarTemplateInput, *, repo: TemplateRepository) -> Template:
    """Edita um template (re-aplica o gate selo RBC — D-ORC-13).

    Preserva ``criado_em``/``criado_por`` (autoria original). 404 se inexistente
    neste tenant ou já soft-deletado.
    """
    atual = repo.get_by_id(inp.template_id, tenant_id=inp.tenant_id)
    if atual is None:
        raise OrcamentoNaoEncontrado(
            f"template {inp.template_id} inexistente neste tenant.",
            orcamento_id=str(inp.template_id),
        )
    validar_selo_rbc_permitido(perfil=inp.perfil, selo_rbc=inp.selo_rbc)
    atualizado = Template(
        id=atual.id,
        tenant_id=atual.tenant_id,
        nome=inp.nome,
        tipo=inp.tipo,
        itens_default=list(inp.itens_default),
        condicoes_default=dict(inp.condicoes_default),
        selo_rbc=inp.selo_rbc,
        criado_em=atual.criado_em,
        criado_por=atual.criado_por,
    )
    return repo.salvar(atualizado)


def remover_template(
    template_id: UUID,
    *,
    tenant_id: UUID,
    removido_por: UUID,
    agora: datetime,
    repo: TemplateRepository,
) -> Template:
    """Soft-delete (Padrão C) de um template. 404 se inexistente/já removido."""
    atual = repo.get_by_id(template_id, tenant_id=tenant_id)
    if atual is None:
        raise OrcamentoNaoEncontrado(
            f"template {template_id} inexistente neste tenant.",
            orcamento_id=str(template_id),
        )
    return repo.soft_delete(
        template_id, tenant_id=tenant_id, deletado_por=removido_por, deletado_em=agora
    )
