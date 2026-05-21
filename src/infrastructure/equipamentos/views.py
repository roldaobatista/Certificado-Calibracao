"""DRF views Marco 2 — Equipamento (T-EQP-002 etiqueta PDF + T-EQP-003 Idempotency).

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

T-EQP-003 / AC-EQP-001-2b (P-EQP-T6): POST `/etiqueta.pdf` exige header
`Idempotency-Key` UUID. Politica:
- ausente/invalido        -> 400
- mesma chave, em_processo -> 425 (Retry-After: 1)
- mesma chave, payload diferente -> 422
- mesma chave, expirada (>24h) -> 409
- mesma chave, concluida + janela valida -> replay (re-renderiza PDF
  via `garantir_qrcode_vigente` idempotente — mesmo QRCode original)
"""

from __future__ import annotations

from uuid import UUID

from django.http import HttpResponse
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.request import Request
from rest_framework.response import Response

from src.infrastructure.idempotencia.services_idempotencia import (
    ErroValidacao,
    NovoProcessamento,
    Replay,
    avaliar_chave_idempotencia,
    concluir_chave,
    falhar_chave,
)
from src.infrastructure.multitenant.context import active_tenant_context

from .models import Equipamento
from .serializers import EquipamentoLeituraSerializer
from .services_etiqueta import gerar_etiqueta_pdf

ENDPOINT_ETIQUETA = "equipamentos.etiqueta"


def _active_tenant_obrigatorio() -> UUID:
    """Falsafe pro middleware — `PermissionDenied` se nao houver tenant ativo."""
    active = active_tenant_context.get()
    if active is None:
        raise PermissionDenied("tenant_nao_resolvido")
    return active


def _resposta_pdf_etiqueta(equipamento: Equipamento, pdf_bytes: bytes) -> HttpResponse:
    """Monta HttpResponse com cabecalhos canonicos da etiqueta (AC-EQP-001-2)."""
    response = HttpResponse(
        pdf_bytes, content_type="application/pdf", status=status.HTTP_200_OK
    )
    response["Content-Disposition"] = f'inline; filename="etiqueta-{equipamento.tag}.pdf"'
    # AC-EQP-001-2: cache 60s, PRIVATE (tem nome_fantasia do tenant).
    response["Cache-Control"] = "private, max-age=60"
    return response


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

        Exige header `Idempotency-Key` (UUID). 2a chamada com mesma chave
        retorna o MESMO PDF (mesmo QRCode original), re-renderizado.

        Idempotente: chamadas repetidas reusam o QRCode vigente (UNIQUE
        no hash); cada chamada renderiza PDF fresco (cache HTTP 60s
        encurta esse custo em UI).
        """
        equipamento = self.get_object()
        tenant_id = _active_tenant_obrigatorio()
        # IsAuthenticated em DEFAULT_PERMISSION_CLASSES garante user autenticado
        # antes do handler; user.id e UUID nao-nulo. Assert defensivo.
        user_id = request.user.id
        assert user_id is not None
        usuario_id: UUID = user_id

        chave_header = request.META.get("HTTP_IDEMPOTENCY_KEY")
        avaliacao = avaliar_chave_idempotencia(
            tenant_id=tenant_id,
            usuario_id=usuario_id,
            endpoint=ENDPOINT_ETIQUETA,
            chave_header=chave_header,
            payload={"equipamento_id": str(equipamento.id)},
        )
        if isinstance(avaliacao, ErroValidacao):
            return _resposta_erro_idempotencia(avaliacao)

        if isinstance(avaliacao, Replay):
            # Re-renderiza: `garantir_qrcode_vigente` e idempotente, devolve
            # o MESMO QRCode da 1a chamada (UNIQUE hash + revogado_em IS NULL),
            # garantindo PDF deterministico.
            pdf_bytes = gerar_etiqueta_pdf(equipamento)
            return _resposta_pdf_etiqueta(equipamento, pdf_bytes)

        assert isinstance(avaliacao, NovoProcessamento)
        try:
            pdf_bytes = gerar_etiqueta_pdf(equipamento)
        except Exception:
            falhar_chave(
                chave_id=avaliacao.chave_id,  # type: ignore[arg-type]
                tenant_id=tenant_id,
                response_status=500,
            )
            raise
        resumo: dict[str, str] = {"equipamento_tag": equipamento.tag}
        concluir_chave(
            chave_id=avaliacao.chave_id,  # type: ignore[arg-type]
            tenant_id=tenant_id,
            response_status=200,
            response_body_resumo=resumo,
        )
        return _resposta_pdf_etiqueta(equipamento, pdf_bytes)


def _resposta_erro_idempotencia(erro: ErroValidacao) -> Response:
    """Converte `ErroValidacao` em DRF Response com headers opcionais."""
    body = {"codigo": erro.codigo, "detalhe": erro.detalhe}
    response = Response(body, status=erro.http_status)
    if erro.headers:
        for nome, valor in erro.headers.items():
            response[nome] = valor
    return response
