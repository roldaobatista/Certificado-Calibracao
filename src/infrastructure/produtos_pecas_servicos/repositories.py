"""Adapters Django dos Protocols do catálogo (T-PPS-022 — ADR-0007).

Concorrência (D-PPS-4): `travar_item`/`travar_linha` fazem `pg_advisory_xact_lock`
(namespace 880_403 — distinto de 880_401 certificados M8 e 880_402 numeração
configuracoes). O use case chama o lock DENTRO de `transaction.atomic` ANTES de
ler versões/linhas — densidade `versao_n = max+1` e o par encerrar-anterior+
inserir-nova ficam serializados. A exclusion 0004 é a verdade no banco contra
qualquer caminho que burle o use case (camada independente — TL-(d)).

Revogação/encerramento: UPDATE escopado nos campos one-shot (o trigger 0003
garante one-shot e imutabilidade do resto). NÃO são singletons.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from django.db import connection

from src.domain.produtos_pecas_servicos.entities import (
    ImportacaoCatalogo,
    ItemCatalogo,
    ItemCatalogoVersao,
    KitComposicao,
    LinhaImportacaoCatalogo,
    LinhaTabelaPreco,
    TabelaPreco,
)
from src.infrastructure.produtos_pecas_servicos import mappers
from src.infrastructure.produtos_pecas_servicos.models import (
    ImportacaoCatalogo as ImportacaoModel,
)
from src.infrastructure.produtos_pecas_servicos.models import (
    ImportacaoCatalogoLinha as LinhaImportacaoModel,
)
from src.infrastructure.produtos_pecas_servicos.models import (
    ItemCatalogo as ItemCatalogoModel,
)
from src.infrastructure.produtos_pecas_servicos.models import (
    ItemCatalogoVersao as VersaoModel,
)
from src.infrastructure.produtos_pecas_servicos.models import (
    KitComposicao as KitComposicaoModel,
)
from src.infrastructure.produtos_pecas_servicos.models import (
    LinhaTabelaPreco as LinhaModel,
)
from src.infrastructure.produtos_pecas_servicos.models import (
    TabelaPreco as TabelaPrecoModel,
)

# Namespace do advisory lock do catálogo (serializa criar/corrigir versão por
# item e linha por (tabela, item)).
_ADVISORY_LOCK_CATALOGO = 880_403


def _advisory_lock(chave: str) -> None:
    with connection.cursor() as cur:
        cur.execute(
            "SELECT pg_advisory_xact_lock(%s, hashtext(%s));",
            [_ADVISORY_LOCK_CATALOGO, chave],
        )


class DjangoItemCatalogoRepository:
    """Agregado ItemCatalogo (item estrutural mutável + versões WORM + kit)."""

    def obter(self, *, tenant_id: UUID, item_id: UUID) -> ItemCatalogo | None:
        m = ItemCatalogoModel.objects.filter(tenant_id=tenant_id, id=item_id).first()
        return mappers.item_model_para_entidade(m) if m is not None else None

    def obter_por_codigo(self, *, tenant_id: UUID, codigo_interno: str) -> ItemCatalogo | None:
        m = ItemCatalogoModel.objects.filter(
            tenant_id=tenant_id, codigo_interno=codigo_interno
        ).first()
        return mappers.item_model_para_entidade(m) if m is not None else None

    def salvar(self, item: ItemCatalogo) -> None:
        mutaveis = mappers.item_para_campos(item)
        ItemCatalogoModel.objects.update_or_create(
            id=item.id,
            tenant_id=item.tenant_id,
            defaults=mutaveis,
            # codigo_interno/tipo so no INSERT (imutaveis — 0011 QUAL-M1)
            create_defaults={
                **mutaveis,
                "codigo_interno": item.codigo_interno,
                "tipo": item.tipo.value,
            },
        )

    def travar_item(self, *, tenant_id: UUID, item_id: UUID) -> None:
        """Advisory lock por item (D-PPS-4) — chamar DENTRO de transaction.atomic."""
        _advisory_lock(f"{tenant_id}:item:{item_id}")

    def listar_versoes(self, *, tenant_id: UUID, item_id: UUID) -> list[ItemCatalogoVersao]:
        qs = VersaoModel.objects.filter(tenant_id=tenant_id, item_id=item_id).order_by(
            "versao_n"
        )
        return [mappers.versao_model_para_entidade(m) for m in qs]

    def salvar_versao(self, versao: ItemCatalogoVersao) -> None:
        VersaoModel.objects.create(
            id=versao.id,
            tenant_id=versao.tenant_id,
            item_id=versao.item_id,
            versao_n=versao.versao_n,
            nome=versao.nome,
            descricao=versao.descricao,
            categoria=versao.categoria,
            unidade_medida=versao.unidade_medida,
            preco_padrao=versao.preco_padrao.valor,
            vigencia_inicio=versao.vigencia.inicio,
            vigencia_fim=versao.vigencia.fim,
            criado_por=versao.criado_por,
            motivo=versao.motivo,
        )

    def encerrar_vigencia_versao(
        self, *, tenant_id: UUID, versao_id: UUID, fim: datetime
    ) -> None:
        atualizadas = VersaoModel.objects.filter(
            tenant_id=tenant_id, id=versao_id, vigencia_fim__isnull=True
        ).update(vigencia_fim=fim)
        if atualizadas == 0:  # one-shot violado / inexistente (molde Imposto → 409)
            raise RuntimeError(f"versão {versao_id} sem vigência aberta pra encerrar.")

    def revogar_versao(self, *, tenant_id: UUID, versao_id: UUID, motivo: str) -> None:
        from django.utils import timezone

        atualizadas = VersaoModel.objects.filter(
            tenant_id=tenant_id, id=versao_id, revogado_em__isnull=True
        ).update(revogado_em=timezone.now(), motivo_revogacao=motivo)
        if atualizadas == 0:
            raise RuntimeError(f"versão {versao_id} já revogada ou inexistente.")

    def listar_composicao(self, *, tenant_id: UUID, kit_item_id: UUID) -> list[KitComposicao]:
        qs = KitComposicaoModel.objects.filter(tenant_id=tenant_id, kit_item_id=kit_item_id)
        return [mappers.composicao_model_para_entidade(m) for m in qs]

    def substituir_composicao(
        self, *, tenant_id: UUID, kit_item_id: UUID, composicao: list[KitComposicao]
    ) -> None:
        KitComposicaoModel.objects.filter(
            tenant_id=tenant_id, kit_item_id=kit_item_id
        ).delete()
        KitComposicaoModel.objects.bulk_create(
            KitComposicaoModel(
                tenant_id=tenant_id,
                kit_item_id=parte.kit_item_id,
                item_filho_id=parte.item_filho_id,
                quantidade=parte.quantidade,
            )
            for parte in composicao
        )


class DjangoTabelaPrecoRepository:
    """Agregado TabelaPreco (tabela mutável + linhas WORM — ADR-0081)."""

    def obter_padrao(self, *, tenant_id: UUID) -> TabelaPreco | None:
        m = TabelaPrecoModel.objects.filter(tenant_id=tenant_id, eh_padrao=True).first()
        return mappers.tabela_model_para_entidade(m) if m is not None else None

    def obter(self, *, tenant_id: UUID, tabela_id: UUID) -> TabelaPreco | None:
        m = TabelaPrecoModel.objects.filter(tenant_id=tenant_id, id=tabela_id).first()
        return mappers.tabela_model_para_entidade(m) if m is not None else None

    def salvar(self, tabela: TabelaPreco) -> None:
        TabelaPrecoModel.objects.update_or_create(
            id=tabela.id,
            tenant_id=tabela.tenant_id,
            defaults={
                "nome": tabela.nome,
                "descricao": tabela.descricao,
                "eh_padrao": tabela.eh_padrao,
            },
        )

    def travar_linha(self, *, tenant_id: UUID, tabela_id: UUID, item_id: UUID) -> None:
        """Advisory lock por (tabela, item) — chamar DENTRO de transaction.atomic."""
        _advisory_lock(f"{tenant_id}:linha:{tabela_id}:{item_id}")

    def obter_linha(
        self, *, tenant_id: UUID, tabela_id: UUID, linha_id: UUID
    ) -> LinhaTabelaPreco | None:
        # P9 PERF-M1: lookup pontual por PK (corrigir/encerrar nao materializam
        # a tabela inteira — linha WORM acumula pra sempre).
        m = LinhaModel.objects.filter(
            tenant_id=tenant_id, tabela_id=tabela_id, id=linha_id
        ).first()
        return mappers.linha_model_para_entidade(m) if m is not None else None

    def listar_linhas(
        self, *, tenant_id: UUID, tabela_id: UUID, item_id: UUID | None = None
    ) -> list[LinhaTabelaPreco]:
        qs = LinhaModel.objects.filter(tenant_id=tenant_id, tabela_id=tabela_id)
        if item_id is not None:
            qs = qs.filter(item_id=item_id)
        return [mappers.linha_model_para_entidade(m) for m in qs.order_by("vigencia_inicio")]

    def salvar_linha(self, linha: LinhaTabelaPreco) -> None:
        LinhaModel.objects.create(
            id=linha.id,
            tenant_id=linha.tenant_id,
            tabela_id=linha.tabela_id,
            item_id=linha.item_id,
            preco=linha.preco.valor,
            vigencia_inicio=linha.vigencia.inicio,
            vigencia_fim=linha.vigencia.fim,
            origem_sugestao=linha.origem_sugestao.value,
            criado_por=linha.criado_por,
        )

    def encerrar_vigencia_linha(
        self, *, tenant_id: UUID, linha_id: UUID, fim: datetime
    ) -> None:
        atualizadas = LinhaModel.objects.filter(
            tenant_id=tenant_id, id=linha_id, vigencia_fim__isnull=True
        ).update(vigencia_fim=fim)
        if atualizadas == 0:  # one-shot violado / inexistente (molde Imposto → 409)
            raise RuntimeError(f"linha {linha_id} sem vigência aberta pra encerrar.")

    def revogar_linha(self, *, tenant_id: UUID, linha_id: UUID, motivo: str) -> None:
        from django.utils import timezone

        atualizadas = LinhaModel.objects.filter(
            tenant_id=tenant_id, id=linha_id, revogado_em__isnull=True
        ).update(revogado_em=timezone.now(), motivo_revogacao=motivo)
        if atualizadas == 0:
            raise RuntimeError(f"linha {linha_id} já revogada ou inexistente.")


class DjangoImportacaoCatalogoRepository:
    """Staging da importação CSV (US-CAT-004 — mutável, TTL 90d ADV-PPS-06).

    `marcar_linha_*` são one-shot por UPDATE escopado em `status='validada'`
    (rowcount 0 → RuntimeError → 409): aceite/rejeição nunca reprocessa.
    """

    def salvar_importacao(
        self,
        importacao: ImportacaoCatalogo,
        linhas: list[LinhaImportacaoCatalogo],
    ) -> None:
        ImportacaoModel.objects.create(
            id=importacao.id,
            tenant_id=importacao.tenant_id,
            arquivo_sha256=importacao.arquivo_sha256,
            arquivo_nome_hash=importacao.arquivo_nome_hash,
            total_linhas=importacao.total_linhas,
            criado_por=importacao.criado_por,
            criado_em=importacao.criado_em,
        )
        LinhaImportacaoModel.objects.bulk_create(
            LinhaImportacaoModel(
                id=li.id,
                tenant_id=li.tenant_id,
                importacao_id=li.importacao_id,
                linha_numero=li.linha_numero,
                status=li.status.value,
                codigo_interno=li.codigo_interno,
                tipo=li.tipo,
                nome=li.nome,
                unidade_medida=li.unidade_medida,
                preco_padrao=li.preco_padrao,
                categoria=li.categoria,
                descricao=li.descricao,
                codigo_fabricante=li.codigo_fabricante,
                motivo_rejeicao=li.motivo_rejeicao,
            )
            for li in linhas
        )

    def obter_importacao(
        self, *, tenant_id: UUID, importacao_id: UUID
    ) -> ImportacaoCatalogo | None:
        m = ImportacaoModel.objects.filter(tenant_id=tenant_id, id=importacao_id).first()
        return mappers.importacao_model_para_entidade(m) if m is not None else None

    def listar_linhas(
        self, *, tenant_id: UUID, importacao_id: UUID
    ) -> list[LinhaImportacaoCatalogo]:
        qs = LinhaImportacaoModel.objects.filter(
            tenant_id=tenant_id, importacao_id=importacao_id
        ).order_by("linha_numero")
        return [mappers.linha_importacao_model_para_entidade(m) for m in qs]

    def obter_linha(
        self, *, tenant_id: UUID, linha_id: UUID
    ) -> LinhaImportacaoCatalogo | None:
        m = LinhaImportacaoModel.objects.filter(tenant_id=tenant_id, id=linha_id).first()
        return mappers.linha_importacao_model_para_entidade(m) if m is not None else None

    def marcar_linha_aceita(
        self, *, tenant_id: UUID, linha_id: UUID, item_criado_id: UUID
    ) -> None:
        atualizadas = LinhaImportacaoModel.objects.filter(
            tenant_id=tenant_id, id=linha_id, status="validada"
        ).update(status="aceita", item_criado_id=item_criado_id)
        if atualizadas == 0:
            raise RuntimeError(f"linha {linha_id} não está 'validada' — aceite é one-shot.")

    def marcar_linha_rejeitada(self, *, tenant_id: UUID, linha_id: UUID, motivo: str) -> None:
        atualizadas = LinhaImportacaoModel.objects.filter(
            tenant_id=tenant_id, id=linha_id, status="validada"
        ).update(status="rejeitada", motivo_rejeicao=motivo)
        if atualizadas == 0:
            raise RuntimeError(
                f"linha {linha_id} não está 'validada' — rejeição é one-shot."
            )

    def eliminar_importacoes_anteriores_a(self, *, tenant_id: UUID, limite: datetime) -> int:
        # FK CASCADE elimina as linhas junto (staging — DELETE legítimo).
        # P9 IDEMP-B3: contagem vem do próprio delete() (sem TOCTOU count/delete).
        _, por_modelo = ImportacaoModel.objects.filter(
            tenant_id=tenant_id, criado_em__lt=limite
        ).delete()
        return por_modelo.get("produtos_pecas_servicos.ImportacaoCatalogo", 0)
