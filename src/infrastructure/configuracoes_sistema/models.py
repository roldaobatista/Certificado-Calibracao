# ruff: noqa: RUF012 — choices derivados de enum (list mutavel ok em Model)
"""Frente `configuracoes-sistema` — models Django (Fatia 1b, T-CFG-020).

5 tabelas: `empresa`, `filial`, `imposto`, `serie_documento` e
`numero_documento_reservado` (espelha `numero_certificado_reservado` do M8 —
motor de reserva gap-less REUSADO, não reescrito — TL-02/ADR-0080).
Choices 1:1 dos enums de domínio (anti-drift). Domain NÃO importa Django
(ADR-0007 — o mapper em `mappers.py` converte Model ↔ entidade).

Imutabilidade (ADR-0031):
- `Imposto` = linha de catálogo VERSIONADA por vigência (Padrão B — WORM):
  mudar alíquota = NOVA linha; trigger 0003 barra UPDATE de campo probatório
  (INV-CFG-IMPOSTO-IMUTAVEL) e DELETE físico (retenção fiscal 5a — ADV-05).
  `vigencia_fim` e `revogado_em` são one-shot (NULL→valor).
- `Empresa`/`Filial`/`SerieDocumento` = configuração mutável com auditoria
  (não-WORM); em `serie_documento` o trigger 0003 barra decremento de
  `proximo_numero` (INV-028) e mutação de tipo/prefixo/regime (ADR-0080 —
  regime é DERIVADO do tipo).
- `numero_documento_reservado` = reserva-TTL gap-less; triggers 0003 garantem
  consecutividade no INSERT, confirmação one-shot e DELETE só de reserva
  não-confirmada (INV-CFG-NUM-ATOMICA).

Schema-irmãos:
- 0001_initial: CreateModel ×5 + UNIQUEs (INV-036/037/028).
- 0002_rls_policies: RLS pattern v2 (ADR-0002 §6) nas 5 tabelas.
- 0003_triggers_worm: INV-028 + INV-CFG-IMPOSTO-IMUTAVEL + numeração gap-less.
- 0004_exclusion_imposto: btree_gist (INV-CFG-IMPOSTO-SEM-SOBREPOSICAO).
- 0005_grants_app_user + 0006_seed_authz_configuracoes.
"""

from __future__ import annotations

import uuid
from enum import Enum

from django.db import models

from src.domain.configuracoes_sistema.enums import (
    RegimeNumeracao,
    RegimeTributario,
    TipoDocumento,
    TipoImposto,
)


def _choices(enum_cls: type[Enum]) -> list[tuple[str, str]]:
    """Choices (value, value) a partir do enum de domínio (1:1 anti-drift)."""
    return [(membro.value, str(membro.value)) for membro in enum_cls]


class Empresa(models.Model):
    """Cadastro tributário do tenant (US-CFG-001). INV-036: CNPJ único por tenant.

    PII PJ (MEI = CPF embutido no CNPJ — nota LGPD ADV-06, base legal no RAT).
    Config mutável com auditoria via trilha central (D-CFG-7) — não-WORM.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, serialize=False)
    tenant = models.ForeignKey(
        "tenant.tenant", on_delete=models.PROTECT, related_name="empresas_config"
    )
    razao_social = models.CharField(max_length=200)
    cnpj = models.CharField(
        max_length=14,
        help_text="Normalizado pelo VO CNPJ (ADR-0017 — alfanumérico IN RFB 2.229/2024).",
    )
    regime_tributario = models.CharField(
        max_length=20,
        choices=_choices(RegimeTributario),
        help_text="Conjunto final exigível = validação contador/OAB pré-produção (D-CFG-9).",
    )
    inscricao_estadual = models.CharField(max_length=20, blank=True, default="")
    inscricao_municipal = models.CharField(max_length=20, blank=True, default="")
    endereco = models.TextField(blank=True, default="")
    logo_url = models.CharField(max_length=300, blank=True, default="")
    site = models.CharField(max_length=200, blank=True, default="")
    telefone = models.CharField(max_length=20, blank=True, default="")
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "empresa"
        verbose_name = "Empresa (cadastro tributário)"
        verbose_name_plural = "Empresas (cadastro tributário)"
        constraints = [
            models.UniqueConstraint(fields=("tenant", "cnpj"), name="uq_cfg_empresa_cnpj"),
        ]

    def __str__(self) -> str:
        return f"Empresa({self.razao_social} — {self.cnpj})"


class Filial(models.Model):
    """Filial de uma empresa (US-CFG-001). INV-037: exatamente 1 matriz.

    A "exatamente 1" tem duas metades: UNIQUE parcial `uq_cfg_filial_uma_matriz`
    (≤1 no banco) + `validar_uma_matriz` no domínio (≥1 quando há filiais).
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, serialize=False)
    tenant = models.ForeignKey(
        "tenant.tenant", on_delete=models.PROTECT, related_name="filiais_config"
    )
    empresa = models.ForeignKey(Empresa, on_delete=models.PROTECT, related_name="filiais")
    cnpj = models.CharField(
        max_length=14, help_text="CNPJ próprio da filial (AC-CFG-001-2; VO ADR-0017)."
    )
    nome = models.CharField(max_length=200)
    eh_matriz = models.BooleanField(
        default=False, help_text="Exatamente 1 por empresa (INV-037 — UNIQUE parcial)."
    )
    endereco = models.TextField(blank=True, default="")
    inscricao_estadual = models.CharField(max_length=20, blank=True, default="")
    inscricao_municipal = models.CharField(max_length=20, blank=True, default="")
    telefone = models.CharField(max_length=20, blank=True, default="")
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "filial"
        verbose_name = "Filial"
        verbose_name_plural = "Filiais"
        constraints = [
            models.UniqueConstraint(fields=("tenant", "cnpj"), name="uq_cfg_filial_cnpj"),
            models.UniqueConstraint(
                fields=("tenant", "empresa"),
                condition=models.Q(eh_matriz=True),
                name="uq_cfg_filial_uma_matriz",
            ),
        ]

    def __str__(self) -> str:
        return f"Filial({self.nome}{' — matriz' if self.eh_matriz else ''})"


class Imposto(models.Model):
    """Linha de catálogo tributário versionada e IMUTÁVEL (US-CFG-003; D-CFG-3).

    Mudar alíquota = NOVA linha com nova vigência (INV-CFG-IMPOSTO-IMUTAVEL —
    trigger 0003); INV-026 fecha no CONSUMIDOR (documento emitido snapshota a
    alíquota usada). Não-sobreposição de vigência por (tenant, tipo, filial) =
    exclusion constraint btree_gist 0004 (INV-CFG-IMPOSTO-SEM-SOBREPOSICAO) →
    "vigente em D" é determinístico. `filial` NULL = vale para o tenant inteiro.
    Vigência canônica ADR-0030 (`vigencia_*`/`revogado_em`/`motivo_revogacao`);
    revogar = linha cadastrada errada (one-shot, motivo ≥10 chars no domínio) —
    linha revogada sai da exclusion (WHERE revogado_em IS NULL) e da resolução.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, serialize=False)
    tenant = models.ForeignKey(
        "tenant.tenant", on_delete=models.PROTECT, related_name="impostos_config"
    )
    tipo = models.CharField(max_length=10, choices=_choices(TipoImposto))
    aliquota = models.DecimalField(
        max_digits=7,
        decimal_places=4,
        help_text="Pontos percentuais 0..100 (VO Aliquota). Imutável — nova linha por vigência.",
    )
    vigencia_inicio = models.DateTimeField()
    vigencia_fim = models.DateTimeField(
        null=True,
        blank=True,
        help_text="NULL = vigência aberta. Encerrar = one-shot NULL→data (D-CFG-3).",
    )
    revogado_em = models.DateTimeField(
        null=True,
        blank=True,
        help_text="One-shot. Linha cadastrada errada (DELETE físico é bloqueado — retenção 5a).",
    )
    motivo_revogacao = models.TextField(
        blank=True, default="", help_text="≥10 chars quando revogado (INV-VIG-002)."
    )
    filial = models.ForeignKey(
        Filial,
        on_delete=models.PROTECT,
        related_name="impostos",
        null=True,
        blank=True,
        help_text="NULL = catálogo do tenant inteiro (ISS municipal usa filial).",
    )
    cfop_padrao = models.CharField(max_length=10, blank=True, default="")
    ncm_padrao = models.CharField(max_length=10, blank=True, default="")
    iss_retido_fonte = models.BooleanField(
        default=False, help_text="LC 116/2003 art. 6º (ADV-02/D-CFG-9)."
    )
    tem_st = models.BooleanField(
        default=False, help_text="ST do ICMS é atributo, NÃO regime (ADV-03)."
    )
    simples_excedeu_sublimite = models.BooleanField(
        default=False, help_text="Sublimite do Simples estourado (ADV-02)."
    )
    observacoes = models.TextField(blank=True, default="")
    correlation_id = models.UUIDField(default=uuid.uuid4)
    criado_em = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = "imposto"
        verbose_name = "Imposto (linha de catálogo)"
        verbose_name_plural = "Impostos (catálogo tributário)"
        ordering = ["tenant", "tipo", "vigencia_inicio"]
        indexes = [
            models.Index(fields=["tenant", "tipo"], name="imposto_tenant_tipo_idx"),
        ]

    def __str__(self) -> str:
        return f"Imposto({self.tipo} {self.aliquota}% desde {self.vigencia_inicio:%Y-%m-%d})"


class SerieDocumento(models.Model):
    """Série de numeração LOCAL de documento (US-CFG-002; ADR-0080).

    `regime_numeracao` é DERIVADO do tipo (`regime_numeracao_do_tipo`), nunca do
    caller: fatura/certificado = GAP_LESS (reserva-TTL); os/orcamento/recibo/
    interno = BURACOS_ACEITOS (UPDATE atômico estilo ADR-0056). NFS-e/NF NÃO
    entram (BaaS/município numera — ADV-04). `proximo_numero` nunca diminui
    (INV-028 — trigger 0003), exceto reset anual legítimo (TL-07: vira contador
    por ano quando `reset_anual`, detectado pela troca de `ano_corrente`).
    Chave de unicidade (tenant, filial, tipo, prefixo) — TL-06; `filial` NULL =
    série global do tenant (UNIQUE parcial própria).
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, serialize=False)
    tenant = models.ForeignKey(
        "tenant.tenant", on_delete=models.PROTECT, related_name="series_documento"
    )
    filial = models.ForeignKey(
        Filial,
        on_delete=models.PROTECT,
        related_name="series_documento",
        null=True,
        blank=True,
        help_text="NULL = série global do tenant.",
    )
    tipo = models.CharField(
        max_length=20,
        choices=_choices(TipoDocumento),
        help_text="os/orcamento/fatura/certificado/recibo/interno (nf/nfse NÃO — ADV-04).",
    )
    prefixo = models.CharField(max_length=16)
    proximo_numero = models.IntegerField(
        default=1, help_text="Próximo a alocar. Nunca diminui (INV-028), exceto reset anual."
    )
    regime_numeracao = models.CharField(
        max_length=20,
        choices=_choices(RegimeNumeracao),
        help_text="DERIVADO do tipo (ADR-0080) — imutável (trigger 0003).",
    )
    formato = models.CharField(
        max_length=60,
        default="{prefixo}-{seq}",
        help_text="Placeholders: {prefixo}, {seq} (com padding), {ano}.",
    )
    padding = models.IntegerField(default=6)
    reset_anual = models.BooleanField(
        default=False, help_text="Contador por (série, ano) quando formato usa {ano} (TL-07)."
    )
    ano_corrente = models.IntegerField(
        null=True, blank=True, help_text="Ano do contador atual (só com reset_anual)."
    )
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "serie_documento"
        verbose_name = "Série de documento"
        verbose_name_plural = "Séries de documento"
        constraints = [
            models.UniqueConstraint(
                fields=("tenant", "filial", "tipo", "prefixo"),
                condition=models.Q(filial__isnull=False),
                name="uq_cfg_serie_chave_filial",
            ),
            models.UniqueConstraint(
                fields=("tenant", "tipo", "prefixo"),
                condition=models.Q(filial__isnull=True),
                name="uq_cfg_serie_chave_global",
            ),
        ]

    def __str__(self) -> str:
        return f"Serie({self.tipo}/{self.prefixo} — próx. {self.proximo_numero})"


class NumeroDocumentoReservado(models.Model):
    """Reserva-TTL do número gap-less (ADR-0080; espelha `numero_certificado_reservado`).

    Só séries GAP_LESS usam esta tabela. Densidade por (tenant, serie, ano):
    `ano=0` quando a série não tem reset anual (sem dimensão de ano). Reserva
    não-confirmada expira no TTL e devolve o número à sequência; confirmada é
    one-shot e nunca deletada (INV-CFG-NUM-ATOMICA — triggers 0003).
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, serialize=False)
    tenant = models.ForeignKey(
        "tenant.tenant", on_delete=models.PROTECT, related_name="numeros_documento_reservados"
    )
    serie = models.ForeignKey(
        SerieDocumento, on_delete=models.PROTECT, related_name="numeros_reservados"
    )
    ano = models.IntegerField(help_text="Dimensão do contador (TL-07). 0 = série sem reset anual.")
    sequencial = models.IntegerField(help_text="Número denso ≥1 (sem buracos confirmados).")
    reservado_em = models.DateTimeField(auto_now_add=True)
    ttl_expira_em = models.DateTimeField(
        help_text="Reserva não-confirmada expira aqui (TTL 5min — motor M8)."
    )
    confirmado = models.BooleanField(
        default=False, help_text="True na confirmação one-shot (transação do emissor)."
    )
    correlation_id = models.UUIDField(default=uuid.uuid4)

    class Meta:
        db_table = "numero_documento_reservado"
        verbose_name = "Número de documento reservado"
        verbose_name_plural = "Números de documento reservados"
        ordering = ["tenant", "serie", "ano", "sequencial"]
        indexes = [
            models.Index(fields=["tenant", "serie", "ano"], name="ix_num_doc_reservado_chave"),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=("tenant", "serie", "ano", "sequencial"),
                name="uq_num_doc_reservado",
            ),
        ]

    def __str__(self) -> str:
        return f"NumDoc(serie={self.serie_id} ano={self.ano} seq={self.sequencial})"
