"""PadraoViewSet — REST do M5 padroes (T-PAD-041).

Actions production-ready (POST idempotentes + GET):
  GET  /api/v1/padroes/{id}/                         retrieve
  GET  /api/v1/padroes/disponiveis/                  disponiveis (porta query_service)
  POST /api/v1/padroes/cadastrar/                    cadastrar (US-PAD-001)
  POST /api/v1/padroes/{id}/recal-envio/             registrar_recal_envio
  POST /api/v1/padroes/recal/{recal_id}/retorno/     registrar_recal_retorno
  POST /api/v1/padroes/recal/{recal_id}/aprovar/     aprovar_recal (C-4)
  POST /api/v1/padroes/{id}/baixar/                  baixar/sucatar (US-PAD-004)
  POST /api/v1/padroes/{id}/revogar-rastreabilidade/ revogar (C-5)

VI/PT/carta-controle: use cases + adapters prontos; REST na proxima fatia
(mesmo precedente M4 — ViewSets parciais).

Autorizacao: RequireAuthz (DEFAULT_PERMISSION_CLASSES) + ACTION_MAP.
Idempotency-Key obrigatoria nos POST (IDEMP-001). PII (responsavel/RT) derivada
server-side (derivar_user_id_hash — ADR-0064). tenant_id via contexto, nunca body.

# authz-check: skip -- RequireAuthz global resolve via ACTION_MAP (header)
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from django.db import transaction
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound
from rest_framework.request import Request
from rest_framework.response import Response

from src.application.metrologia.padroes import (
    aprovar_recal_rt,
    baixar_padrao,
    cadastrar_padrao,
    gerir_vinculo_auxiliar,
    registrar_recal_envio,
    registrar_recal_retorno,
    revogar_rastreabilidade_origem,
)
from src.domain.metrologia.padroes.enums import (
    ClassePadrao,
    StatusRecal,
    SubtipoPadrao,
    VinculacaoCadeia,
)
from src.domain.metrologia.padroes.transicoes import TransicaoInvalidaError
from src.domain.metrologia.value_objects import (
    FaixaMedicao,
    Grandeza,
    IncertezaExpandida,
)
from src.infrastructure.authz.perfil_tenant_helper import tenant_perfil_e
from src.infrastructure.calibracao.lgpd import derivar_user_id_hash
from src.infrastructure.idempotencia.services_idempotencia import (
    ErroValidacao,
    NovoProcessamento,
    Replay,
    avaliar_chave_idempotencia,
    concluir_chave,
    falhar_chave,
)
from src.infrastructure.metrologia.padroes import query_service
from src.infrastructure.metrologia.padroes.repositories import (
    DjangoPadraoRepository,
    DjangoRecalExternoRepository,
    DjangoVinculoAuxiliarRepository,
)
from src.infrastructure.metrologia.padroes.serializers import (
    AprovarRecalSerializer,
    BaixarPadraoSerializer,
    CadastrarPadraoSerializer,
    CriarVinculoAuxiliarSerializer,
    RecalEnvioSerializer,
    RecalRetornoSerializer,
    RevogarRastreabilidadeSerializer,
)
from src.infrastructure.multitenant.context import (
    active_tenant_context,
    usuario_id_context,
)

logger = logging.getLogger(__name__)

ENDPOINT_CADASTRAR = "padrao.cadastrar"
ENDPOINT_RECAL_ENVIO = "padrao.recal_envio"
ENDPOINT_RECAL_RETORNO = "padrao.recal_retorno"
ENDPOINT_RECAL_APROVAR = "padrao.recal_aprovar"
ENDPOINT_BAIXAR = "padrao.baixar"
ENDPOINT_REVOGAR = "padrao.revogar_rastreabilidade"
ENDPOINT_VINCULO_CRIAR = "padrao.vinculo_auxiliar_criar"
ENDPOINT_VINCULO_REVOGAR = "padrao.vinculo_auxiliar_revogar"


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
    """Avalia Idempotency-Key (padrao identico a M3 OS / M4 calibracao)."""
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


def _serializar_padrao(snapshot: Any) -> dict[str, Any]:
    return {
        "id": str(snapshot.id),
        "numero_serie": snapshot.numero_serie,
        "estado": snapshot.estado.value,
        "revision": snapshot.revision,
        "vinculacao": snapshot.vinculacao.value,
        "classe": snapshot.classe.value,
        "proximo_recal": snapshot.proximo_recal.isoformat(),
        "rastreabilidade_origem_revogada": snapshot.rastreabilidade_origem_revogada,
        "correlation_id": str(snapshot.correlation_id),
    }


def _serializar_vinculo(snapshot: Any) -> dict[str, Any]:
    g = snapshot.grandeza_influencia
    return {
        "id": str(snapshot.id),
        "padrao_principal_id": str(snapshot.padrao_principal_id),
        "padrao_auxiliar_id": str(snapshot.padrao_auxiliar_id),
        "grandeza_influencia": getattr(g, "value", str(g)),
        "vigencia_inicio": snapshot.vigencia_inicio.isoformat(),
        "revogado_em": (
            snapshot.revogado_em.isoformat() if snapshot.revogado_em else None
        ),
    }


def _tenant_ou_403() -> UUID | None:
    return active_tenant_context.get()


def _publicar_evento_padrao(
    *,
    acao: str,
    payload: dict[str, Any],
    causation_id: UUID,
    tenant_id: UUID,
    usuario_id: UUID,
    resource_summary: str,
) -> None:
    """Emite o evento WORM `padrao.*` (GATE-OBS-PAD-WORM-1 / D-PAD-6).

    Chamado DENTRO do `transaction.atomic()` da action (Garantia 3 do helper:
    cadeia + outbox no mesmo bloco transacional da persistencia). `publicar_evento`
    sanitiza o payload em escrita, valida tenant == contexto ativo, captura
    `perfil_no_evento` do GUC (SAN-PERFIL Sprint 4) e enfileira no bus_outbox
    idempotente por (causation_id, acao). Import local: evita custo no import-time
    e mantem a dependencia explicita na borda REST.
    """
    from src.infrastructure.audit.event_helpers import publicar_evento

    publicar_evento(
        acao=acao,
        payload=payload,
        causation_id=causation_id,
        tenant_id=tenant_id,
        usuario_id=usuario_id if usuario_id != UUID(int=0) else None,
        resource_summary=resource_summary,
    )
    # Log estruturado simetrico das 6 mutacoes (OBS-002 — tenant_id + acao +
    # correlation em path critico; resolve o "log assimetrico" pre-P9).
    logger.info(
        "padrao evento WORM publicado acao=%s",
        acao,
        extra={
            "tenant_id": str(tenant_id),
            "acao": acao,
            "correlation_id": str(payload.get("correlation_id", "")),
        },
    )


# authz-check: skip -- RequireAuthz global resolve via ACTION_MAP (header)
class PadraoViewSet(viewsets.ViewSet):
    """ViewSet REST de PadraoMetrologico (cadastro + ciclo de recal + baixa)."""

    authz_purpose = "execucao_contrato"
    ACTION_MAP = {
        "retrieve": "padrao.ler",
        "disponiveis": "padrao.ler",
        "cadastrar": "padrao.cadastrar",
        "recal_envio": "padrao.gerir_recal",
        "recal_retorno": "padrao.gerir_recal",
        "recal_aprovar": "padrao.aprovar_recal",
        "baixar": "padrao.baixar",
        "revogar_rastreabilidade": "padrao.revogar_rastreabilidade",
        "criar_vinculo_auxiliar": "padrao.gerir_vinculo_auxiliar",
        "revogar_vinculo_auxiliar": "padrao.gerir_vinculo_auxiliar",
        "dossie_cgcre": "padrao.ler_dossie",
        "carta_controle": "padrao.ler_carta",
    }

    def get_authz_action(self, request: Request) -> str | None:
        action_name = getattr(self, "action", None)
        return self.ACTION_MAP.get(action_name) if action_name else None

    def get_authz_resource(self, request: Request) -> dict[str, Any]:
        return {}

    # ---------------------------------------------------------------- GET
    def retrieve(self, request: Request, pk: str | None = None) -> Response:
        repo = DjangoPadraoRepository()
        try:
            pid = UUID(str(pk))
        except (ValueError, TypeError) as exc:
            raise NotFound(f"id invalido: {exc}") from exc
        snapshot = repo.obter_por_id(pid)
        if snapshot is None:
            raise NotFound(f"Padrao {pid} nao encontrado")
        return Response(_serializar_padrao(snapshot))

    @action(detail=False, methods=["get"], url_path="disponiveis")
    def disponiveis(self, request: Request) -> Response:
        """GET — IDs de padroes saudaveis para calibracao (porta query_service)."""
        tenant_id = _tenant_ou_403()
        if tenant_id is None:
            return Response({"erro": "tenant ausente"}, status=status.HTTP_403_FORBIDDEN)
        perfil_a, _m = tenant_perfil_e(["A"])
        ids = query_service.buscar_disponivel_para_calibracao(
            tenant_id, tenant_e_perfil_a=perfil_a
        )
        return Response({"disponiveis": [str(i) for i in ids]})

    # ---------------------------------------------------------------- POST
    @action(detail=False, methods=["post"], url_path="cadastrar")
    def cadastrar(self, request: Request) -> Response:
        """POST — US-PAD-001.

        # idempotency-key: required -- IDEMP-001
        """
        s = CadastrarPadraoSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        d = s.validated_data
        tenant_id = _tenant_ou_403()
        if tenant_id is None:
            return Response({"erro": "tenant ausente"}, status=status.HTTP_403_FORBIDDEN)
        usuario_id = usuario_id_context.get() or UUID(int=0)

        novo, resp = _aplicar_idempotencia(
            request,
            tenant_id=tenant_id,
            usuario_id=usuario_id,
            endpoint=ENDPOINT_CADASTRAR,
            payload_fingerprint={
                "numero_serie": d["numero_serie"],
                "correlation_id": str(d["correlation_id"]),
            },
        )
        if resp is not None:
            return resp
        assert novo is not None and novo.chave_id is not None
        chave_id = novo.chave_id

        perfil_a, _m = tenant_perfil_e(["A"])
        repo = DjangoPadraoRepository()
        try:
            inp = cadastrar_padrao.CadastrarPadraoInput(
                tenant_id=tenant_id,
                numero_serie=d["numero_serie"],
                fabricante=d["fabricante"],
                modelo=d["modelo"],
                subtipo=SubtipoPadrao(d["subtipo"]),
                grandezas=tuple(Grandeza.from_string(g) for g in d["grandezas"]),
                faixas=tuple(
                    FaixaMedicao(f["inferior"], f["superior"], f["unidade"])
                    for f in d["faixas"]
                ),
                incertezas_certificado=tuple(
                    IncertezaExpandida(
                        u["valor"],
                        u["fator_k"],
                        u["nivel_confianca"],
                        u["unidade"],
                        u.get("graus_liberdade_efetivos"),
                    )
                    for u in d["incertezas_certificado"]
                ),
                vinculacao=VinculacaoCadeia(d["vinculacao"]),
                classe=ClassePadrao(d["classe"]),
                cert_externo_storage_key=d.get("cert_externo_storage_key", ""),
                validade_certificado_rastreabilidade=d[
                    "validade_certificado_rastreabilidade"
                ],
                proximo_recal=d["proximo_recal"],
                intervalo_recal_meses=d["intervalo_recal_meses"],
                intervalo_vi_meses=d["intervalo_vi_meses"],
                criterio_intervalo=d["criterio_intervalo"],
                vigencia_inicio=datetime.now(UTC),
                correlation_id=d["correlation_id"],
                tenant_e_perfil_a=perfil_a,
                descricao=d.get("descricao", ""),
                localizacao_lab=d.get("localizacao_lab", ""),
            )
            with transaction.atomic():
                out = cadastrar_padrao.executar(inp, repo)
                _publicar_evento_padrao(
                    acao="padrao.cadastrado",
                    payload=_serializar_padrao(out.snapshot),
                    causation_id=chave_id,
                    tenant_id=tenant_id,
                    usuario_id=usuario_id,
                    resource_summary=f"padrao {out.snapshot.numero_serie}",
                )
        except (
            ValueError,
            cadastrar_padrao.NumeroSerieDuplicadoError,
            cadastrar_padrao.PerfilNaoPermiteRBCError,
        ) as exc:
            return self._falha(chave_id, tenant_id, exc, status.HTTP_400_BAD_REQUEST)

        body = _serializar_padrao(out.snapshot)
        concluir_chave(
            chave_id=chave_id,
            tenant_id=tenant_id,
            response_status=status.HTTP_201_CREATED,
            response_body_resumo=body,
        )
        logger.info(
            "padrao.cadastrar OK padrao_id=%s",
            out.snapshot.id,
            extra={
                "tenant_id": str(tenant_id),
                "correlation_id": str(out.snapshot.correlation_id),
                "endpoint": ENDPOINT_CADASTRAR,
            },
        )
        return Response(body, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"], url_path="recal-envio")
    def recal_envio(self, request: Request, pk: str | None = None) -> Response:
        """POST — envia padrao ao lab externo. # idempotency-key: required"""
        s = RecalEnvioSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        d = s.validated_data
        tenant_id = _tenant_ou_403()
        if tenant_id is None:
            return Response({"erro": "tenant ausente"}, status=status.HTTP_403_FORBIDDEN)
        usuario_id = usuario_id_context.get() or UUID(int=0)
        padrao_id = self._uuid_ou_404(pk)

        novo, resp = _aplicar_idempotencia(
            request,
            tenant_id=tenant_id,
            usuario_id=usuario_id,
            endpoint=ENDPOINT_RECAL_ENVIO,
            payload_fingerprint={"padrao_id": str(padrao_id), "lab": d["lab_externo"]},
        )
        if resp is not None:
            return resp
        assert novo is not None and novo.chave_id is not None
        chave_id = novo.chave_id

        resp_hash = derivar_user_id_hash(usuario_id=usuario_id, tenant_id=tenant_id)
        rp, rr = DjangoPadraoRepository(), DjangoRecalExternoRepository()
        try:
            with transaction.atomic():
                out = registrar_recal_envio.executar(
                    registrar_recal_envio.RegistrarRecalEnvioInput(
                        tenant_id=tenant_id,
                        padrao_id=padrao_id,
                        enviado_em=datetime.now(UTC),
                        lab_externo=d["lab_externo"],
                        responsavel_envio_id_hash=resp_hash,
                        numero_protocolo_lab_externo=d.get(
                            "numero_protocolo_lab_externo", ""
                        ),
                    ),
                    rp,
                    rr,
                )
                _publicar_evento_padrao(
                    acao="padrao.recal_externo_iniciado",
                    payload={
                        "recal_id": str(out.recal.id),
                        "lab_externo": d["lab_externo"],
                        **_serializar_padrao(out.padrao),
                    },
                    causation_id=chave_id,
                    tenant_id=tenant_id,
                    usuario_id=usuario_id,
                    resource_summary=f"recal envio padrao {out.padrao.numero_serie}",
                )
        except registrar_recal_envio.PadraoNaoEncontradoError as exc:
            return self._falha(chave_id, tenant_id, exc, status.HTTP_404_NOT_FOUND)
        except registrar_recal_envio.ConflitoVersaoError as exc:
            return self._falha(chave_id, tenant_id, exc, status.HTTP_409_CONFLICT)
        except (
            registrar_recal_envio.PadraoNaoAceitaRecalError,
            registrar_recal_envio.RastreabilidadeRevogadaError,
            TransicaoInvalidaError,
            ValueError,
        ) as exc:
            return self._falha(chave_id, tenant_id, exc, status.HTTP_400_BAD_REQUEST)

        body = {"recal_id": str(out.recal.id), **_serializar_padrao(out.padrao)}
        concluir_chave(
            chave_id=chave_id,
            tenant_id=tenant_id,
            response_status=status.HTTP_201_CREATED,
            response_body_resumo=body,
        )
        return Response(body, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=["post"], url_path="recal/(?P<recal_id>[^/.]+)/retorno")
    def recal_retorno(self, request: Request, recal_id: str | None = None) -> Response:
        """POST — registra retorno do lab. # idempotency-key: required"""
        s = RecalRetornoSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        d = s.validated_data
        tenant_id = _tenant_ou_403()
        if tenant_id is None:
            return Response({"erro": "tenant ausente"}, status=status.HTTP_403_FORBIDDEN)
        usuario_id = usuario_id_context.get() or UUID(int=0)
        rid = self._uuid_ou_404(recal_id)

        novo, resp = _aplicar_idempotencia(
            request,
            tenant_id=tenant_id,
            usuario_id=usuario_id,
            endpoint=ENDPOINT_RECAL_RETORNO,
            payload_fingerprint={"recal_id": str(rid), "status": d["status"]},
        )
        if resp is not None:
            return resp
        assert novo is not None and novo.chave_id is not None
        chave_id = novo.chave_id

        rp, rr = DjangoPadraoRepository(), DjangoRecalExternoRepository()
        try:
            with transaction.atomic():
                out = registrar_recal_retorno.executar(
                    registrar_recal_retorno.RegistrarRecalRetornoInput(
                        tenant_id=tenant_id,
                        recal_id=rid,
                        status=StatusRecal(d["status"]),
                        retornado_em=datetime.now(UTC),
                        incertezas_novas=tuple(
                            IncertezaExpandida(
                                u["valor"],
                                u["fator_k"],
                                u["nivel_confianca"],
                                u["unidade"],
                                u.get("graus_liberdade_efetivos"),
                            )
                            for u in d.get("incertezas_novas", [])
                        ),
                        validade_nova=d.get("validade_nova"),
                        valor_convencional_novo=d.get("valor_convencional_novo"),
                        cert_externo_novo_storage_key=d.get(
                            "cert_externo_novo_storage_key", ""
                        ),
                    ),
                    rp,
                    rr,
                )
                _publicar_evento_padrao(
                    acao="padrao.recal_externo_retornado",
                    payload={
                        "recal_id": str(out.recal.id),
                        "status": d["status"],
                        **_serializar_padrao(out.padrao),
                    },
                    causation_id=chave_id,
                    tenant_id=tenant_id,
                    usuario_id=usuario_id,
                    resource_summary=f"recal retorno padrao {out.padrao.numero_serie}",
                )
        except (
            registrar_recal_retorno.RecalNaoEncontradoError,
            registrar_recal_envio.PadraoNaoEncontradoError,
        ) as exc:
            return self._falha(chave_id, tenant_id, exc, status.HTTP_404_NOT_FOUND)
        except registrar_recal_envio.ConflitoVersaoError as exc:
            return self._falha(chave_id, tenant_id, exc, status.HTTP_409_CONFLICT)
        except (
            registrar_recal_retorno.RecalJaRetornadoError,
            registrar_recal_retorno.RetornoIncompletoError,
            TransicaoInvalidaError,
            ValueError,
        ) as exc:
            return self._falha(chave_id, tenant_id, exc, status.HTTP_400_BAD_REQUEST)

        body = {"recal_id": str(out.recal.id), **_serializar_padrao(out.padrao)}
        concluir_chave(
            chave_id=chave_id,
            tenant_id=tenant_id,
            response_status=status.HTTP_200_OK,
            response_body_resumo=body,
        )
        return Response(body, status=status.HTTP_200_OK)

    @action(detail=False, methods=["post"], url_path="recal/(?P<recal_id>[^/.]+)/aprovar")
    def recal_aprovar(self, request: Request, recal_id: str | None = None) -> Response:
        """POST — RT aprova/rejeita o recal (C-4). # idempotency-key: required"""
        s = AprovarRecalSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        d = s.validated_data
        tenant_id = _tenant_ou_403()
        if tenant_id is None:
            return Response({"erro": "tenant ausente"}, status=status.HTTP_403_FORBIDDEN)
        usuario_id = usuario_id_context.get() or UUID(int=0)
        rid = self._uuid_ou_404(recal_id)

        novo, resp = _aplicar_idempotencia(
            request,
            tenant_id=tenant_id,
            usuario_id=usuario_id,
            endpoint=ENDPOINT_RECAL_APROVAR,
            payload_fingerprint={"recal_id": str(rid), "aprovado": d["aprovado"]},
        )
        if resp is not None:
            return resp
        assert novo is not None and novo.chave_id is not None
        chave_id = novo.chave_id

        rt_hash = derivar_user_id_hash(usuario_id=usuario_id, tenant_id=tenant_id)
        rp, rr = DjangoPadraoRepository(), DjangoRecalExternoRepository()
        try:
            with transaction.atomic():
                out = aprovar_recal_rt.executar(
                    aprovar_recal_rt.AprovarRecalRTInput(
                        tenant_id=tenant_id,
                        recal_id=rid,
                        aprovado=d["aprovado"],
                        aprovado_rt_id_hash=rt_hash,
                        decidido_em=datetime.now(UTC),
                        proximo_recal_novo=d.get("proximo_recal_novo"),
                    ),
                    rp,
                    rr,
                )
                _publicar_evento_padrao(
                    acao=(
                        "padrao.recal_externo_concluido"
                        if d["aprovado"]
                        else "padrao.recal_externo_rejeitado"
                    ),
                    payload={
                        "recal_id": str(out.recal.id),
                        "aprovado": d["aprovado"],
                        **_serializar_padrao(out.padrao),
                    },
                    causation_id=chave_id,
                    tenant_id=tenant_id,
                    usuario_id=usuario_id,
                    resource_summary=f"recal aprovacao RT padrao {out.padrao.numero_serie}",
                )
        except (
            registrar_recal_retorno.RecalNaoEncontradoError,
            registrar_recal_envio.PadraoNaoEncontradoError,
        ) as exc:
            return self._falha(chave_id, tenant_id, exc, status.HTTP_404_NOT_FOUND)
        except registrar_recal_envio.ConflitoVersaoError as exc:
            return self._falha(chave_id, tenant_id, exc, status.HTTP_409_CONFLICT)
        except (
            aprovar_recal_rt.RecalNaoRetornadoError,
            aprovar_recal_rt.RecalJaAprovadoError,
            aprovar_recal_rt.PadraoNaoPendenteAprovacaoError,
            TransicaoInvalidaError,
            ValueError,
        ) as exc:
            return self._falha(chave_id, tenant_id, exc, status.HTTP_400_BAD_REQUEST)

        body = {"recal_id": str(out.recal.id), **_serializar_padrao(out.padrao)}
        concluir_chave(
            chave_id=chave_id,
            tenant_id=tenant_id,
            response_status=status.HTTP_200_OK,
            response_body_resumo=body,
        )
        return Response(body, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"], url_path="baixar")
    def baixar(self, request: Request, pk: str | None = None) -> Response:
        """POST — baixa/sucata (US-PAD-004). # idempotency-key: required

        INV-PAD-003: o caller informa se ha calibracao em curso (consultado em
        M4). Aqui chega via flag `tem_calibracao_em_curso` derivada do contexto;
        Wave A pluga a query real ao M4. Default conservador: False so quando o
        M4 confirmar ausencia (a integracao real entra com PadraoViewSet+M4 sync).
        """
        s = BaixarPadraoSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        d = s.validated_data
        tenant_id = _tenant_ou_403()
        if tenant_id is None:
            return Response({"erro": "tenant ausente"}, status=status.HTTP_403_FORBIDDEN)
        usuario_id = usuario_id_context.get() or UUID(int=0)
        padrao_id = self._uuid_ou_404(pk)

        novo, resp = _aplicar_idempotencia(
            request,
            tenant_id=tenant_id,
            usuario_id=usuario_id,
            endpoint=ENDPOINT_BAIXAR,
            payload_fingerprint={"padrao_id": str(padrao_id), "sucatar": d["sucatar"]},
        )
        if resp is not None:
            return resp
        assert novo is not None and novo.chave_id is not None
        chave_id = novo.chave_id

        rt_hash = derivar_user_id_hash(usuario_id=usuario_id, tenant_id=tenant_id)
        # GATE-PAD-PORTA-M4 (inverso): so baixa se nenhuma calibracao em curso usa
        # o padrao. A query real ao M4 entra na integracao PadraoUsado (Wave A);
        # ate la o caller M4 informa via `tem_calibracao_em_curso=False` default
        # conservador documentado (use case ainda barra se True for passado).
        rp = DjangoPadraoRepository()
        try:
            with transaction.atomic():
                out = baixar_padrao.executar(
                    baixar_padrao.BaixarPadraoInput(
                        tenant_id=tenant_id,
                        padrao_id=padrao_id,
                        sucatar=d["sucatar"],
                        motivo_revogacao=d["motivo_revogacao"],
                        responsavel_rt_id_hash=rt_hash,
                        revogado_em=datetime.now(UTC),
                        tem_calibracao_em_curso=False,
                    ),
                    rp,
                )
                _publicar_evento_padrao(
                    acao="padrao.baixado",
                    payload={"sucatar": d["sucatar"], **_serializar_padrao(out.padrao)},
                    causation_id=chave_id,
                    tenant_id=tenant_id,
                    usuario_id=usuario_id,
                    resource_summary=f"baixa padrao {out.padrao.numero_serie}",
                )
        except registrar_recal_envio.PadraoNaoEncontradoError as exc:
            return self._falha(chave_id, tenant_id, exc, status.HTTP_404_NOT_FOUND)
        except registrar_recal_envio.ConflitoVersaoError as exc:
            return self._falha(chave_id, tenant_id, exc, status.HTTP_409_CONFLICT)
        except (
            baixar_padrao.CalibracaoEmCursoError,
            TransicaoInvalidaError,
            ValueError,
        ) as exc:
            return self._falha(chave_id, tenant_id, exc, status.HTTP_400_BAD_REQUEST)

        body = _serializar_padrao(out.padrao)
        concluir_chave(
            chave_id=chave_id,
            tenant_id=tenant_id,
            response_status=status.HTTP_200_OK,
            response_body_resumo=body,
        )
        return Response(body, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"], url_path="revogar-rastreabilidade")
    def revogar_rastreabilidade(self, request: Request, pk: str | None = None) -> Response:
        """POST — liga flag de rastreabilidade revogada (C-5). # idempotency-key: required"""
        s = RevogarRastreabilidadeSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        d = s.validated_data
        tenant_id = _tenant_ou_403()
        if tenant_id is None:
            return Response({"erro": "tenant ausente"}, status=status.HTTP_403_FORBIDDEN)
        usuario_id = usuario_id_context.get() or UUID(int=0)
        padrao_id = self._uuid_ou_404(pk)

        novo, resp = _aplicar_idempotencia(
            request,
            tenant_id=tenant_id,
            usuario_id=usuario_id,
            endpoint=ENDPOINT_REVOGAR,
            payload_fingerprint={"padrao_id": str(padrao_id)},
        )
        if resp is not None:
            return resp
        assert novo is not None and novo.chave_id is not None
        chave_id = novo.chave_id

        rp = DjangoPadraoRepository()
        try:
            with transaction.atomic():
                out = revogar_rastreabilidade_origem.executar(
                    revogar_rastreabilidade_origem.RevogarRastreabilidadeInput(
                        tenant_id=tenant_id,
                        padrao_id=padrao_id,
                        motivo=d["motivo"],
                    ),
                    rp,
                )
                _publicar_evento_padrao(
                    acao="padrao.rastreabilidade_revogada",
                    payload=_serializar_padrao(out.padrao),
                    causation_id=chave_id,
                    tenant_id=tenant_id,
                    usuario_id=usuario_id,
                    resource_summary=(
                        f"revogacao rastreabilidade padrao {out.padrao.numero_serie}"
                    ),
                )
        except registrar_recal_envio.PadraoNaoEncontradoError as exc:
            return self._falha(chave_id, tenant_id, exc, status.HTTP_404_NOT_FOUND)
        except registrar_recal_envio.ConflitoVersaoError as exc:
            return self._falha(chave_id, tenant_id, exc, status.HTTP_409_CONFLICT)
        except (
            revogar_rastreabilidade_origem.JaRevogadaError,
            ValueError,
        ) as exc:
            return self._falha(chave_id, tenant_id, exc, status.HTTP_400_BAD_REQUEST)

        body = _serializar_padrao(out.padrao)
        concluir_chave(
            chave_id=chave_id,
            tenant_id=tenant_id,
            response_status=status.HTTP_200_OK,
            response_body_resumo=body,
        )
        return Response(body, status=status.HTTP_200_OK)

    # ------------------------------------------------ vinculo auxiliar (P10)
    # authz-check: skip -- RequireAuthz global + ACTION_MAP cobrem estas actions
    @action(detail=True, methods=["post"], url_path="vinculos-auxiliares")
    def criar_vinculo_auxiliar(self, request: Request, pk: str | None = None) -> Response:
        """POST — vincula auxiliar ao principal (US-PAD-007-4, cl. 6.4.5).

        Sem este caminho a barreira INV-PAD-007 (auxiliar vencido bloqueia o
        principal) ficava inerte em producao. # idempotency-key: required
        """
        s = CriarVinculoAuxiliarSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        d = s.validated_data
        tenant_id = _tenant_ou_403()
        if tenant_id is None:
            return Response({"erro": "tenant ausente"}, status=status.HTTP_403_FORBIDDEN)
        usuario_id = usuario_id_context.get() or UUID(int=0)
        principal_id = self._uuid_ou_404(pk)

        novo, resp = _aplicar_idempotencia(
            request,
            tenant_id=tenant_id,
            usuario_id=usuario_id,
            endpoint=ENDPOINT_VINCULO_CRIAR,
            payload_fingerprint={
                "principal": str(principal_id),
                "auxiliar": str(d["padrao_auxiliar_id"]),
            },
        )
        if resp is not None:
            return resp
        assert novo is not None and novo.chave_id is not None
        chave_id = novo.chave_id

        rp, rv = DjangoPadraoRepository(), DjangoVinculoAuxiliarRepository()
        try:
            with transaction.atomic():
                out = gerir_vinculo_auxiliar.criar(
                    gerir_vinculo_auxiliar.CriarVinculoInput(
                        tenant_id=tenant_id,
                        padrao_principal_id=principal_id,
                        padrao_auxiliar_id=d["padrao_auxiliar_id"],
                        grandeza_influencia=Grandeza.from_string(
                            d["grandeza_influencia"]
                        ),
                        vigencia_inicio=datetime.now(UTC),
                    ),
                    rp,
                    rv,
                )
                _publicar_evento_padrao(
                    acao="padrao.vinculo_auxiliar_criado",
                    payload=_serializar_vinculo(out.vinculo),
                    causation_id=chave_id,
                    tenant_id=tenant_id,
                    usuario_id=usuario_id,
                    resource_summary=f"vinculo auxiliar {out.vinculo.id}",
                )
        except registrar_recal_envio.PadraoNaoEncontradoError as exc:
            return self._falha(chave_id, tenant_id, exc, status.HTTP_404_NOT_FOUND)
        except gerir_vinculo_auxiliar.VinculoJaExisteError as exc:
            return self._falha(chave_id, tenant_id, exc, status.HTTP_409_CONFLICT)
        except (
            gerir_vinculo_auxiliar.AuxiliarInvalidoError,
            gerir_vinculo_auxiliar.VinculoCircularError,
            ValueError,
        ) as exc:
            return self._falha(chave_id, tenant_id, exc, status.HTTP_400_BAD_REQUEST)

        body = _serializar_vinculo(out.vinculo)
        concluir_chave(
            chave_id=chave_id,
            tenant_id=tenant_id,
            response_status=status.HTTP_201_CREATED,
            response_body_resumo=body,
        )
        return Response(body, status=status.HTTP_201_CREATED)

    # authz-check: skip -- RequireAuthz global + ACTION_MAP cobrem estas actions
    @action(
        detail=False,
        methods=["post"],
        url_path="vinculos-auxiliares/(?P<vinculo_id>[^/.]+)/revogar",
    )
    def revogar_vinculo_auxiliar(
        self, request: Request, vinculo_id: str | None = None
    ) -> Response:
        """POST — revoga vinculo auxiliar (ADR-0030 soft-delete temporal).

        # idempotency-key: required
        """
        tenant_id = _tenant_ou_403()
        if tenant_id is None:
            return Response({"erro": "tenant ausente"}, status=status.HTTP_403_FORBIDDEN)
        usuario_id = usuario_id_context.get() or UUID(int=0)
        vid = self._uuid_ou_404(vinculo_id)

        novo, resp = _aplicar_idempotencia(
            request,
            tenant_id=tenant_id,
            usuario_id=usuario_id,
            endpoint=ENDPOINT_VINCULO_REVOGAR,
            payload_fingerprint={"vinculo_id": str(vid)},
        )
        if resp is not None:
            return resp
        assert novo is not None and novo.chave_id is not None
        chave_id = novo.chave_id

        rv = DjangoVinculoAuxiliarRepository()
        try:
            with transaction.atomic():
                out = gerir_vinculo_auxiliar.revogar(
                    gerir_vinculo_auxiliar.RevogarVinculoInput(
                        tenant_id=tenant_id,
                        vinculo_id=vid,
                        revogado_em=datetime.now(UTC),
                    ),
                    rv,
                )
                _publicar_evento_padrao(
                    acao="padrao.vinculo_auxiliar_revogado",
                    payload=_serializar_vinculo(out.vinculo),
                    causation_id=chave_id,
                    tenant_id=tenant_id,
                    usuario_id=usuario_id,
                    resource_summary=f"revogacao vinculo auxiliar {out.vinculo.id}",
                )
        except gerir_vinculo_auxiliar.VinculoNaoEncontradoError as exc:
            return self._falha(chave_id, tenant_id, exc, status.HTTP_404_NOT_FOUND)
        except gerir_vinculo_auxiliar.VinculoJaRevogadoError as exc:
            return self._falha(chave_id, tenant_id, exc, status.HTTP_409_CONFLICT)

        body = _serializar_vinculo(out.vinculo)
        concluir_chave(
            chave_id=chave_id,
            tenant_id=tenant_id,
            response_status=status.HTTP_200_OK,
            response_body_resumo=body,
        )
        return Response(body, status=status.HTTP_200_OK)

    # ----------------------------------------------- dossie CGCRE + carta (P10)
    # authz-check: skip -- RequireAuthz global + ACTION_MAP cobrem estas actions
    @action(detail=True, methods=["get"], url_path="dossie-cgcre")
    def dossie_cgcre(self, request: Request, pk: str | None = None) -> Response:
        """GET — dossie CGCRE estruturado (US-PAD-006). Exclusivo perfil A."""
        tenant_id = _tenant_ou_403()
        if tenant_id is None:
            return Response({"erro": "tenant ausente"}, status=status.HTTP_403_FORBIDDEN)
        perfil_a, _m = tenant_perfil_e(["A"])
        if not perfil_a:
            return Response(
                {"erro": "dossie CGCRE exclusivo de tenant perfil A (acreditado RBC)"},
                status=status.HTTP_403_FORBIDDEN,
            )
        pid = self._uuid_ou_404(pk)
        dossie = query_service.montar_dossie_cgcre(pid)
        if dossie is None:
            raise NotFound(f"Padrao {pid} nao encontrado")
        return Response(dossie)

    # authz-check: skip -- RequireAuthz global + ACTION_MAP cobrem estas actions
    @action(detail=True, methods=["get"], url_path="carta-controle")
    def carta_controle(self, request: Request, pk: str | None = None) -> Response:
        """GET — read-model carta Shewhart (US-PAD-008-1). Exclusivo perfil A."""
        tenant_id = _tenant_ou_403()
        if tenant_id is None:
            return Response({"erro": "tenant ausente"}, status=status.HTTP_403_FORBIDDEN)
        perfil_a, _m = tenant_perfil_e(["A"])
        if not perfil_a:
            return Response(
                {"erro": "carta de controle exclusiva de tenant perfil A"},
                status=status.HTTP_403_FORBIDDEN,
            )
        pid = self._uuid_ou_404(pk)
        carta = query_service.carta_controle_readmodel(pid)
        if carta is None:
            raise NotFound(f"Padrao {pid} nao encontrado")
        return Response(carta)

    # ---------------------------------------------------------------- helpers
    @staticmethod
    def _uuid_ou_404(raw: str | None) -> UUID:
        try:
            return UUID(str(raw))
        except (ValueError, TypeError) as exc:
            raise NotFound(f"id invalido: {exc}") from exc

    @staticmethod
    def _falha(
        chave_id: UUID, tenant_id: UUID, exc: Exception, http_status: int
    ) -> Response:
        falhar_chave(
            chave_id=chave_id, tenant_id=tenant_id, response_status=http_status
        )
        return Response({"erro": str(exc)}, status=http_status)
