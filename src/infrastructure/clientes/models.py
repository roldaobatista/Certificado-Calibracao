"""Modelo Cliente — Wave A · Marco 1 (modulo comercial/clientes).

Cliente eh PF (Pessoa Fisica, CPF) OU PJ (Pessoa Juridica, CNPJ alfanumerico).
A entidade armazena o documento normalizado (sem pontuacao, UPPER pra CNPJ).

Invariantes implementadas:
- INV-024 (dedup): UNIQUE(tenant_id, tipo_pessoa, documento) — impede que o
  mesmo CPF/CNPJ vire 2 clientes no mesmo tenant.
- INV-036 (CNPJ unico por tenant): caso particular de INV-024 quando tipo_pessoa = PJ.

VOs CNPJ/CPF (src/domain/shared/value_objects.py) sao usados no boundary
(serializer DRF) e em clean(). O banco armazena string normalizada.

ADR-0017 (CNPJ alfanumerico): documento aceita [A-Z0-9]{12}[0-9]{2} pra PJ
desde ja; vigencia oficial jul/2026.
"""

from __future__ import annotations

import uuid

from django.core.exceptions import ValidationError
from django.db import models

from src.domain.shared.value_objects import CNPJ, CPF
from src.infrastructure.tenant.models import Tenant


class TipoPessoa(models.TextChoices):
    PF = "PF", "Pessoa Fisica"
    PJ = "PJ", "Pessoa Juridica"


class Cliente(models.Model):
    """Cliente PF ou PJ de um tenant.

    Modelo intencionalmente magrelo no Marco 1: nome + documento + email +
    telefone. Atributos comerciais (endereco, ramo, segmento) entram quando o
    proximo modulo (orcamentos/CRM) pedir — evitamos especular schema.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.PROTECT,
        related_name="clientes",
    )
    tipo_pessoa = models.CharField(
        max_length=2,
        choices=TipoPessoa.choices,
        help_text="PF (CPF) ou PJ (CNPJ alfanumerico IN RFB 2.229/2024).",
    )
    documento = models.CharField(
        max_length=14,
        help_text=(
            "CPF (11 digitos) OU CNPJ (12 alfanumericos + 2 DV digitos). "
            "Armazenado normalizado: sem pontuacao, UPPER para CNPJ."
        ),
    )
    nome = models.CharField(
        max_length=200,
        help_text="Nome completo (PF) ou razao social (PJ).",
    )
    nome_fantasia = models.CharField(max_length=200, blank=True)
    email = models.EmailField(blank=True)
    telefone = models.CharField(
        max_length=20,
        blank=True,
        help_text="Formato livre nesta fase; normalizacao entra com modulo comunicacao.",
    )
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = "clientes"
        db_table = "clientes"
        verbose_name = "Cliente"
        verbose_name_plural = "Clientes"
        ordering = ["nome"]
        constraints = [
            # INV-024 + INV-036: dedup por (tenant_id, tipo_pessoa, documento).
            # Mesmo CPF/CNPJ pode existir em tenants diferentes — multi-tenancy
            # preservado. Dentro de um tenant nao duplica.
            models.UniqueConstraint(
                fields=["tenant", "tipo_pessoa", "documento"],
                name="uq_cliente_tenant_documento",
            ),
        ]
        indexes = [
            models.Index(fields=["tenant", "documento"], name="ix_cliente_tenant_doc"),
            models.Index(fields=["tenant", "nome"], name="ix_cliente_tenant_nome"),
        ]

    def __str__(self) -> str:
        return f"{self.nome} ({self.tipo_pessoa} {self.documento})"

    def clean(self) -> None:
        """Validacao no boundary — chamado por full_clean()."""
        super().clean()
        try:
            if self.tipo_pessoa == TipoPessoa.PF:
                CPF(self.documento)
            elif self.tipo_pessoa == TipoPessoa.PJ:
                CNPJ(self.documento)
            else:
                raise ValidationError({"tipo_pessoa": "Tipo invalido"})
        except ValueError as e:
            raise ValidationError({"documento": str(e)}) from e
