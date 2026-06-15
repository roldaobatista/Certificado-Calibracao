"""Adapters Django dos Protocols de repositorio do dominio Orcamentos — T-ORC-026.

Implementa `OrcamentoRepository` e `TemplateRepository`
(`src/domain/comercial/orcamentos/repository.py`) sobre Django ORM. A view/use case
injeta estes adapters; o repositorio NAO gerencia transacao (o caller abre o
`transaction.atomic`) e roda dentro de `run_in_tenant_context` (RLS escopa por tenant).

WORM: `salvar_aprovacao` / `salvar_analise_critica` sao INSERT puro (trigger 0003
bloqueia mutacao). `salvar_versao` cria a versao (snapshot={} em rascunho; congela
ao enviar via UPDATE one-shot do snapshot, feito pelo use case — Fatia 2).

Numeracao gap-less (D-ORC-18): o `numero` chega ja resolvido pelo use case via
`SerieDocumento` (`reservar_numero`/`confirmar_numero`) no atomic da criacao — a
constraint `uq_orcamento_numero_tenant` (0004) e a defesa de banco. Integracao do
motor SerieDocumento = Fatia 2 (use case `criar_orcamento`).

Molde: `src/infrastructure/clientes/repositories.py`.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from src.domain.comercial.orcamentos.entities import (
    AnaliseCriticaOrcamento,
    Aprovacao,
    ItemOrcamento,
    LinkPublico,
    Orcamento,
    Template,
    VersaoOrcamento,
)
from src.domain.comercial.orcamentos.enums import EstadoOrcamento
from src.infrastructure.orcamentos import mappers
from src.infrastructure.orcamentos import models as m


class DjangoOrcamentoRepository:
    """Implementa `OrcamentoRepository` Protocol sobre Django ORM."""

    # ----- Orcamento (raiz) -----------------------------------------

    def get_by_id(self, orcamento_id: UUID, *, tenant_id: UUID) -> Orcamento | None:
        obj = m.Orcamento.objects.filter(id=orcamento_id, tenant_id=tenant_id).first()
        return mappers.to_orcamento(obj) if obj is not None else None

    def salvar(self, orcamento: Orcamento) -> Orcamento:
        moeda = orcamento.total_bruto.moeda
        obj, _ = m.Orcamento.objects.update_or_create(
            id=orcamento.id,
            defaults={
                "tenant_id": orcamento.tenant_id,
                "cliente_atual_id": orcamento.cliente_atual_id,
                "cliente_referencia_hash": orcamento.cliente_referencia_hash,
                "cliente_key_id": orcamento.cliente_key_id,
                "numero": orcamento.numero,
                "estado": orcamento.estado.value,
                "validade_inicio": orcamento.validade.inicio,
                "validade_fim": orcamento.validade.fim,
                "moeda": moeda,
                "total_bruto_centavos": orcamento.total_bruto.centavos,
                "descontos_centavos": orcamento.descontos.centavos,
                "impostos_centavos": orcamento.impostos.centavos,
                "liquido_centavos": orcamento.liquido.centavos,
                "comissao_prevista_centavos": orcamento.comissao_prevista.centavos,
                "condicoes_pagamento": mappers.serializar_condicoes(orcamento.condicoes_pagamento),
                "template_id": orcamento.template_id,
                "tabela_preco_id": orcamento.tabela_preco_id,
                "observacoes": orcamento.observacoes or "",
                "responsavel_id": orcamento.responsavel_id,
                "chamado_origem_id": orcamento.chamado_origem_id,
                "criado_por": orcamento.criado_por,
            },
        )
        return mappers.to_orcamento(obj)

    def listar(
        self,
        *,
        tenant_id: UUID,
        estado: EstadoOrcamento | None = None,
        cliente_id: UUID | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> list[Orcamento]:
        qs = m.Orcamento.objects.filter(tenant_id=tenant_id)
        if estado is not None:
            qs = qs.filter(estado=estado.value)
        if cliente_id is not None:
            qs = qs.filter(cliente_atual_id=cliente_id)
        qs = qs.order_by("-criado_em")[offset : offset + limit]
        return [mappers.to_orcamento(o) for o in qs]

    def atualizar_estado(
        self, orcamento_id: UUID, *, tenant_id: UUID, novo_estado: EstadoOrcamento
    ) -> Orcamento:
        m.Orcamento.objects.filter(id=orcamento_id, tenant_id=tenant_id).update(
            estado=novo_estado.value
        )
        obj = m.Orcamento.objects.get(id=orcamento_id, tenant_id=tenant_id)
        return mappers.to_orcamento(obj)

    # ----- Versao ---------------------------------------------------

    def salvar_versao(self, versao: VersaoOrcamento) -> VersaoOrcamento:
        obj = m.VersaoOrcamento.objects.create(
            id=versao.id,
            orcamento_id=versao.orcamento_id,
            tenant_id=versao.tenant_id,
            numero_versao=versao.numero_versao,
            snapshot=versao.snapshot,
            criada_por=versao.criada_por,
            revogado_em=versao.revogado_em,
            motivo_revogacao=versao.motivo_revogacao or "",
        )
        return mappers.to_versao(obj)

    def get_versao_ativa(self, orcamento_id: UUID, *, tenant_id: UUID) -> VersaoOrcamento | None:
        obj = (
            m.VersaoOrcamento.objects.filter(
                orcamento_id=orcamento_id, tenant_id=tenant_id, revogado_em__isnull=True
            )
            .order_by("-numero_versao")
            .first()
        )
        return mappers.to_versao(obj) if obj is not None else None

    def congelar_versao(
        self, versao_id: UUID, *, tenant_id: UUID, snapshot: dict[str, object]
    ) -> VersaoOrcamento:
        # UPDATE one-shot: trigger 0003 permite snapshot '{}' -> conteudo (D-ORC-8).
        m.VersaoOrcamento.objects.filter(id=versao_id, tenant_id=tenant_id).update(
            snapshot=snapshot
        )
        obj = m.VersaoOrcamento.objects.get(id=versao_id, tenant_id=tenant_id)
        return mappers.to_versao(obj)

    # ----- Item -----------------------------------------------------

    def salvar_item(self, item: ItemOrcamento) -> ItemOrcamento:
        obj, _ = m.ItemOrcamento.objects.update_or_create(
            id=item.id,
            defaults={
                "versao_id": item.versao_id,
                "tenant_id": item.tenant_id,
                "catalogo_item_id": item.catalogo_item_id,
                "sequencia": item.sequencia,
                "preco_resolvido": mappers.serializar_preco_resolvido(item.preco_resolvido),
                "moeda": item.preco_final.moeda,
                "preco_final_centavos": item.preco_final.centavos,
                "desconto_pct": item.desconto_pct,
                "desconto_valor_centavos": item.desconto_valor.centavos,
                "quantidade": item.quantidade,
                "total_centavos": item.total.centavos,
                "semaforo": item.semaforo,
                "descricao_snapshot": item.descricao_snapshot,
                "equipamento_id": item.equipamento_id,
                "tipo_atividade_alvo": (
                    item.tipo_atividade_alvo.value if item.tipo_atividade_alvo else ""
                ),
                "tipo_item_comercial": (
                    item.tipo_item_comercial.value if item.tipo_item_comercial else ""
                ),
                "grandeza_solicitada": item.grandeza_solicitada or "",
                "faixa_solicitada_min": item.faixa_solicitada_min,
                "faixa_solicitada_max": item.faixa_solicitada_max,
                "unidade_solicitada": item.unidade_solicitada or "",
            },
        )
        return mappers.to_item(obj)

    def listar_itens_versao(self, versao_id: UUID, *, tenant_id: UUID) -> list[ItemOrcamento]:
        qs = m.ItemOrcamento.objects.filter(versao_id=versao_id, tenant_id=tenant_id).order_by(
            "sequencia"
        )
        return [mappers.to_item(i) for i in qs]

    # ----- Aprovacao (WORM) -----------------------------------------

    def salvar_aprovacao(self, aprovacao: Aprovacao) -> Aprovacao:
        obj = m.Aprovacao.objects.create(
            id=aprovacao.id,
            orcamento_id=aprovacao.orcamento_id,
            versao_id=aprovacao.versao_id,
            tenant_id=aprovacao.tenant_id,
            aprovado_em=aprovacao.aprovado_em,
            canal=aprovacao.canal.value,
            nome_aprovador_hash=aprovacao.nome_aprovador_hash,
            email_aprovador_hash=aprovacao.email_aprovador_hash,
            lgpd_aceite_versao_termo=aprovacao.lgpd_aceite_versao_termo,
            lgpd_aceite_texto_hash=aprovacao.lgpd_aceite_texto_hash,
            ip_hash=aprovacao.ip_hash,
            user_agent=aprovacao.user_agent,
            ressalvas_aceitas=aprovacao.ressalvas_aceitas,
            aprovado_por=aprovacao.aprovado_por,
        )
        return mappers.to_aprovacao(obj)

    # ----- Analise critica (WORM) -----------------------------------

    def salvar_analise_critica(self, analise: AnaliseCriticaOrcamento) -> AnaliseCriticaOrcamento:
        obj = m.AnaliseCriticaOrcamento.objects.create(
            id=analise.id,
            orcamento_id=analise.orcamento_id,
            versao_id=analise.versao_id,
            tenant_id=analise.tenant_id,
            perfil_no_evento=analise.perfil_no_evento,
            veredito=analise.veredito.value,
            norma_referencia=analise.norma_referencia,
            itens_avaliados=list(analise.itens_avaliados),
            snapshot_hash=analise.snapshot_hash,
            avaliada_em=analise.avaliada_em,
            avaliada_por=analise.avaliada_por,
        )
        return mappers.to_analise(obj)

    def get_analise_critica(
        self, orcamento_id: UUID, *, tenant_id: UUID
    ) -> AnaliseCriticaOrcamento | None:
        obj = (
            m.AnaliseCriticaOrcamento.objects.filter(orcamento_id=orcamento_id, tenant_id=tenant_id)
            .order_by("-criado_em")
            .first()
        )
        return mappers.to_analise(obj) if obj is not None else None

    # ----- Link publico ---------------------------------------------

    def salvar_link(self, link: LinkPublico) -> LinkPublico:
        obj = m.LinkPublico.objects.create(
            id=link.id,
            orcamento_id=link.orcamento_id,
            tenant_id=link.tenant_id,
            token=link.token,
            expira_em=link.expira_em,
            revogado_em=link.revogado_em,
            motivo_revogacao=link.motivo_revogacao or "",
        )
        return mappers.to_link(obj)

    def get_link_ativo(self, orcamento_id: UUID, *, tenant_id: UUID) -> LinkPublico | None:
        obj = m.LinkPublico.objects.filter(
            orcamento_id=orcamento_id, tenant_id=tenant_id, revogado_em__isnull=True
        ).first()
        return mappers.to_link(obj) if obj is not None else None

    def get_link_por_token(self, token: str) -> LinkPublico | None:
        """Lookup por token SEM RLS via função SECURITY DEFINER (D-ORC-19 — T-ORC-038).

        `resolver_orc_publico_token` (migration 0009) resolve o token para
        (tenant_id, orcamento_id, link_id, expira_em, revogado_em, criado_em) com
        bypass controlado de RLS (GUC `app.scope`). Usado pelo endpoint público
        ANTES de entrar em `run_in_tenant_context` (galinha-ovo). `motivo_revogacao`
        não é resolvido aqui (a view só usa `revogado_em`/`expira_em`).
        """
        from django.db import connection

        with connection.cursor() as cur:
            cur.execute(
                "SELECT tenant_id, orcamento_id, link_id, expira_em, revogado_em, criado_em "
                "FROM resolver_orc_publico_token(%s::text)",
                [token],
            )
            row = cur.fetchone()
        if row is None:
            return None
        tenant_id, orcamento_id, link_id, expira_em, revogado_em, criado_em = row
        return LinkPublico(
            id=link_id,
            orcamento_id=orcamento_id,
            tenant_id=tenant_id,
            token=token,
            expira_em=expira_em,
            criado_em=criado_em,
            revogado_em=revogado_em,
            motivo_revogacao=None,
        )

    def revogar_link(self, link_id: UUID, *, revogado_em: datetime, motivo: str) -> None:
        m.LinkPublico.objects.filter(id=link_id).update(
            revogado_em=revogado_em, motivo_revogacao=motivo
        )


class DjangoTemplateRepository:
    """Implementa `TemplateRepository` Protocol sobre Django ORM (Padrao C soft-delete)."""

    def get_by_id(self, template_id: UUID, *, tenant_id: UUID) -> Template | None:
        # `objects` (manager default) ja filtra soft-deletados.
        obj = m.Template.objects.filter(id=template_id, tenant_id=tenant_id).first()
        return mappers.to_template(obj) if obj is not None else None

    def salvar(self, template: Template) -> Template:
        obj, _ = m.Template.all_objects.update_or_create(
            id=template.id,
            defaults={
                "tenant_id": template.tenant_id,
                "nome": template.nome,
                "tipo": template.tipo,
                "itens_default": template.itens_default,
                "condicoes_default": template.condicoes_default,
                "selo_rbc": template.selo_rbc,
                "criado_por": template.criado_por,
                "deletado_em": template.deletado_em,
                "deletado_por": template.deletado_por,
            },
        )
        return mappers.to_template(obj)

    def listar(
        self,
        *,
        tenant_id: UUID,
        incluir_deletados: bool = False,
        offset: int = 0,
        limit: int = 50,
    ) -> list[Template]:
        manager = m.Template.all_objects if incluir_deletados else m.Template.objects
        qs = manager.filter(tenant_id=tenant_id).order_by("nome")[offset : offset + limit]
        return [mappers.to_template(t) for t in qs]

    def soft_delete(
        self,
        template_id: UUID,
        *,
        tenant_id: UUID,
        deletado_por: UUID,
        deletado_em: datetime,
    ) -> Template:
        m.Template.all_objects.filter(id=template_id, tenant_id=tenant_id).update(
            deletado_em=deletado_em, deletado_por=deletado_por
        )
        obj = m.Template.all_objects.get(id=template_id, tenant_id=tenant_id)
        return mappers.to_template(obj)
