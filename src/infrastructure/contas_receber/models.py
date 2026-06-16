# ruff: noqa: RUF012 — choices derivados de enum (list mutavel ok em Model)
"""Frente contas-receber — models Django (Fatia 1b, T-CR-020/021).

4 tabelas achatadas: `titulo_receber`, `parcela_titulo`, `pagamento_titulo`,
`override_bloqueio`. Espelham as entidades de domínio em
`src/domain/contas_receber/entities.py`. Choices 1:1 dos enums (anti-drift via
`_choices(enum)`). Domain NÃO importa Django — o mapper em `mappers.py` converte.

WORM / semântica de imutabilidade:
- `Titulo` — WORM Padrão B: block-delete + campos probatórios congelados (trigger
  0003); `estado`/timestamps/dados de cobrança MUTÁVEIS; `data_baixa` e `cancelado_em`
  ONE-SHOT NULL→valor (trigger 0003).
- `Pagamento` — INSERT-only PURO: block-update + block-delete (trigger 0003).
- `OverrideBloqueio` — INSERT-only PURO: block-update + block-delete (trigger 0003).
- `Parcela` — tabela operacional; sem WORM próprio (gerenciada junto do Titulo).

`perfil_no_evento` CHAR(1): snapshot do perfil do tenant na emissão (ADR-0067 §3
/ D-CR-6). Trigger fallback BEFORE INSERT em `Titulo` preenche via
`COALESCE(NEW.perfil_no_evento, current_setting('app.perfil_tenant'))` quando NULL
(R4); NUNCA sobrescreve valor já presente (INV-FIN-SNAPSHOT-PERFIL-001).

Schema-irmãos:
- 0001_initial: CreateModel + UNIQUE negócio + CHECK + índices.
- 0002_rls_policies: RLS pattern v2 (ADR-0002 §6).
- 0003_triggers_worm: WORM Título + INSERT-only Pagamento/Override + perfil fallback.
- 0004_grants_app_user: GRANT app_user.
- 0005_seed_authz: matriz papel × ação contas_receber.*.
"""

from __future__ import annotations

import uuid
from enum import Enum

from django.db import models

from src.domain.contas_receber.enums import (
    CategoriaReceita,
    EstadoTitulo,
    MeioCobranca,
    OrigemPagamento,
    OrigemTitulo,
)


def _choices(enum_cls: type[Enum]) -> list[tuple[str, str]]:
    """Choices (value, value) a partir do enum de domínio (1:1 anti-drift)."""
    return [(membro.value, str(membro.value)) for membro in enum_cls]


class Titulo(models.Model):
    """Título a receber — agregado raiz (D-CR-2 / spec §4). WORM Padrão B.

    Idempotência de negócio:
      - `(tenant, os_id_origem) WHERE estado != cancelado` (INV-CR-OS-TITULO-UNICO / R6).
      - `perfil_no_evento` imutável após INSERT (INV-FIN-SNAPSHOT-PERFIL-001 / D-CR-6).
      - `cliente_referencia_hash` + `cliente_key_id` (ADR-0032 / D-CR-16).

    Campos mutáveis (trigger 0003 permite):
      `estado`, `gateway_externo_id`, `linha_digitavel`, `qr_code`, `tx_id`,
      `data_baixa` (one-shot), `cancelado_em` (one-shot), `revision`, `atualizado_em`.

    `convenio_pix_id NOT NULL` CHECK quando `meio=pix_recorrente` (INV-FIN-GW-002).
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, serialize=False)
    tenant = models.ForeignKey(
        "tenant.tenant",
        on_delete=models.PROTECT,
        related_name="titulos_receber",
    )
    # --- cliente (ReferenciaPIIAnonimizavel — ADR-0032 / D-CR-16) ---
    cliente_atual_id = models.UUIDField(
        null=True,
        blank=True,
        help_text="FK lógica SET_NULL ao cliente (PII direta; zerada em anonimização).",
    )
    cliente_referencia_hash = models.CharField(
        max_length=80,
        help_text="HMAC do cliente — pseudônimo na trilha (ADR-0032). Imutável, NOT NULL.",
    )
    cliente_key_id = models.CharField(
        max_length=10,
        help_text="Versão da chave HMAC (ex: v1, v2 — ADR-0064 / rotação anual).",
    )
    # --- valor e datas ---
    valor_original = models.BigIntegerField(
        help_text="Valor original do título em centavos (Dinheiro). Imutável pos-INSERT.",
    )
    data_emissao = models.DateField(help_text="Data de emissão do título. Imutável.")
    data_vencimento = models.DateField(help_text="Data de vencimento original. Imutável.")
    data_baixa = models.DateField(
        null=True,
        blank=True,
        help_text="One-shot: NULL→data quando pago. Trigger 0003 bloqueia sobrescrita.",
    )
    # --- máquina de estados ---
    estado = models.CharField(
        max_length=20,
        choices=_choices(EstadoTitulo),
        help_text="Estado do título (D-CR-3). Mutável por transição válida.",
    )
    # --- meios e categoria ---
    meio = models.CharField(
        max_length=20,
        choices=_choices(MeioCobranca),
        help_text="Canal de cobrança (D-CR-7).",
    )
    categoria_receita = models.CharField(
        max_length=30,
        choices=_choices(CategoriaReceita),
        help_text="Categoria da receita — perfil-aware (D-CR-5 / INV-FIN-PERFIL-001). Imutável.",
    )
    # --- perfil snapshot (imutável — D-CR-6) ---
    perfil_no_evento = models.CharField(
        max_length=1,
        help_text=(
            "Snapshot CHAR(1) do perfil regulatório do tenant na emissão (ADR-0067 §3 / D-CR-6). "
            "Imutável. Trigger BEFORE INSERT preenche via COALESCE se NULL (R4)."
        ),
    )
    # --- origem ---
    origem = models.CharField(
        max_length=10,
        choices=_choices(OrigemTitulo),
        help_text="Fato gerador do título (D-CR-12). Imutável.",
    )
    os_id_origem = models.UUIDField(
        null=True,
        blank=True,
        help_text="OS que originou este título (gatilho canônico — D-CR-12). Imutável.",
    )
    nfse_id_origem = models.UUIDField(
        null=True,
        blank=True,
        help_text="NF-e de origem (GATE-CR-NFSE — Wave B). Imutável.",
    )
    # --- gateway ---
    gateway_externo_id = models.CharField(
        max_length=120,
        blank=True,
        default="",
        help_text="ID no gateway (NOT NULL ⟺ cobrança emitida — derivado, não estado). Mutável.",
    )
    convenio_pix_id = models.CharField(
        max_length=120,
        blank=True,
        default="",
        help_text="Convênio PIX recorrente (NOT NULL obrigatório se meio=pix_recorrente — INV-FIN-GW-002).",
    )
    linha_digitavel = models.CharField(
        max_length=200,
        blank=True,
        default="",
        help_text="Linha digitável do boleto. Mutável.",
    )
    qr_code = models.TextField(
        blank=True,
        default="",
        help_text="QR code do PIX (payload). Mutável.",
    )
    tx_id = models.CharField(
        max_length=120,
        blank=True,
        default="",
        help_text="TxID do PIX direto. Mutável.",
    )
    # --- juros / desconto ---
    desconto_pontualidade_pct = models.IntegerField(
        null=True,
        blank=True,
        help_text="Percentual de desconto por pontualidade (bps 0-10000). Imutável.",
    )
    numero_sequencial_tenant = models.BigIntegerField(
        null=True,
        blank=True,
        help_text="Numeração GAP_LESS via SerieDocumento (D-CR-18). NULL = não exigida.",
    )
    # --- controle ---
    # vigencia-canonica: skip -- Titulo nao tem janela de vigencia; cancelado_em e transicao one-shot da maquina de estados (estado=cancelado), nao revogado_em ADR-0030 (molde fiscal/OS)
    cancelado_em = models.DateTimeField(
        null=True,
        blank=True,
        help_text="One-shot: NULL→datetime quando cancelado. Trigger 0003 bloqueia sobrescrita.",
    )
    revision = models.IntegerField(
        default=0,
        help_text="Contador de transições (observabilidade / OCC). Bumpa por F('revision')+1.",
    )
    criado_em = models.DateTimeField(auto_now_add=True, db_index=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "titulo_receber"
        verbose_name = "Título a Receber"
        verbose_name_plural = "Títulos a Receber"
        ordering = ["-criado_em"]
        constraints = [
            # R6 / INV-CR-OS-TITULO-UNICO: 1 OS → 1 título ativo
            models.UniqueConstraint(
                fields=["tenant", "os_id_origem"],
                condition=~models.Q(estado="cancelado"),
                name="uq_cr_titulo_os_ativo",
            ),
            # INV-FIN-GW-002: pix_recorrente exige convenio_pix_id
            models.CheckConstraint(
                condition=(~models.Q(meio="pix_recorrente") | ~models.Q(convenio_pix_id="")),
                name="chk_cr_titulo_pix_recorrente_convenio",
            ),
        ]
        indexes = [
            models.Index(fields=["tenant", "estado"], name="cr_titulo_tenant_estado_idx"),
            models.Index(fields=["tenant", "os_id_origem"], name="cr_titulo_tenant_os_idx"),
            models.Index(
                fields=["tenant", "cliente_atual_id"], name="cr_titulo_tenant_cliente_idx"
            ),
            models.Index(fields=["tenant", "data_vencimento"], name="cr_titulo_vencimento_idx"),
        ]

    def __str__(self) -> str:
        return f"Titulo({self.id} — {self.estado})"


class Parcela(models.Model):
    """Sub-entidade de parcelamento simples (D-CR-15 / spec §4).

    N parcelas iguais emitidas junto com o título.
    Baixa parcial com título sucessor = Wave B.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, serialize=False)
    titulo = models.ForeignKey(
        Titulo,
        on_delete=models.PROTECT,
        related_name="parcelas",
    )
    tenant = models.ForeignKey(
        "tenant.tenant",
        on_delete=models.PROTECT,
        related_name="parcelas_titulo",
    )
    numero = models.IntegerField(help_text="Número 1-based da parcela.")
    valor = models.BigIntegerField(help_text="Valor da parcela em centavos.")
    vencimento = models.DateField()
    status = models.CharField(
        max_length=20,
        default="aberta",
        help_text="aberta | paga | cancelada.",
    )
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "parcela_titulo"
        verbose_name = "Parcela de Título"
        verbose_name_plural = "Parcelas de Título"
        ordering = ["numero"]
        constraints = [
            models.UniqueConstraint(
                fields=["titulo", "numero"],
                name="uq_cr_parcela_titulo_numero",
            ),
        ]
        indexes = [
            models.Index(fields=["tenant", "titulo"], name="cr_parcela_tenant_titulo_idx"),
        ]

    def __str__(self) -> str:
        return f"Parcela({self.titulo_id} #{self.numero})"


class Pagamento(models.Model):
    """Evento de pagamento INSERT-only (INV-CR-PAGAMENTO-WORM / D-CR-8 / spec §4).

    Imutável via trigger block-update + block-delete (0003 — Padrão B INSERT-only).
    `gateway_event_id` para idempotência de webhook (INV-FIN-GW-001 / R10).
    `valor_atualizado_snapshot_em_pagamento` = M-FIN-002 (valor com juros/multa
    calculado por `calcular_valor_atualizado` no momento da baixa).
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, serialize=False)
    titulo = models.ForeignKey(
        Titulo,
        on_delete=models.PROTECT,
        related_name="pagamentos",
    )
    tenant = models.ForeignKey(
        "tenant.tenant",
        on_delete=models.PROTECT,
        related_name="pagamentos_titulo",
    )
    valor = models.BigIntegerField(help_text="Valor efetivamente pago (centavos).")
    data = models.DateField(help_text="Data do pagamento.")
    origem = models.CharField(
        max_length=20,
        choices=_choices(OrigemPagamento),
        help_text="Como o pagamento foi confirmado (D-CR-8).",
    )
    valor_atualizado_snapshot_em_pagamento = models.BigIntegerField(
        help_text="Snapshot do valor atualizado (com juros/multa) na data da baixa (M-FIN-002).",
    )
    gateway_event_id = models.CharField(
        max_length=120,
        blank=True,
        default="",
        help_text="ID do evento de webhook do gateway (idempotência — INV-FIN-GW-001).",
    )
    comprovante_url = models.URLField(
        blank=True,
        default="",
        help_text="URL do comprovante (baixa manual ou PIX). Sem PII do pagador (D-CR-19).",
    )
    criado_em = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = "pagamento_titulo"
        verbose_name = "Pagamento de Título"
        verbose_name_plural = "Pagamentos de Título"
        ordering = ["criado_em"]
        constraints = [
            # INV-FIN-GW-001 (P9 MÉDIO-1 idempotência): idempotência de webhook RESISTENTE A
            # CORRIDA — 2 webhooks paralelos com o mesmo gateway_event_id não duplicam o
            # Pagamento WORM (o check `existe_gateway_event` sozinho é TOCTOU sob READ COMMITTED).
            # Parcial: pagamentos manuais (gateway_event_id="") ficam de fora.
            models.UniqueConstraint(
                fields=["tenant", "gateway_event_id"],
                condition=~models.Q(gateway_event_id=""),
                name="uq_cr_pagamento_gateway_event",
            ),
        ]
        indexes = [
            models.Index(fields=["tenant", "titulo"], name="cr_pagamento_tenant_titulo_idx"),
            models.Index(fields=["gateway_event_id"], name="cr_pagamento_gw_event_idx"),
        ]

    def __str__(self) -> str:
        return f"Pagamento({self.titulo_id} — {self.valor}c)"


class OverrideBloqueio(models.Model):
    """Override de bloqueio de inadimplência — WORM Padrão B INSERT-only (D-CR-10 / spec §4).

    Exige papel `gerente_financeiro`/`admin_tenant`.
    `justificativa` ≥100 chars + filtro anti-PII (INV-CR-OVERRIDE-ANTI-PII / D-CR-20).
    `novo_prazo_max_dias` ≤90 (AC-CR-010-5).
    `a3_signature_id` = referência Wave A (A3 real = GATE-CR-A3).
    Limite 5%/mês dos bloqueios por tenant (use case — R-CR-NOVO-4).
    Retenção 5a (ato gerencial/fiscal — D-CR-20).
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, serialize=False)
    titulo = models.ForeignKey(
        Titulo,
        on_delete=models.PROTECT,
        related_name="overrides_bloqueio",
    )
    tenant = models.ForeignKey(
        "tenant.tenant",
        on_delete=models.PROTECT,
        related_name="overrides_bloqueio",
    )
    cliente_id = models.UUIDField(
        help_text="ID concreto do cliente no momento (não hash — OverrideBloqueio é ato gerencial).",
    )
    novo_prazo_max_dias = models.IntegerField(
        help_text="Novo prazo máximo de bloqueio em dias (≤90 — AC-CR-010-5).",
    )
    justificativa = models.TextField(
        help_text="Justificativa textual ≥100 chars + filtro anti-PII (INV-CR-OVERRIDE-ANTI-PII).",
    )
    a3_signature_id = models.CharField(
        max_length=200,
        help_text="Referência da assinatura A3 (stub Wave A — verificação real = GATE-CR-A3).",
    )
    usuario_id = models.UUIDField(
        help_text="ID do usuário que executou o override (papel gerente).",
    )
    perfil_no_evento = models.CharField(
        max_length=1,
        help_text="Snapshot CHAR(1) do perfil do tenant no momento do override (D-CR-6).",
    )
    criado_em = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = "override_bloqueio"
        verbose_name = "Override de Bloqueio"
        verbose_name_plural = "Overrides de Bloqueio"
        ordering = ["criado_em"]
        indexes = [
            models.Index(fields=["tenant", "titulo"], name="cr_override_tenant_titulo_idx"),
            models.Index(fields=["tenant", "criado_em"], name="cr_override_tenant_criado_idx"),
        ]

    def __str__(self) -> str:
        return f"OverrideBloqueio({self.titulo_id} — {self.novo_prazo_max_dias}d)"


class NotificacaoInadimplencia(models.Model):
    """Prova de envio de aviso de inadimplência D+30/D+45 (Fatia 3b-3 — T-CR-044b).

    INSERT-only (block-update + block-delete — trigger 0007 / ADR-0031 Padrão B).
    Duas finalidades (parecer advogado Caminho C):
      1. **Prova de cumprimento CDC** (aviso prévio enviado) — retenção 5a.
      2. Base do **FAIL-CLOSED** do bloqueio perfil A: o adapter de inadimplência só
         inclui o título na régua de bloqueio se há registro de aviso aqui (D-CR-9).

    Minimização (D-CR-19): NÃO grava o e-mail do cliente — só `cliente_referencia_hash`.
    `UNIQUE(tenant, titulo, marco)` = idempotência de envio (não reenvia o mesmo marco).
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, serialize=False)
    titulo = models.ForeignKey(
        Titulo,
        on_delete=models.PROTECT,
        related_name="notificacoes_inadimplencia",
    )
    tenant = models.ForeignKey(
        "tenant.tenant",
        on_delete=models.PROTECT,
        related_name="notificacoes_inadimplencia",
    )
    cliente_referencia_hash = models.CharField(
        max_length=80,
        help_text="HMAC do cliente (pseudônimo — D-CR-16). Sem e-mail/PII direta (D-CR-19).",
    )
    marco = models.CharField(
        max_length=3,
        help_text="Marco do aviso: 'D30' (prévio) | 'D45' (final). Imutável.",
    )
    dias_vencido = models.IntegerField(help_text="Dias em atraso no momento do aviso.")
    perfil_no_evento = models.CharField(
        max_length=1,
        help_text="Snapshot CHAR(1) do perfil do tenant no aviso (D-CR-6). Wave A: só 'A'.",
    )
    canal = models.CharField(
        max_length=20,
        default="email_cliente",
        help_text="Canal do aviso (email_cliente). Aviso ao admin = evento, não e-mail.",
    )
    enviada_em = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = "notificacao_inadimplencia"
        verbose_name = "Notificação de Inadimplência"
        verbose_name_plural = "Notificações de Inadimplência"
        ordering = ["enviada_em"]
        constraints = [
            # Idempotência de envio: 1 aviso por título por marco.
            models.UniqueConstraint(
                fields=["tenant", "titulo", "marco"],
                name="uq_cr_notif_inad_titulo_marco",
            ),
        ]
        indexes = [
            models.Index(fields=["tenant", "titulo"], name="cr_notif_inad_tenant_tit_idx"),
        ]

    def __str__(self) -> str:
        return f"NotificacaoInadimplencia({self.titulo_id} — {self.marco})"
