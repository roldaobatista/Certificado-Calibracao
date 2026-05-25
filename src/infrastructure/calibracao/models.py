"""Marco 4 — modelos Django metrologia/calibracao (T-CAL-001 minimal).

Estado inicial:
- Calibracao (calibracao.Calibracao) — entidade raiz agregado; sequence
  global calibracao_numero_seq_global + UNIQUE(tenant, numero_interno)
  (paralelo ADR-0056 + INV-CAL-NUM-001).

Spec autoritativa: docs/faseamento/M4-calibracao/spec.md §3.2 + §16.4
(absorve 10 BLOQUEANTE + 23 MEDIO dos 4 reviews P2).

Demais entidades (Leitura, LeituraCorrecao, CondicoesAmbientais,
OrcamentoIncerteza, ComponenteIncerteza, OrcamentoPorPonto, PadraoUsado,
RecepcaoItemCalibracao, MedicaoControle, EventoDeCalibracao,
NaoConformidade, AnaliseImpactoNCProficiencia, LaboratorioSubcontratado,
AceiteSubcontratacao, AceiteRegraDecisao, OverrideRegraDecisaoCliente,
ReclamacaoCalibracao, ConsentimentoContatoTecnicoCliente,
ConsentimentoFotoRecusado, AvaliacaoPeriodicaSubcontratado,
PlanoAcaoProficienciaWarning, EventoBackupMetrologico) entram em
migrations subsequentes (T-CAL-002..023).

RLS policies + triggers + UNIQUE indexes concorrencia (ADR-0065) =
T-CAL-002+ (migrations-irmas na sequencia).
"""

from __future__ import annotations

import uuid

from django.db import models

# 6 zonas ILAC G8 + NA (ADR-0024 revisado P3 / INV-CAL-DEC-005)
ZONA_ILAC_G8_CHOICES = [
    ("PASS", "Pass (valor + U dentro de [LSL, USL])"),
    ("CONDITIONAL_PASS", "Conditional pass (valor dentro, U cruza limite)"),
    ("PASS_COM_RESSALVA", "Pass com ressalva (banda de guarda 30%)"),
    ("CONDITIONAL_FAIL", "Conditional fail (valor fora, U cruza limite)"),
    ("FAIL_COM_RESSALVA", "Fail com ressalva"),
    ("FAIL", "Fail (valor + U totalmente fora)"),
    ("NA", "Nao aplicavel (calibracao descritiva)"),
]

# Maquina de estados (spec §4.1) — 12 estados
STATUS_CALIBRACAO_CHOICES = [
    ("recepcionada", "Recepcionada"),
    ("configurada", "Configurada"),
    ("em_execucao", "Em execucao"),
    ("em_revisao_1", "Em revisao 1 (RT 1a conferencia)"),
    ("aguardando_2a_conferencia", "Aguardando 2a conferencia"),
    ("aprovada", "Aprovada (imutavel)"),
    ("rejeitada", "Rejeitada"),
    ("cancelada", "Cancelada"),
    ("nao_conforme", "Nao conforme"),
    ("pendente_resolucao_nc", "Pendente resolucao NC"),
    ("aguardando_subcontratado", "Aguardando subcontratado"),
    ("recebida_do_subcontratado", "Recebida do subcontratado"),
]

# Decisao agregada (snapshot ILAC G8)
DECISAO_CHOICES = [
    ("APROVADO", "Aprovado"),
    ("REPROVADO", "Reprovado"),
    ("CONDICIONAL", "Condicional"),
    ("NA", "Nao aplicavel"),
]

# Regra de decisao ADR-0024
REGRA_DECISAO_CHOICES = [
    ("ACEITACAO_SIMPLES", "Aceitacao simples (ILAC G8 §4.2)"),
    ("BANDA_GUARDA_30", "Banda de guarda 30% (ILAC G8 §4.4)"),
    ("RISCO_COMPARTILHADO", "Risco compartilhado (ILAC G8 §4.3 + JCGM 106)"),
]

# Tipo acreditacao
TIPO_ACREDITACAO_CHOICES = [
    ("RBC", "RBC (laboratorio acreditado CGCRE)"),
    ("NAO_RBC", "Nao RBC"),
]


class Calibracao(models.Model):
    """Raiz agregado metrologica (ISO/IEC 17025 + ADRs 0023/0024/0025/0026/0040/0064/0065).

    Estados terminais: aprovada, rejeitada, cancelada.
    Estado `aprovada` IMUTAVEL pos-emissao (INV-CAL-WORM-001 + trigger PG
    em migration 0002). Reprocessar exige nova Calibracao com causation_id.
    """

    # ----- Identidade + multi-tenancy -----
    id = models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)
    tenant = models.ForeignKey(
        "tenant.Tenant",
        on_delete=models.PROTECT,
        related_name="calibracoes",
    )
    numero_interno = models.BigIntegerField(
        help_text=(
            "Gerado por sequence global calibracao_numero_seq_global no DEFAULT "
            "da migration (paralelo ADR-0056 + INV-CAL-NUM-001). "
            "UNIQUE(tenant, numero_interno). Buracos por rollback aceitos."
        ),
    )
    # numero_exibido GENERATED ALWAYS AS ('CAL-' || EXTRACT(YEAR FROM criada_em) ||
    # '-' || LPAD(numero_interno::text, 6, '0')) STORED — aplicado em migration 0002.
    numero_exibido = models.CharField(
        max_length=20,
        blank=True,
        default="",
        help_text="GENERATED STORED via SQL em migration 0002 — formato CAL-YYYY-NNNNNN.",
    )

    # ----- Vinculacao operacional -----
    atividade_os_id = models.UUIDField(
        null=True,
        blank=True,
        help_text=(
            "FK AtividadeDaOS (db_constraint=False — modulo ordens_servico). "
            "NULL em recepcao avulsa (US-CAL-001). ADR-0023."
        ),
    )
    cliente = models.ForeignKey(
        "clientes.Cliente",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        db_constraint=False,
        related_name="calibracoes",
        help_text=(
            "Pode ficar NULL pos-anonimizacao (ADR-0032 + INV-CAL-ANON-001). "
            "Hash preservado em cliente_referencia_hash."
        ),
    )
    cliente_referencia_hash = models.CharField(
        max_length=80,
        help_text=(
            "HashVersionado canonico v<NN>$<base64> (ADR-0064 + INV-HMAC-001). "
            "Preserva audit pos-anonimizacao (ADR-0032)."
        ),
    )
    cliente_key_id = models.CharField(max_length=40, help_text="KMS key id ADR-0064 (HMAC_KEY_<tenant>).")

    instrumento = models.ForeignKey(
        "equipamentos.Equipamento",
        on_delete=models.PROTECT,
        related_name="calibracoes",
        help_text="Equipamento do cliente em calibracao (M2).",
    )
    snapshot_equipamento_json = models.JSONField(
        default=dict,
        help_text=(
            "Snapshot imutavel capturado em recepcionarInstrumento (cl. 7.4): "
            "nome, tag, NS, fabricante, modelo, perfil_tenant_snapshot (ADR-0022). "
            "INV-CAL-WORM-001."
        ),
    )

    # ----- Procedimento + escopo + configuracao -----
    procedimento_id = models.UUIDField(
        null=True,
        blank=True,
        help_text=(
            "FK ProcedimentoCalibracao (db_constraint=False — modulo procedimentos a criar). "
            "NOT NULL apos configurarCalibracao (US-CAL-016). ADR-0030 vigencia."
        ),
    )
    procedimento_versao_snapshot = models.JSONField(
        default=dict,
        blank=True,
        help_text=(
            "Snapshot capturado em configurarCalibracao (US-CAL-016): "
            "codigo + versao_semver + hash_anexo_pdf. INV-CAL-WORM-001."
        ),
    )
    tipo_acreditacao = models.CharField(
        max_length=10,
        choices=TIPO_ACREDITACAO_CHOICES,
        default="NAO_RBC",
        help_text="RBC requer escopo + CMC + acordo regra decisao + vinculacao SI (INV-CAL-RAST-002).",
    )
    escopo_id = models.UUIDField(
        null=True,
        blank=True,
        help_text="FK Escopo CMC (db_constraint=False). NULL se NAO_RBC.",
    )
    configuracao_id = models.UUIDField(
        null=True,
        blank=True,
        help_text="FK ConfiguracaoCalibracao (a criar T-CAL-NNN). Preenchido em configurarCalibracao.",
    )

    # ----- Maquina de estados -----
    status = models.CharField(
        max_length=30,
        choices=STATUS_CALIBRACAO_CHOICES,
        default="recepcionada",
        help_text="Maquina estados §4.1 spec. Trigger PG em migration 0002 bloqueia UPDATE pos `aprovada`.",
    )

    # ----- Concorrencia ADR-0065 (P-CAL-T1 tech-lead) -----
    revision = models.IntegerField(
        default=0,
        help_text=(
            "Optimistic lock CAS — ADR-0065 + INV-CAL-CONC-003. "
            "UPDATE com WHERE revision = :expected RETURNING revision+1; "
            "0 rows -> 409 ConflitoVersao. 11 transicoes de estado fazem CAS."
        ),
    )

    # ----- Atores (anti-fraude INV-CAL-FRAUDE-*) -----
    executor_id = models.UUIDField(
        null=True,
        blank=True,
        help_text=(
            "Metrologista que registra leituras (INV-CAL-FRAUDE-EXEC-001). "
            "NULLABLE quando subcontratado_id NOT NULL (P-CAL-T9 tech-lead)."
        ),
    )
    revisor_id = models.UUIDField(
        null=True,
        blank=True,
        help_text="RT 1a conferencia (INV-CAL-FRAUDE-REV-001). cl. 6.2.",
    )
    conferente_id = models.UUIDField(
        null=True,
        blank=True,
        help_text=(
            "RT 2a conferencia (INV-CAL-FRAUDE-CONF-001 + ADR-0026). "
            "Default conferente_id != revisor_id; excecao via Excecao2aConferencia (4 condicoes)."
        ),
    )
    recebedor_user_id = models.UUIDField(
        null=True,
        blank=True,
        help_text=(
            "Quem recebe cert externo do subcontratado (INV-CAL-FRAUDE-RECEB-001). "
            "NOT NULL quando subcontratado_id NOT NULL. P-CAL-T9 tech-lead."
        ),
    )
    excecao_2a_conf_id = models.UUIDField(
        null=True,
        blank=True,
        help_text="FK Excecao2aConferencia (ADR-0026 4 condicoes objetivas + 5%/mes).",
    )

    # ----- Decisao ILAC G8 + PFA/PRA (ADR-0024 revisado P3 / 6 zonas) -----
    decisao = models.CharField(
        max_length=15,
        choices=DECISAO_CHOICES,
        default="NA",
        help_text="Decisao agregada. zona_ilac_g8 carrega zona granular (INV-CAL-DEC-005).",
    )
    zona_ilac_g8 = models.CharField(
        max_length=20,
        choices=ZONA_ILAC_G8_CHOICES,
        default="NA",
        help_text=(
            "6 zonas ILAC G8:09/2019 §4 tabela 1 + NA. INV-CAL-DEC-005 "
            "(CHECK constraint em migration 0002). Calculado por motor §3.3."
        ),
    )
    regra_decisao = models.CharField(
        max_length=25,
        choices=REGRA_DECISAO_CHOICES,
        default="ACEITACAO_SIMPLES",
        help_text=(
            "Snapshot da regra acordada (ADR-0024 + INV-CAL-DEC-001). "
            "Lock pos APROVADA via trigger PG (INV-CAL-DEC-003)."
        ),
    )
    regra_decisao_override_cliente = models.BooleanField(
        default=False,
        help_text=(
            "True se cliente requisitou override (INV-CAL-DEC-002). "
            "Exige clausula contratual + assinatura A3 (AC-CAL-002-3 + P-CAL-A3)."
        ),
    )
    pfa_calculada = models.DecimalField(
        max_digits=6,
        decimal_places=4,
        null=True,
        blank=True,
        help_text=(
            "Probabilidade de aceitacao falsa (ILAC G8 §4.4 + JCGM 106 §9). "
            "NOT NULL quando regra_decisao=BANDA_GUARDA_30 (INV-CAL-DEC-004)."
        ),
    )
    pra_calculada = models.DecimalField(
        max_digits=6,
        decimal_places=4,
        null=True,
        blank=True,
        help_text=(
            "Probabilidade de rejeicao falsa. NOT NULL quando "
            "regra_decisao=RISCO_COMPARTILHADO (INV-CAL-DEC-004)."
        ),
    )
    nivel_confianca = models.DecimalField(
        max_digits=6,
        decimal_places=4,
        default="0.9545",
        help_text="k=2 -> 95.45%. Usado no calculo PFA/PRA.",
    )

    # ----- Acordo cliente regra decisao (cl. 7.1.3 + P-CAL-R3 RBC + P-CAL-A3 advogado) -----
    regra_decisao_acordada_em = models.DateTimeField(
        null=True,
        blank=True,
        help_text=(
            "Quando cliente acordou a regra (cl. 7.1.3). NOT NULL antes de "
            "em_revisao_1 quando tipo_acreditacao=RBC (INV-CAL-DEC-006)."
        ),
    )
    regra_decisao_acordada_documento_id = models.UUIDField(
        null=True,
        blank=True,
        help_text=(
            "FK AceiteRegraDecisao (db_constraint=False — entidade a criar T-CAL-016). "
            "Predicate regra_decisao_acordada_cobre valida vigencia."
        ),
    )
    regra_decisao_acordada_hash = models.CharField(
        max_length=80,
        blank=True,
        default="",
        help_text="HashVersionado v<NN>$<base64> do texto acordado (ADR-0064 + INV-DOC-CANON-001).",
    )

    # ----- Analise critica do pedido (cl. 7.1.1 + P-CAL-R4 RBC) -----
    analise_critica_pedido_id = models.UUIDField(
        null=True,
        blank=True,
        help_text=(
            "FK orcamento.analise_critica quando atividade_os_id NOT NULL. "
            "cl. 7.1.1. (db_constraint=False)."
        ),
    )
    analise_critica_pedido_inline_hash = models.CharField(
        max_length=80,
        blank=True,
        default="",
        help_text=(
            "Hash canonicalizado quando recepcao avulsa (atividade_os_id IS NULL). "
            "INV-CAL-ANAL-001 + AC-CAL-001-3. CHECK composta em migration 0002."
        ),
    )
    analise_critica_pedido_inline_canonicalizada = models.TextField(
        blank=True,
        default="",
        help_text=(
            "Texto >=100 chars + anti-PII INV-CAL-TXT-001 + INV-DOC-CANON-001. "
            "Pre-hash. Usado em recepcao avulsa."
        ),
    )
    capacidade_tecnica_confirmada_por_user_id = models.UUIDField(
        null=True,
        blank=True,
        help_text=(
            "Quem confirmou capacidade tecnica em recepcao avulsa (cl. 7.1.1). "
            "Use case bloqueia INSERT sem este campo."
        ),
    )

    # ----- Snapshot competencia RT (cl. 6.2 + P-CAL-R10 RBC + ADR-0022) -----
    snapshot_competencia_revisor_json = models.JSONField(
        null=True,
        blank=True,
        help_text=(
            "Capturado em aprovarRevisao (US-CAL-007 + AC-CAL-007-5 + INV-CAL-RT-002). "
            "Imutavel — preserva grandeza+faixa+vigencia da RTCompetencia na DATA da aprovacao."
        ),
    )
    snapshot_competencia_conferente_json = models.JSONField(
        null=True,
        blank=True,
        help_text=(
            "Capturado em aprovar2aConferencia (US-CAL-008 + AC-CAL-008-4). "
            "Imutavel. INV-CAL-RT-002 + ADR-0026."
        ),
    )

    # ----- Validacao software ISO 17025 cl. 7.11 (ADR-0025) -----
    versao_motor_calculo = models.CharField(
        max_length=50,
        blank=True,
        default="",
        help_text=(
            "Semver + commit-hash do motor (§3.3 spec + INV-CAL-VERSAO-001). "
            "Snapshot por calibracao pra replay deterministico em CGCRE 2050."
        ),
    )

    # ----- Subcontratacao (US-CAL-017 + cl. 6.6) -----
    subcontratado_id = models.UUIDField(
        null=True,
        blank=True,
        help_text=(
            "FK LaboratorioSubcontratado (db_constraint=False — T-CAL-014). "
            "NOT NULL quando fluxo subcontratacao ativo."
        ),
    )
    aceite_subcontratacao_id = models.UUIDField(
        null=True,
        blank=True,
        help_text=(
            "FK AceiteSubcontratacao (T-CAL-015). NOT NULL quando "
            "subcontratado_id NOT NULL (INV-CAL-SUBC-001)."
        ),
    )
    certificado_subcontratado_snapshot_json = models.JSONField(
        null=True,
        blank=True,
        help_text=(
            "Snapshot cert externo recebido (INV-CAL-SUBC-003). "
            "Imutavel apos registrarRecebimentoSubcontratado."
        ),
    )
    declaracao_subcontratacao_texto_id = models.UUIDField(
        null=True,
        blank=True,
        help_text=(
            "FK declaracao-subcontratacao-certificado-v1.0.md (ILAC G18 §6.3 + "
            "INV-CAL-SUBC-006). REQUER OAB+CGCRE."
        ),
    )

    # ----- Texto livre + cancelamento -----
    observacoes_gerais = models.TextField(
        blank=True,
        default="",
        help_text="<=500 chars + anti-PII INV-CAL-TXT-001 (regex saude estendida P-CAL-A2).",
    )
    motivo_cancelamento_hash = models.CharField(
        max_length=80,
        blank=True,
        default="",
        help_text="HashVersionado v<NN>$<base64> (ADR-0064) — quando status=cancelada.",
    )

    # ----- Forensica (correlation + causation) -----
    correlation_id = models.UUIDField(
        default=uuid.uuid4,
        help_text="Cadeia forense (NOVO-ALTO-1 Onda 7B retrofit M3 paralelo M4).",
    )
    causation_id = models.UUIDField(
        null=True,
        blank=True,
        help_text=(
            "FK calibracao_id que originou esta calibracao (reprocessamento). "
            "Estado APROVADA e imutavel — nova calibracao com causation_id."
        ),
    )

    # ----- Timestamps + autor -----
    criada_em = models.DateTimeField(auto_now_add=True, db_index=True)
    atualizada_em = models.DateTimeField(auto_now=True)
    criada_por_user_id = models.UUIDField(
        null=True,
        blank=True,
        help_text="Quem recepcionou (auditoria + cl. 7.1).",
    )

    class Meta:
        verbose_name = "Calibracao"
        verbose_name_plural = "Calibracoes"
        db_table = "calibracao"
        ordering = ["-criada_em"]
        constraints = [
            models.UniqueConstraint(
                fields=["tenant", "numero_interno"],
                name="uq_calibracao_numero_por_tenant",
            ),
        ]
        indexes = [
            models.Index(fields=["tenant", "status", "criada_em"], name="cal_tenant_st_cri_idx"),
            models.Index(fields=["tenant", "cliente"], name="cal_tenant_cliente_idx"),
            models.Index(fields=["tenant", "instrumento"], name="cal_tenant_instrum_idx"),
            models.Index(
                fields=["tenant", "instrumento", "criada_em"],
                condition=models.Q(status="aprovada"),
                name="cal_historico_inst_idx",
            ),
        ]

    def __str__(self) -> str:
        return f"Calibracao {self.numero_exibido or self.id} ({self.status})"


# =============================================================
# Leitura (cl. 7.5 ISO 17025 — imutavel apos INSERT)
# =============================================================

ORIGEM_LEITURA_CHOICES = [
    ("MANUAL", "Manual (operador digita)"),
    ("INTEGRACAO_SERIAL", "Integracao serial (cabo serial)"),
    ("INTEGRACAO_USB", "Integracao USB"),
]


class Leitura(models.Model):
    """Leitura individual em ponto+repeticao (cl. 7.5 ISO 17025).

    Imutavel pos-INSERT (INV-CAL-WORM-001 + trigger PG em migration 0004).
    Correcoes via `LeituraCorrecao` (rasura digital — entidade T-CAL-005).
    UNIQUE composto (tenant_id, calibracao_id, ponto, numero_repeticao)
    impede leituras duplicadas concorrentes (ADR-0065 + INV-CAL-CONC-001).
    """

    id = models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)
    tenant = models.ForeignKey(
        "tenant.Tenant",
        on_delete=models.PROTECT,
        related_name="leituras",
    )
    calibracao = models.ForeignKey(
        Calibracao,
        on_delete=models.PROTECT,
        related_name="leituras",
        help_text="Calibracao raiz agregado.",
    )
    ponto_calibracao = models.DecimalField(
        max_digits=20,
        decimal_places=8,
        help_text="Valor do ponto da calibracao (ex: 10.000 kg).",
    )
    numero_repeticao = models.IntegerField(
        help_text=(
            "1, 2, 3, ... Tipicamente 3-10 repeticoes por ponto. "
            "UNIQUE composto (tenant, calibracao, ponto, repeticao) — "
            "INV-CAL-CONC-001 + ADR-0065."
        ),
    )
    valor_lido = models.DecimalField(
        max_digits=20,
        decimal_places=8,
        help_text="Valor lido do instrumento sob calibracao.",
    )
    unidade = models.CharField(
        max_length=20,
        help_text="Unidade SI ou derivada (kg, g, mL, °C, ...).",
    )
    origem = models.CharField(
        max_length=20,
        choices=ORIGEM_LEITURA_CHOICES,
        default="MANUAL",
        help_text="Origem da leitura.",
    )
    timestamp = models.DateTimeField(
        help_text="Momento da leitura no instrumento (relogio do PC do operador).",
    )
    executor_id_hash = models.CharField(
        max_length=80,
        help_text=(
            "HashVersionado v<NN>$<base64> do executor (ADR-0064 + INV-CAL-FRAUDE-EXEC-001). "
            "UUID cru NAO persistido aqui — anti-stalking pos 25a."
        ),
    )
    client_event_id = models.UUIDField(
        null=True,
        blank=True,
        help_text=(
            "ID idempotente client-generated para sync de calibracao de campo "
            "(ADR-0027). UNIQUE parcial WHERE NOT NULL. NULL em laboratorio."
        ),
    )
    correlation_id = models.UUIDField(
        default=uuid.uuid4,
        help_text="Cadeia forense (paralelo M3).",
    )

    class Meta:
        verbose_name = "Leitura"
        verbose_name_plural = "Leituras"
        db_table = "leitura"
        ordering = ["calibracao", "ponto_calibracao", "numero_repeticao"]
        constraints = [
            # INV-CAL-CONC-001 + ADR-0065 — idempotencia forte
            models.UniqueConstraint(
                fields=["tenant", "calibracao", "ponto_calibracao", "numero_repeticao"],
                name="uq_leitura_ponto_repeticao",
            ),
            # Idempotencia client-event sync mobile (ADR-0027)
            models.UniqueConstraint(
                fields=["tenant", "calibracao", "client_event_id"],
                condition=models.Q(client_event_id__isnull=False),
                name="uq_leitura_client_event",
            ),
        ]
        indexes = [
            models.Index(fields=["tenant", "calibracao", "ponto_calibracao"], name="leit_cal_ponto_idx"),
        ]

    def __str__(self) -> str:
        return f"Leitura {self.ponto_calibracao}@{self.numero_repeticao} = {self.valor_lido}"
