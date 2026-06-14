"""Listagem + filtros OS — T-OS-086..087 (P-OS-T4 p95 ≤500ms).

- `listar_os`: filtros estado + cliente_id + equipamento_id + paginacao.
  T-OSME-035 (ADR-0082): filtro equipamento_id usa AtividadeDaOS — spec §7.
- `os_do_tecnico`: lista OSs cujo tecnico_executor_id de qualquer atividade
  bate com o user_id passado.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from src.domain.operacao.os.entities import OSSnapshot
from src.domain.operacao.os.repository import OSRepository


@dataclass(frozen=True, slots=True)
class OSItemListagem:
    os_id: UUID
    numero_os: int
    estado: str
    tipo_predominante: str
    cliente_id: UUID | None
    # ADR-0082 / D-OSME-2: NULL em OS multi-equipamento.
    # Use equipamentos_distintos para obter os equipamentos reais da OS.
    equipamento_id: UUID | None
    valor_total_atualizado: Decimal
    nao_conformidade_global: bool
    criada_em: datetime


def _to_item(o: OSSnapshot) -> OSItemListagem:
    return OSItemListagem(
        os_id=o.id,
        numero_os=o.numero_os,
        estado=o.estado.value,
        tipo_predominante=o.tipo_predominante,
        cliente_id=o.cliente_id,
        equipamento_id=o.equipamento_id,
        valor_total_atualizado=o.valor_total_atualizado,
        nao_conformidade_global=o.nao_conformidade_global,
        criada_em=o.criada_em,
    )


def listar_os(
    *,
    tenant_id: UUID,
    repository: OSRepository,
    estado: str | None = None,
    cliente_id: UUID | None = None,
    equipamento_id: UUID | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[OSItemListagem]:
    """Listagem paginada com filtros (T-OS-086)."""
    if limit < 1 or limit > 200:
        raise ValueError("limit deve estar entre 1 e 200")
    if offset < 0:
        raise ValueError("offset deve ser >= 0")
    snaps = repository.listar_os_por_tenant(
        tenant_id,
        estado=estado,
        cliente_id=cliente_id,
        equipamento_id=equipamento_id,
        limit=limit,
        offset=offset,
    )
    return [_to_item(s) for s in snaps]


def os_do_tecnico(
    *,
    tenant_id: UUID,
    tecnico_user_id: UUID,
    repository: OSRepository,
    limit: int = 50,
    offset: int = 0,
) -> list[OSItemListagem]:
    """Lista OSs do tecnico (qualquer atividade dele) — T-OS-087.

    JOIN unico via repository (ADR-0082 P9 — anti-N+1): 1 query, independente
    do numero de OSs do tenant. Substitui o loop antigo que fazia 1 query de
    atividades por OS.
    """
    snaps = repository.listar_os_por_tecnico_atividade(
        tenant_id,
        tecnico_user_id,
        limit=limit,
        offset=offset,
    )
    return [_to_item(s) for s in snaps]
