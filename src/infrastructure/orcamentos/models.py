"""Models do modulo Orcamentos — T-ORC-020 (Fatia 1b).

7 tabelas (spec §4 / plan §3):
  orcamento                  — agregado raiz (estado D-ORC-3 + totais Dinheiro)
  versao_orcamento           — Padrao B imutavel (V1 snapshot ao enviar — D-ORC-8)
  item_orcamento             — item do orcamento (carimbo PrecoResolvido SEM margem)
  orcamento_link_publico     — token opaco de aprovacao (1 ativo — INV-ORC-LINK-TOKEN)
  orcamento_aprovacao        — WORM Padrao B (aceite rico + PII HMAC — INV-ORC-APROVACAO-WORM)
  analise_critica_orcamento  — WORM Padrao B (probatorio cl. 7.1 — D-ORC-15)
  template_orcamento         — Padrao C soft-delete (D-ORC-13)

Decisoes de schema (Opus — Fatia 1b; reconciliacao P8):
  - VALORES MONETARIOS: o dominio usa o VO `Dinheiro` (centavos+moeda). Persistimos
    como `*_centavos` (BigIntegerField) + `moeda` (CharField). O mapper reconstroi o VO.
  - `preco_resolvido`: jsonb (snapshot probatorio completo do `PrecoResolvido` — D-ORC-1/
    INV-026). NUNCA margem/custo no item (INV-ORC-MARGEM-OFF).
  - CLIENTE via ReferenciaPIIAnonimizavel (ADR-0032 / D-ORC-4): `cliente_atual_id`
    (UUIDField, SET_NULL LOGICO via consumer `Cliente.Anonimizado` — molde aceite_atividade
    NAO usa FK fisica cross-modulo) + `cliente_referencia_hash` (HMAC NOT NULL) + `cliente_key_id`.
  - `item_orcamento.versao` FK NOT NULL (espelha a entidade ItemOrcamento.versao_id, que
    NAO tem orcamento_id): a `VersaoOrcamento` nasce na CRIACAO do orcamento com snapshot={}
    (versao corrente de trabalho) e e CONGELADA ao enviar (snapshot preenchido one-shot —
    trigger 0003). Itens em rascunho sao mutaveis (sem WORM); o orcamento deriva via
    `versao.orcamento`. A semantica criacao-da-versao se confirma nos use cases (Fatia 2).

Multi-tenancy: todas as tabelas tem `tenant` FK NOT NULL; RLS v2 na migration 0002.
WORM: triggers anti-mutacao na migration 0003 (aprovacao/analise/versao). Constraints
(partial unique link, unique numero/tenant, CHECK estado terminal, CHECK bifurcacao) na 0004.

Refs: spec §4; D-ORC-1/2/3/4/8/13/15; INV-ORC-*; plan §3.
"""

from __future__ import annotations

import uuid

from django.db import models

from src.domain.comercial.orcamentos.enums import (
    CanalAprovacao,
    EstadoOrcamento,
    TipoAtividadeAlvo,
    VeredictoAnaliseCritica,
)
from src.infrastructure.tenant.models import Tenant

# Choices derivadas dos enums do dominio (fonte unica — evita drift dominio<->schema).
_ESTADO_CHOICES = [(e.value, e.value) for e in EstadoOrcamento]
_CANAL_CHOICES = [(c.value, c.value) for c in CanalAprovacao]
_TIPO_ATIVIDADE_ALVO_CHOICES = [(t.value, t.value) for t in TipoAtividadeAlvo]
_VEREDITO_CHOICES = [(v.value, v.value) for v in VeredictoAnaliseCritica]


# =====================================================================
# AGREGADO RAIZ — orcamento
# =====================================================================


class Orcamento(models.Model):
    """Agregado raiz do modulo (spec §4 / D-ORC-2).

    `estado` segue a maquina D-ORC-3 (dominio `transicoes.py`). Totais em
    CENTAVOS (VO Dinheiro). `validade_inicio`/`validade_fim` reconstroem a
    `JanelaVigencia` (ADR-0030) que decide expiracao.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.PROTECT, related_name="orcamentos")

    # Cliente via ReferenciaPIIAnonimizavel (D-ORC-4 / ADR-0032).
    cliente_atual_id = models.UUIDField(
        null=True,
        blank=True,
        db_index=True,
        help_text=(
            "UUID do cliente. NULL apos anonimizacao (SET_NULL logico via consumer "
            "Cliente.Anonimizado). Sem FK fisica cross-modulo — molde aceite_atividade."
        ),
    )
    cliente_referencia_hash = models.CharField(
        max_length=128,
        help_text="HMAC-SHA256 do cliente_id original (ADR-0032). NOT NULL — preservado pos-anonimizacao.",
    )
    cliente_key_id = models.CharField(
        max_length=40, help_text="Versao da chave KMS (rotacao) — formato vN."
    )

    numero = models.PositiveIntegerField(
        help_text="Sequencial gap-less por tenant (D-ORC-18 / SerieDocumento). UNIQUE(tenant, numero) na 0004."
    )
    estado = models.CharField(
        max_length=30,
        choices=_ESTADO_CHOICES,
        default=EstadoOrcamento.RASCUNHO.value,
        db_index=True,
        help_text="Maquina D-ORC-3. `convertido` terminal (INV-ORC-CONVERTIDO-TERMINAL — CHECK na 0004).",
    )

    # JanelaVigencia (ADR-0030) — validade do orcamento.
    validade_inicio = models.DateTimeField(
        help_text="Inicio da vigencia da proposta (normalmente = criado_em)."
    )
    validade_fim = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Fim da vigencia (validade_ate). NULL = sem expiracao automatica.",
    )

    # Totais como CENTAVOS (VO Dinheiro — D-ORC-1).
    moeda = models.CharField(max_length=3, default="BRL", help_text="ISO 4217. MVP-1: BRL only.")
    total_bruto_centavos = models.BigIntegerField(default=0)
    descontos_centavos = models.BigIntegerField(default=0)
    impostos_centavos = models.BigIntegerField(default=0)
    liquido_centavos = models.BigIntegerField(default=0)
    comissao_prevista_centavos = models.BigIntegerField(
        default=0,
        help_text="Visivel SO com `orcamento.ver_margem` (choke-point server-side — INV-ORC-MARGEM-OFF).",
    )

    condicoes_pagamento = models.JSONField(
        default=dict, help_text="Serializacao do VO CondicoesPagamento (parcelas/forma/dias)."
    )

    template_id = models.UUIDField(null=True, blank=True)
    tabela_preco_id = models.UUIDField(null=True, blank=True)
    observacoes = models.TextField(blank=True)
    responsavel_id = models.UUIDField(
        null=True, blank=True, help_text="user_id do responsavel comercial."
    )
    chamado_origem_id = models.UUIDField(null=True, blank=True)

    criado_em = models.DateTimeField(auto_now_add=True)
    criado_por = models.UUIDField(help_text="user_id de quem criou.")
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = "orcamentos"
        db_table = "orcamento"
        verbose_name = "Orcamento"
        verbose_name_plural = "Orcamentos"
        ordering = ["-criado_em"]
        indexes = [
            models.Index(fields=["tenant", "estado"], name="ix_orc_tenant_estado"),
            models.Index(fields=["tenant", "cliente_atual_id"], name="ix_orc_tenant_cliente"),
            models.Index(fields=["tenant", "-criado_em"], name="ix_orc_tenant_criado"),
        ]

    def __str__(self) -> str:
        return f"Orcamento #{self.numero} ({self.estado})"


# =====================================================================
# VERSAO — versao_orcamento (Padrao B imutavel)
# =====================================================================


class VersaoOrcamento(models.Model):
    """Versao do orcamento — congelamento probatorio (D-ORC-8 / Padrao B apos congelar).

    A versao corrente nasce na CRIACAO do orcamento com `snapshot={}` (working-set
    mutavel) e e CONGELADA ao enviar: o `snapshot` (jsonb) e preenchido UMA vez (foto
    de itens+condicoes+totais). O trigger WORM (0003) permite o preenchimento one-shot
    `{} -> conteudo` + setar `revogado_em`, mas bloqueia re-edicao do snapshot ja
    congelado, mudanca do nucleo (orcamento/tenant/numero_versao/criada_por) e DELETE.
    V2/V3 + comparacao = Wave B (US-ORC-003).
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    orcamento = models.ForeignKey(Orcamento, on_delete=models.PROTECT, related_name="versoes")
    tenant = models.ForeignKey(Tenant, on_delete=models.PROTECT, related_name="orcamento_versoes")
    numero_versao = models.PositiveIntegerField(help_text="Comeca em 1.")
    snapshot = models.JSONField(
        help_text="Foto congelada (itens+condicoes+totais). Imutavel pos-INSERT (trigger WORM)."
    )
    criada_em = models.DateTimeField(auto_now_add=True)
    criada_por = models.UUIDField()

    # Revogacao (Wave B — soft-revoke; nao mutado em Wave A).
    revogado_em = models.DateTimeField(null=True, blank=True)
    motivo_revogacao = models.CharField(max_length=200, blank=True)

    class Meta:
        app_label = "orcamentos"
        db_table = "versao_orcamento"
        verbose_name = "Versao do orcamento"
        verbose_name_plural = "Versoes do orcamento"
        ordering = ["orcamento", "numero_versao"]
        constraints = [
            models.UniqueConstraint(
                fields=["orcamento", "numero_versao"], name="uq_versao_orc_numero"
            ),
        ]
        indexes = [
            models.Index(fields=["tenant", "orcamento"], name="ix_versao_tenant_orc"),
        ]

    def __str__(self) -> str:
        return f"V{self.numero_versao} de {self.orcamento_id}"


# =====================================================================
# ITEM — item_orcamento
# =====================================================================


class ItemOrcamento(models.Model):
    """Item do orcamento (spec §4 / INV-ORC-EQUIP-ITEM / INV-ORC-MARGEM-OFF).

    Bifurcacao (CHECK na 0004):
      - `equipamento_id` preenchido + `tipo_atividade_alvo` != ''  -> item tecnico (vira AtividadeDaOS)
      - `equipamento_id` NULL + `tipo_atividade_alvo` == ''        -> item comercial (vira ItemComercialOS)

    INV-ORC-MARGEM-OFF: NUNCA ha coluna de margem/custo/comissao. O carimbo de
    preco e `preco_resolvido` (jsonb — snapshot probatorio completo do PrecoResolvido).
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    # Item pertence sempre a uma versao (espelha a entidade ItemOrcamento.versao_id).
    # A versao corrente nasce na criacao do orcamento (snapshot={}); o orcamento deriva
    # via versao.orcamento. Item mutavel em rascunho (sem WORM).
    versao = models.ForeignKey(VersaoOrcamento, on_delete=models.PROTECT, related_name="itens")
    tenant = models.ForeignKey(Tenant, on_delete=models.PROTECT, related_name="orcamento_itens")

    catalogo_item_id = models.UUIDField(
        db_index=True, help_text="FK logica ao catalogo (produtos_pecas_servicos)."
    )
    sequencia = models.PositiveIntegerField(
        help_text="1-based; rastro item<->atividade (D-ORC-11)."
    )

    # Carimbo de preco IMUTAVEL (D-ORC-1 / INV-ORC-PRECO-001) — snapshot probatorio.
    preco_resolvido = models.JSONField(
        help_text="Snapshot do PrecoResolvido (item_versao_n, linha_tabela_id, tabela_id, preco, "
        "data_referencia, origem_preco). NUNCA margem/custo (INV-ORC-MARGEM-OFF)."
    )

    moeda = models.CharField(max_length=3, default="BRL")
    preco_final_centavos = models.BigIntegerField(
        help_text="Preco unitario final apos desconto (centavos)."
    )
    desconto_pct = models.DecimalField(
        max_digits=5, decimal_places=2, default=0, help_text="Percentual 0..100."
    )
    desconto_valor_centavos = models.BigIntegerField(default=0)
    quantidade = models.DecimalField(
        max_digits=12, decimal_places=3, default=1, help_text="Pode ser fracionaria."
    )
    total_centavos = models.BigIntegerField(help_text="preco_final * quantidade (centavos).")

    semaforo = models.CharField(
        max_length=10, help_text="verde | amarelo | vermelho (precificacao)."
    )
    descricao_snapshot = models.CharField(max_length=300, help_text="Descricao do item congelada.")

    # Bifurcacao tecnico x comercial (INV-ORC-EQUIP-ITEM / D-ORC-16).
    equipamento_id = models.UUIDField(
        null=True,
        blank=True,
        db_index=True,
        help_text="Preenchido em itens tecnicos (calibracao/manutencao/...). NULL em itens comerciais.",
    )
    tipo_atividade_alvo = models.CharField(
        max_length=20,
        blank=True,
        choices=_TIPO_ATIVIDADE_ALVO_CHOICES,
        help_text="Tipo de atividade (itens tecnicos). Vazio em itens comerciais.",
    )
    tipo_item_comercial = models.CharField(
        max_length=20,
        blank=True,
        help_text="Tipo do item comercial (deslocamento/taxa/outro) quando equipamento_id is NULL.",
    )

    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = "orcamentos"
        db_table = "item_orcamento"
        verbose_name = "Item do orcamento"
        verbose_name_plural = "Itens do orcamento"
        ordering = ["versao", "sequencia"]
        indexes = [
            models.Index(fields=["tenant", "versao"], name="ix_item_tenant_versao"),
            models.Index(fields=["versao", "sequencia"], name="ix_item_versao_seq"),
        ]

    def __str__(self) -> str:
        return f"Item {self.sequencia} (versao {self.versao_id})"


# =====================================================================
# LINK PUBLICO — orcamento_link_publico
# =====================================================================


class LinkPublico(models.Model):
    """Token opaco de aprovacao publica (D-ORC-7/19 / INV-ORC-LINK-TOKEN).

    1 link ativo por orcamento (partial unique WHERE revogado_em IS NULL — 0004).
    Token = secrets.token_urlsafe(32) >=128 bits (ADV-ORC-08a). Lookup por token
    resolve tenant SEM RLS no repository (D-ORC-19).
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    orcamento = models.ForeignKey(Orcamento, on_delete=models.PROTECT, related_name="links")
    tenant = models.ForeignKey(Tenant, on_delete=models.PROTECT, related_name="orcamento_links")
    token = models.CharField(
        max_length=128,
        unique=True,
        help_text="Opaco urlsafe >=128 bits. UNIQUE global (lookup rapido + colisao impossivel).",
    )
    expira_em = models.DateTimeField(help_text="Expiracao checada no GET e no POST (D-ORC-19).")
    criado_em = models.DateTimeField(auto_now_add=True)

    revogado_em = models.DateTimeField(null=True, blank=True)
    motivo_revogacao = models.CharField(max_length=200, blank=True)

    class Meta:
        app_label = "orcamentos"
        db_table = "orcamento_link_publico"
        verbose_name = "Link publico de orcamento"
        verbose_name_plural = "Links publicos de orcamento"
        ordering = ["-criado_em"]
        indexes = [
            models.Index(fields=["tenant", "orcamento"], name="ix_link_tenant_orc"),
        ]

    def __str__(self) -> str:
        status_ = "ativo" if self.revogado_em is None else "revogado"
        return f"Link {self.id} ({status_})"


# =====================================================================
# APROVACAO — orcamento_aprovacao (WORM Padrao B)
# =====================================================================


class Aprovacao(models.Model):
    """Registro imutavel de aprovacao (D-ORC-7 / INV-ORC-APROVACAO-WORM).

    WORM Padrao B: INSERT-only (trigger anti-mutacao na 0003). PII do aprovador
    em HMAC Wave A (D-ORC-17); exibicao do nome = GATE-ORC-KMS-APROVADOR.
    `lgpd_aceite_*` = prova rica do consentimento (ADV-ORC-04). `ressalvas_aceitas`
    = True quando analise critica `com_ressalva` e aprovador confirmou (cl. 7.1.1-d).
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    orcamento = models.ForeignKey(Orcamento, on_delete=models.PROTECT, related_name="aprovacoes")
    versao = models.ForeignKey(VersaoOrcamento, on_delete=models.PROTECT, related_name="aprovacoes")
    tenant = models.ForeignKey(
        Tenant, on_delete=models.PROTECT, related_name="orcamento_aprovacoes"
    )

    aprovado_em = models.DateTimeField(help_text="Timestamp server-side da aprovacao.")
    canal = models.CharField(max_length=20, choices=_CANAL_CHOICES)

    # PII do aprovador — HMAC Wave A (D-ORC-17).
    nome_aprovador_hash = models.CharField(max_length=128, help_text="HMAC(nome, chave_tenant).")
    email_aprovador_hash = models.CharField(max_length=128, help_text="HMAC(email, chave_tenant).")

    # Aceite LGPD rico (ADV-ORC-04 — nao boolean).
    lgpd_aceite_versao_termo = models.CharField(max_length=40, help_text='Ex.: "v2026-01".')
    lgpd_aceite_texto_hash = models.CharField(
        max_length=128, help_text="Hash do texto exibido (prova do consentido)."
    )

    # Forense.
    ip_hash = models.CharField(max_length=128, help_text="HMAC(ip_real, chave_servidor).")
    user_agent = models.CharField(max_length=512, blank=True)

    ressalvas_aceitas = models.BooleanField(
        default=False,
        help_text="True quando analise=com_ressalva e aprovador confirmou (cl. 7.1.1-d).",
    )
    aprovado_por = models.UUIDField(
        null=True, blank=True, help_text="user_id do aprovador interno; NULL em aprovacao publica."
    )

    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = "orcamentos"
        db_table = "orcamento_aprovacao"
        verbose_name = "Aprovacao de orcamento"
        verbose_name_plural = "Aprovacoes de orcamento"
        ordering = ["-criado_em"]
        indexes = [
            models.Index(fields=["tenant", "orcamento"], name="ix_aprov_tenant_orc"),
        ]

    def __str__(self) -> str:
        return f"Aprovacao {self.id} ({self.canal})"


# =====================================================================
# ANALISE CRITICA — analise_critica_orcamento (WORM Padrao B)
# =====================================================================


class AnaliseCriticaOrcamento(models.Model):
    """Registro imutavel da analise critica cl. 7.1 ISO 17025 (D-ORC-15).

    WORM Padrao B: INSERT-only (trigger anti-mutacao na 0003). `snapshot_hash`
    (canonicalizacao ADR-0029) e carimbado no envelope `orcamento.aprovado` e
    verificavel offline (INV-ORC-ANALISE-WORM). `itens_avaliados` = registro
    probatorio por item de calibracao (C1, cl. 7.1.1-a).
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    orcamento = models.ForeignKey(
        Orcamento, on_delete=models.PROTECT, related_name="analises_criticas"
    )
    versao = models.ForeignKey(
        VersaoOrcamento, on_delete=models.PROTECT, related_name="analises_criticas"
    )
    tenant = models.ForeignKey(Tenant, on_delete=models.PROTECT, related_name="orcamento_analises")

    perfil_no_evento = models.CharField(
        max_length=1, help_text="Snapshot do perfil no momento: A|B|C|D."
    )
    veredito = models.CharField(max_length=20, choices=_VEREDITO_CHOICES)
    norma_referencia = models.CharField(
        max_length=60, help_text='Ex.: "ISO/IEC 17025:2017 cl. 7.1.1" (C6).'
    )
    itens_avaliados = models.JSONField(
        help_text="Registro probatorio por item (C1): equipamento_id/grandeza/faixa/cmc/procedimento/ressalvas."
    )
    snapshot_hash = models.CharField(
        max_length=64, help_text="Canonicalizacao ADR-0029 — carimbado no envelope."
    )
    avaliada_em = models.DateTimeField(help_text="Server-side (nunca client-supplied).")
    avaliada_por = models.CharField(
        max_length=80, help_text='user_id str OU "SISTEMA/AUTO:<aprovacao_id>" (C5).'
    )

    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = "orcamentos"
        db_table = "analise_critica_orcamento"
        verbose_name = "Analise critica de orcamento"
        verbose_name_plural = "Analises criticas de orcamento"
        ordering = ["-criado_em"]
        indexes = [
            models.Index(fields=["tenant", "orcamento"], name="ix_analise_tenant_orc"),
        ]

    def __str__(self) -> str:
        return f"AnaliseCritica {self.id} ({self.veredito})"


# =====================================================================
# TEMPLATE — template_orcamento (Padrao C soft-delete)
# =====================================================================


class TemplateAtivosManager(models.Manager["Template"]):
    """Manager default — filtra soft-deleted (D-ORC-13 / Padrao C)."""

    def get_queryset(self) -> models.QuerySet[Template]:
        return super().get_queryset().filter(deletado_em__isnull=True)


class Template(models.Model):
    """Template de orcamento reutilizavel (D-ORC-13 / US-ORC-005).

    `selo_rbc=True` so pode ser salvo em perfil A (gate no hook/use case — D-ORC-13).
    Padrao C: `deletado_em` permite soft-delete sem perda de historico.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.PROTECT, related_name="orcamento_templates")
    nome = models.CharField(max_length=200)
    tipo = models.CharField(max_length=60, help_text='Ex.: "calibracao_balanca".')
    itens_default = models.JSONField(
        default=list, help_text="[{catalogo_item_id, quantidade, ...}]"
    )
    condicoes_default = models.JSONField(
        default=dict, help_text="Serializacao de CondicoesPagamento."
    )
    selo_rbc = models.BooleanField(default=False, help_text="True so em perfil A (gate D-ORC-13).")
    criado_em = models.DateTimeField(auto_now_add=True)
    criado_por = models.UUIDField()

    deletado_em = models.DateTimeField(null=True, blank=True, db_index=True)
    deletado_por = models.UUIDField(null=True, blank=True)

    # Ordem fields -> managers -> Meta (Django-canonica). noqa DJ012: quirk do ruff
    # com manager tipado generico (models.Manager["Template"]) que reporta falso
    # desvio de ordem mesmo com a ordem correta (mesmo padrao de clientes/models.py).
    objects = TemplateAtivosManager()
    all_objects = models.Manager()  # noqa: DJ012 -- all_objects expoe soft-deletados p/ auditoria

    class Meta:
        app_label = "orcamentos"
        db_table = "template_orcamento"
        verbose_name = "Template de orcamento"
        verbose_name_plural = "Templates de orcamento"
        ordering = ["nome"]
        indexes = [
            models.Index(fields=["tenant", "nome"], name="ix_template_tenant_nome"),
        ]

    def __str__(self) -> str:
        return f"Template {self.nome}"
