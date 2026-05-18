"""DRF ViewSet do modulo Clientes — Wave A · Marco 1 (US-CLI-001 completa).

Toda decisao de autorizacao passa por AuthorizationProvider.can() via
`RequireAuthz` (registrada em DEFAULT_PERMISSION_CLASSES). Declarar
`authz_action` na view eh obrigatorio.

INV-AUTHZ-001: o hook authz-check.sh valida em pre-commit.
INV-TENANT-001: queryset SEMPRE filtra por active_tenant (RLS faz a defesa
no banco, mas filtramos no ORM tambem — defesa em profundidade).
"""

from __future__ import annotations

import hashlib

from rest_framework import status, viewsets
from rest_framework.response import Response

from src.infrastructure.clientes.models import Cliente
from src.infrastructure.clientes.serializers import ClienteSerializer
from src.infrastructure.multitenant.context import active_tenant_context


def _hashear_ip(request) -> str:  # type: ignore[no-untyped-def]
    """SHA-256 do IP do request (LGPD — nao armazena IP cru)."""
    ip = (
        request.META.get("HTTP_X_FORWARDED_FOR", "").split(",")[0].strip()
        or request.META.get("REMOTE_ADDR", "")
    )
    if not ip:
        return ""
    return hashlib.sha256(ip.encode("utf-8")).hexdigest()


def _hashear_doc(documento: str) -> str:
    """SHA-256 do documento — pra gravar em audit sem PII cru (TL3)."""
    return hashlib.sha256(documento.encode("utf-8")).hexdigest()


class ClienteViewSet(viewsets.ModelViewSet):
    """CRUD de Cliente — autorizado por `RequireAuthz`."""

    serializer_class = ClienteSerializer
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
        action = getattr(self, "action", None)
        return self.ACTION_MAP.get(action) if action else None

    def get_authz_resource(self, request):  # type: ignore[no-untyped-def]
        return {}

    def get_queryset(self):  # type: ignore[no-untyped-def]
        active = active_tenant_context.get()
        if active is None:
            return Cliente.objects.none()
        return Cliente.objects.filter(tenant_id=active)

    def create(self, request, *args, **kwargs):  # type: ignore[no-untyped-def]
        """POST /clientes/ — dedup cross-tenant safe + 409 estruturada (TL1).

        Detectamos duplicata via QUERYSET FILTRADO POR active_tenant — nunca via
        IntegrityError (que poderia vazar existencia cross-tenant). 409 retorna
        link pro cliente existente DENTRO do mesmo tenant.
        """
        active = active_tenant_context.get()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        tipo = serializer.validated_data["tipo_pessoa"]
        documento = serializer.validated_data["documento"]
        existente = Cliente.objects.filter(
            tenant_id=active, tipo_pessoa=tipo, documento=documento
        ).first()
        if existente is not None:
            return Response(
                {
                    "detail": "cliente_ja_existe",
                    "cliente_id": str(existente.id),
                    "link": f"/api/v1/clientes/{existente.id}/",
                },
                status=status.HTTP_409_CONFLICT,
            )

        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data, status=status.HTTP_201_CREATED, headers=headers
        )

    def perform_create(self, serializer) -> None:  # type: ignore[no-untyped-def]
        """Cria cliente + grava audit `cliente.criado` sem PII cru (TL3).

        Audit fica em `auditoria` (F-A) como event-as-audit-trail enquanto
        eventbus formal (Procrastinate) nao existe. Quando bus existir, vira
        publicacao adicional — audit fica.
        """
        from src.infrastructure.audit.services import registrar_auditoria
        from src.infrastructure.tenant.models import Tenant

        active = active_tenant_context.get()
        tenant = Tenant.objects.filter(id=active).get()

        # Injeta IP hash + tenant
        ip_hash = _hashear_ip(self.request)  # type: ignore[attr-defined]
        cliente = serializer.save(tenant=tenant, aceite_lgpd_ip_hash=ip_hash)

        # Audit `cliente.criado` — sem PII cru
        from src.infrastructure.multitenant.context import usuario_id_context

        usuario_id = usuario_id_context.get()
        registrar_auditoria(
            tenant_id=tenant.id,
            usuario_id=usuario_id,
            action="cliente.criado",
            resource_summary=str(cliente.id),
            payload={
                "cliente_id": str(cliente.id),
                "tipo_pessoa": cliente.tipo_pessoa,
                "documento_hash": _hashear_doc(cliente.documento),
                "aceite_lgpd_versao": cliente.aceite_lgpd_versao or None,
                "aceite_lgpd_origem": cliente.aceite_lgpd_origem or None,
            },
        )
