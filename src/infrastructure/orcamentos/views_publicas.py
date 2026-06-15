"""Endpoint PÚBLICO de aprovação de orçamento (Onda 2e — T-ORC-038 / D-ORC-7/19).

GET  /api/v1/public/orcamentos/{token}/         → preview allowlist + ressalvas
POST /api/v1/public/orcamentos/{token}/aprovar/ → aprovação 1-clique (Aprovacao WORM)

SEM autenticação (token opaco = autorização). O token resolve o tenant SEM RLS via
`resolver_orc_publico_token` (migration 0009 — `repo.get_link_por_token`); então a
view entra em `run_in_tenant_context(tenant_id)` e o resto roda sob RLS normal.

Segurança (D-ORC-7/19 / `[SEC-PRE-PROD]`):
  - Rate-limit por IP (30 req/min — GATE-ORC-RATELIMIT-PUBLICO p/ alerta + lockout).
  - Token inválido/expirado/revogado → 404 (não vaza existência — ADV-ORC-08a).
  - PII do aprovador (nome/email/ip) em HMAC (D-ORC-17; exibição = GATE-ORC-KMS-APROVADOR).
  - Serializer público allowlist (NUNCA margem/custo/comissão/observações — ADV-ORC-09).

Análise crítica cl. 7.1 reusa o motor da aprovação interna (`aprovar_orcamento`):
  - GET faz a decisão PURA (sem gravar) só para exibir ressalvas.
  - POST: reprovada (perfil A) → grava análise WORM + evento + 422 (sem Aprovacao);
    com_ressalva média sem `ressalvas_confirmadas` → 422; aprovável → cria Aprovacao
    WORM (avaliada_por="SISTEMA/AUTO:<aprovacao_id>" — C5) + aprova + publica.

# authz-check: skip -- endpoint PUBLICO via PublicEndpoint mixin (token = autorização, D-ORC-19)
"""

from __future__ import annotations

import hashlib
import hmac
import logging
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any
from uuid import UUID, uuid4

from django.conf import settings
from django.core.cache import caches
from django.db import transaction
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from src.application.comercial.orcamentos import aprovacao as uc_aprovar
from src.domain.comercial.orcamentos.analise_critica import (
    DecisaoAnaliseCritica,
    decidir_analise_critica,
)
from src.domain.comercial.orcamentos.entities import Aprovacao
from src.domain.comercial.orcamentos.enums import (
    CanalAprovacao,
    EstadoOrcamento,
    VeredictoAnaliseCritica,
)
from src.domain.comercial.orcamentos.erros import PerfilIndeterminado
from src.infrastructure.authz.decorators import PublicEndpoint
from src.infrastructure.multitenant.connection import run_in_tenant_context
from src.infrastructure.orcamentos.analise_critica_ports import (
    avaliar_itens_calibracao,
    resolver_perfil_e_suspensao,
)
from src.infrastructure.orcamentos.repositories import DjangoOrcamentoRepository
from src.infrastructure.orcamentos.serializers_publico import (
    AprovarPublicoSerializer,
    serializar_orcamento_publico,
)
from src.infrastructure.orcamentos.views import _publicar_eventos_analise

if TYPE_CHECKING:
    from src.domain.comercial.orcamentos.entities import LinkPublico

logger = logging.getLogger(__name__)

# Rate-limit do endpoint público (Wave A). 30 req/min/IP (D-ORC-7). O alerta
# `aprovacao-suspeita` (>5/min) + lockout = GATE-ORC-RATELIMIT-PUBLICO.
_LIMITE_REQ_MIN = 30
_JANELA_SEG = 60

# IP em HMAC com salt GLOBAL (cross-tenant; reusa o salt do rate-limit do QR —
# GATE-ORC-KMS-APROVADOR difere a cifragem KMS dedicada). Truncado a 128 bits.
_IP_SALT = settings.QR_IP_RATELIMIT_SALT.encode("utf-8")


def _hash_ip(
    ip: str,
) -> str:  # audit-pii-salt: skip -- ip forense/rate-limit cross-tenant exige salt GLOBAL; HMAC protege contra rainbow table; KMS dedicado = GATE-ORC-KMS-APROVADOR
    """HMAC-SHA256 do IP com salt global (forense + rate-limit). '' se vazio."""
    if not ip:
        return ""
    return hmac.new(_IP_SALT, ip.encode("utf-8"), hashlib.sha256).hexdigest()[:32]


def _extrair_ip(request: Request) -> str:
    forwarded = str(request.META.get("HTTP_X_FORWARDED_FOR", "") or "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return str(request.META.get("REMOTE_ADDR", "") or "")


def _rate_limit_ok(ip_hash: str) -> bool:
    """30 req/min/IP (janela fixa). True se permitido."""
    if not ip_hash:
        return True
    cache = caches["ratelimit"]
    chave = f"orc:pub:ip:{ip_hash}"
    cache.add(chave, 0, _JANELA_SEG)
    try:
        contagem = cache.incr(chave)
    except ValueError:
        cache.set(chave, 1, _JANELA_SEG)
        contagem = 1
    return contagem <= _LIMITE_REQ_MIN


def _resposta_429() -> Response:
    resp = Response(
        {"codigo": "rate_limit_excedido", "detalhe": "muitas requisicoes — tente em instantes."},
        status=status.HTTP_429_TOO_MANY_REQUESTS,
    )
    resp["Retry-After"] = str(_JANELA_SEG)
    return resp


def _resposta_404() -> Response:
    """404 indistinguível (token inválido/expirado/revogado — não vaza existência)."""
    return Response(
        {"codigo": "token_invalido_ou_expirado", "detalhe": "link nao encontrado."},
        status=status.HTTP_404_NOT_FOUND,
    )


def _link_valido(link: LinkPublico | None, agora: datetime) -> bool:
    """True se o link existe, não foi revogado e não expirou (D-ORC-19)."""
    return (
        link is not None
        and link.revogado_em is None
        and link.expira_em is not None
        and link.expira_em > agora
    )


def _coletar_ressalvas(decisao: DecisaoAnaliseCritica) -> list[str]:
    """Achata as ressalvas dos itens avaliados (dedup, ordem preservada)."""
    vistas: dict[str, None] = {}
    for item in decisao.itens_avaliados:
        for r in item.get("ressalvas", []):
            vistas.setdefault(r, None)
    return list(vistas)


def _avaliar_decisao(orcamento_id: UUID, tenant_id: UUID, agora: datetime, repo):
    """Dentro do contexto: carrega versão+itens, resolve perfil, avalia portas e decide.

    Retorna ``(versao, itens, perfil, suspensa, resultados, decisao)`` — perfil/suspensa/
    resultados são repassados ao ``aprovar_orcamento`` (no POST) para garantir que a
    análise gravada seja IDÊNTICA ao pré-check. Levanta ``PerfilIndeterminado`` se o
    perfil for indeterminado (fail-closed — D-ORC-19).
    """
    versao = repo.get_versao_ativa(orcamento_id, tenant_id=tenant_id)
    itens = repo.listar_itens_versao(versao.id, tenant_id=tenant_id) if versao is not None else []
    perfil, suspensa = resolver_perfil_e_suspensao()
    resultados = (
        avaliar_itens_calibracao(itens, tenant_id=tenant_id, data=agora) if perfil != "D" else []
    )
    decisao = decidir_analise_critica(
        perfil=perfil, acreditacao_suspensa=suspensa, resultados=resultados
    )
    return versao, itens, perfil, suspensa, resultados, decisao


# authz-check: skip -- endpoint PUBLICO via PublicEndpoint mixin (token = autorização)
class OrcamentoPublicoView(PublicEndpoint, APIView):
    """GET preview + POST aprovação 1-clique via token opaco (D-ORC-7/19)."""

    authentication_classes: list[Any] = []
    permission_classes: list[Any] = []

    # ----- GET preview --------------------------------------------------

    def get(self, request: Request, token: str) -> Response:
        ip_hash = _hash_ip(_extrair_ip(request))
        if not _rate_limit_ok(ip_hash):
            return _resposta_429()

        agora = datetime.now(UTC)
        repo = DjangoOrcamentoRepository()
        link = repo.get_link_por_token(token)
        if not _link_valido(link, agora):
            return _resposta_404()
        assert link is not None  # _link_valido garante

        with run_in_tenant_context(link.tenant_id):
            orcamento = repo.get_by_id(link.orcamento_id, tenant_id=link.tenant_id)
            if orcamento is None or orcamento.estado != EstadoOrcamento.ENVIADO:
                # Já aprovado/recusado/expirado — não há proposta aberta a exibir.
                return _resposta_404()
            try:
                _versao, itens, _perfil, _suspensa, _resultados, decisao = _avaliar_decisao(
                    link.orcamento_id, link.tenant_id, agora, repo
                )
            except PerfilIndeterminado:
                # Fail-closed: não expõe ressalvas; a aprovação será barrada no POST.
                versao = repo.get_versao_ativa(link.orcamento_id, tenant_id=link.tenant_id)
                itens = (
                    repo.listar_itens_versao(versao.id, tenant_id=link.tenant_id)
                    if versao is not None
                    else []
                )
                ressalvas: list[str] = []
                requer_conf = False
            else:
                com_ressalva = decisao.veredito == VeredictoAnaliseCritica.COM_RESSALVA
                ressalvas = _coletar_ressalvas(decisao) if com_ressalva else []
                requer_conf = decisao.exige_confirmacao_ressalvas

            corpo = serializar_orcamento_publico(
                orcamento, itens, ressalvas=ressalvas, requer_confirmacao_ressalvas=requer_conf
            )
        return Response(corpo, status=status.HTTP_200_OK)

    # ----- POST aprovação 1-clique --------------------------------------

    def post(self, request: Request, token: str) -> Response:
        ip = _extrair_ip(request)
        ip_hash = _hash_ip(ip)
        if not _rate_limit_ok(ip_hash):
            return _resposta_429()

        ser = AprovarPublicoSerializer(data=request.data)
        if not ser.is_valid():
            return Response(ser.errors, status=status.HTTP_422_UNPROCESSABLE_ENTITY)
        dados = ser.validated_data

        agora = datetime.now(UTC)
        repo = DjangoOrcamentoRepository()
        link = repo.get_link_por_token(token)
        if not _link_valido(link, agora):
            return _resposta_404()
        assert link is not None
        tenant_id = link.tenant_id
        user_agent = request.META.get("HTTP_USER_AGENT", "")[:512]

        from src.infrastructure.calibracao.lgpd import derivar_hash_texto_canonicalizado

        try:
            with run_in_tenant_context(tenant_id), transaction.atomic():
                orcamento = repo.get_by_id(link.orcamento_id, tenant_id=tenant_id)
                if orcamento is None or orcamento.estado != EstadoOrcamento.ENVIADO:
                    return _resposta_404()
                versao, _itens, perfil, suspensa, resultados, decisao = _avaliar_decisao(
                    link.orcamento_id, tenant_id, agora, repo
                )
                if versao is None:
                    return _resposta_404()

                # com_ressalva média exige confirmação explícita (cl. 7.1.1-d).
                if decisao.exige_confirmacao_ressalvas and not dados["ressalvas_confirmadas"]:
                    return Response(
                        {
                            "codigo": "ressalvas_nao_confirmadas",
                            "detalhe": "confirme as ressalvas para aprovar (cl. 7.1.1-d).",
                            "ressalvas": _coletar_ressalvas(decisao),
                        },
                        status=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    )

                aprovacao_id = uuid4()
                if decisao.bloqueia:
                    # Reprovada (perfil A): grava análise WORM + evento, NÃO cria Aprovacao.
                    avaliada_por = "SISTEMA/AUTO:reprovada"
                else:
                    # Aprovável: cria Aprovacao WORM (aceite rico) ANTES da análise.
                    avaliada_por = f"SISTEMA/AUTO:{aprovacao_id}"
                    repo.salvar_aprovacao(
                        Aprovacao(
                            id=aprovacao_id,
                            orcamento_id=link.orcamento_id,
                            versao_id=versao.id,
                            tenant_id=tenant_id,
                            aprovado_em=agora,
                            canal=CanalAprovacao.LINK_PUBLICO,
                            nome_aprovador_hash=derivar_hash_texto_canonicalizado(
                                texto=dados["nome_aprovador"], tenant_id=tenant_id
                            ),
                            email_aprovador_hash=derivar_hash_texto_canonicalizado(
                                texto=dados["email_aprovador"], tenant_id=tenant_id
                            ),
                            lgpd_aceite_versao_termo=dados["aceite_versao_termo"],
                            lgpd_aceite_texto_hash=derivar_hash_texto_canonicalizado(
                                texto=dados["aceite_texto"], tenant_id=tenant_id
                            ),
                            ip_hash=_hash_ip(ip),
                            user_agent=user_agent,
                            ressalvas_aceitas=bool(dados["ressalvas_confirmadas"]),
                            aprovado_por=None,
                        )
                    )

                out = uc_aprovar.aprovar_orcamento(
                    uc_aprovar.AprovarOrcamentoInput(
                        tenant_id=tenant_id,
                        orcamento_id=link.orcamento_id,
                        perfil=perfil,
                        acreditacao_suspensa=suspensa,
                        resultados_itens=resultados,
                        avaliada_por=avaliada_por,
                        agora=agora,
                        criada_por_user_id=None,
                    ),
                    repo=repo,
                )
                _publicar_eventos_analise(
                    out, orcamento_id=link.orcamento_id, tenant_id=tenant_id, usuario_id=None
                )

                if not out.aprovado:
                    # Reprovada: WORM + evento gravados; NÃO revoga o link (o cliente
                    # ainda pode visualizar; a reprovação é técnica, não resolúvel por
                    # ele; rate-limit protege contra reenvio abusivo). Responde 422.
                    return Response(
                        {
                            "codigo": "analise_critica_reprovada",
                            "detalhe": "nao foi possivel aprovar este orcamento (analise tecnica).",
                        },
                        status=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    )

                # Aprovado: revoga o link (one-shot — não reaprovável) e responde 200.
                repo.revogar_link(link.id, revogado_em=agora, motivo="orcamento aprovado")
                return Response(
                    {
                        "codigo": "aprovado",
                        "estado": out.orcamento.estado.value,
                        "numero": out.orcamento.numero,
                        "veredito": out.veredito.value,
                    },
                    status=status.HTTP_200_OK,
                )
        except PerfilIndeterminado:
            logger.warning(
                "orcamento publico aprovar: perfil indeterminado orcamento=%s", link.orcamento_id
            )
            return Response(
                {"codigo": "perfil_indeterminado", "detalhe": "nao foi possivel aprovar agora."},
                status=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )


orcamento_publico_view = OrcamentoPublicoView.as_view()
