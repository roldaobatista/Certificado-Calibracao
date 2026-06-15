"""ViewSet REST de Templates de orçamento (T-ORC-039 / US-ORC-005 / D-ORC-13).

CRUD de `Template` (Padrão C soft-delete) + **gate selo RBC por perfil**: criar/editar
template com `selo_rbc=True` exige tenant perfil A (matriz feature×perfil ADR-0067). O
perfil é resolvido server-side (`resolver_perfil_e_suspensao`), NUNCA do payload — o gate
mora no use case `templates.validar_selo_rbc_permitido` (INV-ORC-SELO-RBC).

  POST   /api/v1/orcamento-templates/        create    -> orcamento.gerir_template
  GET    /api/v1/orcamento-templates/        list      -> orcamento.ver
  GET    /api/v1/orcamento-templates/{id}/   retrieve  -> orcamento.ver
  PUT    /api/v1/orcamento-templates/{id}/   update    -> orcamento.gerir_template
  DELETE /api/v1/orcamento-templates/{id}/   destroy   -> orcamento.gerir_template (soft-delete)

# authz-check: skip -- RequireAuthz global resolve via ACTION_MAP (header)
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import ClassVar

from django.db import transaction
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response

from src.application.comercial.orcamentos import templates as uc_template
from src.domain.comercial.orcamentos.erros import ErroOrcamento
from src.infrastructure.idempotencia.services_idempotencia import concluir_chave
from src.infrastructure.orcamentos._views_suporte import (
    _aplicar_idempotencia,
    _falha_404,
    _falha_erro_orcamento,
    _OrcamentoViewSetBase,
    _tenant_ou_none,
    _usuario_id_ou_none,
)
from src.infrastructure.orcamentos.analise_critica_ports import resolver_perfil_e_suspensao
from src.infrastructure.orcamentos.repositories import DjangoTemplateRepository
from src.infrastructure.orcamentos.serializers import TemplateSerializer, serializar_template


class TemplateViewSet(_OrcamentoViewSetBase):
    """US-ORC-005 — CRUD de templates + gate selo RBC perfil A (D-ORC-13)."""

    ACTION_MAP: ClassVar[dict[str, str]] = {
        "create": "orcamento.gerir_template",
        "update": "orcamento.gerir_template",
        "destroy": "orcamento.gerir_template",
        "list": "orcamento.ver",
        "retrieve": "orcamento.ver",
    }

    # ----- criar (POST /orcamento-templates/) -----------------------

    def create(self, request: Request) -> Response:
        tenant_id = _tenant_ou_none()
        usuario_id = _usuario_id_ou_none()
        if tenant_id is None or usuario_id is None:
            return Response({"detalhe": "contexto ausente"}, status=status.HTTP_401_UNAUTHORIZED)

        ser = TemplateSerializer(data=request.data)
        if not ser.is_valid():
            return Response(ser.errors, status=status.HTTP_422_UNPROCESSABLE_ENTITY)
        dados = ser.validated_data

        novo, resp_erro = _aplicar_idempotencia(
            request,
            tenant_id=tenant_id,
            usuario_id=usuario_id,
            endpoint="orcamentos:template_criar",
            payload_fingerprint={
                "nome": dados["nome"],
                "tipo": dados["tipo"],
                "selo_rbc": bool(dados["selo_rbc"]),
            },
        )
        if resp_erro is not None:
            return resp_erro

        # Perfil regulatório server-side (AJUSTE-3 / nunca do payload) — gate D-ORC-13.
        perfil, _suspensa = resolver_perfil_e_suspensao()
        try:
            with transaction.atomic():
                tpl = uc_template.criar_template(
                    uc_template.CriarTemplateInput(
                        tenant_id=tenant_id,
                        criado_por=usuario_id,
                        perfil=perfil,
                        nome=dados["nome"],
                        tipo=dados["tipo"],
                        agora=datetime.now(UTC),
                        selo_rbc=bool(dados["selo_rbc"]),
                        itens_default=dados.get("itens_default") or [],
                        condicoes_default=dados.get("condicoes_default") or {},
                    ),
                    repo=DjangoTemplateRepository(),
                )
        except ErroOrcamento as exc:
            return _falha_erro_orcamento(exc, tenant_id=tenant_id, chave_idempotencia=novo)

        corpo = serializar_template(tpl)
        if novo is not None and novo.chave_id is not None:
            concluir_chave(
                chave_id=novo.chave_id,
                tenant_id=tenant_id,
                response_status=status.HTTP_201_CREATED,
                response_body_resumo={"id": str(tpl.id), "nome": tpl.nome},
            )
        return Response(corpo, status=status.HTTP_201_CREATED)

    # ----- leitura --------------------------------------------------

    def list(self, request: Request) -> Response:
        tenant_id = _tenant_ou_none()
        if tenant_id is None:
            return Response({"detalhe": "contexto ausente"}, status=status.HTTP_401_UNAUTHORIZED)
        templates = DjangoTemplateRepository().listar(tenant_id=tenant_id)
        return Response([serializar_template(t) for t in templates], status=status.HTTP_200_OK)

    def retrieve(self, request: Request, pk: str | None = None) -> Response:
        tenant_id = _tenant_ou_none()
        if tenant_id is None:
            return Response({"detalhe": "contexto ausente"}, status=status.HTTP_401_UNAUTHORIZED)
        template_id = self._uuid_ou_404(pk)
        tpl = DjangoTemplateRepository().get_by_id(template_id, tenant_id=tenant_id)
        if tpl is None:
            return _falha_404(f"template {template_id} nao encontrado")
        return Response(serializar_template(tpl), status=status.HTTP_200_OK)

    # ----- editar (PUT /orcamento-templates/{id}/) ------------------

    def update(self, request: Request, pk: str | None = None) -> Response:
        tenant_id = _tenant_ou_none()
        usuario_id = _usuario_id_ou_none()
        if tenant_id is None or usuario_id is None:
            return Response({"detalhe": "contexto ausente"}, status=status.HTTP_401_UNAUTHORIZED)
        template_id = self._uuid_ou_404(pk)

        ser = TemplateSerializer(data=request.data)
        if not ser.is_valid():
            return Response(ser.errors, status=status.HTTP_422_UNPROCESSABLE_ENTITY)
        dados = ser.validated_data

        novo, resp_erro = _aplicar_idempotencia(
            request,
            tenant_id=tenant_id,
            usuario_id=usuario_id,
            endpoint="orcamentos:template_editar",
            payload_fingerprint={
                "template_id": str(template_id),
                "nome": dados["nome"],
                "tipo": dados["tipo"],
                "selo_rbc": bool(dados["selo_rbc"]),
            },
        )
        if resp_erro is not None:
            return resp_erro

        perfil, _suspensa = resolver_perfil_e_suspensao()
        try:
            with transaction.atomic():
                tpl = uc_template.editar_template(
                    uc_template.EditarTemplateInput(
                        tenant_id=tenant_id,
                        template_id=template_id,
                        perfil=perfil,
                        nome=dados["nome"],
                        tipo=dados["tipo"],
                        selo_rbc=bool(dados["selo_rbc"]),
                        itens_default=dados.get("itens_default") or [],
                        condicoes_default=dados.get("condicoes_default") or {},
                    ),
                    repo=DjangoTemplateRepository(),
                )
        except ErroOrcamento as exc:
            return _falha_erro_orcamento(exc, tenant_id=tenant_id, chave_idempotencia=novo)

        corpo = serializar_template(tpl)
        if novo is not None and novo.chave_id is not None:
            concluir_chave(
                chave_id=novo.chave_id,
                tenant_id=tenant_id,
                response_status=status.HTTP_200_OK,
                response_body_resumo={"id": str(tpl.id), "nome": tpl.nome},
            )
        return Response(corpo, status=status.HTTP_200_OK)

    # ----- remover (DELETE /orcamento-templates/{id}/) — soft-delete --

    def destroy(self, request: Request, pk: str | None = None) -> Response:
        tenant_id = _tenant_ou_none()
        usuario_id = _usuario_id_ou_none()
        if tenant_id is None or usuario_id is None:
            return Response({"detalhe": "contexto ausente"}, status=status.HTTP_401_UNAUTHORIZED)
        template_id = self._uuid_ou_404(pk)
        try:
            with transaction.atomic():
                uc_template.remover_template(
                    template_id,
                    tenant_id=tenant_id,
                    removido_por=usuario_id,
                    agora=datetime.now(UTC),
                    repo=DjangoTemplateRepository(),
                )
        except ErroOrcamento as exc:
            return _falha_erro_orcamento(exc, tenant_id=tenant_id)
        return Response(status=status.HTTP_204_NO_CONTENT)
