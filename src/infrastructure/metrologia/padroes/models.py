# ruff: noqa: RUF012 — choices derivados de enum (list mutavel ok em Model)
"""M5 `metrologia/padroes` — modelos Django (T-PAD-010..016).

6 tabelas espelhando os snapshots de `src/domain/metrologia/padroes/entities.py`
(ADR-0007 spec-as-source — o use case NUNCA conhece Django; o adapter em
`repositories.py` converte Model PG <-> Snapshot). Choices derivados 1:1 dos
enums de dominio (anti-drift — o enum e a fonte canonica).

VOs metrologicos (Grandeza/FaixaMedicao/IncertezaExpandida) viajam como JSON
(`grandezas`/`faixas`/`incertezas_certificado`) — o adapter serializa/parseia
(reuso do padrao M4 `snapshot_*_json`). NAO recriar VO aqui (T-PAD-003).

Schema-irmaos na sequencia de migrations (ADR-0002/0031/0070):
- 0001_initial: CreateModel das 6 tabelas + UNIQUE(tenant, numero_serie).
- 0002_rls_policies: RLS pattern v2 (ADR-0002 §6) nas 6 tabelas.
- 0003_triggers_worm: incertezas-so-via-recal (INV-PAD-006 via GUC
  `app.padrao_recal_em_curso`) + block-delete (INV-SOFT-002) + WORM em
  recal/VI/PT/analise-carta.
- 0004_grants_app_user: GRANT app_user (PROD OWNER=app_migrator — SEG analogo M4).
"""

from __future__ import annotations

import uuid
from enum import Enum

from django.db import models

from src.domain.metrologia.padroes.enums import (
    ClassePadrao,
    DecisaoRTCarta,
    EstadoPadrao,
    RegraWesternElectric,
    ResultadoPT,
    ResultadoVI,
    StatusRecal,
    SubtipoPadrao,
    VinculacaoCadeia,
)


def _choices(enum_cls: type[Enum]) -> list[tuple[str, str]]:
    """Choices (value, value) a partir do enum de dominio (1:1 anti-drift)."""
    return [(membro.value, str(membro.value)) for membro in enum_cls]


class PadraoMetrologico(models.Model):
    """Agregado raiz — padrao metrologico do laboratorio do tenant (ADR-0040).

    Soft-delete padrao B (ADR-0031 — `revogado_em`; hard DELETE bloqueado por
    trigger INV-SOFT-002). Vigencia canonica ADR-0030. CAS via `revision`
    (ADR-0065 paralelo). `incertezas_certificado`/`validade_certificado_*`/
    `proximo_recal` so mutam dentro do fluxo de recal (INV-PAD-006 — trigger
    PG bloqueia UPDATE direto sem o GUC `app.padrao_recal_em_curso`).
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, serialize=False)
    tenant = models.ForeignKey(
        "tenant.tenant",
        on_delete=models.PROTECT,
        related_name="padroes_metrologicos",
    )
    numero_serie = models.CharField(
        max_length=120,
        help_text="UNIQUE por tenant (INV-PAD-001). Imutavel pos 1o uso.",
    )
    fabricante = models.CharField(max_length=120)
    modelo = models.CharField(max_length=120)
    subtipo = models.CharField(
        max_length=30,
        choices=_choices(SubtipoPadrao),
        default=SubtipoPadrao.PRINCIPAL.value,
        help_text="PRINCIPAL vs auxiliar cl. 6.4.5 (C-8).",
    )
    grandezas = models.JSONField(
        default=list,
        help_text="Lista de Grandeza (VO) serializada. >=1. Adapter parseia.",
    )
    faixas = models.JSONField(
        default=list,
        help_text="Lista de FaixaMedicao (VO) serializada. >=1.",
    )
    incertezas_certificado = models.JSONField(
        default=list,
        help_text=(
            "Lista de IncertezaExpandida (VO). >=1. So muta via fluxo de recal "
            "(INV-PAD-006 — trigger PG exige GUC app.padrao_recal_em_curso)."
        ),
    )
    vinculacao = models.CharField(
        max_length=20,
        choices=_choices(VinculacaoCadeia),
        help_text="Cadeia de rastreabilidade ao SI (cl. 6.5). RBC exige perfil A (INV-PAD-005).",
    )
    classe = models.CharField(max_length=10, choices=_choices(ClassePadrao))
    cert_externo_storage_key = models.CharField(
        max_length=200,
        blank=True,
        default="",
        help_text="Chave opaca do binario cifrado (KMS por-tenant — C-14). Nunca PII em claro.",
    )
    validade_certificado_rastreabilidade = models.DateField(
        help_text="So muta via recal (INV-PAD-006)."
    )
    proximo_recal = models.DateField(help_text="So muta via recal (INV-PAD-006).")
    intervalo_recal_meses = models.IntegerField(
        help_text="Configuravel (C-9 — cl. 6.4.7 + ILAC-G24). NAO cravar valor R111."
    )
    intervalo_vi_meses = models.IntegerField(help_text="Configuravel (C-9).")
    criterio_intervalo = models.TextField(
        help_text="Justificativa do intervalo (cl. 6.4.7 — C-9). NAO PII."
    )
    estado = models.CharField(
        max_length=40,
        choices=_choices(EstadoPadrao),
        default=EstadoPadrao.EM_USO.value,
        help_text="Maquina de estados (plan §14). Apenas EM_USO libera uso em calibracao.",
    )
    revision = models.IntegerField(
        default=0,
        help_text="Optimistic lock CAS (ADR-0065 paralelo). UPDATE WHERE revision=:esperada.",
    )
    rastreabilidade_origem_revogada = models.BooleanField(
        default=False,
        help_text=(
            "Flag transversal (C-5 FURO-4). True bloqueia uso INDEPENDENTE do estado "
            "(evento externo: lab de origem perdeu acreditacao — paralelo ADR-0045)."
        ),
    )
    vigencia_inicio = models.DateTimeField(help_text="Vigencia canonica ADR-0030.")
    correlation_id = models.UUIDField(default=uuid.uuid4, help_text="Cadeia forense.")
    descricao = models.TextField(blank=True, default="", help_text="<=500 chars anti-PII.")
    localizacao_lab = models.CharField(
        max_length=200,
        blank=True,
        default="",
        help_text="<=200 chars anti-PII (nao logar em claro).",
    )
    revogado_em = models.DateTimeField(
        null=True, blank=True, help_text="Soft-delete B (ADR-0031). NULL = vigente."
    )
    motivo_revogacao = models.TextField(
        blank=True, default="", help_text=">=10 chars quando revogado (ADR-0030)."
    )
    criado_em = models.DateTimeField(auto_now_add=True, db_index=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "padrao_metrologico"
        verbose_name = "Padrao Metrologico"
        verbose_name_plural = "Padroes Metrologicos"
        ordering = ["-criado_em"]
        constraints = [
            models.UniqueConstraint(
                fields=("tenant", "numero_serie"),
                name="uq_padrao_numero_serie_por_tenant",
            ),
        ]
        indexes = [
            models.Index(fields=["tenant", "estado", "proximo_recal"], name="pad_tenant_est_recal_idx"),
            models.Index(fields=["tenant", "subtipo"], name="pad_tenant_subtipo_idx"),
        ]

    def __str__(self) -> str:
        return f"PadraoMetrologico({self.numero_serie} — {self.estado})"


class RecalExternoPadrao(models.Model):
    """Recal externo (envio -> retorno -> aprovacao RT). Imutavel pos retorno.

    Pos `retornado_em`, trigger WORM bloqueia mutacao dos valores retornados;
    APENAS a transicao `aprovado_rt_em`/`aprovado_rt_id_hash` (NULL -> valor,
    one-shot) e permitida — C-4 FURO-1 (analise critica do RT libera EM_USO).
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, serialize=False)
    tenant = models.ForeignKey(
        "tenant.tenant", on_delete=models.PROTECT, related_name="recais_padrao"
    )
    padrao = models.ForeignKey(
        PadraoMetrologico, on_delete=models.PROTECT, related_name="recais"
    )
    enviado_em = models.DateTimeField()
    lab_externo = models.CharField(max_length=200, help_text="Nome do lab (sem PII direta).")
    responsavel_envio_id_hash = models.CharField(
        max_length=80, help_text="HashVersionado v<NN>$<base64> (ADR-0064) — funcionario."
    )
    status = models.CharField(max_length=30, choices=_choices(StatusRecal))
    numero_protocolo_lab_externo = models.CharField(max_length=120, blank=True, default="")
    retornado_em = models.DateTimeField(null=True, blank=True)
    cert_externo_novo_storage_key = models.CharField(max_length=200, blank=True, default="")
    incertezas_novas = models.JSONField(default=list)
    validade_nova = models.DateField(null=True, blank=True)
    valor_convencional_novo = models.DecimalField(
        max_digits=30, decimal_places=12, null=True, blank=True
    )
    aprovado_rt_em = models.DateTimeField(null=True, blank=True, help_text="C-4 — analise critica RT.")
    aprovado_rt_id_hash = models.CharField(
        max_length=80, blank=True, default="", help_text="C-4 — RT que aprovou (HashVersionado)."
    )
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "recal_externo_padrao"
        verbose_name = "Recal Externo de Padrao"
        verbose_name_plural = "Recais Externos de Padrao"
        ordering = ["-enviado_em"]
        indexes = [
            models.Index(fields=["tenant", "padrao", "status"], name="recal_tenant_pad_st_idx"),
        ]

    def __str__(self) -> str:
        return f"RecalExternoPadrao({self.padrao_id} — {self.status})"


class VerificacaoIntermediaria(models.Model):
    """VI periodica (cl. 6.4.10 — INV-022). Append-only WORM."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, serialize=False)
    tenant = models.ForeignKey(
        "tenant.tenant", on_delete=models.PROTECT, related_name="vis_padrao"
    )
    padrao = models.ForeignKey(
        PadraoMetrologico, on_delete=models.PROTECT, related_name="verificacoes_intermediarias"
    )
    data_vi = models.DateTimeField()
    executor_id_hash = models.CharField(max_length=80, help_text="HashVersionado (ADR-0064).")
    metodo_canonicalizado = models.TextField(help_text="<=500 chars anti-PII (ADR-0029).")
    metodo_hash = models.CharField(max_length=80)
    resultado = models.CharField(max_length=20, choices=_choices(ResultadoVI))
    desvio_observado = models.DecimalField(
        max_digits=30, decimal_places=12, null=True, blank=True
    )
    acao_corretiva_canonicalizada = models.TextField(
        blank=True, default="", help_text=">=30 chars se REPROVADO (ADR-0029)."
    )
    acao_corretiva_hash = models.CharField(max_length=80, blank=True, default="")
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "verificacao_intermediaria"
        verbose_name = "Verificacao Intermediaria"
        verbose_name_plural = "Verificacoes Intermediarias"
        ordering = ["-data_vi"]
        indexes = [
            models.Index(fields=["tenant", "padrao", "data_vi"], name="vi_tenant_pad_data_idx"),
        ]

    def __str__(self) -> str:
        return f"VerificacaoIntermediaria({self.padrao_id} — {self.resultado})"


class IntercomparacaoPT(models.Model):
    """Intercomparacao / proficiency testing (cl. 6.6 — INV-023, perfil A). WORM.

    `data_inicio`/`lab_organizador`/`protocolo` imutaveis pos insert; o resultado
    (`resultado`/`data_resultado`/`zeta_score`/`relatorio_pt_storage_key`)
    transiciona uma vez (NULL -> valor) e congela pos finalizacao
    (`data_resultado` preenchido). `nao_conformidade_id` NAO e congelado de
    proposito: a NC do modulo `nao-conformidades` (Wave B+) costuma ser aberta
    DEPOIS da finalizacao de um PT rejeitado, entao o vinculo precisa poder ser
    gravado tardiamente (o trigger `intercomparacao_pt_worm_check` deliberadamente
    nao o inclui na lista congelada).
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, serialize=False)
    tenant = models.ForeignKey(
        "tenant.tenant", on_delete=models.PROTECT, related_name="pts_padrao"
    )
    padrao = models.ForeignKey(
        PadraoMetrologico, on_delete=models.PROTECT, related_name="intercomparacoes_pt"
    )
    lab_organizador = models.CharField(max_length=200)
    protocolo = models.CharField(max_length=120)
    data_inicio = models.DateTimeField()
    resultado = models.CharField(  # noqa: DJ001 — choice field: NULL = PT sem resultado (cl. 6.6); "" nao e choice valido
        max_length=20, choices=_choices(ResultadoPT), null=True, blank=True
    )
    data_resultado = models.DateTimeField(null=True, blank=True)
    zeta_score = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True)
    relatorio_pt_storage_key = models.CharField(max_length=200, blank=True, default="")
    nao_conformidade_id = models.UUIDField(
        null=True, blank=True, help_text="Ref modulo nao-conformidades (Wave B+)."
    )
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "intercomparacao_pt"
        verbose_name = "Intercomparacao / PT"
        verbose_name_plural = "Intercomparacoes / PT"
        ordering = ["-data_inicio"]
        indexes = [
            models.Index(fields=["tenant", "padrao", "data_inicio"], name="pt_tenant_pad_data_idx"),
        ]

    def __str__(self) -> str:
        return f"IntercomparacaoPT({self.protocolo} — {self.resultado or 'EM_CURSO'})"


class AnaliseCartaControle(models.Model):
    """Registro WORM congelado da decisao derivada da carta Shewhart (ADR-0070).

    Snapshot dos LIMITES vigentes no instante da decisao + `versao_motor_shewhart`
    (cl. 7.11) + decisao do RT — reconstruivel em auditoria CGCRE (cl. 8.4). NAO
    copia os pontos (vivem WORM nas VIs/recais — `pontos_referenciados_ids`).
    Append-only WORM. INV-PAD-010.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, serialize=False)
    tenant = models.ForeignKey(
        "tenant.tenant", on_delete=models.PROTECT, related_name="analises_carta_controle"
    )
    padrao = models.ForeignKey(
        PadraoMetrologico, on_delete=models.PROTECT, related_name="analises_carta_controle"
    )
    regra_violada = models.CharField(max_length=30, choices=_choices(RegraWesternElectric))
    pontos_referenciados_ids = models.JSONField(
        default=list, help_text="FKs VIs/recais (sem copiar valor)."
    )
    linha_central = models.DecimalField(max_digits=30, decimal_places=12)
    ucl = models.DecimalField(max_digits=30, decimal_places=12)
    lcl = models.DecimalField(max_digits=30, decimal_places=12)
    sigma = models.DecimalField(max_digits=30, decimal_places=12)
    n_pontos = models.IntegerField()
    janela_meses = models.IntegerField()
    versao_motor_shewhart = models.CharField(max_length=50)
    decisao_rt = models.CharField(max_length=30, choices=_choices(DecisaoRTCarta))
    justificativa_canonicalizada = models.TextField(help_text="ADR-0029 anti-PII.")
    justificativa_hash = models.CharField(max_length=80)
    assinatura_a3_rt_id = models.UUIDField(
        null=True, blank=True, help_text="NULL ate A3 plugar (Wave A)."
    )
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "analise_carta_controle"
        verbose_name = "Analise de Carta de Controle"
        verbose_name_plural = "Analises de Carta de Controle"
        ordering = ["-criado_em"]
        indexes = [
            models.Index(fields=["tenant", "padrao", "criado_em"], name="acc_tenant_pad_cri_idx"),
        ]

    def __str__(self) -> str:
        return f"AnaliseCartaControle({self.padrao_id} — {self.regra_violada} -> {self.decisao_rt})"


class VinculoAuxiliar(models.Model):
    """Vinculo temporal N:N padrao principal <-> auxiliar (cl. 6.4.5 — C-8).

    Carrega a grandeza de influencia que o auxiliar monitora (temp/umidade/
    pressao) — usada pra snapshotar a leitura ambiental no momento do uso do
    principal (PadraoUsadoSnapshot). Temporal (ADR-0030 — `revogado_em`).
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, serialize=False)
    tenant = models.ForeignKey(
        "tenant.tenant", on_delete=models.PROTECT, related_name="vinculos_auxiliar"
    )
    padrao_principal = models.ForeignKey(
        PadraoMetrologico, on_delete=models.PROTECT, related_name="vinculos_como_principal"
    )
    padrao_auxiliar = models.ForeignKey(
        PadraoMetrologico, on_delete=models.PROTECT, related_name="vinculos_como_auxiliar"
    )
    grandeza_influencia = models.JSONField(
        help_text="Grandeza (VO) que o auxiliar monitora (temp/umidade/pressao)."
    )
    vigencia_inicio = models.DateTimeField()
    revogado_em = models.DateTimeField(null=True, blank=True, help_text="ADR-0030. NULL = vigente.")
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "vinculo_auxiliar"
        verbose_name = "Vinculo Auxiliar"
        verbose_name_plural = "Vinculos Auxiliares"
        ordering = ["-vigencia_inicio"]
        indexes = [
            models.Index(
                fields=["tenant", "padrao_principal", "revogado_em"],
                name="vinc_tenant_princ_rev_idx",
            ),
        ]

    def __str__(self) -> str:
        return f"VinculoAuxiliar({self.padrao_principal_id} <- {self.padrao_auxiliar_id})"
