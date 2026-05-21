"""DRF views Marco 2 — Equipamento (T-EQP-002 etiqueta PDF).

# authz-check: skip -- RequireAuthz global (DEFAULT_PERMISSION_CLASSES)
# resolve via ACTION_MAP — mesmo pattern de clientes/views.py.

Esta task entrega APENAS o endpoint POST `/equipamentos/{id}/etiqueta.pdf`.
CRUD pleno (POST /equipamentos/, PATCH versionado, transferir etc.) fica
para T-EQP-001-CRUD/T-EQP-003+. Por isso o ViewSet aqui e minimo:
list/retrieve + action customizada `etiqueta`.

Autorizacao via RequireAuthz (DEFAULT_PERMISSION_CLASSES) + ACTION_MAP:
- `equipamentos.ler` para list/retrieve
- `equipamentos.imprimir_etiqueta` para POST etiqueta.pdf (perfil diferente
  de "ler" — gera artefato fisico)

Multi-tenant (defesa em profundidade ADR-0002):
- queryset filtrado por `active_tenant_context` no ORM
- RLS no banco (POLICY equipamentos_tenant_isolation_*) bloqueia se ORM
  filter for esquecido — falha duro (RLS=FORCE)

Cache 60s (AC-EQP-001-2): `Cache-Control: private, max-age=60` no response.
Cache PRIVATE porque etiqueta tem nome_fantasia do tenant e e por-equipamento.
"""

from __future__ import annotations

from uuid import UUID

from django.http import HttpResponse
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.request import Request
from rest_framework.response import Response

from src.infrastructure.multitenant.context import active_tenant_context

from .models import Equipamento
from .serializers import EquipamentoLeituraSerializer
from .services_etiqueta import gerar_etiqueta_pdf


def _active_tenant_obrigatorio() -> UUID:
    """Falsafe pro middleware — `PermissionDenied` se nao houver tenant ativo."""
    active = active_tenant_context.get()
    if active is None:
        raise PermissionDenied("tenant_nao_resolvido")
    return active


class EquipamentoViewSet(viewsets.ReadOnlyModelViewSet):
    """ReadOnly + action `etiqueta` — CRUD pleno em T-EQP futuras."""

    serializer_class = EquipamentoLeituraSerializer
    queryset = Equipamento.objects.none()
    authz_purpose = "execucao_contrato"
    lookup_field = "id"
    lookup_value_regex = r"[0-9a-f-]{36}"

    ACTION_MAP = {
        "list": "equipamentos.ler",
        "retrieve": "equipamentos.ler",
        "etiqueta": "equipamentos.imprimir_etiqueta",
    }

    def get_authz_action(self, request) -> str | None:
        action_name = getattr(self, "action", None)
        return self.ACTION_MAP.get(action_name) if action_name else None

    def get_authz_resource(self, request):
        return {}

    def get_queryset(self):
        active = _active_tenant_obrigatorio()
        return Equipamento.objects.filter(tenant_id=active)

    @action(detail=True, methods=["post"], url_path="etiqueta.pdf")
    def etiqueta(self, request: Request, id: str | None = None) -> Response | HttpResponse:
        """POST `/equipamentos/{id}/etiqueta.pdf` — gera/retorna PDF.

        Idempotente: chamadas repetidas reusam o QRCode vigente (UNIQUE
        no hash); cada chamada renderiza PDF fresco (cache HTTP 60s
        encurta esse custo em UI).
        """
        equipamento = self.get_object()
        pdf_bytes = gerar_etiqueta_pdf(equipamento)
        response = HttpResponse(
            pdf_bytes, content_type="application/pdf", status=status.HTTP_200_OK
        )
        response["Content-Disposition"] = f'inline; filename="etiqueta-{equipamento.tag}.pdf"'
        # AC-EQP-001-2: cache 60s, PRIVATE (tem nome_fantasia do tenant).
        response["Cache-Control"] = "private, max-age=60"
        return response
