"""Modelo Equipamento — Wave A · Marco 2 (suporte-plataforma/equipamentos).

Equipamento fisico do cliente (balanca, paquimetro, termometro etc.) que
o tenant calibra. Spec: docs/faseamento/M2-equipamentos/spec.md.

Invariantes implementadas (citacao em REGRAS-INEGOCIAVEIS.md a registrar
em P4):
- INV-049 (TAG unica por tenant): UNIQUE parcial
  (tenant_id, tag) WHERE deletado_em IS NULL.
- INV-051 (QR HMAC): QR Code com hash versionado pela `QR_HMAC_KEY_REGISTRO`
  (mesmo padrao FA-A1 PII_HASH_KEY_REGISTRO).
- INV-025 (imutabilidade pos-cert): triggers PG restringem alteracao de
  TAG, NS, fabricante pos primeira emissao de certificado — implementado
  em T-EQP futuro quando modulo `certificados` existir; em Marco 2,
  hooks de codigo + trigger reservada.
- INV-EQP-001 (perfil_tenant_snapshot imutavel) — JSONB + trigger PG
  BEFORE UPDATE; promocao D->A unica via funcao SECURITY DEFINER
  `promover_perfil_equipamento_snapshot` (AC-EQP-001-7b).
- INV-EQP-LOC-001 (localizacao_fisica anti-PII): serializer valida.
- AC-EQP-006-3a (maquina de estados `Equipamento.status`): 7 valores +
  trigger PG `bloquear_transicao_status_equipamento_invalida`.
- AC-EQP-001-8 (P-EQP-T9): `cliente_atual_id` FK ON DELETE SET NULL +
  trigger anti-orfao marca status=orfao_pendente_decisao.

Referencias spec: AC-EQP-001-1 a AC-EQP-001-11. Reviews P2 absorvidos:
P-EQP-T1, T2, T4, T5, T6, T9; P-EQP-R1.
"""

from __future__ import annotations

import uuid

from django.db import models

from src.infrastructure.clientes.models import Cliente
from src.infrastructure.tenant.models import Tenant


class EquipamentoStatus(models.TextChoices):
    """7 estados (AC-EQP-006-3a). Matriz de transicao no trigger PG.

    - `ativo`: estado padrao apos cadastro; calibravel.
    - `inativo_temporario`: manutencao; reversivel via UPDATE.
    - `aposentado`: fim de vida util operacional (reversivel com A3 RT).
    - `em_calibracao_lab`: equipamento entregue ao lab (vinculado a
      EquipamentoRecebimento.status_fluxo_lab).
    - `sucata`: terminal-com-excecao-unica — so transita pra `extraviado`.
    - `orfao_pendente_decisao`: cliente_atual_id virou NULL via LGPD
      eliminacao (AC-EQP-001-8); decisao do tenant: atribuir novo
      cliente ou aposentar.
    - `extraviado`: equipamento sumiu fisicamente (cliente reportou
      roubo; reversivel se recuperado).
    """

    ATIVO = "ativo", "Ativo"
    INATIVO_TEMPORARIO = "inativo_temporario", "Inativo temporario (manutencao)"
    APOSENTADO = "aposentado", "Aposentado (fim de vida util)"
    EM_CALIBRACAO_LAB = "em_calibracao_lab", "Em calibracao no laboratorio"
    SUCATA = "sucata", "Sucata (terminal)"
    ORFAO_PENDENTE_DECISAO = "orfao_pendente_decisao", "Orfao pendente de decisao"
    EXTRAVIADO = "extraviado", "Extraviado"


class EquipamentoAtivosManager(models.Manager["Equipamento"]):
    """Default manager — filtra soft-deleted (padrao Marco 1)."""

    def get_queryset(self) -> models.QuerySet[Equipamento]:
        return super().get_queryset().filter(deletado_em__isnull=True)


class Equipamento(models.Model):
    """Equipamento fisico do cliente (US-EQP-001..006).

    Modelo minimo necessario pra Marco 2; campos descritivos cobertos
    pelo enum `motivo_mudanca` em `EquipamentoVersao` (US-EQP-002) sao
    versionaveis pos-emissao de certificado (INV-025).
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.PROTECT,
        related_name="equipamentos",
    )
    # AC-EQP-001-3 + INV-049: UNIQUE parcial via constraint em Meta.
    tag = models.CharField(
        max_length=50,
        help_text="TAG operacional do equipamento. Unica por tenant (INV-049).",
    )
    numero_serie = models.CharField(
        max_length=100,
        help_text="Numero de serie do fabricante. Imutavel pos-emissao de cert (INV-025).",
    )
    fabricante = models.CharField(
        max_length=100,
        help_text="Imutavel pos-emissao de cert (INV-025).",
    )
    modelo = models.CharField(
        max_length=100,
        help_text="Versionavel pos-cert (US-EQP-002 motivo_mudanca).",
    )
    faixa = models.CharField(
        max_length=100,
        blank=True,
        help_text="Versionavel pos-cert.",
    )
    classe = models.CharField(
        max_length=100,
        blank=True,
        help_text="Versionavel pos-cert.",
    )
    # AC-EQP-001-8 (P-EQP-T9): ON DELETE SET NULL — trigger anti-orfao
    # marca status=orfao_pendente_decisao quando cliente eliminado por LGPD.
    # db_constraint=False: igual ClienteIdentidadeHistorico (Marco 1) -
    # evita FK validation passando por RLS na criacao via Django (cliente
    # esta sob RLS pattern v2). Integridade real garantida por trigger.
    cliente_atual = models.ForeignKey(
        Cliente,
        on_delete=models.SET_NULL,
        related_name="equipamentos",
        null=True,
        blank=True,
        db_constraint=False,
        help_text=(
            "Cliente atual proprietario. db_constraint=False (RLS); ON DELETE "
            "SET NULL via trigger PG; status=orfao_pendente_decisao se eliminado."
        ),
    )
    localizacao_fisica = models.CharField(
        max_length=200,
        blank=True,
        help_text=(
            "Onde o equipamento esta fisicamente. Anti-PII (INV-EQP-LOC-001) "
            "via validator no serializer/clean — proibido CPF/email/nomes."
        ),
    )
    # AC-EQP-001-7 + INV-EQP-001: JSONB imutavel via trigger PG.
    # P-EQP-R1: 7 campos minimos + snapshot_schema_version.
    perfil_tenant_snapshot = models.JSONField(
        default=dict,
        help_text=(
            "Snapshot do perfil do tenant no momento do cadastro. Imutavel "
            "via trigger PG BEFORE UPDATE. Excecao unica via funcao SECURITY "
            "DEFINER `promover_perfil_equipamento_snapshot` (D->A only)."
        ),
    )
    snapshot_schema_version = models.CharField(
        max_length=20,
        default="1.0.0",
        help_text=(
            "Versao semantica do schema do snapshot. Imutavel junto com o "
            "snapshot. Permite parser evoluir sem quebrar snapshots antigos."
        ),
    )
    status = models.CharField(
        max_length=30,
        choices=EquipamentoStatus.choices,
        default=EquipamentoStatus.ATIVO,
        help_text=(
            "Estado operacional. Maquina de transicao via trigger PG "
            "`bloquear_transicao_status_equipamento_invalida` (AC-EQP-006-3a)."
        ),
    )
    criado_em = models.DateTimeField(auto_now_add=True, db_index=True)
    atualizado_em = models.DateTimeField(auto_now=True)
    deletado_em = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Soft-delete; UNIQUE INV-049 parcial WHERE deletado_em IS NULL.",
    )

    # Managers: default filtra soft-deleted; `all_objects` enxerga.
    objects = EquipamentoAtivosManager()
    all_objects = models.Manager()  # noqa: DJ012 -- quirk ruff manager tipado generico (vide Cliente Marco 1)

    class Meta:
        app_label = "equipamentos"
        db_table = "equipamentos"
        verbose_name = "Equipamento"
        verbose_name_plural = "Equipamentos"
        ordering = ["-criado_em"]
        constraints = [
            # INV-049: TAG unica por tenant entre equipamentos vivos.
            models.UniqueConstraint(
                fields=["tenant", "tag"],
                condition=models.Q(deletado_em__isnull=True),
                name="uq_equipamentos_tag_por_tenant_ativos",
            ),
        ]
        indexes = [
            models.Index(fields=["tenant", "status"]),
            models.Index(fields=["tenant", "cliente_atual"]),
        ]

    def __str__(self) -> str:
        return f"{self.tag} ({self.fabricante} {self.modelo})"


class QRCodeAtivosManager(models.Manager["QRCode"]):
    """Default manager — filtra revogados; equivalente a `qrcode_vigente`."""

    def get_queryset(self) -> models.QuerySet[QRCode]:
        return super().get_queryset().filter(revogado_em__isnull=True)


class QRCode(models.Model):
    """Hash QR HMAC-versionado vinculado a um equipamento (SEC-QR-001 / INV-051).

    Cada cadastro de equipamento gera UM `QRCode` ativo. Re-emissao
    (mudanca de TAG, perda fisica de etiqueta) cria NOVO registro e
    revoga o anterior gravando `revogado_em` (soft-revoke; INSERT-only
    pra historico). Validacao de scan via
    `verificar_qr_hash_em_tabela` (consulta UNIQUE; nunca recomputa —
    `INV-EQP-QR-NUNCA-RECOMPUTA`).

    `hash` armazena o digest COMPLETO incluindo prefixo `qrN:` —
    permite resolver versao da chave em tempo de auditoria sem
    metadado paralelo.

    Trigger PG `qrcode_imutavel_pos_insert` bloqueia UPDATE em todos os
    campos exceto `revogado_em` (LGPD art. 6º V exatidao + ISO 17025
    cl. 7.5 imutabilidade de identificadores).
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.PROTECT,
        related_name="qrcodes",
        help_text="Denormalizado pra RLS (mesmo padrao Marco 1).",
    )
    equipamento = models.ForeignKey(
        Equipamento,
        on_delete=models.PROTECT,
        related_name="qrcodes",
        help_text="Equipamento ao qual este QR pertence.",
    )
    hash = models.CharField(
        max_length=255,
        unique=True,
        help_text=(
            "Digest completo `qrN:base64url(...)`. UNIQUE global — colisao "
            "entre tenants e cripto-impossivel com HMAC-SHA256 com chave de "
            "servidor; UNIQUE detecta bug em vez de degradar silenciosamente."
        ),
    )
    emitido_em = models.DateTimeField(
        help_text=(
            "Timestamp usado no payload do HMAC. Imutavel pos-INSERT. "
            "Necessario pra reconstruir a evidencia (nao pra recomputar)."
        ),
    )
    revogado_em = models.DateTimeField(
        null=True,
        blank=True,
        help_text=(
            "Quando o hash foi invalidado (re-emissao por mudanca de TAG, "
            "perda fisica). UNICO campo mutavel apos INSERT."
        ),
    )
    criado_em = models.DateTimeField(auto_now_add=True, db_index=True)

    objects = QRCodeAtivosManager()
    all_objects = models.Manager()  # noqa: DJ012 -- quirk ruff manager tipado (vide Cliente Marco 1)

    class Meta:
        app_label = "equipamentos"
        db_table = "equipamentos_qrcode"
        verbose_name = "QR Code de equipamento"
        verbose_name_plural = "QR Codes de equipamentos"
        ordering = ["-criado_em"]
        indexes = [
            models.Index(fields=["tenant", "equipamento"]),
            models.Index(fields=["equipamento", "revogado_em"]),
        ]

    def __str__(self) -> str:
        return f"QR {self.hash[:14]}... (eq {self.equipamento_id})"
