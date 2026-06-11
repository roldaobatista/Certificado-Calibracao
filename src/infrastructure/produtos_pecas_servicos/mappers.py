"""Mappers Model ↔ entidade de domínio (T-PPS-022 — ADR-0007).

`motivo_revogacao=''` no banco ↔ `None` na JanelaVigencia (o VO exige motivo
≥10 chars QUANDO revogado; coluna usa default '' pra evitar DJ001).
"""

from __future__ import annotations

from src.domain.produtos_pecas_servicos.entities import (
    ImportacaoCatalogo,
    ItemCatalogo,
    ItemCatalogoVersao,
    KitComposicao,
    LinhaImportacaoCatalogo,
    LinhaTabelaPreco,
    TabelaPreco,
)
from src.domain.produtos_pecas_servicos.enums import (
    OrigemPreco,
    StatusItem,
    StatusLinhaImportacao,
    TipoItem,
)
from src.domain.produtos_pecas_servicos.value_objects import Preco
from src.domain.shared.value_objects import JanelaVigencia
from src.infrastructure.produtos_pecas_servicos import models


def item_model_para_entidade(m: models.ItemCatalogo) -> ItemCatalogo:
    return ItemCatalogo(
        id=m.id,
        tenant_id=m.tenant_id,
        codigo_interno=m.codigo_interno,
        tipo=TipoItem(m.tipo),
        controla_estoque=m.controla_estoque,
        status=StatusItem(m.status),
        codigo_fabricante=m.codigo_fabricante,
    )


def item_para_campos(item: ItemCatalogo) -> dict[str, object]:
    """Campos pro update_or_create (sem id/tenant — chaves do lookup)."""
    return {
        "codigo_interno": item.codigo_interno,
        "tipo": item.tipo.value,
        "controla_estoque": item.controla_estoque,
        "status": item.status.value,
        "codigo_fabricante": item.codigo_fabricante,
    }


def _vigencia(m: models.ItemCatalogoVersao | models.LinhaTabelaPreco) -> JanelaVigencia:
    return JanelaVigencia(
        inicio=m.vigencia_inicio,
        fim=m.vigencia_fim,
        revogado_em=m.revogado_em,
        motivo_revogacao=m.motivo_revogacao or None,
    )


def versao_model_para_entidade(m: models.ItemCatalogoVersao) -> ItemCatalogoVersao:
    return ItemCatalogoVersao(
        id=m.id,
        tenant_id=m.tenant_id,
        item_id=m.item_id,
        versao_n=m.versao_n,
        nome=m.nome,
        unidade_medida=m.unidade_medida,
        preco_padrao=Preco(m.preco_padrao),
        vigencia=_vigencia(m),
        criado_por=m.criado_por,
        descricao=m.descricao,
        categoria=m.categoria,
        motivo=m.motivo,
    )


def composicao_model_para_entidade(m: models.KitComposicao) -> KitComposicao:
    return KitComposicao(
        kit_item_id=m.kit_item_id,
        item_filho_id=m.item_filho_id,
        quantidade=m.quantidade,
    )


def tabela_model_para_entidade(m: models.TabelaPreco) -> TabelaPreco:
    return TabelaPreco(
        id=m.id,
        tenant_id=m.tenant_id,
        nome=m.nome,
        eh_padrao=m.eh_padrao,
        descricao=m.descricao,
    )


def linha_model_para_entidade(m: models.LinhaTabelaPreco) -> LinhaTabelaPreco:
    return LinhaTabelaPreco(
        id=m.id,
        tenant_id=m.tenant_id,
        tabela_id=m.tabela_id,
        item_id=m.item_id,
        preco=Preco(m.preco),
        vigencia=_vigencia(m),
        criado_por=m.criado_por,
        origem_sugestao=OrigemPreco(m.origem_sugestao),
    )


def importacao_model_para_entidade(m: models.ImportacaoCatalogo) -> ImportacaoCatalogo:
    return ImportacaoCatalogo(
        id=m.id,
        tenant_id=m.tenant_id,
        arquivo_sha256=m.arquivo_sha256,
        arquivo_nome_hash=m.arquivo_nome_hash,
        total_linhas=m.total_linhas,
        criado_por=m.criado_por,
        criado_em=m.criado_em,
    )


def linha_importacao_model_para_entidade(
    m: models.ImportacaoCatalogoLinha,
) -> LinhaImportacaoCatalogo:
    return LinhaImportacaoCatalogo(
        id=m.id,
        tenant_id=m.tenant_id,
        importacao_id=m.importacao_id,
        linha_numero=m.linha_numero,
        status=StatusLinhaImportacao(m.status),
        codigo_interno=m.codigo_interno,
        tipo=m.tipo,
        nome=m.nome,
        unidade_medida=m.unidade_medida,
        preco_padrao=m.preco_padrao,
        categoria=m.categoria,
        descricao=m.descricao,
        codigo_fabricante=m.codigo_fabricante,
        motivo_rejeicao=m.motivo_rejeicao,
        item_criado_id=m.item_criado_id,
    )
