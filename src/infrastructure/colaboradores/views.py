"""ViewSet REST do módulo `colaboradores` (T-COL-035).

ColaboradorViewSet:
  list             — GET  /colaboradores/          (filtros: papel/vinculo/ativo/q)
  create           — POST /colaboradores/           (Dono)
  retrieve         — GET  /colaboradores/{id}/      (mascarado por papel)
  partial_update   — PATCH /colaboradores/{id}/     (CPF imutável)
  destroy          — DELETE /colaboradores/{id}/    (= desligamento, não delete físico)
  @papeis          — POST/DELETE /colaboradores/{id}/papeis/
  @habilidades     — POST/DELETE /colaboradores/{id}/habilidades/
  @documentos      — POST /colaboradores/{id}/documentos/
  @auditoria       — GET  /colaboradores/{id}/auditoria/  (Dono/Qualidade)
  @elegiveis       — GET  /colaboradores/elegiveis/       (DTO mínimo allowlist)
  @comissao_vigente— GET  /colaboradores/{id}/comissao-vigente/

Autorização: RequireAuthz global (ACTION_MAP `colaboradores.*`).
Idempotency-Key: create/partial_update/destroy/papeis POST/DELETE/documentos.
Leitura/elegiveis/comissao-vigente: SEM Idempotency-Key (stateless).

Mascaramento PII (D-COL-7 / INV-COL-PII-MASCARA):
  filtrar_visao_pii() aplicado em TODOS serializers de saída.
  `/elegiveis` usa ElegivelDTOSerializer (allowlist isolada — INV-COL-ELEGIVEIS-MINIMO).

Guard busca-CPF (ADV-COL-08 / anti-oráculo):
  busca por CPF no parâmetro `q` só para papéis com `ver_pii`.

PII em log: NUNCA em claro — só colaborador_id/hashes/tipo (INV-COL-PII-LOG).

# authz-check: skip -- RequireAuthz global resolve via ACTION_MAP (header)
"""

from __future__ import annotations

import logging
from decimal import Decimal
from typing import Any, ClassVar
from uuid import UUID

from django.db import DataError, IntegrityError, transaction
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound
from rest_framework.parsers import MultiPartParser
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet

from src.application.rh_frota_qualidade.colaboradores import cadastro as uc_cadastro
from src.application.rh_frota_qualidade.colaboradores import consultas as uc_consultas
from src.application.rh_frota_qualidade.colaboradores import documentos as uc_documentos
from src.application.rh_frota_qualidade.colaboradores import habilidades as uc_habilidades
from src.application.rh_frota_qualidade.colaboradores import papeis as uc_papeis
from src.domain.rh_frota_qualidade.colaboradores.enums import (
    PapelColaborador,
    TipoDocumento,
    Vinculo,
)
from src.domain.rh_frota_qualidade.colaboradores.erros import (
    ColaboradorInativo,
    ComissaoForaDaFaixa,
    DonoJaExiste,
    DuplicateCpf,
    SignatarioRtNaoCasa,
    SignatarioSemEscopo,
    SignatarioSemUsuario,
)
from src.infrastructure.colaboradores.anexo_storage import obter_anexo_storage
from src.infrastructure.colaboradores.repositories import (
    DjangoColaboradorRepository,
    DjangoHabilidadeRepository,
    DjangoPapelRepository,
)
from src.infrastructure.colaboradores.serializers import (
    AnexarDocumentoSerializer,
    AtribuirPapelSerializer,
    ColaboradorCreateSerializer,
    ColaboradorUpdateSerializer,
    ComissaoVigenteSerializer,
    DesligarColaboradorSerializer,
    ElegivelDTOSerializer,
    RegistrarHabilidadeSerializer,
    RevogarPapelSerializer,
    filtrar_visao_pii,
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
    correlation_id_context,
    usuario_id_context,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helpers de contexto
# ---------------------------------------------------------------------------


def _tenant_id() -> UUID | None:
    return active_tenant_context.get()


def _usuario_id() -> UUID | None:
    return usuario_id_context.get()


def _correlation_id() -> str | None:
    v = correlation_id_context.get()
    return v if v else None


def _papeis_do_usuario(tenant_id: UUID, usuario_id: UUID) -> set[str]:
    """Retorna papéis de negócio ATIVOS do usuário no tenant.

    Busca em ColaboradorPapel por usuario_id via Colaborador.usuario_id.
    Fail-closed: se não encontrar → set vazio.
    """
    from src.infrastructure.colaboradores.models import (
        Colaborador as ColaboradorModel,
    )
    from src.infrastructure.colaboradores.models import (
        ColaboradorPapel as PapelModel,
    )

    colab = (
        ColaboradorModel.ativos.filter(tenant_id=tenant_id, usuario_id=usuario_id)
        .only("id")
        .first()
    )
    if colab is None:
        return set()

    papeis = PapelModel.objects.filter(
        tenant_id=tenant_id,
        colaborador_id=colab.id,
        data_fim__isnull=True,
        revogado_em__isnull=True,
    ).values_list("papel", flat=True)
    return set(papeis)


def _pode_ver_pii(papeis_solicitante: set[str]) -> bool:
    """True se o solicitante tem permissão `ver_pii` (Dono ou papel com acesso)."""
    return PapelColaborador.DONO.value in papeis_solicitante


# ---------------------------------------------------------------------------
# Idempotência
# ---------------------------------------------------------------------------


def _avaliar_idemp(
    request: Request,
    *,
    tenant_id: UUID,
    usuario_id: UUID,
    endpoint: str,
    payload_fp: dict[str, Any],
) -> tuple[NovoProcessamento | None, Response | None]:
    avaliacao = avaliar_chave_idempotencia(
        tenant_id=tenant_id,
        usuario_id=usuario_id,
        endpoint=endpoint,
        chave_header=request.META.get("HTTP_IDEMPOTENCY_KEY"),
        payload=payload_fp,
    )
    if isinstance(avaliacao, ErroValidacao):
        body = {"codigo": avaliacao.codigo, "detalhe": avaliacao.detalhe}
        if avaliacao.headers:
            return None, Response(body, status=avaliacao.http_status, headers=avaliacao.headers)
        return None, Response(body, status=avaliacao.http_status)
    if isinstance(avaliacao, Replay):
        return None, Response(
            avaliacao.response_body_resumo or {}, status=avaliacao.response_status
        )
    assert isinstance(avaliacao, NovoProcessamento)
    return avaliacao, None


def _falha(
    chave_id: UUID,
    tenant_id: UUID,
    exc: Exception,
    http_status: int,
    chave_idemp: NovoProcessamento | None = None,
) -> Response:
    """Registra erro SEM PII no log (INV-COL-PII-LOG)."""
    logger.warning(
        "colaboradores acao recusada",
        extra={
            "chave_id": str(chave_id),
            "http_status": http_status,
            "erro": type(exc).__name__,
            "tenant_id": str(tenant_id),
            "correlation_id": _correlation_id(),
            # NÃO loga str(exc) — pode conter PII (INV-COL-PII-LOG)
        },
    )
    if chave_idemp is not None and chave_idemp.chave_id is not None:
        try:
            falhar_chave(
                chave_id=chave_idemp.chave_id,
                tenant_id=tenant_id,
                response_status=http_status,
            )
        except Exception as _exc_idemp:
            logger.warning(
                "colaboradores falhar_chave ignorada",
                extra={"tenant_id": str(tenant_id), "erro": type(_exc_idemp).__name__},
            )
    reason = getattr(exc, "reason", type(exc).__name__)
    return Response({"codigo": reason, "detalhe": reason}, status=http_status)


def _uuid_ou_404(raw: str | None) -> UUID:
    try:
        return UUID(str(raw))
    except (ValueError, TypeError) as exc:
        raise NotFound(f"id inválido: {exc}") from exc


def _colaborador_dict(
    colab_model: Any, papeis: list[Any], habilidades: list[Any], documentos: list[Any]
) -> dict[str, Any]:
    """Monta dict de colaborador para serialização + mascaramento."""
    return {
        "id": colab_model.id,
        "tenant_id": colab_model.tenant_id,
        "nome": colab_model.nome,
        "cpf": colab_model.cpf,
        "email": colab_model.email,
        "telefone": colab_model.telefone,
        "vinculo": colab_model.vinculo,
        "data_admissao": colab_model.data_admissao,
        "comissao_default_pct": colab_model.comissao_default_pct,
        "observacao": colab_model.observacao,
        "usuario_id": colab_model.usuario_id,
        "foto_storage_key": colab_model.foto_storage_key,
        "data_desligamento": colab_model.data_desligamento,
        "motivo_desligamento": colab_model.motivo_desligamento,
        "ativo": colab_model.data_desligamento is None and colab_model.deletado_em is None,
        "papeis": [
            {
                "id": p.id,
                "papel": p.papel,
                "data_inicio": p.data_inicio,
                "data_fim": p.data_fim,
                "revogado_em": p.revogado_em,
                "responsabilidade_tecnica_id": p.responsabilidade_tecnica_id,
                "pendencia_cnh": p.pendencia_cnh,
            }
            for p in papeis
        ],
        "habilidades": [
            {
                "id": h.id,
                "nivel": h.nivel,
                "data_avaliacao": h.data_avaliacao,
                "catalogo_id": h.catalogo_id,
                "descricao_livre": h.descricao_livre,
                "evidencia_url": h.evidencia_url,
            }
            for h in habilidades
        ],
        "documentos": [
            {
                "id": d.id,
                "tipo": d.tipo,
                "storage_key": d.storage_key,
                "sha256": d.sha256,
                "data_upload": d.data_upload,
                "data_validade": d.data_validade,
            }
            for d in documentos
        ],
    }


def _publicar_evento_colaborador(
    *,
    acao: str,
    payload: dict[str, Any],
    causation_id: UUID,
    tenant_id: UUID,
    usuario_id: UUID | None,
    resource_summary: str,
) -> None:
    """Evento `colaborador.*` via outbox=True (D-COL-10 / T-COL-036).

    PII pseudonimizada (D-COL-8 / ADV-COL-06) — caller já hashifica.
    Import local (molde fiscal/configuracoes — evita ciclo infra→infra).
    """
    from src.infrastructure.audit.event_helpers import publicar_evento

    publicar_evento(
        acao=acao,
        payload=payload,
        causation_id=causation_id,
        tenant_id=tenant_id,
        usuario_id=usuario_id if usuario_id != UUID(int=0) else None,
        resource_summary=resource_summary,
        outbox=True,
        cadeia=True,
    )
    logger.info(
        "colaboradores evento registrado",
        extra={
            "tenant_id": str(tenant_id),
            "acao": acao,
            "correlation_id": _correlation_id(),
        },
    )


def _hmac_tenant(texto: str, tenant_id: UUID) -> str:
    """HMAC-tenant de texto (ADR-0029/0064 — pseudonimização D-COL-8)."""
    from src.infrastructure.calibracao.lgpd import derivar_hash_texto_canonicalizado

    return derivar_hash_texto_canonicalizado(texto=texto, tenant_id=tenant_id)


def _hmac_user(usuario_id: UUID, tenant_id: UUID) -> str:
    """HMAC-tenant de usuario_id (D-COL-8)."""
    from src.infrastructure.calibracao.lgpd import derivar_user_id_hash

    return derivar_user_id_hash(usuario_id=usuario_id, tenant_id=tenant_id)


# ---------------------------------------------------------------------------
# ACTION_MAP authz `colaboradores.*` (D-COL-12 / spec §7)
# ---------------------------------------------------------------------------

_ACTION_MAP: dict[str, str] = {
    "list": "colaboradores.ver",
    "create": "colaboradores.cadastrar",
    "retrieve": "colaboradores.ver",
    "partial_update": "colaboradores.editar",
    "destroy": "colaboradores.desligar",
    "papeis": "colaboradores.gerir_papel",
    "habilidades": "colaboradores.gerir_habilidade",
    "documentos": "colaboradores.gerir_habilidade",  # reutiliza permissão
    "auditoria": "colaboradores.ver_auditoria",
    "elegiveis": "colaboradores.consultar_elegiveis",
    "comissao_vigente": "colaboradores.ver_comissao",
}


# ---------------------------------------------------------------------------
# ViewSet
# ---------------------------------------------------------------------------


class ColaboradorViewSet(ViewSet):
    """ViewSet REST de colaboradores (T-COL-035 / spec §7).

    Autorização: RequireAuthz global (ACTION_MAP `colaboradores.*`).
    """

    ACTION_MAP: ClassVar[dict[str, str]] = _ACTION_MAP
    authz_purpose: str = "gestao_colaboradores"

    def get_authz_action(self, request: Request) -> str | None:
        action_name = getattr(self, "action", None)
        return self.ACTION_MAP.get(action_name) if action_name else None

    def get_authz_resource(self, request: Request) -> dict[str, Any]:
        return {}

    # ------------------------------------------------------------------
    # list
    # ------------------------------------------------------------------

    def list(self, request: Request) -> Response:
        """GET /colaboradores/ — lista paginada com filtros (prefetch anti-N+1)."""
        tenant_id = _tenant_id()
        usuario_id = _usuario_id()
        if tenant_id is None or usuario_id is None:
            return Response(
                {"codigo": "SemContexto", "detalhe": "sem contexto"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        from django.db.models import Prefetch

        from src.infrastructure.colaboradores.models import (
            Colaborador as ColaboradorModel,
        )
        from src.infrastructure.colaboradores.models import (
            ColaboradorDocumento as DocModel,
        )
        from src.infrastructure.colaboradores.models import (
            ColaboradorHabilidade as HabModel,
        )
        from src.infrastructure.colaboradores.models import (
            ColaboradorPapel as PapelModel,
        )

        papeis_solicitante = _papeis_do_usuario(tenant_id, usuario_id)
        pode_pii = _pode_ver_pii(papeis_solicitante)

        qs = ColaboradorModel.objects.filter(tenant_id=tenant_id).prefetch_related(
            Prefetch(
                "papeis",
                queryset=PapelModel.objects.filter(revogado_em__isnull=True, data_fim__isnull=True),
                to_attr="_papeis",
            ),
            Prefetch("habilidades", queryset=HabModel.objects.all(), to_attr="_habilidades"),
            Prefetch("documentos", queryset=DocModel.objects.all(), to_attr="_documentos"),
        )

        # Filtros
        papel_filtro = request.query_params.get("papel")
        if papel_filtro:
            qs = qs.filter(
                papeis__papel=papel_filtro,
                papeis__revogado_em__isnull=True,
                papeis__data_fim__isnull=True,
            ).distinct()

        vinculo_filtro = request.query_params.get("vinculo")
        if vinculo_filtro:
            qs = qs.filter(vinculo=vinculo_filtro)

        ativo_filtro = request.query_params.get("ativo")
        if ativo_filtro == "true":
            qs = qs.filter(data_desligamento__isnull=True)
        elif ativo_filtro == "false":
            qs = qs.filter(data_desligamento__isnull=False)

        # Guard busca-CPF: só quem tem ver_pii pode buscar por CPF (ADV-COL-08)
        q = request.query_params.get("q", "").strip()
        if q:
            import re

            cpf_digits = re.sub(r"\D", "", q)
            eh_busca_cpf = len(cpf_digits) == 11
            if eh_busca_cpf:
                if pode_pii:
                    qs = qs.filter(cpf=cpf_digits)
                else:
                    # Anti-oráculo: sem papel ver_pii, busca por CPF retorna vazio
                    qs = qs.none()
            else:
                qs = qs.filter(nome__icontains=q)

        # Paginação simples (≤100)
        qs = qs[:100]

        resultado = []
        for colab in qs:
            dados = _colaborador_dict(
                colab,
                getattr(colab, "_papeis", []),
                getattr(colab, "_habilidades", []),
                getattr(colab, "_documentos", []),
            )
            eh_proprio = colab.usuario_id == usuario_id
            dados_mascarados = filtrar_visao_pii(
                papeis_solicitante, eh_proprio=eh_proprio, dados=dados
            )
            resultado.append(dados_mascarados)

        return Response(resultado)

    # ------------------------------------------------------------------
    # create
    # ------------------------------------------------------------------

    def create(self, request: Request) -> Response:
        """POST /colaboradores/ — cadastra colaborador (Dono)."""
        tenant_id = _tenant_id()
        usuario_id = _usuario_id()
        if tenant_id is None or usuario_id is None:
            return Response(
                {"codigo": "SemContexto", "detalhe": "sem contexto"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        ser = ColaboradorCreateSerializer(data=request.data)
        if not ser.is_valid():
            return Response(ser.errors, status=status.HTTP_422_UNPROCESSABLE_ENTITY)

        chave_idemp, resp_idemp = _avaliar_idemp(
            request,
            tenant_id=tenant_id,
            usuario_id=usuario_id,
            endpoint="colaboradores.create",
            payload_fp=ser.validated_data,
        )
        if resp_idemp is not None:
            return resp_idemp

        assert chave_idemp is not None
        try:
            with transaction.atomic():
                d = ser.validated_data
                cmd = uc_cadastro.ComandoCadastrarColaborador(
                    tenant_id=tenant_id,
                    nome=d["nome"],
                    cpf_value=d["cpf"],
                    email=d["email"],
                    telefone=d["telefone"],
                    vinculo=Vinculo(d["vinculo"]),
                    data_admissao=d["data_admissao"],
                    comissao_default_pct=Decimal(str(d["comissao_default_pct"])),
                    observacao=d.get("observacao", ""),
                    usuario_id=d.get("usuario_id"),
                )
                repo = DjangoColaboradorRepository()
                colaborador_id = uc_cadastro.cadastrar_colaborador(cmd, repo_colab=repo)

                # Evento Colaborador.Cadastrado (outbox=True — D-COL-10)
                import uuid as _uuid

                causation_id = _uuid.uuid5(
                    _uuid.NAMESPACE_URL,
                    f"colaborador.cadastrado:{tenant_id}:{colaborador_id}",
                )
                _publicar_evento_colaborador(
                    acao="colaborador.cadastrado",
                    payload={
                        "colaborador_id": str(colaborador_id),
                        "tenant_id": str(tenant_id),
                        "vinculo": d["vinculo"],
                        "cpf_hash": _hmac_tenant(
                            d["cpf"].replace(".", "").replace("-", ""), tenant_id
                        ),
                        "nome_hash": _hmac_tenant(d["nome"], tenant_id),
                    },
                    causation_id=causation_id,
                    tenant_id=tenant_id,
                    usuario_id=usuario_id,
                    resource_summary=f"colaborador:{colaborador_id}",
                )

        except DuplicateCpf as exc:
            return _falha(tenant_id, tenant_id, exc, status.HTTP_409_CONFLICT, chave_idemp)
        except (
            SignatarioSemUsuario,
            SignatarioRtNaoCasa,
            SignatarioSemEscopo,
            ComissaoForaDaFaixa,
        ) as exc:
            return _falha(
                tenant_id, tenant_id, exc, status.HTTP_422_UNPROCESSABLE_ENTITY, chave_idemp
            )
        except (DataError, IntegrityError) as exc:
            return _falha(tenant_id, tenant_id, exc, status.HTTP_409_CONFLICT, chave_idemp)
        except Exception as exc:
            return _falha(
                tenant_id, tenant_id, exc, status.HTTP_500_INTERNAL_SERVER_ERROR, chave_idemp
            )

        body = {"colaborador_id": str(colaborador_id)}
        if chave_idemp.chave_id is not None:
            concluir_chave(
                chave_id=chave_idemp.chave_id,
                tenant_id=tenant_id,
                response_status=status.HTTP_201_CREATED,
                response_body_resumo=body,
            )
        return Response(body, status=status.HTTP_201_CREATED)

    # ------------------------------------------------------------------
    # retrieve
    # ------------------------------------------------------------------

    def retrieve(self, request: Request, pk: str | None = None) -> Response:
        """GET /colaboradores/{id}/ — agregado mascarado por papel."""
        tenant_id = _tenant_id()
        usuario_id = _usuario_id()
        if tenant_id is None or usuario_id is None:
            return Response(
                {"codigo": "SemContexto", "detalhe": "sem contexto"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        colab_id = _uuid_ou_404(pk)
        papeis_solicitante = _papeis_do_usuario(tenant_id, usuario_id)

        from django.db.models import Prefetch

        from src.infrastructure.colaboradores.models import (
            Colaborador as ColaboradorModel,
        )
        from src.infrastructure.colaboradores.models import (
            ColaboradorDocumento as DocModel,
        )
        from src.infrastructure.colaboradores.models import (
            ColaboradorHabilidade as HabModel,
        )
        from src.infrastructure.colaboradores.models import (
            ColaboradorPapel as PapelModel,
        )

        colab = (
            ColaboradorModel.objects.filter(tenant_id=tenant_id, id=colab_id)
            .prefetch_related(
                Prefetch("papeis", queryset=PapelModel.objects.all(), to_attr="_papeis"),
                Prefetch("habilidades", queryset=HabModel.objects.all(), to_attr="_habilidades"),
                Prefetch("documentos", queryset=DocModel.objects.all(), to_attr="_documentos"),
            )
            .first()
        )
        if colab is None:
            raise NotFound(f"Colaborador {colab_id} não encontrado.")

        dados = _colaborador_dict(
            colab,
            getattr(colab, "_papeis", []),
            getattr(colab, "_habilidades", []),
            getattr(colab, "_documentos", []),
        )
        eh_proprio = colab.usuario_id == usuario_id
        dados_mascarados = filtrar_visao_pii(papeis_solicitante, eh_proprio=eh_proprio, dados=dados)
        return Response(dados_mascarados)

    # ------------------------------------------------------------------
    # partial_update
    # ------------------------------------------------------------------

    def partial_update(self, request: Request, pk: str | None = None) -> Response:
        """PATCH /colaboradores/{id}/ — edição parcial (CPF imutável)."""
        tenant_id = _tenant_id()
        usuario_id = _usuario_id()
        if tenant_id is None or usuario_id is None:
            return Response(
                {"codigo": "SemContexto", "detalhe": "sem contexto"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        colab_id = _uuid_ou_404(pk)
        ser = ColaboradorUpdateSerializer(data=request.data, partial=True)
        if not ser.is_valid():
            return Response(ser.errors, status=status.HTTP_422_UNPROCESSABLE_ENTITY)

        chave_idemp, resp_idemp = _avaliar_idemp(
            request,
            tenant_id=tenant_id,
            usuario_id=usuario_id,
            endpoint=f"colaboradores.partial_update.{colab_id}",
            payload_fp={**ser.validated_data, "_id": str(colab_id)},
        )
        if resp_idemp is not None:
            return resp_idemp
        assert chave_idemp is not None

        try:
            with transaction.atomic():
                d = ser.validated_data
                cmd = uc_cadastro.ComandoEditarColaborador(
                    tenant_id=tenant_id,
                    colaborador_id=colab_id,
                    nome=d.get("nome"),
                    email=d.get("email"),
                    telefone=d.get("telefone"),
                    vinculo=Vinculo(d["vinculo"]) if "vinculo" in d else None,
                    data_admissao=d.get("data_admissao"),
                    comissao_default_pct=Decimal(str(d["comissao_default_pct"]))
                    if "comissao_default_pct" in d
                    else None,
                    observacao=d.get("observacao"),
                    usuario_id=d.get("usuario_id"),
                )
                repo = DjangoColaboradorRepository()
                uc_cadastro.editar_colaborador(cmd, repo_colab=repo)
        except ColaboradorInativo as exc:
            return _falha(colab_id, tenant_id, exc, status.HTTP_409_CONFLICT, chave_idemp)
        except ComissaoForaDaFaixa as exc:
            return _falha(
                colab_id, tenant_id, exc, status.HTTP_422_UNPROCESSABLE_ENTITY, chave_idemp
            )
        except Exception as exc:
            return _falha(
                colab_id, tenant_id, exc, status.HTTP_500_INTERNAL_SERVER_ERROR, chave_idemp
            )

        body = {"colaborador_id": str(colab_id)}
        if chave_idemp.chave_id is not None:
            concluir_chave(
                chave_id=chave_idemp.chave_id,
                tenant_id=tenant_id,
                response_status=status.HTTP_200_OK,
                response_body_resumo=body,
            )
        return Response(body)

    # ------------------------------------------------------------------
    # destroy = desligamento (não hard-delete)
    # ------------------------------------------------------------------

    def destroy(self, request: Request, pk: str | None = None) -> Response:
        """DELETE /colaboradores/{id}/ = desligamento (D-COL-3 / AC-COL-06).

        Cascade: revoga papéis + publica `colaborador.desligado` via outbox.
        Idempotente por chave estável (TL-COL-13 / D-COL-10).
        """
        tenant_id = _tenant_id()
        usuario_id = _usuario_id()
        if tenant_id is None or usuario_id is None:
            return Response(
                {"codigo": "SemContexto", "detalhe": "sem contexto"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        colab_id = _uuid_ou_404(pk)
        ser = DesligarColaboradorSerializer(data=request.data)
        if not ser.is_valid():
            return Response(ser.errors, status=status.HTTP_422_UNPROCESSABLE_ENTITY)

        d = ser.validated_data
        chave_idemp, resp_idemp = _avaliar_idemp(
            request,
            tenant_id=tenant_id,
            usuario_id=usuario_id,
            endpoint=f"colaboradores.desligar.{colab_id}",
            payload_fp={
                "colaborador_id": str(colab_id),
                "data_desligamento": str(d["data_desligamento"]),
            },
        )
        if resp_idemp is not None:
            return resp_idemp
        assert chave_idemp is not None

        try:
            with transaction.atomic():
                cmd = uc_cadastro.ComandoDesligarColaborador(
                    tenant_id=tenant_id,
                    colaborador_id=colab_id,
                    data_desligamento=d["data_desligamento"],
                    motivo_desligamento=d["motivo_desligamento"],
                    ator_id=usuario_id,
                )
                uc_cadastro.desligar_colaborador(
                    cmd,
                    repo_colab=DjangoColaboradorRepository(),
                    repo_papel=DjangoPapelRepository(),
                    tenant_id_para_evento=tenant_id,
                )
        except ColaboradorInativo as exc:
            return _falha(colab_id, tenant_id, exc, status.HTTP_409_CONFLICT, chave_idemp)
        except Exception as exc:
            return _falha(
                colab_id, tenant_id, exc, status.HTTP_500_INTERNAL_SERVER_ERROR, chave_idemp
            )

        body = {"colaborador_id": str(colab_id), "desligado": True}
        if chave_idemp.chave_id is not None:
            concluir_chave(
                chave_id=chave_idemp.chave_id,
                tenant_id=tenant_id,
                response_status=status.HTTP_200_OK,
                response_body_resumo=body,
            )
        return Response(body)

    # ------------------------------------------------------------------
    # @action papeis
    # ------------------------------------------------------------------

    @action(detail=True, methods=["post", "delete"], url_path="papeis")
    def papeis(self, request: Request, pk: str | None = None) -> Response:
        """POST/DELETE /colaboradores/{id}/papeis/ — atribuir/revogar papel."""
        tenant_id = _tenant_id()
        usuario_id = _usuario_id()
        if tenant_id is None or usuario_id is None:
            return Response(
                {"codigo": "SemContexto", "detalhe": "sem contexto"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        colab_id = _uuid_ou_404(pk)
        repo_colab = DjangoColaboradorRepository()
        repo_papel = DjangoPapelRepository()

        if request.method == "POST":
            ser = AtribuirPapelSerializer(data=request.data)
            if not ser.is_valid():
                return Response(ser.errors, status=status.HTTP_422_UNPROCESSABLE_ENTITY)

            chave_idemp, resp_idemp = _avaliar_idemp(
                request,
                tenant_id=tenant_id,
                usuario_id=usuario_id,
                endpoint=f"colaboradores.papeis.atribuir.{colab_id}",
                payload_fp={**ser.validated_data, "_colab": str(colab_id)},
            )
            if resp_idemp is not None:
                return resp_idemp
            assert chave_idemp is not None

            try:
                with transaction.atomic():
                    d = ser.validated_data
                    cmd = uc_papeis.ComandoAtribuirPapel(
                        tenant_id=tenant_id,
                        colaborador_id=colab_id,
                        papel=PapelColaborador(d["papel"]),
                        data_inicio=d["data_inicio"],
                        data_fim=d.get("data_fim"),
                        responsabilidade_tecnica_id=d.get("responsabilidade_tecnica_id"),
                        tem_cnh=d.get("tem_cnh", True),
                        perfil_tenant="A",  # GATE-COL-PERFIL-MATRIZ
                    )
                    papel_id = uc_papeis.atribuir_papel(
                        cmd, repo_colab=repo_colab, repo_papel=repo_papel
                    )

                    # Evento PapelAtribuido (outbox=True)
                    import uuid as _uuid

                    causation_id = _uuid.uuid5(
                        _uuid.NAMESPACE_URL,
                        f"colaborador.papel_atribuido:{tenant_id}:{papel_id}",
                    )
                    ator_hash = _hmac_user(usuario_id, tenant_id)
                    _publicar_evento_colaborador(
                        acao="colaborador.papel_atribuido",
                        payload={
                            "colaborador_id": str(colab_id),
                            "papel_id": str(papel_id),
                            "papel": d["papel"],
                            "vigencia_inicio": str(d["data_inicio"]),
                            "ator_id_hash": ator_hash,
                        },
                        causation_id=causation_id,
                        tenant_id=tenant_id,
                        usuario_id=usuario_id,
                        resource_summary=f"colaborador:{colab_id}:papel:{papel_id}",
                    )
            except ColaboradorInativo as exc:
                return _falha(colab_id, tenant_id, exc, status.HTTP_409_CONFLICT, chave_idemp)
            except (SignatarioSemUsuario, SignatarioRtNaoCasa, SignatarioSemEscopo) as exc:
                return _falha(
                    colab_id, tenant_id, exc, status.HTTP_422_UNPROCESSABLE_ENTITY, chave_idemp
                )
            except DonoJaExiste as exc:
                return _falha(colab_id, tenant_id, exc, status.HTTP_409_CONFLICT, chave_idemp)
            except IntegrityError as exc:
                return _falha(colab_id, tenant_id, exc, status.HTTP_409_CONFLICT, chave_idemp)
            except Exception as exc:
                return _falha(
                    colab_id, tenant_id, exc, status.HTTP_500_INTERNAL_SERVER_ERROR, chave_idemp
                )

            body = {"papel_id": str(papel_id)}
            if chave_idemp.chave_id is not None:
                concluir_chave(
                    chave_id=chave_idemp.chave_id,
                    tenant_id=tenant_id,
                    response_status=status.HTTP_201_CREATED,
                    response_body_resumo=body,
                )
            return Response(body, status=status.HTTP_201_CREATED)

        else:  # DELETE
            ser_rev = RevogarPapelSerializer(data=request.data)
            if not ser_rev.is_valid():
                return Response(ser_rev.errors, status=status.HTTP_422_UNPROCESSABLE_ENTITY)

            chave_idemp, resp_idemp = _avaliar_idemp(
                request,
                tenant_id=tenant_id,
                usuario_id=usuario_id,
                endpoint=f"colaboradores.papeis.revogar.{colab_id}",
                payload_fp={**ser_rev.validated_data, "_colab": str(colab_id)},
            )
            if resp_idemp is not None:
                return resp_idemp
            assert chave_idemp is not None

            try:
                with transaction.atomic():
                    d_rev = ser_rev.validated_data
                    cmd_rev = uc_papeis.ComandoRevogarPapel(
                        tenant_id=tenant_id,
                        colaborador_id=colab_id,
                        papel_id=d_rev["papel_id"],
                    )
                    uc_papeis.revogar_papel(cmd_rev, repo_colab=repo_colab, repo_papel=repo_papel)

                    import uuid as _uuid

                    causation_id = _uuid.uuid5(
                        _uuid.NAMESPACE_URL,
                        f"colaborador.papel_revogado:{tenant_id}:{d_rev['papel_id']}",
                    )
                    _publicar_evento_colaborador(
                        acao="colaborador.papel_revogado",
                        payload={
                            "colaborador_id": str(colab_id),
                            "papel_id": str(d_rev["papel_id"]),
                            "ator_id_hash": _hmac_user(usuario_id, tenant_id),
                        },
                        causation_id=causation_id,
                        tenant_id=tenant_id,
                        usuario_id=usuario_id,
                        resource_summary=f"colaborador:{colab_id}:papel:{d_rev['papel_id']}",
                    )
            except ColaboradorInativo as exc:
                return _falha(colab_id, tenant_id, exc, status.HTTP_409_CONFLICT, chave_idemp)
            except Exception as exc:
                return _falha(
                    colab_id, tenant_id, exc, status.HTTP_500_INTERNAL_SERVER_ERROR, chave_idemp
                )

            body_rev: dict[str, object] = {"papel_id": str(d_rev["papel_id"]), "revogado": True}
            if chave_idemp.chave_id is not None:
                concluir_chave(
                    chave_id=chave_idemp.chave_id,
                    tenant_id=tenant_id,
                    response_status=status.HTTP_200_OK,
                    response_body_resumo=body_rev,
                )
            return Response(body_rev)

    # ------------------------------------------------------------------
    # @action habilidades
    # ------------------------------------------------------------------

    @action(detail=True, methods=["post", "delete"], url_path="habilidades")
    def habilidades(self, request: Request, pk: str | None = None) -> Response:
        """POST/DELETE /colaboradores/{id}/habilidades/."""
        tenant_id = _tenant_id()
        usuario_id = _usuario_id()
        if tenant_id is None or usuario_id is None:
            return Response(
                {"codigo": "SemContexto", "detalhe": "sem contexto"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        colab_id = _uuid_ou_404(pk)

        if request.method == "POST":
            ser = RegistrarHabilidadeSerializer(data=request.data)
            if not ser.is_valid():
                return Response(ser.errors, status=status.HTTP_422_UNPROCESSABLE_ENTITY)

            chave_idemp, resp_idemp = _avaliar_idemp(
                request,
                tenant_id=tenant_id,
                usuario_id=usuario_id,
                endpoint=f"colaboradores.habilidades.registrar.{colab_id}",
                payload_fp={**ser.validated_data, "_colab": str(colab_id)},
            )
            if resp_idemp is not None:
                return resp_idemp
            assert chave_idemp is not None

            try:
                with transaction.atomic():
                    d = ser.validated_data
                    from src.domain.rh_frota_qualidade.colaboradores.enums import NivelHabilidade

                    cmd = uc_habilidades.ComandoRegistrarHabilidade(
                        tenant_id=tenant_id,
                        colaborador_id=colab_id,
                        nivel=NivelHabilidade(d["nivel"]),
                        data_avaliacao=d["data_avaliacao"],
                        catalogo_id=d.get("catalogo_id"),
                        descricao_livre=d.get("descricao_livre"),
                        evidencia_url=d.get("evidencia_url"),
                    )
                    habilidade_id = uc_habilidades.registrar_habilidade(
                        cmd,
                        repo_colab=DjangoColaboradorRepository(),
                        repo_hab=DjangoHabilidadeRepository(),
                    )

                    import uuid as _uuid

                    causation_id = _uuid.uuid5(
                        _uuid.NAMESPACE_URL,
                        f"colaborador.habilidade_atualizada:{tenant_id}:{habilidade_id}",
                    )
                    _publicar_evento_colaborador(
                        acao="colaborador.habilidade_atualizada",
                        payload={
                            "colaborador_id": str(colab_id),
                            "habilidade_id": str(habilidade_id),
                            "nivel": d["nivel"],
                        },
                        causation_id=causation_id,
                        tenant_id=tenant_id,
                        usuario_id=usuario_id,
                        resource_summary=f"colaborador:{colab_id}:habilidade:{habilidade_id}",
                    )
            except ColaboradorInativo as exc:
                return _falha(colab_id, tenant_id, exc, status.HTTP_409_CONFLICT, chave_idemp)
            except ValueError as exc:
                return _falha(
                    colab_id, tenant_id, exc, status.HTTP_422_UNPROCESSABLE_ENTITY, chave_idemp
                )
            except Exception as exc:
                return _falha(
                    colab_id, tenant_id, exc, status.HTTP_500_INTERNAL_SERVER_ERROR, chave_idemp
                )

            body = {"habilidade_id": str(habilidade_id)}
            if chave_idemp.chave_id is not None:
                concluir_chave(
                    chave_id=chave_idemp.chave_id,
                    tenant_id=tenant_id,
                    response_status=status.HTTP_201_CREATED,
                    response_body_resumo=body,
                )
            return Response(body, status=status.HTTP_201_CREATED)

        else:
            return Response(
                {
                    "codigo": "NaoImplementado",
                    "detalhe": "DELETE habilidade não implementado nesta fatia",
                },
                status=status.HTTP_501_NOT_IMPLEMENTED,
            )

    # ------------------------------------------------------------------
    # @action documentos
    # ------------------------------------------------------------------

    @action(detail=True, methods=["post"], url_path="documentos", parser_classes=[MultiPartParser])
    def documentos(self, request: Request, pk: str | None = None) -> Response:
        """POST /colaboradores/{id}/documentos/ — upload de documento."""
        tenant_id = _tenant_id()
        usuario_id = _usuario_id()
        if tenant_id is None or usuario_id is None:
            return Response(
                {"codigo": "SemContexto", "detalhe": "sem contexto"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        colab_id = _uuid_ou_404(pk)
        ser = AnexarDocumentoSerializer(data=request.data)
        if not ser.is_valid():
            return Response(ser.errors, status=status.HTTP_422_UNPROCESSABLE_ENTITY)

        arquivo = request.FILES.get("arquivo")
        if arquivo is None:
            return Response(
                {"codigo": "ArquivoAusente", "detalhe": "Campo 'arquivo' obrigatório"},
                status=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )

        chave_idemp, resp_idemp = _avaliar_idemp(
            request,
            tenant_id=tenant_id,
            usuario_id=usuario_id,
            endpoint=f"colaboradores.documentos.anexar.{colab_id}",
            payload_fp={"tipo": ser.validated_data["tipo"], "_colab": str(colab_id)},
        )
        if resp_idemp is not None:
            return resp_idemp
        assert chave_idemp is not None

        try:
            with transaction.atomic():
                d = ser.validated_data
                arquivo_bytes = arquivo.read()
                mime_type = arquivo.content_type or "application/octet-stream"

                cmd = uc_documentos.ComandoAnexarDocumento(
                    tenant_id=tenant_id,
                    colaborador_id=colab_id,
                    tipo=TipoDocumento(d["tipo"]),
                    arquivo_bytes=arquivo_bytes,
                    nome_sugerido=arquivo.name or "documento",
                    mime_type=mime_type,
                    data_validade=d.get("data_validade"),
                )
                storage = obter_anexo_storage()
                documento_id = uc_documentos.anexar_documento(
                    cmd,
                    repo_colab=DjangoColaboradorRepository(),
                    storage_port=storage,
                )
        except ColaboradorInativo as exc:
            return _falha(colab_id, tenant_id, exc, status.HTTP_409_CONFLICT, chave_idemp)
        except uc_documentos.ArquivoInvalido as exc:
            return _falha(
                colab_id, tenant_id, exc, status.HTTP_422_UNPROCESSABLE_ENTITY, chave_idemp
            )
        except Exception as exc:
            return _falha(
                colab_id, tenant_id, exc, status.HTTP_500_INTERNAL_SERVER_ERROR, chave_idemp
            )

        body = {"documento_id": str(documento_id)}
        if chave_idemp.chave_id is not None:
            concluir_chave(
                chave_id=chave_idemp.chave_id,
                tenant_id=tenant_id,
                response_status=status.HTTP_201_CREATED,
                response_body_resumo=body,
            )
        return Response(body, status=status.HTTP_201_CREATED)

    # ------------------------------------------------------------------
    # @action auditoria
    # ------------------------------------------------------------------

    @action(detail=True, methods=["get"], url_path="auditoria")
    def auditoria(self, request: Request, pk: str | None = None) -> Response:
        """GET /colaboradores/{id}/auditoria/ — Dono/Qualidade (D-COL-14)."""
        tenant_id = _tenant_id()
        usuario_id = _usuario_id()
        if tenant_id is None or usuario_id is None:
            return Response(
                {"codigo": "SemContexto", "detalhe": "sem contexto"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        papeis_solicitante = _papeis_do_usuario(tenant_id, usuario_id)
        pode_ver = (
            PapelColaborador.DONO.value in papeis_solicitante
            or PapelColaborador.QUALIDADE.value in papeis_solicitante
        )
        if not pode_ver:
            return Response(
                {"codigo": "Proibido", "detalhe": "Apenas Dono/Qualidade podem ver auditoria"},
                status=status.HTTP_403_FORBIDDEN,
            )

        colab_id = _uuid_ou_404(pk)

        from src.infrastructure.audit.models import Auditoria

        eventos = (
            Auditoria.objects.filter(
                tenant_id=tenant_id,
                resource_summary__icontains=str(colab_id),
            )
            .order_by("-timestamp")
            .values("id", "action", "timestamp", "resource_summary")[:50]
        )
        return Response(list(eventos))

    # ------------------------------------------------------------------
    # @action elegiveis
    # ------------------------------------------------------------------

    @action(detail=False, methods=["get"], url_path="elegiveis")
    def elegiveis(self, request: Request) -> Response:
        """GET /colaboradores/elegiveis/ — DTO mínimo (INV-COL-ELEGIVEIS-MINIMO).

        NUNCA retorna CPF/e-mail/telefone/documentos/comissão/foto/vínculo/observação.
        Sem Idempotency-Key (leitura stateless).
        """
        tenant_id = _tenant_id()
        if tenant_id is None:
            return Response(
                {"codigo": "SemContexto", "detalhe": "sem contexto"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        papel_filtro = request.query_params.get("papel")
        papel_enum = PapelColaborador(papel_filtro) if papel_filtro else None
        habilidade_codigo = request.query_params.get("habilidade")

        elegiveis = uc_consultas.consultar_elegiveis(
            tenant_id=tenant_id,
            papel=papel_enum,
            habilidade_codigo=habilidade_codigo,
        )

        ser = ElegivelDTOSerializer(
            [
                {
                    "colaborador_id": e.colaborador_id,
                    "nome_exibicao": e.nome_exibicao,
                    "papel": e.papel.value if e.papel else None,
                    "habilidades": [
                        {"nivel": h.nivel.value, "descricao": h.descricao} for h in e.habilidades
                    ],
                    "ativo": e.ativo,
                }
                for e in elegiveis
            ],
            many=True,
        )
        return Response(ser.data)

    # ------------------------------------------------------------------
    # @action comissao_vigente
    # ------------------------------------------------------------------

    @action(detail=True, methods=["get"], url_path="comissao-vigente")
    def comissao_vigente(self, request: Request, pk: str | None = None) -> Response:
        """GET /colaboradores/{id}/comissao-vigente/ — D-COL-9 / AC-COL-04.

        Sem Idempotency-Key (leitura stateless).
        """
        tenant_id = _tenant_id()
        if tenant_id is None:
            return Response(
                {"codigo": "SemContexto", "detalhe": "sem contexto"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        colab_id = _uuid_ou_404(pk)
        resultado = uc_consultas.comissao_vigente(
            tenant_id=tenant_id,
            colaborador_id=colab_id,
        )
        if resultado is None:
            raise NotFound(f"Colaborador {colab_id} não encontrado.")

        ser = ComissaoVigenteSerializer(
            {
                "pct_default": resultado.pct_default,
                "vigente_desde": resultado.vigente_desde,
            }
        )
        return Response(ser.data)
