"""ContasReceberViewSet — REST da frente contas-receber (T-CR-035 / T-CR-036).

Actions autenticadas (ContasReceberViewSet):
  GET  /api/v1/contas-receber/{id}/                  retrieve
  GET  /api/v1/contas-receber/                       list
  POST /api/v1/contas-receber/criar/                 criar    (US-CR-001 manual)
  POST /api/v1/contas-receber/{id}/baixar-manual/    baixar-manual (US-CR-003)
  POST /api/v1/contas-receber/{id}/cancelar/         cancelar (T-CR-034)
  POST /api/v1/contas-receber/{id}/emitir-boleto/    emitir-boleto (T-CR-031)
  POST /api/v1/contas-receber/{id}/emitir-pix/       emitir-pix-recorrente (T-CR-031)
  POST /api/v1/contas-receber/override-bloqueio/     override-bloqueio (T-CR-034)

Endpoint público (ContasReceberWebhookView):
  POST /api/v1/public/contas-receber/webhook/        webhook gateway (T-CR-036)

Autorização: RequireAuthz (DEFAULT_PERMISSION_CLASSES) + ACTION_MAP.
Idempotency-Key obrigatória em POST de escrita (IDEMP-001).
Perfil server-side (D-CR-6 / INV-FIN-SNAPSHOT-PERFIL-001 — nunca payload).
Advisory lock `pg_advisory_xact_lock(hashtext("cr:{op}:{tenant}:{id}"))`.
`publicar_evento(outbox=True)` dentro do mesmo `transaction.atomic`.

# authz-check: skip -- RequireAuthz global resolve via ACTION_MAP (header)
"""

from __future__ import annotations

import logging
from typing import Any
from uuid import UUID

from django.db import connection, transaction
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound
from rest_framework.request import Request
from rest_framework.response import Response

from src.application.contas_receber import (
    baixar_titulo_manual,
    cancelar_titulo,
    criar_titulo_manual,
    emitir_cobranca,
)
from src.application.contas_receber import (
    override_bloqueio as uc_override,
)
from src.domain.contas_receber.enums import (
    CategoriaReceita,
    EstadoTitulo,
    MeioCobranca,
)
from src.domain.contas_receber.erros import (
    CategoriaReceitaExigePerfilA,
    ClienteObrigatorio,
    ConvenioPixAusente,
    GatewayIndisponivel,
    JustificativaInsuficiente,
    OverrideForaDeAlcada,
    PerfilIndeterminado,
    TituloComPagamentoParcial,
    TituloNaoEncontrado,
    TransicaoProibida,
)
from src.domain.contas_receber.portas import PaymentGatewayProvider
from src.infrastructure.authz.perfil_tenant_helper import obter_perfil_tenant_corrente
from src.infrastructure.contas_receber.repositories import DjangoTituloRepository
from src.infrastructure.contas_receber.serializers import (
    BaixarTituloSerializer,
    CancelarTituloSerializer,
    CriarTituloSerializer,
    EmitirBoletoSerializer,
    EmitirPixRecorrenteSerializer,
    OverrideBloqueioSerializer,
)
from src.infrastructure.idempotencia.services_idempotencia import (
    ErroValidacao,
    NovoProcessamento,
    Replay,
    avaliar_chave_idempotencia,
    concluir_chave,
    falhar_chave,
)
from src.infrastructure.multitenant.context import (
    active_tenant_context,
    usuario_id_context,
)

logger = logging.getLogger(__name__)

ENDPOINT_CRIAR = "contas_receber.criar"
ENDPOINT_BAIXAR = "contas_receber.baixar_manual"
ENDPOINT_CANCELAR = "contas_receber.cancelar"
ENDPOINT_EMITIR_BOLETO = "contas_receber.emitir_boleto"
ENDPOINT_EMITIR_PIX = "contas_receber.emitir_pix_recorrente"
ENDPOINT_OVERRIDE = "contas_receber.override_bloqueio"


def _obter_provider() -> PaymentGatewayProvider:
    """Instancia o MockPaymentGatewayProvider com o modo configurado em settings.

    Molde: `FISCAL_PROVIDER_MOCK_MODO` em fiscal/views.py.
    Adapter Asaas real = GATE-CR-ASAAS (pré-produção).
    """
    from django.conf import settings

    from src.domain.contas_receber.mock_provider import MockPaymentGatewayProvider, ModoMock

    modo_str = getattr(settings, "CR_GATEWAY_PROVIDER_MOCK_MODO", "always_confirm")
    try:
        modo = ModoMock(modo_str)
    except ValueError:
        logger.warning(
            "CR_GATEWAY_PROVIDER_MOCK_MODO inválido (%r) — usando always_confirm", modo_str
        )
        modo = ModoMock.ALWAYS_CONFIRM
    return MockPaymentGatewayProvider(modo=modo)


def _tenant_ou_none() -> UUID | None:
    return active_tenant_context.get()


def _obter_perfil_ou_fail() -> str | None:
    """Retorna perfil server-side ou None (fail-closed)."""
    return obter_perfil_tenant_corrente() or None


def _serializar_titulo(t: Any) -> dict[str, Any]:
    ref = t.cliente_referencia
    return {
        "titulo_id": str(t.titulo_id),
        "tenant_id": str(t.tenant_id),
        "valor_original": t.valor_original.centavos,
        "data_emissao": t.data_emissao.isoformat(),
        "data_vencimento": t.data_vencimento.isoformat(),
        "data_baixa": t.data_baixa.isoformat() if t.data_baixa else None,
        "estado": t.estado.value,
        "meio": t.meio.value,
        "categoria_receita": t.categoria_receita.value,
        "perfil_no_evento": t.perfil_no_evento,
        "origem": t.origem.value,
        "cliente_atual_id": str(ref.uuid_atual_id) if ref.uuid_atual_id else None,
        "cliente_referencia_hash": ref.hash_original,
        "os_id_origem": str(t.os_id_origem) if t.os_id_origem else None,
        "gateway_externo_id": t.gateway_externo_id,
        "revision": t.revision,
    }


def _resposta_erro_idempotencia(erro: ErroValidacao) -> Response:
    body = {"codigo": erro.codigo, "detalhe": erro.detalhe}
    if erro.headers:
        return Response(body, status=erro.http_status, headers=erro.headers)
    return Response(body, status=erro.http_status)


def _aplicar_idempotencia(
    request: Request,
    *,
    tenant_id: UUID,
    usuario_id: UUID,
    endpoint: str,
    payload_fingerprint: dict[str, Any],
) -> tuple[NovoProcessamento | None, Response | None]:
    avaliacao = avaliar_chave_idempotencia(
        tenant_id=tenant_id,
        usuario_id=usuario_id,
        endpoint=endpoint,
        chave_header=request.META.get("HTTP_IDEMPOTENCY_KEY"),
        payload=payload_fingerprint,
    )
    if isinstance(avaliacao, ErroValidacao):
        return None, _resposta_erro_idempotencia(avaliacao)
    if isinstance(avaliacao, Replay):
        return None, Response(
            avaliacao.response_body_resumo or {}, status=avaliacao.response_status
        )
    assert isinstance(avaliacao, NovoProcessamento)
    return avaliacao, None


def _publicar_evento_cr(
    *,
    acao: str,
    payload: dict[str, Any],
    causation_id: UUID,
    tenant_id: UUID,
    usuario_id: UUID,
    resource_summary: str,
) -> None:
    """Evento na cadeia hash + outbox (D-CR-14). Import local (molde fiscal)."""
    from src.infrastructure.audit.event_helpers import publicar_evento

    publicar_evento(
        acao=acao,
        payload=payload,
        causation_id=causation_id,
        tenant_id=tenant_id,
        usuario_id=usuario_id if usuario_id != UUID(int=0) else None,
        resource_summary=resource_summary,
    )
    logger.info(
        "contas_receber evento WORM publicado",
        extra={
            "tenant_id": str(tenant_id),
            "acao": acao,
            "correlation_id": str(payload.get("titulo_id", "")),
        },
    )


# authz-check: skip -- RequireAuthz global resolve via ACTION_MAP (header)
class ContasReceberViewSet(viewsets.ViewSet):
    """ViewSet REST de ContasReceber (Fatia 2a — criar/baixar-manual/cancelar/retrieve/list)."""

    authz_purpose = "execucao_contrato"
    ACTION_MAP = {
        "retrieve": "contas_receber.ver",
        "list": "contas_receber.ver",
        "criar": "contas_receber.criar",
        "baixar_manual": "contas_receber.baixar",
        "cancelar": "contas_receber.cancelar",
        # Fatia 2b
        "emitir_boleto": "contas_receber.emitir",
        "emitir_pix_recorrente": "contas_receber.emitir",
        "override_bloqueio": "contas_receber.override_bloqueio",
    }

    def get_authz_action(self, request: Request) -> str | None:
        action_name = getattr(self, "action", None)
        return self.ACTION_MAP.get(action_name) if action_name else None

    def get_authz_resource(self, request: Request) -> dict[str, Any]:
        return {}

    # ---------------------------------------------------------------- GET retrieve
    def retrieve(self, request: Request, pk: str | None = None) -> Response:
        tenant_id = _tenant_ou_none()
        if tenant_id is None:
            return Response({"erro": "tenant ausente"}, status=status.HTTP_403_FORBIDDEN)
        repo = DjangoTituloRepository()
        titulo = repo.obter_por_id(tenant_id=tenant_id, titulo_id=self._uuid_ou_404(pk))
        if titulo is None:
            raise NotFound(f"Título {pk} não encontrado.")
        return Response(_serializar_titulo(titulo))

    # ---------------------------------------------------------------- GET list
    def list(self, request: Request) -> Response:
        tenant_id = _tenant_ou_none()
        if tenant_id is None:
            return Response({"erro": "tenant ausente"}, status=status.HTTP_403_FORBIDDEN)
        repo = DjangoTituloRepository()
        estado_filtro = request.query_params.get("estado")
        cliente_id_str = request.query_params.get("cliente_atual_id")
        cliente_id: UUID | None = None
        if cliente_id_str:
            try:
                cliente_id = UUID(cliente_id_str)
            except ValueError:
                return Response(
                    {"erro": "cliente_atual_id inválido"}, status=status.HTTP_400_BAD_REQUEST
                )
        titulos = repo.listar_por_tenant(
            tenant_id=tenant_id,
            estado=estado_filtro,
            cliente_atual_id=cliente_id,
        )
        return Response([_serializar_titulo(t) for t in titulos])

    # ---------------------------------------------------------------- POST criar
    @action(detail=False, methods=["post"], url_path="criar")
    def criar(self, request: Request) -> Response:
        """POST — US-CR-001 manual. # idempotency-key: required"""
        s = CriarTituloSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        d = s.validated_data

        tenant_id = _tenant_ou_none()
        if tenant_id is None:
            return Response({"erro": "tenant ausente"}, status=status.HTTP_403_FORBIDDEN)

        perfil_str = _obter_perfil_ou_fail()
        if not perfil_str:
            return Response(
                {"erro": "perfil regulatório indisponível (fail-closed ADR-0067)"},
                status=status.HTTP_403_FORBIDDEN,
            )

        usuario_id = usuario_id_context.get() or UUID(int=0)

        # Fingerprint: hash do cliente + data_vencimento (sem PII direta)
        novo, resp = _aplicar_idempotencia(
            request,
            tenant_id=tenant_id,
            usuario_id=usuario_id,
            endpoint=ENDPOINT_CRIAR,
            payload_fingerprint={
                "cliente_referencia_hash": d["cliente_referencia_hash"],
                "cliente_key_id": d["cliente_key_id"],
                "valor_centavos": d["valor_centavos"],
                "data_vencimento": str(d["data_vencimento"]),
            },
        )
        if resp is not None:
            return resp
        assert novo is not None and novo.chave_id is not None
        chave_id = novo.chave_id

        # Categoria (pode ser None → derivada pelo use case)
        categoria_raw = d.get("categoria_receita")
        categoria: CategoriaReceita | None = (
            CategoriaReceita(categoria_raw) if categoria_raw else None
        )

        repo = DjangoTituloRepository()
        try:
            inp = criar_titulo_manual.CriarTituloManualInput(
                tenant_id=tenant_id,
                cliente_referencia_hash=d["cliente_referencia_hash"],
                cliente_key_id=d["cliente_key_id"],
                valor_centavos=d["valor_centavos"],
                data_vencimento=d["data_vencimento"],
                meio=MeioCobranca(d["meio"]),
                perfil_no_evento=perfil_str,
                cliente_atual_id=d.get("cliente_atual_id"),
                categoria_receita=categoria,
            )
            with transaction.atomic():
                # Advisory lock por cliente + tenant (serializa criações concorrentes)
                self._advisory_lock(f"cr:criar:{tenant_id}:{d['cliente_referencia_hash']}")
                out = criar_titulo_manual.executar(inp, repo=repo)
                _publicar_evento_cr(
                    acao="contas_receber.titulo_emitido",
                    payload={
                        "titulo_id": str(out.titulo.titulo_id),
                        "cliente_referencia_hash": d["cliente_referencia_hash"],
                        "valor_centavos": out.titulo.valor_original.centavos,
                        "data_vencimento": out.titulo.data_vencimento.isoformat(),
                        "categoria_receita": out.titulo.categoria_receita.value,
                        "perfil_no_evento": out.titulo.perfil_no_evento,
                        "meio": out.titulo.meio.value,
                        "origem": out.titulo.origem.value,
                    },
                    causation_id=chave_id,
                    tenant_id=tenant_id,
                    usuario_id=usuario_id,
                    resource_summary=f"titulo_receber {out.titulo.titulo_id} emitido",
                )
        except CategoriaReceitaExigePerfilA as exc:
            # Publica evento de auditoria (INV-FIN-PERFIL-001 / D-CR-5)
            try:
                with transaction.atomic():
                    _publicar_evento_cr(
                        acao="contas_receber.categoria_receita_bloqueada",
                        payload={
                            "categoria": categoria.value if categoria else "derivada",
                            "perfil": perfil_str,
                            "razao": str(exc),
                        },
                        causation_id=chave_id,
                        tenant_id=tenant_id,
                        usuario_id=usuario_id,
                        resource_summary="categoria_receita_bloqueada",
                    )
            except Exception:  # -- falha no evento de auditoria não deve mascarar o 403
                logger.warning(
                    "falha ao publicar evento categoria_receita_bloqueada",
                    exc_info=True,
                )
            return self._falha(chave_id, tenant_id, exc, status.HTTP_403_FORBIDDEN)
        except PerfilIndeterminado as exc:
            return self._falha(chave_id, tenant_id, exc, status.HTTP_422_UNPROCESSABLE_ENTITY)
        except ClienteObrigatorio as exc:
            return self._falha(chave_id, tenant_id, exc, status.HTTP_422_UNPROCESSABLE_ENTITY)
        except ValueError as exc:
            return self._falha(chave_id, tenant_id, exc, status.HTTP_400_BAD_REQUEST)

        body = _serializar_titulo(out.titulo)
        concluir_chave(
            chave_id=chave_id,
            tenant_id=tenant_id,
            response_status=status.HTTP_201_CREATED,
            response_body_resumo=body,
        )
        return Response(body, status=status.HTTP_201_CREATED)

    # ---------------------------------------------------------------- POST baixar-manual
    @action(detail=True, methods=["post"], url_path="baixar-manual")
    def baixar_manual(self, request: Request, pk: str | None = None) -> Response:
        """POST — US-CR-003 baixa manual. # idempotency-key: required"""
        s = BaixarTituloSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        d = s.validated_data

        tenant_id = _tenant_ou_none()
        if tenant_id is None:
            return Response({"erro": "tenant ausente"}, status=status.HTTP_403_FORBIDDEN)

        titulo_id = self._uuid_ou_404(pk)
        usuario_id = usuario_id_context.get() or UUID(int=0)

        novo, resp = _aplicar_idempotencia(
            request,
            tenant_id=tenant_id,
            usuario_id=usuario_id,
            endpoint=ENDPOINT_BAIXAR,
            payload_fingerprint={
                "titulo_id": str(titulo_id),
                "data_pagamento": str(d["data_pagamento"]),
            },
        )
        if resp is not None:
            return resp
        assert novo is not None and novo.chave_id is not None
        chave_id = novo.chave_id

        repo = DjangoTituloRepository()
        try:
            inp = baixar_titulo_manual.BaixarTituloManualInput(
                tenant_id=tenant_id,
                titulo_id=titulo_id,
                valor_centavos=d["valor_centavos"],
                data_pagamento=d["data_pagamento"],
                comprovante_url=d.get("comprovante_url"),
            )
            with transaction.atomic():
                self._advisory_lock(f"cr:baixar:{tenant_id}:{titulo_id}")
                out = baixar_titulo_manual.executar(inp, repo=repo)
                # Publica contas_receber.pago (D-CR-11 / D-CR-14)
                _publicar_evento_cr(
                    acao="contas_receber.pago",
                    payload={
                        "titulo_id": str(titulo_id),
                        "pagamento_id": str(out.pagamento.pagamento_id),
                        "valor_centavos": out.pagamento.valor.centavos,
                        "valor_atualizado_snapshot": (
                            out.pagamento.valor_atualizado_snapshot_em_pagamento.centavos
                        ),
                        "data": out.pagamento.data.isoformat(),
                        "origem": out.pagamento.origem.value,
                        "novo_estado": out.novo_estado.value,
                        "perfil_no_evento": out.titulo.perfil_no_evento,
                        "os_id_origem": (
                            str(out.titulo.os_id_origem) if out.titulo.os_id_origem else None
                        ),
                    },
                    causation_id=chave_id,
                    tenant_id=tenant_id,
                    usuario_id=usuario_id,
                    resource_summary=f"titulo_receber {titulo_id} baixa {out.novo_estado.value}",
                )
                # T-CR-042: baixa de título de OS → publica os.paga (R2 / D-CR-12),
                # SÓ quando totalmente PAGO (parcial mantém a OS em faturada). Mesmo
                # atomic. Webhook publica equivalente (views_webhook.py — Fatia 2b).
                if out.titulo.os_id_origem and out.novo_estado == EstadoTitulo.PAGO:
                    _publicar_evento_cr(
                        acao="os.paga",
                        payload={"os_id": str(out.titulo.os_id_origem)},
                        causation_id=chave_id,
                        tenant_id=tenant_id,
                        usuario_id=usuario_id,
                        resource_summary=f"os {out.titulo.os_id_origem} paga (baixa manual)",
                    )
        except TituloNaoEncontrado as exc:
            return self._falha(chave_id, tenant_id, exc, status.HTTP_404_NOT_FOUND)
        except TransicaoProibida as exc:
            return self._falha(chave_id, tenant_id, exc, status.HTTP_409_CONFLICT)
        except ValueError as exc:
            return self._falha(chave_id, tenant_id, exc, status.HTTP_400_BAD_REQUEST)

        body = _serializar_titulo(out.titulo)
        body["pagamento_id"] = str(out.pagamento.pagamento_id)
        body["valor_pago"] = out.pagamento.valor.centavos
        body["valor_atualizado_snapshot"] = (
            out.pagamento.valor_atualizado_snapshot_em_pagamento.centavos
        )
        concluir_chave(
            chave_id=chave_id,
            tenant_id=tenant_id,
            response_status=status.HTTP_200_OK,
            response_body_resumo=body,
        )
        return Response(body, status=status.HTTP_200_OK)

    # ---------------------------------------------------------------- POST cancelar
    @action(detail=True, methods=["post"], url_path="cancelar")
    def cancelar(self, request: Request, pk: str | None = None) -> Response:
        """POST — T-CR-034 cancelar. # idempotency-key: required"""
        s = CancelarTituloSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        d = s.validated_data

        tenant_id = _tenant_ou_none()
        if tenant_id is None:
            return Response({"erro": "tenant ausente"}, status=status.HTTP_403_FORBIDDEN)

        titulo_id = self._uuid_ou_404(pk)
        usuario_id = usuario_id_context.get() or UUID(int=0)

        novo, resp = _aplicar_idempotencia(
            request,
            tenant_id=tenant_id,
            usuario_id=usuario_id,
            endpoint=ENDPOINT_CANCELAR,
            payload_fingerprint={"titulo_id": str(titulo_id)},
        )
        if resp is not None:
            return resp
        assert novo is not None and novo.chave_id is not None
        chave_id = novo.chave_id

        repo = DjangoTituloRepository()
        try:
            inp = cancelar_titulo.CancelarTituloInput(
                tenant_id=tenant_id,
                titulo_id=titulo_id,
                razao=d.get("razao", ""),
            )
            with transaction.atomic():
                self._advisory_lock(f"cr:cancelar:{tenant_id}:{titulo_id}")
                out = cancelar_titulo.executar(inp, repo=repo)
                _publicar_evento_cr(
                    acao="contas_receber.titulo_cancelado",
                    payload={
                        "titulo_id": str(titulo_id),
                        "razao": inp.razao,
                        "cancelado_em": out.cancelado_em.isoformat(),
                        "perfil_no_evento": out.titulo.perfil_no_evento,
                    },
                    causation_id=chave_id,
                    tenant_id=tenant_id,
                    usuario_id=usuario_id,
                    resource_summary=f"titulo_receber {titulo_id} cancelado",
                )
        except TituloNaoEncontrado as exc:
            return self._falha(chave_id, tenant_id, exc, status.HTTP_404_NOT_FOUND)
        except TituloComPagamentoParcial as exc:
            return self._falha(chave_id, tenant_id, exc, status.HTTP_409_CONFLICT)
        except TransicaoProibida as exc:
            return self._falha(chave_id, tenant_id, exc, status.HTTP_409_CONFLICT)
        except ValueError as exc:
            return self._falha(chave_id, tenant_id, exc, status.HTTP_400_BAD_REQUEST)

        body = _serializar_titulo(out.titulo)
        body["cancelado_em"] = out.cancelado_em.isoformat()
        concluir_chave(
            chave_id=chave_id,
            tenant_id=tenant_id,
            response_status=status.HTTP_200_OK,
            response_body_resumo=body,
        )
        return Response(body, status=status.HTTP_200_OK)

    # ---------------------------------------------------------------- POST emitir-boleto (Fatia 2b)
    @action(detail=True, methods=["post"], url_path="emitir-boleto")
    def emitir_boleto(self, request: Request, pk: str | None = None) -> Response:
        """POST — US-CR-002 emitir boleto. # idempotency-key: required"""
        s = EmitirBoletoSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        d = s.validated_data

        tenant_id = _tenant_ou_none()
        if tenant_id is None:
            return Response({"erro": "tenant ausente"}, status=status.HTTP_403_FORBIDDEN)

        titulo_id = self._uuid_ou_404(pk)
        usuario_id = usuario_id_context.get() or UUID(int=0)

        novo, resp = _aplicar_idempotencia(
            request,
            tenant_id=tenant_id,
            usuario_id=usuario_id,
            endpoint=ENDPOINT_EMITIR_BOLETO,
            payload_fingerprint={"titulo_id": str(titulo_id)},
        )
        if resp is not None:
            return resp
        assert novo is not None and novo.chave_id is not None
        chave_id = novo.chave_id

        repo = DjangoTituloRepository()
        provider = _obter_provider()
        try:
            inp = emitir_cobranca.EmitirBoletoInput(
                tenant_id=tenant_id,
                titulo_id=titulo_id,
                vencimento_override=d.get("vencimento_override"),
            )
            with transaction.atomic():
                self._advisory_lock(f"cr:emitir_boleto:{tenant_id}:{titulo_id}")
                out = emitir_cobranca.emitir_boleto(inp, repo=repo, provider=provider)
                _publicar_evento_cr(
                    acao="contas_receber.boleto_emitido",
                    payload={
                        "titulo_id": str(titulo_id),
                        "gateway_externo_id": out.titulo.gateway_externo_id,
                        "linha_digitavel": out.titulo.linha_digitavel,
                        "qr_code": out.titulo.qr_code,
                        "perfil_no_evento": out.titulo.perfil_no_evento,
                    },
                    causation_id=chave_id,
                    tenant_id=tenant_id,
                    usuario_id=usuario_id,
                    resource_summary=f"titulo_receber {titulo_id} boleto emitido",
                )
        except TituloNaoEncontrado as exc:
            return self._falha(chave_id, tenant_id, exc, status.HTTP_404_NOT_FOUND)
        except TransicaoProibida as exc:
            return self._falha(chave_id, tenant_id, exc, status.HTTP_409_CONFLICT)
        except GatewayIndisponivel as exc:
            # 503 + publica evento gateway_indisponivel (D-CR-7).
            try:
                with transaction.atomic():
                    _publicar_evento_cr(
                        acao="contas_receber.gateway_indisponivel",
                        payload={
                            "titulo_id": str(titulo_id),
                            "retry_em_segundos": 60,
                            "detalhe": str(exc),
                        },
                        causation_id=chave_id,
                        tenant_id=tenant_id,
                        usuario_id=usuario_id,
                        resource_summary=f"gateway_indisponivel boleto {titulo_id}",
                    )
            except Exception:
                logger.warning("falha ao publicar gateway_indisponivel", exc_info=True)
            return self._falha(
                chave_id, tenant_id, exc, status.HTTP_503_SERVICE_UNAVAILABLE
            )
        except ValueError as exc:
            return self._falha(chave_id, tenant_id, exc, status.HTTP_400_BAD_REQUEST)

        body = _serializar_titulo(out.titulo)
        body["gateway_externo_id"] = out.cobranca.gateway_id
        body["linha_digitavel"] = out.cobranca.linha_digitavel
        body["qr_code"] = out.cobranca.qr_code
        concluir_chave(
            chave_id=chave_id,
            tenant_id=tenant_id,
            response_status=status.HTTP_201_CREATED,
            response_body_resumo=body,
        )
        return Response(body, status=status.HTTP_201_CREATED)

    # ---------------------------------------------------------------- POST emitir-pix (Fatia 2b)
    @action(detail=True, methods=["post"], url_path="emitir-pix")
    def emitir_pix_recorrente(self, request: Request, pk: str | None = None) -> Response:
        """POST — US-CR-002 emitir PIX recorrente. # idempotency-key: required"""
        s = EmitirPixRecorrenteSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        d = s.validated_data

        tenant_id = _tenant_ou_none()
        if tenant_id is None:
            return Response({"erro": "tenant ausente"}, status=status.HTTP_403_FORBIDDEN)

        titulo_id = self._uuid_ou_404(pk)
        usuario_id = usuario_id_context.get() or UUID(int=0)

        novo, resp = _aplicar_idempotencia(
            request,
            tenant_id=tenant_id,
            usuario_id=usuario_id,
            endpoint=ENDPOINT_EMITIR_PIX,
            payload_fingerprint={
                "titulo_id": str(titulo_id),
                "convenio_pix_id": d.get("convenio_pix_id", ""),
            },
        )
        if resp is not None:
            return resp
        assert novo is not None and novo.chave_id is not None
        chave_id = novo.chave_id

        repo = DjangoTituloRepository()
        provider = _obter_provider()
        try:
            inp = emitir_cobranca.EmitirPixRecorrenteInput(
                tenant_id=tenant_id,
                titulo_id=titulo_id,
                convenio_pix_id=d.get("convenio_pix_id", ""),
            )
            with transaction.atomic():
                self._advisory_lock(f"cr:emitir_pix:{tenant_id}:{titulo_id}")
                out = emitir_cobranca.emitir_pix_recorrente(inp, repo=repo, provider=provider)
                _publicar_evento_cr(
                    acao="contas_receber.boleto_emitido",
                    payload={
                        "titulo_id": str(titulo_id),
                        "gateway_externo_id": out.titulo.gateway_externo_id,
                        "convenio_pix_id": out.titulo.convenio_pix_id,
                        "meio": "pix_recorrente",
                        "perfil_no_evento": out.titulo.perfil_no_evento,
                    },
                    causation_id=chave_id,
                    tenant_id=tenant_id,
                    usuario_id=usuario_id,
                    resource_summary=f"titulo_receber {titulo_id} pix_recorrente emitido",
                )
        except TituloNaoEncontrado as exc:
            return self._falha(chave_id, tenant_id, exc, status.HTTP_404_NOT_FOUND)
        except ConvenioPixAusente as exc:
            return self._falha(chave_id, tenant_id, exc, status.HTTP_422_UNPROCESSABLE_ENTITY)
        except TransicaoProibida as exc:
            return self._falha(chave_id, tenant_id, exc, status.HTTP_409_CONFLICT)
        except GatewayIndisponivel as exc:
            try:
                with transaction.atomic():
                    _publicar_evento_cr(
                        acao="contas_receber.gateway_indisponivel",
                        payload={
                            "titulo_id": str(titulo_id),
                            "retry_em_segundos": 60,
                            "detalhe": str(exc),
                        },
                        causation_id=chave_id,
                        tenant_id=tenant_id,
                        usuario_id=usuario_id,
                        resource_summary=f"gateway_indisponivel pix {titulo_id}",
                    )
            except Exception:
                logger.warning("falha ao publicar gateway_indisponivel pix", exc_info=True)
            return self._falha(
                chave_id, tenant_id, exc, status.HTTP_503_SERVICE_UNAVAILABLE
            )
        except ValueError as exc:
            return self._falha(chave_id, tenant_id, exc, status.HTTP_400_BAD_REQUEST)

        body = _serializar_titulo(out.titulo)
        body["gateway_externo_id"] = out.recorrencia.gateway_id
        body["convenio_pix_id"] = out.recorrencia.convenio_id
        concluir_chave(
            chave_id=chave_id,
            tenant_id=tenant_id,
            response_status=status.HTTP_201_CREATED,
            response_body_resumo=body,
        )
        return Response(body, status=status.HTTP_201_CREATED)

    # ---------------------------------------------------------------- POST override-bloqueio (Fatia 2b)
    @action(detail=False, methods=["post"], url_path="override-bloqueio")
    def override_bloqueio(self, request: Request) -> Response:
        """POST — D-CR-10 override de bloqueio de inadimplência (papel gerente).
        # idempotency-key: required
        """
        s = OverrideBloqueioSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        d = s.validated_data

        tenant_id = _tenant_ou_none()
        if tenant_id is None:
            return Response({"erro": "tenant ausente"}, status=status.HTTP_403_FORBIDDEN)

        perfil_str = _obter_perfil_ou_fail()
        if not perfil_str:
            return Response(
                {"erro": "perfil regulatório indisponível (fail-closed ADR-0067)"},
                status=status.HTTP_403_FORBIDDEN,
            )

        usuario_id = usuario_id_context.get() or UUID(int=0)

        novo, resp = _aplicar_idempotencia(
            request,
            tenant_id=tenant_id,
            usuario_id=usuario_id,
            endpoint=ENDPOINT_OVERRIDE,
            payload_fingerprint={
                "titulo_id": str(d["titulo_id"]),
                "cliente_id": str(d["cliente_id"]),
                "novo_prazo_max_dias": d["novo_prazo_max_dias"],
            },
        )
        if resp is not None:
            return resp
        assert novo is not None and novo.chave_id is not None
        chave_id = novo.chave_id

        repo = DjangoTituloRepository()
        try:
            inp = uc_override.OverrideBloqueioInput(
                tenant_id=tenant_id,
                titulo_id=d["titulo_id"],
                cliente_id=d["cliente_id"],
                novo_prazo_max_dias=d["novo_prazo_max_dias"],
                justificativa=d["justificativa"],
                a3_signature_id=d.get("a3_signature_id", "wave-a-stub"),
                usuario_id=usuario_id,
                perfil_no_evento=perfil_str,
            )
            with transaction.atomic():
                self._advisory_lock(
                    f"cr:override:{tenant_id}:{d['titulo_id']}:{d['cliente_id']}"
                )
                out = uc_override.executar(inp, repo=repo)
        except TituloNaoEncontrado as exc:
            return self._falha(chave_id, tenant_id, exc, status.HTTP_404_NOT_FOUND)
        except JustificativaInsuficiente as exc:
            return self._falha(chave_id, tenant_id, exc, status.HTTP_422_UNPROCESSABLE_ENTITY)
        except OverrideForaDeAlcada as exc:
            return self._falha(chave_id, tenant_id, exc, status.HTTP_422_UNPROCESSABLE_ENTITY)
        except ValueError as exc:
            return self._falha(chave_id, tenant_id, exc, status.HTTP_400_BAD_REQUEST)

        body = {
            "override_id": str(out.override.override_id),
            "titulo_id": str(out.override.titulo_id),
            "cliente_id": str(out.override.cliente_id),
            "novo_prazo_max_dias": out.override.novo_prazo_max_dias,
            "criado_em": out.override.criado_em.isoformat(),
            "perfil_no_evento": out.override.perfil_no_evento,
        }
        concluir_chave(
            chave_id=chave_id,
            tenant_id=tenant_id,
            response_status=status.HTTP_201_CREATED,
            response_body_resumo=body,
        )
        return Response(body, status=status.HTTP_201_CREATED)

    # ---------------------------------------------------------------- helpers
    @staticmethod
    def _advisory_lock(chave: str) -> None:
        """Advisory lock transacional para serializar operações concorrentes."""
        with connection.cursor() as cur:
            cur.execute("SELECT pg_advisory_xact_lock(hashtext(%s))", [chave])

    @staticmethod
    def _uuid_ou_404(raw: str | None) -> UUID:
        try:
            return UUID(str(raw))
        except (ValueError, TypeError) as exc:
            raise NotFound(f"id inválido: {exc}") from exc

    @staticmethod
    def _falha(chave_id: UUID, tenant_id: UUID, exc: Exception, http_status_code: int) -> Response:
        falhar_chave(chave_id=chave_id, tenant_id=tenant_id, response_status=http_status_code)
        return Response({"erro": str(exc)}, status=http_status_code)
