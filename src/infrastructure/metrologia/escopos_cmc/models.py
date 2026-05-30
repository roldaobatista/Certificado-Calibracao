# ruff: noqa: RUF012 — choices derivados de enum (list mutavel ok em Model)
"""M6 `metrologia/escopos-cmc` — modelos Django (T-ECMC-010/011).

2 tabelas:
- `escopo_cmc` (raiz) — espelha `EscopoCMCSnapshot` do domínio com COLUNAS
  TIPADAS (D-ECMC-2 / TL-C-02): diferente do M5 (JSONField) porque `cobre()`/
  `cmc_para()` precisam de índice PG eficiente por grandeza + range numérico.
- `escopo_extraido` (staging — TL-C-08) — rascunho da extração de PDF, mutável,
  NÃO WORM. Confirmação CRIA uma linha CONFIRMADA em `escopo_cmc` (não muta a
  staging em escopo vigente — INV-ECMC-007).

Choices derivados 1:1 dos enums de domínio (anti-drift). Domain NÃO importa
Django (ADR-0007 — o adapter em `repositories.py` converte Model <-> Snapshot).

Schema-irmãos (ADR-0002/0031/0073/0074):
- 0001_initial: CreateModel + UNIQUE (nulls_distinct=False) + índice parcial.
- 0002_rls_policies: RLS pattern v2 nas 2 tabelas.
- 0003_triggers_worm: Padrão B — block-delete + WORM de campo metrológico em
  linha CONFIRMADA (exceto revogação/encerramento one-shot).
- 0004_grants_app_user: GRANT app_user.
- 0005_seed_authz_escopos_cmc: matriz papel × ação.
"""

from __future__ import annotations

import uuid
from enum import Enum

from django.db import models
from django.db.models import Q

from src.domain.metrologia.escopos_cmc.enums import (
    EstadoEscopo,
    FormaCMC,
    OrigemEscopo,
)
from src.domain.metrologia.value_objects import Grandeza


def _choices(enum_cls: type[Enum]) -> list[tuple[str, str]]:
    """Choices (value, value) a partir do enum de domínio (1:1 anti-drift)."""
    return [(membro.value, str(membro.value)) for membro in enum_cls]


class EscopoCMC(models.Model):
    """Linha do escopo de acreditação CGCRE (perfil A) ou capacidade interna
    (perfis B/C/D — `rbc_acreditado=False`, ADR-0075).

    WORM Padrão B (ADR-0031): linha CONFIRMADA é imutável nos campos
    metrológicos (trigger 0003 — INV-ECMC-003); revisão = INSERT de nova `versao`
    (TL-C-07), nunca UPDATE in-place. Vigência canônica ADR-0030. CAS via
    `revision`. Só `estado=CONFIRMADO` + vigente entra na cobertura (ADR-0073).
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, serialize=False)
    tenant = models.ForeignKey(
        "tenant.tenant", on_delete=models.PROTECT, related_name="escopos_cmc"
    )
    grandeza = models.CharField(
        max_length=30,
        choices=_choices(Grandeza),
        help_text="Grandeza RBC (VO Grandeza). Índice de filtro de cobertura.",
    )
    faixa_min = models.DecimalField(
        max_digits=30, decimal_places=12, help_text="Limite inferior da faixa (Decimal)."
    )
    faixa_max = models.DecimalField(
        max_digits=30, decimal_places=12, help_text="Limite superior (faixa_min < faixa_max)."
    )
    unidade = models.CharField(max_length=20, help_text="Unidade SI/RBC da faixa (whitelist VO).")
    cmc_forma = models.CharField(
        max_length=20,
        choices=_choices(FormaCMC),
        default=FormaCMC.ABSOLUTA.value,
        help_text="ABSOLUTA (cmc_valor constante) ou RELATIVA_LINEAR (a + b·|X|) — ADR-0074.",
    )
    cmc_valor = models.DecimalField(
        max_digits=30,
        decimal_places=12,
        help_text="ABSOLUTA: a própria CMC; RELATIVA_LINEAR: termo fixo `a`. Menor incerteza declarada.",
    )
    cmc_unidade = models.CharField(max_length=20, help_text="Unidade da CMC.")
    cmc_coef_relativo = models.DecimalField(
        max_digits=30,
        decimal_places=12,
        null=True,
        blank=True,
        help_text="Coeficiente `b` (só RELATIVA_LINEAR — CMC = a + b·|X|).",
    )
    rbc_acreditado = models.BooleanField(
        default=False,
        help_text=(
            "True só perfil A (INV-ECMC-002 — `tenant_perfil_e(['A'])`; forçado "
            "False p/ B/C/D server-side, anti-fraude FAIL L6). Bloqueio 412 RBC-only."
        ),
    )
    numero_escopo_cgcre = models.CharField(
        max_length=60, blank=True, default="", help_text="Nº do escopo CGCRE (decisão K)."
    )
    procedimento_id = models.UUIDField(
        null=True,
        blank=True,
        help_text="FK método (módulo procedimentos-calibracao Wave A; NOT NULL p/ RBC — T-ECMC-007).",
    )
    documento_regulatorio_id = models.UUIDField(
        null=True, blank=True, help_text="FK Licenças (INV-012; NULLABLE até módulo existir)."
    )
    versao = models.IntegerField(default=1, help_text="Revisão preserva versão anterior (AC-CAL-015-2).")
    vigente_a_partir = models.DateTimeField(help_text="Início da vigência desta versão.")
    estado = models.CharField(
        max_length=20,
        choices=_choices(EstadoEscopo),
        default=EstadoEscopo.CONFIRMADO.value,
        help_text="Em escopo_cmc só CONFIRMADO/REVOGADO (rascunho vive em escopo_extraido).",
    )
    origem = models.CharField(
        max_length=20,
        choices=_choices(OrigemEscopo),
        default=OrigemEscopo.MANUAL.value,
        help_text="Proveniência: MANUAL ou EXTRACAO_PDF (decisão N).",
    )
    revision = models.IntegerField(
        default=0, help_text="Optimistic lock CAS. UPDATE WHERE revision=:esperada."
    )
    vigencia_inicio = models.DateTimeField(help_text="Vigência canônica ADR-0030.")
    vigencia_fim = models.DateTimeField(
        null=True, blank=True, help_text="NULL = aberta. One-shot ao ser superada por nova versão."
    )
    correlation_id = models.UUIDField(default=uuid.uuid4, help_text="Cadeia forense.")
    revogado_em = models.DateTimeField(
        null=True, blank=True, help_text="Soft-delete B (ADR-0031). NULL = vigente."
    )
    motivo_revogacao = models.TextField(
        blank=True, default="", help_text=">=10 chars quando revogado (ADR-0030)."
    )
    criado_em = models.DateTimeField(auto_now_add=True, db_index=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "escopo_cmc"
        verbose_name = "Escopo CMC"
        verbose_name_plural = "Escopos CMC"
        ordering = ["-criado_em"]
        constraints = [
            models.UniqueConstraint(
                fields=(
                    "tenant",
                    "grandeza",
                    "faixa_min",
                    "faixa_max",
                    "procedimento_id",
                    "versao",
                ),
                name="uq_escopo_cmc_chave_natural",
                nulls_distinct=False,  # procedimento_id NULL (B/C/D) ainda deduplica — INV-ECMC-001
            ),
        ]
        indexes = [
            # Índice parcial da query quente cobre()/cmc_para() (TL-C-11).
            models.Index(
                fields=["tenant", "grandeza", "vigencia_fim"],
                name="ecmc_cobertura_idx",
                condition=Q(estado=EstadoEscopo.CONFIRMADO.value, revogado_em__isnull=True),
            ),
            models.Index(fields=["tenant", "grandeza", "estado"], name="ecmc_tenant_gr_est_idx"),
        ]

    def __str__(self) -> str:
        return f"EscopoCMC({self.grandeza} [{self.faixa_min},{self.faixa_max}]{self.unidade} v{self.versao} — {self.estado})"


class EscopoExtraido(models.Model):
    """Staging da extração de PDF da CGCRE (decisão N / TL-C-08). Mutável, NÃO
    WORM — editável na tela de conferência; nunca persiste vigente sem
    confirmação (INV-ECMC-007). Confirmar cria linha CONFIRMADA em escopo_cmc.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, serialize=False)
    tenant = models.ForeignKey(
        "tenant.tenant", on_delete=models.PROTECT, related_name="escopos_extraidos"
    )
    origem_pdf_storage_key = models.CharField(
        max_length=200, help_text="Chave opaca do PDF CGCRE (documento público)."
    )
    numero_escopo_cgcre = models.CharField(max_length=60, blank=True, default="")
    extraido_em = models.DateTimeField()
    linhas = models.JSONField(
        default=list, help_text="Lista de LinhaEscopoExtraida (texto cru + confiança)."
    )
    confirmado_em = models.DateTimeField(
        null=True, blank=True, help_text="NULL = pendente conferência humana."
    )
    confirmado_por_id_hash = models.CharField(max_length=80, blank=True, default="")
    criado_em = models.DateTimeField(auto_now_add=True, db_index=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "escopo_extraido"
        verbose_name = "Escopo Extraído (staging)"
        verbose_name_plural = "Escopos Extraídos (staging)"
        ordering = ["-criado_em"]
        indexes = [
            models.Index(fields=["tenant", "confirmado_em"], name="eextr_tenant_conf_idx"),
        ]

    def __str__(self) -> str:
        estado = "confirmado" if self.confirmado_em else "pendente"
        return f"EscopoExtraido({self.numero_escopo_cgcre or self.id} — {estado})"
