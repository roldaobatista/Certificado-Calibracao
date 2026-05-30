"""EscopoCMCViewSet — REST do M6 escopos-cmc (T-ECMC-031).

Actions:
  GET  /api/v1/escopos-cmc/{id}/            retrieve
  GET  /api/v1/escopos-cmc/vigentes/        vigentes?grandeza= (cobertura atual)
  POST /api/v1/escopos-cmc/cadastrar/       cadastrar (US-ECMC-001 — perfil A escopo RBC)
  POST /api/v1/escopos-cmc/declarar-capacidade/ declarar_capacidade (US-ECMC-007 — B/C/D)
  POST /api/v1/escopos-cmc/{id}/revisar/    revisar (US-ECMC-002 — nova versão)
  POST /api/v1/escopos-cmc/{id}/revogar/    revogar (US-ECMC-003)

Autorização: RequireAuthz (DEFAULT_PERMISSION_CLASSES) + ACTION_MAP. Idempotency-Key
obrigatória nos POST (IDEMP-001). Perfil regulatório via contexto (ADR-0067), nunca
payload; `rbc_acreditado` efetivo forçado por perfil (anti-fraude ADR-0075). tenant
via contexto. Eventos WORM na cadeia hash (TL-C-06).

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

from src.application.metrologia.escopos_cmc import (
    cadastrar_escopo,
    confirmar_escopo_extraido,
    importar_escopo_pdf,
    revisar_escopo,
    revogar_escopo,
)
from src.domain.metrologia.escopos_cmc.enums import FormaCMC
from src.domain.metrologia.escopos_cmc.extracao import MapaColunas
from src.domain.metrologia.value_objects import FaixaMedicao, Grandeza
from src.infrastructure.authz.perfil_tenant_helper import obter_perfil_tenant_corrente
from src.infrastructure.calibracao.lgpd import derivar_user_id_hash
from src.infrastructure.idempotencia.services_idempotencia import (
    ErroValidacao,
    NovoProcessamento,
    Replay,
    avaliar_chave_idempotencia,
    concluir_chave,
    falhar_chave,
)
from src.infrastructure.metrologia.escopos_cmc.repositories import (
    DjangoEscopoExtraidoRepository,
    DjangoEscopoRepository,
)
from src.infrastructure.metrologia.escopos_cmc.serializers import (
    CadastrarEscopoSerializer,
    ConfirmarExtraidoSerializer,
    ImportarExtracaoSerializer,
    RevisarEscopoSerializer,
    RevogarEscopoSerializer,
)
from src.infrastructure.multitenant.context import (
    active_tenant_context,
    usuario_id_context,
)

logger = logging.getLogger(__name__)

ENDPOINT_CADASTRAR = "escopos_cmc.cadastrar"
ENDPOINT_DECLARAR = "escopos_cmc.declarar_capacidade"
ENDPOINT_REVISAR = "escopos_cmc.revisar"
ENDPOINT_REVOGAR = "escopos_cmc.revogar"
ENDPOINT_IMPORTAR = "escopos_cmc.importar_extracao"
ENDPOINT_CONFIRMAR = "escopos_cmc.confirmar_extraido"


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


def _serializar_escopo(s: Any) -> dict[str, Any]:
    return {
        "id": str(s.id),
        "grandeza": s.grandeza.value,
        "faixa_min": str(s.faixa.inferior),
        "faixa_max": str(s.faixa.superior),
        "unidade": s.faixa.unidade,
        "cmc_forma": s.cmc_forma.value,
        "cmc_valor": str(s.cmc_valor),
        "cmc_unidade": s.cmc_unidade,
        "cmc_coef_relativo": None if s.cmc_coef_relativo is None else str(s.cmc_coef_relativo),
        "rbc_acreditado": s.rbc_acreditado,
        "numero_escopo_cgcre": s.numero_escopo_cgcre,
        "versao": s.versao,
        "estado": s.estado.value,
        "revision": s.revision,
        "vigencia_fim": s.vigencia_fim.isoformat() if s.vigencia_fim else None,
        "correlation_id": str(s.correlation_id),
    }


def _serializar_extraido(e: Any) -> dict[str, Any]:
    """Staging (escopo extraído) + linhas candidatas com confiança (tela conferência)."""
    return {
        "id": str(e.id),
        "numero_escopo_cgcre": e.numero_escopo_cgcre,
        "origem_pdf_storage_key": e.origem_pdf_storage_key,
        "confirmado_em": e.confirmado_em.isoformat() if e.confirmado_em else None,
        "linhas": [
            {
                "grandeza_texto": ln.grandeza_texto,
                "unidade": ln.unidade,
                "cmc_texto": ln.cmc_texto,
                "faixa_min": None if ln.faixa_min is None else str(ln.faixa_min),
                "faixa_max": None if ln.faixa_max is None else str(ln.faixa_max),
                "metodo_texto": ln.metodo_texto,
                "confianca": str(ln.confianca),
            }
            for ln in e.linhas
        ],
    }


def _tenant_ou_none() -> UUID | None:
    return active_tenant_context.get()


def _publicar_evento_escopo(
    *,
    acao: str,
    payload: dict[str, Any],
    causation_id: UUID,
    tenant_id: UUID,
    usuario_id: UUID,
    resource_summary: str,
) -> None:
    """Emite evento na cadeia hash central `auditoria` (TL-C-06). Import local."""
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
        "escopos_cmc evento WORM publicado acao=%s",
        acao,
        extra={
            "tenant_id": str(tenant_id),
            "acao": acao,
            "correlation_id": str(payload.get("correlation_id", "")),
        },
    )


# authz-check: skip -- RequireAuthz global resolve via ACTION_MAP (header)
class EscopoCMCViewSet(viewsets.ViewSet):
    """ViewSet REST de EscopoCMC (cadastro + versionamento + revogação)."""

    authz_purpose = "execucao_contrato"
    ACTION_MAP = {
        "retrieve": "escopos_cmc.ver",
        "vigentes": "escopos_cmc.ver",
        "cadastrar": "escopos_cmc.cadastrar",
        "declarar_capacidade": "escopos_cmc.declarar_capacidade",
        "revisar": "escopos_cmc.revisar",
        "revogar": "escopos_cmc.revogar",
        # importar staging = direito de criar conteúdo de escopo (reusa cadastrar;
        # não há ação `importar` semeada — só `confirmar_extraido` é privilegiada).
        "importar_extracao": "escopos_cmc.cadastrar",
        "confirmar_extraido": "escopos_cmc.confirmar_extraido",
    }

    def get_authz_action(self, request: Request) -> str | None:
        action_name = getattr(self, "action", None)
        return self.ACTION_MAP.get(action_name) if action_name else None

    def get_authz_resource(self, request: Request) -> dict[str, Any]:
        return {}

    # ---------------------------------------------------------------- GET
    def retrieve(self, request: Request, pk: str | None = None) -> Response:
        repo = DjangoEscopoRepository()
        snapshot = repo.obter_por_id(self._uuid_ou_404(pk))
        if snapshot is None:
            raise NotFound(f"Escopo {pk} não encontrado")
        return Response(_serializar_escopo(snapshot))

    @action(detail=False, methods=["get"], url_path="vigentes")
    def vigentes(self, request: Request) -> Response:
        """GET — escopos CONFIRMADO vigentes de uma grandeza (cobertura atual)."""
        tenant_id = _tenant_ou_none()
        if tenant_id is None:
            return Response({"erro": "tenant ausente"}, status=status.HTTP_403_FORBIDDEN)
        grandeza_raw = request.query_params.get("grandeza", "")
        try:
            grandeza = Grandeza.from_string(grandeza_raw)
        except ValueError as exc:
            return Response({"erro": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        repo = DjangoEscopoRepository()
        vigentes = repo.listar_confirmados_vigentes(
            tenant_id=tenant_id, grandeza=grandeza, em=datetime.now(UTC)
        )
        return Response({"vigentes": [_serializar_escopo(s) for s in vigentes]})

    # ---------------------------------------------------------------- POST cadastro
    @action(detail=False, methods=["post"], url_path="cadastrar")
    def cadastrar(self, request: Request) -> Response:
        """POST — US-ECMC-001 (perfil A escopo RBC). # idempotency-key: required"""
        return self._criar(request, endpoint=ENDPOINT_CADASTRAR, forcar_interna=False)

    @action(detail=False, methods=["post"], url_path="declarar-capacidade")
    def declarar_capacidade(self, request: Request) -> Response:
        """POST — US-ECMC-007 (B/C/D capacidade interna). # idempotency-key: required"""
        return self._criar(request, endpoint=ENDPOINT_DECLARAR, forcar_interna=True)

    def _criar(
        self, request: Request, *, endpoint: str, forcar_interna: bool
    ) -> Response:
        s = CadastrarEscopoSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        d = s.validated_data
        tenant_id = _tenant_ou_none()
        if tenant_id is None:
            return Response({"erro": "tenant ausente"}, status=status.HTTP_403_FORBIDDEN)
        perfil = obter_perfil_tenant_corrente()
        if not perfil:
            return Response(
                {"erro": "perfil regulatório indisponível (fail-closed ADR-0067)"},
                status=status.HTTP_403_FORBIDDEN,
            )
        usuario_id = usuario_id_context.get() or UUID(int=0)

        novo, resp = _aplicar_idempotencia(
            request,
            tenant_id=tenant_id,
            usuario_id=usuario_id,
            endpoint=endpoint,
            payload_fingerprint={
                "grandeza": d["grandeza"],
                "faixa_min": str(d["faixa_min"]),
                "faixa_max": str(d["faixa_max"]),
                "correlation_id": str(d["correlation_id"]),
            },
        )
        if resp is not None:
            return resp
        assert novo is not None and novo.chave_id is not None
        chave_id = novo.chave_id

        repo = DjangoEscopoRepository()
        try:
            inp = cadastrar_escopo.CadastrarEscopoInput(
                tenant_id=tenant_id,
                grandeza=Grandeza.from_string(d["grandeza"]),
                faixa=FaixaMedicao(d["faixa_min"], d["faixa_max"], d["unidade"]),
                cmc_forma=FormaCMC(d["cmc_forma"]),
                cmc_valor=d["cmc_valor"],
                cmc_unidade=d["cmc_unidade"],
                perfil=perfil,
                rbc_solicitado=False if forcar_interna else d.get("rbc_acreditado", False),
                vigencia_inicio=datetime.now(UTC),
                correlation_id=d["correlation_id"],
                cmc_coef_relativo=d.get("cmc_coef_relativo"),
                numero_escopo_cgcre=d.get("numero_escopo_cgcre", ""),
                procedimento_id=d.get("procedimento_id"),
                documento_regulatorio_id=d.get("documento_regulatorio_id"),
            )
            with transaction.atomic():
                out = cadastrar_escopo.executar(inp, repo)
                _publicar_evento_escopo(
                    acao="escopos_cmc.cadastrado",
                    payload=_serializar_escopo(out.snapshot),
                    causation_id=chave_id,
                    tenant_id=tenant_id,
                    usuario_id=usuario_id,
                    resource_summary=f"escopo {out.snapshot.grandeza.value} v{out.snapshot.versao}",
                )
        except (
            ValueError,
            cadastrar_escopo.ChaveDuplicadaError,
            cadastrar_escopo.ProcedimentoObrigatorioParaRBCError,
        ) as exc:
            return self._falha(chave_id, tenant_id, exc, status.HTTP_400_BAD_REQUEST)

        body = _serializar_escopo(out.snapshot)
        concluir_chave(
            chave_id=chave_id,
            tenant_id=tenant_id,
            response_status=status.HTTP_201_CREATED,
            response_body_resumo=body,
        )
        return Response(body, status=status.HTTP_201_CREATED)

    # ---------------------------------------------------------------- POST revisar
    @action(detail=True, methods=["post"], url_path="revisar")
    def revisar(self, request: Request, pk: str | None = None) -> Response:
        """POST — US-ECMC-002 (nova versão preserva anterior). # idempotency-key: required"""
        s = RevisarEscopoSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        d = s.validated_data
        tenant_id = _tenant_ou_none()
        if tenant_id is None:
            return Response({"erro": "tenant ausente"}, status=status.HTTP_403_FORBIDDEN)
        usuario_id = usuario_id_context.get() or UUID(int=0)
        escopo_id = self._uuid_ou_404(pk)

        novo, resp = _aplicar_idempotencia(
            request,
            tenant_id=tenant_id,
            usuario_id=usuario_id,
            endpoint=ENDPOINT_REVISAR,
            payload_fingerprint={"escopo_id": str(escopo_id), "correlation_id": str(d["correlation_id"])},
        )
        if resp is not None:
            return resp
        assert novo is not None and novo.chave_id is not None
        chave_id = novo.chave_id

        repo = DjangoEscopoRepository()
        try:
            inp = revisar_escopo.RevisarEscopoInput(
                tenant_id=tenant_id,
                escopo_id_atual=escopo_id,
                cmc_forma=FormaCMC(d["cmc_forma"]),
                cmc_valor=d["cmc_valor"],
                cmc_unidade=d["cmc_unidade"],
                vigencia_inicio=datetime.now(UTC),
                correlation_id=d["correlation_id"],
                cmc_coef_relativo=d.get("cmc_coef_relativo"),
                numero_escopo_cgcre=d.get("numero_escopo_cgcre", ""),
                documento_regulatorio_id=d.get("documento_regulatorio_id"),
            )
            with transaction.atomic():
                out = revisar_escopo.executar(inp, repo)
                _publicar_evento_escopo(
                    acao="escopos_cmc.revisado",
                    payload={"anterior_id": str(out.anterior_id), **_serializar_escopo(out.nova_versao)},
                    causation_id=chave_id,
                    tenant_id=tenant_id,
                    usuario_id=usuario_id,
                    resource_summary=f"revisao escopo {out.nova_versao.grandeza.value} v{out.nova_versao.versao}",
                )
        except revisar_escopo.EscopoNaoEncontradoError as exc:
            return self._falha(chave_id, tenant_id, exc, status.HTTP_404_NOT_FOUND)
        except revisar_escopo.ConflitoVersaoError as exc:
            return self._falha(chave_id, tenant_id, exc, status.HTTP_409_CONFLICT)
        except (revisar_escopo.EscopoNaoRevisavelError, ValueError) as exc:
            return self._falha(chave_id, tenant_id, exc, status.HTTP_400_BAD_REQUEST)

        body = {"anterior_id": str(out.anterior_id), **_serializar_escopo(out.nova_versao)}
        concluir_chave(
            chave_id=chave_id,
            tenant_id=tenant_id,
            response_status=status.HTTP_201_CREATED,
            response_body_resumo=body,
        )
        return Response(body, status=status.HTTP_201_CREATED)

    # ---------------------------------------------------------------- POST revogar
    @action(detail=True, methods=["post"], url_path="revogar")
    def revogar(self, request: Request, pk: str | None = None) -> Response:
        """POST — US-ECMC-003 (revogação one-shot). # idempotency-key: required"""
        s = RevogarEscopoSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        d = s.validated_data
        tenant_id = _tenant_ou_none()
        if tenant_id is None:
            return Response({"erro": "tenant ausente"}, status=status.HTTP_403_FORBIDDEN)
        usuario_id = usuario_id_context.get() or UUID(int=0)
        escopo_id = self._uuid_ou_404(pk)

        novo, resp = _aplicar_idempotencia(
            request,
            tenant_id=tenant_id,
            usuario_id=usuario_id,
            endpoint=ENDPOINT_REVOGAR,
            payload_fingerprint={"escopo_id": str(escopo_id)},
        )
        if resp is not None:
            return resp
        assert novo is not None and novo.chave_id is not None
        chave_id = novo.chave_id

        repo = DjangoEscopoRepository()
        try:
            inp = revogar_escopo.RevogarEscopoInput(
                tenant_id=tenant_id,
                escopo_id=escopo_id,
                motivo=d["motivo"],
                revogado_em=datetime.now(UTC),
            )
            with transaction.atomic():
                revogar_escopo.executar(inp, repo)
                _publicar_evento_escopo(
                    acao="escopos_cmc.revogado",
                    payload={"escopo_id": str(escopo_id), "correlation_id": str(escopo_id)},
                    causation_id=chave_id,
                    tenant_id=tenant_id,
                    usuario_id=usuario_id,
                    resource_summary=f"revogacao escopo {escopo_id}",
                )
        except revogar_escopo.EscopoNaoEncontradoError as exc:
            return self._falha(chave_id, tenant_id, exc, status.HTTP_404_NOT_FOUND)
        except revogar_escopo.JaRevogadoError as exc:
            return self._falha(chave_id, tenant_id, exc, status.HTTP_409_CONFLICT)
        except ValueError as exc:
            return self._falha(chave_id, tenant_id, exc, status.HTTP_400_BAD_REQUEST)

        body = {"escopo_id": str(escopo_id), "estado": "REVOGADO"}
        concluir_chave(
            chave_id=chave_id,
            tenant_id=tenant_id,
            response_status=status.HTTP_200_OK,
            response_body_resumo=body,
        )
        return Response(body, status=status.HTTP_200_OK)

    # ---------------------------------------------------------------- POST extração PDF (Fatia 4)
    @action(detail=False, methods=["post"], url_path="importar-extracao")
    def importar_extracao(self, request: Request) -> Response:
        """POST — T-ECMC-051: parseia linhas extraídas + grava staging RASCUNHO
        (INV-ECMC-007 — nunca vigente). # idempotency-key: required

        # authz-check: skip -- RequireAuthz global resolve via ACTION_MAP (header)
        """
        s = ImportarExtracaoSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        d = s.validated_data
        tenant_id = _tenant_ou_none()
        if tenant_id is None:
            return Response({"erro": "tenant ausente"}, status=status.HTTP_403_FORBIDDEN)
        usuario_id = usuario_id_context.get() or UUID(int=0)

        novo, resp = _aplicar_idempotencia(
            request,
            tenant_id=tenant_id,
            usuario_id=usuario_id,
            endpoint=ENDPOINT_IMPORTAR,
            payload_fingerprint={
                "origem_pdf_storage_key": d["origem_pdf_storage_key"],
                "correlation_id": str(d["correlation_id"]),
            },
        )
        if resp is not None:
            return resp
        assert novo is not None and novo.chave_id is not None
        chave_id = novo.chave_id

        repo = DjangoEscopoExtraidoRepository()
        try:
            inp = importar_escopo_pdf.ImportarEscopoPdfInput(
                tenant_id=tenant_id,
                origem_pdf_storage_key=d["origem_pdf_storage_key"],
                numero_escopo_cgcre=d.get("numero_escopo_cgcre", ""),
                linhas_cruas=d["linhas_cruas"],
                mapa_colunas=MapaColunas(**d["mapa_colunas"]),
                extraido_em=datetime.now(UTC),
                correlation_id=d["correlation_id"],
            )
            with transaction.atomic():
                out = importar_escopo_pdf.executar(inp, repo)
                _publicar_evento_escopo(
                    acao="escopos_cmc.extracao_importada",
                    payload={
                        "extraido_id": str(out.extraido.id),
                        "numero_escopo_cgcre": out.extraido.numero_escopo_cgcre,
                        "linhas": len(out.extraido.linhas),
                        "correlation_id": str(d["correlation_id"]),
                    },
                    causation_id=chave_id,
                    tenant_id=tenant_id,
                    usuario_id=usuario_id,
                    resource_summary=f"extracao staging {out.extraido.id}",
                )
        except (ValueError, TypeError) as exc:
            return self._falha(chave_id, tenant_id, exc, status.HTTP_400_BAD_REQUEST)

        body = _serializar_extraido(out.extraido)
        concluir_chave(
            chave_id=chave_id,
            tenant_id=tenant_id,
            response_status=status.HTTP_201_CREATED,
            response_body_resumo=body,
        )
        return Response(body, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"], url_path="confirmar-extraido")
    def confirmar_extraido(self, request: Request, pk: str | None = None) -> Response:
        """POST — T-ECMC-052: conferência humana promove staging -> N escopos
        CONFIRMADO (WORM). # idempotency-key: required

        # authz-check: skip -- RequireAuthz global resolve via ACTION_MAP (header)
        """
        s = ConfirmarExtraidoSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        d = s.validated_data
        tenant_id = _tenant_ou_none()
        if tenant_id is None:
            return Response({"erro": "tenant ausente"}, status=status.HTTP_403_FORBIDDEN)
        perfil = obter_perfil_tenant_corrente()
        if not perfil:
            return Response(
                {"erro": "perfil regulatório indisponível (fail-closed ADR-0067)"},
                status=status.HTTP_403_FORBIDDEN,
            )
        usuario_id = usuario_id_context.get() or UUID(int=0)
        extraido_id = self._uuid_ou_404(pk)

        novo, resp = _aplicar_idempotencia(
            request,
            tenant_id=tenant_id,
            usuario_id=usuario_id,
            endpoint=ENDPOINT_CONFIRMAR,
            payload_fingerprint={
                "extraido_id": str(extraido_id),
                "n_escopos": len(d["escopos"]),
            },
        )
        if resp is not None:
            return resp
        assert novo is not None and novo.chave_id is not None
        chave_id = novo.chave_id

        # Conferência confirmada server-side: perfil do tenant (não payload),
        # vigência = agora, origem forçada EXTRACAO_PDF no use case.
        agora = datetime.now(UTC)
        linhas_norm = tuple(
            cadastrar_escopo.CadastrarEscopoInput(
                tenant_id=tenant_id,
                grandeza=Grandeza.from_string(esc["grandeza"]),
                faixa=FaixaMedicao(esc["faixa_min"], esc["faixa_max"], esc["unidade"]),
                cmc_forma=FormaCMC(esc["cmc_forma"]),
                cmc_valor=esc["cmc_valor"],
                cmc_unidade=esc["cmc_unidade"],
                perfil=perfil,
                rbc_solicitado=esc.get("rbc_acreditado", False),
                vigencia_inicio=agora,
                correlation_id=esc["correlation_id"],
                cmc_coef_relativo=esc.get("cmc_coef_relativo"),
                numero_escopo_cgcre=esc.get("numero_escopo_cgcre", ""),
                procedimento_id=esc.get("procedimento_id"),
                documento_regulatorio_id=esc.get("documento_regulatorio_id"),
            )
            for esc in d["escopos"]
        )
        repo_extr = DjangoEscopoExtraidoRepository()
        repo_esc = DjangoEscopoRepository()
        try:
            inp = confirmar_escopo_extraido.ConfirmarEscopoExtraidoInput(
                extraido_id=extraido_id,
                tenant_id=tenant_id,
                confirmado_por_id_hash=derivar_user_id_hash(
                    usuario_id=usuario_id, tenant_id=tenant_id
                ),
                confirmado_em=agora,
                escopos=linhas_norm,
            )
            with transaction.atomic():
                out = confirmar_escopo_extraido.executar(inp, repo_extr, repo_esc)
                for snap in out.confirmados:
                    _publicar_evento_escopo(
                        acao="escopos_cmc.cadastrado",
                        payload=_serializar_escopo(snap),
                        causation_id=chave_id,
                        tenant_id=tenant_id,
                        usuario_id=usuario_id,
                        resource_summary=(
                            f"escopo {snap.grandeza.value} v{snap.versao} (extracao PDF)"
                        ),
                    )
                _publicar_evento_escopo(
                    acao="escopos_cmc.extracao_confirmada",
                    payload={
                        "extraido_id": str(extraido_id),
                        "confirmados": len(out.confirmados),
                        "correlation_id": str(extraido_id),
                    },
                    causation_id=chave_id,
                    tenant_id=tenant_id,
                    usuario_id=usuario_id,
                    resource_summary=f"confirma extracao {extraido_id}",
                )
        except confirmar_escopo_extraido.ExtraidoNaoEncontrado as exc:
            return self._falha(chave_id, tenant_id, exc, status.HTTP_404_NOT_FOUND)
        except confirmar_escopo_extraido.ExtraidoJaConfirmado as exc:
            return self._falha(chave_id, tenant_id, exc, status.HTTP_409_CONFLICT)
        except (
            ValueError,
            cadastrar_escopo.ChaveDuplicadaError,
            cadastrar_escopo.ProcedimentoObrigatorioParaRBCError,
        ) as exc:
            return self._falha(chave_id, tenant_id, exc, status.HTTP_400_BAD_REQUEST)

        body = {
            "extraido_id": str(extraido_id),
            "confirmados": [_serializar_escopo(s) for s in out.confirmados],
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
    def _uuid_ou_404(raw: str | None) -> UUID:
        try:
            return UUID(str(raw))
        except (ValueError, TypeError) as exc:
            raise NotFound(f"id inválido: {exc}") from exc

    @staticmethod
    def _falha(
        chave_id: UUID, tenant_id: UUID, exc: Exception, http_status: int
    ) -> Response:
        falhar_chave(chave_id=chave_id, tenant_id=tenant_id, response_status=http_status)
        return Response({"erro": str(exc)}, status=http_status)
