"""Mappers Model ↔ entidade de domínio (T-PRC-026 — ADR-0007).

`motivo_revogacao=''` no banco ↔ `None` na JanelaVigencia (o VO exige motivo
≥10 chars QUANDO revogado; coluna usa default '' pra evitar DJ001).
`aviso_texto=''` no banco ↔ `None` na entidade PerfilComposicaoPreco.
`justificativa_hash=''` no banco ↔ `None` na entidade PedidoAprovacaoDesconto.
"""

from __future__ import annotations

from src.domain.precificacao.entities import (
    FaixaAprovacaoDesconto,
    ParametrosPrecificacaoTenant,
    PedidoAprovacaoDesconto,
    PerfilComposicaoPreco,
    RegraFormacaoPreco,
    VinculoTabelaPrecoCliente,
)
from src.domain.precificacao.enums import Alcada, ContextoTipo, EstadoPedido, ModoFormacaoPreco
from src.domain.precificacao.value_objects import Percentual
from src.domain.shared.value_objects import JanelaVigencia
from src.infrastructure.precificacao import models


def _vigencia_regra(m: models.RegraFormacaoPreco) -> JanelaVigencia:
    return JanelaVigencia(
        inicio=m.vigencia_inicio,
        fim=m.vigencia_fim,
        revogado_em=m.revogado_em,
        motivo_revogacao=m.motivo_revogacao or None,
    )


def _vigencia_vinculo(m: models.VinculoTabelaPrecoCliente) -> JanelaVigencia:
    return JanelaVigencia(
        inicio=m.vigencia_inicio,
        fim=m.vigencia_fim,
        revogado_em=m.revogado_em,
        motivo_revogacao=m.motivo_revogacao or None,
    )


def regra_model_para_entidade(m: models.RegraFormacaoPreco) -> RegraFormacaoPreco:
    return RegraFormacaoPreco(
        id=m.id,
        tenant_id=m.tenant_id,
        item_id=m.item_id,
        modo=ModoFormacaoPreco(m.modo),
        vigencia=_vigencia_regra(m),
        versao_n=m.versao_n,
        criado_por=m.criado_por,
        preco_fixo=m.preco_fixo,
        custo_manual_declarado=m.custo_manual_declarado,
        custo_referencia_em=m.custo_referencia_em,
        margem_alvo_pct=Percentual(m.margem_alvo_pct) if m.margem_alvo_pct is not None else None,
        margem_piso_pct=Percentual(m.margem_piso_pct) if m.margem_piso_pct is not None else None,
    )


def perfil_model_para_entidade(m: models.PerfilComposicaoPreco) -> PerfilComposicaoPreco:
    from uuid import UUID
    return PerfilComposicaoPreco(
        id=m.id,
        tenant_id=m.tenant_id,
        item_servico_id=m.item_servico_id,
        componentes_esperados=tuple(UUID(c) if isinstance(c, str) else c for c in (m.componentes_esperados or [])),
        criado_por=m.criado_por,
        aviso_texto=m.aviso_texto or None,
        deletado_em=m.deletado_em,
    )


def faixa_model_para_entidade(m: models.FaixaAprovacaoDesconto) -> FaixaAprovacaoDesconto:
    return FaixaAprovacaoDesconto(
        id=m.id,
        tenant_id=m.tenant_id,
        pct_de=Percentual(m.pct_de),
        pct_ate=Percentual(m.pct_ate),
        alcada=Alcada(m.alcada),
        versao_n=m.versao_n,
        hash_conjunto=m.hash_conjunto,
        criado_por=m.criado_por,
    )


def pedido_model_para_entidade(m: models.PedidoAprovacaoDesconto) -> PedidoAprovacaoDesconto:
    return PedidoAprovacaoDesconto(
        id=m.id,
        tenant_id=m.tenant_id,
        contexto_tipo=ContextoTipo(m.contexto_tipo),
        pct_solicitado=Percentual(m.pct_solicitado),
        cortesia=m.cortesia,
        alcada_exigida=Alcada(m.alcada_exigida),
        fingerprint_calculo=m.fingerprint_calculo,
        estado=EstadoPedido(m.estado),
        solicitante_id=m.solicitante_id,
        snapshot_probatorio=m.snapshot_probatorio,
        criado_em=m.criado_em,
        contexto_id=m.contexto_id,
        decisor_id=m.decisor_id,
        justificativa_hash=m.justificativa_hash or None,
        decidido_em=m.decidido_em,
    )


def vinculo_model_para_entidade(m: models.VinculoTabelaPrecoCliente) -> VinculoTabelaPrecoCliente:
    return VinculoTabelaPrecoCliente(
        id=m.id,
        tenant_id=m.tenant_id,
        tabela_id=m.tabela_id,
        cliente_id=m.cliente_id,
        vigencia=_vigencia_vinculo(m),
        criado_por=m.criado_por,
    )


def parametros_model_para_entidade(m: models.ParametrosPrecificacaoTenant) -> ParametrosPrecificacaoTenant:
    return ParametrosPrecificacaoTenant(
        id=m.id,
        tenant_id=m.tenant_id,
        versao_n=m.versao_n,
        custo_km=m.custo_km,
        taxa_parcelamento_mensal=Percentual(m.taxa_parcelamento_mensal),
        pct_comissao_prevista=Percentual(m.pct_comissao_prevista),
        margem_alvo_default=Percentual(m.margem_alvo_default),
        margem_piso_default=Percentual(m.margem_piso_default),
        criado_por=m.criado_por,
        criado_em=m.criado_em,
    )
