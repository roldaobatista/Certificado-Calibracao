"""Repository protocol pra Clientes — camada DOMINIO puro (ADR-0007).

NAO importar django.* nem psycopg. Aqui mora apenas o CONTRATO; a
implementacao concreta (adapter Django) vive em
`src/infrastructure/clientes/repositories.py`.

Use cases (`src/application/comercial/clientes/`) consomem este Protocol e
nunca conhecem Django.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Protocol, runtime_checkable
from uuid import UUID


@dataclass(frozen=True)
class ClienteSnapshot:
    """Snapshot de Cliente — DTO imutavel pra atravessar fronteiras de camada.

    Reflete o que o domain precisa saber. Adapter Django converte Model <-> Snapshot.
    """

    id: UUID
    tenant_id: UUID
    tipo_pessoa: str  # "PF" | "PJ"
    documento: str
    nome: str
    nome_fantasia: str
    email: str
    telefone: str
    aceite_lgpd_em: datetime | None
    aceite_lgpd_versao: str
    aceite_lgpd_ip_hash: str
    aceite_lgpd_origem: str
    aceite_lgpd_dispensa_motivo: str
    deletado_em: datetime | None


@runtime_checkable
class ClienteRepository(Protocol):
    """Contrato de persistencia do agregado Cliente.

    Use cases recebem isso via DI. Adapter Django (`DjangoClienteRepository`)
    implementa. Em Wave C+ pode haver adapter pra outro storage.
    """

    def get_by_id(
        self, cliente_id: UUID, *, incluir_deletados: bool = False
    ) -> ClienteSnapshot | None:
        """Busca por id. Soft-deleted retorna apenas se `incluir_deletados=True`."""
        ...

    def aplicar_sobrescritas(
        self, cliente_id: UUID, sobrescritas: dict[str, Any]
    ) -> ClienteSnapshot:
        """Aplica dict de campos no vencedor + retorna snapshot pos-update."""
        ...

    def soft_delete(
        self,
        cliente_id: UUID,
        *,
        motivo_categoria: str,
        usuario_id: UUID | None,
        agora: datetime,
    ) -> ClienteSnapshot:
        """Marca cliente como soft-deleted; retorna snapshot pos-delete."""
        ...
