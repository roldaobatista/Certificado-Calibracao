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
from datetime import datetime, timezone
from uuid import UUID, uuid4 as uuid_module_uuid4

from django.db import transaction
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from src.application.comercial.clientes.mesclar_clientes import (
    ErroMesclagem,
    mesclar_clientes,
)
from src.infrastructure.clientes.mesclagem import (
    MOTIVOS_VALIDOS,
    validar_observacao,
)
from src.infrastructure.clientes.models import Cliente
from src.infrastructure.clientes.repositories import DjangoClienteRepository
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
        "mesclar": "clientes.mesclar",  # US-CLI-005
        "bloquear": "clientes.bloquear",  # US-CLI-004
        "desbloquear": "clientes.desbloquear",  # US-CLI-004
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

    # =============================================================
    # US-CLI-005 — mesclar 2 clientes (dedup manual)
    # authz-check: skip -- RequireAuthz global resolve via ACTION_MAP["mesclar"]="clientes.mesclar"
    # =============================================================
    @action(detail=True, methods=["post"], url_path=r"mesclar/(?P<perdedor_id>[^/.]+)")
    def mesclar(self, request, pk=None, perdedor_id=None):  # type: ignore[no-untyped-def]
        """Mescla `perdedor_id` em `pk` (vencedor). Soft-delete do perdedor."""
        from src.infrastructure.audit.services import registrar_auditoria
        from src.infrastructure.multitenant.context import usuario_id_context

        sobrescritas = request.data.get("sobrescrever") or {}
        motivo_categoria = request.data.get("motivo_categoria") or ""
        motivo_observacao = request.data.get("motivo_observacao") or ""

        if motivo_categoria not in MOTIVOS_VALIDOS:
            return Response(
                {
                    "detail": "motivo_categoria_invalido",
                    "validos": list(MOTIVOS_VALIDOS),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        if motivo_observacao:
            try:
                validar_observacao(motivo_observacao)
            except ValueError as e:
                return Response(
                    {"detail": "motivo_observacao_com_pii", "erro": str(e)},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        try:
            vencedor_uuid = UUID(str(pk))
            perdedor_uuid = UUID(str(perdedor_id))
        except (ValueError, TypeError):
            return Response(
                {"detail": "id_invalido"}, status=status.HTTP_400_BAD_REQUEST
            )

        repo = DjangoClienteRepository()
        usuario_id = usuario_id_context.get()
        agora = datetime.now(timezone.utc)
        active = active_tenant_context.get()

        try:
            with transaction.atomic():
                resultado = mesclar_clientes(
                    repository=repo,
                    vencedor_id=vencedor_uuid,
                    perdedor_id=perdedor_uuid,
                    sobrescritas=sobrescritas,
                    motivo_categoria=motivo_categoria,
                    usuario_id=usuario_id,
                    agora=agora,
                )
                obs_hash = (
                    hashlib.sha256(motivo_observacao.encode("utf-8")).hexdigest()
                    if motivo_observacao
                    else ""
                )
                registrar_auditoria(
                    tenant_id=active,
                    usuario_id=usuario_id,
                    action="cliente.mesclado",
                    resource_summary=str(resultado.vencedor.id),
                    payload={
                        "vencedor_id": str(resultado.vencedor.id),
                        "perdedor_id": str(resultado.perdedor.id),
                        "tenant_id": str(active) if active else None,
                        "mesclado_em": resultado.mesclado_em.isoformat(),
                        "campos_sobrescritos_keys": list(
                            resultado.campos_sobrescritos_keys
                        ),
                        "motivo_categoria": resultado.motivo_categoria,
                        "motivo_observacao_hash": obs_hash,
                        "usuario_id": str(usuario_id) if usuario_id else None,
                        "perdedor_documento_hash": _hashear_doc(
                            resultado.perdedor.documento
                        ),
                        "perdedor_nome_hash": hashlib.sha256(
                            resultado.perdedor.nome.encode("utf-8")
                        ).hexdigest(),
                    },
                )
        except ErroMesclagem as e:
            mapping = {
                "vencedor_nao_encontrado": status.HTTP_404_NOT_FOUND,
                "perdedor_nao_encontrado": status.HTTP_404_NOT_FOUND,
                "tenants_diferentes": status.HTTP_403_FORBIDDEN,
                "mesma_entidade": status.HTTP_400_BAD_REQUEST,
                "perdedor_ja_deletado": status.HTTP_409_CONFLICT,
            }
            return Response(
                {"detail": e.code, "erro": str(e)},
                status=mapping.get(e.code, status.HTTP_400_BAD_REQUEST),
            )

        return Response(
            {
                "vencedor_id": str(resultado.vencedor.id),
                "perdedor_id": str(resultado.perdedor.id),
                "mesclado_em": resultado.mesclado_em.isoformat(),
                "campos_sobrescritos_keys": list(
                    resultado.campos_sobrescritos_keys
                ),
            },
            status=status.HTTP_200_OK,
        )

    # =============================================================
    # US-CLI-004 — bloquear/desbloquear cliente
    # authz-check: skip -- RequireAuthz resolve via ACTION_MAP
    # =============================================================
    @action(detail=True, methods=["post"], url_path="bloquear")
    def bloquear(self, request, pk=None):  # type: ignore[no-untyped-def]
        """Bloqueia cliente. Idempotente: no-op se ja bloqueado."""
        from src.infrastructure.audit.services import registrar_auditoria
        from src.infrastructure.clientes.bloqueio import (
            CAUSATION_MANUAL_DECISAO_ADMIN,
            CAUSATION_TYPES_VALIDOS,
            JUSTIFICATIVA_MIN_CHARS,
            MOTIVOS_MANUAIS,
            MOTIVOS_VALIDOS,
        )
        from src.infrastructure.clientes.mesclagem import validar_observacao
        from src.infrastructure.clientes.models import (
            Cliente,
            ClienteBloqueio,
        )
        from src.infrastructure.multitenant.context import usuario_id_context
        from src.infrastructure.tenant.models import Tenant

        motivo_categoria = request.data.get("motivo_categoria") or ""
        justificativa = request.data.get("justificativa") or ""
        motivo_observacao = request.data.get("motivo_observacao") or ""
        confirmacao = bool(request.data.get("confirmacao_comunicacao_previa"))
        causation_type = request.data.get("causation_type") or CAUSATION_MANUAL_DECISAO_ADMIN
        causation_id_raw = request.data.get("causation_id")

        if motivo_categoria not in MOTIVOS_VALIDOS:
            return Response(
                {
                    "detail": "motivo_categoria_invalido",
                    "validos": list(MOTIVOS_VALIDOS),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        if motivo_categoria in MOTIVOS_MANUAIS and not confirmacao:
            return Response(
                {
                    "detail": "comunicacao_previa_obrigatoria",
                    "hint": (
                        "Bloqueio manual exige confirmacao_comunicacao_previa=True "
                        "(CDC art. 6 III/IV + Lei 14.181/2021 — R3 advogado)."
                    ),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        if len(justificativa) < JUSTIFICATIVA_MIN_CHARS:
            return Response(
                {
                    "detail": "justificativa_muito_curta",
                    "minimo": JUSTIFICATIVA_MIN_CHARS,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        if motivo_observacao:
            try:
                validar_observacao(motivo_observacao)
            except ValueError as e:
                return Response(
                    {"detail": "motivo_observacao_com_pii", "erro": str(e)},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        if causation_type and causation_type not in CAUSATION_TYPES_VALIDOS:
            return Response(
                {
                    "detail": "causation_type_invalido",
                    "validos": list(CAUSATION_TYPES_VALIDOS),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        causation_id_uuid: UUID | None = None
        if causation_id_raw:
            try:
                causation_id_uuid = UUID(str(causation_id_raw))
            except (ValueError, TypeError):
                return Response(
                    {"detail": "causation_id_invalido"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        try:
            cliente_uuid = UUID(str(pk))
        except (ValueError, TypeError):
            return Response(
                {"detail": "id_invalido"}, status=status.HTTP_400_BAD_REQUEST
            )

        usuario_id = usuario_id_context.get()
        active = active_tenant_context.get()
        tenant = Tenant.objects.filter(id=active).get()

        try:
            cliente = Cliente.objects.get(id=cliente_uuid)
        except Cliente.DoesNotExist:
            return Response(
                {"detail": "cliente_nao_encontrado"},
                status=status.HTTP_404_NOT_FOUND,
            )

        with transaction.atomic():
            ativo = ClienteBloqueio.objects.filter(
                cliente=cliente, desbloqueado_em__isnull=True
            ).select_for_update().first()
            if ativo is not None:
                # TL3: idempotente — no-op
                return Response(
                    {
                        "ja_estava_bloqueado": True,
                        "bloqueio_atual_id": str(ativo.id),
                        "motivo_categoria": ativo.motivo_categoria,
                    },
                    status=status.HTTP_200_OK,
                )

            bloqueio = ClienteBloqueio.objects.create(
                cliente=cliente,
                tenant=tenant,
                motivo_categoria=motivo_categoria,
                motivo_observacao=motivo_observacao,
                justificativa_bruta=justificativa,
                causation_type=causation_type or "",
                causation_id=causation_id_uuid,
                confirmacao_comunicacao_previa=confirmacao,
                bloqueado_por_usuario_id=usuario_id,
            )
            # Audit `cliente.bloqueado` — sem PII cru (R1 advogado + TL6)
            justif_hash = hashlib.sha256(
                justificativa.encode("utf-8")
            ).hexdigest()
            registrar_auditoria(
                tenant_id=tenant.id,
                usuario_id=usuario_id,
                action="cliente.bloqueado",
                resource_summary=str(cliente.id),
                payload={
                    "event_id": str(uuid_module_uuid4()),
                    "cliente_id": str(cliente.id),
                    "tenant_id": str(tenant.id),
                    "bloqueio_id": str(bloqueio.id),
                    "motivo_categoria": motivo_categoria,
                    "justificativa_hash": justif_hash,
                    "causation_type": causation_type or None,
                    "causation_id": str(causation_id_uuid)
                    if causation_id_uuid
                    else None,
                    "usuario_id": str(usuario_id) if usuario_id else None,
                },
            )

        return Response(
            {
                "ja_estava_bloqueado": False,
                "bloqueio_atual_id": str(bloqueio.id),
                "motivo_categoria": bloqueio.motivo_categoria,
            },
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["post"], url_path="desbloquear")
    def desbloquear(self, request, pk=None):  # type: ignore[no-untyped-def]
        """Desbloqueia cliente. No-op se nao havia bloqueio ativo."""
        from src.infrastructure.audit.services import registrar_auditoria
        from src.infrastructure.clientes.models import Cliente, ClienteBloqueio
        from src.infrastructure.multitenant.context import usuario_id_context

        motivo = (request.data.get("motivo") or "").strip()
        if motivo:
            from src.infrastructure.clientes.mesclagem import validar_observacao

            try:
                validar_observacao(motivo)
            except ValueError as e:
                return Response(
                    {"detail": "motivo_com_pii", "erro": str(e)},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        try:
            cliente_uuid = UUID(str(pk))
        except (ValueError, TypeError):
            return Response(
                {"detail": "id_invalido"}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            cliente = Cliente.objects.get(id=cliente_uuid)
        except Cliente.DoesNotExist:
            return Response(
                {"detail": "cliente_nao_encontrado"},
                status=status.HTTP_404_NOT_FOUND,
            )

        usuario_id = usuario_id_context.get()
        active = active_tenant_context.get()
        agora = datetime.now(timezone.utc)

        with transaction.atomic():
            ativo = (
                ClienteBloqueio.objects.filter(
                    cliente=cliente, desbloqueado_em__isnull=True
                )
                .select_for_update()
                .first()
            )
            if ativo is None:
                return Response(
                    {"ja_estava_desbloqueado": True}, status=status.HTTP_200_OK
                )
            ativo.desbloqueado_em = agora
            ativo.desbloqueado_por_usuario_id = usuario_id
            ativo.desbloqueado_motivo = motivo
            ativo.save(
                update_fields=[
                    "desbloqueado_em",
                    "desbloqueado_por_usuario_id",
                    "desbloqueado_motivo",
                ]
            )
            registrar_auditoria(
                tenant_id=active,
                usuario_id=usuario_id,
                action="cliente.desbloqueado",
                resource_summary=str(cliente.id),
                payload={
                    "event_id": str(uuid_module_uuid4()),
                    "cliente_id": str(cliente.id),
                    "tenant_id": str(active) if active else None,
                    "bloqueio_id": str(ativo.id),
                    "motivo_hash": hashlib.sha256(motivo.encode("utf-8")).hexdigest()
                    if motivo
                    else "",
                    "usuario_id": str(usuario_id) if usuario_id else None,
                },
            )

        return Response(
            {
                "ja_estava_desbloqueado": False,
                "bloqueio_id_encerrado": str(ativo.id),
            },
            status=status.HTTP_200_OK,
        )
