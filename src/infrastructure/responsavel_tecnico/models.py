"""Modelos `ResponsavelTecnicoTenant` + `RTCompetencia` (US-EQP-007).

ResponsavelTecnicoTenant (AC-EQP-007-1):
    Identidade + vigencia do RT. Tabela INSERT-only — campos imutaveis
    pos-INSERT exceto `encerrado_em`, `encerrado_por`, `motivo_encerramento`
    (transicao unica: ativo -> encerrado). Trigger PG `rt_imutavel_pos_insert`
    bloqueia UPDATE em demais campos.

RTCompetencia (AC-EQP-007-3):
    Declaracao de competencia por grandeza acreditada. EXCLUDE GIST
    em `(tenant_id, grandeza, daterange(declarado_em, vigente_ate, '[)') WITH &&)`
    garante INV-EQP-RT-001 — apenas 1 competencia vigente por (tenant,
    grandeza) em qualquer janela temporal (P-EQP-R10).

Anti-PII:
    `cpf_hash` armazena HMAC-SHA256 com sal por tenant (mesmo padrao
    SANEA-02). `nome_completo_snapshot` aceita texto cru por enquanto
    porque RT e PUBLICO (consta no escopo de acreditacao na CGCRE).
"""

from __future__ import annotations

import uuid

from django.db import models

from src.infrastructure.tenant.models import Tenant
from src.infrastructure.usuario.models import Usuario


class RegistroProfissionalTipo(models.TextChoices):
    """Conselhos profissionais aceitos para RT (Wave A pode expandir).

    Lista conservadora: cobre o caso comum em laboratorio metrologico
    (engenheiro/quimico). `OUTRO` permite cadastrar com texto livre em
    `registro_profissional_descricao_outro` quando necessario.
    """

    CREA = "CREA", "CREA — Engenharia"
    CRQ = "CRQ", "CRQ — Quimica"
    CRF = "CRF", "CRF — Farmacia"
    OUTRO = "OUTRO", "Outro conselho profissional"


class MotivoEncerramentoRT(models.TextChoices):
    """Por que o RT deixa de ser ativo."""

    DESLIGAMENTO = "desligamento", "Desligamento do profissional"
    SUBSTITUICAO = "substituicao", "Substituicao por novo RT"
    APOSENTADORIA = "aposentadoria", "Aposentadoria"
    CESSACAO_OPERACOES = "cessacao_operacoes", "Cessacao de operacoes do tenant"
    OUTRO = "outro", "Outro (vide motivo_detalhe)"


class ResponsavelTecnicoTenant(models.Model):
    """RT do tenant — INSERT-only com encerramento controlado (P-EQP-R10).

    Trigger PG `rt_imutavel_pos_insert` bloqueia UPDATE em todos os
    campos EXCETO `encerrado_em`, `encerrado_por`, `motivo_encerramento`,
    `motivo_detalhe`. Transicao permitida apenas UMA vez (encerrado_em
    IS NULL -> NOT NULL); apos isso a linha vira totalmente imutavel.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.PROTECT,
        related_name="responsaveis_tecnicos",
        help_text="Denormalizado pra RLS (mesmo padrao Marco 1).",
    )
    usuario = models.ForeignKey(
        Usuario,
        on_delete=models.PROTECT,
        related_name="vinculos_rt",
        help_text=(
            "Usuario do tenant que e o RT. Vinculacao logica — o usuario "
            "pode logar como qualquer perfil; RT e papel separado."
        ),
    )
    nome_completo_snapshot = models.CharField(
        max_length=200,
        help_text=(
            "Nome do RT no momento do cadastro (CGCRE — escopo de "
            "acreditacao tem o nome PUBLICO). Snapshot imutavel."
        ),
    )
    cpf_hash = models.CharField(
        max_length=80,
        help_text=(
            "HMAC-SHA256(cpf, salt_tenant) prefixado por key_id (formato "
            "`vN:64hex`). CPF cru NUNCA persiste; comparacao via hash."
        ),
    )
    formacao_academica = models.CharField(
        max_length=200,
        help_text="Ex: 'Engenharia Mecanica - UFMG - 2010'.",
    )
    registro_profissional_tipo = models.CharField(
        max_length=10,
        choices=RegistroProfissionalTipo.choices,
    )
    registro_profissional_numero = models.CharField(
        max_length=40,
        help_text="Numero do registro (ex: 'CREA-MG 123.456/D').",
    )
    registro_profissional_descricao_outro = models.CharField(
        max_length=80,
        blank=True,
        default="",
        help_text=(
            "Quando tipo=OUTRO, descrever o conselho (ex: 'CFB - Biologia'). "
            "Vazio quando tipo != OUTRO."
        ),
    )
    data_inicio_vigencia = models.DateField(
        help_text="Data efetiva em que o RT assumiu."
    )
    data_fim_vigencia = models.DateField(
        null=True,
        blank=True,
        help_text=(
            "Data planejada de fim (NULL = vigencia indeterminada). NAO e "
            "o mesmo que `encerrado_em` (encerramento real do vinculo)."
        ),
    )
    criado_em = models.DateTimeField(auto_now_add=True, db_index=True)
    criado_por = models.ForeignKey(
        Usuario,
        on_delete=models.PROTECT,
        related_name="rt_cadastrou",
        help_text="Quem cadastrou o RT (autoria).",
    )
    encerrado_em = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Timestamp de encerramento (UNICA mutacao permitida).",
    )
    encerrado_por = models.ForeignKey(
        Usuario,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="rt_encerrou",
        help_text="Quem efetuou o encerramento.",
    )
    motivo_encerramento = models.CharField(
        max_length=30,
        choices=MotivoEncerramentoRT.choices,
        blank=True,
        default="",
        help_text="Vazio enquanto vigente; obrigatorio ao encerrar.",
    )
    motivo_detalhe = models.CharField(
        max_length=500,
        blank=True,
        default="",
        help_text="Texto livre quando motivo=OUTRO. Anti-PII (regex valida).",
    )

    class Meta:
        app_label = "responsavel_tecnico"
        db_table = "responsavel_tecnico_tenant"
        verbose_name = "Responsavel Tecnico do tenant"
        verbose_name_plural = "Responsaveis Tecnicos do tenant"
        ordering = ["-criado_em"]
        indexes = [
            models.Index(fields=["tenant", "encerrado_em"]),
            models.Index(fields=["usuario"]),
        ]

    def __str__(self) -> str:
        status = "encerrado" if self.encerrado_em else "ativo"
        return f"RT {self.nome_completo_snapshot} ({status})"

    @property
    def vigente(self) -> bool:
        """True quando ainda nao encerrado."""
        return self.encerrado_em is None


class RTCompetencia(models.Model):
    """Competencia declarada do RT por grandeza (P-EQP-R10 / RBC cl. 6.2).

    EXCLUDE GIST `(tenant_id, grandeza, daterange(declarado_em,
    vigente_ate, '[)') WITH &&)` materializa INV-EQP-RT-001: por tenant
    + grandeza, ao MAXIMO 1 competencia vigente em qualquer janela
    temporal.

    `carta_competencia_anexo_id` referencia o ID de um anexo em modulo
    de anexos (Wave A); por enquanto UUID opaco — service valida
    presenca quando obrigatorio (politica RBC pra alguns escopos).
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.PROTECT,
        related_name="rt_competencias",
        help_text="Denormalizado pra RLS + EXCLUDE GIST.",
    )
    rt = models.ForeignKey(
        ResponsavelTecnicoTenant,
        on_delete=models.PROTECT,
        related_name="competencias",
    )
    grandeza = models.CharField(
        max_length=80,
        help_text=(
            "Grandeza acreditada (massa, volume, temperatura, dimensional, "
            "etc.). Texto livre — NIT-DICLA-016 lista grandezas; whitelist "
            "Wave A. Lowercase + underscore (ex: 'massa', 'temperatura_ar')."
        ),
    )
    carta_competencia_anexo_id = models.UUIDField(
        null=True,
        blank=True,
        help_text=(
            "Anexo com carta de competencia formal. Opcional aqui; alguns "
            "escopos exigem (validacao na camada de servico/Wave A)."
        ),
    )
    declarado_em = models.DateField(
        help_text="Data de inicio da vigencia da competencia.",
    )
    vigente_ate = models.DateField(
        null=True,
        blank=True,
        help_text="Fim da vigencia (NULL = indefinido).",
    )
    criado_em = models.DateTimeField(auto_now_add=True, db_index=True)
    criado_por = models.ForeignKey(
        Usuario,
        on_delete=models.PROTECT,
        related_name="rt_competencia_declarou",
    )

    class Meta:
        app_label = "responsavel_tecnico"
        db_table = "responsavel_tecnico_competencia"
        verbose_name = "Competencia declarada de RT"
        verbose_name_plural = "Competencias declaradas de RT"
        ordering = ["-criado_em"]
        indexes = [
            models.Index(fields=["tenant", "grandeza", "vigente_ate"]),
            models.Index(fields=["rt"]),
        ]

    def __str__(self) -> str:
        return f"RT {self.rt_id} competente em {self.grandeza}"
