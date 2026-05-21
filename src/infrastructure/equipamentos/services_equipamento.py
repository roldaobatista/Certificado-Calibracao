"""Service de dominio do Equipamento (T-EQP-005 + T-EQP-007).

`criar_equipamento`: orquestra criacao + publica `equipamento.criado`
no bus_outbox. Idempotency-Key (T-EQP-003) e responsabilidade do viewset
(antes de chamar este service).

Eventos publicados:
- `equipamento.criado` (T-EQP-007 / AC-EQP-001-6): payload sanitizado
  com tag_hash, numero_serie_hash, cliente_atual_id_hash (HMAC).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from uuid import UUID, uuid4

from django.db import IntegrityError, transaction

from src.infrastructure.audit.event_helpers import publicar_evento
from src.infrastructure.audit.services import hashear_pii_com_salt_tenant

from .models import Equipamento


class TagDuplicada(Exception):
    """INV-049: TAG ja existe no tenant entre equipamentos vivos."""

    def __init__(self, tag: str, equipamento_id_existente: UUID) -> None:
        super().__init__(
            f"INV-049: TAG '{tag}' ja existe neste tenant "
            f"(equipamento {equipamento_id_existente})."
        )
        self.tag = tag
        self.equipamento_id_existente = equipamento_id_existente


@dataclass(frozen=True)
class DadosCriacaoEquipamento:
    """Payload de criacao agnostico de HTTP."""

    tag: str
    numero_serie: str
    fabricante: str
    modelo: str
    localizacao_fisica: str = ""
    cliente_atual_id: UUID | None = None
    perfil_tenant_snapshot: dict[str, Any] | None = None
    snapshot_schema_version: str = "1.0.0"


def criar_equipamento(
    *,
    tenant_id: UUID,
    criado_por_id: UUID,
    dados: DadosCriacaoEquipamento,
    causation_id: UUID | None = None,
) -> Equipamento:
    """Cria equipamento + publica `equipamento.criado`.

    UNIQUE parcial `(tenant, tag) WHERE deletado_em IS NULL` cravada em
    PG; IntegrityError vira `TagDuplicada` com referencia ao existente.
    """
    causation_id = causation_id or uuid4()
    with transaction.atomic():
        # Savepoint pra capturar UNIQUE violation sem invalidar a transacao
        # externa (queremos consultar `existente` ainda dentro do contexto).
        try:
            with transaction.atomic():
                equipamento = Equipamento.objects.create(
                    tenant_id=tenant_id,
                    tag=dados.tag.strip(),
                    numero_serie=dados.numero_serie.strip(),
                    fabricante=dados.fabricante.strip(),
                    modelo=dados.modelo.strip(),
                    cliente_atual_id=dados.cliente_atual_id,
                    localizacao_fisica=dados.localizacao_fisica.strip(),
                    perfil_tenant_snapshot=dados.perfil_tenant_snapshot or {},
                    snapshot_schema_version=dados.snapshot_schema_version,
                )
        except IntegrityError as exc:
            if "uq_equipamentos_tag_por_tenant_ativos" in str(exc):
                existente = (
                    Equipamento.objects.filter(
                        tenant_id=tenant_id,
                        tag=dados.tag.strip(),
                        deletado_em__isnull=True,
                    )
                    .only("id")
                    .first()
                )
                raise TagDuplicada(
                    tag=dados.tag.strip(),
                    equipamento_id_existente=existente.id if existente else uuid4(),
                ) from exc
            raise

        # AC-EQP-001-6: evento `equipamento.criado` com payload sanitizado.
        publicar_evento(
            acao="equipamento.criado",
            tenant_id=tenant_id,
            usuario_id=criado_por_id,
            causation_id=causation_id,
            payload={
                "tenant_id": str(tenant_id),
                "equipamento_id": str(equipamento.id),
                "tag_hash": hashear_pii_com_salt_tenant(dados.tag.strip(), tenant_id),
                "numero_serie_hash": hashear_pii_com_salt_tenant(
                    dados.numero_serie.strip(), tenant_id
                ),
                "cliente_atual_id_hash": (
                    hashear_pii_com_salt_tenant(str(dados.cliente_atual_id), tenant_id)
                    if dados.cliente_atual_id
                    else None
                ),
                "snapshot_schema_version": dados.snapshot_schema_version,
                "criado_em": equipamento.criado_em.isoformat(),
            },
            resource_summary=f"equipamento:{equipamento.id}",
        )
    return equipamento
