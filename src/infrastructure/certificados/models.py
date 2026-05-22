"""Modelo stub `Certificado` — Marco 2 cria so o suficiente para destravar
INV-025 (T-EQP-013 trigger PG).

Wave A expandira com:
- emissao A3 cliente-side via Lacuna
- PDF assinado + WORM Backblaze B2
- escopo acreditacao RBC + grandezas + incertezas
- numero NIT-DICLA + signatarios autorizados
- ciclo de revisao

Por ora apenas: tenant, equipamento, status (emitido/revogado/rascunho),
emitido_em, revogado_em. Trigger `equipamento_imutabilidade_pos_cert`
em equipamentos consulta esta tabela (status=emitido + revogado_em IS NULL).
"""

from __future__ import annotations

import uuid
from typing import Any

from django.db import models

from src.infrastructure.equipamentos.models import Equipamento
from src.infrastructure.tenant.models import Tenant


class StatusCertificado(models.TextChoices):
    """Estados do certificado. Marco 2 usa so 3; Wave A pode expandir
    (suspenso, em_revisao, etc) sem migration destrutiva."""

    RASCUNHO = "rascunho", "Rascunho (sem efeito legal)"
    EMITIDO = "emitido", "Emitido (vigente — bloqueia mutacao INV-025)"
    REVOGADO = "revogado", "Revogado (substituido ou erro)"


class CertificadoVigentesManager(models.Manager["Certificado"]):
    """Default manager — filtra so EMITIDO + nao revogado.

    `INV-025` usa esta visao pra detectar mutacao bloqueada. Marco 2:
    1 certificado por equipamento (Wave A introduzira historico).
    """

    def get_queryset(self) -> models.QuerySet[Certificado]:
        return (
            super()
            .get_queryset()
            .filter(status=StatusCertificado.EMITIDO, revogado_em__isnull=True)
        )


class Certificado(models.Model):
    """Stub Marco 2 para destravar INV-025.

    Hooks de codigo (T-EQP-071 hook + Wave A use case `editar_equipamento`)
    consultam `Certificado.vigentes.filter(equipamento_id=eq.id).exists()`
    antes de permitir mutacao em campos criticos. Trigger PG faz a mesma
    checagem como camada B (defesa em profundidade).
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.PROTECT,
        related_name="certificados",
    )
    equipamento = models.ForeignKey(
        Equipamento,
        on_delete=models.PROTECT,
        related_name="certificados",
    )
    status = models.CharField(
        max_length=20,
        choices=StatusCertificado.choices,
        default=StatusCertificado.RASCUNHO,
    )
    emitido_em = models.DateTimeField(
        null=True,
        blank=True,
        help_text=(
            "Quando o cert foi assinado (A3 Wave A). NULL enquanto "
            "rascunho. Marca a transicao para `emitido`."
        ),
    )
    revogado_em = models.DateTimeField(
        null=True,
        blank=True,
        help_text=(
            "Quando o cert foi invalidado. INV-025 deixa de bloquear "
            "mutacao no equipamento quando todos os certs ficam revogados."
        ),
    )
    criado_em = models.DateTimeField(auto_now_add=True, db_index=True)

    objects = CertificadoVigentesManager()
    all_objects = models.Manager()  # noqa: DJ012 -- quirk ruff manager tipado generico

    class Meta:
        app_label = "certificados"
        db_table = "certificados"
        verbose_name = "Certificado (stub Marco 2)"
        verbose_name_plural = "Certificados (stub Marco 2)"
        ordering = ["-criado_em"]
        indexes = [
            # INV-025 query hot path — trigger PG e service usam isso.
            models.Index(
                fields=["equipamento", "status", "revogado_em"],
                name="ix_cert_eq_status_rev",
            ),
            models.Index(fields=["tenant", "status"]),
        ]

    def __str__(self) -> str:
        return (
            f"Cert {self.id} eq={self.equipamento_id} "
            f"status={self.status}"
        )

    def save(self, *args: Any, **kwargs: Any) -> None:
        # Marco 2 stub: nenhuma validacao adicional (Wave A trara).
        super().save(*args, **kwargs)
