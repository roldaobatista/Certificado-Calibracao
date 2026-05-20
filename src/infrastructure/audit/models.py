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
from typing import Any

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
    hash_anterior = models.CharField(  # noqa: DJ001 -- NULL = genese da cadeia (sem predecessor), semanticamente != "" (string vazia seria hash valido)
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
    # FA-C1: ordem monotonica da cadeia (SEQUENCE global). Encadeamento e
    # por-tenant; sequencia so desempata (timestamp colide em microssegundo
    # sob lock). `db_default=nextval('auditoria_seq')` (Django 5.0) faz o
    # INSERT do ORM emitir DEFAULT em vez de NULL — a sequence (criada em
    # audit/0009) preenche. NOT NULL no banco.
    sequencia = models.BigIntegerField(
        editable=False,
        db_default=models.Func(models.Value("auditoria_seq"), function="nextval"),
    )

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

    def save(self, *args: Any, **kwargs: Any) -> None:
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

    def delete(self, *args: Any, **kwargs: Any) -> tuple[int, dict[str, int]]:
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


class BusOutbox(models.Model):
    """Fila intermediaria de eventos de dominio (T-CLI-107 / INV-INT-010).

    Padrao outbox transacional: `publicar_evento(outbox=True)` faz INSERT
    aqui no MESMO `transaction.atomic` do caller, junto com o INSERT na
    cadeia hash F-A (`registrar_em_cadeia`). Worker
    `processar_outbox_em_contexto_tenant` drena (FOR UPDATE SKIP LOCKED)
    e entrega `envelope_jsonb` ao consumer registrado pra `acao`.

    Garantias:
    1. Atomicidade: INSERT no `atomic` do caller — nao abre tx propria.
    2. Idempotencia: UNIQUE (causation_id, acao) com ON CONFLICT DO
       NOTHING no helper.
    3. Sanitizacao em escrita: `envelope_jsonb` ja vem sanitizado por
       `sanitizar_payload_audit` no helper unico (SEC-SANITIZE-001).
    4. Multi-tenant: RLS FORCE + predicate identico ao de Auditoria
       (BLOQ-A do review tech-lead).
    5. Anti-PII na `acao`: CHECK constraint enum semantico
       (BLOQ-A1 advogado — slug `dominio.entidade.operacao`).
    6. `ultimo_erro` ja vem sanitizado por `sanitizar_erro_para_outbox`
       (BLOQ-A4 advogado — truncado 500c).
    7. Poison message: `tentativas >= 5` para de drenar; `listar_outbox
       _envenenado` mostra pro DPO/SRE sem expor envelope.

    Retencao: ≤ 7 dias apos `processado_em` (matriz §2). NAO eh
    evidencia regulatoria — fonte da verdade eh a cadeia F-A.
    Fora do escopo art. 18 II/V LGPD (POLITICA_BUS_OUTBOX em
    audit/politicas_lgpd.py).

    `causation_id` eh dado pessoal indireto (LGPD art. 12) — Wave A
    restringe SELECT a perfis dpo + sre via AuthorizationProvider.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    causation_id = models.UUIDField(
        help_text="UUID que liga o evento a request/comando original. Chave de idempotencia.",
    )
    acao = models.CharField(
        max_length=100,
        help_text="Enum semantico (slug). CHECK constraint anti-PII no banco.",
    )
    envelope_jsonb = models.JSONField(
        help_text="Envelope completo sanitizado em escrita. CHECK pg_column_size < 64 KiB.",
    )
    tenant_id = models.UUIDField(
        null=True,
        blank=True,
        db_index=True,
        help_text="NULL = evento sistema (provisioning, manutencao).",
    )
    criado_em = models.DateTimeField(auto_now_add=True, db_index=True)
    processado_em = models.DateTimeField(
        null=True,
        blank=True,
        help_text="NULL = pendente; preenchido pelo worker apos dispatch OK.",
    )
    tentativas = models.SmallIntegerField(
        default=0,
        help_text="Incrementado em Tx-1 antes do dispatch (sobrevive a crash). "
        "tentativas >= 5 vira poison message — listar_outbox_envenenado mostra.",
    )
    ultimo_erro = models.TextField(  # noqa: DJ001 -- NULL eh "sem erro"; "" seria ambiguidade.
        null=True,
        blank=True,
        help_text="Sanitizado + truncado 500c por sanitizar_erro_para_outbox (BLOQ-A4).",
    )

    class Meta:
        app_label = "audit"
        db_table = "bus_outbox"
        verbose_name = "Linha do outbox (T-CLI-107)"
        verbose_name_plural = "Bus outbox (fila intermediaria)"
        ordering = ["criado_em"]
        constraints = [
            models.UniqueConstraint(
                fields=["causation_id", "acao"],
                name="bus_outbox_idempotencia",
            ),
        ]
        indexes = [
            models.Index(
                fields=["processado_em", "tentativas", "criado_em"],
                name="ix_bus_outbox_drenar",
                # Worker drena WHERE processado_em IS NULL AND tentativas < 5
                # ORDER BY criado_em.
            ),
        ]

    def __str__(self) -> str:
        marca = (
            f"processada {self.processado_em:%Y-%m-%d %H:%M}"
            if self.processado_em
            else f"pendente (tent={self.tentativas})"
        )
        return f"{self.acao} tenant={self.tenant_id} [{marca}]"


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
    # FA-A1: hash de PII agora prefixado com versao da chave ("v1:"+64hex).
    # TextField (sem limite) — imune a crescimento futuro do key_id.
    ip_hash = models.TextField(blank=True)
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


class BreakerAcessoPIIEvento(models.Model):
    """T-CLI-104 — evento do circuit breaker observado pra `AcessoDadosCliente`.

    Cada chamada de `registrar_acesso_dados_cliente_com_breaker` grava UM
    evento aqui via conexao paralela autocommit (`breaker_writer`):
    - ok=True quando gravacao foi bem-sucedida
    - ok=False quando levantou (e o caller propagou — fail-loud)

    Conexao autocommit garante que o evento de falha SOBREVIVE ao rollback
    do request HTTP do caller (sem isso o breaker fica cego nas falhas que
    existe pra contar — CRÍTICO T2 do review tech-lead).

    Sliding window 5min + threshold OR `(pct >= 0.1% AND total >= 1000)
    OR (falhas_absolutas >= 3)` é avaliada por
    `avaliar_circuit_breaker_acesso_pii`. Tenants violando o limiar
    geram evento P1 imutavel `sistema.breaker_acesso_pii.disparado` na
    cadeia hash F-A (25 anos — evidencia de longo prazo, BLOQ-C3
    corretora).

    Retencao: 7 dias (matriz §2). Cleanup Wave A.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant_id = models.UUIDField(db_index=True)
    ts = models.DateTimeField(auto_now_add=True, db_index=True)
    ok = models.BooleanField(
        help_text="True = gravação OK; False = registrar_acesso_dados_cliente levantou."
    )

    class Meta:
        app_label = "audit"
        db_table = "breaker_acesso_pii_evento"
        verbose_name = "Evento do breaker AcessoDadosCliente (T-CLI-104)"
        verbose_name_plural = "Eventos do breaker AcessoDadosCliente"
        ordering = ["-ts"]
        indexes = [
            models.Index(fields=["tenant_id", "-ts"], name="ix_breaker_acesso_pii_t_ts"),
        ]

    def __str__(self) -> str:
        marca = "ok" if self.ok else "falhou"
        return f"{self.ts:%Y-%m-%d %H:%M:%S} tenant={self.tenant_id} [{marca}]"
