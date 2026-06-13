"""Entidades do módulo `precificacao` (T-PRC-012 — frozen dataclasses).

6 entidades frozen espelhando o schema (Fatia 1b):
  RegraFormacaoPreco, PerfilComposicaoPreco, FaixaAprovacaoDesconto,
  PedidoAprovacaoDesconto, VinculoTabelaPrecoCliente,
  ParametrosPrecificacaoTenant.

Refs: spec §4; D-PRC-3/7/12/14.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from src.domain.shared.value_objects import JanelaVigencia

from .enums import Alcada, ContextoTipo, EstadoPedido, ModoFormacaoPreco
from .value_objects import Percentual


@dataclass(frozen=True)
class RegraFormacaoPreco:
    """Regra de formação de preço por item, versionada WORM molde Imposto (D-PRC-7).

    Imutável pós-publicação (trigger WORM Padrão B — Fatia 1b).
    Correção = revogar + recriar (revogar_regra + publicar_regra).
    `versao_n`: denso por (tenant, item) sob advisory lock namespace 880_404.

    custo_manual_declarado: obrigatório quando modo=MARGEM_ALVO (origem CUSTO_MANUAL).
    custo_referencia_em: data de referência do custo manual (staleness — TL-PRC-07).
    margem_alvo_pct: margem desejada (% sobre custo) — MARGEM_ALVO e COST_PLUS.
    margem_piso_pct: piso de margem mínima abaixo do qual bloqueia (D-PRC-8).
    """

    id: UUID
    tenant_id: UUID
    item_id: UUID
    modo: ModoFormacaoPreco
    vigencia: JanelaVigencia
    versao_n: int
    criado_por: UUID
    preco_fixo: Decimal | None = None
    custo_manual_declarado: Decimal | None = None
    custo_referencia_em: datetime | None = None
    margem_alvo_pct: Percentual | None = None
    margem_piso_pct: Percentual | None = None


@dataclass(frozen=True)
class PerfilComposicaoPreco:
    """Perfil declarativo de componentes esperados por item-serviço (D-PRC-2).

    componentes_esperados: IDs de itens de catálogo que DEVEM estar na cesta
        quando este item-serviço estiver presente (ModoMontagem.COMPONENTES_CHECKLIST).
    aviso_texto: texto emitido como aviso em ModoMontagem.FECHADO_COM_AVISO.
    deletado_em: soft-delete mutável (ADR-0031 Padrão C — campo de conf. mutável).

    NÃO é frozen total: deletado_em muda no ciclo de vida. O campo `frozen=True`
    em Python garante que o domínio não muta — o adapter ORM atualiza diretamente.
    """

    id: UUID
    tenant_id: UUID
    item_servico_id: UUID
    componentes_esperados: tuple[UUID, ...]
    criado_por: UUID
    aviso_texto: str | None = None
    deletado_em: datetime | None = None


@dataclass(frozen=True)
class FaixaAprovacaoDesconto:
    """Conjunto de faixas de aprovação de desconto por tenant (D-PRC-3).

    Faixas contíguas cobrindo 0..100 sem buraco nem sobreposição (replace-all
    atômico — `configurar_faixas` valida o CONJUNTO via `validar_faixas_contiguas`).

    pct_de, pct_ate: limites da faixa (half-open [pct_de, pct_ate)).
    alcada: alçada de aprovação exigida nesta faixa.
    versao_n: versão densa do conjunto de faixas (incrementa em replace-all).
    hash_conjunto: hash canônico ADR-0029 do conjunto completo (fingerprint de versão).
    """

    id: UUID
    tenant_id: UUID
    pct_de: Percentual
    pct_ate: Percentual
    alcada: Alcada
    versao_n: int
    hash_conjunto: str
    criado_por: UUID


@dataclass(frozen=True)
class PedidoAprovacaoDesconto:
    """Pedido de aprovação de desconto WORM one-shot (D-PRC-14).

    Estado SOLICITADO→APROVADO|NEGADO via UPDATE escopado + trigger one-shot.
    Nunca volta atrás (INV-PRC-APROVACAO-ONE-SHOT).

    fingerprint_calculo: hash canônico ADR-0029 de (entradas + refs + pct) —
        binding aprovação↔cálculo (D-PRC-14); consumidor só usa aprovação se
        fingerprint do cálculo vigente bater.
    snapshot_probatorio: JSON frozen capturado na solicitação (eco das entradas
        para replay — AC-PRC-002-3).
    justificativa_hash: hash ADR-0029+HMAC-tenant do texto justificativo
        (texto cru em JustificativaDecisaoDesconto — D-PRC-15).
    cortesia: True quando pct_solicitado == 100 (alçada DONO obrigatória — D-PRC-13).
    decisor_id: preenchido na decisão; DEVE ser != solicitante_id (INV-PRC-APROVACAO-INDEPENDENTE).
    """

    id: UUID
    tenant_id: UUID
    contexto_tipo: ContextoTipo
    pct_solicitado: Percentual
    cortesia: bool
    alcada_exigida: Alcada
    fingerprint_calculo: str
    estado: EstadoPedido
    solicitante_id: UUID
    snapshot_probatorio: str  # JSON canônico ADR-0029
    criado_em: datetime
    contexto_id: UUID | None = None  # FK real adicionada quando módulo consumidor existir
    decisor_id: UUID | None = None
    justificativa_hash: str | None = None
    decidido_em: datetime | None = None


@dataclass(frozen=True)
class VinculoTabelaPrecoCliente:
    """Vínculo entre cliente e tabela de preço específica (D-PRC-12).

    Resolve cliente→tabela DENTRO desta frente (zero retrofit de schema na PPS).
    UNIQUE parcial vigente por (tenant, cliente_id) — só 1 vínculo ativo por cliente.
    vigencia: ADR-0030 (consumer de Cliente.Anonimizado revoga — ADR-0032).
    """

    id: UUID
    tenant_id: UUID
    tabela_id: UUID  # FK→LinhaTabelaPreco.tabela_id (PPS)
    cliente_id: UUID  # pseudônimo; revogado quando Cliente.Anonimizado
    vigencia: JanelaVigencia
    criado_por: UUID


@dataclass(frozen=True)
class ParametrosPrecificacaoTenant:
    """Parâmetros globais de precificação do tenant, versionados (D-PRC-9).

    Versionado (versao_n denso) para replay bit-a-bit do motor (AC-PRC-002-3).

    custo_km: custo por km de deslocamento (US-PRC-006 simulação).
    taxa_parcelamento_mensal: taxa mensal de parcelamento em % (US-PRC-006).
    pct_comissao_prevista: comissão prevista em % sobre preço de venda (PREVISTA
        — provider real em GATE-PRC-COMISSAO-REAL).
    margem_alvo_default: margem alvo padrão para regras sem margem_alvo_pct.
    margem_piso_default: piso padrão para regras sem margem_piso_pct.
    """

    id: UUID
    tenant_id: UUID
    versao_n: int
    custo_km: Decimal
    taxa_parcelamento_mensal: Percentual
    pct_comissao_prevista: Percentual
    margem_alvo_default: Percentual
    margem_piso_default: Percentual
    criado_por: UUID
    criado_em: datetime
