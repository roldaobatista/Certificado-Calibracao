"""Modelo `ChaveIdempotencia` — F-A horizontal (T-EQP-003 / P-EQP-T6).

Politica (P-EQP-T6, plan.md M2):
- TTL 24h (chave nasce em `criada_em`, expira em `expira_em = criada_em + 24h`)
- UNIQUE `(tenant_id, endpoint, chave)` — chave so colide DENTRO do mesmo
  tenant + endpoint. Tenants nao se enxergam (RLS + UNIQUE composto).
- `status`:
    em_processo → request entrou, ainda nao concluiu (concorrencia → 425)
    concluida   → resposta cacheada disponivel pra replay
    falhada     → erro permanente, retorna mesmo erro pro retry
- `payload_hash`: SHA256 do payload normalizado. Mesma chave + payload
  diferente → 422 (cliente reutilizou chave indevidamente).
- `response_status` + `response_body_resumo`: minimo pra replay. NAO
  guarda PDF/binarios — apenas metadados pra reconstruir a resposta
  determinante (pra etiqueta: `qrcode_id` + `equipamento_tag`).

Imutabilidade pos-concluida garantida por trigger PG (migration 0001).
RLS pattern v2 (ADR-0002 §6) — chave e tenant-scoped.
"""

from __future__ import annotations

import uuid

from django.db import models

from src.infrastructure.tenant.models import Tenant


class StatusChaveIdempotencia(models.TextChoices):
    """3 estados do ciclo de vida da chave (T-EQP-003 / P-EQP-T6)."""

    EM_PROCESSO = "em_processo", "Em processo"
    CONCLUIDA = "concluida", "Concluida"
    FALHADA = "falhada", "Falhada"


class ChaveIdempotencia(models.Model):
    """Chave de idempotencia para POST criticos (F-A horizontal).

    Cada combinacao `(tenant_id, endpoint, chave)` e UNIQUE — segunda
    chamada com mesma trinca dispara replay/425/422 conforme estado.

    Trigger PG `chave_idempotencia_imutavel_pos_concluida` bloqueia
    qualquer UPDATE quando status=concluida ou falhada (terminal).
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.PROTECT,
        related_name="chaves_idempotencia",
        help_text="Denormalizado pra RLS (mesmo padrao Marco 1).",
    )
    endpoint = models.CharField(
        max_length=120,
        help_text=(
            "Identificador estavel do endpoint (ex: "
            "'equipamentos.etiqueta', 'equipamentos.transferir'). NUNCA "
            "trocar sem migracao consciente — chaves antigas viram orfas."
        ),
    )
    chave = models.UUIDField(
        help_text=(
            "UUID enviado pelo cliente no header `Idempotency-Key`. "
            "Cliente gera UMA vez antes da 1a tentativa (RFC draft "
            "ietf-httpapi-idempotency-key-header)."
        ),
    )
    payload_hash = models.CharField(
        max_length=64,
        help_text=(
            "SHA256-hex do payload normalizado (resource_id + body). "
            "Mesma `chave` com payload_hash diferente → 422 (politica "
            "P-EQP-T6)."
        ),
    )
    usuario_id = models.UUIDField(
        help_text=(
            "Quem fez a chamada (autoria). Defesa em profundidade: chave "
            "criada por user A nao pode ser replayed por user B (mesmo "
            "tenant) — service compara antes de aceitar."
        ),
    )
    status = models.CharField(
        max_length=20,
        choices=StatusChaveIdempotencia.choices,
        default=StatusChaveIdempotencia.EM_PROCESSO,
    )
    response_status = models.SmallIntegerField(
        null=True,
        blank=True,
        help_text="HTTP status devolvido na 1a execucao (replay devolve igual).",
    )
    response_body_resumo = models.JSONField(
        null=True,
        blank=True,
        help_text=(
            "Resumo determinante da resposta (NUNCA PDF/binario). "
            "Para etiqueta: {qrcode_id, equipamento_tag}. Permite que "
            "a 2a chamada re-renderize o mesmo artefato sem armazenar "
            "binarios no DB."
        ),
    )
    criada_em = models.DateTimeField(auto_now_add=True, db_index=True)
    concluida_em = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Timestamp da transicao para `concluida` ou `falhada`.",
    )
    expira_em = models.DateTimeField(
        db_index=True,
        help_text=(
            "criada_em + TTL (24h padrao). Apos esta data, replay retorna "
            "409 (chave expirada — politica P-EQP-T6)."
        ),
    )

    class Meta:
        app_label = "idempotencia"
        db_table = "idempotencia_chave"
        verbose_name = "Chave de idempotencia"
        verbose_name_plural = "Chaves de idempotencia"
        ordering = ["-criada_em"]
        constraints = [
            models.UniqueConstraint(
                fields=["tenant", "endpoint", "chave"],
                name="idempotencia_chave_uniq_tenant_endpoint",
            ),
        ]
        indexes = [
            models.Index(fields=["expira_em"]),
            models.Index(fields=["tenant", "endpoint", "status"]),
        ]

    def __str__(self) -> str:
        return f"{self.endpoint}[{self.chave}] {self.status}"
