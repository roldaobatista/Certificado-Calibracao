# ruff: noqa: RUF012 — choices derivados de enum (list mutavel ok em Model)
"""Frente `produtos-pecas-servicos` — models Django (Fatia 1b, T-PPS-020).

5 tabelas: `item_catalogo`, `item_catalogo_versao`, `kit_composicao`,
`tabela_preco`, `linha_tabela_preco`. Choices 1:1 dos enums de domínio
(anti-drift). Domain NÃO importa Django (ADR-0007 — `mappers.py` converte).

Imutabilidade (ADR-0031/0081 — molde `Imposto` da frente #1):
- `item_catalogo_versao` (preço de LISTA) e `linha_tabela_preco` (preço de
  VENDA) = Padrão B WORM: campos probatórios imutáveis pós-INSERT (trigger
  0003), `vigencia_fim`/`revogado_em`+motivo one-shot, DELETE bloqueado
  (retenção 10a — CC art. 205, retencao-matriz). Corrigir = revogar+recriar
  (use case composto — D-PPS-8).
- `item_catalogo` (estrutural: controla_estoque/status) e `tabela_preco` =
  configuração mutável com auditoria (não-WORM).
- `kit_composicao` = mutável (recompor kit gera evento `Catalogo.KitAlterado`).

Schema-irmãos:
- 0001_initial: CreateModel ×5 + UNIQUEs (INV-PPS-CODIGO-UNICO; versao_n;
  eh_padrao parcial; kit filho único) + CHECKs preco>0 / quantidade>0.
- 0002_rls_policies: RLS pattern v2 (ADR-0002 §6) nas 5 tabelas.
- 0003_triggers_worm: imutabilidade versão+linha (INV-PPS-VERSAO-IMUTAVEL /
  INV-PPS-LINHA-IMUTAVEL) + block DELETE.
- 0004_exclusions: btree_gist não-sobreposição (versão por item; linha por
  tabela+item) WHERE revogado_em IS NULL.
- 0005_grants_app_user + 0006_seed_authz_catalogo.

LGPD: `criado_por` é pseudônimo (art. 12 — RAT-PPS-CRIADO-POR); eventos WORM
levam só o hash. `descricao`/`motivo` são texto livre — NUNCA cru em evento
(ADV-PPS-02; hash ADR-0029 na camada de eventos, Fatia 2).
"""

from __future__ import annotations

import uuid
from enum import Enum

from django.db import models

from src.domain.produtos_pecas_servicos.enums import (
    OrigemPreco,
    StatusItem,
    TipoItem,
)


def _choices(enum_cls: type[Enum]) -> list[tuple[str, str]]:
    """Choices (value, value) a partir do enum de domínio (1:1 anti-drift)."""
    return [(membro.value, str(membro.value)) for membro in enum_cls]


class ItemCatalogo(models.Model):
    """Agregado raiz do catálogo (US-CAT-001). INV-PPS-CODIGO-UNICO por tenant."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, serialize=False)
    tenant = models.ForeignKey(
        "tenant.tenant", on_delete=models.PROTECT, related_name="itens_catalogo"
    )
    codigo_interno = models.CharField(
        max_length=60, help_text="SKU canônico do tenant (imutável — trigger 0003 não cobre; ADR-0007 use case não expõe edição)."
    )
    tipo = models.CharField(
        max_length=10,
        choices=_choices(TipoItem),
        help_text="produto|peca|servico|kit — imutável. produto×peca são rótulos (TL-PPS-14).",
    )
    codigo_fabricante = models.CharField(
        max_length=60, blank=True, default="",
        help_text="Identifica produto, não pessoa (não-PII — ADV-PPS-09).",
    )
    controla_estoque = models.BooleanField(
        help_text=(
            "Flag ESTRUTURAL do item (TL-PPS-12 — não é atributo de versão). "
            "Saldo é do módulo Estoque (non-goal)."
        ),
    )
    status = models.CharField(
        max_length=10,
        choices=_choices(StatusItem),
        default=StatusItem.ATIVO.value,
        help_text="ativo|inativo (ADR-0031 — sem DELETE; AC-CAT-005-1).",
    )
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "item_catalogo"
        verbose_name = "Item de catálogo"
        verbose_name_plural = "Itens de catálogo"
        constraints = [
            models.UniqueConstraint(
                fields=("tenant", "codigo_interno"), name="uq_pps_item_codigo"
            ),
        ]
        indexes = [
            models.Index(fields=["tenant", "status"], name="ix_pps_item_status"),
        ]

    def __str__(self) -> str:
        return f"ItemCatalogo({self.codigo_interno} — {self.tipo})"


class ItemCatalogoVersao(models.Model):
    """Versão imutável de apresentação + preço de LISTA (INV-026 / INV-PPS-VERSAO-IMUTAVEL).

    `versao_n` denso por item (max+1 sob advisory lock 880_403 — TL-PPS-04).
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, serialize=False)
    tenant = models.ForeignKey(
        "tenant.tenant", on_delete=models.PROTECT, related_name="versoes_catalogo"
    )
    item = models.ForeignKey(ItemCatalogo, on_delete=models.PROTECT, related_name="versoes")
    versao_n = models.IntegerField(help_text="Denso por item: 1,2,3... (max+1 sob lock).")
    nome = models.CharField(max_length=200)
    descricao = models.TextField(
        blank=True, default="",
        help_text="Texto livre — em evento WORM vai HASHIFICADA (ADV-PPS-02).",
    )
    categoria = models.CharField(max_length=100, blank=True, default="")
    unidade_medida = models.CharField(
        max_length=20, help_text="Texto curto validado contra seed de UMs (TL-PPS-11)."
    )
    preco_padrao = models.DecimalField(
        max_digits=12, decimal_places=2,
        help_text="Preço de LISTA (ADR-0081) — VO Preco: escala 2, > 0 (CHECK).",
    )
    vigencia_inicio = models.DateTimeField()
    vigencia_fim = models.DateTimeField(
        null=True, blank=True, help_text="One-shot NULL→data (trigger 0003)."
    )
    revogado_em = models.DateTimeField(
        null=True, blank=True,
        help_text="One-shot — versão errada sai da exclusion e nunca resolve (lição M2).",
    )
    motivo_revogacao = models.CharField(max_length=200, blank=True, default="")
    criado_por = models.UUIDField(
        help_text="Pseudônimo art. 12 LGPD (RAT-PPS-CRIADO-POR); evento WORM leva só hash."
    )
    motivo = models.CharField(
        max_length=200, blank=True, default="",
        help_text="Texto livre — em evento WORM vai HASHIFICADO (ADV-PPS-02).",
    )
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "item_catalogo_versao"
        verbose_name = "Versão de item de catálogo"
        verbose_name_plural = "Versões de item de catálogo"
        constraints = [
            models.UniqueConstraint(
                fields=("tenant", "item", "versao_n"), name="uq_pps_versao_n"
            ),
            models.CheckConstraint(
                check=models.Q(preco_padrao__gt=0), name="ck_pps_versao_preco_positivo"
            ),
        ]
        indexes = [
            models.Index(fields=["tenant", "item"], name="ix_pps_versao_item"),
        ]

    def __str__(self) -> str:
        return f"ItemCatalogoVersao(item={self.item_id} v{self.versao_n})"


class KitComposicao(models.Model):
    """Parte de kit (US-CAT-003). Filho NUNCA é kit (INV-PPS-KIT-SEM-CICLO — use case);
    UM deriva da versão vigente do filho (TL-PPS-11 — sem coluna própria)."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, serialize=False)
    tenant = models.ForeignKey(
        "tenant.tenant", on_delete=models.PROTECT, related_name="kits_composicao"
    )
    kit_item = models.ForeignKey(
        ItemCatalogo, on_delete=models.PROTECT, related_name="composicao"
    )
    item_filho = models.ForeignKey(
        ItemCatalogo, on_delete=models.PROTECT, related_name="usado_em_kits"
    )
    quantidade = models.DecimalField(
        max_digits=12, decimal_places=3,
        help_text="Fracionária legítima (0.5 kg de solda) — > 0 (CHECK).",
    )
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "kit_composicao"
        verbose_name = "Composição de kit"
        verbose_name_plural = "Composições de kit"
        constraints = [
            models.UniqueConstraint(
                fields=("tenant", "kit_item", "item_filho"), name="uq_pps_kit_filho"
            ),
            models.CheckConstraint(
                check=models.Q(quantidade__gt=0), name="ck_pps_kit_qtd_positiva"
            ),
        ]

    def __str__(self) -> str:
        return f"KitComposicao(kit={self.kit_item_id} filho={self.item_filho_id})"


class TabelaPreco(models.Model):
    """Tabela de VENDA (ADR-0081). MVP: exatamente 1 padrão por tenant (UNIQUE
    parcial `eh_padrao` — D-PPS-3; schema já N-tabelas pra V2)."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, serialize=False)
    tenant = models.ForeignKey(
        "tenant.tenant", on_delete=models.PROTECT, related_name="tabelas_preco"
    )
    nome = models.CharField(max_length=120)
    descricao = models.TextField(blank=True, default="")
    eh_padrao = models.BooleanField(
        default=False, help_text="Única por tenant no MVP (UNIQUE parcial — molde INV-037)."
    )
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "tabela_preco"
        verbose_name = "Tabela de preço"
        verbose_name_plural = "Tabelas de preço"
        constraints = [
            models.UniqueConstraint(
                fields=("tenant",),
                condition=models.Q(eh_padrao=True),
                name="uq_pps_tabela_padrao",
            ),
        ]

    def __str__(self) -> str:
        return f"TabelaPreco({self.nome}{' — padrão' if self.eh_padrao else ''})"


class LinhaTabelaPreco(models.Model):
    """Preço de VENDA vigente por (tabela, item) — imutável molde Imposto
    (INV-PPS-LINHA-IMUTAVEL + INV-PPS-LINHA-SEM-SOBREPOSICAO). É o que a porta
    `preco_para_os` resolve fail-closed (422 sem linha — ADR-0081)."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, serialize=False)
    tenant = models.ForeignKey(
        "tenant.tenant", on_delete=models.PROTECT, related_name="linhas_tabela_preco"
    )
    tabela = models.ForeignKey(TabelaPreco, on_delete=models.PROTECT, related_name="linhas")
    item = models.ForeignKey(
        ItemCatalogo, on_delete=models.PROTECT, related_name="linhas_preco"
    )
    preco = models.DecimalField(
        max_digits=12, decimal_places=2,
        help_text="Preço de VENDA — > 0 (CHECK; 0 é sentinela da OS — TL-PPS-16).",
    )
    vigencia_inicio = models.DateTimeField()
    vigencia_fim = models.DateTimeField(null=True, blank=True)
    revogado_em = models.DateTimeField(null=True, blank=True)
    motivo_revogacao = models.CharField(max_length=200, blank=True, default="")
    origem_sugestao = models.CharField(
        max_length=12,
        choices=_choices(OrigemPreco),
        default=OrigemPreco.MANUAL.value,
        help_text="manual|soma_partes — origem do VALOR sugerido na criação (ADV-PPS-08).",
    )
    criado_por = models.UUIDField()
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "linha_tabela_preco"
        verbose_name = "Linha de tabela de preço"
        verbose_name_plural = "Linhas de tabela de preço"
        constraints = [
            models.CheckConstraint(
                check=models.Q(preco__gt=0), name="ck_pps_linha_preco_positivo"
            ),
        ]
        indexes = [
            models.Index(fields=["tenant", "tabela", "item"], name="ix_pps_linha_chave"),
        ]

    def __str__(self) -> str:
        return f"LinhaTabelaPreco(tabela={self.tabela_id} item={self.item_id})"
