# ruff: noqa: RUF012 — choices derivados de enum (list mutavel ok em Model)
"""M7 `metrologia/procedimentos-calibracao` — modelo Django (T-PROC-020).

1 tabela `procedimento_calibracao` (raiz) — espelha `ProcedimentoSnapshot` do
domínio com COLUNAS TIPADAS (molde M6 escopo_cmc): a resolução `vigente_em`
precisa de índice PG por grandeza + range. SEM tabela de staging (procedimento é
autorado, não extraído — D1 vs M6).

Choices derivados 1:1 dos enums de domínio (anti-drift). Domain NÃO importa
Django (ADR-0007 — adapter em repositories.py converte Model <-> Snapshot).

Schema-irmãos (ADR-0002/0031/0073):
- 0001_initial: CreateModel + UNIQUE documental + UNIQUE parcial não-overlap
  (INV-PROC-008) + índice parcial resolução.
- 0002_rls_policies: RLS pattern v2.
- 0003_triggers_worm: Padrão B — block-delete + WORM de campo técnico de
  PUBLICADO/REVOGADO (exceto revogação/encerramento one-shot).
- 0004_grants_app_user / 0005_seed_authz_procedimentos.
"""

from __future__ import annotations

import uuid
from enum import Enum

from django.db import models
from django.db.models import Q

from src.domain.metrologia.procedimentos_calibracao.enums import (
    EstadoProcedimento,
    TipoMetodo,
)
from src.domain.metrologia.value_objects import Grandeza


def _choices(enum_cls: type[Enum]) -> list[tuple[str, str]]:
    """Choices (value, value) a partir do enum de domínio (1:1 anti-drift)."""
    return [(membro.value, str(membro.value)) for membro in enum_cls]


class ProcedimentoCalibracao(models.Model):
    """Procedimento técnico documentado controlado (ISO 17025 cl. 7.2.1).

    Documento que define o "como medir" por grandeza+faixa. WORM Padrão B
    (ADR-0031): linha PUBLICADA é imutável nos campos técnicos (trigger 0003 —
    INV-PROC-003); revisão = INSERT de nova `versao` (AC-CAL-016-3), nunca UPDATE
    in-place. Vigência canônica ADR-0030. CAS via `revision`. Só
    `estado=PUBLICADO` + vigente entra na resolução `vigente_em()` (ADR-0073).
    No máximo UMA versão PUBLICADA vigente por chave natural (INV-PROC-008).
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, serialize=False)
    tenant = models.ForeignKey(
        "tenant.tenant", on_delete=models.PROTECT, related_name="procedimentos_calibracao"
    )
    codigo = models.CharField(
        max_length=60, help_text="Identidade do documento controlado (cl. 8.3), ex. PC-MASSA-001."
    )
    titulo = models.CharField(max_length=200, help_text="Título do procedimento.")
    grandeza = models.CharField(
        max_length=30,
        choices=_choices(Grandeza),
        help_text="UMA grandeza por código (D-PROC-2). Índice de resolução.",
    )
    faixa_min = models.DecimalField(
        max_digits=30, decimal_places=12, help_text="Limite inferior da faixa (Decimal)."
    )
    faixa_max = models.DecimalField(
        max_digits=30, decimal_places=12, help_text="Limite superior (faixa_min < faixa_max)."
    )
    unidade = models.CharField(max_length=20, help_text="Unidade SI da faixa (whitelist VO).")
    metodo_norma = models.CharField(
        max_length=120, help_text="Método/norma de referência (NIT-DICLA / ABNT / OIML / ISO)."
    )
    tipo_metodo = models.CharField(
        max_length=20,
        choices=_choices(TipoMetodo),
        default=TipoMetodo.NORMALIZADO.value,
        help_text="NORMALIZADO / NAO_NORMALIZADO / MODIFICADO (cl. 7.2.2 — INV-PROC-010).",
    )
    registro_validacao_id = models.UUIDField(
        null=True,
        blank=True,
        help_text="Evidência de validação de método não-normalizado (cl. 7.2.2; NULL=fail-open lazy).",
    )
    numero_revisao = models.CharField(
        max_length=40, blank=True, default="", help_text='Ex. "Rev. 03" — cl. 8.3.2c (distinto de versao).'
    )
    aprovado_em = models.DateTimeField(
        null=True, blank=True, help_text="Data do ato de aprovação (cl. 8.3.1; ≠ vigência)."
    )
    aprovado_por_id = models.UUIDField(null=True, blank=True, help_text="Quem aprovou (RT/gestor).")
    aprovado_por_nome_snapshot = models.CharField(max_length=160, blank=True, default="")
    anexo_pdf_storage_key = models.CharField(
        max_length=200, blank=True, default="", help_text="Chave opaca do PDF (storage)."
    )
    anexo_pdf_sha256 = models.CharField(
        max_length=80, blank=True, default="", help_text="sha256 do binário, recalculado server-side (INV-PROC-007)."
    )
    versao = models.IntegerField(default=1, help_text="Revisão preserva versão anterior (AC-CAL-016-3).")
    vigente_a_partir = models.DateTimeField(help_text="Início da vigência desta versão.")
    estado = models.CharField(
        max_length=20,
        choices=_choices(EstadoProcedimento),
        default=EstadoProcedimento.RASCUNHO.value,
        help_text="RASCUNHO (editável) → PUBLICADO (WORM) → REVOGADO (terminal).",
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
        db_table = "procedimento_calibracao"
        verbose_name = "Procedimento de Calibração"
        verbose_name_plural = "Procedimentos de Calibração"
        ordering = ["-criado_em"]
        constraints = [
            models.UniqueConstraint(
                fields=("tenant", "codigo", "versao"),
                name="uq_proc_chave_documental",
            ),
            # INV-PROC-008 — no máximo 1 PUBLICADO vigente por chave natural.
            models.UniqueConstraint(
                fields=("tenant", "codigo", "grandeza", "faixa_min", "faixa_max"),
                name="uq_proc_uma_vigente",
                condition=Q(
                    estado=EstadoProcedimento.PUBLICADO.value,
                    vigencia_fim__isnull=True,
                    revogado_em__isnull=True,
                ),
            ),
        ]
        indexes = [
            # Índice parcial da query quente vigente_em().
            models.Index(
                fields=["tenant", "grandeza", "vigencia_fim"],
                name="proc_resolucao_idx",
                condition=Q(estado=EstadoProcedimento.PUBLICADO.value, revogado_em__isnull=True),
            ),
            models.Index(fields=["tenant", "codigo"], name="proc_tenant_codigo_idx"),
        ]

    def __str__(self) -> str:
        return f"ProcedimentoCalibracao({self.codigo} v{self.versao} {self.grandeza} — {self.estado})"
