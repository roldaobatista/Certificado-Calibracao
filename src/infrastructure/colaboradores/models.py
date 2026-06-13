# ruff: noqa: RUF012 — choices derivados de enum (list mutável ok em Model)
"""Frente `colaboradores` — models Django (Fatia 1b, T-COL-020).

5 tabelas:
  - `catalogo_habilidade`: catálogo global read-only SEM tenant_id / SEM RLS.
  - `colaborador`: agregado raiz; soft-delete Padrão C; 3 managers.
  - `colaborador_papel`: papel de negócio atribuído (vigência solta — D-COL-4).
  - `colaborador_habilidade`: habilidade por colaborador (catalogo XOR livre — D-COL-5).
  - `colaborador_documento`: documento anexado (TipoDocumento — D-COL-6).

Managers em Colaborador (T-COL-020):
  - `ativos`  → filtra data_desligamento IS NULL AND deletado_em IS NULL.
  - `objects` → (default) filtra deletado_em IS NULL.
  - `all_objects` → expõe tudo (soft-deletados incluídos).

Constraints criadas via SQL na migration 0001 (Django não suporta partial unique
nativamente sem Constraint.condition — criadas como índices/CHECKs via RunSQL):
  - uq_col_cpf_ativo: UNIQUE INDEX parcial (tenant, cpf) WHERE deletado_em IS NULL.
  - uq_col_papel_dono_unico: UNIQUE INDEX parcial (tenant) WHERE papel='dono'
    AND data_fim IS NULL AND revogado_em IS NULL.
  - ck_col_comissao_range: CHECK comissao_default_pct BETWEEN 0 AND 100.
  - ck_col_hab_xor: CHECK (catalogo_id IS NOT NULL XOR descricao_livre IS NOT NULL).

RLS:
  - catalogo_habilidade: SEM RLS (global — isenção documentada no 0002_rls_policies).
  - Demais 4 tabelas: RLS pattern v2 (ADR-0002 §6) em 0002_rls_policies.

Advisory lock: namespace 880_405 em repositories.py (troca de DONO — ADR-0065/D-COL-4).

LGPD: cpf/email/telefone são PII (art. 5° IX LGPD); base legal: art. 7° II (CLT) /
art. 7° V (PJ/estag./sócio/terceirizado). foto_storage_key referencia storage externo
(sem cru em banco — ADV-COL-01). ASO fora do MVP (R-COL-2 / dado de saúde art. 11).
"""

from __future__ import annotations

import uuid
from enum import Enum

from django.db import models

from src.domain.rh_frota_qualidade.colaboradores.enums import (
    NivelHabilidade,
    PapelColaborador,
    TipoDocumento,
    Vinculo,
)


def _choices(enum_cls: type[Enum]) -> list[tuple[str, str]]:
    """Choices (value, value) a partir do enum de domínio (1:1 anti-drift)."""
    return [(membro.value, str(membro.value)) for membro in enum_cls]


# =============================================================
# Manager auxiliares para Colaborador
# =============================================================


class _AtivoManager(models.Manager["Colaborador"]):
    """Filtra colaboradores ativos: não desligados E não soft-deletados."""

    def get_queryset(self) -> models.QuerySet[Colaborador]:
        return (
            super().get_queryset().filter(data_desligamento__isnull=True, deletado_em__isnull=True)
        )


class _SoftDeleteManager(models.Manager["Colaborador"]):
    """Manager default: exclui soft-deletados (deletado_em IS NULL)."""

    def get_queryset(self) -> models.QuerySet[Colaborador]:
        return super().get_queryset().filter(deletado_em__isnull=True)


# =============================================================
# Tabela global (sem tenant_id / sem RLS)
# =============================================================


class CatalogoHabilidade(models.Model):
    """Catálogo global de habilidades — SEM tenant_id, SEM RLS (TL-COL-10 / D-COL-5).

    Tabela read-only para tenants: INSERT exclusivo via migration de seed (0006).
    `grandeza` referencia a grandeza metrológica (ex: "massa", "temperatura");
    None para habilidades de laboratório geral ou inspeção.
    PK textual `codigo` permite JOIN sem JOIN (evita N+1 lookup).
    """

    codigo = models.CharField(
        primary_key=True,
        max_length=60,
        help_text="Código canônico da habilidade (ex: 'massa', 'temperatura').",
    )
    descricao = models.CharField(
        max_length=300,
        help_text="Descrição humana da habilidade.",
    )
    grandeza = models.CharField(  # noqa: DJ001 -- NULL = habilidade geral sem grandeza metrológica (≠ string vazia que seria grandeza inválida)
        max_length=60,
        blank=True,
        null=True,
        help_text="Grandeza metrológica associada; None para habilidades gerais.",
    )

    class Meta:
        db_table = "catalogo_habilidade"
        # Sem tenant_id, sem RLS — isenção documentada em 0002_rls_policies.py

    def __str__(self) -> str:
        return f"{self.codigo}: {self.descricao}"


# =============================================================
# Colaborador (agregado raiz)
# =============================================================


class Colaborador(models.Model):
    """Agregado raiz do módulo colaboradores (spec §4 / D-COL-1..14).

    Soft-delete Padrão C (ADR-0031):
      deletado_em / deletado_por_usuario_id / deletado_motivo.

    Desligamento de negócio (D-COL-3):
      data_desligamento / motivo_desligamento.

    CPF: CharField(11) — dígitos sem máscara (PII art. 5° IX LGPD).
    Unicidade: índice parcial uq_col_cpf_ativo criado via RunSQL em 0001
    (Django UniqueConstraint com condition=~Q não é portável — molde clientes).

    comissao_default_pct: CHECK 0..100 via RunSQL em 0001 (ck_col_comissao_range).
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        serialize=False,
    )
    tenant = models.ForeignKey(
        "tenant.tenant",
        on_delete=models.PROTECT,
        related_name="colaboradores",
    )
    nome = models.CharField(max_length=200)
    cpf = models.CharField(
        max_length=11,
        help_text="CPF somente dígitos (PII — art. 5° IX LGPD).",
    )
    email = models.CharField(
        max_length=254,
        help_text="E-mail funcional/pessoal (PII — base legal vinculo).",
    )
    telefone = models.CharField(
        max_length=20,
        help_text="Telefone de contato (PII — base legal vinculo).",
    )
    foto_storage_key = models.CharField(  # noqa: DJ001 -- NULL = sem foto (≠ '' que seria chave inválida no storage)
        max_length=500,
        blank=True,
        null=True,
        help_text="Chave no storage externo (sem conteúdo cru — ADV-COL-01).",
    )
    usuario_id = models.UUIDField(
        blank=True,
        null=True,
        help_text=(
            "UUID do usuário associado (opcional — D-COL-2). "
            "SIGNATARIO EXIGE NOT NULL (INV-COL-SIGNATARIO-IDENTIDADE)."
        ),
    )
    vinculo = models.CharField(
        max_length=15,
        choices=_choices(Vinculo),
        help_text="Vínculo empregatício/contratual (base legal LGPD — ADV-COL-01).",
    )
    data_admissao = models.DateField()
    data_desligamento = models.DateField(
        blank=True,
        null=True,
        help_text="Data efetiva de encerramento do vínculo (D-COL-3).",
    )
    motivo_desligamento = models.CharField(  # noqa: DJ001 -- NULL = não-desligado (≠ '' que seria motivo ausente após desligamento)
        max_length=500,
        blank=True,
        null=True,
    )
    comissao_default_pct = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        help_text="Comissão padrão em % (0..100 — CHECK ck_col_comissao_range em 0001).",
    )
    observacao = models.TextField(blank=True, default="")
    # Soft-delete Padrão C (ADR-0031 / D-COL-3)
    deletado_em = models.DateTimeField(blank=True, null=True)
    deletado_por_usuario_id = models.UUIDField(blank=True, null=True)
    deletado_motivo = models.CharField(  # noqa: DJ001 -- NULL = não-deletado (≠ '' que seria motivo ausente após deleção)
        max_length=500,
        blank=True,
        null=True,
    )
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    # Managers (ordem importa: primeiro declarado é o default se não houver default=True)
    # default=True em _SoftDeleteManager garante que Colaborador.objects filtra deletado.
    objects: models.Manager[Colaborador] = _SoftDeleteManager()
    ativos: models.Manager[Colaborador] = _AtivoManager()
    all_objects: models.Manager[Colaborador] = models.Manager()

    class Meta:
        db_table = "colaborador"
        # Índice parcial uq_col_cpf_ativo e CHECK ck_col_comissao_range
        # criados via RunSQL em 0001_initial (não suportados nativamente pelo ORM
        # sem btree_gist — molde clientes/migrations/0001_initial.py).

    def __str__(self) -> str:
        return f"{self.nome} ({self.cpf})"


# =============================================================
# ColaboradorPapel
# =============================================================


class ColaboradorPapel(models.Model):
    """Papel de negócio atribuído ao colaborador (D-COL-4 / spec §4).

    Vigência solta (NÃO usa JanelaVigencia — entidade mutável, D-COL-4/TL-COL-09):
      data_inicio / data_fim / revogado_em.

    DONO: único por tenant ativo — índice parcial uq_col_papel_dono_unico em 0001
    (WHERE papel='dono' AND data_fim IS NULL AND revogado_em IS NULL).

    SIGNATARIO: responsabilidade_tecnica_id aponta para RTCompetencia vigente
    (INV-COL-SIGNATARIO-IDENTIDADE / D-COL-11).

    MOTORISTA_UMC: pendencia_cnh=True quando CNH ausente/expirada (R-COL-1).
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        serialize=False,
    )
    colaborador = models.ForeignKey(
        Colaborador,
        on_delete=models.PROTECT,
        related_name="papeis",
    )
    tenant = models.ForeignKey(
        "tenant.tenant",
        on_delete=models.PROTECT,
        related_name="colaborador_papeis",
    )
    papel = models.CharField(
        max_length=20,
        choices=_choices(PapelColaborador),
    )
    data_inicio = models.DateField()
    data_fim = models.DateField(blank=True, null=True)
    revogado_em = models.DateTimeField(blank=True, null=True)
    responsabilidade_tecnica_id = models.UUIDField(
        blank=True,
        null=True,
        help_text="RTCompetencia vigente — obrigatório quando papel=SIGNATARIO (D-COL-11).",
    )
    pendencia_cnh = models.BooleanField(
        default=False,
        help_text="True quando MOTORISTA_UMC sem CNH válida (R-COL-1).",
    )
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "colaborador_papel"
        # Índice parcial uq_col_papel_dono_unico criado via RunSQL em 0001.

    def __str__(self) -> str:
        return f"{self.papel} — colaborador {self.colaborador_id}"


# =============================================================
# ColaboradorHabilidade
# =============================================================


class ColaboradorHabilidade(models.Model):
    """Habilidade registrada por colaborador (D-COL-5 / spec §4).

    `catalogo` XOR `descricao_livre`: exatamente um NOT NULL
    (CHECK ck_col_hab_xor em 0001_initial via RunSQL).
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        serialize=False,
    )
    colaborador = models.ForeignKey(
        Colaborador,
        on_delete=models.PROTECT,
        related_name="habilidades",
    )
    tenant = models.ForeignKey(
        "tenant.tenant",
        on_delete=models.PROTECT,
        related_name="colaborador_habilidades",
    )
    catalogo = models.ForeignKey(
        CatalogoHabilidade,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="habilidades",
        help_text="Habilidade do catálogo global; None se habilidade livre (D-COL-5).",
    )
    descricao_livre = models.CharField(  # noqa: DJ001 -- NULL = habilidade de catálogo (XOR com catalogo — ck_col_hab_xor; '' seria habilidade vazia inválida)
        max_length=300,
        blank=True,
        null=True,
        help_text="Habilidade livre não catalogada; None se habilidade de catálogo.",
    )
    nivel = models.CharField(
        max_length=15,
        choices=_choices(NivelHabilidade),
    )
    evidencia_url = models.CharField(  # noqa: DJ001 -- NULL = sem evidência anexada (≠ '' que seria URL inválida)
        max_length=500,
        blank=True,
        null=True,
        help_text="URL do documento comprobatório (opcional).",
    )
    data_avaliacao = models.DateField()
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "colaborador_habilidade"
        # CHECK ck_col_hab_xor criado via RunSQL em 0001_initial.

    def __str__(self) -> str:
        fonte = self.catalogo_id or self.descricao_livre or "?"
        return f"{self.nivel} — {fonte}"


# =============================================================
# ColaboradorDocumento
# =============================================================


class ColaboradorDocumento(models.Model):
    """Documento anexado ao colaborador (D-COL-6 / spec §4).

    ASO (Atestado de Saúde Ocupacional) FORA do MVP (R-COL-2).
    `storage_key` aponta para storage externo (não conteúdo cru — ADV-COL-01).
    `sha256` calculado server-side para integridade.
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        serialize=False,
    )
    colaborador = models.ForeignKey(
        Colaborador,
        on_delete=models.PROTECT,
        related_name="documentos",
    )
    tenant = models.ForeignKey(
        "tenant.tenant",
        on_delete=models.PROTECT,
        related_name="colaborador_documentos",
    )
    tipo = models.CharField(
        max_length=20,
        choices=_choices(TipoDocumento),
    )
    storage_key = models.CharField(
        max_length=500,
        help_text="Chave no storage externo (sem conteúdo cru — ADV-COL-01).",
    )
    sha256 = models.CharField(
        max_length=64,
        help_text="Hash SHA-256 do arquivo calculado server-side (integridade).",
    )
    data_upload = models.DateTimeField()
    data_validade = models.DateField(
        blank=True,
        null=True,
        help_text="Validade do documento (CNH, certificados com prazo).",
    )
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "colaborador_documento"

    def __str__(self) -> str:
        return f"{self.tipo} — colaborador {self.colaborador_id}"
