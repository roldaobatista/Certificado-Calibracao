"""WebhookDestino — cadastro DPA + chave HMAC + politica de rotacao.

Implementa INV-WEBHOOK-OUT-005 (F-C1 P3 retrofit / R-5 / LGP-FC1-02):
adapter REJEITA chamada quando `dpa_assinado_em IS NULL` ou
`dpa_vence_em < hoje` ou `chave_expires_at < hoje` ou
`desativado_em IS NOT NULL`.

LGPD art. 39 exige contrato escrito (DPA) com operador. Cada destino
webhook out (Asaas, INMETRO, SendGrid, Lacuna, KMS, ...) e um operador
ou destinatario distinto — exige cadastro com base legal + finalidade +
categorias de dados.

Cadastro e mutavel (administracao); historico via audit trail externo
(`audit_trail` da F-A) + soft-delete (`desativado_em`, ADR-0031 padrao
configuracoes mutaveis).

Multi-tenant: cada tenant tem seus proprios destinos (RLS — INV-TENANT-001).
"""

from __future__ import annotations

import uuid

from django.db import models


class PapelLGPD(models.TextChoices):
    """Papel do destino na LGPD (art. 5, 6, 39)."""

    CONTROLADOR = "controlador", "Controlador (compartilhamento)"
    OPERADOR = "operador", "Operador (DPA obrigatorio art. 39)"
    TERCEIRO = "terceiro_destinatario", "Terceiro destinatario"


class CategoriaDado(models.TextChoices):
    """Categorias de PII que o adapter envia para o destino."""

    NOME = "nome", "Nome"
    CPF = "cpf", "CPF"
    CNPJ = "cnpj", "CNPJ"
    EMAIL = "email", "Email"
    TELEFONE = "telefone", "Telefone"
    ENDERECO = "endereco", "Endereco"
    VALOR_MONETARIO = "valor_monetario", "Valor monetario"
    METADADO_OS = "metadado_os", "Metadado OS (numero, status)"
    CERTIFICADO = "certificado", "Certificado (numero, dados tecnicos)"
    NENHUM = "nenhum", "Nenhum (healthcheck, ping)"


class WebhookDestino(models.Model):
    """Destino canonico de chamada outbound (com cadastro DPA + chave HMAC).

    Mutavel (campos `nome`, `url_base`, `categorias_dados`, etc. mudam quando
    o operador altera politica). Soft-delete via `desativado_em` (ADR-0031).
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant_id = models.UUIDField(db_index=True)

    nome = models.CharField(max_length=120, help_text="Ex: 'Asaas', 'INMETRO', 'SendGrid'.")
    url_base = models.URLField(
        max_length=500,
        help_text="URL base do destino (ex: https://api.asaas.com). Sem path final.",
    )

    papel_lgpd = models.CharField(max_length=30, choices=PapelLGPD.choices)
    dpa_url = models.URLField(
        max_length=500,
        help_text="Link pro DPA assinado (S3, Drive interno, etc.).",
    )
    dpa_assinado_em = models.DateField(help_text="Data de assinatura do DPA.")
    dpa_vence_em = models.DateField(
        help_text="Data limite de vigencia do DPA (null/infinito proibido)."
    )
    finalidade = models.TextField(
        help_text="Ex: 'cobranca recorrente cliente final', 'envio cartao verde INMETRO'.",
    )
    categorias_dados = models.JSONField(
        help_text="Array de CategoriaDado. Adapter valida payload contra esta lista.",
        default=list,
    )

    chave_hmac_id = models.CharField(
        max_length=120,
        help_text="ID opaco da chave HMAC (lookup em KMS quando F-C3; ate la, env var).",
    )
    chave_expires_at = models.DateField(
        help_text="Vencimento da chave HMAC (rotacao <=90d - SEG-FC1-03).",
    )

    permite_http = models.BooleanField(
        default=False,
        help_text="Se True, permite porta 80 (anti-pratica; usar so em destino legado).",
    )

    criado_em = models.DateTimeField(auto_now_add=True)
    criado_por = models.UUIDField()
    desativado_em = models.DateTimeField(null=True, blank=True, db_index=True)
    desativado_por = models.UUIDField(null=True, blank=True)
    desativado_motivo = models.TextField(blank=True)

    class Meta:
        db_table = "webhook_destino"
        verbose_name = "Webhook destino"
        verbose_name_plural = "Webhook destinos"
        constraints = [
            models.UniqueConstraint(
                fields=["tenant_id", "nome"],
                condition=models.Q(desativado_em__isnull=True),
                name="webhook_destino_nome_unique_por_tenant_ativo",
            ),
            models.CheckConstraint(
                check=models.Q(dpa_vence_em__gt=models.F("dpa_assinado_em")),
                name="webhook_destino_dpa_vigencia_coerente",
            ),
        ]
        indexes = [
            models.Index(fields=["tenant_id", "dpa_vence_em"]),
            models.Index(fields=["tenant_id", "chave_expires_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.nome} ({self.tenant_id})"

    @property
    def esta_ativo(self) -> bool:
        return self.desativado_em is None

    def dpa_vigente_em(self, data) -> bool:
        return self.dpa_assinado_em <= data <= self.dpa_vence_em

    def chave_vigente_em(self, data) -> bool:
        return data <= self.chave_expires_at
