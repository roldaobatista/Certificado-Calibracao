"""Modelo Auditoria — INSERT-only com hash chain.

Marco 2 entrega o MODELO (campos + indices). Marco 4 entrega:
- Helper que calcula hash_atual = sha256(hash_anterior || payload_canonicalizado)
- Trigger PG que bloqueia UPDATE/DELETE nesta tabela (imutabilidade hard)
- Job Procrastinate que exporta linhas pra Backblaze B2 hourly

Por que hash chain: se alguem (humano ou agente IA) tentar adulterar uma linha,
a cadeia quebra na proxima verificacao. Conformidade ISO 17025 + RBC + LGPD.
"""

from __future__ import annotations

import uuid

from django.db import models

from src.infrastructure.tenant.models import Tenant
from src.infrastructure.usuario.models import Usuario


class Auditoria(models.Model):
    """Linha imutavel da trilha de auditoria. Append-only.

    `payload_jsonb` deve ser canonicalizado (chaves ordenadas, sem espaco,
    datetimes ISO-8601 UTC) ANTES de calcular hash_atual. Marco 4 implementa
    o helper.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="auditoria",
        help_text="NULL = evento global (provisioning de tenant, manutencao).",
    )
    usuario = models.ForeignKey(
        Usuario,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="auditoria",
        help_text="NULL = evento do sistema (cron, integracao externa).",
    )
    action = models.CharField(
        max_length=100,
        help_text="Identificador semantico (ex: 'usuario.criado', 'certificado.emitido').",
    )
    resource_summary = models.CharField(
        max_length=255,
        help_text="Resumo legivel do recurso afetado (ex: 'Certificado #123 / Tenant slug').",
    )
    payload_jsonb = models.JSONField(
        help_text="Payload completo da acao. Canonicalizado antes de calcular hash.",
    )
    hash_anterior = models.CharField(
        max_length=64,
        null=True,
        blank=True,
        help_text="sha256 do hash_atual da linha imediatamente anterior. NULL = primeira linha.",
    )
    hash_atual = models.CharField(
        max_length=64,
        help_text="sha256(hash_anterior || payload_canonicalizado). Calculado no Marco 4.",
    )
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        app_label = "audit"
        db_table = "auditoria"
        verbose_name = "Linha de auditoria"
        verbose_name_plural = "Auditoria (trilha imutavel)"
        ordering = ["-timestamp"]
        indexes = [
            models.Index(fields=["tenant", "-timestamp"], name="ix_audit_tenant_ts"),
            models.Index(fields=["action", "-timestamp"], name="ix_audit_action_ts"),
            models.Index(fields=["usuario", "-timestamp"], name="ix_audit_user_ts"),
        ]

    def __str__(self) -> str:
        return f"{self.timestamp:%Y-%m-%d %H:%M:%S} {self.action} ({self.resource_summary})"

    def save(self, *args: object, **kwargs: object) -> None:
        """Modelo Auditoria so permite INSERT (defesa de aplicacao).

        Trigger PG no Marco 4 reforca isso a nivel de banco. Quem tentar
        chamar `.save()` numa instancia ja persistida leva RuntimeError.
        """
        if self.pk is not None and Auditoria.objects.filter(pk=self.pk).exists():
            raise RuntimeError(
                "Auditoria e INSERT-only. UPDATE bloqueado em codigo (Marco 2) e "
                "em trigger PG (Marco 4)."
            )
        super().save(*args, **kwargs)

    def delete(self, *args: object, **kwargs: object) -> None:
        raise RuntimeError(
            "Auditoria e INSERT-only. DELETE bloqueado em codigo (Marco 2) e "
            "em trigger PG (Marco 4)."
        )
