"""Use case: mesclar 2 cadastros de cliente (US-CLI-005).

Camada APPLICATION. Recebe Repository (Protocol do domain) via DI. NUNCA
importa Django nem PG. Adapter concreto fica em
`src/infrastructure/clientes/repositories.py`.

Fluxo:
1. Buscar vencedor e perdedor pelo Repository.
2. Validar:
   - ambos existem
   - ambos no MESMO tenant (defesa em profundidade — TL5)
   - perdedor nao soft-deleted ja
3. Aplicar sobrescritas no vencedor (campos escolhidos pelo atendente).
4. Soft-delete do perdedor.
5. Devolver resultado pra view publicar audit (TL2 contrato evento).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID

from src.domain.comercial.clientes.repository import (
    ClienteRepository,
    ClienteSnapshot,
)


class ErroMesclagem(Exception):
    """Erro de regra de negocio na mesclagem."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class ResultadoMesclagem:
    """O que a view precisa pra responder + auditar."""

    vencedor: ClienteSnapshot
    perdedor: ClienteSnapshot
    campos_sobrescritos_keys: tuple[str, ...]
    motivo_categoria: str
    mesclado_em: datetime


def mesclar_clientes(
    *,
    repository: ClienteRepository,
    vencedor_id: UUID,
    perdedor_id: UUID,
    sobrescritas: dict[str, Any],
    motivo_categoria: str,
    usuario_id: UUID | None,
    agora: datetime,
) -> ResultadoMesclagem:
    """Mescla 2 clientes. Soft-delete do perdedor.

    Sem efeito colateral fora do Repository. A view e responsavel por:
    - envolver a chamada em transaction.atomic() (TL6)
    - publicar audit `cliente.mesclado` (TL2)
    - retornar HTTP response

    Levanta ErroMesclagem em caso de regra violada.
    """
    if vencedor_id == perdedor_id:
        raise ErroMesclagem(
            "mesma_entidade", "Vencedor e perdedor sao o mesmo cliente."
        )

    vencedor = repository.get_by_id(vencedor_id)
    if vencedor is None:
        raise ErroMesclagem("vencedor_nao_encontrado", "Cliente vencedor nao existe.")

    perdedor = repository.get_by_id(perdedor_id)
    if perdedor is None:
        raise ErroMesclagem("perdedor_nao_encontrado", "Cliente perdedor nao existe.")

    # Defesa em profundidade (TL5): RLS ja filtra, mas validamos no use case.
    if vencedor.tenant_id != perdedor.tenant_id:
        raise ErroMesclagem(
            "tenants_diferentes",
            "Vencedor e perdedor estao em tenants diferentes — operacao bloqueada.",
        )

    if perdedor.deletado_em is not None:
        raise ErroMesclagem(
            "perdedor_ja_deletado", "Perdedor ja esta soft-deleted."
        )

    campos_sobrescritos_keys: tuple[str, ...] = tuple(sorted(sobrescritas.keys()))
    vencedor_pos = (
        repository.aplicar_sobrescritas(vencedor_id, sobrescritas)
        if sobrescritas
        else vencedor
    )
    perdedor_pos = repository.soft_delete(
        perdedor_id,
        motivo_categoria=motivo_categoria,
        usuario_id=usuario_id,
        agora=agora,
    )

    return ResultadoMesclagem(
        vencedor=vencedor_pos,
        perdedor=perdedor_pos,
        campos_sobrescritos_keys=campos_sobrescritos_keys,
        motivo_categoria=motivo_categoria,
        mesclado_em=agora,
    )
