"""DRF views — US-EQP-007 (T-EQP-064).

# authz-check: skip -- RequireAuthz global (DEFAULT_PERMISSION_CLASSES)
# resolve via ACTION_MAP — mesmo pattern dos demais viewsets.

Endpoints:
- GET    /api/v1/responsaveis-tecnicos/             list RT do tenant
- GET    /api/v1/responsaveis-tecnicos/{id}/         retrieve
- POST   /api/v1/responsaveis-tecnicos/             cadastrar
- POST   /api/v1/responsaveis-tecnicos/{id}/encerrar/
- POST   /api/v1/responsaveis-tecnicos/{id}/trocar/
- POST   /api/v1/responsaveis-tecnicos/{id}/competencias/

Authz:
- gerenciar (cadastrar/encerrar/trocar/competencia): admin_tenant +
  gestor_qualidade.
- ler: todos perfis com leitura no modulo.
"""

from __future__ import annotations

from uuid import UUID

from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.request import Request
from rest_framework.response import Response

from src.infrastructure.multitenant.context import active_tenant_context

from .models import ResponsavelTecnicoTenant
from .serializers import (
    CadastrarRTPayloadSerializer,
    DeclararCompetenciaPayloadSerializer,
    EncerrarRTPayloadSerializer,
    ResponsavelTecnicoLeituraSerializer,
    RTCompetenciaLeituraSerializer,
    TrocarRTPayloadSerializer,
)
from .services_rt import (
    CompetenciaSobreposta,
    DadosCadastroRT,
    DadosCompetencia,
    cadastrar_rt,
    declarar_competencia,
    encerrar_rt,
    trocar_rt,
)


def _active_tenant_obrigatorio() -> UUID:
    """PermissionDenied se nao houver tenant ativo (falsafe do middleware)."""
    active = active_tenant_context.get()
    if active is None:
        raise PermissionDenied("tenant_nao_resolvido")
    return active


def _dados_cadastro_do_payload(data: dict) -> DadosCadastroRT:
    return DadosCadastroRT(
        nome_completo=data["nome_completo"],
        cpf=data["cpf"],
        formacao_academica=data["formacao_academica"],
        registro_profissional_tipo=data["registro_profissional_tipo"],
        registro_profissional_numero=data["registro_profissional_numero"],
        registro_profissional_descricao_outro=data.get(
            "registro_profissional_descricao_outro", ""
        ),
        data_inicio_vigencia=data["data_inicio_vigencia"],
        data_fim_vigencia=data.get("data_fim_vigencia"),
    )


class ResponsavelTecnicoViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    viewsets.GenericViewSet,
):
    """CRUD + actions encerrar/trocar/competencias."""

    serializer_class = ResponsavelTecnicoLeituraSerializer
    queryset = ResponsavelTecnicoTenant.objects.none()
    authz_purpose = "execucao_contrato"
    lookup_field = "id"
    lookup_value_regex = r"[0-9a-f-]{36}"

    ACTION_MAP = {
        "list": "responsavel_tecnico.ler",
        "retrieve": "responsavel_tecnico.ler",
        "create": "responsavel_tecnico.gerenciar",
        "encerrar": "responsavel_tecnico.gerenciar",
        "trocar": "responsavel_tecnico.gerenciar",
        "competencias": "responsavel_tecnico.gerenciar",
    }

    def get_authz_action(self, request) -> str | None:
        action_name = getattr(self, "action", None)
        return self.ACTION_MAP.get(action_name) if action_name else None

    def get_authz_resource(self, request):
        return {}

    def get_queryset(self):
        active = _active_tenant_obrigatorio()
        return ResponsavelTecnicoTenant.objects.filter(tenant_id=active)

    def create(self, request: Request, *args, **kwargs) -> Response:
        tenant_id = _active_tenant_obrigatorio()
        ser = CadastrarRTPayloadSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        op_id = request.user.id
        assert op_id is not None
        rt = cadastrar_rt(
            tenant_id=tenant_id,
            usuario_rt_id=ser.validated_data["usuario_rt_id"],
            criado_por_id=op_id,
            dados=_dados_cadastro_do_payload(ser.validated_data),
        )
        return Response(
            ResponsavelTecnicoLeituraSerializer(rt).data,
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["post"], url_path="encerrar")
    def encerrar(self, request: Request, id: str | None = None) -> Response:
        rt = self.get_object()
        ser = EncerrarRTPayloadSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        op_id = request.user.id
        assert op_id is not None
        rt = encerrar_rt(
            rt=rt,
            encerrado_por_id=op_id,
            motivo=ser.validated_data["motivo"],
            motivo_detalhe=ser.validated_data.get("motivo_detalhe", ""),
        )
        return Response(ResponsavelTecnicoLeituraSerializer(rt).data)

    @action(detail=True, methods=["post"], url_path="trocar")
    def trocar(self, request: Request, id: str | None = None) -> Response:
        rt_atual = self.get_object()
        ser = TrocarRTPayloadSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        op_id = request.user.id
        assert op_id is not None
        _, novo = trocar_rt(
            rt_atual=rt_atual,
            usuario_novo_rt_id=ser.validated_data["usuario_rt_id"],
            operador_id=op_id,
            dados_novo_rt=_dados_cadastro_do_payload(ser.validated_data),
            motivo_encerramento_anterior=ser.validated_data.get(
                "motivo_encerramento_anterior", "substituicao"
            ),
        )
        return Response(
            ResponsavelTecnicoLeituraSerializer(novo).data,
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["post"], url_path="competencias")
    def competencias(self, request: Request, id: str | None = None) -> Response:
        rt = self.get_object()
        ser = DeclararCompetenciaPayloadSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        op_id = request.user.id
        assert op_id is not None
        try:
            competencia = declarar_competencia(
                rt=rt,
                criado_por_id=op_id,
                dados=DadosCompetencia(
                    grandeza=ser.validated_data["grandeza"],
                    declarado_em=ser.validated_data["declarado_em"],
                    vigente_ate=ser.validated_data.get("vigente_ate"),
                    carta_competencia_anexo_id=ser.validated_data.get(
                        "carta_competencia_anexo_id"
                    ),
                ),
            )
        except CompetenciaSobreposta as exc:
            return Response(
                {
                    "codigo": "rt_competencia_sobreposta",
                    "detalhe": str(exc),
                },
                status=status.HTTP_409_CONFLICT,
            )
        return Response(
            RTCompetenciaLeituraSerializer(competencia).data,
            status=status.HTTP_201_CREATED,
        )
