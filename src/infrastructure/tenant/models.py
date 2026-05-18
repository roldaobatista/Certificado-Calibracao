"""Modelo Tenant — cada linha = 1 cliente do sistema.

Tabela "SHARED ACROSS TENANTS" (ADR-0002 §8) — NAO tem tenant_id proprio.
Acesso a esta tabela e protegido por permissoes do Django Admin + perfis
de aplicacao (ADR-0012), nao por RLS.
"""

from __future__ import annotations

import uuid

from django.db import models


class StatusLifecycle(models.TextChoices):
    """Estados possiveis de um tenant (preparacao ADR-0015 lifecycle)."""

    ATIVO = "ativo", "Ativo"
    SUSPENSO = "suspenso", "Suspenso (inadimplencia ou desativacao temporaria)"
    CANCELADO = "cancelado", "Cancelado (encerrado pelo cliente)"


class Tenant(models.Model):
    """Um cliente do sistema. Provisiona-se em onboarding (ADR-0015)."""

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
    # US-CLI-004 R3 advogado + INV-CLI-BLOQ-001: bloqueio automatico fica OFF
    # por default no Marco 1. Wave A liga quando comunicacao-omnichannel
    # entregar a regua D+30/60/89.
    bloqueio_automatico_inadimplencia_habilitado = models.BooleanField(
        default=False,
        help_text=(
            "Se True, job D+90 marca clientes inadimplentes como bloqueados. "
            "Wave A: exige tambem registro da regua D+30/60/89 antes do bloqueio "
            "(CDC art. 6 III/IV + Lei 14.181/2021)."
        ),
    )
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = "tenant"
        db_table = "tenants"
        verbose_name = "Tenant"
        verbose_name_plural = "Tenants"
        ordering = ["nome_fantasia"]

    def __str__(self) -> str:
        return f"{self.nome_fantasia} ({self.slug})"
