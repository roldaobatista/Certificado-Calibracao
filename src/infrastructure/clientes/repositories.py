"""Adapter Django do `ClienteRepository` (ADR-0007).

Implementa o Protocol `src.domain.comercial.clientes.repository.ClienteRepository`
sobre Django ORM. View injeta este adapter no use case.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from src.domain.comercial.clientes.repository import ClienteSnapshot
from src.infrastructure.clientes.models import Cliente


def _to_snapshot(c: Cliente) -> ClienteSnapshot:
    return ClienteSnapshot(
        id=c.id,
        tenant_id=c.tenant_id,
        tipo_pessoa=c.tipo_pessoa,
        documento=c.documento,
        nome=c.nome,
        nome_fantasia=c.nome_fantasia,
        email=c.email,
        telefone=c.telefone,
        aceite_lgpd_em=c.aceite_lgpd_em,
        aceite_lgpd_versao=c.aceite_lgpd_versao,
        aceite_lgpd_ip_hash=c.aceite_lgpd_ip_hash,
        aceite_lgpd_origem=c.aceite_lgpd_origem,
        aceite_lgpd_dispensa_motivo=c.aceite_lgpd_dispensa_motivo,
        deletado_em=c.deletado_em,
    )


class DjangoClienteRepository:
    """Implementa `ClienteRepository` Protocol sobre Django ORM."""

    # Campos do Cliente que aceitam sobrescritas em mesclagem.
    CAMPOS_SOBRESCRITAVEIS = frozenset(
        {
            "nome",
            "nome_fantasia",
            "email",
            "telefone",
        }
    )

    def get_by_id(
        self, cliente_id: UUID, *, incluir_deletados: bool = False
    ) -> ClienteSnapshot | None:
        qs = Cliente.all_objects if incluir_deletados else Cliente.objects
        # Mesclar precisa enxergar perdedor mesmo se ja soft-deleted (regra ja
        # bloqueia em use case), mas aqui o get_by_id sem flag preserva
        # comportamento default (so ativos). Use case pede com incluir_deletados=False;
        # validacao de "perdedor_ja_deletado" verifica snapshot.deletado_em.
        try:
            obj = qs.get(id=cliente_id)
        except Cliente.DoesNotExist:
            # Tenta com all_objects pra capturar perdedor recem soft-deleted (caso raro)
            if not incluir_deletados:
                try:
                    obj = Cliente.all_objects.get(id=cliente_id)
                except Cliente.DoesNotExist:
                    return None
            else:
                return None
        return _to_snapshot(obj)

    def aplicar_sobrescritas(
        self, cliente_id: UUID, sobrescritas: dict[str, Any]
    ) -> ClienteSnapshot:
        invalidos = set(sobrescritas) - self.CAMPOS_SOBRESCRITAVEIS
        if invalidos:
            raise ValueError(
                f"Campos nao-sobrescritaveis: {sorted(invalidos)}. "
                f"Validos: {sorted(self.CAMPOS_SOBRESCRITAVEIS)}"
            )
        # update() em vez de save() pra evitar trigger post_save indesejado
        Cliente.objects.filter(id=cliente_id).update(**sobrescritas)
        obj = Cliente.objects.get(id=cliente_id)
        return _to_snapshot(obj)

    def soft_delete(
        self,
        cliente_id: UUID,
        *,
        motivo_categoria: str,
        usuario_id: UUID | None,
        agora: datetime,
    ) -> ClienteSnapshot:
        Cliente.all_objects.filter(id=cliente_id).update(
            deletado_em=agora,
            deletado_por_usuario_id=usuario_id,
            deletado_motivo_categoria=motivo_categoria,
        )
        obj = Cliente.all_objects.get(id=cliente_id)
        return _to_snapshot(obj)
