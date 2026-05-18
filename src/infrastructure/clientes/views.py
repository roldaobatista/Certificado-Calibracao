"""DRF ViewSet do modulo Clientes — Wave A · Marco 1.

Toda decisao de autorizacao passa por AuthorizationProvider.can() via
`RequireAuthz` (registrada em DEFAULT_PERMISSION_CLASSES). Declarar
`authz_action` na view eh obrigatorio.

INV-AUTHZ-001: o hook authz-check.sh valida em pre-commit.
INV-TENANT-001: queryset SEMPRE filtra por active_tenant (RLS faz a defesa
no banco, mas filtramos no ORM tambem — defesa em profundidade).
"""

from __future__ import annotations

from rest_framework import viewsets

from src.infrastructure.clientes.models import Cliente
from src.infrastructure.clientes.serializers import ClienteSerializer
from src.infrastructure.multitenant.context import active_tenant_context


class ClienteViewSet(viewsets.ModelViewSet):
    """CRUD de Cliente — autorizado por `RequireAuthz`.

    `authz_action` resolvido por metodo HTTP:
      GET list/retrieve -> clientes.ler
      POST              -> clientes.criar
      PUT/PATCH         -> clientes.atualizar
      DELETE            -> clientes.deletar
    """

    serializer_class = ClienteSerializer
    # queryset default vazio — get_queryset filtra por tenant_id (INV-TENANT-001)
    queryset = Cliente.objects.none()
    authz_purpose = "execucao_contrato"

    ACTION_MAP = {
        "list": "clientes.ler",
        "retrieve": "clientes.ler",
        "create": "clientes.criar",
        "update": "clientes.atualizar",
        "partial_update": "clientes.atualizar",
        "destroy": "clientes.deletar",
    }

    def get_authz_action(self, request) -> str | None:  # type: ignore[no-untyped-def]
        """Chamada pela permission RequireAuthz — INV-AUTHZ-001."""
        action = getattr(self, "action", None)
        return self.ACTION_MAP.get(action) if action else None

    def get_authz_resource(self, request):  # type: ignore[no-untyped-def]
        """ABAC payload — F-B vazio; Wave A enriquece quando precisar."""
        return {}

    def get_queryset(self):  # type: ignore[no-untyped-def]
        """Filtro explicito por active_tenant — defesa em profundidade alem da RLS."""
        active = active_tenant_context.get()
        if active is None:
            return Cliente.objects.none()
        return Cliente.objects.filter(tenant_id=active)

    def perform_create(self, serializer) -> None:  # type: ignore[no-untyped-def]
        # Tenant vem do contexto, NUNCA do payload — INV-TENANT-001.
        active = active_tenant_context.get()
        # Tenant deve existir; middleware ja garantiu.
        from src.infrastructure.tenant.models import Tenant

        serializer.save(tenant=Tenant.objects.filter(id=active).get())
