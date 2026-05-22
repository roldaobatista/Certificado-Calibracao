"""DRF views Marco 2 — RecebimentoProvisorio (T-EQP-053+056+057 /
US-EQP-006 AC-EQP-006-6+8+9).

Endpoints:
- POST `/api/v1/equipamentos/provisorios/` — cria provisorio autonomo
  (equipamento ainda nao cadastrado). Multipart-form com foto.
- POST `/api/v1/equipamentos/provisorios/{id}/promover/` — promove
  provisorio a `Equipamento` canonico (cria Equipamento + 1o
  EquipamentoRecebimento). One-shot.
- GET `/api/v1/equipamentos/provisorios/metricas/` —
  taxa_provisorios_mensal (admin / supervisor RBC).

Autorizacao via RequireAuthz + ACTION_MAP (mesmo padrao
EquipamentoViewSet).
"""

from __future__ import annotations

from typing import ClassVar
from uuid import UUID

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.request import Request
from rest_framework.response import Response

from src.infrastructure.equipamentos.models import (
    RecebimentoProvisorio,
)
from src.infrastructure.multitenant.context import active_tenant_context


def _active_tenant_obrigatorio() -> UUID:
    active = active_tenant_context.get()
    if active is None:
        raise PermissionDenied("tenant_nao_resolvido")
    return active


class RecebimentoProvisorioViewSet(viewsets.GenericViewSet):
    """ViewSet sem queryset padrao (list/retrieve nao expostos em
    Marco 2; apenas actions custom).

    # authz-check: skip -- RequireAuthz global resolve via ACTION_MAP.
    """

    queryset = RecebimentoProvisorio.objects.none()
    authz_purpose = "execucao_contrato"
    lookup_field = "id"
    lookup_value_regex = r"[0-9a-f-]{36}"

    ACTION_MAP: ClassVar[dict[str, str]] = {
        "create": "equipamentos.receber_provisorio",
        "promover": "equipamentos.promover_provisorio",
        "metricas": "equipamentos.ler_metricas_provisorio",
    }

    def get_authz_action(self, request) -> str | None:
        action_name = getattr(self, "action", None)
        return self.ACTION_MAP.get(action_name) if action_name else None

    def get_authz_resource(self, request):
        return {}

    def get_queryset(self):
        active = _active_tenant_obrigatorio()
        return RecebimentoProvisorio.objects.filter(tenant_id=active)

    # authz-check: skip -- RequireAuthz + ACTION_MAP['create'] = 'equipamentos.receber_provisorio'
    def create(self, request: Request, *args, **kwargs) -> Response:
        """POST /api/v1/equipamentos/provisorios/ — cria provisorio
        autonomo (Caminho A Roldao)."""
        from src.infrastructure.equipamentos.services_foto_storage import (
            FotoInvalida,
        )
        from src.infrastructure.equipamentos.services_provisorio import (
            CondicaoProvisorioInvalida,
            DadosCriarProvisorio,
            DescricaoEstimadaInvalida,
            FotoObrigatoriaProvisorio,
            ProvisorioInvalido,
            TagProvisoriaInvalida,
            criar_provisorio,
        )

        tenant_id = _active_tenant_obrigatorio()
        user_id = request.user.id
        assert user_id is not None

        body = request.data or {}
        foto_arquivo = request.FILES.get("foto") if request.FILES else None
        foto_bytes = foto_arquivo.read() if foto_arquivo is not None else b""
        foto_mime = (
            foto_arquivo.content_type if foto_arquivo is not None else ""
        )

        dados = DadosCriarProvisorio(
            tag_provisoria=str(body.get("tag_provisoria", "")),
            descricao_estimada=str(body.get("descricao_estimada", "")),
            condicao_visual_chegada=str(body.get("condicao_visual_chegada", "")),
            foto_bytes=foto_bytes,
            foto_mime_type=foto_mime,
        )

        try:
            resultado = criar_provisorio(
                tenant_id=tenant_id,
                recebido_por_id=user_id,
                dados=dados,
            )
        except (
            TagProvisoriaInvalida,
            DescricaoEstimadaInvalida,
            CondicaoProvisorioInvalida,
            FotoObrigatoriaProvisorio,
        ) as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except FotoInvalida as exc:
            return Response(
                {"detail": str(exc), "codigo": "foto_invalida"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except ProvisorioInvalido as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {
                "provisorio_id": str(resultado.provisorio.id),
                "tag_provisoria": resultado.provisorio.tag_provisoria,
                "ttl_expira_em": resultado.provisorio.ttl_expira_em.isoformat(),
                "status": resultado.provisorio.status,
                "foto_sha256": resultado.foto_sha256,
            },
            status=status.HTTP_201_CREATED,
        )

    # authz-check: skip -- RequireAuthz + ACTION_MAP['promover'] = 'equipamentos.promover_provisorio'
    @action(detail=True, methods=["post"], url_path="promover")
    def promover(
        self, request: Request, id: str | None = None
    ) -> Response:
        """POST /api/v1/equipamentos/provisorios/{id}/promover/ —
        promove a Equipamento canonico (one-shot)."""
        from src.infrastructure.equipamentos.services_provisorio import (
            DadosPromoverProvisorio,
            ProvisorioExpirado,
            ProvisorioInvalido,
            ProvisorioJaPromovido,
            TagCanonicaInvalida,
            promover_provisorio,
        )

        provisorio = self.get_object()
        tenant_id = _active_tenant_obrigatorio()
        user_id = request.user.id
        assert user_id is not None

        body = request.data or {}
        dados = DadosPromoverProvisorio(
            tag_canonica=str(body.get("tag_canonica", "")),
            numero_serie=str(body.get("numero_serie", "")),
            fabricante=str(body.get("fabricante", "")),
            modelo=str(body.get("modelo", "")),
            cliente_atual_id=(
                UUID(str(body["cliente_atual_id"]))
                if body.get("cliente_atual_id")
                else None
            ),
            perfil_tenant_snapshot=body.get("perfil_tenant_snapshot"),
            snapshot_schema_version=str(
                body.get("snapshot_schema_version", "1.0.0")
            ),
        )

        try:
            resultado = promover_provisorio(
                tenant_id=tenant_id,
                provisorio=provisorio,
                promovido_por_id=user_id,
                dados=dados,
            )
        except (ProvisorioJaPromovido, ProvisorioExpirado) as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_409_CONFLICT,
            )
        except TagCanonicaInvalida as exc:
            return Response(
                {"detail": str(exc), "codigo": "tag_canonica_invalida"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except ProvisorioInvalido as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {
                "provisorio_id": str(resultado.provisorio.id),
                "equipamento_id": str(resultado.equipamento.id),
                "recebimento_id": str(resultado.recebimento.id),
                "tag_canonica": resultado.equipamento.tag,
                "promovido_em": (
                    resultado.provisorio.promovido_em.isoformat()
                    if resultado.provisorio.promovido_em
                    else None
                ),
            },
            status=status.HTTP_200_OK,
        )

    # authz-check: skip -- RequireAuthz + ACTION_MAP['metricas'] = 'equipamentos.ler_metricas_provisorio'
    @action(detail=False, methods=["get"], url_path="metricas")
    def metricas(self, request: Request) -> Response:
        """GET /api/v1/equipamentos/provisorios/metricas/ — retorna
        taxa_provisorios_mensal + alerta_excedido (P-EQP-R9)."""
        from src.infrastructure.equipamentos.services_provisorio import (
            calcular_taxa_provisorios_mensal,
        )

        tenant_id = _active_tenant_obrigatorio()
        metricas = calcular_taxa_provisorios_mensal(tenant_id=tenant_id)
        return Response(metricas, status=status.HTTP_200_OK)
