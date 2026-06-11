"""Modelos Tenant e TenantPerfilHistorico (ADR-0067).

Tabela "SHARED ACROSS TENANTS" (ADR-0002 §8) — NAO tem tenant_id proprio.
Acesso a estas tabelas e protegido por permissoes do Django Admin + perfis
de aplicacao (ADR-0012), nao por RLS.

Origem da expansao 2026-05-27:
- Saneamento SAN-PERFIL-TENANT pos-auditoria 10 lentes.
- ADR-0067 aceita 2026-05-27 (Roldao via AskUserQuestion).
- T-SAN-PERFIL-011 + T-SAN-PERFIL-012 do tasks.md P4.
"""

from __future__ import annotations

import re
import uuid
from typing import Any, NoReturn

from django.core.exceptions import ValidationError
from django.db import models

# Regex oficial do numero RBC — formato CRL NNNN ou CRL NNNN-NN (filial).
# Fonte: NIT-DICLA-080 (CGCRE). Validado em Tenant.clean() quando perfil='A'.
_REGEX_NUMERO_RBC = re.compile(r"^CRL \d{4}(-\d{2})?$")


class StatusLifecycle(models.TextChoices):
    """Estados possiveis de um tenant (preparacao ADR-0015 lifecycle)."""

    ATIVO = "ativo", "Ativo"
    SUSPENSO = "suspenso", "Suspenso (inadimplencia ou desativacao temporaria)"
    CANCELADO = "cancelado", "Cancelado (encerrado pelo cliente)"


class PerfilRegulatorioChoices(models.TextChoices):
    """Os 4 perfis regulatorios canonicos (PRD §2 + ADR-0067).

    Espelho do enum de dominio em src/domain/tenant/enums.py
    (TextChoices serve apenas pra Django admin/forms).
    """

    A_ACREDITADO_RBC = "A", "A — Acreditado RBC/CGCRE"
    B_RASTREAVEL = "B", "B — Rastreavel nao-acreditado"
    C_EM_PREPARACAO = "C", "C — Em preparacao para acreditar"
    D_COMERCIAL_PURO = "D", "D — Comercial puro (sem ISO 17025)"


class Tenant(models.Model):
    """Um cliente do sistema. Provisiona-se em onboarding (ADR-0015 + ADR-0067 etapa 0)."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    slug = models.SlugField(
        max_length=50,
        unique=True,
        help_text="Identificador url-safe (ex: 'balancas-solution').",
    )
    nome_fantasia = models.CharField(max_length=200)
    plano = models.CharField(
        max_length=50,
        default="placeholder",
        help_text="Plano comercial. Modelo composicional real entra Wave B (ADR-0013).",
    )
    status_lifecycle = models.CharField(
        max_length=20,
        choices=StatusLifecycle.choices,
        default=StatusLifecycle.ATIVO,
    )
    bloqueio_automatico_inadimplencia_habilitado = models.BooleanField(
        default=False,
        help_text=(
            "Se True, job D+90 marca clientes inadimplentes como bloqueados. "
            "Wave A: exige tambem registro da regua D+30/60/89 antes do bloqueio "
            "(CDC art. 6 III/IV + Lei 14.181/2021)."
        ),
    )

    # ============ ADR-0067 — Perfil regulatorio ============
    # NOTA: mutavel APENAS via funcoes SECURITY DEFINER aplicar_evento_cgcre()
    # e rebaixar_perfil_tenant_voluntario_cliente() (migrations 0008/0009 — Sprint 1 P5).
    perfil_regulatorio = models.CharField(
        max_length=1,
        choices=PerfilRegulatorioChoices.choices,
        help_text=(
            "Perfil regulatorio do tenant (ADR-0067 — INV-TENANT-PERFIL-002). "
            "NOT NULL pos-migration 0005. Mutavel apenas via funcoes "
            "SECURITY DEFINER. Hook `tenant-perfil-imutavel-check` bloqueia "
            "qualquer migration que tente UPDATE direto."
        ),
    )
    acreditacao_cgcre_numero = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        help_text=(
            "Numero RBC formato 'CRL NNNN' ou 'CRL NNNN-NN'. "
            "Preenchido apenas quando perfil_regulatorio='A'. "
            "Validacao regex em Tenant.clean()."
        ),
    )
    acreditacao_suspensa_em = models.DateField(
        null=True,
        blank=True,
        help_text=(
            "Data inicio da suspensao temporaria CGCRE (NIT-DICLA-005 §7.4). "
            "Preserva perfil='A' mas predicate tenant_perfil_e({'A'}) "
            "retorna False enquanto today < acreditacao_suspensa_ate."
        ),
    )
    acreditacao_suspensa_ate = models.DateField(
        null=True,
        blank=True,
        help_text=(
            "Data prevista de fim da suspensao temporaria CGCRE. "
            "Cancelamento definitivo usa direcao=CANCELAMENTO_CGCRE."
        ),
    )
    acreditacao_vigencia_fim = models.DateField(
        null=True,
        blank=True,
        help_text=(
            "Data de validade da acreditacao CGCRE (INV-CER-CGCRE-VIG-001). "
            "Preenchida apenas em perfil A. A emissao so classifica ponto como "
            "RBC quando a acreditacao esta vigente nesta data (> data_de_emissao). "
            "NULL = fail-open lazy (campo novo; GATE-CER-CGCRE-VIG-DATA-POPULAR "
            "Wave A torna o bloqueio por vencimento efetivo quando populado)."
        ),
    )
    ilac_mra_aderido = models.BooleanField(
        default=False,
        help_text=(
            "Se True, lab esta no ILAC-MRA (reconhecimento internacional). "
            "Template de certificado A com selo ILAC-MRA so e permitido se True "
            "(hook template-ilac-mra-coerencia em Sprint 5 Wave A). R9 plan.md."
        ),
    )
    # =======================================================

    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = "tenant"
        db_table = "tenants"
        verbose_name = "Tenant"
        verbose_name_plural = "Tenants"
        ordering = ["nome_fantasia"]

    def __str__(self) -> str:
        return f"{self.nome_fantasia} ({self.slug}) [perfil={self.perfil_regulatorio}]"

    def clean(self) -> None:
        """Validacoes de coerencia entre perfil e campos auxiliares (AC-001-1e).

        DB tambem tem CHECK constraints redundantes — clean() apanha em forms/admin
        antes de chegar ao banco.
        """
        super().clean()

        # 1. Numero RBC so faz sentido quando perfil='A'.
        if self.acreditacao_cgcre_numero and self.perfil_regulatorio != "A":
            raise ValidationError(
                {
                    "acreditacao_cgcre_numero": (
                        "Numero RBC so pode ser preenchido em tenant perfil A. "
                        f"Perfil atual: {self.perfil_regulatorio}."
                    )
                }
            )

        # 2. Regex CRL NNNN ou CRL NNNN-NN (NIT-DICLA-080).
        if self.acreditacao_cgcre_numero and not _REGEX_NUMERO_RBC.match(
            self.acreditacao_cgcre_numero
        ):
            raise ValidationError(
                {
                    "acreditacao_cgcre_numero": (
                        "Numero RBC com formato invalido. Esperado 'CRL NNNN' "
                        f"ou 'CRL NNNN-NN' (NIT-DICLA-080). Recebido: "
                        f"{self.acreditacao_cgcre_numero!r}."
                    )
                }
            )

        # 3. ILAC-MRA so para perfil A.
        if self.ilac_mra_aderido and self.perfil_regulatorio != "A":
            raise ValidationError(
                {
                    "ilac_mra_aderido": (
                        "ILAC-MRA aderido so e permitido em tenant perfil A. "
                        f"Perfil atual: {self.perfil_regulatorio}."
                    )
                }
            )

        # 4. Janela de suspensao deve ter ate >= em.
        if (
            self.acreditacao_suspensa_em
            and self.acreditacao_suspensa_ate
            and self.acreditacao_suspensa_ate < self.acreditacao_suspensa_em
        ):
            raise ValidationError(
                {
                    "acreditacao_suspensa_ate": (
                        "Data de fim da suspensao deve ser >= data de inicio."
                    )
                }
            )

        # 5. Vigencia da acreditacao so faz sentido em perfil A (INV-CER-CGCRE-VIG-001).
        if self.acreditacao_vigencia_fim and self.perfil_regulatorio != "A":
            raise ValidationError(
                {
                    "acreditacao_vigencia_fim": (
                        "Vigencia da acreditacao CGCRE so pode ser preenchida em "
                        f"tenant perfil A. Perfil atual: {self.perfil_regulatorio}."
                    )
                }
            )


class DirecaoMudancaPerfilChoices(models.TextChoices):
    """Espelho Django do enum DirecaoMudancaPerfil de dominio."""

    PROVISIONAMENTO_INICIAL = "provisionamento_inicial", "Provisionamento inicial"
    PROMOCAO_REGULATORIA = "promocao_regulatoria", "Promocao regulatoria (D->C->B->A)"
    SUSPENSAO_TEMPORARIA_CGCRE = "suspensao_temporaria_cgcre", "Suspensao temporaria CGCRE"
    CANCELAMENTO_CGCRE = "cancelamento_cgcre", "Cancelamento CGCRE (A->B)"
    REDUCAO_ESCOPO_CGCRE = "reducao_escopo_cgcre", "Reducao de escopo CGCRE"
    CORRECAO_ADMINISTRATIVA = "correcao_administrativa", "Correcao administrativa"
    REBAIXAMENTO_VOLUNTARIO_CLIENTE = (
        "rebaixamento_voluntario_cliente",
        "Rebaixamento voluntario do cliente",
    )


class TenantPerfilHistorico(models.Model):
    """Trilha imutavel de mudancas de perfil de tenant (ADR-0067 §1).

    Append-only enforced via trigger anti-mutacao (migration 0007).
    Shared-across-tenants — sem RLS propria (padrao ADR-0002 §8).
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(
        "tenant.Tenant",
        on_delete=models.PROTECT,
        related_name="historico_perfil",
        help_text="Tenant alvo da mudanca de perfil.",
    )
    perfil_anterior = models.CharField(
        max_length=1,
        null=True,
        blank=True,
        choices=PerfilRegulatorioChoices.choices,
        help_text="Perfil antes. NULL apenas em direcao=provisionamento_inicial.",
    )
    perfil_novo = models.CharField(
        max_length=1,
        choices=PerfilRegulatorioChoices.choices,
        help_text="Perfil apos a mudanca. NOT NULL.",
    )
    direcao = models.CharField(
        max_length=40,
        choices=DirecaoMudancaPerfilChoices.choices,
        help_text="Direcao da mudanca (ADR-0067 + plan.md R3 + A1).",
    )
    motivo = models.TextField(
        help_text=(
            "Justificativa textual. Min 100 chars (CHECK constraint). "
            "Sanitizada via sanitizar_payload_audit antes do INSERT (A8 plan.md)."
        ),
    )
    evento_origem_id = models.UUIDField(null=True, blank=True)
    auditor_cgcre = models.CharField(max_length=200, null=True, blank=True)
    certificado_acreditacao_documento_id = models.UUIDField(null=True, blank=True)
    registrado_em = models.DateTimeField(auto_now_add=True)
    registrado_por_usuario_id = models.UUIDField(null=True, blank=True)
    assinatura_a3_id = models.UUIDField(null=True, blank=True)

    class Meta:
        app_label = "tenant"
        db_table = "tenant_perfil_historico"
        verbose_name = "Historico de perfil de tenant"
        verbose_name_plural = "Historico de perfis de tenants"
        ordering = ["-registrado_em"]

    def __str__(self) -> str:
        prev = self.perfil_anterior or "—"
        return (
            f"{self.tenant.slug}: {prev}→{self.perfil_novo} "
            f"[{self.direcao}] em {self.registrado_em.isoformat()}"
        )

    def delete(self, *args: Any, **kwargs: Any) -> NoReturn:
        """Bloqueio em Python antes do banco — defesa em profundidade."""
        raise RuntimeError(
            "TenantPerfilHistorico e append-only. DELETE proibido "
            "(INV-TENANT-PERFIL-002 + trigger tph_anti_delete_trigger)."
        )

    def save(self, *args: Any, **kwargs: Any) -> None:
        """Bloqueio em Python contra UPDATE — defesa em profundidade.

        INSERT (pk ainda nao gravada) e permitido; UPDATE (pk ja existe) nao.
        """
        if self.pk and TenantPerfilHistorico.objects.filter(pk=self.pk).exists():
            raise RuntimeError(
                "TenantPerfilHistorico e append-only. UPDATE proibido "
                "(INV-TENANT-PERFIL-002 + trigger tph_anti_update_trigger)."
            )
        super().save(*args, **kwargs)
