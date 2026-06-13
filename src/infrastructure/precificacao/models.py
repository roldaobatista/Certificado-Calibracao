# ruff: noqa: RUF012 — choices derivados de enum (list mutavel ok em Model)
"""Frente `precificacao` — models Django (Fatia 1b, T-PRC-020).

7 tabelas: `regra_formacao_preco`, `perfil_composicao_preco`,
`faixa_aprovacao_desconto`, `pedido_aprovacao_desconto`,
`justificativa_decisao_desconto`, `vinculo_tabela_preco_cliente`,
`parametros_precificacao_tenant`.

Choices 1:1 dos enums de domínio (anti-drift). Domain NÃO importa
Django (ADR-0007 — `mappers.py` converte).

Imutabilidade (D-PRC-7 / INV-PRC-REGRA-IMUTAVEL — molde `Imposto` #1):
- `regra_formacao_preco` = Padrão B WORM: campos probatórios imutáveis
  pós-INSERT (trigger 0003), `vigencia_fim` one-shot, `revogado_em`+
  motivo one-shot, DELETE bloqueado (retenção comercial 5a).
- `pedido_aprovacao_desconto` = WORM one-shot: SOLICITADO→APROVADO|NEGADO
  via trigger (INV-PRC-APROVACAO-ONE-SHOT); campos probatórios pós-decisão
  congelados por trigger.
- `justificativa_decisao_desconto` = soft-delete ADR-0031 (texto cru TTL 5a —
  D-PRC-15; texto exposto ao vendedor via AC-PRC-004-3).
- Demais tabelas = configuração mutável com auditoria.

Schema-irmãos:
- 0001_initial: CreateModel ×7 + UNIQUEs + CHECKs + one-shot estado pedido.
- 0002_rls_policies: RLS pattern v2 (ADR-0002 §6) nas 7 tabelas.
- 0003_triggers_worm: imutabilidade regra (INV-PRC-REGRA-IMUTAVEL) +
  one-shot pedido (INV-PRC-APROVACAO-ONE-SHOT) + anti-mutação probatório pós-decisão.
- 0004_exclusions: btree_gist `(tenant, item)` regra WHERE revogado_em IS NULL.
- 0005_grants_app_user + 0006_seed_authz_precificacao.

LGPD: `criado_por`/`solicitante_id`/`decisor_id` são pseudônimos (art. 12);
eventos WORM levam só hash. `justificativa_*` NUNCA cru em evento (ADV-PRC-01;
hash ADR-0029 na camada de eventos, Fatia 2). Parâmetros/faixas NUNCA em claro
em evento (segredo comercial — INV-PRC-SEGREDO-LOG).
"""

from __future__ import annotations

import uuid
from enum import Enum

from django.db import models

from src.domain.precificacao.enums import (
    Alcada,
    ContextoTipo,
    EstadoPedido,
    ModoFormacaoPreco,
)


def _choices(enum_cls: type[Enum]) -> list[tuple[str, str]]:
    """Choices (value, value) a partir do enum de domínio (1:1 anti-drift)."""
    return [(membro.value, str(membro.value)) for membro in enum_cls]


class RegraFormacaoPreco(models.Model):
    """Regra de formação de preço por item, versionada WORM molde Imposto (D-PRC-7).

    `versao_n`: denso por (tenant, item) sob advisory lock 880_404 — TL-PRC-04.
    Correção = revogar + recriar (revogar_regra + publicar_regra).
    UNIQUE `(tenant, item, versao_n)` — INV-PRC-REGRA-IMUTAVEL.
    Exclusion btree_gist `(tenant, item) WHERE revogado_em IS NULL` em 0004
    (não-sobreposição de vigência — INV-PRC-REGRA-SEM-SOBREPOSICAO).
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, serialize=False)
    tenant = models.ForeignKey(
        "tenant.tenant", on_delete=models.PROTECT, related_name="regras_formacao_preco"
    )
    item = models.ForeignKey(
        "produtos_pecas_servicos.ItemCatalogo",
        on_delete=models.PROTECT,
        related_name="regras_preco",
        help_text="Item do catálogo para o qual esta regra define formação de preço.",
    )
    modo = models.CharField(
        max_length=15,
        choices=_choices(ModoFormacaoPreco),
        help_text="preco_fixo|margem_alvo|cost_plus — imutável (trigger 0003).",
    )
    versao_n = models.IntegerField(
        help_text="Denso por (tenant, item): 1,2,3... (max+1 sob advisory lock 880_404)."
    )
    preco_fixo = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True,
        help_text="Preço fixo declarado (obrigatório quando modo=PRECO_FIXO).",
    )
    custo_manual_declarado = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True,
        help_text="Custo manual declarado (obrigatório quando modo=MARGEM_ALVO).",
    )
    custo_referencia_em = models.DateTimeField(
        null=True, blank=True,
        help_text="Data de referência do custo manual (staleness — TL-PRC-07).",
    )
    margem_alvo_pct = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True,
        help_text="Margem alvo % (0..100) — MARGEM_ALVO e COST_PLUS.",
    )
    margem_piso_pct = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True,
        help_text="Piso de margem mínima % — abaixo bloqueia (D-PRC-8).",
    )
    vigencia_inicio = models.DateTimeField()
    vigencia_fim = models.DateTimeField(
        null=True, blank=True,
        help_text="One-shot NULL→data (encerramento pela regra sucessora — trigger 0003).",
    )
    revogado_em = models.DateTimeField(
        null=True, blank=True,
        help_text="One-shot — regra errada sai da exclusion e nunca resolve.",
    )
    motivo_revogacao = models.CharField(max_length=600, blank=True, default="")
    # lgpd-base: pseudônimo art. 12 LGPD; evento WORM leva só hash
    criado_por = models.UUIDField(
        help_text="Pseudônimo art. 12 LGPD; evento WORM leva só hash."
    )
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "regra_formacao_preco"
        verbose_name = "Regra de formação de preço"
        verbose_name_plural = "Regras de formação de preço"
        constraints = [
            models.UniqueConstraint(
                fields=("tenant", "item", "versao_n"), name="uq_prc_regra_versao_n"
            ),
        ]
        indexes = [
            models.Index(fields=["tenant", "item"], name="ix_prc_regra_item"),
        ]

    def __str__(self) -> str:
        return f"RegraFormacaoPreco(item={self.item_id} v{self.versao_n} {self.modo})"


class PerfilComposicaoPreco(models.Model):
    """Perfil declarativo de componentes esperados por item-serviço (D-PRC-2).

    `componentes_esperados` é JSON com lista de UUIDs de itens do catálogo.
    Configuração mutável (ADR-0031 Padrão C — soft-delete por `deletado_em`).
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, serialize=False)
    tenant = models.ForeignKey(
        "tenant.tenant", on_delete=models.PROTECT, related_name="perfis_composicao_preco"
    )
    item_servico = models.ForeignKey(
        "produtos_pecas_servicos.ItemCatalogo",
        on_delete=models.PROTECT,
        related_name="perfis_composicao",
        help_text="Item-serviço ao qual este perfil se aplica.",
    )
    componentes_esperados = models.JSONField(
        default=list,
        help_text="Lista de UUIDs de itens de catálogo esperados na cesta (D-PRC-2).",
    )
    aviso_texto = models.CharField(
        max_length=600, blank=True, default="",
        help_text="Texto de aviso para ModoMontagem.FECHADO_COM_AVISO.",
    )
    # lgpd-base: pseudônimo art. 12 LGPD
    criado_por = models.UUIDField(
        help_text="Pseudônimo art. 12 LGPD."
    )
    deletado_em = models.DateTimeField(
        null=True, blank=True,
        help_text="Soft-delete (ADR-0031 Padrão C — configuração mutável).",
    )
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "perfil_composicao_preco"
        verbose_name = "Perfil de composição de preço"
        verbose_name_plural = "Perfis de composição de preço"
        indexes = [
            models.Index(fields=["tenant", "item_servico"], name="ix_prc_perfil_item"),
        ]

    def __str__(self) -> str:
        return f"PerfilComposicaoPreco(item={self.item_servico_id})"


class FaixaAprovacaoDesconto(models.Model):
    """Faixa de aprovação de desconto por tenant (D-PRC-3).

    Replace-all atômico sob advisory lock 880_404 por tenant (TL-PRC-16).
    Conjunto contíguo 0..100 sem buraco nem sobreposição — validado no
    domínio via `validar_faixas_contiguas` (INV-PRC-FAIXAS-CONTIGUAS).
    `versao_n` densa (incrementa em replace-all); `hash_conjunto` = hash
    canônico ADR-0029 do conjunto completo (fingerprint de versão).
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, serialize=False)
    tenant = models.ForeignKey(
        "tenant.tenant", on_delete=models.PROTECT, related_name="faixas_aprovacao_desconto"
    )
    pct_de = models.DecimalField(
        max_digits=5, decimal_places=2,
        help_text="Limite inferior da faixa % (half-open [pct_de, pct_ate)).",
    )
    pct_ate = models.DecimalField(
        max_digits=5, decimal_places=2,
        help_text="Limite superior da faixa % (half-open [pct_de, pct_ate)).",
    )
    alcada = models.CharField(
        max_length=10,
        choices=_choices(Alcada),
        help_text="livre|gerente|dono — alçada exigida nesta faixa.",
    )
    versao_n = models.IntegerField(
        help_text="Versão densa do conjunto de faixas (incrementa em replace-all)."
    )
    hash_conjunto = models.CharField(
        max_length=200,
        help_text="Hash canônico ADR-0029 do conjunto completo de faixas (fingerprint).",
    )
    # lgpd-base: pseudônimo art. 12 LGPD
    criado_por = models.UUIDField(
        help_text="Pseudônimo art. 12 LGPD."
    )
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "faixa_aprovacao_desconto"
        verbose_name = "Faixa de aprovação de desconto"
        verbose_name_plural = "Faixas de aprovação de desconto"
        indexes = [
            models.Index(fields=["tenant", "versao_n"], name="ix_prc_faixa_versao"),
        ]

    def __str__(self) -> str:
        return f"FaixaAprovacaoDesconto({self.pct_de}%..{self.pct_ate}% {self.alcada})"


class PedidoAprovacaoDesconto(models.Model):
    """Pedido de aprovação de desconto WORM one-shot (D-PRC-14 — INV-PRC-APROVACAO-ONE-SHOT).

    Estado SOLICITADO→APROVADO|NEGADO via trigger (nunca volta atrás).
    Campos probatórios pós-decisão congelados por trigger (trigger 0003).
    CHECK `decisor_id != solicitante_id` (INV-PRC-APROVACAO-INDEPENDENTE).
    `fingerprint_calculo`: binding aprovação↔cálculo (D-PRC-14).
    `justificativa_hash`: hash ADR-0029+HMAC-tenant (texto cru em tabela-par D-PRC-15).
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, serialize=False)
    tenant = models.ForeignKey(
        "tenant.tenant", on_delete=models.PROTECT, related_name="pedidos_aprovacao_desconto"
    )
    contexto_tipo = models.CharField(
        max_length=10,
        choices=_choices(ContextoTipo),
        help_text="orcamento|os|avulso — contexto de uso do pedido (D-PRC-14).",
    )
    contexto_id = models.UUIDField(
        null=True, blank=True,
        help_text="ID do documento consumidor (NULL = AVULSO; FK aditiva quando módulo existir).",
    )
    pct_solicitado = models.DecimalField(
        max_digits=5, decimal_places=2,
        help_text="Percentual de desconto solicitado (0..100).",
    )
    cortesia = models.BooleanField(
        default=False,
        help_text="True quando pct_solicitado == 100 (alçada DONO obrigatória — D-PRC-13).",
    )
    alcada_exigida = models.CharField(
        max_length=10,
        choices=_choices(Alcada),
        help_text="Alçada exigida para aprovação desta faixa.",
    )
    fingerprint_calculo = models.CharField(
        max_length=200,
        help_text="Hash canônico ADR-0029 de (entradas+refs+pct) — binding aprovação↔cálculo.",
    )
    estado = models.CharField(
        max_length=12,
        choices=_choices(EstadoPedido),
        default=EstadoPedido.SOLICITADO.value,
        help_text="solicitado|aprovado|negado — one-shot via trigger (INV-PRC-APROVACAO-ONE-SHOT).",
    )
    # lgpd-base: pseudônimos art. 12 LGPD; eventos levam só hash
    solicitante_id = models.UUIDField(
        help_text="Quem solicitou o desconto (pseudônimo art. 12 LGPD)."
    )
    decisor_id = models.UUIDField(
        null=True, blank=True,
        help_text="Quem decidiu (preenchido na decisão; DEVE ser != solicitante — CHECK).",
    )
    snapshot_probatorio = models.TextField(
        help_text="JSON canônico ADR-0029 das entradas do cálculo (replay — AC-PRC-002-3).",
    )
    justificativa_hash = models.CharField(
        max_length=200, blank=True, default="",
        help_text="Hash ADR-0029+HMAC-tenant do texto (texto cru em JustificativaDecisaoDesconto).",
    )
    decidido_em = models.DateTimeField(
        null=True, blank=True,
        help_text="Timestamp da decisão (preenchido junto com decisor_id).",
    )
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "pedido_aprovacao_desconto"
        verbose_name = "Pedido de aprovação de desconto"
        verbose_name_plural = "Pedidos de aprovação de desconto"
        constraints = [
            models.CheckConstraint(
                check=~models.Q(decisor_id=models.F("solicitante_id"))
                | models.Q(decisor_id__isnull=True),
                name="ck_prc_pedido_decisor_independente",
            ),
        ]
        indexes = [
            models.Index(fields=["tenant", "estado"], name="ix_prc_pedido_estado"),
        ]

    def __str__(self) -> str:
        return f"PedidoAprovacaoDesconto({self.id} {self.estado})"


class JustificativaDecisaoDesconto(models.Model):
    """Tabela-par mutável com texto cru da justificativa (D-PRC-15 / ADV-PRC-01).

    Texto cru necessário para AC-PRC-004-3 (vendedor lê justificativa).
    Soft-delete ADR-0031 (TTL 5a — retenção comercial).
    `pedido` é 1:1 com PedidoAprovacaoDesconto.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, serialize=False)
    tenant = models.ForeignKey(
        "tenant.tenant", on_delete=models.PROTECT, related_name="justificativas_desconto"
    )
    pedido = models.OneToOneField(
        PedidoAprovacaoDesconto,
        on_delete=models.PROTECT,
        related_name="justificativa",
        help_text="1:1 com PedidoAprovacaoDesconto.",
    )
    texto = models.TextField(
        help_text="Texto cru da justificativa (AC-PRC-004-3 — exposição ao vendedor).",
    )
    deletado_em = models.DateTimeField(
        null=True, blank=True,
        help_text="Soft-delete ADR-0031 (TTL 5a — retenção comercial).",
    )
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "justificativa_decisao_desconto"
        verbose_name = "Justificativa de decisão de desconto"
        verbose_name_plural = "Justificativas de decisão de desconto"

    def __str__(self) -> str:
        return f"JustificativaDecisaoDesconto(pedido={self.pedido_id})"


class VinculoTabelaPrecoCliente(models.Model):
    """Vínculo cliente → tabela de preço específica (D-PRC-12).

    Resolve cliente→tabela DENTRO desta frente (zero retrofit de schema na PPS).
    UNIQUE parcial vigente por `(tenant, cliente_id)` WHERE vigencia_fim IS NULL
    AND revogado_em IS NULL — só 1 vínculo ativo por cliente (D-PRC-12).
    Consumer de `Cliente.Anonimizado` revoga o vínculo (ADR-0032).
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, serialize=False)
    tenant = models.ForeignKey(
        "tenant.tenant", on_delete=models.PROTECT, related_name="vinculos_tabela_preco_cliente"
    )
    tabela_id = models.UUIDField(
        help_text="FK→tabela_preco.id (PPS); sem FK Django pra evitar cross-app (ADR-0007).",
    )
    # lgpd-base: pseudônimo art. 12 LGPD; revogado quando Cliente.Anonimizado (ADR-0032)
    cliente_id = models.UUIDField(
        help_text="Pseudônimo art. 12 LGPD; revogado quando Cliente.Anonimizado (ADR-0032).",
    )
    vigencia_inicio = models.DateTimeField()
    vigencia_fim = models.DateTimeField(
        null=True, blank=True,
        help_text="One-shot NULL→data (encerramento).",
    )
    revogado_em = models.DateTimeField(
        null=True, blank=True,
        help_text="Revogado quando Cliente.Anonimizado (ADR-0032).",
    )
    motivo_revogacao = models.CharField(max_length=600, blank=True, default="")
    # lgpd-base: pseudônimo art. 12 LGPD
    criado_por = models.UUIDField(
        help_text="Pseudônimo art. 12 LGPD."
    )
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "vinculo_tabela_preco_cliente"
        verbose_name = "Vínculo tabela de preço ↔ cliente"
        verbose_name_plural = "Vínculos tabela de preço ↔ clientes"
        constraints = [
            models.UniqueConstraint(
                fields=("tenant", "cliente_id"),
                condition=models.Q(vigencia_fim__isnull=True, revogado_em__isnull=True),
                name="uq_prc_vinculo_cliente_vigente",
            ),
        ]
        indexes = [
            models.Index(fields=["tenant", "cliente_id"], name="ix_prc_vinculo_cliente"),
        ]

    def __str__(self) -> str:
        return f"VinculoTabelaPrecoCliente(cliente={self.cliente_id})"


class ParametrosPrecificacaoTenant(models.Model):
    """Parâmetros globais de precificação do tenant, versionados (D-PRC-9).

    Singleton por tenant no sentido de que o use case sempre cria nova versão
    (versao_n denso) — replay bit-a-bit exige referência a versão específica.
    `custo_km`, `taxa_parcelamento_mensal`, `pct_comissao_prevista`,
    `margem_alvo_default`, `margem_piso_default` nunca em claro em eventos
    (segredo comercial — INV-PRC-SEGREDO-LOG).
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, serialize=False)
    tenant = models.ForeignKey(
        "tenant.tenant", on_delete=models.PROTECT, related_name="parametros_precificacao"
    )
    versao_n = models.IntegerField(
        help_text="Versão densa por tenant (max+1 sob advisory lock 880_404)."
    )
    custo_km = models.DecimalField(
        max_digits=10, decimal_places=4,
        help_text="Custo por km de deslocamento (R$/km — US-PRC-006 simulação).",
    )
    taxa_parcelamento_mensal = models.DecimalField(
        max_digits=5, decimal_places=2,
        help_text="Taxa mensal de parcelamento % (US-PRC-006).",
    )
    pct_comissao_prevista = models.DecimalField(
        max_digits=5, decimal_places=2,
        help_text="Comissão prevista % sobre preço de venda (PREVISTA — GATE-PRC-COMISSAO-REAL).",
    )
    margem_alvo_default = models.DecimalField(
        max_digits=5, decimal_places=2,
        help_text="Margem alvo default % (para regras sem margem_alvo_pct explícita).",
    )
    margem_piso_default = models.DecimalField(
        max_digits=5, decimal_places=2,
        help_text="Margem piso default % (para regras sem margem_piso_pct explícita).",
    )
    # lgpd-base: pseudônimo art. 12 LGPD
    criado_por = models.UUIDField(
        help_text="Pseudônimo art. 12 LGPD."
    )
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "parametros_precificacao_tenant"
        verbose_name = "Parâmetros de precificação do tenant"
        verbose_name_plural = "Parâmetros de precificação dos tenants"
        constraints = [
            models.UniqueConstraint(
                fields=("tenant", "versao_n"), name="uq_prc_parametros_versao_n"
            ),
        ]
        indexes = [
            models.Index(fields=["tenant", "versao_n"], name="ix_prc_parametros_versao"),
        ]

    def __str__(self) -> str:
        return f"ParametrosPrecificacaoTenant(tenant={self.tenant_id} v{self.versao_n})"
