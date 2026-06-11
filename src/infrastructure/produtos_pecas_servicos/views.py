"""ViewSets REST da frente `produtos-pecas-servicos` (Fatia 2 — T-PPS-033).

Actions:
  GET  /api/v1/catalogo/itens/{id}/                       item + versões + composição
  POST /api/v1/catalogo/itens/cadastrar/                  US-CAT-001 (item + v1)
  POST /api/v1/catalogo/itens/{id}/nova-versao/           US-CAT-002 (anti-retroativa)
  POST /api/v1/catalogo/itens/{id}/corrigir-versao/       D-PPS-8 (revoga+recria)
  POST /api/v1/catalogo/itens/{id}/inativar/              US-CAT-005
  POST /api/v1/catalogo/itens/{id}/montar-kit/            US-CAT-003
  GET  /api/v1/catalogo/tabelas/{id}/                     tabela + linhas
  POST /api/v1/catalogo/tabelas/criar/                    D-PPS-3 (eh_padrao única)
  POST /api/v1/catalogo/tabelas/{id}/criar-linha/         ADR-0081 (default sugerido)
  POST /api/v1/catalogo/tabelas/{id}/corrigir-linha/      D-PPS-8 (revoga+recria)
  POST /api/v1/catalogo/tabelas/{id}/encerrar-linha/      one-shot NULL→data
  GET  /api/v1/catalogo/tabelas/preco-vigente/            porta `preco_para_os`

Autorização: RequireAuthz (DEFAULT_PERMISSION_CLASSES) + ACTION_MAP (seed
0006: catalogo.ver/editar/gerenciar_tabela/importar). Idempotency-Key nos POST
mutadores — fingerprint = payload completo + alvo (lição B6); resumo
persistido sem texto livre (lição B9); `_falha` com log (lição B13).

Eventos `Catalogo.*` (ACOES_CATALOGO) vão SÓ na cadeia hash (outbox=False —
D-PPS-9). LGPD (ADV-PPS-01/02): payload leva `criado_por_id_hash` (HMAC-tenant)
e `descricao`/`motivo` HASHIFICADOS (ADR-0029 — texto livre é PII acidental
ineliminável em WORM); o nome do item vai em claro sob a chave `nome_item`
(nome de ITEM não é pessoa; a chave `nome` da denylist do sanitizador é pra
nome de gente — colisão de chave redigiria à toa).

# authz-check: skip -- RequireAuthz global resolve via ACTION_MAP (header)
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from django.db import DataError, IntegrityError, transaction
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound
from rest_framework.request import Request
from rest_framework.response import Response

from src.application.produtos_pecas_servicos import importacao as uc_importacao
from src.application.produtos_pecas_servicos import item as uc_item
from src.application.produtos_pecas_servicos import tabela as uc_tabela
from src.domain.produtos_pecas_servicos.entities import (
    ItemCatalogo,
    ItemCatalogoVersao,
    KitComposicao,
    LinhaImportacaoCatalogo,
    LinhaTabelaPreco,
    PrecoResolvido,
    TabelaPreco,
)
from src.domain.produtos_pecas_servicos.enums import TipoItem
from src.domain.produtos_pecas_servicos.erros import (
    CodigoDuplicadoError,
    ItemInativoError,
    KitComCicloError,
    PrecoTabelaAusenteError,
    TabelaPadraoDuplicadaError,
    VersaoRetroativaError,
)
from src.domain.produtos_pecas_servicos.extracao_csv import (
    ErroLayoutCsvError,
    parsear_linhas_catalogo,
)
from src.infrastructure.calibracao.lgpd import (
    derivar_hash_texto_canonicalizado,
    derivar_user_id_hash,
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
from src.infrastructure.produtos_pecas_servicos import query_service
from src.infrastructure.produtos_pecas_servicos.repositories import (
    DjangoImportacaoCatalogoRepository,
    DjangoItemCatalogoRepository,
    DjangoTabelaPrecoRepository,
)
from src.infrastructure.produtos_pecas_servicos.serializers import (
    AceitarLinhaImportacaoSerializer,
    CadastrarItemSerializer,
    CorrigirLinhaSerializer,
    CorrigirVersaoSerializer,
    CriarLinhaSerializer,
    CriarTabelaSerializer,
    EncerrarLinhaSerializer,
    ImportarCatalogoSerializer,
    MontarKitSerializer,
    NovaVersaoPrecoSerializer,
    RejeitarLinhaImportacaoSerializer,
)

logger = logging.getLogger(__name__)


def _tenant_ou_none() -> UUID | None:
    return active_tenant_context.get()


def _serializar_item(i: ItemCatalogo) -> dict[str, Any]:
    return {
        "id": str(i.id),
        "codigo_interno": i.codigo_interno,
        "tipo": i.tipo.value,
        "controla_estoque": i.controla_estoque,
        "status": i.status.value,
        "codigo_fabricante": i.codigo_fabricante,
    }


def _serializar_versao(v: ItemCatalogoVersao) -> dict[str, Any]:
    return {
        "id": str(v.id),
        "item_id": str(v.item_id),
        "versao_n": v.versao_n,
        "nome": v.nome,
        "descricao": v.descricao,
        "categoria": v.categoria,
        "unidade_medida": v.unidade_medida,
        "preco_padrao": str(v.preco_padrao.valor),
        "vigencia_inicio": v.vigencia.inicio.isoformat(),
        "vigencia_fim": v.vigencia.fim.isoformat() if v.vigencia.fim else None,
        "revogado_em": (
            v.vigencia.revogado_em.isoformat() if v.vigencia.revogado_em else None
        ),
        "motivo": v.motivo,
    }


def _serializar_composicao(partes: list[KitComposicao]) -> list[dict[str, Any]]:
    return [
        {"item_filho_id": str(p.item_filho_id), "quantidade": str(p.quantidade)}
        for p in partes
    ]


def _serializar_tabela(t: TabelaPreco) -> dict[str, Any]:
    return {
        "id": str(t.id),
        "nome": t.nome,
        "eh_padrao": t.eh_padrao,
        "descricao": t.descricao,
    }


def _serializar_linha(linha: LinhaTabelaPreco) -> dict[str, Any]:
    return {
        "id": str(linha.id),
        "tabela_id": str(linha.tabela_id),
        "item_id": str(linha.item_id),
        "preco": str(linha.preco.valor),
        "origem_sugestao": linha.origem_sugestao.value,
        "vigencia_inicio": linha.vigencia.inicio.isoformat(),
        "vigencia_fim": linha.vigencia.fim.isoformat() if linha.vigencia.fim else None,
        "revogado_em": (
            linha.vigencia.revogado_em.isoformat() if linha.vigencia.revogado_em else None
        ),
    }


def _serializar_preco_resolvido(p: PrecoResolvido) -> dict[str, Any]:
    """Contrato ADR-0081 §4 COMPLETO — caller persiste as refs junto do valor."""
    return {
        "item_id": str(p.item_id),
        "item_versao_n": p.item_versao_n,
        "linha_tabela_id": str(p.linha_tabela_id),
        "tabela_id": str(p.tabela_id),
        "preco": str(p.preco.valor),
        "data_referencia": p.data_referencia.isoformat(),
        "origem_preco": p.origem_preco.value,
        "composicao_resolvida": [
            {
                "item_filho_id": str(c.item_filho_id),
                "quantidade": str(c.quantidade),
                "versao_n": c.versao_n,
                "preco_unitario": str(c.preco_unitario.valor),
            }
            for c in p.composicao_resolvida
        ],
    }


def _hash_texto_ou_none(texto: str, tenant_id: UUID) -> str | None:
    """ADV-PPS-02: texto livre NUNCA cru em evento WORM (ADR-0029)."""
    if not texto:
        return None
    return derivar_hash_texto_canonicalizado(texto=texto, tenant_id=tenant_id)


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


def _publicar_evento_catalogo(
    *,
    acao: str,
    payload: dict[str, Any],
    causation_id: UUID,
    tenant_id: UUID,
    usuario_id: UUID,
    resource_summary: str,
) -> None:
    """Evento `Catalogo.*` na cadeia hash central (outbox=False — D-PPS-9;
    promoção a outbox é GATE-PPS-OUTBOX-ESTOQUE). Payload sanitizado pelo
    helper. Import local (molde fiscal/configuracoes)."""
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
        "catalogo evento WORM registrado na transacao",
        extra={
            "tenant_id": str(tenant_id),
            "acao": acao,
            "correlation_id": str(causation_id),
        },
    )


class _CatalogoViewSetBase(viewsets.ViewSet):
    """Base: ACTION_MAP authz + helpers comuns (molde configuracoes_sistema)."""

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
        # B13: erro de domínio 4xx deixa rastro no servidor (processor F-C2
        # injeta correlation_id/tenant_id/usuario_id — OBS-002).
        logger.warning(
            "catalogo acao recusada",
            extra={
                "chave_id": str(chave_id),
                "http_status": http_status,
                "erro": type(exc).__name__,
                "detalhe": str(exc),
            },
        )
        falhar_chave(chave_id=chave_id, tenant_id=tenant_id, response_status=http_status)
        if isinstance(exc, IntegrityError | DataError):
            # P9 SEG-B3: nunca vazar detail do PG (constraint/valores) no corpo.
            body = {
                "erro": "conflito de unicidade/vigencia ou dado fora do limite — operação não aplicada",
                "codigo": "CONFLITO" if isinstance(exc, IntegrityError) else "DADO_INVALIDO",
            }
        else:
            body = {"erro": str(exc)}
            codigo = getattr(exc, "reason", None)
            if codigo:
                body["codigo"] = codigo
        return Response(body, status=http_status)

    def _falha_404(self, chave_id: UUID, tenant_id: UUID, exc: Exception) -> Response:
        logger.warning(
            "catalogo alvo inexistente",
            extra={"chave_id": str(chave_id), "erro": type(exc).__name__},
        )
        falhar_chave(
            chave_id=chave_id, tenant_id=tenant_id, response_status=status.HTTP_404_NOT_FOUND
        )
        raise NotFound(str(exc)) from exc

    @staticmethod
    def _contexto() -> tuple[UUID | None, UUID]:
        return _tenant_ou_none(), usuario_id_context.get() or UUID(int=0)


# authz-check: skip -- RequireAuthz global resolve via ACTION_MAP (header)
class ItemCatalogoViewSet(_CatalogoViewSetBase):
    """Catálogo do tenant — item + versões de lista imutáveis (US-CAT-001..005)."""

    ACTION_MAP = {
        "retrieve": "catalogo.ver",
        "cadastrar": "catalogo.editar",
        "nova_versao": "catalogo.editar",
        "corrigir_versao": "catalogo.editar",
        "inativar": "catalogo.editar",
        "montar_kit": "catalogo.editar",
    }

    def retrieve(self, request: Request, pk: str | None = None) -> Response:
        tenant_id = _tenant_ou_none()
        if tenant_id is None:
            return Response({"erro": "tenant ausente"}, status=status.HTTP_403_FORBIDDEN)
        item_id = self._uuid_ou_404(pk)
        repo = DjangoItemCatalogoRepository()
        item = repo.obter(tenant_id=tenant_id, item_id=item_id)
        if item is None:
            raise NotFound(f"item {pk} não encontrado")
        versoes = repo.listar_versoes(tenant_id=tenant_id, item_id=item_id)
        body = _serializar_item(item)
        body["versoes"] = [_serializar_versao(v) for v in versoes]
        if item.tipo == TipoItem.KIT:
            body["composicao"] = _serializar_composicao(
                repo.listar_composicao(tenant_id=tenant_id, kit_item_id=item_id)
            )
        return Response(body)

    @action(detail=False, methods=["post"], url_path="cadastrar")
    def cadastrar(self, request: Request) -> Response:
        """POST — AC-CAT-001-1/2 (item + v1; código dup 409). # idempotency-key: required"""
        s = CadastrarItemSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        d = s.validated_data
        tenant_id, usuario_id = self._contexto()
        if tenant_id is None:
            return Response({"erro": "tenant ausente"}, status=status.HTTP_403_FORBIDDEN)

        novo, resp = _aplicar_idempotencia(
            request,
            tenant_id=tenant_id,
            usuario_id=usuario_id,
            endpoint="catalogo.cadastrar_item",
            # Fingerprint = payload COMPLETO (B6).
            payload_fingerprint={
                **{k: v for k, v in d.items() if k != "preco_padrao"},
                "preco_padrao": str(d["preco_padrao"]),
                "vigencia_inicio": (
                    d["vigencia_inicio"].isoformat() if d["vigencia_inicio"] else None
                ),
            },
        )
        if resp is not None:
            return resp
        assert novo is not None and novo.chave_id is not None
        chave_id = novo.chave_id

        try:
            inp = uc_item.CadastrarItemInput(
                tenant_id=tenant_id,
                codigo_interno=d["codigo_interno"],
                tipo=TipoItem(d["tipo"]),
                nome=d["nome"],
                unidade_medida=d["unidade_medida"],
                preco_padrao=d["preco_padrao"],
                criado_por=usuario_id,
                agora=datetime.now(UTC),
                vigencia_inicio=d["vigencia_inicio"],
                controla_estoque=d["controla_estoque"],
                codigo_fabricante=d["codigo_fabricante"],
                descricao=d["descricao"],
                categoria=d["categoria"],
                motivo=d["motivo"],
            )
            with transaction.atomic():
                out = uc_item.cadastrar_item(inp, repo=DjangoItemCatalogoRepository())
                _publicar_evento_catalogo(
                    acao="Catalogo.ItemCadastrado",
                    payload={
                        "item_id": str(out.item.id),
                        "codigo_interno": out.item.codigo_interno,
                        "tipo": out.item.tipo.value,
                        "controla_estoque": out.item.controla_estoque,
                        "nome_item": out.versao.nome,
                        "versao_n": out.versao.versao_n,
                        "preco_padrao": str(out.versao.preco_padrao.valor),
                        "vigencia_inicio": out.versao.vigencia.inicio.isoformat(),
                        "criado_por_id_hash": derivar_user_id_hash(
                            usuario_id=usuario_id, tenant_id=tenant_id
                        ),
                        "descricao_hash": _hash_texto_ou_none(out.versao.descricao, tenant_id),
                    },
                    causation_id=chave_id,
                    tenant_id=tenant_id,
                    usuario_id=usuario_id,
                    resource_summary=f"item {out.item.codigo_interno} cadastrado",
                )
        except CodigoDuplicadoError as exc:
            return self._falha(chave_id, tenant_id, exc, status.HTTP_409_CONFLICT)
        except VersaoRetroativaError as exc:
            return self._falha(chave_id, tenant_id, exc, status.HTTP_422_UNPROCESSABLE_ENTITY)
        except DataError as exc:
            # P9 SEG-M1: input excede coluna — 400 com chave liberada, nunca 500.
            return self._falha(chave_id, tenant_id, exc, status.HTTP_400_BAD_REQUEST)
        except IntegrityError as exc:
            # corrida no UNIQUE codigo_interno — a verdade no banco
            return self._falha(chave_id, tenant_id, exc, status.HTTP_409_CONFLICT)
        except ValueError as exc:
            return self._falha(chave_id, tenant_id, exc, status.HTTP_400_BAD_REQUEST)

        body = _serializar_item(out.item)
        body["versao"] = _serializar_versao(out.versao)
        concluir_chave(
            chave_id=chave_id,
            tenant_id=tenant_id,
            response_status=status.HTTP_201_CREATED,
            # B9: resumo persistido sem texto livre.
            response_body_resumo={
                "item_id": str(out.item.id),
                "codigo_interno": out.item.codigo_interno,
                "versao_n": out.versao.versao_n,
            },
        )
        return Response(body, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"], url_path="nova-versao")
    def nova_versao(self, request: Request, pk: str | None = None) -> Response:
        """POST — AC-CAT-002-1/2 + INV-PPS-PRECO-NAO-RETROATIVO. # idempotency-key: required"""
        s = NovaVersaoPrecoSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        d = s.validated_data
        tenant_id, usuario_id = self._contexto()
        if tenant_id is None:
            return Response({"erro": "tenant ausente"}, status=status.HTTP_403_FORBIDDEN)
        item_id = self._uuid_ou_404(pk)

        novo, resp = _aplicar_idempotencia(
            request,
            tenant_id=tenant_id,
            usuario_id=usuario_id,
            endpoint="catalogo.nova_versao_preco",
            payload_fingerprint={
                "item_id": str(item_id),
                "preco_padrao": str(d["preco_padrao"]),
                "vigencia_inicio": (
                    d["vigencia_inicio"].isoformat() if d["vigencia_inicio"] else None
                ),
                "nome": d["nome"],
                "unidade_medida": d["unidade_medida"],
                "descricao": d["descricao"],
                "categoria": d["categoria"],
                "motivo": d["motivo"],
            },
        )
        if resp is not None:
            return resp
        assert novo is not None and novo.chave_id is not None
        chave_id = novo.chave_id

        try:
            inp = uc_item.NovaVersaoPrecoInput(
                tenant_id=tenant_id,
                item_id=item_id,
                preco_padrao=d["preco_padrao"],
                criado_por=usuario_id,
                agora=datetime.now(UTC),
                vigencia_inicio=d["vigencia_inicio"],
                nome=d["nome"],
                unidade_medida=d["unidade_medida"],
                descricao=d["descricao"],
                categoria=d["categoria"],
                motivo=d["motivo"],
            )
            with transaction.atomic():
                out = uc_item.nova_versao_preco(inp, repo=DjangoItemCatalogoRepository())
                _publicar_evento_catalogo(
                    acao="Catalogo.PrecoAlterado",
                    payload={
                        "item_id": str(item_id),
                        "versao_id": str(out.versao.id),
                        "versao_n": out.versao.versao_n,
                        "preco_padrao": str(out.versao.preco_padrao.valor),
                        "vigencia_inicio": out.versao.vigencia.inicio.isoformat(),
                        "versao_encerrada_id": (
                            str(out.versao_encerrada_id) if out.versao_encerrada_id else None
                        ),
                        "correcao": False,
                        "criado_por_id_hash": derivar_user_id_hash(
                            usuario_id=usuario_id, tenant_id=tenant_id
                        ),
                        "motivo_hash": _hash_texto_ou_none(out.versao.motivo, tenant_id),
                    },
                    causation_id=chave_id,
                    tenant_id=tenant_id,
                    usuario_id=usuario_id,
                    resource_summary=f"item {item_id} preco v{out.versao.versao_n}",
                )
        except uc_item.ItemAusenteError as exc:
            return self._falha_404(chave_id, tenant_id, exc)
        except uc_item.VersaoAusenteError as exc:
            return self._falha(chave_id, tenant_id, exc, status.HTTP_422_UNPROCESSABLE_ENTITY)
        except (VersaoRetroativaError, ItemInativoError) as exc:
            return self._falha(chave_id, tenant_id, exc, status.HTTP_422_UNPROCESSABLE_ENTITY)
        except DataError as exc:
            # P9 SEG-M1: input excede coluna — 400 com chave liberada, nunca 500.
            return self._falha(chave_id, tenant_id, exc, status.HTTP_400_BAD_REQUEST)
        except IntegrityError as exc:
            # exclusion 0004 (a verdade) — colisão de janela que escapou
            return self._falha(chave_id, tenant_id, exc, status.HTTP_422_UNPROCESSABLE_ENTITY)
        except RuntimeError as exc:
            return self._falha(chave_id, tenant_id, exc, status.HTTP_409_CONFLICT)
        except ValueError as exc:
            return self._falha(chave_id, tenant_id, exc, status.HTTP_400_BAD_REQUEST)

        body = _serializar_versao(out.versao)
        body["versao_encerrada_id"] = (
            str(out.versao_encerrada_id) if out.versao_encerrada_id else None
        )
        concluir_chave(
            chave_id=chave_id,
            tenant_id=tenant_id,
            response_status=status.HTTP_201_CREATED,
            response_body_resumo={
                "item_id": str(item_id),
                "versao_id": str(out.versao.id),
                "versao_n": out.versao.versao_n,
            },
        )
        return Response(body, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"], url_path="corrigir-versao")
    def corrigir_versao(self, request: Request, pk: str | None = None) -> Response:
        """POST — D-PPS-8 (revoga+recria na MESMA janela). # idempotency-key: required"""
        s = CorrigirVersaoSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        d = s.validated_data
        tenant_id, usuario_id = self._contexto()
        if tenant_id is None:
            return Response({"erro": "tenant ausente"}, status=status.HTTP_403_FORBIDDEN)
        item_id = self._uuid_ou_404(pk)

        novo, resp = _aplicar_idempotencia(
            request,
            tenant_id=tenant_id,
            usuario_id=usuario_id,
            endpoint="catalogo.corrigir_versao",
            payload_fingerprint={
                "item_id": str(item_id),
                "versao_id": str(d["versao_id"]),
                "motivo": d["motivo"],
                "preco_padrao": str(d["preco_padrao"]) if d["preco_padrao"] else None,
                "nome": d["nome"],
                "unidade_medida": d["unidade_medida"],
                "descricao": d["descricao"],
                "categoria": d["categoria"],
            },
        )
        if resp is not None:
            return resp
        assert novo is not None and novo.chave_id is not None
        chave_id = novo.chave_id

        try:
            inp = uc_item.CorrigirVersaoInput(
                tenant_id=tenant_id,
                item_id=item_id,
                versao_id=d["versao_id"],
                motivo=d["motivo"],
                criado_por=usuario_id,
                preco_padrao=d["preco_padrao"],
                nome=d["nome"],
                unidade_medida=d["unidade_medida"],
                descricao=d["descricao"],
                categoria=d["categoria"],
            )
            with transaction.atomic():
                out = uc_item.corrigir_versao(inp, repo=DjangoItemCatalogoRepository())
                _publicar_evento_catalogo(
                    acao="Catalogo.PrecoAlterado",
                    payload={
                        "item_id": str(item_id),
                        "versao_id": str(out.versao.id),
                        "versao_n": out.versao.versao_n,
                        "preco_padrao": str(out.versao.preco_padrao.valor),
                        "vigencia_inicio": out.versao.vigencia.inicio.isoformat(),
                        "versao_revogada_id": str(out.versao_revogada_id),
                        "correcao": True,
                        "criado_por_id_hash": derivar_user_id_hash(
                            usuario_id=usuario_id, tenant_id=tenant_id
                        ),
                        "motivo_hash": _hash_texto_ou_none(d["motivo"], tenant_id),
                    },
                    causation_id=chave_id,
                    tenant_id=tenant_id,
                    usuario_id=usuario_id,
                    resource_summary=f"item {item_id} versao corrigida",
                )
        except uc_item.ItemAusenteError as exc:
            return self._falha_404(chave_id, tenant_id, exc)
        except uc_item.VersaoAusenteError as exc:
            return self._falha_404(chave_id, tenant_id, exc)
        except DataError as exc:
            # P9 SEG-M1: input excede coluna — 400 com chave liberada, nunca 500.
            return self._falha(chave_id, tenant_id, exc, status.HTTP_400_BAD_REQUEST)
        except IntegrityError as exc:
            return self._falha(chave_id, tenant_id, exc, status.HTTP_422_UNPROCESSABLE_ENTITY)
        except RuntimeError as exc:
            return self._falha(chave_id, tenant_id, exc, status.HTTP_409_CONFLICT)
        except ValueError as exc:
            return self._falha(chave_id, tenant_id, exc, status.HTTP_400_BAD_REQUEST)

        body = _serializar_versao(out.versao)
        body["versao_revogada_id"] = str(out.versao_revogada_id)
        concluir_chave(
            chave_id=chave_id,
            tenant_id=tenant_id,
            response_status=status.HTTP_201_CREATED,
            response_body_resumo={
                "item_id": str(item_id),
                "versao_id": str(out.versao.id),
                "versao_revogada_id": str(out.versao_revogada_id),
            },
        )
        return Response(body, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"], url_path="inativar")
    def inativar(self, request: Request, pk: str | None = None) -> Response:
        """POST — AC-CAT-005-1 (ADR-0031). # idempotency-key: required"""
        tenant_id, usuario_id = self._contexto()
        if tenant_id is None:
            return Response({"erro": "tenant ausente"}, status=status.HTTP_403_FORBIDDEN)
        item_id = self._uuid_ou_404(pk)

        novo, resp = _aplicar_idempotencia(
            request,
            tenant_id=tenant_id,
            usuario_id=usuario_id,
            endpoint="catalogo.inativar_item",
            payload_fingerprint={"item_id": str(item_id)},
        )
        if resp is not None:
            return resp
        assert novo is not None and novo.chave_id is not None
        chave_id = novo.chave_id

        try:
            with transaction.atomic():
                item = uc_item.inativar_item(
                    uc_item.InativarItemInput(tenant_id=tenant_id, item_id=item_id),
                    repo=DjangoItemCatalogoRepository(),
                )
                _publicar_evento_catalogo(
                    acao="Catalogo.ItemInativado",
                    payload={
                        "item_id": str(item.id),
                        "codigo_interno": item.codigo_interno,
                        "criado_por_id_hash": derivar_user_id_hash(
                            usuario_id=usuario_id, tenant_id=tenant_id
                        ),
                    },
                    causation_id=chave_id,
                    tenant_id=tenant_id,
                    usuario_id=usuario_id,
                    resource_summary=f"item {item.codigo_interno} inativado",
                )
        except uc_item.ItemAusenteError as exc:
            return self._falha_404(chave_id, tenant_id, exc)
        except ItemInativoError as exc:
            return self._falha(chave_id, tenant_id, exc, status.HTTP_422_UNPROCESSABLE_ENTITY)
        except ValueError as exc:
            return self._falha(chave_id, tenant_id, exc, status.HTTP_400_BAD_REQUEST)

        body = _serializar_item(item)
        concluir_chave(
            chave_id=chave_id,
            tenant_id=tenant_id,
            response_status=status.HTTP_200_OK,
            response_body_resumo={"item_id": str(item.id), "status": item.status.value},
        )
        return Response(body, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"], url_path="montar-kit")
    def montar_kit(self, request: Request, pk: str | None = None) -> Response:
        """POST — US-CAT-003 (INV-PPS-KIT-SEM-CICLO). # idempotency-key: required"""
        s = MontarKitSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        d = s.validated_data
        tenant_id, usuario_id = self._contexto()
        if tenant_id is None:
            return Response({"erro": "tenant ausente"}, status=status.HTTP_403_FORBIDDEN)
        kit_id = self._uuid_ou_404(pk)
        componentes = tuple(
            (c["item_filho_id"], c["quantidade"]) for c in d["componentes"]
        )

        novo, resp = _aplicar_idempotencia(
            request,
            tenant_id=tenant_id,
            usuario_id=usuario_id,
            endpoint="catalogo.montar_kit",
            payload_fingerprint={
                "kit_item_id": str(kit_id),
                "componentes": [
                    {"item_filho_id": str(f), "quantidade": str(q)} for f, q in componentes
                ],
            },
        )
        if resp is not None:
            return resp
        assert novo is not None and novo.chave_id is not None
        chave_id = novo.chave_id

        try:
            with transaction.atomic():
                composicao = uc_item.montar_kit(
                    uc_item.MontarKitInput(
                        tenant_id=tenant_id, kit_item_id=kit_id, componentes=componentes
                    ),
                    repo=DjangoItemCatalogoRepository(),
                )
                _publicar_evento_catalogo(
                    acao="Catalogo.KitAlterado",
                    payload={
                        "kit_item_id": str(kit_id),
                        "componentes": _serializar_composicao(composicao),
                        "criado_por_id_hash": derivar_user_id_hash(
                            usuario_id=usuario_id, tenant_id=tenant_id
                        ),
                    },
                    causation_id=chave_id,
                    tenant_id=tenant_id,
                    usuario_id=usuario_id,
                    resource_summary=f"kit {kit_id} recomposto",
                )
        except uc_item.ItemAusenteError as exc:
            return self._falha_404(chave_id, tenant_id, exc)
        except (KitComCicloError, ItemInativoError) as exc:
            return self._falha(chave_id, tenant_id, exc, status.HTTP_422_UNPROCESSABLE_ENTITY)
        except DataError as exc:
            return self._falha(chave_id, tenant_id, exc, status.HTTP_400_BAD_REQUEST)
        except IntegrityError as exc:
            # P9 IDEMP-M1: corrida residual no uq_pps_kit_filho (lock 880_403
            # serializa o caminho normal; isto cobre quem burlar o use case).
            return self._falha(chave_id, tenant_id, exc, status.HTTP_409_CONFLICT)
        except ValueError as exc:
            return self._falha(chave_id, tenant_id, exc, status.HTTP_400_BAD_REQUEST)

        body = {
            "kit_item_id": str(kit_id),
            "composicao": _serializar_composicao(composicao),
        }
        concluir_chave(
            chave_id=chave_id,
            tenant_id=tenant_id,
            response_status=status.HTTP_200_OK,
            response_body_resumo={
                "kit_item_id": str(kit_id),
                "n_componentes": len(composicao),
            },
        )
        return Response(body, status=status.HTTP_200_OK)


# authz-check: skip -- RequireAuthz global resolve via ACTION_MAP (header)
class TabelaPrecoViewSet(_CatalogoViewSetBase):
    """Tabela de VENDA vigente — fonte fail-closed da OS (ADR-0081)."""

    ACTION_MAP = {
        "retrieve": "catalogo.ver",
        "preco_vigente": "catalogo.ver",
        "criar": "catalogo.gerenciar_tabela",
        "criar_linha": "catalogo.gerenciar_tabela",
        "corrigir_linha": "catalogo.gerenciar_tabela",
        "encerrar_linha": "catalogo.gerenciar_tabela",
    }

    def retrieve(self, request: Request, pk: str | None = None) -> Response:
        tenant_id = _tenant_ou_none()
        if tenant_id is None:
            return Response({"erro": "tenant ausente"}, status=status.HTTP_403_FORBIDDEN)
        tabela_id = self._uuid_ou_404(pk)
        repo = DjangoTabelaPrecoRepository()
        tabela = repo.obter(tenant_id=tenant_id, tabela_id=tabela_id)
        if tabela is None:
            raise NotFound(f"tabela {pk} não encontrada")
        body = _serializar_tabela(tabela)
        body["linhas"] = [
            _serializar_linha(linha)
            for linha in repo.listar_linhas(tenant_id=tenant_id, tabela_id=tabela_id)
        ]
        return Response(body)

    @action(detail=False, methods=["get"], url_path="preco-vigente")
    def preco_vigente(self, request: Request) -> Response:
        """GET — porta `preco_para_os` exposta (contrato ADR-0081 §4).

        `data_referencia` = data do FATO GERADOR COMERCIAL (contratação) —
        default agora. Fail-closed: 422 `PRECO_TABELA_AUSENTE` sem fallback.
        """
        tenant_id = _tenant_ou_none()
        if tenant_id is None:
            return Response({"erro": "tenant ausente"}, status=status.HTTP_403_FORBIDDEN)
        item_id = self._uuid_ou_404(request.query_params.get("item_id"))
        raw_ref = request.query_params.get("data_referencia")
        if raw_ref:
            try:
                data_referencia = datetime.fromisoformat(raw_ref)
            except ValueError as exc:
                return Response(
                    {"erro": f"data_referencia inválida: {exc}"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if data_referencia.tzinfo is None:
                return Response(
                    {"erro": "data_referencia exige timezone (INV-VIG-004)"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        else:
            data_referencia = datetime.now(UTC)
        try:
            resolvido = query_service.preco_para_os(
                tenant_id=tenant_id, item_id=item_id, data_referencia=data_referencia
            )
        except PrecoTabelaAusenteError as exc:
            logger.warning(
                "catalogo preco fail-closed",
                extra={"item_id": str(item_id), "erro": type(exc).__name__},
            )
            return Response(
                {"erro": str(exc), "codigo": exc.reason},
                status=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )
        except ItemInativoError as exc:
            logger.warning(
                "catalogo preco item inativo",
                extra={"item_id": str(item_id), "erro": type(exc).__name__},
            )
            return Response(
                {"erro": str(exc), "codigo": exc.reason},
                status=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )
        return Response(_serializar_preco_resolvido(resolvido))

    @action(detail=False, methods=["post"], url_path="criar")
    def criar(self, request: Request) -> Response:
        """POST — D-PPS-3 (2ª padrão → 422). # idempotency-key: required"""
        s = CriarTabelaSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        d = s.validated_data
        tenant_id, usuario_id = self._contexto()
        if tenant_id is None:
            return Response({"erro": "tenant ausente"}, status=status.HTTP_403_FORBIDDEN)

        novo, resp = _aplicar_idempotencia(
            request,
            tenant_id=tenant_id,
            usuario_id=usuario_id,
            endpoint="catalogo.criar_tabela",
            payload_fingerprint=dict(d),
        )
        if resp is not None:
            return resp
        assert novo is not None and novo.chave_id is not None
        chave_id = novo.chave_id

        try:
            with transaction.atomic():
                tabela = uc_tabela.criar_tabela(
                    uc_tabela.CriarTabelaInput(
                        tenant_id=tenant_id,
                        nome=d["nome"],
                        eh_padrao=d["eh_padrao"],
                        descricao=d["descricao"],
                    ),
                    repo=DjangoTabelaPrecoRepository(),
                )
                _publicar_evento_catalogo(
                    acao="Catalogo.TabelaCriada",
                    payload={
                        "tabela_id": str(tabela.id),
                        "nome_tabela_hash": _hash_texto_ou_none(tabela.nome, tenant_id),
                        "eh_padrao": tabela.eh_padrao,
                        "criado_por_id_hash": derivar_user_id_hash(
                            usuario_id=usuario_id, tenant_id=tenant_id
                        ),
                    },
                    causation_id=chave_id,
                    tenant_id=tenant_id,
                    usuario_id=usuario_id,
                    resource_summary=f"tabela {tabela.id} criada",
                )
        except TabelaPadraoDuplicadaError as exc:
            return self._falha(chave_id, tenant_id, exc, status.HTTP_422_UNPROCESSABLE_ENTITY)
        except DataError as exc:
            # P9 SEG-M1: input excede coluna — 400 com chave liberada, nunca 500.
            return self._falha(chave_id, tenant_id, exc, status.HTTP_400_BAD_REQUEST)
        except IntegrityError as exc:
            # UNIQUE parcial eh_padrao (a verdade) — corrida que escapou
            return self._falha(chave_id, tenant_id, exc, status.HTTP_422_UNPROCESSABLE_ENTITY)
        except ValueError as exc:
            return self._falha(chave_id, tenant_id, exc, status.HTTP_400_BAD_REQUEST)

        body = _serializar_tabela(tabela)
        concluir_chave(
            chave_id=chave_id,
            tenant_id=tenant_id,
            response_status=status.HTTP_201_CREATED,
            response_body_resumo={"tabela_id": str(tabela.id), "eh_padrao": tabela.eh_padrao},
        )
        return Response(body, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"], url_path="criar-linha")
    def criar_linha(self, request: Request, pk: str | None = None) -> Response:
        """POST — ADR-0081 (preço ausente = default SUGERIDO). # idempotency-key: required"""
        s = CriarLinhaSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        d = s.validated_data
        tenant_id, usuario_id = self._contexto()
        if tenant_id is None:
            return Response({"erro": "tenant ausente"}, status=status.HTTP_403_FORBIDDEN)
        tabela_id = self._uuid_ou_404(pk)

        novo, resp = _aplicar_idempotencia(
            request,
            tenant_id=tenant_id,
            usuario_id=usuario_id,
            endpoint="catalogo.criar_linha",
            payload_fingerprint={
                "tabela_id": str(tabela_id),
                "item_id": str(d["item_id"]),
                "preco": str(d["preco"]) if d["preco"] is not None else None,
                "vigencia_inicio": (
                    d["vigencia_inicio"].isoformat() if d["vigencia_inicio"] else None
                ),
                "vigencia_fim": d["vigencia_fim"].isoformat() if d["vigencia_fim"] else None,
            },
        )
        if resp is not None:
            return resp
        assert novo is not None and novo.chave_id is not None
        chave_id = novo.chave_id

        try:
            with transaction.atomic():
                out = uc_tabela.criar_linha(
                    uc_tabela.CriarLinhaInput(
                        tenant_id=tenant_id,
                        tabela_id=tabela_id,
                        item_id=d["item_id"],
                        criado_por=usuario_id,
                        agora=datetime.now(UTC),
                        preco=d["preco"],
                        vigencia_inicio=d["vigencia_inicio"],
                        vigencia_fim=d["vigencia_fim"],
                    ),
                    tabela_repo=DjangoTabelaPrecoRepository(),
                    item_repo=DjangoItemCatalogoRepository(),
                )
                _publicar_evento_catalogo(
                    acao="Catalogo.LinhaPrecoCriada",
                    payload={
                        "linha_id": str(out.linha.id),
                        "tabela_id": str(out.linha.tabela_id),
                        "item_id": str(out.linha.item_id),
                        "preco": str(out.linha.preco.valor),
                        "origem_sugestao": out.linha.origem_sugestao.value,
                        "vigencia_inicio": out.linha.vigencia.inicio.isoformat(),
                        "criado_por_id_hash": derivar_user_id_hash(
                            usuario_id=usuario_id, tenant_id=tenant_id
                        ),
                    },
                    causation_id=chave_id,
                    tenant_id=tenant_id,
                    usuario_id=usuario_id,
                    resource_summary=f"linha {out.linha.id} criada",
                )
        except (uc_tabela.TabelaAusenteError, uc_item.ItemAusenteError) as exc:
            return self._falha_404(chave_id, tenant_id, exc)
        except (
            ItemInativoError,
            uc_tabela.LinhaSobrepostaError,
            uc_tabela.SugestaoPrecoIndisponivelError,
        ) as exc:
            return self._falha(chave_id, tenant_id, exc, status.HTTP_422_UNPROCESSABLE_ENTITY)
        except DataError as exc:
            # P9 SEG-M1: input excede coluna — 400 com chave liberada, nunca 500.
            return self._falha(chave_id, tenant_id, exc, status.HTTP_400_BAD_REQUEST)
        except IntegrityError as exc:
            # exclusion 0004 / CHECK preco>0 (a verdade no banco)
            return self._falha(chave_id, tenant_id, exc, status.HTTP_422_UNPROCESSABLE_ENTITY)
        except ValueError as exc:
            return self._falha(chave_id, tenant_id, exc, status.HTTP_400_BAD_REQUEST)

        body = _serializar_linha(out.linha)
        concluir_chave(
            chave_id=chave_id,
            tenant_id=tenant_id,
            response_status=status.HTTP_201_CREATED,
            response_body_resumo={
                "linha_id": str(out.linha.id),
                "item_id": str(out.linha.item_id),
                "origem_sugestao": out.linha.origem_sugestao.value,
            },
        )
        return Response(body, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"], url_path="corrigir-linha")
    def corrigir_linha(self, request: Request, pk: str | None = None) -> Response:
        """POST — D-PPS-8 (revoga+recria atômico). # idempotency-key: required"""
        s = CorrigirLinhaSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        d = s.validated_data
        tenant_id, usuario_id = self._contexto()
        if tenant_id is None:
            return Response({"erro": "tenant ausente"}, status=status.HTTP_403_FORBIDDEN)
        tabela_id = self._uuid_ou_404(pk)

        novo, resp = _aplicar_idempotencia(
            request,
            tenant_id=tenant_id,
            usuario_id=usuario_id,
            endpoint="catalogo.corrigir_linha",
            payload_fingerprint={
                "tabela_id": str(tabela_id),
                "linha_id": str(d["linha_id"]),
                "preco": str(d["preco"]),
                "motivo": d["motivo"],
            },
        )
        if resp is not None:
            return resp
        assert novo is not None and novo.chave_id is not None
        chave_id = novo.chave_id

        try:
            with transaction.atomic():
                out = uc_tabela.corrigir_linha(
                    uc_tabela.CorrigirLinhaInput(
                        tenant_id=tenant_id,
                        tabela_id=tabela_id,
                        linha_id=d["linha_id"],
                        preco=d["preco"],
                        motivo=d["motivo"],
                        criado_por=usuario_id,
                    ),
                    tabela_repo=DjangoTabelaPrecoRepository(),
                )
                _publicar_evento_catalogo(
                    acao="Catalogo.LinhaPrecoCorrigida",
                    payload={
                        "linha_revogada_id": str(out.linha_revogada_id),
                        "linha_id": str(out.linha.id),
                        "tabela_id": str(out.linha.tabela_id),
                        "item_id": str(out.linha.item_id),
                        "preco": str(out.linha.preco.valor),
                        "criado_por_id_hash": derivar_user_id_hash(
                            usuario_id=usuario_id, tenant_id=tenant_id
                        ),
                        "motivo_hash": _hash_texto_ou_none(d["motivo"], tenant_id),
                    },
                    causation_id=chave_id,
                    tenant_id=tenant_id,
                    usuario_id=usuario_id,
                    resource_summary=f"linha {out.linha_revogada_id} corrigida",
                )
        except uc_tabela.LinhaAusenteError as exc:
            return self._falha_404(chave_id, tenant_id, exc)
        except DataError as exc:
            # P9 SEG-M1: input excede coluna — 400 com chave liberada, nunca 500.
            return self._falha(chave_id, tenant_id, exc, status.HTTP_400_BAD_REQUEST)
        except IntegrityError as exc:
            return self._falha(chave_id, tenant_id, exc, status.HTTP_422_UNPROCESSABLE_ENTITY)
        except RuntimeError as exc:
            return self._falha(chave_id, tenant_id, exc, status.HTTP_409_CONFLICT)
        except ValueError as exc:
            return self._falha(chave_id, tenant_id, exc, status.HTTP_400_BAD_REQUEST)

        body = _serializar_linha(out.linha)
        body["linha_revogada_id"] = str(out.linha_revogada_id)
        concluir_chave(
            chave_id=chave_id,
            tenant_id=tenant_id,
            response_status=status.HTTP_201_CREATED,
            response_body_resumo={
                "linha_id": str(out.linha.id),
                "linha_revogada_id": str(out.linha_revogada_id),
            },
        )
        return Response(body, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"], url_path="encerrar-linha")
    def encerrar_linha(self, request: Request, pk: str | None = None) -> Response:
        """POST — one-shot NULL→data. # idempotency-key: required"""
        s = EncerrarLinhaSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        d = s.validated_data
        tenant_id, usuario_id = self._contexto()
        if tenant_id is None:
            return Response({"erro": "tenant ausente"}, status=status.HTTP_403_FORBIDDEN)
        tabela_id = self._uuid_ou_404(pk)

        novo, resp = _aplicar_idempotencia(
            request,
            tenant_id=tenant_id,
            usuario_id=usuario_id,
            endpoint="catalogo.encerrar_linha",
            payload_fingerprint={
                "tabela_id": str(tabela_id),
                "linha_id": str(d["linha_id"]),
                "fim": d["fim"].isoformat(),
            },
        )
        if resp is not None:
            return resp
        assert novo is not None and novo.chave_id is not None
        chave_id = novo.chave_id

        try:
            with transaction.atomic():
                uc_tabela.encerrar_linha(
                    uc_tabela.EncerrarLinhaInput(
                        tenant_id=tenant_id,
                        tabela_id=tabela_id,
                        linha_id=d["linha_id"],
                        fim=d["fim"],
                    ),
                    tabela_repo=DjangoTabelaPrecoRepository(),
                )
                _publicar_evento_catalogo(
                    acao="Catalogo.LinhaPrecoEncerrada",
                    payload={
                        "linha_id": str(d["linha_id"]),
                        "tabela_id": str(tabela_id),
                        "fim": d["fim"].isoformat(),
                        "criado_por_id_hash": derivar_user_id_hash(
                            usuario_id=usuario_id, tenant_id=tenant_id
                        ),
                    },
                    causation_id=chave_id,
                    tenant_id=tenant_id,
                    usuario_id=usuario_id,
                    resource_summary=f"linha {d['linha_id']} encerrada",
                )
        except uc_tabela.LinhaAusenteError as exc:
            return self._falha_404(chave_id, tenant_id, exc)
        except RuntimeError as exc:
            return self._falha(chave_id, tenant_id, exc, status.HTTP_409_CONFLICT)
        except DataError as exc:
            return self._falha(chave_id, tenant_id, exc, status.HTTP_400_BAD_REQUEST)
        except (IntegrityError, ValueError) as exc:
            http = (
                status.HTTP_422_UNPROCESSABLE_ENTITY
                if isinstance(exc, IntegrityError)
                else status.HTTP_400_BAD_REQUEST
            )
            return self._falha(chave_id, tenant_id, exc, http)

        body = {"linha_id": str(d["linha_id"]), "fim": d["fim"].isoformat()}
        concluir_chave(
            chave_id=chave_id,
            tenant_id=tenant_id,
            response_status=status.HTTP_200_OK,
            response_body_resumo=body,
        )
        return Response(body, status=status.HTTP_200_OK)


# authz-check: skip -- RequireAuthz global resolve via ACTION_MAP (header)
class ImportacaoCatalogoViewSet(_CatalogoViewSetBase):
    """Importação CSV em STAGING (US-CAT-004 — INV-PPS-IMPORTACAO-STAGING).

    Importar NUNCA cria item; aceite é POR LINHA (one-shot) e reusa o caminho
    canônico `cadastrar_item`. Leitura física reusa `clientes/csv_io` (UTF-8/
    BOM + sniffer `;`/`,` + limites) e TODAS as células passam por
    `sanitizar_celula_csv` (anti formula-injection) ANTES do staging.
    """

    ACTION_MAP = {
        "retrieve": "catalogo.importar",
        "importar": "catalogo.importar",
        "aceitar_linha": "catalogo.importar",
        "rejeitar_linha": "catalogo.importar",
    }

    def retrieve(self, request: Request, pk: str | None = None) -> Response:
        tenant_id = _tenant_ou_none()
        if tenant_id is None:
            return Response({"erro": "tenant ausente"}, status=status.HTTP_403_FORBIDDEN)
        importacao_id = self._uuid_ou_404(pk)
        repo = DjangoImportacaoCatalogoRepository()
        importacao = repo.obter_importacao(tenant_id=tenant_id, importacao_id=importacao_id)
        if importacao is None:
            raise NotFound(f"importação {pk} não encontrada")
        linhas = repo.listar_linhas(tenant_id=tenant_id, importacao_id=importacao_id)
        return Response(
            {
                "id": str(importacao.id),
                "arquivo_sha256": importacao.arquivo_sha256,
                "total_linhas": importacao.total_linhas,
                "criado_em": importacao.criado_em.isoformat(),
                "linhas": [_serializar_linha_importacao(li) for li in linhas],
            }
        )

    @action(detail=False, methods=["post"], url_path="importar")
    def importar(self, request: Request) -> Response:
        """POST multipart — cria o lote em STAGING. # idempotency-key: required"""
        import contextlib
        import hashlib

        from src.infrastructure.clientes.csv_io import (
            LIMITE_BYTES,
            ErroCsvIo,
            ler_csv_normalizado,
            sanitizar_celula_csv,
        )

        s = ImportarCatalogoSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        upload = s.validated_data["arquivo"]
        tenant_id, usuario_id = self._contexto()
        if tenant_id is None:
            return Response({"erro": "tenant ausente"}, status=status.HTTP_403_FORBIDDEN)

        try:
            tamanho_declarado = getattr(upload, "size", None)
            if tamanho_declarado is not None and tamanho_declarado > LIMITE_BYTES:
                # P9 SEG-B4: rejeita ANTES do read (sem materializar o corpo).
                logger.warning(
                    "catalogo importacao recusada",
                    extra={"codigo": "arquivo_excede_limite", "tamanho_bytes": tamanho_declarado},
                )
                return Response(
                    {"erro": "arquivo_excede_limite", "limite_bytes": LIMITE_BYTES},
                    status=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                )
            arquivo_bytes = upload.read()
            if len(arquivo_bytes) > LIMITE_BYTES:
                logger.warning(
                    "catalogo importacao recusada",
                    extra={"codigo": "arquivo_excede_limite", "tamanho_bytes": len(arquivo_bytes)},
                )
                return Response(
                    {"erro": "arquivo_excede_limite", "limite_bytes": LIMITE_BYTES},
                    status=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                )
            try:
                norm = ler_csv_normalizado(arquivo_bytes)
            except ErroCsvIo as exc:
                logger.warning(
                    "catalogo importacao recusada",
                    extra={"codigo": exc.code, "tamanho_bytes": len(arquivo_bytes)},
                )
                return Response(
                    {"erro": str(exc), "codigo": exc.code},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        finally:
            with contextlib.suppress(Exception):
                upload.close()

        arquivo_sha256 = hashlib.sha256(arquivo_bytes).hexdigest()
        novo, resp = _aplicar_idempotencia(
            request,
            tenant_id=tenant_id,
            usuario_id=usuario_id,
            endpoint="catalogo.importar_csv",
            payload_fingerprint={"arquivo_sha256": arquivo_sha256},
        )
        if resp is not None:
            return resp
        assert novo is not None and novo.chave_id is not None
        chave_id = novo.chave_id

        # Sanitização anti formula-injection ANTES do staging (SEC-CSV-001).
        linhas_sanitizadas = tuple(
            tuple(sanitizar_celula_csv(c) for c in linha) for linha in norm.linhas
        )
        try:
            parseadas = parsear_linhas_catalogo(norm.headers, linhas_sanitizadas)
            inp = uc_importacao.RegistrarImportacaoInput(
                tenant_id=tenant_id,
                arquivo_sha256=arquivo_sha256,
                arquivo_nome_hash=_hash_texto_ou_none(
                    getattr(upload, "name", "") or "", tenant_id
                )
                or "",
                criado_por=usuario_id,
                agora=datetime.now(UTC),
                linhas_parseadas=parseadas,
            )
            with transaction.atomic():
                out = uc_importacao.registrar_importacao(
                    inp, repo=DjangoImportacaoCatalogoRepository()
                )
                _publicar_evento_catalogo(
                    acao="Catalogo.ImportacaoConcluida",
                    payload={
                        "importacao_id": str(out.importacao.id),
                        # Prova PERMANENTE de integridade (ADV-PPS-06) — o
                        # staging expira em 90d; o evento WORM não.
                        "arquivo_sha256": out.importacao.arquivo_sha256,
                        "arquivo_nome_hash": out.importacao.arquivo_nome_hash,
                        "total_linhas": out.importacao.total_linhas,
                        "validadas": out.total_validadas,
                        "rejeitadas": out.total_rejeitadas,
                        "criado_por_id_hash": derivar_user_id_hash(
                            usuario_id=usuario_id, tenant_id=tenant_id
                        ),
                    },
                    causation_id=chave_id,
                    tenant_id=tenant_id,
                    usuario_id=usuario_id,
                    resource_summary=f"importacao {out.importacao.id} em staging",
                )
        except ErroLayoutCsvError as exc:
            return self._falha(chave_id, tenant_id, exc, status.HTTP_400_BAD_REQUEST)
        except ValueError as exc:
            return self._falha(chave_id, tenant_id, exc, status.HTTP_400_BAD_REQUEST)

        body = {
            "id": str(out.importacao.id),
            "arquivo_sha256": out.importacao.arquivo_sha256,
            "total_linhas": out.importacao.total_linhas,
            "validadas": out.total_validadas,
            "rejeitadas": out.total_rejeitadas,
            "linhas": [_serializar_linha_importacao(li) for li in out.linhas],
        }
        concluir_chave(
            chave_id=chave_id,
            tenant_id=tenant_id,
            response_status=status.HTTP_201_CREATED,
            # B9: resumo persistido sem conteúdo de linha (texto livre fica fora).
            response_body_resumo={
                "importacao_id": str(out.importacao.id),
                "arquivo_sha256": out.importacao.arquivo_sha256,
                "validadas": out.total_validadas,
                "rejeitadas": out.total_rejeitadas,
            },
        )
        return Response(body, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"], url_path="aceitar-linha")
    def aceitar_linha(self, request: Request, pk: str | None = None) -> Response:
        """POST — one-shot VALIDADA→ACEITA (reusa cadastrar_item). # idempotency-key: required"""
        s = AceitarLinhaImportacaoSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        d = s.validated_data
        tenant_id, usuario_id = self._contexto()
        if tenant_id is None:
            return Response({"erro": "tenant ausente"}, status=status.HTTP_403_FORBIDDEN)
        importacao_id = self._uuid_ou_404(pk)

        novo, resp = _aplicar_idempotencia(
            request,
            tenant_id=tenant_id,
            usuario_id=usuario_id,
            endpoint="catalogo.aceitar_linha_importacao",
            payload_fingerprint={
                "importacao_id": str(importacao_id),
                "linha_id": str(d["linha_id"]),
            },
        )
        if resp is not None:
            return resp
        assert novo is not None and novo.chave_id is not None
        chave_id = novo.chave_id

        repo = DjangoImportacaoCatalogoRepository()
        try:
            # P9 IDEMP-B2: lookup DENTRO do try — erro inesperado não deixa
            # a chave presa em_processo.
            linha = repo.obter_linha(tenant_id=tenant_id, linha_id=d["linha_id"])
            if linha is None or linha.importacao_id != importacao_id:
                raise uc_importacao.LinhaImportacaoAusenteError(
                    f"linha {d['linha_id']} inexistente no lote {importacao_id}."
                )
            with transaction.atomic():
                out = uc_importacao.aceitar_linha(
                    uc_importacao.AceitarLinhaInput(
                        tenant_id=tenant_id,
                        linha_id=d["linha_id"],
                        criado_por=usuario_id,
                        agora=datetime.now(UTC),
                    ),
                    importacao_repo=repo,
                    item_repo=DjangoItemCatalogoRepository(),
                )
                _publicar_evento_catalogo(
                    acao="Catalogo.ItemCadastrado",
                    payload={
                        "item_id": str(out.item.item.id),
                        "codigo_interno": out.item.item.codigo_interno,
                        "tipo": out.item.item.tipo.value,
                        "controla_estoque": out.item.item.controla_estoque,
                        "nome_item": out.item.versao.nome,
                        "versao_n": out.item.versao.versao_n,
                        "preco_padrao": str(out.item.versao.preco_padrao.valor),
                        "vigencia_inicio": out.item.versao.vigencia.inicio.isoformat(),
                        "origem_importacao_id": str(importacao_id),
                        "criado_por_id_hash": derivar_user_id_hash(
                            usuario_id=usuario_id, tenant_id=tenant_id
                        ),
                        "descricao_hash": _hash_texto_ou_none(
                            out.item.versao.descricao, tenant_id
                        ),
                    },
                    causation_id=chave_id,
                    tenant_id=tenant_id,
                    usuario_id=usuario_id,
                    resource_summary=(
                        f"item {out.item.item.codigo_interno} aceito da importacao"
                    ),
                )
        except uc_importacao.LinhaImportacaoAusenteError as exc:
            return self._falha_404(chave_id, tenant_id, exc)
        except CodigoDuplicadoError as exc:
            # código passou a existir entre upload e aceite — linha fica validada
            return self._falha(chave_id, tenant_id, exc, status.HTTP_409_CONFLICT)
        except DataError as exc:
            # P9 SEG-M1: input excede coluna — 400 com chave liberada, nunca 500.
            return self._falha(chave_id, tenant_id, exc, status.HTTP_400_BAD_REQUEST)
        except IntegrityError as exc:
            return self._falha(chave_id, tenant_id, exc, status.HTTP_409_CONFLICT)
        except RuntimeError as exc:
            return self._falha(chave_id, tenant_id, exc, status.HTTP_409_CONFLICT)
        except ValueError as exc:
            return self._falha(chave_id, tenant_id, exc, status.HTTP_400_BAD_REQUEST)

        body = _serializar_item(out.item.item)
        body["versao"] = _serializar_versao(out.item.versao)
        body["linha_id"] = str(out.linha_id)
        concluir_chave(
            chave_id=chave_id,
            tenant_id=tenant_id,
            response_status=status.HTTP_201_CREATED,
            response_body_resumo={
                "linha_id": str(out.linha_id),
                "item_id": str(out.item.item.id),
                "codigo_interno": out.item.item.codigo_interno,
            },
        )
        return Response(body, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"], url_path="rejeitar-linha")
    def rejeitar_linha(self, request: Request, pk: str | None = None) -> Response:
        """POST — one-shot VALIDADA→REJEITADA. # idempotency-key: required"""
        s = RejeitarLinhaImportacaoSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        d = s.validated_data
        tenant_id, usuario_id = self._contexto()
        if tenant_id is None:
            return Response({"erro": "tenant ausente"}, status=status.HTTP_403_FORBIDDEN)
        importacao_id = self._uuid_ou_404(pk)

        novo, resp = _aplicar_idempotencia(
            request,
            tenant_id=tenant_id,
            usuario_id=usuario_id,
            endpoint="catalogo.rejeitar_linha_importacao",
            payload_fingerprint={
                "importacao_id": str(importacao_id),
                "linha_id": str(d["linha_id"]),
                "motivo": d["motivo"],
            },
        )
        if resp is not None:
            return resp
        assert novo is not None and novo.chave_id is not None
        chave_id = novo.chave_id

        repo = DjangoImportacaoCatalogoRepository()
        try:
            # P9 IDEMP-B2: lookup DENTRO do try — erro inesperado não deixa
            # a chave presa em_processo.
            linha = repo.obter_linha(tenant_id=tenant_id, linha_id=d["linha_id"])
            if linha is None or linha.importacao_id != importacao_id:
                raise uc_importacao.LinhaImportacaoAusenteError(
                    f"linha {d['linha_id']} inexistente no lote {importacao_id}."
                )
            with transaction.atomic():
                uc_importacao.rejeitar_linha(
                    uc_importacao.RejeitarLinhaInput(
                        tenant_id=tenant_id, linha_id=d["linha_id"], motivo=d["motivo"]
                    ),
                    importacao_repo=repo,
                )
                # P9 OBS-M1: rejeição é decisão humana one-shot e o staging
                # expira em 90d — sem evento WORM a decisão sumiria sem rastro.
                _publicar_evento_catalogo(
                    acao="Catalogo.LinhaImportacaoRejeitada",
                    payload={
                        "linha_id": str(d["linha_id"]),
                        "importacao_id": str(importacao_id),
                        "linha_numero": linha.linha_numero,
                        "motivo_hash": _hash_texto_ou_none(d["motivo"], tenant_id),
                        "criado_por_id_hash": derivar_user_id_hash(
                            usuario_id=usuario_id, tenant_id=tenant_id
                        ),
                    },
                    causation_id=chave_id,
                    tenant_id=tenant_id,
                    usuario_id=usuario_id,
                    resource_summary=f"linha {d['linha_id']} rejeitada na conferencia",
                )
        except uc_importacao.LinhaImportacaoAusenteError as exc:
            return self._falha_404(chave_id, tenant_id, exc)
        except RuntimeError as exc:
            return self._falha(chave_id, tenant_id, exc, status.HTTP_409_CONFLICT)
        except ValueError as exc:
            return self._falha(chave_id, tenant_id, exc, status.HTTP_400_BAD_REQUEST)

        body = {"linha_id": str(d["linha_id"]), "status": "rejeitada"}
        concluir_chave(
            chave_id=chave_id,
            tenant_id=tenant_id,
            response_status=status.HTTP_200_OK,
            response_body_resumo=body,
        )
        return Response(body, status=status.HTTP_200_OK)


def _serializar_linha_importacao(li: LinhaImportacaoCatalogo) -> dict[str, Any]:
    return {
        "id": str(li.id),
        "linha_numero": li.linha_numero,
        "status": li.status.value,
        "codigo_interno": li.codigo_interno,
        "tipo": li.tipo,
        "nome": li.nome,
        "unidade_medida": li.unidade_medida,
        "preco_padrao": str(li.preco_padrao) if li.preco_padrao is not None else None,
        "categoria": li.categoria,
        "descricao": li.descricao,
        "codigo_fabricante": li.codigo_fabricante,
        "motivo_rejeicao": li.motivo_rejeicao,
        "item_criado_id": str(li.item_criado_id) if li.item_criado_id else None,
    }
