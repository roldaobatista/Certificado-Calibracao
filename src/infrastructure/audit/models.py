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


# =============================================================
# Acesso a dados de cliente (US-CLI-002 — INV-013)
# Tabela paralela a `auditoria` focada em LOG DE VISUALIZACAO de PII.
# 8 finalidades cravadas (R2 advogado) + 5 categorias de dado (R1).
# =============================================================


class FinalidadeAcessoCliente(models.TextChoices):
    """Cravado pelo advogado em 2026-05-18 (R2 US-CLI-002).

    Distinto das 4 bases legais (`finalidades-lgpd.md`) — aqui sao
    propositos operacionais que justificam visualizar dados do cliente.
    """

    ATENDIMENTO_POS_VENDA = "atendimento_pos_venda"
    PREPARAR_ORCAMENTO = "preparar_orcamento"
    EXECUTAR_OS = "executar_os"
    EMITIR_DOCUMENTO_FISCAL = "emitir_documento_fiscal"
    COBRANCA_INADIMPLENCIA = "cobranca_inadimplencia"
    AUDITORIA_INTERNA = "auditoria_interna"
    ATENDIMENTO_LGPD_TITULAR = "atendimento_lgpd_titular"
    INVESTIGACAO_INCIDENTE = "investigacao_incidente"
    # US-CLI-003 R7 advogado: leitura do historico de importacoes dispara INV-013.
    CONSULTA_RELATORIO_IMPORTACAO = "consulta_relatorio_importacao"


class CategoriaDadoAcessado(models.TextChoices):
    """R1 advogado — ANPD precisa estimar gravidade em incidente."""

    PII_IDENTIFICADORA = "pii_identificadora", "PII identificadora (nome, CPF/CNPJ, contato)"
    PII_SENSIVEL = "pii_sensivel", "PII sensivel (LGPD art. 5 II)"
    DADO_FISCAL = "dado_fiscal", "Dado fiscal (NF-e, retencao)"
    DADO_REGULATORIO = "dado_regulatorio", "Dado regulatorio (certificado ISO 17025)"
    METADADO = "metadado", "Metadado (sem PII — UUIDs, timestamps)"


class AcessoDadosCliente(models.Model):
    """Log de visualizacao de dados de cliente (US-CLI-002 — INV-013).

    Tabela imutavel. Trigger PG bloqueia UPDATE/DELETE (migration 0005).
    RLS pattern v2 + retencao 5 anos (R4 advogado — `retencao-matriz.md`
    linha "audit acoes sensiveis"). Crypto-shredding Wave B.

    `recurso` JSONB sem PII cru (R1 advogado) — apenas UUIDs.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant_id = models.UUIDField(db_index=True)
    usuario_id = models.UUIDField(null=True, blank=True, db_index=True)
    # cliente_id NULL = acesso agregado (lista historica de importacoes, busca
    # de clientes, etc — INV-013 cobre tambem visualizacoes sem cliente unico).
    # CONCERN auditor Seguranca 2026-05-18.
    cliente_id = models.UUIDField(null=True, blank=True, db_index=True)
    finalidade = models.CharField(
        max_length=40,
        choices=FinalidadeAcessoCliente.choices,
        help_text="Enum cravado pelo advogado (R2). CHECK constraint na migration.",
    )
    categoria_dado_acessado = models.CharField(
        max_length=30,
        choices=CategoriaDadoAcessado.choices,
        default=CategoriaDadoAcessado.PII_IDENTIFICADORA,
    )
    recurso = models.JSONField(
        default=dict,
        help_text="UUIDs + metadados (sem PII cru) — R1 advogado.",
    )
    ip_hash = models.CharField(max_length=64, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        app_label = "audit"
        db_table = "acessos_dados_cliente"
        verbose_name = "Acesso a dados de cliente (INV-013)"
        verbose_name_plural = "Acessos a dados de cliente"
        ordering = ["-timestamp"]
        indexes = [
            models.Index(
                fields=["tenant_id", "cliente_id", "-timestamp"],
                name="ix_acessos_tenant_cli_ts",
            ),
            models.Index(
                fields=["tenant_id", "usuario_id", "-timestamp"],
                name="ix_acessos_tenant_user_ts",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.timestamp:%Y-%m-%d %H:%M} cli={self.cliente_id} ({self.finalidade})"
