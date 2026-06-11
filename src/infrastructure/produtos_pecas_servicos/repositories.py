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
    ItemCatalogo,
    ItemCatalogoVersao,
    KitComposicao,
    LinhaTabelaPreco,
    TabelaPreco,
)
from src.infrastructure.produtos_pecas_servicos import mappers
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

    def listar(self, *, tenant_id: UUID, apenas_ativos: bool = False) -> list[ItemCatalogo]:
        qs = ItemCatalogoModel.objects.filter(tenant_id=tenant_id).order_by("codigo_interno")
        if apenas_ativos:
            qs = qs.filter(status="ativo")
        return [mappers.item_model_para_entidade(m) for m in qs]

    def salvar(self, item: ItemCatalogo) -> None:
        ItemCatalogoModel.objects.update_or_create(
            id=item.id,
            tenant_id=item.tenant_id,
            defaults=mappers.item_para_campos(item),
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
