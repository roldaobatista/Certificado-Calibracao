"""Modelo FeatureFlag — preparacao ADR-0006 + ADR-0015 INV-INT-008.

Tabela "SHARED ACROSS TENANTS" mas com tenant_id (NULL = flag global).
RLS policy especifica (Marco 3) permite leitura cross-tenant SE tenant_id IS NULL.
"""

from __future__ import annotations

import uuid

from django.db import models

from src.infrastructure.tenant.models import Tenant


class FonteFlag(models.TextChoices):
    """De onde a flag vem (auditoria — INV-INT-008)."""

    PLANO = "plano", "Plano comercial (deriva do plano do tenant)"
    OVERRIDE_MANUAL = "override_manual", "Override manual (suporte habilitou pontualmente)"
    A_B_TEST = "a_b_test", "Experimento A/B"
    GLOBAL = "global", "Flag global do produto (tenant_id NULL)"


class FeatureFlag(models.Model):
    """Liga/desliga uma feature pra um tenant (ou globalmente)."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="feature_flags",
        help_text="NULL = flag global (todos os tenants).",
    )
    modulo = models.CharField(
        max_length=50,
        help_text="Modulo dono da flag (ex: 'calibracao', 'fiscal', 'app-tecnico').",
    )
    feature_key = models.CharField(
        max_length=100,
        help_text="Identificador da feature (ex: 'NFS-e-automatico', 'assinatura-a3').",
    )
    ativo = models.BooleanField(default=False)
    fonte = models.CharField(
        max_length=20,
        choices=FonteFlag.choices,
        default=FonteFlag.PLANO,
    )
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = "feature_flag"
        db_table = "feature_flags"
        verbose_name = "Feature flag"
        verbose_name_plural = "Feature flags"
        ordering = ["modulo", "feature_key"]
        constraints = [
            models.UniqueConstraint(
                fields=["tenant", "modulo", "feature_key"],
                name="uq_feature_flag_tenant_modulo_key",
            ),
        ]
        indexes = [
            models.Index(fields=["tenant", "modulo"], name="ix_flag_tenant_modulo"),
        ]

    def __str__(self) -> str:
        escopo = self.tenant.slug if self.tenant else "(global)"
        return f"[{escopo}] {self.modulo}.{self.feature_key} = {self.ativo}"
