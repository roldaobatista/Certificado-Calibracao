"""ViewSets REST da frente `configuracoes-sistema` (Fatia 2 — T-CFG-033).

Actions:
  GET  /api/v1/configuracoes/empresa/atual/                  empresa do tenant
  POST /api/v1/configuracoes/empresa/atualizar/              upsert (US-CFG-001)
  GET  /api/v1/configuracoes/empresa/filiais/                lista filiais
  POST /api/v1/configuracoes/empresa/adicionar-filial/       INV-037 no use case
  GET  /api/v1/configuracoes/impostos/                       catálogo do tenant
  POST /api/v1/configuracoes/impostos/cadastrar/             nova linha imutável
  POST /api/v1/configuracoes/impostos/{id}/encerrar-vigencia/ one-shot D-CFG-3
  GET  /api/v1/configuracoes/series/{id}/                    retrieve
  POST /api/v1/configuracoes/series/criar/                   regime DERIVADO
  POST /api/v1/configuracoes/series/{id}/reservar-numero/    2 regimes ADR-0080

Autorização: RequireAuthz (DEFAULT_PERMISSION_CLASSES) + ACTION_MAP. Idempotency-Key
nos POST mutadores (IDEMP-001) — em especial `reservar-numero` (retry de rede sem
chave duplicaria número consumido). Eventos `Config.*` (ACOES_CONFIG) vão SÓ na
cadeia hash (outbox=False — PascalCase da spec; molde Certificados). A trava de
sobreposição de imposto é exclusion constraint (a verdade) + defesa no use case.

# authz-check: skip -- RequireAuthz global resolve via ACTION_MAP (header)
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from django.db import IntegrityError, transaction
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound
from rest_framework.request import Request
from rest_framework.response import Response

from src.application.configuracoes_sistema import empresa as uc_empresa
from src.application.configuracoes_sistema import imposto as uc_imposto
from src.application.configuracoes_sistema import serie as uc_serie
from src.domain.configuracoes_sistema.enums import (
    RegimeTributario,
    TipoDocumento,
    TipoImposto,
)
from src.domain.configuracoes_sistema.erros import (
    ImpostoVigenciaSobrepostaError,
    MatrizInvalidaError,
)
from src.infrastructure.configuracoes_sistema.repositories import (
    DjangoEmpresaRepository,
    DjangoImpostoRepository,
    DjangoSerieDocumentoRepository,
)
from src.infrastructure.configuracoes_sistema.serializers import (
    AdicionarFilialSerializer,
    AtualizarEmpresaSerializer,
    CadastrarImpostoSerializer,
    CriarSerieSerializer,
    EncerrarVigenciaImpostoSerializer,
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


def _tenant_ou_none() -> UUID | None:
    return active_tenant_context.get()


def _serializar_empresa(e: Any) -> dict[str, Any]:
    return {
        "id": str(e.id),
        "razao_social": e.razao_social,
        "cnpj": e.cnpj.value,
        "regime_tributario": e.regime_tributario.value,
        "inscricao_estadual": e.inscricao_estadual,
        "inscricao_municipal": e.inscricao_municipal,
        "endereco": e.endereco,
        "logo_url": e.logo_url,
        "site": e.site,
        "telefone": e.telefone,
    }


def _serializar_filial(f: Any) -> dict[str, Any]:
    return {
        "id": str(f.id),
        "empresa_id": str(f.empresa_id),
        "cnpj": f.cnpj.value,
        "nome": f.nome,
        "eh_matriz": f.eh_matriz,
        "endereco": f.endereco,
        "inscricao_estadual": f.inscricao_estadual,
        "inscricao_municipal": f.inscricao_municipal,
        "telefone": f.telefone,
    }


def _serializar_imposto(i: Any) -> dict[str, Any]:
    return {
        "id": str(i.id),
        "tipo": i.tipo.value,
        "aliquota": str(i.aliquota.valor),
        "vigencia_inicio": i.vigencia.inicio.isoformat(),
        "vigencia_fim": i.vigencia.fim.isoformat() if i.vigencia.fim else None,
        "revogado_em": i.vigencia.revogado_em.isoformat() if i.vigencia.revogado_em else None,
        "filial_id": str(i.filial_id) if i.filial_id else None,
        "cfop_padrao": i.cfop_padrao,
        "ncm_padrao": i.ncm_padrao,
        "iss_retido_fonte": i.iss_retido_fonte,
        "tem_st": i.tem_st,
        "simples_excedeu_sublimite": i.simples_excedeu_sublimite,
        "observacoes": i.observacoes,
    }


def _serializar_serie(s: Any) -> dict[str, Any]:
    return {
        "id": str(s.id),
        "tipo": s.tipo.value,
        "prefixo": s.prefixo,
        "proximo_numero": s.proximo_numero,
        "regime_numeracao": s.regime_numeracao.value,
        "formato": s.formato,
        "padding": s.padding,
        "filial_id": str(s.filial_id) if s.filial_id else None,
        "reset_anual": s.reset_anual,
        "ano_corrente": s.ano_corrente,
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


def _publicar_evento_config(
    *,
    acao: str,
    payload: dict[str, Any],
    causation_id: UUID,
    tenant_id: UUID,
    usuario_id: UUID,
    resource_summary: str,
) -> None:
    """Evento `Config.*` na cadeia hash central (outbox=False — PascalCase da
    spec US-CFG-001; CHECK do bus_outbox exige slug lowercase, molde M8).
    Payload sanitizado pelo helper (D-CFG-7). Import local (molde fiscal)."""
    from src.infrastructure.audit.event_helpers import publicar_evento

    publicar_evento(
        acao=acao,
        payload=payload,
        causation_id=causation_id,
        tenant_id=tenant_id,
        usuario_id=usuario_id if usuario_id != UUID(int=0) else None,
        resource_summary=resource_summary,
        outbox=False,
    )
    logger.info(
        "configuracoes evento WORM publicado",
        extra={
            "tenant_id": str(tenant_id),
            "acao": acao,
            "correlation_id": str(causation_id),
        },
    )


class _ConfigViewSetBase(viewsets.ViewSet):
    """Base: ACTION_MAP authz + helpers comuns (molde fiscal)."""

    authz_purpose = "execucao_contrato"
    ACTION_MAP: dict[str, str] = {}

    def get_authz_action(self, request: Request) -> str | None:
        action_name = getattr(self, "action", None)
        return self.ACTION_MAP.get(action_name) if action_name else None

    def get_authz_resource(self, request: Request) -> dict[str, Any]:
        return {}

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

    @staticmethod
    def _contexto() -> tuple[UUID | None, UUID]:
        return _tenant_ou_none(), usuario_id_context.get() or UUID(int=0)


# authz-check: skip -- RequireAuthz global resolve via ACTION_MAP (header)
class EmpresaConfigViewSet(_ConfigViewSetBase):
    """Cadastro tributário do tenant + filiais (US-CFG-001)."""

    ACTION_MAP = {
        "atual": "configuracoes_sistema.ver",
        "filiais": "configuracoes_sistema.ver",
        "atualizar": "configuracoes_sistema.atualizar_empresa",
        "adicionar_filial": "configuracoes_sistema.gerenciar_filial",
    }

    @action(detail=False, methods=["get"], url_path="atual")
    def atual(self, request: Request) -> Response:
        tenant_id = _tenant_ou_none()
        if tenant_id is None:
            return Response({"erro": "tenant ausente"}, status=status.HTTP_403_FORBIDDEN)
        empresa = DjangoEmpresaRepository().obter(tenant_id=tenant_id)
        if empresa is None:
            raise NotFound("empresa não cadastrada para o tenant")
        return Response(_serializar_empresa(empresa))

    @action(detail=False, methods=["get"], url_path="filiais")
    def filiais(self, request: Request) -> Response:
        tenant_id = _tenant_ou_none()
        if tenant_id is None:
            return Response({"erro": "tenant ausente"}, status=status.HTTP_403_FORBIDDEN)
        repo = DjangoEmpresaRepository()
        empresa = repo.obter(tenant_id=tenant_id)
        if empresa is None:
            raise NotFound("empresa não cadastrada para o tenant")
        itens = repo.listar_filiais(tenant_id=tenant_id, empresa_id=empresa.id)
        return Response({"filiais": [_serializar_filial(f) for f in itens]})

    @action(detail=False, methods=["post"], url_path="atualizar")
    def atualizar(self, request: Request) -> Response:
        """POST — AC-CFG-001-1 (upsert + evento). # idempotency-key: required"""
        s = AtualizarEmpresaSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        d = s.validated_data
        tenant_id, usuario_id = self._contexto()
        if tenant_id is None:
            return Response({"erro": "tenant ausente"}, status=status.HTTP_403_FORBIDDEN)

        novo, resp = _aplicar_idempotencia(
            request,
            tenant_id=tenant_id,
            usuario_id=usuario_id,
            endpoint="configuracoes_sistema.atualizar_empresa",
            payload_fingerprint=dict(d),
        )
        if resp is not None:
            return resp
        assert novo is not None and novo.chave_id is not None
        chave_id = novo.chave_id

        try:
            inp = uc_empresa.AtualizarEmpresaInput(
                tenant_id=tenant_id,
                razao_social=d["razao_social"],
                cnpj=d["cnpj"],
                regime_tributario=RegimeTributario(d["regime_tributario"]),
                inscricao_estadual=d["inscricao_estadual"],
                inscricao_municipal=d["inscricao_municipal"],
                endereco=d["endereco"],
                logo_url=d["logo_url"],
                site=d["site"],
                telefone=d["telefone"],
            )
            with transaction.atomic():
                out = uc_empresa.atualizar_empresa(inp, repo=DjangoEmpresaRepository())
                _publicar_evento_config(
                    acao="Config.EmpresaAtualizada",
                    payload={
                        "empresa_id": str(out.empresa.id),
                        "criada": out.criada,
                        "antes": _serializar_empresa(out.antes) if out.antes else None,
                        "depois": _serializar_empresa(out.empresa),
                    },
                    causation_id=chave_id,
                    tenant_id=tenant_id,
                    usuario_id=usuario_id,
                    resource_summary=f"empresa {out.empresa.id} atualizada",
                )
        except IntegrityError as exc:
            return self._falha(chave_id, tenant_id, exc, status.HTTP_409_CONFLICT)
        except ValueError as exc:
            return self._falha(chave_id, tenant_id, exc, status.HTTP_400_BAD_REQUEST)

        body = _serializar_empresa(out.empresa)
        http_status = status.HTTP_201_CREATED if out.criada else status.HTTP_200_OK
        concluir_chave(
            chave_id=chave_id,
            tenant_id=tenant_id,
            response_status=http_status,
            response_body_resumo=body,
        )
        return Response(body, status=http_status)

    @action(detail=False, methods=["post"], url_path="adicionar-filial")
    def adicionar_filial(self, request: Request) -> Response:
        """POST — AC-CFG-001-2 (CNPJ próprio + INV-037). # idempotency-key: required"""
        s = AdicionarFilialSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        d = s.validated_data
        tenant_id, usuario_id = self._contexto()
        if tenant_id is None:
            return Response({"erro": "tenant ausente"}, status=status.HTTP_403_FORBIDDEN)

        novo, resp = _aplicar_idempotencia(
            request,
            tenant_id=tenant_id,
            usuario_id=usuario_id,
            endpoint="configuracoes_sistema.adicionar_filial",
            payload_fingerprint=dict(d),
        )
        if resp is not None:
            return resp
        assert novo is not None and novo.chave_id is not None
        chave_id = novo.chave_id

        try:
            inp = uc_empresa.AdicionarFilialInput(
                tenant_id=tenant_id,
                cnpj=d["cnpj"],
                nome=d["nome"],
                eh_matriz=d["eh_matriz"],
                endereco=d["endereco"],
                inscricao_estadual=d["inscricao_estadual"],
                inscricao_municipal=d["inscricao_municipal"],
                telefone=d["telefone"],
            )
            with transaction.atomic():
                filial = uc_empresa.adicionar_filial(inp, repo=DjangoEmpresaRepository())
                _publicar_evento_config(
                    acao="Config.FilialAdicionada",
                    payload={
                        "filial_id": str(filial.id),
                        "empresa_id": str(filial.empresa_id),
                        "eh_matriz": filial.eh_matriz,
                    },
                    causation_id=chave_id,
                    tenant_id=tenant_id,
                    usuario_id=usuario_id,
                    resource_summary=f"filial {filial.id} adicionada",
                )
        except uc_empresa.EmpresaAusenteError as exc:
            return self._falha(chave_id, tenant_id, exc, status.HTTP_422_UNPROCESSABLE_ENTITY)
        except MatrizInvalidaError as exc:
            return self._falha(chave_id, tenant_id, exc, status.HTTP_422_UNPROCESSABLE_ENTITY)
        except IntegrityError as exc:
            return self._falha(chave_id, tenant_id, exc, status.HTTP_409_CONFLICT)
        except ValueError as exc:
            return self._falha(chave_id, tenant_id, exc, status.HTTP_400_BAD_REQUEST)

        body = _serializar_filial(filial)
        concluir_chave(
            chave_id=chave_id,
            tenant_id=tenant_id,
            response_status=status.HTTP_201_CREATED,
            response_body_resumo=body,
        )
        return Response(body, status=status.HTTP_201_CREATED)


# authz-check: skip -- RequireAuthz global resolve via ACTION_MAP (header)
class ImpostoViewSet(_ConfigViewSetBase):
    """Catálogo tributário versionado e imutável (US-CFG-003)."""

    ACTION_MAP = {
        "list": "configuracoes_sistema.ver",
        "cadastrar": "configuracoes_sistema.cadastrar_imposto",
        "encerrar_vigencia": "configuracoes_sistema.encerrar_imposto",
    }

    def list(self, request: Request) -> Response:
        tenant_id = _tenant_ou_none()
        if tenant_id is None:
            return Response({"erro": "tenant ausente"}, status=status.HTTP_403_FORBIDDEN)
        itens = DjangoImpostoRepository().listar(tenant_id=tenant_id)
        return Response({"impostos": [_serializar_imposto(i) for i in itens]})

    @action(detail=False, methods=["post"], url_path="cadastrar")
    def cadastrar(self, request: Request) -> Response:
        """POST — AC-CFG-003-1/2 (nova linha imutável). # idempotency-key: required"""
        s = CadastrarImpostoSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        d = s.validated_data
        tenant_id, usuario_id = self._contexto()
        if tenant_id is None:
            return Response({"erro": "tenant ausente"}, status=status.HTTP_403_FORBIDDEN)

        novo, resp = _aplicar_idempotencia(
            request,
            tenant_id=tenant_id,
            usuario_id=usuario_id,
            endpoint="configuracoes_sistema.cadastrar_imposto",
            # Fingerprint = payload COMPLETO (B6): payload diferente sob a mesma
            # chave deve dar 422 PAYLOAD_DIVERGENTE, não replay silencioso.
            payload_fingerprint={
                "tipo": d["tipo"],
                "aliquota": str(d["aliquota"]),
                "vigencia_inicio": d["vigencia_inicio"].isoformat(),
                "vigencia_fim": d["vigencia_fim"].isoformat() if d["vigencia_fim"] else None,
                "filial_id": str(d["filial_id"]) if d["filial_id"] else None,
                "cfop_padrao": d["cfop_padrao"],
                "ncm_padrao": d["ncm_padrao"],
                "iss_retido_fonte": d["iss_retido_fonte"],
                "tem_st": d["tem_st"],
                "simples_excedeu_sublimite": d["simples_excedeu_sublimite"],
                "observacoes": d["observacoes"],
            },
        )
        if resp is not None:
            return resp
        assert novo is not None and novo.chave_id is not None
        chave_id = novo.chave_id

        try:
            inp = uc_imposto.CadastrarImpostoInput(
                tenant_id=tenant_id,
                tipo=TipoImposto(d["tipo"]),
                aliquota=d["aliquota"],
                vigencia_inicio=d["vigencia_inicio"],
                vigencia_fim=d["vigencia_fim"],
                filial_id=d["filial_id"],
                cfop_padrao=d["cfop_padrao"],
                ncm_padrao=d["ncm_padrao"],
                iss_retido_fonte=d["iss_retido_fonte"],
                tem_st=d["tem_st"],
                simples_excedeu_sublimite=d["simples_excedeu_sublimite"],
                observacoes=d["observacoes"],
            )
            with transaction.atomic():
                imposto = uc_imposto.cadastrar_imposto(inp, repo=DjangoImpostoRepository())
                _publicar_evento_config(
                    acao="Config.ImpostoCadastrado",
                    payload={
                        "imposto_id": str(imposto.id),
                        "tipo": imposto.tipo.value,
                        "aliquota": str(imposto.aliquota.valor),
                        "vigencia_inicio": imposto.vigencia.inicio.isoformat(),
                    },
                    causation_id=chave_id,
                    tenant_id=tenant_id,
                    usuario_id=usuario_id,
                    resource_summary=f"imposto {imposto.tipo.value} cadastrado",
                )
        except ImpostoVigenciaSobrepostaError as exc:
            return self._falha(chave_id, tenant_id, exc, status.HTTP_422_UNPROCESSABLE_ENTITY)
        except IntegrityError as exc:
            # Exclusion constraint (a verdade) — corrida que passou pela defesa.
            return self._falha(chave_id, tenant_id, exc, status.HTTP_422_UNPROCESSABLE_ENTITY)
        except ValueError as exc:
            return self._falha(chave_id, tenant_id, exc, status.HTTP_400_BAD_REQUEST)

        body = _serializar_imposto(imposto)
        concluir_chave(
            chave_id=chave_id,
            tenant_id=tenant_id,
            response_status=status.HTTP_201_CREATED,
            response_body_resumo=body,
        )
        return Response(body, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"], url_path="encerrar-vigencia")
    def encerrar_vigencia(self, request: Request, pk: str | None = None) -> Response:
        """POST — D-CFG-3 (one-shot NULL→data). # idempotency-key: required"""
        s = EncerrarVigenciaImpostoSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        d = s.validated_data
        tenant_id, usuario_id = self._contexto()
        if tenant_id is None:
            return Response({"erro": "tenant ausente"}, status=status.HTTP_403_FORBIDDEN)
        imposto_id = self._uuid_ou_404(pk)

        novo, resp = _aplicar_idempotencia(
            request,
            tenant_id=tenant_id,
            usuario_id=usuario_id,
            endpoint="configuracoes_sistema.encerrar_imposto",
            # Fingerprint = payload completo (B6): mesma chave com `fim` diferente
            # é payload divergente, não replay.
            payload_fingerprint={"imposto_id": str(imposto_id), "fim": d["fim"].isoformat()},
        )
        if resp is not None:
            return resp
        assert novo is not None and novo.chave_id is not None
        chave_id = novo.chave_id

        try:
            inp = uc_imposto.EncerrarVigenciaInput(
                tenant_id=tenant_id, imposto_id=imposto_id, fim=d["fim"]
            )
            with transaction.atomic():
                uc_imposto.encerrar_vigencia_imposto(inp, repo=DjangoImpostoRepository())
                _publicar_evento_config(
                    acao="Config.ImpostoVigenciaEncerrada",
                    payload={
                        "imposto_id": str(imposto_id),
                        "fim": d["fim"].isoformat(),
                    },
                    causation_id=chave_id,
                    tenant_id=tenant_id,
                    usuario_id=usuario_id,
                    resource_summary=f"imposto {imposto_id} vigência encerrada",
                )
        except RuntimeError as exc:
            # Linha já encerrada/revogada/inexistente — one-shot violado.
            return self._falha(chave_id, tenant_id, exc, status.HTTP_409_CONFLICT)
        except ValueError as exc:
            return self._falha(chave_id, tenant_id, exc, status.HTTP_400_BAD_REQUEST)

        imposto = next(
            (
                i
                for i in DjangoImpostoRepository().listar(tenant_id=tenant_id)
                if i.id == imposto_id
            ),
            None,
        )
        body = _serializar_imposto(imposto) if imposto else {"imposto_id": str(imposto_id)}
        concluir_chave(
            chave_id=chave_id,
            tenant_id=tenant_id,
            response_status=status.HTTP_200_OK,
            response_body_resumo=body,
        )
        return Response(body, status=status.HTTP_200_OK)


# authz-check: skip -- RequireAuthz global resolve via ACTION_MAP (header)
class SerieDocumentoViewSet(_ConfigViewSetBase):
    """Séries de numeração local — 2 regimes por tipo (US-CFG-002/ADR-0080)."""

    ACTION_MAP = {
        "retrieve": "configuracoes_sistema.ver",
        "criar": "configuracoes_sistema.criar_serie",
        "reservar_numero": "configuracoes_sistema.reservar_numero",
    }

    def retrieve(self, request: Request, pk: str | None = None) -> Response:
        tenant_id = _tenant_ou_none()
        if tenant_id is None:
            return Response({"erro": "tenant ausente"}, status=status.HTTP_403_FORBIDDEN)
        serie = DjangoSerieDocumentoRepository().obter_por_id(
            tenant_id=tenant_id, serie_id=self._uuid_ou_404(pk)
        )
        if serie is None:
            raise NotFound(f"série {pk} não encontrada")
        return Response(_serializar_serie(serie))

    @action(detail=False, methods=["post"], url_path="criar")
    def criar(self, request: Request) -> Response:
        """POST — AC-CFG-002-1 (regime DERIVADO do tipo). # idempotency-key: required"""
        s = CriarSerieSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        d = s.validated_data
        tenant_id, usuario_id = self._contexto()
        if tenant_id is None:
            return Response({"erro": "tenant ausente"}, status=status.HTTP_403_FORBIDDEN)

        novo, resp = _aplicar_idempotencia(
            request,
            tenant_id=tenant_id,
            usuario_id=usuario_id,
            endpoint="configuracoes_sistema.criar_serie",
            # Fingerprint = payload completo (B6).
            payload_fingerprint={
                "tipo": d["tipo"],
                "prefixo": d["prefixo"],
                "formato": d["formato"],
                "padding": d["padding"],
                "filial_id": str(d["filial_id"]) if d["filial_id"] else None,
            },
        )
        if resp is not None:
            return resp
        assert novo is not None and novo.chave_id is not None
        chave_id = novo.chave_id

        try:
            inp = uc_serie.CriarSerieInput(
                tenant_id=tenant_id,
                tipo=TipoDocumento(d["tipo"]),
                prefixo=d["prefixo"],
                formato=d["formato"],
                padding=d["padding"],
                filial_id=d["filial_id"],
            )
            with transaction.atomic():
                serie = uc_serie.criar_serie(inp, repo=DjangoSerieDocumentoRepository())
                _publicar_evento_config(
                    acao="Config.SerieCriada",
                    payload={
                        "serie_id": str(serie.id),
                        "tipo": serie.tipo.value,
                        "prefixo": serie.prefixo,
                        "regime_numeracao": serie.regime_numeracao.value,
                        "reset_anual": serie.reset_anual,
                    },
                    causation_id=chave_id,
                    tenant_id=tenant_id,
                    usuario_id=usuario_id,
                    resource_summary=f"serie {serie.tipo.value}/{serie.prefixo} criada",
                )
        except uc_serie.SerieJaExisteError as exc:
            return self._falha(chave_id, tenant_id, exc, status.HTTP_409_CONFLICT)
        except IntegrityError as exc:
            return self._falha(chave_id, tenant_id, exc, status.HTTP_409_CONFLICT)
        except ValueError as exc:
            return self._falha(chave_id, tenant_id, exc, status.HTTP_400_BAD_REQUEST)

        body = _serializar_serie(serie)
        concluir_chave(
            chave_id=chave_id,
            tenant_id=tenant_id,
            response_status=status.HTTP_201_CREATED,
            response_body_resumo=body,
        )
        return Response(body, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"], url_path="reservar-numero")
    def reservar_numero(self, request: Request, pk: str | None = None) -> Response:
        """POST — AC-CFG-002-2 (INV-028/INV-CFG-NUM-ATOMICA). # idempotency-key: required

        Sem Idempotency-Key, retry de rede consumiria/reservaria 2 números. No
        regime GAP_LESS a resposta é uma RESERVA (TTL 5min) — o emissor confirma
        na própria transação (fluxo do motor M8); não confirmada expira e o
        número volta à sequência. Sem evento Config (consumo operacional).
        """
        tenant_id, usuario_id = self._contexto()
        if tenant_id is None:
            return Response({"erro": "tenant ausente"}, status=status.HTTP_403_FORBIDDEN)
        serie_id = self._uuid_ou_404(pk)

        novo, resp = _aplicar_idempotencia(
            request,
            tenant_id=tenant_id,
            usuario_id=usuario_id,
            endpoint="configuracoes_sistema.reservar_numero",
            payload_fingerprint={"serie_id": str(serie_id)},
        )
        if resp is not None:
            return resp
        assert novo is not None and novo.chave_id is not None
        chave_id = novo.chave_id

        try:
            inp = uc_serie.ReservarNumeroInput(
                tenant_id=tenant_id, serie_id=serie_id, agora=datetime.now(UTC)
            )
            out = uc_serie.reservar_numero(inp, repo=DjangoSerieDocumentoRepository())
        except uc_serie.SerieNaoEncontradaError as exc:
            return self._falha(chave_id, tenant_id, exc, status.HTTP_404_NOT_FOUND)
        except (LookupError, ValueError) as exc:
            return self._falha(chave_id, tenant_id, exc, status.HTTP_400_BAD_REQUEST)

        body = {
            "serie_id": str(out.serie_id),
            "sequencial": out.sequencial,
            "numero_formatado": out.numero_formatado,
            "regime_numeracao": out.regime_numeracao.value,
            "ano": out.ano,
            # GAP_LESS: alvo do confirmar_numero (CFG-IDEMP-01); None em
            # BURACOS_ACEITOS (número já consumido, nada a confirmar).
            "reserva_id": str(out.reserva_id) if out.reserva_id else None,
        }
        concluir_chave(
            chave_id=chave_id,
            tenant_id=tenant_id,
            response_status=status.HTTP_201_CREATED,
            response_body_resumo=body,
        )
        return Response(body, status=status.HTTP_201_CREATED)
