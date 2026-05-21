"""DRF ViewSet do modulo Clientes — Wave A · Marco 1 (US-CLI-001 completa).

Toda decisao de autorizacao passa por AuthorizationProvider.can() via
`RequireAuthz` (registrada em DEFAULT_PERMISSION_CLASSES). Declarar
`authz_action` na view eh obrigatorio.

INV-AUTHZ-001: o hook authz-check.sh valida em pre-commit.
INV-TENANT-001: queryset SEMPRE filtra por active_tenant (RLS faz a defesa
no banco, mas filtramos no ORM tambem — defesa em profundidade).
"""

from __future__ import annotations

import contextlib
import hashlib
import hmac
from datetime import UTC, datetime
from uuid import UUID
from uuid import uuid4 as uuid_module_uuid4

from django.conf import settings
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

# T-CLI-112 (AC-CLI-005-3b — consultor-rbc §C): enum tipo_mesclagem
# obrigatório no POST mesclar. M&A_SOCIETARIO exige
# `evidencia_documental_id` (contrato social consolidado, ata JC,
# procuração) — defesa cível CC art. 1.116 + supervisão CGCRE.
TIPOS_MESCLAGEM_VALIDOS = frozenset({"DUPLICATA_OPERACIONAL", "M&A_SOCIETARIO"})


def _hashear_ip(request, tenant_id: UUID | str) -> str:
    """HMAC do IP do request por tenant (LGPD — nao armazena IP cru).

    IP eh PII LGPD e espaco IPv4 eh trivial pra rainbow table. SANEA-02:
    tenant_id obrigatorio (removido o default None — era brecha cross-tenant).
    """
    from src.infrastructure.audit.services import hashear_pii_com_salt_tenant

    ip = request.META.get("HTTP_X_FORWARDED_FOR", "").split(",")[0].strip() or request.META.get(
        "REMOTE_ADDR", ""
    )
    return hashear_pii_com_salt_tenant(ip, tenant_id)


def _hashear_doc(documento: str, tenant_id: UUID | str) -> str:
    """HMAC de CPF/CNPJ por tenant pra referenciar em audit sem o dado cru.

    SANEA-02: tenant_id obrigatorio (removido o default None — auditores
    Seguranca SEG-D5 / LGPD D5 / corretora R-CLI-05: hash sem tenant fica
    cross-tenant correlacionavel). Agora Marco 1 fechou — sem retrocompat.
    """
    from src.infrastructure.audit.services import hashear_pii_com_salt_tenant

    return hashear_pii_com_salt_tenant(documento, tenant_id)


def _hashear_pii(valor: str, tenant_id: UUID | str) -> str:
    """HMAC por tenant pra qualquer PII em audit (nome, email, etc)."""
    from src.infrastructure.audit.services import hashear_pii_com_salt_tenant

    return hashear_pii_com_salt_tenant(valor, tenant_id)


def _active_tenant_obrigatorio() -> UUID:
    """Retorna o tenant ativo ou levanta — defesa em profundidade ao middleware.

    O TenantMiddleware ja garante que endpoints protegidos so passam com
    active_tenant setado. Esta funcao eh failsafe: se chegar aqui sem tenant,
    eh bug ou bypass do middleware — preferimos crash explicito a query None.
    """
    from rest_framework.exceptions import PermissionDenied

    active_inner = active_tenant_context.get()
    if active_inner is None:
        raise PermissionDenied("tenant_nao_resolvido")
    return active_inner


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
        "visao_360": "clientes.visao360",  # US-CLI-002
        "importar_preview": "clientes.importar",  # US-CLI-003
        "importar_executar": "clientes.importar",  # US-CLI-003
        "importacoes": "clientes.importar",  # US-CLI-003 — listagem historico
        "revogar_consentimento": "clientes.atualizar",  # T-CLI-115 US-CLI-006
        "dedup_compare": "clientes.ler",  # T-CLI-111 — GET dedup comparison
    }

    def get_authz_action(self, request) -> str | None:
        action = getattr(self, "action", None)
        return self.ACTION_MAP.get(action) if action else None

    def get_authz_resource(self, request):
        return {}

    def get_queryset(self):
        active = _active_tenant_obrigatorio()
        if active is None:
            return Cliente.objects.none()
        return Cliente.objects.filter(tenant_id=active)

    def create(self, request, *args, **kwargs):
        """POST /clientes/ — dedup cross-tenant safe + 409 estruturada (TL1).

        Detectamos duplicata via QUERYSET FILTRADO POR active_tenant — nunca via
        IntegrityError (que poderia vazar existencia cross-tenant). 409 retorna
        link pro cliente existente DENTRO do mesmo tenant.
        """
        active = _active_tenant_obrigatorio()
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
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def perform_create(self, serializer) -> None:
        """Cria cliente + grava audit `cliente.criado` sem PII cru (TL3).

        Audit fica em `auditoria` (F-A) como event-as-audit-trail enquanto
        eventbus formal (Procrastinate) nao existe. Quando bus existir, vira
        publicacao adicional — audit fica.
        """
        from src.infrastructure.audit.services import registrar_auditoria
        from src.infrastructure.tenant.models import Tenant

        active = _active_tenant_obrigatorio()
        tenant = Tenant.objects.filter(id=active).get()

        # Injeta IP hash + tenant
        ip_hash = _hashear_ip(self.request, tenant.id)
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
                "documento_hash": _hashear_doc(cliente.documento, tenant.id),
                "aceite_lgpd_versao": cliente.aceite_lgpd_versao or None,
                "aceite_lgpd_origem": cliente.aceite_lgpd_origem or None,
            },
        )

    # =============================================================
    # US-CLI-005 — mesclar 2 clientes (dedup manual)
    # authz-check: skip -- RequireAuthz global resolve via ACTION_MAP["mesclar"]="clientes.mesclar"
    # =============================================================
    @action(detail=True, methods=["post"], url_path=r"mesclar/(?P<perdedor_id>[^/.]+)")
    def mesclar(self, request, pk=None, perdedor_id=None):
        """Mescla `perdedor_id` em `pk` (vencedor). Soft-delete do perdedor."""
        from src.infrastructure.audit.event_helpers import publicar_evento
        from src.infrastructure.multitenant.context import usuario_id_context

        sobrescritas = request.data.get("sobrescrever") or {}
        motivo_categoria = request.data.get("motivo_categoria") or ""
        motivo_observacao = request.data.get("motivo_observacao") or ""
        # T-CLI-112 (AC-CLI-005-3b — consultor-rbc §C)
        tipo_mesclagem = request.data.get("tipo_mesclagem") or ""
        evidencia_documental_id = request.data.get("evidencia_documental_id") or ""

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

        # T-CLI-112: tipo_mesclagem obrigatório + evidencia se M&A
        if tipo_mesclagem not in TIPOS_MESCLAGEM_VALIDOS:
            return Response(
                {
                    "detail": "tipo_mesclagem_invalido",
                    "validos": list(TIPOS_MESCLAGEM_VALIDOS),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        if tipo_mesclagem == "M&A_SOCIETARIO" and not evidencia_documental_id:
            return Response(
                {
                    "detail": "evidencia_documental_obrigatoria_em_ma",
                    "erro": "M&A_SOCIETARIO exige evidencia_documental_id "
                    "(contrato social/ata JC/procuração — CC art. 1.116 + CGCRE)",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            vencedor_uuid = UUID(str(pk))
            perdedor_uuid = UUID(str(perdedor_id))
        except (ValueError, TypeError):
            return Response({"detail": "id_invalido"}, status=status.HTTP_400_BAD_REQUEST)

        repo = DjangoClienteRepository()
        usuario_id = usuario_id_context.get()
        agora = datetime.now(UTC)
        active = _active_tenant_obrigatorio()

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
                obs_hash = _hashear_pii(motivo_observacao, active) if motivo_observacao else ""
                # T-CLI-112 + débito técnico: migra de registrar_auditoria
                # pra publicar_evento (helper único — SANEA-08).
                publicar_evento(
                    acao="cliente.mesclado",
                    payload={
                        "vencedor_id": str(resultado.vencedor.id),
                        "perdedor_id": str(resultado.perdedor.id),
                        "tenant_id": str(active) if active else None,
                        "mesclado_em": resultado.mesclado_em.isoformat(),
                        "campos_sobrescritos_keys": list(resultado.campos_sobrescritos_keys),
                        "motivo_categoria": resultado.motivo_categoria,
                        "motivo_observacao_hash": obs_hash,
                        # T-CLI-112: rastreabilidade ISO/IEC 17025 §7.8.2.1 (b)
                        "tipo_mesclagem": tipo_mesclagem,
                        "evidencia_documental_id": evidencia_documental_id or None,
                        "usuario_id": str(usuario_id) if usuario_id else None,
                        "perdedor_documento_hash": _hashear_doc(
                            resultado.perdedor.documento, active
                        ),
                        "perdedor_nome_hash": _hashear_pii(resultado.perdedor.nome, active),
                    },
                    causation_id=uuid_module_uuid4(),
                    tenant_id=active,
                    usuario_id=usuario_id,
                    resource_summary=str(resultado.vencedor.id),
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
                "campos_sobrescritos_keys": list(resultado.campos_sobrescritos_keys),
            },
            status=status.HTTP_200_OK,
        )

    # =============================================================
    # T-CLI-111 (AC-CLI-005-1) — GET dedup compare
    # GET /api/v1/clientes/{vencedor_id}/dedup/{perdedor_id}/
    # authz: AuthorizationProvider.can('clientes.ler') via
    # ACTION_MAP['dedup_compare'] — RequireAuthz aplica.
    # =============================================================
    @action(
        detail=True,
        methods=["get"],
        url_path=r"dedup/(?P<perdedor_id>[^/.]+)",
    )
    def dedup_compare(self, request, pk=None, perdedor_id=None):
        """Retorna comparação campo-a-campo de vencedor vs perdedor
        + contagens de entidades atreladas (OS, certificados, faturas,
        contatos — todas 0 em Marco 1; módulos Wave A).
        """
        try:
            vencedor_uuid = UUID(str(pk))
            perdedor_uuid = UUID(str(perdedor_id))
        except (ValueError, TypeError):
            return Response({"detail": "id_invalido"}, status=status.HTTP_400_BAD_REQUEST)

        active = _active_tenant_obrigatorio()
        # Conserto MÉDIO-1 SEC P5 (2026-05-21): defesa em profundidade —
        # filter por `tenant_id=active` no ORM além do RLS no banco.
        # Mesmo padrão das outras rotas (bloquear/desbloquear/visao_360/etc).
        try:
            vencedor = Cliente.objects.filter(tenant_id=active, id=vencedor_uuid).get()
        except Cliente.DoesNotExist:
            return Response(
                {"detail": "vencedor_nao_encontrado"},
                status=status.HTTP_404_NOT_FOUND,
            )
        try:
            perdedor = Cliente.objects.filter(tenant_id=active, id=perdedor_uuid).get()
        except Cliente.DoesNotExist:
            return Response(
                {"detail": "perdedor_nao_encontrado"},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Defesa em profundidade: confirma mesmo tenant via objeto
        # (RLS já filtra, mas tornamos explícito).
        if vencedor.tenant_id != perdedor.tenant_id:
            return Response({"detail": "tenants_diferentes"}, status=status.HTTP_403_FORBIDDEN)

        def _ladob_a_lado(campo: str) -> dict:
            return {
                "campo": campo,
                "vencedor": getattr(vencedor, campo) or None,
                "perdedor": getattr(perdedor, campo) or None,
            }

        campos = [
            "tipo_pessoa",
            "documento",
            "nome",
            "nome_fantasia",
            "email",
            "telefone",
            "data_nascimento",
            "observacao",
        ]
        # GATE-CLI-DEDUP-COUNTS Wave A: contagens reais quando módulos
        # OS/certificados/faturas/contatos existirem.
        contagens = {
            "os_atreladas": {"vencedor": 0, "perdedor": 0},
            "certificados_atrelados": {"vencedor": 0, "perdedor": 0},
            "faturas_atreladas": {"vencedor": 0, "perdedor": 0},
            "contatos_atrelados": {"vencedor": 0, "perdedor": 0},
        }
        _ = active  # silencia ruff (active validado pra trigger RLS)
        return Response(
            {
                "vencedor_id": str(vencedor.id),
                "perdedor_id": str(perdedor.id),
                "campos": [_ladob_a_lado(c) for c in campos],
                "contagens": contagens,
                "gate_wave_a": "contagens reais quando módulos OS/cert/"
                "fatura/contatos existirem",
            },
            status=status.HTTP_200_OK,
        )

    # =============================================================
    # US-CLI-004 — bloquear/desbloquear cliente
    # authz-check: skip -- RequireAuthz resolve via ACTION_MAP
    # T-CLI-108: usa publicar_evento(outbox=True) — payload canônico
    # via montar_payload_cliente_bloqueado com slot agendamentos_futuros.
    # =============================================================
    @action(detail=True, methods=["post"], url_path="bloquear")
    def bloquear(self, request, pk=None):
        """Bloqueia cliente. Idempotente: no-op se ja bloqueado.

        # authz-check: skip -- RequireAuthz global aplica via ACTION_MAP["bloquear"]
        """
        from src.infrastructure.audit.event_helpers import publicar_evento
        from src.infrastructure.clientes.bloqueio import (
            CAUSATION_MANUAL_DECISAO_ADMIN,
            CAUSATION_TYPES_VALIDOS,
            JUSTIFICATIVA_MIN_CHARS,
            MOTIVOS_MANUAIS,
            MOTIVOS_VALIDOS,
            montar_payload_cliente_bloqueado,
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
            return Response({"detail": "id_invalido"}, status=status.HTTP_400_BAD_REQUEST)

        usuario_id = usuario_id_context.get()
        active = _active_tenant_obrigatorio()
        tenant = Tenant.objects.filter(id=active).get()

        # Conserto MÉDIO-1 SEC P5 (2026-05-21): defesa em profundidade — filter por tenant_id.
        try:
            cliente = Cliente.objects.filter(tenant_id=active, id=cliente_uuid).get()
        except Cliente.DoesNotExist:
            return Response(
                {"detail": "cliente_nao_encontrado"},
                status=status.HTTP_404_NOT_FOUND,
            )

        with transaction.atomic():
            ativo = (
                ClienteBloqueio.objects.filter(cliente=cliente, desbloqueado_em__isnull=True)
                .select_for_update()
                .first()
            )
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
            # T-CLI-108 + AC-CLI-004-7: publica via helper único com outbox transacional.
            # Payload canônico via montar_payload_cliente_bloqueado — inclui
            # `agendamentos_futuros` (slot pro consumer Wave A operacao/agenda — GATE-CLI-7).
            justif_hash = _hashear_pii(justificativa, tenant.id)
            payload_bloqueado = montar_payload_cliente_bloqueado(
                cliente_id=cliente.id,
                tenant_id=tenant.id,
                bloqueio_id=bloqueio.id,
                motivo_categoria=motivo_categoria,
                justificativa_hash=justif_hash,
                causation_type=causation_type or None,
                causation_id=causation_id_uuid,
                usuario_id=usuario_id,
            )
            publicar_evento(
                acao="cliente.bloqueado",
                payload=payload_bloqueado,
                causation_id=causation_id_uuid or UUID(payload_bloqueado["event_id"]),
                tenant_id=tenant.id,
                usuario_id=usuario_id,
                resource_summary=str(cliente.id),
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
    def desbloquear(self, request, pk=None):
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
            return Response({"detail": "id_invalido"}, status=status.HTTP_400_BAD_REQUEST)

        usuario_id = usuario_id_context.get()
        active = _active_tenant_obrigatorio()
        agora = datetime.now(UTC)

        # Conserto MÉDIO-1 SEC P5 (2026-05-21): defesa em profundidade — filter por tenant_id.
        try:
            cliente = Cliente.objects.filter(tenant_id=active, id=cliente_uuid).get()
        except Cliente.DoesNotExist:
            return Response(
                {"detail": "cliente_nao_encontrado"},
                status=status.HTTP_404_NOT_FOUND,
            )

        with transaction.atomic():
            ativo = (
                ClienteBloqueio.objects.filter(cliente=cliente, desbloqueado_em__isnull=True)
                .select_for_update()
                .first()
            )
            if ativo is None:
                return Response({"ja_estava_desbloqueado": True}, status=status.HTTP_200_OK)
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
                    "motivo_hash": _hashear_pii(motivo, active) if motivo else "",
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

    # =============================================================
    # US-CLI-002 — Visao 360 do cliente (AC-1 + AC-3 INV-013)
    # authz-check: skip -- RequireAuthz resolve via ACTION_MAP["visao_360"]="clientes.visao360"
    # =============================================================
    @action(detail=True, methods=["get"], url_path="visao-360")
    def visao_360(self, request, pk=None):
        """GET /clientes/{id}/visao-360/?finalidade=executar_os

        Registra acesso em `acessos_dados_cliente` ANTES de ler timeline (INV-013).
        Timeline le de `auditoria` filtrada por payload_jsonb->>'cliente_id'.
        """
        from src.infrastructure.audit.breaker import (
            registrar_acesso_dados_cliente_com_breaker,
        )
        from src.infrastructure.audit.models import (
            Auditoria,
            FinalidadeAcessoCliente,
        )
        from src.infrastructure.clientes.models import Cliente
        from src.infrastructure.multitenant.context import usuario_id_context

        finalidade = request.query_params.get("finalidade", "")
        if finalidade not in FinalidadeAcessoCliente.values:
            return Response(
                {
                    "detail": "finalidade_obrigatoria_e_enum",
                    "validas": list(FinalidadeAcessoCliente.values),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            cliente_uuid = UUID(str(pk))
        except (ValueError, TypeError):
            return Response({"detail": "id_invalido"}, status=status.HTTP_400_BAD_REQUEST)

        usuario_id = usuario_id_context.get()
        active = _active_tenant_obrigatorio()
        ip_hash = _hashear_ip(request, active)

        # Conserto MÉDIO-1 SEC P5 (2026-05-21): defesa em profundidade — filter por tenant_id.
        try:
            cliente = Cliente.objects.filter(tenant_id=active, id=cliente_uuid).get()
        except Cliente.DoesNotExist:
            return Response(
                {"detail": "cliente_nao_encontrado"},
                status=status.HTTP_404_NOT_FOUND,
            )

        # INV-013 — grava acesso ANTES de ler timeline.
        # T-CLI-104: wrapper com circuit breaker observado — grava evento
        # em conexão paralela autocommit (sobrevive rollback do request).
        registrar_acesso_dados_cliente_com_breaker(
            tenant_id=active,
            usuario_id=usuario_id,
            cliente_id=cliente.id,
            finalidade=finalidade,
            recurso={"cliente_id": str(cliente.id)},  # sem PII cru (R1 advogado)
            ip_hash=ip_hash,
        )

        # Timeline via auditoria filtrada pelo cliente_id no payload_jsonb (TL1).
        eventos = (
            Auditoria.objects.filter(
                tenant_id=active,
                payload_jsonb__cliente_id=str(cliente.id),
            )
            .order_by("-timestamp")
            .values("id", "action", "timestamp", "payload_jsonb")[:200]  # LIMIT 200 (TL5)
        )
        from src.infrastructure.audit.services import sanitizar_payload_audit

        items = [
            {
                "id": str(e["id"]),
                "action": e["action"],
                "timestamp": e["timestamp"].isoformat(),
                # Defesa em profundidade — se algum modulo gravou PII por
                # engano em audit, redact antes de devolver pra UI
                # (CONCERN Auditor Seguranca 2026-05-18 US-002 retroativa).
                "payload": sanitizar_payload_audit(e["payload_jsonb"]),
            }
            for e in eventos
        ]

        return Response(
            {
                "cliente_id": str(cliente.id),
                "eventos": items,
                "total_eventos_exibidos": len(items),
                "limite_aplicado": 200,
            },
            status=status.HTTP_200_OK,
        )

    # =============================================================
    # US-CLI-003 — importacao 1-clique CSV
    # authz-check: skip -- RequireAuthz resolve via ACTION_MAP["importar_*"]="clientes.importar"
    # =============================================================
    # authz-check: skip -- RequireAuthz global resolve via ACTION_MAP["importar_preview"]="clientes.importar"
    @action(
        detail=False,
        methods=["post"],
        url_path="importar-preview",
    )
    def importar_preview(self, request):
        """POST /clientes/importar-preview/ — devolve mapeamento sugerido + amostra."""
        from src.infrastructure.clientes.csv_io import (
            LIMITE_BYTES,
            ErroCsvIo,
            detectar_colunas_cpf_responsavel,
            detectar_colunas_sensiveis,
            ler_csv_normalizado,
            sugerir_mapeamento,
        )
        from src.infrastructure.clientes.serializers import (
            ImportarPreviewSerializer,
        )

        ser = ImportarPreviewSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        upload = ser.validated_data["arquivo"]

        ct = (getattr(upload, "content_type", "") or "").lower()
        if ct and ct not in {
            "text/csv",
            "application/csv",
            "application/vnd.ms-excel",
            "text/plain",
            "application/octet-stream",
        }:
            return Response(
                {"detail": "content_type_invalido", "content_type": ct},
                status=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            )

        # R3 advogado: garantir delete do tempfile em try/finally.
        arquivo_bytes = b""
        try:
            arquivo_bytes = upload.read()
            if len(arquivo_bytes) > LIMITE_BYTES:
                return Response(
                    {
                        "detail": "arquivo_excede_limite",
                        "limite_bytes": LIMITE_BYTES,
                    },
                    status=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                )
            try:
                norm = ler_csv_normalizado(arquivo_bytes)
            except ErroCsvIo as e:
                return Response(
                    {"detail": e.code, "erro": str(e)},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            mapeamento_sugerido = sugerir_mapeamento(norm.headers)
            sensiveis = detectar_colunas_sensiveis(norm.headers)
            cpf_resp = detectar_colunas_cpf_responsavel(norm.headers)
            arquivo_hash = hashlib.sha256(arquivo_bytes).hexdigest()
            amostra = [list(linha) for linha in norm.linhas[:10]]
            return Response(
                {
                    "delimitador_detectado": norm.delimitador,
                    "encoding_detectado": norm.encoding,
                    "linhas_amostra": amostra,
                    "headers_arquivo": list(norm.headers),
                    "mapeamento_sugerido": mapeamento_sugerido,
                    "campos_destino_disponiveis": [
                        "documento",
                        "nome",
                        "nome_fantasia",
                        "email",
                        "telefone",
                        "tipo_pessoa",
                    ],
                    "colunas_sensiveis_detectadas": list(sensiveis),
                    "colunas_cpf_responsavel_detectadas": list(cpf_resp),
                    "total_linhas": norm.total_linhas,
                    "arquivo_hash": arquivo_hash,
                },
                status=status.HTTP_200_OK,
            )
        finally:
            # Forca o Django a apagar tempfile (se houver) — defesa R3 advogado.
            with contextlib.suppress(Exception):
                upload.close()

    # authz-check: skip -- RequireAuthz global resolve via ACTION_MAP["importar_executar"]="clientes.importar"
    # `@transaction.non_atomic_requests` desativa ATOMIC_REQUESTS pra esta
    # view especifica — necessario pra que `repositories.bulk_upsert` consiga
    # setar `SET TRANSACTION ISOLATION LEVEL SERIALIZABLE` antes de iniciar
    # a transacao (R3 tech-lead resolvido 2026-05-18 noite final).
    @transaction.non_atomic_requests
    @action(
        detail=False,
        methods=["post"],
        url_path="importar-executar",
    )
    def importar_executar(self, request):
        """POST /clientes/importar-executar/ — cria/atualiza em lote + audit."""
        from src.application.comercial.clientes.importar_clientes import (
            ContextoImportacao,
            ErroImportacao,
            importar_clientes,
        )
        from src.infrastructure.audit.services import registrar_auditoria
        from src.infrastructure.clientes.csv_io import (
            LIMITE_BYTES,
            ErroCsvIo,
            detectar_colunas_cpf_responsavel,
            detectar_colunas_sensiveis,
            ler_csv_normalizado,
        )
        from src.infrastructure.clientes.lgpd import (
            PF_ACEITE_ORIGENS_VALIDAS,
            VERSAO_VIGENTE,
        )
        from src.infrastructure.clientes.models import (
            ClienteImportacaoDeclaracao,
        )
        from src.infrastructure.clientes.serializers import (
            ImportarExecutarSerializer,
        )
        from src.infrastructure.multitenant.context import usuario_id_context
        from src.infrastructure.tenant.models import Tenant

        ser = ImportarExecutarSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        upload = ser.validated_data["arquivo"]
        mapeamento = ser.validated_data["mapeamento"] or {}
        declaracao = ser.validated_data["declaracao"]
        pf_aceite_origem = (ser.validated_data.get("pf_aceite_origem") or "").strip()
        cpf_responsavel_destino = ser.validated_data["cpf_responsavel_destino"]
        skip_invalid = ser.validated_data["skip_invalid"]
        update_existing = ser.validated_data["update_existing"]

        if pf_aceite_origem and pf_aceite_origem not in PF_ACEITE_ORIGENS_VALIDAS:
            return Response(
                {
                    "detail": "pf_aceite_origem_invalido",
                    "validos": list(PF_ACEITE_ORIGENS_VALIDAS),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        ct = (getattr(upload, "content_type", "") or "").lower()
        if ct and ct not in {
            "text/csv",
            "application/csv",
            "application/vnd.ms-excel",
            "text/plain",
            "application/octet-stream",
        }:
            return Response(
                {"detail": "content_type_invalido", "content_type": ct},
                status=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            )

        active = _active_tenant_obrigatorio()
        if active is None:
            return Response(
                {"detail": "tenant_nao_resolvido"},
                status=status.HTTP_403_FORBIDDEN,
            )
        usuario_id = usuario_id_context.get()
        agora = datetime.now(UTC)
        tenant = Tenant.objects.filter(id=active).get()

        arquivo_bytes = b""
        try:
            arquivo_bytes = upload.read()
            if len(arquivo_bytes) > LIMITE_BYTES:
                return Response(
                    {
                        "detail": "arquivo_excede_limite",
                        "limite_bytes": LIMITE_BYTES,
                    },
                    status=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                )
            try:
                norm = ler_csv_normalizado(arquivo_bytes)
            except ErroCsvIo as e:
                return Response(
                    {"detail": e.code, "erro": str(e)},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            arquivo_hash = hashlib.sha256(arquivo_bytes).hexdigest()
            arquivo_nome_hash = hashlib.sha256((upload.name or "").encode("utf-8")).hexdigest()
            ip_hash = _hashear_ip(request, tenant.id)
            # SANEA-02: chave de hash da linha derivada da PII_HASH_KEY
            # (segredo de servidor) por tenant — NAO mais sha256 de string
            # com tenant.id (que e publico e reconstruivel).
            linha_hash_key = hmac.new(
                settings.PII_HASH_KEY_REGISTRO.chave_ativa(),
                f"import-linha:{tenant.id}".encode(),
                hashlib.sha256,
            ).hexdigest()

            sensiveis = detectar_colunas_sensiveis(norm.headers)
            cpf_resp = detectar_colunas_cpf_responsavel(norm.headers)

            contexto = ContextoImportacao(
                tenant_id=tenant.id,
                usuario_id=usuario_id,
                headers=norm.headers,
                linhas=norm.linhas,
                mapeamento={k: v for k, v in mapeamento.items() if isinstance(v, str)},
                declaracao_tem_base_legal=bool(declaracao["tem_base_legal"]),
                declaracao_compromisso_comunicar=bool(
                    declaracao["compromisso_comunicar_titulares"]
                ),
                declaracao_sem_sensiveis=bool(declaracao["declara_sem_dados_sensiveis"]),
                procedencia_declarada=declaracao["procedencia_declarada"],
                pf_aceite_origem=pf_aceite_origem,
                cpf_responsavel_destino=cpf_responsavel_destino,
                colunas_sensiveis=sensiveis,
                colunas_cpf_responsavel=cpf_resp,
                skip_invalid=skip_invalid,
                update_existing=update_existing,
                arquivo_hash=arquivo_hash,
                arquivo_tamanho_bytes=len(arquivo_bytes),
                arquivo_nome_hash=arquivo_nome_hash,
                delimitador=norm.delimitador,
                encoding=norm.encoding,
                linha_hash_key=linha_hash_key,
                aceite_lgpd_versao=VERSAO_VIGENTE,
                aceite_lgpd_ip_hash=ip_hash,
                agora=agora,
            )

            repo = DjangoClienteRepository()
            try:
                with transaction.atomic():
                    resultado = importar_clientes(repository=repo, contexto=contexto)
                    # R6 advogado — grava declaracao (RLS) + audit.
                    declaracao_obj = ClienteImportacaoDeclaracao.objects.create(
                        tenant=tenant,
                        usuario_id=usuario_id,
                        arquivo_hash=arquivo_hash,
                        arquivo_tamanho_bytes=len(arquivo_bytes),
                        tem_base_legal=contexto.declaracao_tem_base_legal,
                        compromisso_comunicar_titulares=contexto.declaracao_compromisso_comunicar,
                        declara_sem_dados_sensiveis=contexto.declaracao_sem_sensiveis,
                        procedencia_declarada=contexto.procedencia_declarada,
                        pf_aceite_origem=contexto.pf_aceite_origem,
                    )
                    # R5 advogado — audit sanitizado (sem PII)
                    rejeitados_hashes = [
                        {
                            "linha_numero": r.linha_numero,
                            "linha_hash": r.linha_hash,
                            "motivo": r.motivo,
                        }
                        for r in resultado.rejeitados[:200]
                    ]
                    totais = dict(resultado.totais)
                    totais["dados_sensiveis_filtrados"] = resultado.dados_sensiveis_filtrados
                    totais["pj_dispensa_aceite"] = resultado.pj_dispensa_aceite
                    totais["pj_com_pf_pendente_aceite"] = resultado.pj_com_pf_pendente_aceite
                    totais["pf_rejeitadas_por_falta_aceite"] = (
                        resultado.pf_rejeitadas_por_falta_aceite
                    )

                    registrar_auditoria(
                        tenant_id=tenant.id,
                        usuario_id=usuario_id,
                        action="cliente.importacao_executada",
                        resource_summary=str(resultado.importacao_id),
                        payload={
                            "event_id": str(uuid_module_uuid4()),
                            "tenant_id": str(tenant.id),
                            "importacao_id": str(resultado.importacao_id),
                            "declaracao_id": str(declaracao_obj.id),
                            "declaracao_hash": resultado.declaracao_hash,
                            "arquivo_hash": arquivo_hash,
                            "arquivo_nome_hash": arquivo_nome_hash,
                            "arquivo_tamanho_bytes": len(arquivo_bytes),
                            "delimitador": norm.delimitador,
                            "encoding": norm.encoding,
                            "update_existing": update_existing,
                            "skip_invalid": skip_invalid,
                            "pf_aceite_origem": pf_aceite_origem or None,
                            "procedencia_declarada": contexto.procedencia_declarada,
                            "totais": totais,
                            "rejeitados_motivos_agregados": (
                                resultado.rejeitados_motivos_agregados
                            ),
                            "rejeitados_linhas_hashes": rejeitados_hashes,
                            "ip_hash": ip_hash,
                            "usuario_id": (str(usuario_id) if usuario_id else None),
                        },
                    )
            except ErroImportacao as e:
                return Response(
                    {"detail": e.code, "erro": str(e), **e.detalhes},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            return Response(
                {
                    "importacao_id": str(resultado.importacao_id),
                    "totais": totais,
                    "rejeitados_motivos_agregados": (resultado.rejeitados_motivos_agregados),
                    "rejeitados_amostra": [
                        {
                            "linha_numero": r.linha_numero,
                            "motivo_codigo": r.motivo,
                            "motivo_descricao_curta": r.motivo_descricao_curta,
                        }
                        for r in resultado.rejeitados[:50]
                    ],
                },
                status=status.HTTP_200_OK,
            )
        finally:
            with contextlib.suppress(Exception):
                upload.close()

    @action(detail=False, methods=["get"], url_path="importacoes")
    def importacoes(self, request):
        """GET /clientes/importacoes/ — histórico de importações do tenant.

        Cada chamada dispara INV-013 com finalidade `consulta_relatorio_importacao`
        (R7 advogado).
        """
        from src.infrastructure.audit.models import (
            AcessoDadosCliente,
            FinalidadeAcessoCliente,
        )
        from src.infrastructure.clientes.models import ClienteImportacaoDeclaracao
        from src.infrastructure.multitenant.context import usuario_id_context

        active = _active_tenant_obrigatorio()
        usuario_id = usuario_id_context.get()
        ip_hash = _hashear_ip(request, active)

        # INV-013 — registra acesso ao historico de importacoes.
        # cliente_id=None pra acessos agregados (migration audit/0008 — CONCERN
        # auditor Seguranca 2026-05-18). Quebra de rastreabilidade que existia
        # com placeholder fake `uuid4()` eliminada.
        AcessoDadosCliente.objects.create(
            tenant_id=active,
            usuario_id=usuario_id,
            cliente_id=None,
            finalidade=FinalidadeAcessoCliente.CONSULTA_RELATORIO_IMPORTACAO,
            recurso={
                "tabela": "cliente_importacao_declaracoes",
                "tipo_consulta": "lista_historica",
            },
            ip_hash=ip_hash,
        )

        qs = ClienteImportacaoDeclaracao.objects.filter(tenant_id=active).order_by("-criado_em")[
            :200
        ]
        items = [
            {
                "id": str(d.id),
                "criado_em": d.criado_em.isoformat(),
                "arquivo_hash": d.arquivo_hash,
                "arquivo_tamanho_bytes": d.arquivo_tamanho_bytes,
                "procedencia_declarada": d.procedencia_declarada,
                "pf_aceite_origem": d.pf_aceite_origem or None,
                "usuario_id": (str(d.usuario_id) if d.usuario_id else None),
            }
            for d in qs
        ]
        return Response(
            {"importacoes": items, "total_exibido": len(items), "limite": 200},
            status=status.HTTP_200_OK,
        )

    # =============================================================
    # T-CLI-115 (AC-CLI-006-2 — LGPD art. 8º §5º) — revogação consentimento
    # POST /api/v1/clientes/{id}/direitos-titular/revogacao_consentimento/
    # authz: AuthorizationProvider.can('clientes.atualizar', ...) via
    # ACTION_MAP['revogar_consentimento'] — RequireAuthz aplica.
    # =============================================================
    @action(
        detail=True,
        methods=["post"],
        url_path="direitos-titular/revogacao_consentimento",
    )
    def revogar_consentimento(self, request, pk=None):
        """T-CLI-115 — endpoint gratuito e imediato (efeito ≤ 1 min).

        AuthorizationProvider.can("clientes.atualizar") via ACTION_MAP +
        RequireAuthz (defesa em profundidade — ADR-0012).

        Spec AC-CLI-006-2: cliente migra para estado
        `consentimento_revogado_em`; bases CONSENTIMENTO viram
        inaplicáveis; tratamentos subsequentes só se outra base legal
        aplicar (T-CLI-115 grava timestamp; aplicação real do mapa é
        em `politicas_lgpd.base_legal_aplicavel_pos_revogacao`).
        """
        from src.infrastructure.clientes.direitos_titular import (
            ClienteJaRevogou,
        )
        from src.infrastructure.clientes.direitos_titular import (
            revogar_consentimento as use_case_revogar,
        )
        from src.infrastructure.clientes.models import Cliente
        from src.infrastructure.multitenant.context import usuario_id_context

        try:
            cliente_uuid = UUID(str(pk))
        except (ValueError, TypeError):
            return Response({"detail": "id_invalido"}, status=status.HTTP_400_BAD_REQUEST)

        active = _active_tenant_obrigatorio()
        # Conserto MÉDIO-1 SEC P5 (2026-05-21): defesa em profundidade — filter por tenant_id.
        try:
            cliente = Cliente.objects.filter(tenant_id=active, id=cliente_uuid).get()
        except Cliente.DoesNotExist:
            return Response(
                {"detail": "cliente_nao_encontrado"},
                status=status.HTTP_404_NOT_FOUND,
            )

        usuario_id = usuario_id_context.get()
        try:
            use_case_revogar(
                cliente=cliente,
                tenant_id=active,
                usuario_id=usuario_id,
            )
        except ClienteJaRevogou:
            # Cliente já tinha consentimento_revogado_em setado (não-None) —
            # caso contrário ClienteJaRevogou não teria sido levantada.
            revogado_em = cliente.consentimento_revogado_em
            assert revogado_em is not None
            return Response(
                {"ja_revogado": True, "revogado_em": revogado_em.isoformat()},
                status=status.HTTP_200_OK,
            )
        # Use case acabou de setar consentimento_revogado_em
        revogado_em = cliente.consentimento_revogado_em
        assert revogado_em is not None
        return Response(
            {
                "revogado_em": revogado_em.isoformat(),
                "cliente_id": str(cliente.id),
            },
            status=status.HTTP_200_OK,
        )
