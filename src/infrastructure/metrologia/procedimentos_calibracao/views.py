"""ProcedimentoCalibracaoViewSet — REST do M7 procedimentos-calibracao (T-PROC-036).

Actions:
  GET  /api/v1/procedimentos-calibracao/{id}/        retrieve
  GET  /api/v1/procedimentos-calibracao/vigente/     vigente?grandeza=&faixa_min=&faixa_max=&unidade=
  POST /api/v1/procedimentos-calibracao/cadastrar/   cadastrar (US-PROC-001 — RASCUNHO)
  POST /api/v1/procedimentos-calibracao/{id}/revisar/  revisar (US-PROC-003 — nova versão)
  POST /api/v1/procedimentos-calibracao/{id}/publicar/ publicar (US-PROC-002 — advisory lock + supersede)
  POST /api/v1/procedimentos-calibracao/{id}/revogar/  revogar (US-PROC-004)

Autorização: RequireAuthz (DEFAULT_PERMISSION_CLASSES) + ACTION_MAP. Idempotency-Key
obrigatória nos POST (IDEMP-001). tenant via contexto. `anexo_pdf_sha256` recalculado
server-side (INV-PROC-007). publicar serializa concorrência com advisory lock
(D-PROC-3). Eventos WORM na cadeia hash.

# authz-check: skip -- RequireAuthz global resolve via ACTION_MAP (header)
"""

from __future__ import annotations

import base64
import binascii
import logging
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from django.db import connection, transaction
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound
from rest_framework.request import Request
from rest_framework.response import Response

from src.application.metrologia.procedimentos_calibracao import (
    cadastrar_procedimento,
    publicar_procedimento,
    revisar_procedimento,
    revogar_procedimento,
)
from src.application.metrologia.procedimentos_calibracao.anexo_storage import (
    sha256_server_side,
)
from src.domain.metrologia.procedimentos_calibracao.enums import TipoMetodo
from src.domain.metrologia.value_objects import FaixaMedicao, Grandeza
from src.infrastructure.idempotencia.services_idempotencia import (
    ErroValidacao,
    NovoProcessamento,
    Replay,
    avaliar_chave_idempotencia,
    concluir_chave,
    falhar_chave,
)
from src.infrastructure.metrologia.procedimentos_calibracao.anexo_storage_local import (
    obter_anexo_storage,
)
from src.infrastructure.metrologia.procedimentos_calibracao.repositories import (
    DjangoProcedimentoRepository,
)
from src.infrastructure.metrologia.procedimentos_calibracao.serializers import (
    CadastrarProcedimentoSerializer,
    PublicarProcedimentoSerializer,
    RevisarProcedimentoSerializer,
    RevogarProcedimentoSerializer,
)
from src.infrastructure.multitenant.context import (
    active_tenant_context,
    usuario_id_context,
)

logger = logging.getLogger(__name__)

ENDPOINT_CADASTRAR = "procedimentos_calibracao.cadastrar"
ENDPOINT_REVISAR = "procedimentos_calibracao.revisar"
ENDPOINT_PUBLICAR = "procedimentos_calibracao.publicar"
ENDPOINT_REVOGAR = "procedimentos_calibracao.revogar"


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


def _serializar_proc(s: Any) -> dict[str, Any]:
    return {
        "id": str(s.id),
        "codigo": s.codigo,
        "titulo": s.titulo,
        "grandeza": s.grandeza.value,
        "faixa_min": str(s.faixa.inferior),
        "faixa_max": str(s.faixa.superior),
        "unidade": s.faixa.unidade,
        "metodo_norma": s.metodo_norma,
        "tipo_metodo": s.tipo_metodo.value,
        "numero_revisao": s.numero_revisao,
        "anexo_pdf_sha256": s.anexo_pdf_sha256,
        "versao": s.versao,
        "estado": s.estado.value,
        "revision": s.revision,
        "vigencia_fim": s.vigencia_fim.isoformat() if s.vigencia_fim else None,
        "aprovado_em": s.aprovado_em.isoformat() if s.aprovado_em else None,
        "correlation_id": str(s.correlation_id),
    }


def _tenant_ou_none() -> UUID | None:
    return active_tenant_context.get()


def _resolver_anexo(anexo_b64: str, *, tenant_id: UUID) -> tuple[str, str]:
    """Decodifica o base64 do PDF, recalcula sha256 SERVER-SIDE (INV-PROC-007) e
    persiste o binário via porta. Retorna (storage_key, sha256). ("", "") se vazio.
    Levanta ValueError se o base64 for inválido."""
    if not anexo_b64.strip():
        return "", ""
    try:
        pdf_bytes = base64.b64decode(anexo_b64, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise ValueError(f"anexo_pdf_base64 inválido: {exc}") from exc
    sha256 = sha256_server_side(pdf_bytes)
    storage = obter_anexo_storage()
    key = storage.salvar(pdf_bytes=pdf_bytes, nome_sugerido=f"{tenant_id}-{sha256}.pdf")
    return key, sha256


def _advisory_lock_publicacao(
    *, tenant_id: UUID, codigo: str, grandeza: str, faixa_min: str, faixa_max: str
) -> None:
    """Serializa publicações concorrentes do mesmo procedimento (D-PROC-3 — molde
    ADR-0065). Liberado no commit/rollback da transação (xact)."""
    chave = f"{tenant_id}:{codigo}:{grandeza}:{faixa_min}:{faixa_max}"
    with connection.cursor() as cur:
        cur.execute("SELECT pg_advisory_xact_lock(hashtext(%s))", [chave])


def _publicar_evento_proc(
    *, acao: str, payload: dict[str, Any], causation_id: UUID,
    tenant_id: UUID, usuario_id: UUID, resource_summary: str,
) -> None:
    """Emite evento na cadeia hash central `auditoria`. Import local."""
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
        "procedimentos_calibracao evento WORM publicado acao=%s",
        acao,
        extra={
            "tenant_id": str(tenant_id),
            "acao": acao,
            "correlation_id": str(payload.get("correlation_id", "")),
        },
    )


# authz-check: skip -- RequireAuthz global resolve via ACTION_MAP (header)
class ProcedimentoCalibracaoViewSet(viewsets.ViewSet):
    """ViewSet REST de ProcedimentoCalibracao (cadastro + versionamento + publicação)."""

    authz_purpose = "execucao_contrato"
    ACTION_MAP = {
        "retrieve": "procedimentos_calibracao.ver",
        "vigente": "procedimentos_calibracao.ver",
        "cadastrar": "procedimentos_calibracao.cadastrar",
        "revisar": "procedimentos_calibracao.revisar",
        "publicar": "procedimentos_calibracao.publicar",
        "revogar": "procedimentos_calibracao.revogar",
    }

    def get_authz_action(self, request: Request) -> str | None:
        action_name = getattr(self, "action", None)
        return self.ACTION_MAP.get(action_name) if action_name else None

    def get_authz_resource(self, request: Request) -> dict[str, Any]:
        return {}

    # ---------------------------------------------------------------- GET
    def retrieve(self, request: Request, pk: str | None = None) -> Response:
        repo = DjangoProcedimentoRepository()
        snapshot = repo.obter_por_id(self._uuid_ou_404(pk))
        if snapshot is None:
            raise NotFound(f"Procedimento {pk} não encontrado")
        return Response(_serializar_proc(snapshot))

    @action(detail=False, methods=["get"], url_path="vigente")
    def vigente(self, request: Request) -> Response:
        """GET — resolve o procedimento PUBLICADO vigente que cobre grandeza+faixa
        (porta `vigente_em`). 404 se nenhum (fail-closed)."""
        tenant_id = _tenant_ou_none()
        if tenant_id is None:
            return Response({"erro": "tenant ausente"}, status=status.HTTP_403_FORBIDDEN)
        from src.infrastructure.metrologia.procedimentos_calibracao import query_service

        try:
            snap = query_service.vigente_em(
                tenant_id=tenant_id,
                grandeza=request.query_params.get("grandeza", ""),
                faixa_min=request.query_params.get("faixa_min", ""),
                faixa_max=request.query_params.get("faixa_max", ""),
                unidade=request.query_params.get("unidade", ""),
                data=datetime.now(UTC),
            )
        except (ValueError, TypeError) as exc:
            return Response({"erro": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        if snap is None:
            raise NotFound("Nenhum procedimento vigente cobre a grandeza+faixa")
        return Response(_serializar_proc(snap))

    # ---------------------------------------------------------------- POST cadastrar
    @action(detail=False, methods=["post"], url_path="cadastrar")
    def cadastrar(self, request: Request) -> Response:
        """POST — US-PROC-001 (RASCUNHO). # idempotency-key: required"""
        s = CadastrarProcedimentoSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        d = s.validated_data
        tenant_id, perfil, usuario_id, erro = self._contexto_com_perfil()
        if erro is not None:
            return erro

        novo, resp = _aplicar_idempotencia(
            request, tenant_id=tenant_id, usuario_id=usuario_id, endpoint=ENDPOINT_CADASTRAR,
            payload_fingerprint={"codigo": d["codigo"], "correlation_id": str(d["correlation_id"])},
        )
        if resp is not None:
            return resp
        assert novo is not None and novo.chave_id is not None
        chave_id = novo.chave_id

        repo = DjangoProcedimentoRepository()
        try:
            anexo_key, anexo_sha = _resolver_anexo(d.get("anexo_pdf_base64", ""), tenant_id=tenant_id)
            inp = cadastrar_procedimento.CadastrarProcedimentoInput(
                tenant_id=tenant_id,
                codigo=d["codigo"],
                titulo=d["titulo"],
                grandeza=Grandeza.from_string(d["grandeza"]),
                faixa=FaixaMedicao(d["faixa_min"], d["faixa_max"], d["unidade"]),
                metodo_norma=d["metodo_norma"],
                tipo_metodo=TipoMetodo(d["tipo_metodo"]),
                perfil=perfil,
                vigencia_inicio=datetime.now(UTC),
                correlation_id=d["correlation_id"],
                registro_validacao_id=d.get("registro_validacao_id"),
                anexo_pdf_storage_key=anexo_key,
                anexo_pdf_sha256=anexo_sha,
            )
            with transaction.atomic():
                out = cadastrar_procedimento.executar(inp, repo)
                _publicar_evento_proc(
                    acao="procedimentos_calibracao.cadastrado",
                    payload={**_serializar_proc(out.snapshot), "aviso_validacao_metodo": out.aviso_validacao_metodo},
                    causation_id=chave_id, tenant_id=tenant_id, usuario_id=usuario_id,
                    resource_summary=f"procedimento {out.snapshot.codigo} v{out.snapshot.versao}",
                )
        except (ValueError, cadastrar_procedimento.CodigoVersaoDuplicadoError) as exc:
            stts = status.HTTP_409_CONFLICT if isinstance(exc, cadastrar_procedimento.CodigoVersaoDuplicadoError) else status.HTTP_400_BAD_REQUEST
            return self._falha(chave_id, tenant_id, exc, stts)

        body = {**_serializar_proc(out.snapshot), "aviso_validacao_metodo": out.aviso_validacao_metodo}
        concluir_chave(chave_id=chave_id, tenant_id=tenant_id, response_status=status.HTTP_201_CREATED, response_body_resumo=body)
        return Response(body, status=status.HTTP_201_CREATED)

    # ---------------------------------------------------------------- POST revisar
    @action(detail=True, methods=["post"], url_path="revisar")
    def revisar(self, request: Request, pk: str | None = None) -> Response:
        """POST — US-PROC-003 (nova versão RASCUNHO). # idempotency-key: required"""
        s = RevisarProcedimentoSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        d = s.validated_data
        tenant_id, usuario_id, erro = self._contexto()
        if erro is not None:
            return erro
        proc_id = self._uuid_ou_404(pk)

        novo, resp = _aplicar_idempotencia(
            request, tenant_id=tenant_id, usuario_id=usuario_id, endpoint=ENDPOINT_REVISAR,
            payload_fingerprint={"procedimento_id": str(proc_id), "correlation_id": str(d["correlation_id"])},
        )
        if resp is not None:
            return resp
        assert novo is not None and novo.chave_id is not None
        chave_id = novo.chave_id

        repo = DjangoProcedimentoRepository()
        try:
            anexo_key, anexo_sha = _resolver_anexo(d.get("anexo_pdf_base64", ""), tenant_id=tenant_id)
            inp = revisar_procedimento.RevisarProcedimentoInput(
                tenant_id=tenant_id, procedimento_id_atual=proc_id, titulo=d["titulo"],
                metodo_norma=d["metodo_norma"], tipo_metodo=TipoMetodo(d["tipo_metodo"]),
                vigencia_inicio=datetime.now(UTC), correlation_id=d["correlation_id"],
                registro_validacao_id=d.get("registro_validacao_id"),
                anexo_pdf_storage_key=anexo_key, anexo_pdf_sha256=anexo_sha,
            )
            with transaction.atomic():
                out = revisar_procedimento.executar(inp, repo)
                _publicar_evento_proc(
                    acao="procedimentos_calibracao.revisado",
                    payload={"anterior_id": str(out.anterior_id), **_serializar_proc(out.nova_versao)},
                    causation_id=chave_id, tenant_id=tenant_id, usuario_id=usuario_id,
                    resource_summary=f"revisao procedimento {out.nova_versao.codigo} v{out.nova_versao.versao}",
                )
        except revisar_procedimento.ProcedimentoNaoEncontradoError as exc:
            return self._falha(chave_id, tenant_id, exc, status.HTTP_404_NOT_FOUND)
        except ValueError as exc:
            return self._falha(chave_id, tenant_id, exc, status.HTTP_400_BAD_REQUEST)

        body = {"anterior_id": str(out.anterior_id), **_serializar_proc(out.nova_versao)}
        concluir_chave(chave_id=chave_id, tenant_id=tenant_id, response_status=status.HTTP_201_CREATED, response_body_resumo=body)
        return Response(body, status=status.HTTP_201_CREATED)

    # ---------------------------------------------------------------- POST publicar
    @action(detail=True, methods=["post"], url_path="publicar")
    def publicar(self, request: Request, pk: str | None = None) -> Response:
        """POST — US-PROC-002 (RASCUNHO->PUBLICADO + supersede). # idempotency-key: required"""
        s = PublicarProcedimentoSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        d = s.validated_data
        tenant_id, perfil, usuario_id, erro = self._contexto_com_perfil()
        if erro is not None:
            return erro
        proc_id = self._uuid_ou_404(pk)

        novo, resp = _aplicar_idempotencia(
            request, tenant_id=tenant_id, usuario_id=usuario_id, endpoint=ENDPOINT_PUBLICAR,
            payload_fingerprint={"procedimento_id": str(proc_id), "numero_revisao": d["numero_revisao"]},
        )
        if resp is not None:
            return resp
        assert novo is not None and novo.chave_id is not None
        chave_id = novo.chave_id

        repo = DjangoProcedimentoRepository()
        atual = repo.obter_por_id(proc_id)
        if atual is None or atual.tenant_id != tenant_id:
            return self._falha(chave_id, tenant_id, NotFound(f"Procedimento {proc_id}"), status.HTTP_404_NOT_FOUND)
        try:
            agora = datetime.now(UTC)
            inp = publicar_procedimento.PublicarProcedimentoInput(
                tenant_id=tenant_id, procedimento_id=proc_id, numero_revisao=d["numero_revisao"],
                aprovado_em=agora, aprovado_por_id=d["aprovado_por_id"], perfil=perfil,
                aprovado_por_nome_snapshot=d.get("aprovado_por_nome_snapshot", ""),
            )
            with transaction.atomic():
                # D-PROC-3: serializa publicacoes concorrentes da mesma chave natural.
                _advisory_lock_publicacao(
                    tenant_id=tenant_id, codigo=atual.codigo, grandeza=atual.grandeza.value,
                    faixa_min=str(atual.faixa.inferior), faixa_max=str(atual.faixa.superior),
                )
                out = publicar_procedimento.executar(inp, repo)
                _publicar_evento_proc(
                    acao="procedimentos_calibracao.publicado",
                    payload={
                        "anterior_encerrada_id": str(out.anterior_encerrada_id) if out.anterior_encerrada_id else None,
                        "aviso_validacao_metodo": out.aviso_validacao_metodo,
                        **_serializar_proc(out.publicado),
                    },
                    causation_id=chave_id, tenant_id=tenant_id, usuario_id=usuario_id,
                    resource_summary=f"publica procedimento {out.publicado.codigo} v{out.publicado.versao}",
                )
        except publicar_procedimento.ProcedimentoNaoEncontradoError as exc:
            return self._falha(chave_id, tenant_id, exc, status.HTTP_404_NOT_FOUND)
        except publicar_procedimento.ConflitoVersaoError as exc:
            return self._falha(chave_id, tenant_id, exc, status.HTTP_409_CONFLICT)
        except (publicar_procedimento.ProcedimentoNaoPublicavelError, ValueError) as exc:
            return self._falha(chave_id, tenant_id, exc, status.HTTP_400_BAD_REQUEST)

        body = {
            "anterior_encerrada_id": str(out.anterior_encerrada_id) if out.anterior_encerrada_id else None,
            "aviso_validacao_metodo": out.aviso_validacao_metodo,
            **_serializar_proc(out.publicado),
        }
        concluir_chave(chave_id=chave_id, tenant_id=tenant_id, response_status=status.HTTP_200_OK, response_body_resumo=body)
        return Response(body, status=status.HTTP_200_OK)

    # ---------------------------------------------------------------- POST revogar
    @action(detail=True, methods=["post"], url_path="revogar")
    def revogar(self, request: Request, pk: str | None = None) -> Response:
        """POST — US-PROC-004 (revogação one-shot). # idempotency-key: required"""
        s = RevogarProcedimentoSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        d = s.validated_data
        tenant_id, usuario_id, erro = self._contexto()
        if erro is not None:
            return erro
        proc_id = self._uuid_ou_404(pk)

        novo, resp = _aplicar_idempotencia(
            request, tenant_id=tenant_id, usuario_id=usuario_id, endpoint=ENDPOINT_REVOGAR,
            payload_fingerprint={"procedimento_id": str(proc_id)},
        )
        if resp is not None:
            return resp
        assert novo is not None and novo.chave_id is not None
        chave_id = novo.chave_id

        repo = DjangoProcedimentoRepository()
        try:
            inp = revogar_procedimento.RevogarProcedimentoInput(
                tenant_id=tenant_id, procedimento_id=proc_id, motivo=d["motivo"], revogado_em=datetime.now(UTC),
            )
            with transaction.atomic():
                revogar_procedimento.executar(inp, repo)
                _publicar_evento_proc(
                    acao="procedimentos_calibracao.revogado",
                    payload={"procedimento_id": str(proc_id), "correlation_id": str(proc_id)},
                    causation_id=chave_id, tenant_id=tenant_id, usuario_id=usuario_id,
                    resource_summary=f"revogacao procedimento {proc_id}",
                )
        except revogar_procedimento.ProcedimentoNaoEncontradoError as exc:
            return self._falha(chave_id, tenant_id, exc, status.HTTP_404_NOT_FOUND)
        except revogar_procedimento.JaRevogadoError as exc:
            return self._falha(chave_id, tenant_id, exc, status.HTTP_409_CONFLICT)
        except ValueError as exc:
            return self._falha(chave_id, tenant_id, exc, status.HTTP_400_BAD_REQUEST)

        body = {"procedimento_id": str(proc_id), "estado": "REVOGADO"}
        concluir_chave(chave_id=chave_id, tenant_id=tenant_id, response_status=status.HTTP_200_OK, response_body_resumo=body)
        return Response(body, status=status.HTTP_200_OK)

    # ---------------------------------------------------------------- helpers
    def _contexto(self) -> tuple[Any, Any, Response | None]:
        tenant_id = _tenant_ou_none()
        if tenant_id is None:
            return None, None, Response({"erro": "tenant ausente"}, status=status.HTTP_403_FORBIDDEN)
        usuario_id = usuario_id_context.get() or UUID(int=0)
        return tenant_id, usuario_id, None

    def _contexto_com_perfil(self) -> tuple[Any, Any, Any, Response | None]:
        from src.infrastructure.authz.perfil_tenant_helper import (
            obter_perfil_tenant_corrente,
        )

        tenant_id = _tenant_ou_none()
        if tenant_id is None:
            return None, None, None, Response({"erro": "tenant ausente"}, status=status.HTTP_403_FORBIDDEN)
        perfil = obter_perfil_tenant_corrente()
        if not perfil:
            return None, None, None, Response(
                {"erro": "perfil regulatório indisponível (fail-closed ADR-0067)"},
                status=status.HTTP_403_FORBIDDEN,
            )
        usuario_id = usuario_id_context.get() or UUID(int=0)
        return tenant_id, perfil, usuario_id, None

    @staticmethod
    def _uuid_ou_404(raw: str | None) -> UUID:
        try:
            return UUID(str(raw))
        except (ValueError, TypeError) as exc:
            raise NotFound(f"id inválido: {exc}") from exc

    @staticmethod
    def _falha(chave_id: UUID, tenant_id: UUID, exc: Exception, http_status: int) -> Response:
        falhar_chave(chave_id=chave_id, tenant_id=tenant_id, response_status=http_status)
        return Response({"erro": str(exc)}, status=http_status)
