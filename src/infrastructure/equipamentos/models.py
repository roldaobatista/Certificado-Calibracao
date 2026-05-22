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


class MotivoCategoriaTransferencia(models.TextChoices):
    """5 motivos canonicos AC-EQP-004-1."""

    VENDA = "venda", "Venda"
    COMODATO = "comodato", "Comodato"
    DOACAO = "doacao", "Doacao"
    CORRECAO_CADASTRAL = "correcao_cadastral", "Correcao cadastral"
    OUTRO = "outro", "Outro (motivo_detalhe obrigatorio)"


class StatusTransferencia(models.TextChoices):
    """Estados da transferencia (AC-EQP-004-1).

    - PENDENTE: aguardando aceites validos.
    - EFETIVADA: ambos aceites validos + Equipamento.cliente_atual_id
      atualizado + evento publicado.
    - CANCELADA: rejeitada por cedente OU cessionario OU expirada.
    """

    PENDENTE = "pendente", "Pendente"
    EFETIVADA = "efetivada", "Efetivada"
    CANCELADA = "cancelada", "Cancelada"


class ViaAceiteTransferencia(models.TextChoices):
    """3 vias de aceite (AC-EQP-004-1)."""

    PRESENCIAL_ATENDENTE = (
        "presencial_atendente",
        "Presencial via atendente (fraca — exige cap de risco GATE-EQP-S5)",
    )
    CONTRATO_FISICO_DIGITALIZADO = (
        "contrato_fisico_digitalizado",
        "Contrato fisico digitalizado",
    )
    PORTAL_CLIENTE_OTP = (
        "portal_cliente_otp",
        "Portal do cliente (OTP — Wave B+ GATE-EQP-3)",
    )


class TransferenciaEquipamentoAceite(models.Model):
    """Transferencia de equipamento entre clientes do mesmo tenant
    (US-EQP-004 / T-EQP-034..041).

    Defesa em camadas:
    - INV-050 (AC-EQP-004-2): cessionario_cliente.tenant_id ==
      Equipamento.tenant_id. RLS na FK + assert no service.
    - INV-INT-010 (AC-EQP-004-3): cessionario e cedente nao podem estar
      bloqueados (predicate Marco 1 `cliente_nao_bloqueado`). Erro 412
      no endpoint.
    - AC-EQP-004-5 advogado: termo de transferencia tem 3 clausulas
      minimas (cravadas em texto canonico Wave A `transferencia-termo.md`;
      Marco 2 dogfooding aceita ID de versao do termo).
    - AC-EQP-004-6: cessionario sem `consentimento_historico_expresso=True`
      no aceite NAO ve historico (filtro no construir_ficha_360
      Wave A; aqui apenas grava o flag).

    aceite_cedente / aceite_cessionario JSONB com schema:
    `{tipo: <ViaAceiteTransferencia>, usuario_id_atendente: UUID,
       observacao: str, consentimento_historico_expresso: bool?}`.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.PROTECT,
        related_name="transferencias_equipamento",
    )
    equipamento = models.ForeignKey(
        Equipamento,
        on_delete=models.PROTECT,
        related_name="transferencias",
    )
    cedente_cliente = models.ForeignKey(
        Cliente,
        on_delete=models.PROTECT,
        related_name="transferencias_como_cedente",
        null=True,
        blank=True,
        db_constraint=False,
        help_text=(
            "Cliente cedente — snapshot do `Equipamento.cliente_atual_id` no "
            "momento da solicitacao. NULL quando equipamento orfao."
        ),
    )
    cessionario_cliente = models.ForeignKey(
        Cliente,
        on_delete=models.PROTECT,
        related_name="transferencias_como_cessionario",
        db_constraint=False,
        help_text=(
            "Cliente cessionario. INV-050 cravado: tenant_id deve ser igual "
            "ao Equipamento.tenant_id (validado em servico + RLS)."
        ),
    )
    motivo_categoria = models.CharField(
        max_length=30,
        choices=MotivoCategoriaTransferencia.choices,
    )
    motivo_detalhe = models.TextField(
        blank=True,
        default="",
        help_text="Obrigatorio quando motivo_categoria='outro'. Anti-PII Wave A.",
    )
    aceite_cedente = models.JSONField(
        default=dict,
        blank=True,
        help_text=(
            "Schema: {tipo: ViaAceiteTransferencia, usuario_id_atendente: "
            "UUID, observacao: str, consentimento_historico_expresso: bool, "
            "nivel_consentimento_historico: 'nada'|'resumo'|'completo'?}. "
            "{} antes do aceite ser registrado. T-EQP-039: nivel granular "
            "(P-EQP-R6) — quando ausente, deriva via "
            "`consentimento_historico_expresso` (True=completo / False=nada)."
        ),
    )
    aceite_cessionario = models.JSONField(
        default=dict,
        blank=True,
        help_text="Mesmo schema do aceite_cedente.",
    )
    status = models.CharField(
        max_length=20,
        choices=StatusTransferencia.choices,
        default=StatusTransferencia.PENDENTE,
    )
    solicitado_em = models.DateTimeField(auto_now_add=True, db_index=True)
    efetivada_em = models.DateTimeField(null=True, blank=True)
    cancelada_em = models.DateTimeField(null=True, blank=True)
    solicitado_por = models.ForeignKey(
        Usuario,
        on_delete=models.PROTECT,
        related_name="transferencias_solicitadas",
    )
    texto_termo_versao_id = models.CharField(
        max_length=20,
        default="v1.0-2026-05-22",
        help_text=(
            "Versao do termo de transferencia (3 clausulas advogado). "
            "Marco 2 default v1.0; Wave A trara `transferencia-termo.md` "
            "com bump explicito."
        ),
    )

    class Meta:
        app_label = "equipamentos"
        db_table = "equipamentos_transferencia"
        verbose_name = "Transferencia de equipamento"
        verbose_name_plural = "Transferencias de equipamentos"
        ordering = ["-solicitado_em"]
        indexes = [
            models.Index(fields=["tenant", "status", "-solicitado_em"]),
            models.Index(fields=["equipamento", "-solicitado_em"]),
        ]

    def __str__(self) -> str:
        return (
            f"Transf {self.id} eq={self.equipamento_id} "
            f"cessionario={self.cessionario_cliente_id} status={self.status}"
        )


class NivelConsentimentoHistorico(models.TextChoices):
    """3 niveis granulares de consentimento do cedente (P-EQP-R6 / AC-EQP-004-6).

    - `NADA`: cessionario ve APENAS dados gerados a partir da efetivacao
      da transferencia. Historico anterior (versoes, certificados,
      eventos) fica oculto via filtro em `construir_ficha_360` Wave A.
    - `RESUMO`: cessionario ve `ultima_calibracao` + `ultima_versao` do
      historico anterior (visao agregada sem detalhes operacionais).
    - `COMPLETO`: cessionario ve historico inteiro (versoes,
      certificados, eventos) — equivalente ao `consentimento_historico_
      expresso=True` da spec original.
    """

    NADA = "nada", "Nada — apenas dados pos-transferencia"
    RESUMO = "resumo", "Resumo — ultima calibracao + ultima versao"
    COMPLETO = "completo", "Completo — historico inteiro"


class ConsentimentoHistoricoEquipamento(models.Model):
    """Log dedicado de consentimento granular do cedente para visualizacao
    de historico do equipamento pos-transferencia (T-EQP-039 / AC-EQP-004-6).

    Cada transferencia EFETIVADA gera 1 registro neste log (mesmo quando
    `nivel=NADA` — pra prova de que o cedente DECIDIU expressamente nao
    compartilhar). Revogacao posterior (T-EQP-041 / AC-EQP-004-8) grava
    `revogado_em` no MESMO registro — sem criar novo (preserva linha do
    tempo unica por consentimento).

    Trigger PG `consentimento_historico_imutavel_pos_insert`:
    - Bloqueia UPDATE em todos os campos EXCETO `revogado_em`,
      `revogado_por_id`, `revogado_justificativa_hash`, `revogado_via`.
    - Se `OLD.revogado_em IS NOT NULL`: bloqueia mutacao mesmo nos
      campos de revogacao (revogacao e one-shot — re-conceder exige
      novo registro via nova transferencia futura ou endpoint dedicado
      Wave A `conceder-de-novo`).

    Justificativa de revogacao NUNCA persiste em claro — apenas hash
    HMAC com salt do tenant (mesmo helper Marco 1). Texto cru NUNCA
    vaza em payload de evento (mesma regra `motivo_detalhe` da
    transferencia).
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.PROTECT,
        related_name="consentimentos_historico_equipamento",
    )
    equipamento = models.ForeignKey(
        Equipamento,
        on_delete=models.PROTECT,
        related_name="consentimentos_historico",
    )
    transferencia_origem = models.ForeignKey(
        TransferenciaEquipamentoAceite,
        on_delete=models.PROTECT,
        related_name="consentimentos_historico",
        db_constraint=False,
        help_text=(
            "Transferencia que originou este consentimento (1:1 logico). "
            "db_constraint=False por consistencia com FKs cliente_atual "
            "(RLS no banco)."
        ),
    )
    cedente_cliente_id = models.UUIDField(
        null=True,
        blank=True,
        help_text=(
            "Snapshot do cedente no momento da concessao. NULL quando "
            "equipamento ja era orfao (cedente eliminado por LGPD antes da "
            "transferencia — caso raro)."
        ),
    )
    nivel = models.CharField(
        max_length=20,
        choices=NivelConsentimentoHistorico.choices,
        help_text="3 niveis: nada/resumo/completo (P-EQP-R6).",
    )
    concedido_por = models.ForeignKey(
        Usuario,
        on_delete=models.PROTECT,
        related_name="consentimentos_historico_concedidos",
        help_text=(
            "Atendente/admin que processou o aceite presencialmente (Marco 2 "
            "dogfooding). Portal-cliente OTP (Wave B+ GATE-EQP-3) gravara o "
            "proprio usuario do cedente."
        ),
    )
    concedido_em = models.DateTimeField(auto_now_add=True, db_index=True)
    via_concessao = models.CharField(
        max_length=40,
        choices=ViaAceiteTransferencia.choices,
        help_text=(
            "Mesma via do aceite_cedente da TransferenciaEquipamentoAceite "
            "(consistencia auditavel)."
        ),
    )
    revogado_em = models.DateTimeField(null=True, blank=True)
    revogado_por = models.ForeignKey(
        Usuario,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="consentimentos_historico_revogados",
    )
    revogado_justificativa_hash = models.CharField(
        max_length=128,
        blank=True,
        default="",
        help_text=(
            "HMAC-SHA256 da justificativa em claro com salt do tenant. "
            "Texto cru NUNCA persistido (mesma regra `motivo_detalhe` da "
            "transferencia)."
        ),
    )
    revogado_via = models.CharField(
        max_length=40,
        choices=ViaAceiteTransferencia.choices,
        blank=True,
        default="",
    )

    class Meta:
        app_label = "equipamentos"
        db_table = "equipamentos_consentimento_historico"
        verbose_name = "Consentimento historico de equipamento"
        verbose_name_plural = "Consentimentos historicos de equipamentos"
        ordering = ["-concedido_em"]
        indexes = [
            models.Index(fields=["tenant", "equipamento", "-concedido_em"]),
            models.Index(fields=["transferencia_origem"]),
        ]
        constraints = [
            # 1 consentimento ativo (nao revogado) por transferencia.
            # Revogar + reconceder exigira nova transferencia (Wave A).
            models.UniqueConstraint(
                fields=["transferencia_origem"],
                condition=models.Q(revogado_em__isnull=True),
                name="uq_consent_hist_ativo_por_transferencia",
            ),
        ]

    def __str__(self) -> str:
        return (
            f"Consent {self.id} eq={self.equipamento_id} "
            f"transf={self.transferencia_origem_id} nivel={self.nivel} "
            f"revogado={'sim' if self.revogado_em else 'nao'}"
        )


class EquipamentoSucatamento(models.Model):
    """Registro de sucatamento de equipamento (US-EQP-005 / AC-EQP-005-*).

    Tabela dedicada (1 registro por equipamento). Imutavel pos-insert
    via trigger PG — sucatamento e estado terminal (excecao unica
    `sucata→extraviado` ja tratada na maquina de status do migration
    0002).

    `tem_cert_vigente_no_momento` (P-EQP-S9 / AC-EQP-005-2): captura
    se o equipamento tinha certificado vigente no momento do
    sucatamento — determina se evento adicional
    `equipamento.sucateado_com_cert_vigente` e disparado + se
    `confirmacao_dupla=True` era obrigatorio.

    `texto_modal_versao_id` (P-EQP-S9): versao do texto canonico
    exibido no modal de confirmacao_dupla — auditavel via
    `template-notificacao-sucatamento.md` v1.0. Marco 2: aceita default
    `v1.0-2026-05-23`; Wave A: tabela `TextoModalSucatamentoVersao`.

    `ciencia_validade_tecnica_registrada` (P-EQP-R8 / AC-EQP-005-5):
    flag booleana obrigatoria quando `tem_cert_vigente_no_momento=True`.
    Confirma que o decisor leu o modal sobre validade tecnica ISO 17025
    §7.1.1 ANTES de sucatear.

    `justificativa_hash` (AC-EQP-005-1): HMAC-SHA256 com salt tenant
    da justificativa cru (>=30 chars + anti-PII). Texto cru NUNCA
    persistido (mesma regra `motivo_detalhe` da transferencia).
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.PROTECT,
        related_name="sucatamentos_equipamento",
    )
    equipamento = models.OneToOneField(
        Equipamento,
        on_delete=models.PROTECT,
        related_name="sucatamento",
        help_text="OneToOne — sucatamento e terminal e unico por equipamento.",
    )
    justificativa_hash = models.CharField(
        max_length=128,
        help_text=(
            "HMAC-SHA256 da justificativa em claro (>=30 chars + anti-PII) "
            "com salt do tenant. Texto cru NUNCA persistido."
        ),
    )
    tem_cert_vigente_no_momento = models.BooleanField(
        help_text=(
            "Captura snapshot do estado de certificado no momento do "
            "sucatamento (AC-EQP-005-2). Determina se evento extra "
            "`equipamento.sucateado_com_cert_vigente` foi disparado + se "
            "`confirmacao_dupla=True` era obrigatorio."
        ),
    )
    confirmacao_dupla = models.BooleanField(
        help_text=(
            "AC-EQP-005-2 — True OBRIGATORIO quando "
            "tem_cert_vigente_no_momento=True. Valida que UI exibiu o modal "
            "+ usuario confirmou ciencia."
        ),
    )
    texto_modal_versao_id = models.CharField(
        max_length=30,
        default="v1.0-2026-05-23",
        help_text=(
            "Versao do texto canonico do modal exibido (P-EQP-S9). "
            "`template-notificacao-sucatamento.md` v1.0; Marco 2 default "
            "`v1.0-2026-05-23`; Wave A: tabela "
            "`TextoModalSucatamentoVersao`."
        ),
    )
    ciencia_validade_tecnica_registrada = models.BooleanField(
        default=False,
        help_text=(
            "P-EQP-R8 / AC-EQP-005-5 — True OBRIGATORIO quando "
            "tem_cert_vigente_no_momento=True. Confirma ciencia da "
            "validade tecnica do certificado emitido (ISO 17025 §7.1.1)."
        ),
    )
    sucateado_por = models.ForeignKey(
        Usuario,
        on_delete=models.PROTECT,
        related_name="sucatamentos_solicitados",
    )
    sucateado_em = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        app_label = "equipamentos"
        db_table = "equipamentos_sucatamento"
        verbose_name = "Sucatamento de equipamento"
        verbose_name_plural = "Sucatamentos de equipamentos"
        ordering = ["-sucateado_em"]
        indexes = [
            models.Index(fields=["tenant", "-sucateado_em"]),
        ]
        constraints = [
            # AC-EQP-005-2 + P-EQP-R8: cert vigente exige confirmacao_dupla
            # E ciencia_validade_tecnica_registrada.
            models.CheckConstraint(
                condition=(
                    models.Q(tem_cert_vigente_no_momento=False)
                    | (
                        models.Q(tem_cert_vigente_no_momento=True)
                        & models.Q(confirmacao_dupla=True)
                        & models.Q(ciencia_validade_tecnica_registrada=True)
                    )
                ),
                name="ck_sucatamento_cert_vigente_exige_dupla_confirmacao",
            ),
        ]

    def __str__(self) -> str:
        return (
            f"Sucatamento {self.id} eq={self.equipamento_id} "
            f"cert_vigente={'sim' if self.tem_cert_vigente_no_momento else 'nao'}"
        )


class CondicaoVisualChegada(models.TextChoices):
    """6 condicoes visuais no recebimento (AC-EQP-006-1)."""

    INTEGRO = "integro", "Integro"
    AMASSADO = "amassado", "Amassado"
    LACRE_VIOLADO = "lacre_violado", "Lacre violado"
    CONTAMINADO = "contaminado", "Contaminado"
    SEM_ACESSORIOS = "sem_acessorios", "Sem acessorios"
    OUTROS = "outros", "Outros"


class DecisaoAposAnomalia(models.TextChoices):
    """4 decisoes operacionais quando condicao != integro (AC-EQP-006-2)."""

    PROSSEGUIR = "prosseguir", "Prosseguir mesmo assim"
    CONTATAR_CLIENTE_AGUARDANDO = (
        "contatar_cliente_aguardando",
        "Contatar cliente e aguardar resposta",
    )
    RECUSAR_RECEBIMENTO = "recusar_recebimento", "Recusar recebimento"
    ACEITAR_COM_RESSALVA = "aceitar_com_ressalva", "Aceitar com ressalva"


class StatusFluxoLab(models.TextChoices):
    """9 fases + 2 alternativos terminais (AC-EQP-006-3b / P-EQP-R3).

    Fluxo principal (linear):
    aguardando_recebimento -> recebido_pendente_inspecao ->
    em_inspecao_visual -> aguardando_calibracao ->
    aguardando_padrao_disponivel (P-EQP-R3 — RBC cl. 6.3) ->
    em_calibracao -> aguardando_aprovacao_tecnica ->
    aguardando_devolucao -> devolvido.

    Alternativos terminais (caem do fluxo + linkam com RegistroCAPA):
    - nao_conformidade_recebimento
    - nao_conformidade_calibracao
    """

    AGUARDANDO_RECEBIMENTO = "aguardando_recebimento", "Aguardando recebimento"
    RECEBIDO_PENDENTE_INSPECAO = (
        "recebido_pendente_inspecao",
        "Recebido pendente de inspecao",
    )
    EM_INSPECAO_VISUAL = "em_inspecao_visual", "Em inspecao visual"
    AGUARDANDO_CALIBRACAO = "aguardando_calibracao", "Aguardando calibracao"
    AGUARDANDO_PADRAO_DISPONIVEL = (
        "aguardando_padrao_disponivel",
        "Aguardando padrao disponivel (RBC cl. 6.3)",
    )
    EM_CALIBRACAO = "em_calibracao", "Em calibracao"
    AGUARDANDO_APROVACAO_TECNICA = (
        "aguardando_aprovacao_tecnica",
        "Aguardando aprovacao tecnica",
    )
    AGUARDANDO_DEVOLUCAO = "aguardando_devolucao", "Aguardando devolucao"
    DEVOLVIDO = "devolvido", "Devolvido"
    NAO_CONFORMIDADE_RECEBIMENTO = (
        "nao_conformidade_recebimento",
        "Nao conformidade no recebimento (CAPA)",
    )
    NAO_CONFORMIDADE_CALIBRACAO = (
        "nao_conformidade_calibracao",
        "Nao conformidade na calibracao (CAPA)",
    )


# T-EQP-050: estados terminais do fluxo do laboratorio. UPDATE saindo
# destes esta bloqueado pelo trigger PG.
STATUS_FLUXO_LAB_TERMINAIS: frozenset[str] = frozenset(
    {
        StatusFluxoLab.DEVOLVIDO.value,
        StatusFluxoLab.NAO_CONFORMIDADE_RECEBIMENTO.value,
        StatusFluxoLab.NAO_CONFORMIDADE_CALIBRACAO.value,
    }
)


class EquipamentoRecebimento(models.Model):
    """Recebimento fisico do equipamento no laboratorio (US-EQP-006 /
    AC-EQP-006-1+2 / ISO 17025 cl. 7.4).

    Cobre o nucleo do recebimento. Provisorio (RecebimentoProvisorio
    tabela separada) + devolucao (POST `/devolucoes/`) ficam em
    entregas futuras de Marco 2 / Wave A.

    `foto_storage_key` (Marco 2): UUID opaco gerado pelo
    `FotoStorageService.salvar`. Wave A migra para B2 (GATE-EQP-2);
    Marco 2 dogfooding salva binario inline em
    `EquipamentoRecebimentoFoto`.

    `foto_sha256` (P-EQP-S3 — AC-EQP-006-10): SHA-256 do binario
    FINAL pos-EXIF-strip. Imutavel via trigger PG pos-INSERT (corretora
    RAT-EQP-FOTO).

    `status_fluxo_lab` (AC-EQP-006-3b): maquina de 9 fases + 2
    alternativos terminais. Trigger PG `transicao_status_fluxo_lab` em
    migration 0019 valida.

    Defesa em camadas anti-PII:
    - `anomalias_observadas`: clean valida via `INV-EQP-ANOM-001`.
    - `justificativa_decisao`: clean valida via `INV-EQP-ANOM-002`.

    `decisao_apos_anomalia`: obrigatoria quando
    `condicao_visual_chegada != 'integro'`. Service + Django
    CheckConstraint ck_recebimento_anomalia_exige_decisao reforcam.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.PROTECT,
        related_name="recebimentos_equipamento",
    )
    equipamento = models.ForeignKey(
        Equipamento,
        on_delete=models.PROTECT,
        related_name="recebimentos",
    )
    condicao_visual_chegada = models.CharField(
        max_length=30,
        choices=CondicaoVisualChegada.choices,
    )
    anomalias_observadas = models.TextField(
        blank=True,
        default="",
        help_text=(
            "Anti-PII (INV-EQP-ANOM-001) — texto <=500 chars descrevendo "
            "o estado fisico. Proibido CPF/CNPJ/email/telefone/nomes."
        ),
    )
    decisao_apos_anomalia = models.CharField(
        max_length=40,
        choices=DecisaoAposAnomalia.choices,
        blank=True,
        default="",
        help_text=(
            "Obrigatoria quando condicao_visual_chegada != 'integro' "
            "(AC-EQP-006-2). Defesa A: service raise; B: CHECK Django."
        ),
    )
    justificativa_decisao = models.TextField(
        blank=True,
        default="",
        help_text=(
            ">=30 chars + anti-PII (INV-EQP-ANOM-002) quando decisao "
            "preenchida. Texto cru gravado (nao hash — auditoria ISO "
            "17025 cl. 7.4 exige rastreabilidade legivel)."
        ),
    )
    foto_storage_key = models.CharField(
        max_length=64,
        blank=True,
        default="",
        help_text=(
            "UUID opaco gerado pelo FotoStorageService.salvar. Vazio quando "
            "perfil B/C/D recebe sem foto (perfil A: obrigatoria — service "
            "valida)."
        ),
    )
    foto_sha256 = models.CharField(
        max_length=64,
        blank=True,
        default="",
        help_text=(
            "SHA-256 hex do binario FINAL pos-EXIF-strip (P-EQP-S3 / "
            "corretora RAT-EQP-FOTO). Imutavel via trigger PG pos-INSERT. "
            "Vazio quando foto_storage_key vazio."
        ),
    )
    status_fluxo_lab = models.CharField(
        max_length=40,
        choices=StatusFluxoLab.choices,
        default=StatusFluxoLab.RECEBIDO_PENDENTE_INSPECAO,
        help_text=(
            "9 fases + 2 alternativos (AC-EQP-006-3b). Trigger PG "
            "`transicao_status_fluxo_lab` valida + estados terminais "
            "bloqueiam UPDATE."
        ),
    )
    recebido_por = models.ForeignKey(
        Usuario,
        on_delete=models.PROTECT,
        related_name="recebimentos_registrados",
    )
    data_recebimento = models.DateTimeField(auto_now_add=True, db_index=True)
    # T-EQP-055 (P-EQP-R3 / AC-EQP-006-7b) — condicoes ambientais na
    # recepcao. NULL permitido com justificativa quando grandeza nao
    # exige medicao (RBC cl. 6.3 + ISO 17025 cl. 6.4.10). Imutaveis
    # pos-INSERT via trigger PG `recebimento_ambiente_imutavel_check`
    # (migration 0026 — ISO 17025 cl. 7.4 + RBC NIT-DICLA-021 WORM 25a).
    temp_ambiente_c = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=(
            "Temperatura ambiente em °C no momento da recepcao "
            "(P-EQP-R3). NULL permitido com justificativa."
        ),
    )
    ur_percentual = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=(
            "Umidade relativa em % no momento da recepcao (P-EQP-R3). "
            "NULL permitido com justificativa."
        ),
    )
    pressao_kpa = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=(
            "Pressao atmosferica em kPa no momento da recepcao "
            "(P-EQP-R3). NULL permitido com justificativa."
        ),
    )
    justificativa_condicoes_ambientais_ausentes = models.TextField(
        blank=True,
        default="",
        help_text=(
            "Obrigatoria quando temp/ur/pressao sao todos NULL (P-EQP-R3). "
            ">=20 chars + anti-PII. Texto cru (auditoria ISO 17025)."
        ),
    )

    class Meta:
        app_label = "equipamentos"
        db_table = "equipamentos_recebimento"
        verbose_name = "Recebimento de equipamento"
        verbose_name_plural = "Recebimentos de equipamentos"
        ordering = ["-data_recebimento"]
        indexes = [
            models.Index(fields=["tenant", "equipamento", "-data_recebimento"]),
            models.Index(fields=["tenant", "status_fluxo_lab"]),
        ]
        constraints = [
            # AC-EQP-006-2: anomalia exige decisao + justificativa.
            models.CheckConstraint(
                condition=(
                    models.Q(condicao_visual_chegada="integro")
                    | (
                        ~models.Q(condicao_visual_chegada="integro")
                        & ~models.Q(decisao_apos_anomalia="")
                        & ~models.Q(justificativa_decisao="")
                    )
                ),
                name="ck_recebimento_anomalia_exige_decisao",
            ),
            # P-EQP-S3: foto_sha256 e foto_storage_key all-or-nothing.
            models.CheckConstraint(
                condition=(
                    (models.Q(foto_storage_key="") & models.Q(foto_sha256=""))
                    | (
                        ~models.Q(foto_storage_key="")
                        & ~models.Q(foto_sha256="")
                    )
                ),
                name="ck_recebimento_foto_storage_e_sha_all_or_nothing",
            ),
        ]

    def __str__(self) -> str:
        return (
            f"Recebimento {self.id} eq={self.equipamento_id} "
            f"cond={self.condicao_visual_chegada} status={self.status_fluxo_lab}"
        )


class EquipamentoRecebimentoFoto(models.Model):
    """Foto do recebimento — armazenamento INLINE em Marco 2 dogfooding
    (BYTEA) ate Wave A migrar pra B2 (GATE-EQP-2).

    Tabela SEPARADA do recebimento por 2 motivos:
    1. Permite `EquipamentoRecebimento` ser consultado sem carregar
       binario (queries de fluxo lab + auditoria nao precisam dele).
    2. Migracao pra B2 vira `EquipamentoRecebimentoFoto` apenas
       referencia (`bucket`, `object_key`, `versao_b2`) — modelo
       sobrevive a troca de storage backend.

    Limite 5MB enforced no service (`FotoStorageService.salvar`); aqui
    apenas a estrutura.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.PROTECT,
        related_name="recebimento_fotos",
    )
    recebimento = models.OneToOneField(
        EquipamentoRecebimento,
        on_delete=models.PROTECT,
        related_name="foto",
    )
    storage_key = models.CharField(
        max_length=64,
        unique=True,
        help_text="UUID opaco — bate com `EquipamentoRecebimento.foto_storage_key`.",
    )
    conteudo_bytes = models.BinaryField(
        help_text=(
            "Binario JPEG/PNG pos-EXIF-strip. Marco 2: ≤5MB inline; "
            "Wave A migra pra B2 (GATE-EQP-2) — campo permanece como "
            "fallback ou e dropado depois da migracao."
        ),
    )
    mime_type = models.CharField(
        max_length=30,
        help_text="image/jpeg ou image/png (validado no service).",
    )
    tamanho_bytes = models.PositiveIntegerField()
    criado_em = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        app_label = "equipamentos"
        db_table = "equipamentos_recebimento_foto"
        verbose_name = "Foto de recebimento"
        verbose_name_plural = "Fotos de recebimentos"
        ordering = ["-criado_em"]

    def __str__(self) -> str:
        return (
            f"Foto {self.id} rec={self.recebimento_id} "
            f"mime={self.mime_type} bytes={self.tamanho_bytes}"
        )


class EquipamentoDevolucao(models.Model):
    """Devolucao do equipamento ao cliente (US-EQP-006 AC-EQP-006-4 /
    ISO 17025 cl. 7.4.5).

    1:1 com EquipamentoRecebimento (o recebimento e o ciclo completo;
    devolucao encerra o ciclo). Em re-recebimento futuro, novo
    EquipamentoRecebimento eh criado.

    `condicao_visual_devolucao`: mesmo enum do recebimento
    (`integro`/`amassado`/etc.) — registra o estado fisico no momento
    da devolucao para protecao bilateral (RAT-EQP-FOTO).

    `foto_storage_key` + `foto_sha256`: obrigatorios em perfil A
    (ISO 17025 cl. 7.4.5 — evidencia da devolucao); opcional em B/C/D
    (Marco 2 dogfooding: obrigatorios sempre — Wave A diferencia por
    perfil). Imutaveis via trigger PG pos-INSERT.

    `termo_devolucao_versao_id`: versao do termo canonico
    (`v1.0-2026-05-23`); Wave A: tabela
    `TermoDevolucaoVersao`.

    `termo_aceite_hash`: HMAC-SHA256 com salt do tenant do payload
    `f"{texto_termo}|{usuario_id}|{ip_hash}|{aceite_em_iso}"`. Defesa
    contra adulteracao (cliente nega ter aceitado — laboratorio
    apresenta hash + texto canonico + log de IP).

    Imutavel pos-INSERT — devolucao e terminal, registro nunca muda.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.PROTECT,
        related_name="devolucoes_equipamento",
    )
    recebimento = models.OneToOneField(
        EquipamentoRecebimento,
        on_delete=models.PROTECT,
        related_name="devolucao",
        help_text=(
            "OneToOne — uma devolucao encerra um recebimento. "
            "Re-recebimento futuro cria novo EquipamentoRecebimento."
        ),
    )
    condicao_visual_devolucao = models.CharField(
        max_length=30,
        choices=CondicaoVisualChegada.choices,
        help_text=(
            "Reusa enum CondicaoVisualChegada (mesmo escopo) — registra "
            "estado fisico na devolucao (RAT-EQP-FOTO protecao bilateral)."
        ),
    )
    foto_storage_key = models.CharField(
        max_length=64,
        help_text=(
            "Marco 2 dogfooding: obrigatoria sempre. Wave A: opcional em "
            "perfil B/C/D. Imutavel via trigger PG."
        ),
    )
    foto_sha256 = models.CharField(
        max_length=64,
        help_text="SHA-256 hex do binario pos-EXIF-strip. Imutavel pos-INSERT.",
    )
    termo_devolucao_versao_id = models.CharField(
        max_length=30,
        default="v1.0-2026-05-23",
        help_text=(
            "Versao do texto canonico do termo (CPC art. 411 III). "
            "`termo-devolucao.md` v1.0; Marco 2 default; Wave A: tabela "
            "`TermoDevolucaoVersao` com bumps."
        ),
    )
    termo_aceite_hash = models.CharField(
        max_length=128,
        help_text=(
            "HMAC-SHA256 com salt tenant de "
            "`{texto_termo}|{usuario_id}|{ip_hash}|{aceite_em_iso}`. "
            "Defesa anti-adulteracao + prova de aceite."
        ),
    )
    devolvido_por = models.ForeignKey(
        Usuario,
        on_delete=models.PROTECT,
        related_name="devolucoes_registradas",
        help_text=(
            "Atendente/almoxarife que processou a devolucao. Em portal-"
            "cliente OTP Wave B+ pode ser o proprio cliente."
        ),
    )
    devolvido_em = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        app_label = "equipamentos"
        db_table = "equipamentos_devolucao"
        verbose_name = "Devolucao de equipamento"
        verbose_name_plural = "Devolucoes de equipamentos"
        ordering = ["-devolvido_em"]
        indexes = [
            models.Index(fields=["tenant", "-devolvido_em"]),
        ]

    def __str__(self) -> str:
        return (
            f"Devolucao {self.id} rec={self.recebimento_id} "
            f"cond={self.condicao_visual_devolucao}"
        )


class EquipamentoDevolucaoFoto(models.Model):
    """Foto da devolucao — paralela a `EquipamentoRecebimentoFoto`.

    Justificativa do desdobramento (vs reuso): `EquipamentoRecebimentoFoto`
    e OneToOne com recebimento. A devolucao precisa de foto INDEPENDENTE
    (estado fisico na SAIDA — RAT-EQP-FOTO bilateral). Marco 2 dogfooding:
    BLOB inline (≤5MB); Wave A: B2 (GATE-EQP-2).
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.PROTECT,
        related_name="devolucao_fotos",
    )
    devolucao = models.OneToOneField(
        EquipamentoDevolucao,
        on_delete=models.PROTECT,
        related_name="foto",
    )
    storage_key = models.CharField(
        max_length=64,
        unique=True,
        help_text="UUID opaco — bate com `EquipamentoDevolucao.foto_storage_key`.",
    )
    conteudo_bytes = models.BinaryField()
    mime_type = models.CharField(max_length=30)
    tamanho_bytes = models.PositiveIntegerField()
    criado_em = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        app_label = "equipamentos"
        db_table = "equipamentos_devolucao_foto"
        verbose_name = "Foto de devolucao"
        verbose_name_plural = "Fotos de devolucoes"
        ordering = ["-criado_em"]

    def __str__(self) -> str:
        return (
            f"Foto devolucao {self.id} dev={self.devolucao_id} "
            f"mime={self.mime_type} bytes={self.tamanho_bytes}"
        )


class StatusRecebimentoProvisorio(models.TextChoices):
    """3 estados do recebimento provisorio (P-EQP-R9 / INV-EQP-PROV-001).

    - `pendente_promocao`: aguardando cadastro completo + foto + RT
      decidir promocao.
    - `promovido`: virou `Equipamento` definitivo (1x apenas — campo
      `equipamento_promovido_id` aponta).
    - `expirado_descartado`: TTL D+7 vencido sem promocao; job
      `processar_provisorios_expirados` marca + publica
      `sistema.provisorio_expirado` (alerta P2).
    """

    PENDENTE_PROMOCAO = "pendente_promocao", "Pendente de promocao"
    PROMOVIDO = "promovido", "Promovido a equipamento definitivo"
    EXPIRADO_DESCARTADO = "expirado_descartado", "Expirado descartado"


class RecebimentoProvisorio(models.Model):
    """Recebimento de equipamento SEM cadastro completo (Caminho A
    Roldao — INV-EQP-PROV-001 / AC-EQP-006-6 / P-EQP-R9).

    Tabela SEPARADA de `EquipamentoRecebimento`. NAO tem FK em
    `Equipamento` ate ser promovida — exatamente o caso de uso: o
    equipamento chegou no laboratorio sem ter sido cadastrado antes
    (cliente trouxe sem agendamento, sem TAG canonica, sem dados
    completos do fabricante). Operador registra provisoriamente com
    o minimo necessario (TAG provisoria + descricao + foto +
    condicao visual) e ate D+7 o tenant promove para
    `Equipamento` definitivo (criando 1º EquipamentoRecebimento
    canonico no MESMO ato).

    **Defesa contra emitir cert sobre provisorio (Wave A — modulo
    certificados):** trigger PG em `equipamentos_certificado` BLOQUEIA
    INSERT/UPDATE referenciando `RecebimentoProvisorio.id` em qualquer
    campo. Marco 2: `certificados` stub nao tem essa FK; defesa fica
    no design (caller manual nao pode criar cert sobre provisorio
    porque `Certificado.equipamento_id` ja e FK em Equipamento, e
    provisorio NAO E Equipamento).

    `equipamento_promovido_id` (NULL ate promover): UUID do
    `Equipamento` definitivo criado na promocao. Imutavel pos-promocao.

    `ttl_expira_em` (auto D+7 a partir de `data_recebimento`):
    contagem dia-corrido. Job marca como `expirado_descartado` ao
    cruzar.

    Imutabilidade pos-INSERT: trigger PG bloqueia mutacao em CORE
    (tag_provisoria, descricao, foto, recebido_por, data_recebimento,
    ttl_expira_em); apenas 3 campos podem mutar 1 vez:
    `status` (pendente → promovido OU expirado), `equipamento_promovido_id`
    (NULL → UUID na promocao), `promovido_em`.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.PROTECT,
        related_name="recebimentos_provisorios",
    )
    tag_provisoria = models.CharField(
        max_length=50,
        help_text=(
            "TAG temporaria operacional (ex: 'PROV-2026-05-23-001'). "
            "NAO precisa ser unica entre tenants nem entre provisorios — "
            "a promocao gera TAG canonica em Equipamento.tag (INV-049)."
        ),
    )
    descricao_estimada = models.CharField(
        max_length=200,
        help_text=(
            "Descricao livre informada pelo operador no recebimento "
            "provisorio (ex: 'Balanca digital marca incerta cap 30kg'). "
            "Anti-PII (mesmo padrao localizacao_fisica)."
        ),
    )
    condicao_visual_chegada = models.CharField(
        max_length=30,
        choices=CondicaoVisualChegada.choices,
    )
    foto_storage_key = models.CharField(
        max_length=64,
        help_text="Obrigatoria sempre — defesa contra cliente reclamar dano pos-entrega.",
    )
    foto_sha256 = models.CharField(
        max_length=64,
        help_text="SHA-256 hex do binario pos-EXIF-strip. Imutavel pos-INSERT.",
    )
    recebido_por = models.ForeignKey(
        Usuario,
        on_delete=models.PROTECT,
        related_name="provisorios_registrados",
    )
    data_recebimento = models.DateTimeField(auto_now_add=True, db_index=True)
    ttl_expira_em = models.DateTimeField(
        help_text=(
            "D+7 dias corridos a partir de data_recebimento. Job "
            "`processar_provisorios_expirados` marca status="
            "expirado_descartado ao cruzar."
        ),
    )
    status = models.CharField(
        max_length=30,
        choices=StatusRecebimentoProvisorio.choices,
        default=StatusRecebimentoProvisorio.PENDENTE_PROMOCAO,
    )
    equipamento_promovido_id = models.UUIDField(
        null=True,
        blank=True,
        help_text=(
            "Aponta para Equipamento.id quando promovido. NULL ate "
            "promocao; UUID imutavel pos-promocao."
        ),
    )
    promovido_em = models.DateTimeField(null=True, blank=True)

    class Meta:
        app_label = "equipamentos"
        db_table = "equipamentos_recebimento_provisorio"
        verbose_name = "Recebimento provisorio"
        verbose_name_plural = "Recebimentos provisorios"
        ordering = ["-data_recebimento"]
        indexes = [
            models.Index(fields=["tenant", "status", "-data_recebimento"]),
            models.Index(fields=["tenant", "ttl_expira_em"]),
        ]
        constraints = [
            # equipamento_promovido_id e promovido_em sao all-or-nothing
            # com status=promovido.
            models.CheckConstraint(
                condition=(
                    (
                        models.Q(status="promovido")
                        & models.Q(equipamento_promovido_id__isnull=False)
                        & models.Q(promovido_em__isnull=False)
                    )
                    | (
                        ~models.Q(status="promovido")
                        & models.Q(equipamento_promovido_id__isnull=True)
                        & models.Q(promovido_em__isnull=True)
                    )
                ),
                name="ck_provisorio_promovido_all_or_nothing",
            ),
        ]

    def __str__(self) -> str:
        return (
            f"Provisorio {self.id} tag={self.tag_provisoria} "
            f"status={self.status}"
        )


class RecebimentoProvisorioFoto(models.Model):
    """Foto do recebimento provisorio (paralela a
    EquipamentoRecebimentoFoto / EquipamentoDevolucaoFoto).

    1:1 com RecebimentoProvisorio. BLOB inline Marco 2; Wave A: B2.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.PROTECT,
        related_name="provisorio_fotos",
    )
    provisorio = models.OneToOneField(
        RecebimentoProvisorio,
        on_delete=models.PROTECT,
        related_name="foto",
    )
    storage_key = models.CharField(
        max_length=64,
        unique=True,
    )
    conteudo_bytes = models.BinaryField()
    mime_type = models.CharField(max_length=30)
    tamanho_bytes = models.PositiveIntegerField()
    criado_em = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        app_label = "equipamentos"
        db_table = "equipamentos_recebimento_provisorio_foto"
        verbose_name = "Foto de recebimento provisorio"
        verbose_name_plural = "Fotos de recebimentos provisorios"
        ordering = ["-criado_em"]

    def __str__(self) -> str:
        return (
            f"Foto provisorio {self.id} prov={self.provisorio_id} "
            f"bytes={self.tamanho_bytes}"
        )
