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
from typing import Any

from django.db import models

from src.infrastructure.clientes.models import Cliente
from src.infrastructure.tenant.models import Tenant
from src.infrastructure.usuario.models import Usuario


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


class MotivoMudancaEquipamentoVersao(models.TextChoices):
    """Enum fechado RBC B7 + P-EQP-R2 (9 valores).

    Os primeiros 6 sao do AC-EQP-002-1 original (revisao spec STABLE).
    P-EQP-R2 expandiu para 9 com motivos operacionais frequentes que
    o agente IA precisaria pedir ao Roldao caso a lista nao incluisse.

    Motivos que OBRIGAM aprovacao gestor_qualidade (US-EQP-002b):
    `outros`, `substituicao_componente_critico`, `atualizacao_firmware`.
    Motivos que NAO obrigam aprovacao (rotina): demais 6.
    """

    CORRECAO_CADASTRAL = "correcao_cadastral", "Correcao cadastral"
    MUDANCA_LOCAL = "mudanca_local", "Mudanca de local fisico"
    TROCA_ACESSORIO = "troca_acessorio", "Troca de acessorio"
    RECALIBRACAO_DIFERENTE_FAIXA = (
        "recalibracao_diferente_faixa",
        "Recalibracao em faixa diferente",
    )
    MUDANCA_CLASSE_METROLOGICA = (
        "mudanca_classe_metrologica",
        "Mudanca de classe metrologica (D->A via funcao SECURITY DEFINER)",
    )
    AJUSTE_POS_CALIBRACAO = (
        "ajuste_pos_calibracao",
        "Ajuste pos-calibracao (ISO 17025 cl. 6.4.10 — rotina)",
    )
    SUBSTITUICAO_COMPONENTE_CRITICO = (
        "substituicao_componente_critico",
        "Substituicao de componente critico (afeta rastreabilidade)",
    )
    ATUALIZACAO_FIRMWARE = (
        "atualizacao_firmware",
        "Atualizacao de firmware (OIML D 31)",
    )
    OUTROS = "outros", "Outros (motivo_detalhe obrigatorio + aprovacao)"


# T-EQP-015 (P-EQP-R2): conjunto canonico de motivos que disparam fluxo
# de aprovacao US-EQP-002b. Defesa em profundidade: enum + tupla + check
# constraint (Wave A).
MOTIVOS_QUE_OBRIGAM_APROVACAO: frozenset[str] = frozenset(
    {
        MotivoMudancaEquipamentoVersao.OUTROS.value,
        MotivoMudancaEquipamentoVersao.SUBSTITUICAO_COMPONENTE_CRITICO.value,
        MotivoMudancaEquipamentoVersao.ATUALIZACAO_FIRMWARE.value,
    }
)


class StatusAprovacaoVersao(models.TextChoices):
    """Enum fechado de estados da aprovacao (AC-EQP-002b-1).

    Maquina:
    - PENDENTE -> APROVADA (gestor_qualidade decide)
    - PENDENTE -> REJEITADA (gestor_qualidade decide)
    - PENDENTE -> EXPIRADA (job Procrastinate apos SLA)
    - APROVADA / REJEITADA / EXPIRADA = TERMINAIS (trigger PG bloqueia
      qualquer UPDATE saindo destes estados).
    """

    PENDENTE = "pendente", "Pendente de decisao do gestor"
    APROVADA = "aprovada", "Aprovada"
    REJEITADA = "rejeitada", "Rejeitada"
    EXPIRADA = "expirada", "Expirada por SLA"


STATUS_TERMINAIS_APROVACAO: frozenset[str] = frozenset(
    {
        StatusAprovacaoVersao.APROVADA.value,
        StatusAprovacaoVersao.REJEITADA.value,
        StatusAprovacaoVersao.EXPIRADA.value,
    }
)


class EquipamentoVersao(models.Model):
    """Versao auditada de mudanca em campo descritivo do equipamento
    (US-EQP-002 — AC-EQP-002-1; T-EQP-012).

    Insert-only (sem UPDATE/DELETE — INV-025 imutabilidade pos-emissao
    de certificado sera cravada via trigger PG em T-EQP-013 quando o
    modulo certificados existir).

    Hashes:
    - `valor_anterior_hash`/`valor_novo_hash`: HMAC-SHA256 com salt do
      tenant (mesmo helper `hashear_pii_com_salt_tenant` do Marco 1).
      Permite auditoria sem expor valor em claro (INV-EQP-VERSAO-002).

    Assinatura A3 RT (P-EQP-T5):
    - `assinatura_a3_referencia`: UUID opaco emitido pelo Lacuna
      cliente-side (GATE-EQP-1 Wave A). Em Marco 2 o campo aceita NULL
      para motivos que nao exigem A3; quando preenchido, os outros 2
      campos (`assinada_em`, `certificado_emissor_hash`) tornam-se
      obrigatorios via CHECK constraint.
    - Proibido `assinatura_a3_hash` cru ou truncado (INV-EQP-VERSAO-002
      lista negativa).

    Snapshot:
    - `snapshot_jsonb`: dump dos campos versionaveis no momento da
      criacao da versao — permite reconstruir o estado historico sem
      depender de joins com a tabela viva.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.PROTECT,
        related_name="equipamento_versoes",
    )
    equipamento = models.ForeignKey(
        Equipamento,
        on_delete=models.PROTECT,
        related_name="versoes",
    )
    campo = models.CharField(
        max_length=50,
        help_text=(
            "Nome do campo do Equipamento que mudou (`modelo`, `faixa`, "
            "`classe`, `localizacao_fisica`, `perfil_tenant_snapshot`)."
        ),
    )
    valor_anterior_hash = models.CharField(
        max_length=128,
        help_text=(
            "HMAC-SHA256 do valor anterior em claro, salt do tenant. "
            "Nunca o valor cru (INV-EQP-VERSAO-002)."
        ),
    )
    valor_novo_hash = models.CharField(
        max_length=128,
        help_text=(
            "HMAC-SHA256 do valor novo em claro, salt do tenant. "
            "Nunca o valor cru (INV-EQP-VERSAO-002)."
        ),
    )
    motivo_mudanca = models.CharField(
        max_length=40,
        choices=MotivoMudancaEquipamentoVersao.choices,
        help_text="Enum fechado RBC B7 + P-EQP-R2 (9 valores).",
    )
    motivo_detalhe = models.TextField(
        blank=True,
        default="",
        help_text=(
            "Texto livre obrigatorio (>=100 chars) quando motivo_mudanca "
            "obriga aprovacao (outros/substituicao_componente_critico/"
            "atualizacao_firmware). Anti-PII via clean (INV-EQP-VERSAO-001)."
        ),
    )
    snapshot_jsonb = models.JSONField(
        default=dict,
        blank=True,
        help_text=(
            "Dump dos campos versionaveis do Equipamento no momento da "
            "criacao desta versao. Permite reconstruir estado historico "
            "sem depender de joins. `{}` aceito (versoes minimas em "
            "Marco 2; populado pelo service Wave A)."
        ),
    )
    cliente_atual_id_no_momento = models.UUIDField(
        null=True,
        blank=True,
        help_text=(
            "Snapshot opaco do cliente_atual_id no momento. db_constraint "
            "= n/a (UUID puro) - cliente pode ser eliminado por LGPD."
        ),
    )
    criado_por = models.ForeignKey(
        Usuario,
        on_delete=models.PROTECT,
        related_name="equipamento_versoes_criadas",
        help_text="Usuario que solicitou a versao.",
    )
    # P-EQP-T5 — referencia A3 do RT (NUNCA hash truncado).
    assinatura_a3_referencia = models.UUIDField(
        null=True,
        blank=True,
        help_text=(
            "UUID opaco emitido pelo Lacuna cliente-side (GATE-EQP-1 Wave A). "
            "NULL para motivos que nao exigem A3. Proibido hash truncado "
            "(INV-EQP-VERSAO-002)."
        ),
    )
    assinatura_a3_assinada_em = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Timestamp do A3 (obrigatorio quando referencia presente).",
    )
    assinatura_a3_certificado_emissor_hash = models.CharField(
        max_length=128,
        blank=True,
        default="",
        help_text=(
            "HMAC do thumbprint do certificado emissor (AC do A3) com "
            "salt tenant. Obrigatorio quando referencia presente."
        ),
    )
    criado_em = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        app_label = "equipamentos"
        db_table = "equipamentos_versao"
        verbose_name = "Versao de equipamento"
        verbose_name_plural = "Versoes de equipamentos"
        ordering = ["-criado_em"]
        indexes = [
            models.Index(fields=["tenant", "equipamento", "-criado_em"]),
            models.Index(fields=["equipamento", "campo", "-criado_em"]),
            models.Index(fields=["tenant", "motivo_mudanca"]),
        ]
        constraints = [
            # P-EQP-T5: assinatura A3 e all-or-nothing.
            models.CheckConstraint(
                condition=(
                    models.Q(assinatura_a3_referencia__isnull=True)
                    | (
                        models.Q(assinatura_a3_referencia__isnull=False)
                        & models.Q(assinatura_a3_assinada_em__isnull=False)
                        & ~models.Q(assinatura_a3_certificado_emissor_hash="")
                    )
                ),
                name="ck_eqp_versao_a3_all_or_nothing",
            ),
        ]

    def __str__(self) -> str:
        return (
            f"Versao {self.id} eq={self.equipamento_id} "
            f"campo={self.campo} motivo={self.motivo_mudanca}"
        )

    def save(self, *args: Any, **kwargs: Any) -> None:
        """Insert-only (T-EQP-012). UPDATE bloqueado em codigo;
        T-EQP-013 cravara trigger PG quando modulo certificados existir."""
        if self.pk is not None and EquipamentoVersao.objects.filter(pk=self.pk).exists():
            raise RuntimeError(
                "EquipamentoVersao e INSERT-only (INV-025 imutabilidade "
                "pos-cert; trigger PG em T-EQP-013)."
            )
        # Forca clean (defesa: codigo que cria via .objects.create pula).
        self.full_clean(exclude=["assinatura_a3_assinada_em"])
        super().save(*args, **kwargs)

    def delete(self, *args: Any, **kwargs: Any) -> tuple[int, dict[str, int]]:
        raise RuntimeError(
            "EquipamentoVersao e INSERT-only. DELETE bloqueado em codigo."
        )

    def clean(self) -> None:
        """INV-EQP-VERSAO-001 — validador `motivo_detalhe` anti-PII +
        tamanho minimo quando motivo obriga aprovacao."""
        super().clean()
        from src.infrastructure.equipamentos.validators import (
            validar_motivo_detalhe,
        )

        try:
            validar_motivo_detalhe(
                self.motivo_detalhe,
                motivo_obriga_detalhe=self.motivo_mudanca
                in MOTIVOS_QUE_OBRIGAM_APROVACAO,
            )
        except ValueError as exc:
            from django.core.exceptions import ValidationError

            raise ValidationError({"motivo_detalhe": str(exc)}) from exc


class AprovacaoPendenteEquipamentoVersao(models.Model):
    """Aprovacao gestor_qualidade pra `EquipamentoVersao` com motivo
    que obriga aprovacao (US-EQP-002b / AC-EQP-002b-1).

    Maquina de estados (trigger PG `aprovacao_versao_anti_mutacao_terminal`
    em migration 0008): PENDENTE -> APROVADA / REJEITADA / EXPIRADA.
    Estados terminais sao imutaveis — UPDATE bloqueado.

    INV-EQP-002 (AC-EQP-002b-3 / ISO 17025 cl. 6.2 segregacao): CHECK
    `ck_aprovacao_solicitante_neq_decisor` proibe solicitante=decisor.
    Validacao tambem em service (defesa em profundidade).

    `parecer_gestor_texto` (AC-EQP-002b-4): >=30 chars + anti-PII via
    `validar_parecer_gestor_texto` (mesma regex INV-EQP-VERSAO-001).

    `sla_vencimento` calculado em T-EQP-019 via workalendar
    (D+3 sem cert / D+7 com cert).
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.PROTECT,
        related_name="aprovacoes_versao_equipamento",
    )
    equipamento = models.ForeignKey(
        Equipamento,
        on_delete=models.PROTECT,
        related_name="aprovacoes_versao",
    )
    solicitante = models.ForeignKey(
        Usuario,
        on_delete=models.PROTECT,
        related_name="aprovacoes_versao_solicitadas",
        help_text="Quem propos a mudanca (geralmente metrologista).",
    )
    campo = models.CharField(max_length=50)
    valor_anterior_hash = models.CharField(max_length=128)
    valor_novo_hash = models.CharField(max_length=128)
    motivo_mudanca = models.CharField(
        max_length=40,
        choices=MotivoMudancaEquipamentoVersao.choices,
        help_text="Deve estar em MOTIVOS_QUE_OBRIGAM_APROVACAO.",
    )
    motivo_detalhe = models.TextField(
        help_text=(
            ">=100 chars + anti-PII (INV-EQP-VERSAO-001). Reuso do "
            "mesmo validator do EquipamentoVersao."
        ),
    )
    solicitado_em = models.DateTimeField(auto_now_add=True, db_index=True)
    sla_vencimento = models.DateTimeField(
        help_text=(
            "T-EQP-019: D+3 dias uteis se equipamento SEM cert vigente; "
            "D+7 com cert vigente. Calculado por workalendar.america.Brazil."
        ),
    )
    status = models.CharField(
        max_length=20,
        choices=StatusAprovacaoVersao.choices,
        default=StatusAprovacaoVersao.PENDENTE,
        help_text="Trigger PG bloqueia UPDATE saindo de estados terminais.",
    )
    decisor = models.ForeignKey(
        Usuario,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="aprovacoes_versao_decididas",
        help_text="gestor_qualidade que aprovou/rejeitou. NULL ate decidir.",
    )
    parecer_gestor_texto = models.TextField(
        blank=True,
        default="",
        help_text=(
            ">=30 chars quando decidida (aprovada ou rejeitada). Anti-PII "
            "via validator (regex INV-EQP-VERSAO-001)."
        ),
    )
    decidida_em = models.DateTimeField(null=True, blank=True)
    evidencia_documental_id = models.UUIDField(
        null=True,
        blank=True,
        help_text="Opcional: anexo de dossie tecnico que sustenta a decisao.",
    )

    class Meta:
        app_label = "equipamentos"
        db_table = "equipamentos_aprovacao_versao"
        verbose_name = "Aprovacao de versao de equipamento"
        verbose_name_plural = "Aprovacoes de versao de equipamentos"
        ordering = ["-solicitado_em"]
        indexes = [
            models.Index(fields=["tenant", "status", "-solicitado_em"]),
            models.Index(fields=["tenant", "sla_vencimento"]),
            models.Index(fields=["equipamento", "-solicitado_em"]),
        ]
        constraints = [
            # INV-EQP-002 (ISO 17025 cl. 6.2 segregacao de funcoes).
            models.CheckConstraint(
                condition=~models.Q(solicitante=models.F("decisor")),
                name="ck_aprovacao_solicitante_neq_decisor",
            ),
            # AC-EQP-002b-1: decisor + parecer + decidida_em sao
            # all-or-nothing quando status terminal por decisao humana
            # (aprovada/rejeitada). EXPIRADA pode ter decisor=NULL
            # (vem do job). Reforco e na service layer.
        ]

    def __str__(self) -> str:
        return (
            f"Aprovacao {self.id} eq={self.equipamento_id} "
            f"campo={self.campo} status={self.status}"
        )

    def save(self, *args: Any, **kwargs: Any) -> None:
        """Defesa application: forca clean() (parecer anti-PII; INV-EQP-002)."""
        self.full_clean(exclude=["sla_vencimento"] if self.pk is None and not self.sla_vencimento else [])
        super().save(*args, **kwargs)

    def clean(self) -> None:
        super().clean()
        from django.core.exceptions import ValidationError

        from src.infrastructure.equipamentos.validators import (
            validar_motivo_detalhe,
            validar_parecer_gestor_texto,
        )

        # INV-EQP-002 (reforco application — CHECK no banco e camada B).
        if (
            self.solicitante_id is not None
            and self.decisor_id is not None
            and self.solicitante_id == self.decisor_id
        ):
            raise ValidationError(
                {
                    "decisor": (
                        "INV-EQP-002 (ISO 17025 cl. 6.2) — solicitante "
                        "nao pode ser o mesmo que o decisor (segregacao "
                        "de funcoes)."
                    )
                }
            )

        # AC-EQP-002b-1: motivo_detalhe reusa validador EquipamentoVersao
        # (sempre obriga >=100 chars + anti-PII, pois entrada na
        # AprovacaoPendente so existe pra motivos que obrigam aprovacao).
        try:
            validar_motivo_detalhe(self.motivo_detalhe, motivo_obriga_detalhe=True)
        except ValueError as exc:
            raise ValidationError({"motivo_detalhe": str(exc)}) from exc

        # AC-EQP-002b-4: parecer_gestor_texto obrigatorio quando
        # decidida (aprovada/rejeitada). EXPIRADA dispensa.
        if self.status in {
            StatusAprovacaoVersao.APROVADA,
            StatusAprovacaoVersao.REJEITADA,
        }:
            try:
                validar_parecer_gestor_texto(self.parecer_gestor_texto)
            except ValueError as exc:
                raise ValidationError({"parecer_gestor_texto": str(exc)}) from exc
            if self.decisor_id is None:
                raise ValidationError(
                    {"decisor": "Estado terminal exige decisor."}
                )
            if self.decidida_em is None:
                raise ValidationError(
                    {"decidida_em": "Estado terminal exige decidida_em."}
                )
