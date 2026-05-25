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

# Subcontratacao — modo assinatura (P-CAL-A6 advogado)
ASSINATURA_MODO_CHOICES = [
    ("TOUCH", "Touch (biometria simples — exige declaracao alto-risco)"),
    ("A3", "A3 (certificado ICP-Brasil)"),
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


# =============================================================
# LeituraCorrecao (cl. 7.5 ISO 17025 — rasura digital)
# =============================================================


class LeituraCorrecao(models.Model):
    """Rasura digital sobre uma Leitura (cl. 7.5 ISO 17025).

    Preserva valor_original (NAO muta a Leitura — INV-CAL-WORM-001).
    Append-only WORM (INV-CAL-WORM-001 + trigger PG na migration).
    AC-CAL-004-7: so permitido quando calibracao.status IN
    (CONFIGURADA, EM_EXECUCAO). Apos EM_REVISAO_1 correcao exige
    reabertura formal via CAPA (gera NaoConformidade).
    Anti-fraude INV-CAL-FRAUDE-COR-001 (corretor=user).
    """

    id = models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)
    tenant = models.ForeignKey(
        "tenant.Tenant",
        on_delete=models.PROTECT,
        related_name="leituras_correcao",
    )
    leitura = models.ForeignKey(
        Leitura,
        on_delete=models.PROTECT,
        related_name="correcoes",
        help_text="Leitura corrigida (NAO muta — INV-CAL-WORM-001).",
    )
    valor_original = models.DecimalField(
        max_digits=20,
        decimal_places=8,
        help_text="Snapshot do valor_lido da Leitura ANTES da correcao.",
    )
    valor_corrigido = models.DecimalField(
        max_digits=20,
        decimal_places=8,
        help_text="Valor depois da correcao.",
    )
    razao_correcao_canonicalizada = models.TextField(
        help_text=(
            ">=30 chars + anti-PII INV-CAL-TXT-001 + INV-DOC-CANON-001 "
            "(UTF-8 + LF + NFC + marcadores <<<CORPO INICIO/FIM>>>)."
        ),
    )
    razao_correcao_hash = models.CharField(
        max_length=80,
        help_text="HashVersionado v<NN>$<base64> do texto canonicalizado (ADR-0064).",
    )
    corretor_id_hash = models.CharField(
        max_length=80,
        help_text=(
            "HashVersionado do corretor (ADR-0064). UUID cru NAO persistido "
            "aqui — anti-stalking. Validacao INV-CAL-FRAUDE-COR-001 feita no "
            "use case (corretor_user_id == request.user.id)."
        ),
    )
    corrigido_em = models.DateTimeField(
        auto_now_add=True,
        help_text="Momento da correcao.",
    )
    correlation_id = models.UUIDField(
        default=uuid.uuid4,
        help_text="Cadeia forense.",
    )

    class Meta:
        verbose_name = "Leitura — Correcao"
        verbose_name_plural = "Leituras — Correcoes"
        db_table = "leitura_correcao"
        ordering = ["-corrigido_em"]
        indexes = [
            models.Index(fields=["tenant", "leitura"], name="leitcorr_tenant_leit_idx"),
        ]

    def __str__(self) -> str:
        return f"LeituraCorrecao {self.leitura_id}: {self.valor_original} -> {self.valor_corrigido}"


# =============================================================
# CondicoesAmbientais (cl. 6.3.1 + NIT-DICLA-030 — snapshot WORM)
# =============================================================


class CondicoesAmbientais(models.Model):
    """Snapshot de condicoes ambientais no momento da medicao.

    Imutavel pos-INSERT (INV-CAL-WORM-001 + trigger PG na migration).
    INV-CAL-AMB-001: registrarLeitura bloqueia 412 quando
    `dentro_tolerancia=false` (override possivel com justificativa +
    audit + alerta P2 Qualidade).
    """

    id = models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)
    tenant = models.ForeignKey(
        "tenant.Tenant",
        on_delete=models.PROTECT,
        related_name="condicoes_ambientais",
    )
    temperatura_lida_celsius = models.DecimalField(
        max_digits=6,
        decimal_places=3,
        help_text="Temperatura medida na bancada/ambiente.",
    )
    umidade_lida_pct = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        help_text="Umidade relativa medida (0..100).",
    )
    pressao_lida_kpa = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Pressao barometrica (opcional por grandeza).",
    )
    temperatura_alvo_celsius = models.DecimalField(
        max_digits=6,
        decimal_places=3,
        null=True,
        blank=True,
        help_text="Temperatura alvo do ProcedimentoCalibracao.",
    )
    temperatura_tolerancia_celsius = models.DecimalField(
        max_digits=5,
        decimal_places=3,
        null=True,
        blank=True,
        help_text="Tolerancia +/- em torno da temperatura_alvo.",
    )
    umidade_alvo_pct = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Umidade alvo do ProcedimentoCalibracao.",
    )
    umidade_tolerancia_pct = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Tolerancia +/- em torno da umidade_alvo.",
    )
    # dentro_tolerancia GENERATED COLUMN sera adicionada via SQL na migration
    # (Django ORM nao tem suporte nativo; aceita ABS+CASE que sao IMMUTABLE).
    dentro_tolerancia = models.BooleanField(
        default=True,
        help_text=(
            "GENERATED em migration via ABS + CASE NULL-safe. INV-CAL-AMB-001 — "
            "registrarLeitura bloqueia 412 quando false."
        ),
    )
    executor_id_hash = models.CharField(
        max_length=80,
        help_text="HashVersionado executor (ADR-0064).",
    )
    medido_em = models.DateTimeField(
        help_text="Momento da medicao.",
    )
    correlation_id = models.UUIDField(
        default=uuid.uuid4,
    )

    class Meta:
        verbose_name = "Condicoes Ambientais"
        verbose_name_plural = "Condicoes Ambientais"
        db_table = "condicoes_ambientais"
        ordering = ["-medido_em"]
        indexes = [
            models.Index(fields=["tenant", "medido_em"], name="condamb_tenant_med_idx"),
        ]

    def __str__(self) -> str:
        return f"CondicoesAmbientais {self.temperatura_lida_celsius}°C / {self.umidade_lida_pct}%"


# =============================================================
# OrcamentoIncerteza + ComponenteIncerteza + OrcamentoPorPonto
# (cl. 7.6 ISO 17025 + NIT-DICLA-030 rev. 15)
# =============================================================

TIPO_COMPONENTE_CHOICES = [
    ("A", "Tipo A (estatistica — repetibilidade)"),
    ("B", "Tipo B (avaliacao por outros meios)"),
]

# §16.6 — 8 origens obrigatorias por grandeza (matriz CGCRE)
TIPO_ORIGEM_COMPONENTE_CHOICES = [
    ("REPETIBILIDADE", "Repetibilidade (Tipo A)"),
    ("RESOLUCAO_INSTRUMENTO", "Resolucao do instrumento"),
    ("INCERTEZA_PADRAO_REF", "Incerteza herdada do padrao de referencia"),
    ("DERIVA_PADRAO", "Deriva do padrao"),
    ("CONDICOES_AMBIENTAIS", "Condicoes ambientais (temp/umidade/pressao)"),
    ("EXCENTRICIDADE", "Excentricidade (balanca)"),
    ("POLARIZACAO_BIAS", "Polarizacao / bias conhecido (GUM §4.3)"),
    ("OUTRO", "Outro (justificavel)"),
]

DISTRIBUICAO_CHOICES = [
    ("NORMAL", "Normal"),
    ("RETANGULAR", "Retangular (uniforme)"),
    ("TRIANGULAR", "Triangular"),
    ("U", "U (arcoseno)"),
    ("OUTRA", "Outra"),
]

FORMULA_CALCULO_CHOICES = [
    ("REPETIBILIDADE_STD_MEDIA", "Repetibilidade — s(x)/sqrt(n) Tipo A"),
    ("RESOLUCAO_RETANGULAR", "Resolucao — d/(2*sqrt(3))"),
    ("PADRAO_CERTIFICADO", "Padrao certificado — U_pdr/k_pdr"),
    ("DERIVA_LINEAR", "Deriva linear historica do padrao"),
    ("TEMPERATURA_QUADRATICA", "Temperatura — coef * deltaT^2"),
    ("BIAS_CONHECIDO", "Bias conhecido (GUM §4.3)"),
    ("OUTRO", "Outro (justificavel)"),
]


class OrcamentoIncerteza(models.Model):
    """Orcamento de incerteza ponto-a-ponto (NIT-DICLA-030 rev. 15).

    Imutavel pos EM_REVISAO_1 (INV-CAL-WORM-001 — trigger PG na migration).
    Algoritmos 1 e 2 (GUM Decimal + Monte Carlo NumPy — spec §3.3 +
    ADR-0025 + ADR-0065). Replay deterministico em CI (30 fixtures).
    """

    id = models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)
    tenant = models.ForeignKey(
        "tenant.Tenant",
        on_delete=models.PROTECT,
        related_name="orcamentos_incerteza",
    )
    calibracao = models.ForeignKey(
        Calibracao,
        on_delete=models.PROTECT,
        related_name="orcamentos_incerteza",
    )
    # Snapshot do algoritmo 1 (GUM classico) — campos diretos pra query rapida
    u_combinada = models.DecimalField(
        max_digits=20,
        decimal_places=8,
        help_text="Snapshot do algoritmo 1 (GUM classico — pior caso quando OrcamentoPorPonto[]).",
    )
    grau_liberdade_efetivo = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Welch-Satterthwaite (GUM §G.4).",
    )
    k = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default="2.0",
        help_text="Fator de abrangencia (default k=2 -> 95.45%).",
    )
    U_expandida = models.DecimalField(
        max_digits=20,
        decimal_places=8,
        help_text="U = u_combinada * k.",
    )
    nivel_confianca = models.DecimalField(
        max_digits=5,
        decimal_places=3,
        default="0.9545",
        help_text="k=2 -> 95.45%.",
    )
    documentacao_agregacao = models.TextField(
        help_text=(
            ">=50 chars (INV-CAL-INC-001) declarando como u_combinada agrega quando "
            "OrcamentoPorPonto[] existe (NIT-DICLA-030 rev. 15 NOVO-3 RBC R2)."
        ),
    )
    versao_motor_calculo = models.CharField(
        max_length=50,
        help_text="Semver + commit-hash do motor (ADR-0025 + INV-CAL-VERSAO-001).",
    )
    # §16.6 — algoritmo 1 + algoritmo 2 separados em JSONB
    algoritmo_1_resultado = models.JSONField(
        help_text=(
            "Resultado completo do algoritmo 1 (GUM classico Decimal): "
            "u_combinada, U_expandida, k, grau_liberdade_efetivo, etc."
        ),
    )
    algoritmo_2_resultado = models.JSONField(
        null=True,
        blank=True,
        help_text=(
            "Resultado completo do algoritmo 2 (Monte Carlo NumPy + seed em "
            "Calibracao.id). NULL se 2o caminho nao aplicavel pra grandeza."
        ),
    )
    divergencia_pct = models.DecimalField(
        max_digits=5,
        decimal_places=3,
        null=True,
        blank=True,
        help_text=(
            "Divergencia entre algoritmo 1 e 2 em porcentagem. "
            "<=0.1% silencioso; 0.1-1% alerta P3; >1% bloqueia "
            "DivergenciaCalculoInaceitavel (NC automatica)."
        ),
    )
    replay_determinismo_hash = models.CharField(
        max_length=80,
        help_text=(
            "HashVersionado v<NN>$<base64> (ADR-0064) de inputs ordenados "
            "canonicamente + outputs separados. Regressao de calculo (mesmo "
            "input, output diferente) detectada em CI replay."
        ),
    )
    bias_orcado = models.DecimalField(
        max_digits=20,
        decimal_places=8,
        null=True,
        blank=True,
        help_text="Bias conhecido (GUM §4.3 + NIT-DICLA-030 — quando aplicavel).",
    )
    bias_origem = models.CharField(
        max_length=80,
        blank=True,
        default="",
        help_text="Origem do bias (ex: calibracao_externa_padrao_referencia).",
    )
    arredondamento_aplicado_regra = models.CharField(
        max_length=20,
        default="NIT_DICLA_030_2_DIGITOS_SIG",
        help_text="Regra de arredondamento (NIT-DICLA-030 §7.5).",
    )
    calculado_em = models.DateTimeField(
        auto_now_add=True,
    )
    correlation_id = models.UUIDField(
        default=uuid.uuid4,
    )

    class Meta:
        verbose_name = "Orcamento de Incerteza"
        verbose_name_plural = "Orcamentos de Incerteza"
        db_table = "orcamento_incerteza"
        ordering = ["-calculado_em"]
        indexes = [
            models.Index(fields=["tenant", "calibracao"], name="orcinc_tenant_cal_idx"),
        ]

    def __str__(self) -> str:
        return f"OrcamentoIncerteza U={self.U_expandida} (k={self.k})"


class ComponenteIncerteza(models.Model):
    """Componente individual do orcamento (1:N de OrcamentoIncerteza).

    Imutavel pos-INSERT (INV-CAL-WORM-001).
    Tipo A exige n_amostras >= 6 + s_x NOT NULL (INV-CAL-INC-003).
    Correlacao com outro componente via self-FK (GUM §5.2.2 +
    INV-CAL-INC-004).
    """

    id = models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)
    tenant = models.ForeignKey(
        "tenant.Tenant",
        on_delete=models.PROTECT,
        related_name="componentes_incerteza",
    )
    orcamento_incerteza = models.ForeignKey(
        OrcamentoIncerteza,
        on_delete=models.PROTECT,
        related_name="componentes",
    )
    nome_componente = models.CharField(
        max_length=80,
        help_text="Ex: 'Resolucao do indicador', 'Deriva do padrao'.",
    )
    tipo_componente = models.CharField(
        max_length=1,
        choices=TIPO_COMPONENTE_CHOICES,
        help_text="A=estatistico (repetibilidade); B=outros meios.",
    )
    tipo_origem_componente = models.CharField(
        max_length=30,
        choices=TIPO_ORIGEM_COMPONENTE_CHOICES,
        help_text=(
            "8 origens (§16.6). INV-CAL-INC-002 valida obrigatorias por "
            "grandeza+padrao (matriz componentes-obrigatorios-por-grandeza)."
        ),
    )
    distribuicao = models.CharField(
        max_length=20,
        choices=DISTRIBUICAO_CHOICES,
    )
    divisor = models.DecimalField(
        max_digits=15,
        decimal_places=5,
        help_text="Ex: sqrt(3) p/ retangular, sqrt(6) p/ triangular.",
    )
    valor_estimativa = models.DecimalField(
        max_digits=20,
        decimal_places=8,
    )
    contribuicao = models.DecimalField(
        max_digits=20,
        decimal_places=8,
    )
    grau_liberdade = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default="50.0",
    )
    fonte_default_padrao_id = models.UUIDField(
        null=True,
        blank=True,
        help_text="FK PadraoMetrologico (db_constraint=False — modulo padroes).",
    )
    formula_calculo = models.CharField(
        max_length=40,
        choices=FORMULA_CALCULO_CHOICES,
        help_text="§16.6 — formula declarada (matriz formula-calculo-por-grandeza).",
    )
    correlacao_com_componente_id = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="correlacionados",
        help_text="Self-FK GUM §5.2.2 — quando 2+ componentes vem do mesmo padrao.",
    )
    coeficiente_correlacao = models.DecimalField(
        max_digits=5,
        decimal_places=4,
        null=True,
        blank=True,
        help_text="-1 a 1; NOT NULL quando correlacao_com_componente_id NOT NULL.",
    )
    n_amostras = models.IntegerField(
        null=True,
        blank=True,
        help_text=(
            "NOT NULL quando tipo='A' (CHECK constraint na migration). "
            "INV-CAL-INC-003: n>=6 (NIT-DICLA-030 §7.4)."
        ),
    )
    s_x = models.DecimalField(
        max_digits=20,
        decimal_places=8,
        null=True,
        blank=True,
        help_text="Desvio-padrao amostral. NOT NULL quando tipo='A'.",
    )

    class Meta:
        verbose_name = "Componente de Incerteza"
        verbose_name_plural = "Componentes de Incerteza"
        db_table = "componente_incerteza"
        ordering = ["orcamento_incerteza", "nome_componente"]
        indexes = [
            models.Index(fields=["tenant", "orcamento_incerteza"], name="cmpinc_tenant_orc_idx"),
        ]

    def __str__(self) -> str:
        return f"Componente {self.nome_componente} ({self.tipo_componente})"


class OrcamentoPorPonto(models.Model):
    """Incerteza por ponto da calibracao (1:N de OrcamentoIncerteza).

    Imutavel pos-INSERT (INV-CAL-WORM-001).
    """

    id = models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)
    tenant = models.ForeignKey(
        "tenant.Tenant",
        on_delete=models.PROTECT,
        related_name="orcamentos_por_ponto",
    )
    orcamento_incerteza = models.ForeignKey(
        OrcamentoIncerteza,
        on_delete=models.PROTECT,
        related_name="pontos",
    )
    ponto_calibracao = models.DecimalField(
        max_digits=20,
        decimal_places=8,
    )
    u_combinada_no_ponto = models.DecimalField(
        max_digits=20,
        decimal_places=8,
    )
    U_expandida_no_ponto = models.DecimalField(
        max_digits=20,
        decimal_places=8,
    )
    k_no_ponto = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default="2.0",
    )

    class Meta:
        verbose_name = "Orcamento por Ponto"
        verbose_name_plural = "Orcamentos por Ponto"
        db_table = "orcamento_por_ponto"
        ordering = ["orcamento_incerteza", "ponto_calibracao"]
        constraints = [
            models.UniqueConstraint(
                fields=["tenant", "orcamento_incerteza", "ponto_calibracao"],
                name="uq_orcamento_ponto",
            ),
        ]

    def __str__(self) -> str:
        return f"OrcamentoPorPonto p={self.ponto_calibracao} U={self.U_expandida_no_ponto}"


# =============================================================
# PadraoUsado (snapshot ADR-0040 + cl. 6.5 rastreabilidade SI)
# =============================================================

VINCULACAO_SI_TIPO_CHOICES = [
    ("BIPM_DIRETO", "BIPM direto"),
    ("INMETRO", "INMETRO (laboratorio nacional)"),
    ("RBC", "RBC (laboratorio acreditado)"),
    ("NMI_ESTRANGEIRO", "NMI estrangeiro (NIST, PTB, NPL, ...)"),
    ("MRC_NIST_PTB_NPL", "Material de Referencia Certificado"),
    ("INTERNO_DECLARADO", "Interno declarado (proibido em RBC — INV-CAL-RAST-002)"),
]


class PadraoUsado(models.Model):
    """Snapshot de padrao metrologico usado na calibracao (ADR-0040).

    Imutavel pos-INSERT (INV-CAL-WORM-001 — trigger PG na migration).
    snapshot_lock vira true automaticamente quando calibracao.status >=
    em_revisao_1 (trigger via consumer/use case — Fase 5).
    INV-CAL-RT-COMP-001: snapshot so pode ser feito enquanto
    calibracao.status IN (recepcionada, configurada). Pos em_revisao_1
    INSERT bloqueado (trigger).
    INV-CAL-CONC-002: UNIQUE parcial (tenant, calibracao, padrao_id)
    WHERE snapshot_lock=false (ADR-0065).
    INV-CAL-RAST-002: tipo_acreditacao=RBC proibe INTERNO_DECLARADO
    (CHECK composta com Calibracao — validado em use case).
    """

    id = models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)
    tenant = models.ForeignKey(
        "tenant.Tenant",
        on_delete=models.PROTECT,
        related_name="padroes_usados",
    )
    calibracao = models.ForeignKey(
        Calibracao,
        on_delete=models.PROTECT,
        related_name="padroes_usados",
    )
    padrao_id = models.UUIDField(
        help_text=(
            "FK PadraoMetrologico (db_constraint=False — modulo "
            "padroes a criar separadamente conforme ADR-0040)."
        ),
    )
    padrao_id_hash = models.CharField(
        max_length=80,
        help_text=(
            "HashVersionado v<NN>$<base64> (ADR-0064) — protecao "
            "cross-tenant + preserva audit pos-baixa do padrao."
        ),
    )
    snapshot_padrao_json = models.JSONField(
        help_text=(
            "Snapshot imutavel: cert externo, validade, classe, valor "
            "convencional, incertezas_certificado, vinculacao SI. "
            "INV-CAL-SNAP-001 + INV-CAL-RAST-001."
        ),
    )
    snapshot_capturado_at = models.DateTimeField(
        help_text=(
            "Momento da captura — INV-CAL-RT-COMP-001 (snapshot nao "
            "retroativo). Trigger PG bloqueia INSERT quando "
            "calibracao.status NOT IN (recepcionada, configurada)."
        ),
    )
    snapshot_lock = models.BooleanField(
        default=False,
        help_text=(
            "True quando calibracao.status >= em_revisao_1 "
            "(use case seta via UPDATE). UNIQUE parcial WHERE "
            "snapshot_lock=false (INV-CAL-CONC-002)."
        ),
    )
    # §16.7 — Rastreabilidade SI estruturada (P-CAL-R9 RBC)
    vinculacao_si_tipo = models.CharField(
        max_length=20,
        choices=VINCULACAO_SI_TIPO_CHOICES,
        help_text=(
            "INV-CAL-RAST-002: tenant RBC proibe INTERNO_DECLARADO "
            "(validado em use case + CHECK composta cross-table)."
        ),
    )
    vinculacao_si_referencia_id = models.CharField(
        max_length=80,
        help_text="Ex: 'INMETRO-LAB-METROL-MASSA-CERT-2024-456'.",
    )
    cadeia_rastreabilidade_documento_id = models.UUIDField(
        null=True,
        blank=True,
        help_text="FK arquivo do cert do lab emissor (db_constraint=False).",
    )

    class Meta:
        verbose_name = "Padrao Usado"
        verbose_name_plural = "Padroes Usados"
        db_table = "padrao_usado"
        ordering = ["-snapshot_capturado_at"]
        constraints = [
            # INV-CAL-CONC-002 — UNIQUE parcial WHERE snapshot_lock=false
            models.UniqueConstraint(
                fields=["tenant", "calibracao", "padrao_id"],
                condition=models.Q(snapshot_lock=False),
                name="uq_padrao_usado_pre_lock",
            ),
        ]
        indexes = [
            models.Index(fields=["tenant", "calibracao"], name="padusu_tenant_cal_idx"),
        ]

    def __str__(self) -> str:
        return f"PadraoUsado {self.padrao_id} @ {self.snapshot_capturado_at}"


# =============================================================
# RecepcaoItemCalibracao (cl. 7.4 ISO 17025)
# =============================================================

AVALIACAO_APTIDAO_CHOICES = [
    ("APTO", "Apto (item em condicoes de calibracao)"),
    ("APTO_COM_RESSALVA", "Apto com ressalva (condicoes especiais)"),
    ("INAPTO", "Inapto (item recusado — cliente notificado)"),
]


class RecepcaoItemCalibracao(models.Model):
    """Recepcao do item para calibracao (cl. 7.4 ISO 17025).

    Imutavel pos-INSERT (INV-CAL-WORM-001). Cliente pode recusar foto
    (P-CAL-A5 advogado) — quando recusa, foto_evidencia_recusa_id NOT NULL
    apontando para ConsentimentoFotoRecusado (entidade T-CAL-NNN).
    CHECK XOR: foto_evidencia_id OR foto_evidencia_recusa_id (na migration).
    aviso_foto_texto_canonico_id REQUER OAB humana.
    """

    id = models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)
    tenant = models.ForeignKey(
        "tenant.Tenant",
        on_delete=models.PROTECT,
        related_name="recepcoes_calibracao",
    )
    calibracao = models.ForeignKey(
        Calibracao,
        on_delete=models.PROTECT,
        related_name="recepcoes",
    )
    cliente_referencia_hash = models.CharField(
        max_length=80,
        help_text="HashVersionado (ADR-0064) — preservado pos-anonimizacao.",
    )
    instrumento_recebido_em = models.DateTimeField(
        help_text="Momento da recepcao fisica.",
    )
    condicoes_recebidas_canonicalizada = models.TextField(
        help_text=(
            ">=30 chars + anti-PII INV-CAL-TXT-001 + canonicalizacao "
            "INV-DOC-CANON-001 (UTF-8 + LF + NFC + marcadores)."
        ),
    )
    condicoes_recebidas_hash = models.CharField(
        max_length=80,
        help_text="HashVersionado do texto canonicalizado (ADR-0064).",
    )
    avaliacao_aptidao = models.CharField(
        max_length=20,
        choices=AVALIACAO_APTIDAO_CHOICES,
        help_text="Avaliacao do item (cl. 7.4 — separada de analise critica de pedido cl. 7.1.1).",
    )
    motivo_inaptidao_canonicalizada = models.TextField(
        blank=True,
        default="",
        help_text=(
            "NOT NULL quando avaliacao_aptidao=INAPTO. Texto >=30 chars + "
            "anti-PII INV-CAL-TXT-001."
        ),
    )
    motivo_inaptidao_hash = models.CharField(
        max_length=80,
        blank=True,
        default="",
        help_text="HashVersionado quando INAPTO.",
    )
    fluxo_subcontratacao_id = models.UUIDField(
        null=True,
        blank=True,
        help_text="FK quando recepcao decide subcontratar (US-CAL-017).",
    )
    foto_evidencia_id = models.UUIDField(
        null=True,
        blank=True,
        help_text=(
            "FK EvidenciaFotoAtividade (db_constraint=False). NULL quando "
            "cliente recusa (foto_evidencia_recusa_id NOT NULL). EXIF "
            "stripado obrigatorio (INV-CAL-FOTO-001 + hook M4 P9)."
        ),
    )
    foto_evidencia_recusa_id = models.UUIDField(
        null=True,
        blank=True,
        help_text="FK ConsentimentoFotoRecusado (T-CAL-NNN). XOR com foto_evidencia_id.",
    )
    aviso_foto_texto_canonico_id = models.UUIDField(
        help_text=(
            "FK aviso-foto-recepcao-v1.0.md (REQUER OAB — minuta preliminar "
            "pelo agente). Texto renderizado ao cliente antes da captura."
        ),
    )
    condicoes_ambientais_id = models.ForeignKey(
        CondicoesAmbientais,
        on_delete=models.PROTECT,
        related_name="recepcoes",
        help_text="Snapshot CondicoesAmbientais no momento da recepcao.",
    )
    correlation_id = models.UUIDField(
        default=uuid.uuid4,
    )

    class Meta:
        verbose_name = "Recepcao Item Calibracao"
        verbose_name_plural = "Recepcoes Item Calibracao"
        db_table = "recepcao_item_calibracao"
        ordering = ["-instrumento_recebido_em"]
        indexes = [
            models.Index(fields=["tenant", "calibracao"], name="recep_tenant_cal_idx"),
        ]

    def __str__(self) -> str:
        return f"Recepcao calibracao={self.calibracao_id} avaliacao={self.avaliacao_aptidao}"


# =============================================================
# MedicaoControle (cl. 7.7.1 — grafico X-R/CUSUM + Western Electric)
# =============================================================

REGRA_WESTERN_ELECTRIC_CHOICES = [
    ("RULE_1_3SIGMA", "Rule 1 — 1 ponto fora de 3 sigma"),
    ("RULE_2_SEVEN_SAME_SIDE", "Rule 2 — 7 pontos seguidos mesmo lado da media"),
    ("RULE_3_TREND", "Rule 3 — tendencia crescente/decrescente 6+ pontos"),
    ("RULE_5_TWO_OF_THREE", "Rule 5 — 2 de 3 pontos > 2 sigma"),
]


class MedicaoControle(models.Model):
    """Medicao de controle de padrao (cl. 7.7.1 — garantia de validade).

    Imutavel pos-INSERT (INV-CAL-WORM-001). Job procrastinate
    `analisar_padrao_medicoes_controle` recalcula ultimas 30
    medicoes apos cada INSERT (P-CAL-R8 RBC).
    Consumer Padrao.IntercomparacaoConcluida com |z|>2 e <=3 (WARNING)
    cria PlanoAcaoProficienciaWarning automaticamente.
    """

    id = models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)
    tenant = models.ForeignKey(
        "tenant.Tenant",
        on_delete=models.PROTECT,
        related_name="medicoes_controle",
    )
    padrao_id = models.UUIDField(
        help_text="FK PadraoMetrologico (db_constraint=False).",
    )
    grandeza = models.CharField(
        max_length=50,
    )
    faixa_min = models.DecimalField(
        max_digits=20,
        decimal_places=8,
        null=True,
        blank=True,
    )
    faixa_max = models.DecimalField(
        max_digits=20,
        decimal_places=8,
        null=True,
        blank=True,
    )
    valor_medido = models.DecimalField(
        max_digits=20,
        decimal_places=8,
    )
    valor_esperado = models.DecimalField(
        max_digits=20,
        decimal_places=8,
    )
    desvio = models.DecimalField(
        max_digits=20,
        decimal_places=8,
        help_text="valor_medido - valor_esperado.",
    )
    dentro_2sigma = models.BooleanField()
    dentro_3sigma = models.BooleanField()
    escore_z = models.DecimalField(
        max_digits=5,
        decimal_places=3,
        null=True,
        blank=True,
        help_text="(P-CAL-R8) Quando padrao tem incerteza_referencia conhecida.",
    )
    regra_western_electric_violada = models.CharField(
        max_length=30,
        choices=REGRA_WESTERN_ELECTRIC_CHOICES,
        blank=True,
        default="",
        help_text=(
            "Preenchido por job `analisar_padrao_medicoes_controle` "
            "apos INSERT. Job recalcula ultimas 30 medicoes."
        ),
    )
    executor_id_hash = models.CharField(
        max_length=80,
        help_text="HashVersionado (ADR-0064).",
    )
    executado_em = models.DateTimeField()
    correlation_id = models.UUIDField(
        default=uuid.uuid4,
    )

    class Meta:
        verbose_name = "Medicao de Controle"
        verbose_name_plural = "Medicoes de Controle"
        db_table = "medicao_controle"
        ordering = ["-executado_em"]
        indexes = [
            models.Index(fields=["tenant", "padrao_id", "executado_em"], name="medctrl_pad_exec_idx"),
        ]

    def __str__(self) -> str:
        return f"MedicaoControle padrao={self.padrao_id} desvio={self.desvio}"


# =============================================================
# EventoDeCalibracao (audit WORM com hash-chain por calibracao)
# ADR-0065 + INV-CAL-AUD-001/002 + ADR-0064 HashVersionado.
# =============================================================

TIPO_EVENTO_CALIBRACAO_CHOICES = [
    ("CalibracaoRecepcionada", "Calibracao Recepcionada"),
    ("ConfiguracaoSalva", "Configuracao Salva"),
    ("LeituraRegistrada", "Leitura Registrada"),
    ("LeituraCorrigida", "Leitura Corrigida"),
    ("IncertezaCalculada", "Incerteza Calculada"),
    ("ConformidadeAvaliada", "Conformidade Avaliada"),
    ("RevisaoAprovada", "Revisao Aprovada"),
    ("RevisaoRejeitada", "Revisao Rejeitada"),
    ("SegundaConferenciaAprovada", "Segunda Conferencia Aprovada"),
    ("NCAberta", "NC Aberta"),
    ("NCResolvida", "NC Resolvida"),
    ("Aprovada", "Aprovada"),
    ("Rejeitada", "Rejeitada"),
    ("Cancelada", "Cancelada"),
    ("SubcontratadaParaLab", "Subcontratada para Lab"),
    ("RecebidaDoSubcontratado", "Recebida do Subcontratado"),
    ("EpUnacceptableImpactoCriado", "EP Unacceptable Impacto Criado"),
    ("CondicoesForaOverride", "Condicoes Fora Override (P2 Qualidade)"),
    ("ReclamacaoAberta", "Reclamacao Aberta"),
    ("ReclamacaoRespondida", "Reclamacao Respondida"),
    ("AceiteRegraDecisaoConcedido", "Aceite Regra Decisao Concedido"),
    ("OverrideRegraDecisaoCriado", "Override Regra Decisao Criado"),
    ("BackupExecutado", "Backup Metrologico Executado"),
]


class EventoDeCalibracao(models.Model):
    """Audit WORM append-only por calibracao (paralelo EventoDeOS M3).

    Hash-chain por (tenant_id, calibracao_id) serializada via
    advisory lock no use case `append_evento_calibracao` (ADR-0065
    INV-CAL-AUD-002). Sequencia local `sequencia_local BIGINT NOT NULL`
    populada por trigger BEFORE INSERT (MAX+1 dentro da calibracao).

    INV-CAL-AUD-001: payload sanitizado via
    `sanitizar_payload_evento_calibracao()` (helper unico — G2 dossie
    pre-M4). Nao persistir UUIDs crus de operador (so *_hash).
    """

    id = models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)
    tenant = models.ForeignKey(
        "tenant.Tenant",
        on_delete=models.PROTECT,
        related_name="eventos_calibracao",
    )
    calibracao = models.ForeignKey(
        Calibracao,
        on_delete=models.PROTECT,
        related_name="eventos",
    )
    sequencia_local = models.BigIntegerField(
        help_text=(
            "Sequencia 1, 2, 3 ... por (tenant_id, calibracao_id). "
            "Populado por trigger BEFORE INSERT (ADR-0065 INV-CAL-AUD-002). "
            "UNIQUE (tenant, calibracao, sequencia_local)."
        ),
    )
    tipo = models.CharField(
        max_length=40,
        choices=TIPO_EVENTO_CALIBRACAO_CHOICES,
    )
    payload_sanitizado = models.JSONField(
        help_text=(
            "Sanitizado via sanitizar_payload_evento_calibracao() — "
            "G2 dossie pre-M4 + SEC-SANITIZE-001 + INV-CAL-AUD-001."
        ),
    )
    evento_anterior_hash = models.CharField(
        max_length=80,
        blank=True,
        default="",
        help_text=(
            "Hash do evento anterior na cadeia desta calibracao. "
            "Vazio no 1o evento. Calculado via advisory lock no append."
        ),
    )
    evento_hash = models.CharField(
        max_length=80,
        help_text=(
            "HashVersionado v<NN>$<base64> (ADR-0064) — HMAC do payload + "
            "evento_anterior_hash + tenant_id + occurred_at."
        ),
    )
    correlation_id = models.UUIDField(
        default=uuid.uuid4,
    )
    causation_id = models.UUIDField(
        null=True,
        blank=True,
    )
    actor_user_id = models.UUIDField(
        help_text="Quem disparou (auditoria — UUID cru aqui ok porque pareado com hash).",
    )
    actor_user_id_hash = models.CharField(
        max_length=80,
        help_text="HashVersionado do actor (ADR-0064).",
    )
    occurred_at = models.DateTimeField(
        help_text="Momento do evento (relogio NTP-sincronizado).",
    )

    class Meta:
        verbose_name = "Evento de Calibracao"
        verbose_name_plural = "Eventos de Calibracao"
        db_table = "evento_de_calibracao"
        ordering = ["calibracao", "sequencia_local"]
        constraints = [
            models.UniqueConstraint(
                fields=["tenant", "calibracao", "sequencia_local"],
                name="uq_evento_calibracao_seq",
            ),
        ]
        indexes = [
            models.Index(
                fields=["tenant", "calibracao", "occurred_at"],
                name="evcal_tenant_cal_occ_idx",
            ),
        ]

    def __str__(self) -> str:
        return f"EventoDeCalibracao #{self.sequencia_local} {self.tipo}"


# =============================================================
# NaoConformidade (cl. 7.10 + cl. 8.7 CAPA + P-CAL-R6 RBC + P-CAL-A2 advogado)
# =============================================================

ESTADO_NC_CHOICES = [
    ("CONTIDA", "Contida"),
    ("ACAO_CORRETIVA_DEFINIDA", "Acao corretiva definida"),
    ("ACAO_EXECUTADA", "Acao executada"),
    ("EFICACIA_VERIFICADA", "Eficacia verificada"),
    ("FECHADA", "Fechada"),
    ("REABERTA", "Reaberta (volta a CONTIDA — cl. 8.7.2)"),
]

ACAO_CORRETIVA_TIPO_CHOICES = [
    ("RE_EXECUTAR", "Re-executar (calibracao do zero)"),
    ("AJUSTE_ADMINISTRATIVO", "Ajuste administrativo"),
]

DECISAO_CONTINUAR_PARAR_CHOICES = [
    ("PARAR_TRABALHO", "Parar trabalho"),
    ("CONTINUAR_COM_CONTROLE", "Continuar com controle"),
    ("A_DEFINIR", "A definir"),
]

CLIENTE_NOTIFICADO_VIA_CHOICES = [
    ("EMAIL_PORTAL", "E-mail / portal cliente"),
    ("A3_ASSINATURA", "A3 com assinatura"),
    ("TERMO_PRESENCIAL", "Termo presencial"),
]


class NaoConformidade(models.Model):
    """Nao-conformidade (cl. 7.10 + cl. 8.7 CAPA — ciclo fechado).

    Origem mutuamente exclusiva: calibracao_id OU origem_proficiencia_id
    (CHECK XOR na migration). Estado-maquina §4.2 com 6 estados +
    REABERTA volta sempre a CONTIDA (cl. 8.7.2 — NOVO-1 RBC R2).

    P-CAL-R6 RBC + cl. 7.10.1/2 (INV-CAL-NC-002/003):
    - decisao_continuar_ou_parar obrigatorio antes ACAO_EXECUTADA.
    - PARAR_TRABALHO exige cliente_notificado_em NOT NULL.

    P-CAL-A2 advogado: responsavel_acao_user_id_hash CHAR(80) sempre.
    UUID cru em campo auxiliar ≤90d (job nc-responsavel-pseudonimizacao
    zera apos prazo).
    """

    id = models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)
    tenant = models.ForeignKey(
        "tenant.Tenant",
        on_delete=models.PROTECT,
        related_name="naoconformidades",
    )
    calibracao = models.ForeignKey(
        Calibracao,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="naoconformidades",
        help_text=(
            "NULL quando NC originada de Proficiencia via "
            "AnaliseImpactoNCProficiencia (mutuamente exclusivo)."
        ),
    )
    origem_proficiencia_id = models.UUIDField(
        null=True,
        blank=True,
        help_text="FK AnaliseImpactoNCProficiencia (db_constraint=False).",
    )
    descricao_canonicalizada = models.TextField(
        help_text=(
            ">=30 chars + anti-PII INV-CAL-TXT-001 (regex saude P-CAL-A2) + "
            "INV-DOC-CANON-001."
        ),
    )
    descricao_hash = models.CharField(
        max_length=80,
        help_text="HashVersionado v<NN>$<base64> (ADR-0064).",
    )
    estado = models.CharField(
        max_length=30,
        choices=ESTADO_NC_CHOICES,
        default="CONTIDA",
    )
    causa_raiz_canonicalizada = models.TextField(
        blank=True,
        default="",
        help_text="Preenchida em ACAO_CORRETIVA_DEFINIDA.",
    )
    causa_raiz_hash = models.CharField(
        max_length=80,
        blank=True,
        default="",
    )
    acao_corretiva_descricao_hash = models.CharField(
        max_length=80,
        blank=True,
        default="",
    )
    acao_corretiva_tipo = models.CharField(
        max_length=30,
        choices=ACAO_CORRETIVA_TIPO_CHOICES,
        blank=True,
        default="",
        help_text="NOVO-2 RBC R2 — explicito sobre o tipo de acao.",
    )
    acao_executada_em = models.DateTimeField(null=True, blank=True)
    eficacia_verificada_em = models.DateTimeField(null=True, blank=True)
    eficacia_verificada_por_user_id = models.UUIDField(null=True, blank=True)
    # P-CAL-A2 — UUID cru zona quente ≤90d; hash sempre
    responsavel_acao_user_id = models.UUIDField(
        null=True,
        blank=True,
        help_text=(
            "Zona quente (≤90d). Job nc-responsavel-pseudonimizacao zera "
            "UUID apos prazo (anti-stalking pos retencao 25a)."
        ),
    )
    responsavel_acao_user_id_hash = models.CharField(
        max_length=80,
        help_text="HashVersionado (ADR-0064). Sempre presente.",
    )
    # P-CAL-R6 RBC + §16.9 — cl. 7.10.1/2
    decisao_continuar_ou_parar = models.CharField(
        max_length=30,
        choices=DECISAO_CONTINUAR_PARAR_CHOICES,
        default="A_DEFINIR",
        help_text=(
            "INV-CAL-NC-002: obrigatorio (!= A_DEFINIR) antes de "
            "transitar para ACAO_EXECUTADA."
        ),
    )
    cliente_notificado_em = models.DateTimeField(
        null=True,
        blank=True,
        help_text=(
            "INV-CAL-NC-003: NOT NULL quando decisao_continuar_ou_parar = "
            "PARAR_TRABALHO."
        ),
    )
    cliente_notificado_via = models.CharField(
        max_length=20,
        choices=CLIENTE_NOTIFICADO_VIA_CHOICES,
        blank=True,
        default="",
    )
    cliente_notificado_documento_id = models.UUIDField(null=True, blank=True)
    autorizacao_retomada_user_id = models.UUIDField(null=True, blank=True)
    autorizacao_retomada_em = models.DateTimeField(null=True, blank=True)
    correlation_id = models.UUIDField(default=uuid.uuid4)

    class Meta:
        verbose_name = "Nao-Conformidade"
        verbose_name_plural = "Nao-Conformidades"
        db_table = "nao_conformidade"
        ordering = ["-id"]
        indexes = [
            models.Index(fields=["tenant", "estado"], name="nc_tenant_estado_idx"),
            models.Index(fields=["tenant", "calibracao"], name="nc_tenant_cal_idx"),
        ]

    def __str__(self) -> str:
        return f"NaoConformidade {self.id} ({self.estado})"


# =============================================================
# AnaliseImpactoNCProficiencia (cl. 7.7.2 + P-CAL-T8 reescrito P3)
# =============================================================

STATUS_ANALISE_IMPACTO_CHOICES = [
    ("RECALL_PENDENTE_M5", "Recall pendente M5 (certificados_no_periodo NULL)"),
    ("PROCESSADO", "Processado (M5 preencheu certs_no_periodo + decisao)"),
    ("ARQUIVADO", "Arquivado"),
]


class AnaliseImpactoNCProficiencia(models.Model):
    """Analise de impacto de proficiencia UNACCEPTABLE (cl. 7.7.2).

    Reescrito em P3 (P-CAL-T8 tech-lead): em vez de armazenar array de
    certs_no_periodo, armazena janela_inicio + janela_fim. M5
    (Marco 5 certificados) preenche certificados_no_periodo via consumer
    `Calibracao.EpUnacceptableImpactoCriado` quando estiver pronto.
    """

    id = models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)
    tenant = models.ForeignKey(
        "tenant.Tenant",
        on_delete=models.PROTECT,
        related_name="analises_impacto_nc",
    )
    rodada_proficiencia_id = models.UUIDField(
        help_text="FK RodadaProficiencia (db_constraint=False).",
    )
    janela_inicio = models.DateTimeField(
        help_text=(
            "Inicio da janela (ultima PT PASSED). Se nunca PT PASSED, "
            "default = tenant.created_at (documentado em INV-CAL-NC-PT-001)."
        ),
    )
    janela_fim = models.DateTimeField(
        help_text="Fim da janela (PT atual UNACCEPTABLE).",
    )
    certificados_no_periodo = models.JSONField(
        null=True,
        blank=True,
        help_text=(
            "Preenchido em batch pelo M5 quando consumir "
            "Calibracao.EpUnacceptableImpactoCriado. NULL ate M5 processar."
        ),
    )
    gestor_qualidade_decisao = models.JSONField(
        null=True,
        blank=True,
        help_text=(
            "Array por cert: {cert_id, decisao: RECALL | SUSPENSAO | "
            "SEM_IMPACTO, justificativa_hash}. NULL ate gestor decidir."
        ),
    )
    status = models.CharField(
        max_length=30,
        choices=STATUS_ANALISE_IMPACTO_CHOICES,
        default="RECALL_PENDENTE_M5",
    )
    decidida_em = models.DateTimeField(null=True, blank=True)
    decidida_por_user_id = models.UUIDField(null=True, blank=True)
    criada_em = models.DateTimeField(auto_now_add=True)
    correlation_id = models.UUIDField(default=uuid.uuid4)

    class Meta:
        verbose_name = "Analise de Impacto NC Proficiencia"
        verbose_name_plural = "Analises de Impacto NC Proficiencia"
        db_table = "analise_impacto_nc_proficiencia"
        ordering = ["-criada_em"]
        indexes = [
            models.Index(
                fields=["tenant", "rodada_proficiencia_id"],
                name="aimpnc_tenant_rod_idx",
            ),
        ]

    def __str__(self) -> str:
        return f"AnaliseImpactoNCProficiencia {self.id} ({self.status})"


# =============================================================
# PlanoAcaoProficienciaWarning (P-CAL-R8 RBC — |z|>2 e <=3 WARNING)
# =============================================================


class PlanoAcaoProficienciaWarning(models.Model):
    """Plano de acao para resultado proficiencia WARNING (|z|>2 e <=3).

    Paralelo a AnaliseImpactoNCProficiencia mas para WARNING (nao NC
    formal). NIT-DICLA-026 rev. 15 cl. 5.4 exige documentacao + plano
    de acao proporcional ao risco. Imutavel pos-INSERT (WORM).
    """

    id = models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)
    tenant = models.ForeignKey(
        "tenant.Tenant",
        on_delete=models.PROTECT,
        related_name="planos_acao_pt_warning",
    )
    rodada_proficiencia_id = models.UUIDField(
        help_text="FK RodadaProficiencia.",
    )
    escore_z = models.DecimalField(
        max_digits=5,
        decimal_places=3,
        help_text="|z|>2 e <=3 (WARNING). |z|>3 vai pra AnaliseImpactoNCProficiencia.",
    )
    causa_investigada_canonicalizada = models.TextField(
        help_text=">=50 chars + anti-PII + INV-DOC-CANON-001.",
    )
    causa_investigada_hash = models.CharField(max_length=80)
    acao_proporcional_canonicalizada = models.TextField()
    acao_proporcional_hash = models.CharField(max_length=80)
    eficacia_futura_em = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Quando eficacia da acao sera verificada.",
    )
    responsavel_user_id_hash = models.CharField(max_length=80)
    criado_em = models.DateTimeField(auto_now_add=True)
    correlation_id = models.UUIDField(default=uuid.uuid4)

    class Meta:
        verbose_name = "Plano Acao Proficiencia WARNING"
        verbose_name_plural = "Planos Acao Proficiencia WARNING"
        db_table = "plano_acao_proficiencia_warning"
        ordering = ["-criado_em"]
        indexes = [
            models.Index(
                fields=["tenant", "rodada_proficiencia_id"],
                name="paw_tenant_rod_idx",
            ),
        ]

    def __str__(self) -> str:
        return f"PlanoAcaoProficienciaWarning z={self.escore_z}"


class LaboratorioSubcontratado(models.Model):
    """Cadastro de laboratorio externo subcontratado (cl. 6.6 + US-CAL-017).

    Padrao C — soft-delete configuracao (`deletado_em`). PII Zona B
    (razao_social_hash + cnpj_hash + contatos PF hashed). Avaliacao
    periodica obrigatoria (P-CAL-R5 RBC cl. 6.6.2) — 1:N
    AvaliacaoPeriodicaSubcontratado.

    Quando `pais != 'BR'`: dpa_clausulas_internacionais_id NOT NULL
    (P-CAL-A1 advogado — transferencia internacional LGPD art. 33).
    """

    id = models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)
    tenant = models.ForeignKey(
        "tenant.Tenant",
        on_delete=models.PROTECT,
        related_name="laboratorios_subcontratados",
    )
    # PII Zona B (razao social + CNPJ + contatos PF hashed)
    razao_social_hash = models.CharField(
        max_length=80,
        help_text="HashVersionado v<NN>$<base64> (ADR-0064).",
    )
    razao_social_key_id = models.CharField(
        max_length=40,
        help_text="ID chave KMS p/ razao social cleartext (off-band).",
    )
    cnpj_hash = models.CharField(max_length=80)
    cnpj_key_id = models.CharField(max_length=40)
    credenciamento_atual = models.CharField(
        max_length=50,
        help_text="Ex: 'CGCRE-CAL-0123' (codigo acreditacao CGCRE).",
    )
    acreditacoes_vigentes = models.JSONField(
        help_text=(
            "Array [{grandeza, faixa_min, faixa_max, validade}]. "
            "Snapshot consultado em subcontratarCalibracao (US-CAL-017)."
        ),
    )
    contato_comercial_hash = models.CharField(max_length=80)
    contato_tecnico_hash = models.CharField(max_length=80)
    dpa_versao = models.CharField(
        max_length=20,
        help_text="Versao DPA assinada (cl. 4.7 ISO 17025).",
    )
    # §16.10 — campos novos P-CAL-R5
    criterio_selecao_documento_id = models.UUIDField(
        null=True,
        blank=True,
        help_text="FK criterio-selecao-subcontratado-v1.0.md (REQUER OAB).",
    )
    ultima_avaliacao_periodica_em = models.DateTimeField(null=True, blank=True)
    proxima_avaliacao_periodica_em = models.DateTimeField(
        help_text="Default vigencia_inicio + 12 meses (cl. 6.6.2).",
    )
    score_avaliacao_atual = models.DecimalField(
        max_digits=3,
        decimal_places=1,
        null=True,
        blank=True,
        help_text="0-10 (avaliacao periodica).",
    )
    avaliado_por_user_id = models.UUIDField(null=True, blank=True)
    pais = models.CharField(
        max_length=2,
        default="BR",
        help_text="ISO 3166-1 alpha-2 (P-CAL-A1 transferencia internacional).",
    )
    dpa_clausulas_internacionais_id = models.UUIDField(
        null=True,
        blank=True,
        help_text="NOT NULL quando pais != 'BR' (CHECK na migration).",
    )
    # ADR-0030 — vigencia canonica
    vigencia_inicio = models.DateTimeField()
    vigencia_fim = models.DateTimeField(null=True, blank=True)
    # ADR-0031 Padrao C — soft-delete configuracao
    deletado_em = models.DateTimeField(null=True, blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    correlation_id = models.UUIDField(default=uuid.uuid4)

    class Meta:
        verbose_name = "Laboratorio Subcontratado"
        verbose_name_plural = "Laboratorios Subcontratados"
        db_table = "laboratorio_subcontratado"
        ordering = ["-criado_em"]
        indexes = [
            models.Index(
                fields=["tenant", "cnpj_hash"],
                name="labsub_tenant_cnpj_idx",
            ),
            models.Index(
                fields=["tenant", "proxima_avaliacao_periodica_em"],
                name="labsub_tenant_proxav_idx",
            ),
        ]

    def __str__(self) -> str:
        return f"LaboratorioSubcontratado {self.credenciamento_atual}"


class AceiteSubcontratacao(models.Model):
    """Aceite explicito do cliente para subcontratar cl. 6.6 (US-CAL-017).

    Imutavel pos-INSERT (WORM). texto_canonico_id REQUER OAB
    (`aceite-subcontratacao-v1.0.md`). Assinatura touch (biometria) ou
    A3 (ICP-Brasil) — quando touch, declaracao_aceite_touch_alto_risco_id
    NOT NULL (P-CAL-A6 advogado).

    Trigger pos-INSERT bloqueia UPDATE/DELETE
    (INV-CAL-WORM-001 + INV-CAL-SUBC-001).
    """

    id = models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)
    tenant = models.ForeignKey(
        "tenant.Tenant",
        on_delete=models.PROTECT,
        related_name="aceites_subcontratacao",
    )
    calibracao = models.ForeignKey(
        Calibracao,
        on_delete=models.PROTECT,
        related_name="aceites_subcontratacao",
    )
    cliente_referencia_hash = models.CharField(
        max_length=80,
        help_text=(
            "HashVersionado do cliente_id (ADR-0064 + ADR-0032 — preserva "
            "evidencia pos-anonimizacao)."
        ),
    )
    texto_canonico_id = models.UUIDField(
        help_text=(
            "FK aceite-subcontratacao-v1.0.md (REQUER OAB). Texto exibido "
            "ao cliente — INV-DOC-CANON-001."
        ),
    )
    texto_hash = models.CharField(
        max_length=80,
        help_text="SHA-256 do texto exibido (HashVersionado).",
    )
    assinatura_modo = models.CharField(
        max_length=10,
        choices=ASSINATURA_MODO_CHOICES,
        help_text="TOUCH ou A3. §16.11.",
    )
    assinatura_payload_encrypted = models.BinaryField(
        null=True,
        blank=True,
        help_text=(
            "Touch: payload cifrado com BIOMETRIA_KEY_<tenant> "
            "(INV-OS-ACEITE-BIO-001 herdado). A3: PKCS#7."
        ),
    )
    declaracao_aceite_touch_alto_risco_id = models.UUIDField(
        null=True,
        blank=True,
        help_text=(
            "NOT NULL quando assinatura_modo='TOUCH' (texto canonico extra "
            "P-CAL-A6 advogado). CHECK na migration."
        ),
    )
    consentimento_contato_id = models.UUIDField(
        null=True,
        blank=True,
        help_text=(
            "FK ConsentimentoContatoTecnicoCliente — NOT NULL quando contato PF "
            "PJ-empregado assina (P-CAL-A6)."
        ),
    )
    motivo_subcontratacao_canonicalizado = models.TextField(
        help_text=">=30 chars + anti-PII + INV-DOC-CANON-001.",
    )
    motivo_hash = models.CharField(max_length=80)
    ip_hash = models.CharField(
        max_length=80,
        help_text=(
            "HashVersionado do IP cliente — INV-CAL-SUBC-001: IP nunca "
            "persiste cleartext."
        ),
    )
    concedido_em = models.DateTimeField()
    correlation_id = models.UUIDField(default=uuid.uuid4)

    class Meta:
        verbose_name = "Aceite Subcontratacao"
        verbose_name_plural = "Aceites Subcontratacao"
        db_table = "aceite_subcontratacao"
        ordering = ["-concedido_em"]
        indexes = [
            models.Index(
                fields=["tenant", "calibracao"],
                name="acsub_tenant_cal_idx",
            ),
        ]

    def __str__(self) -> str:
        return f"AceiteSubcontratacao {self.id}"


class AvaliacaoPeriodicaSubcontratado(models.Model):
    """Avaliacao periodica anual obrigatoria de subcontratado (P-CAL-R5 RBC).

    1:N de LaboratorioSubcontratado (cl. 6.6.2 — avaliacao da efetividade
    do subcontratado). Imutavel pos-INSERT (WORM). Job
    `verificar_avaliacao_subcontratado_vencendo` consome essa tabela
    para alerta P2 30 dias antes de proxima_avaliacao_periodica_em.
    """

    id = models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)
    tenant = models.ForeignKey(
        "tenant.Tenant",
        on_delete=models.PROTECT,
        related_name="avaliacoes_subcontratado",
    )
    laboratorio = models.ForeignKey(
        LaboratorioSubcontratado,
        on_delete=models.PROTECT,
        related_name="avaliacoes_periodicas",
    )
    avaliado_em = models.DateTimeField()
    avaliado_por_user_id_hash = models.CharField(
        max_length=80,
        help_text="HashVersionado (ADR-0064) — gerente qualidade.",
    )
    score = models.DecimalField(
        max_digits=3,
        decimal_places=1,
        help_text="0-10 (criterios cl. 6.6.2).",
    )
    criterios_aplicados_json = models.JSONField(
        help_text=(
            "Snapshot do criterio-selecao-subcontratado-v1.0.md com "
            "marcacoes [aprovado|pendente|nao_atende]."
        ),
    )
    parecer_canonicalizado = models.TextField(
        help_text=">=100 chars + anti-PII + INV-DOC-CANON-001.",
    )
    parecer_hash = models.CharField(max_length=80)
    decisao = models.CharField(
        max_length=20,
        choices=[
            ("MANTER", "Manter (subcontratado aprovado)"),
            ("ACOMPANHAMENTO", "Manter com acompanhamento (score 6-8)"),
            ("DESCREDENCIAR", "Descredenciar (score <6 ou nc grave)"),
        ],
    )
    proxima_avaliacao_em = models.DateTimeField(
        help_text="Default = avaliado_em + 12 meses (cl. 6.6.2).",
    )
    correlation_id = models.UUIDField(default=uuid.uuid4)
    criada_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Avaliacao Periodica Subcontratado"
        verbose_name_plural = "Avaliacoes Periodicas Subcontratado"
        db_table = "avaliacao_periodica_subcontratado"
        ordering = ["-avaliado_em"]
        indexes = [
            models.Index(
                fields=["tenant", "laboratorio"],
                name="avalsub_tenant_lab_idx",
            ),
        ]

    def __str__(self) -> str:
        return f"AvaliacaoPeriodicaSubcontratado {self.score}"


class AceiteRegraDecisao(models.Model):
    """Aceite cliente sobre regra de decisao por calibracao (ADR-0024 rev.).

    Cl. 7.1.3 + ADR-0024 revisado §16.3 — cliente acorda explicitamente
    qual regra de decisao (ACEITACAO_SIMPLES / BANDA_GUARDA_30 /
    RISCO_COMPARTILHADO) sera aplicada. Imutavel pos-INSERT (WORM).

    P-CAL-R3 RBC + P-CAL-A3 advogado — sem aceite, calibracao nao avanca
    para configurada (INV-CAL-DEC-006).
    """

    id = models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)
    tenant = models.ForeignKey(
        "tenant.Tenant",
        on_delete=models.PROTECT,
        related_name="aceites_regra_decisao",
    )
    calibracao = models.ForeignKey(
        Calibracao,
        on_delete=models.PROTECT,
        related_name="aceites_regra_decisao",
    )
    cliente_referencia_hash = models.CharField(
        max_length=80,
        help_text="HashVersionado cliente_id (ADR-0064 + ADR-0032).",
    )
    regra_decisao_escolhida = models.CharField(
        max_length=25,
        choices=REGRA_DECISAO_CHOICES,
    )
    escopo_aplicacao = models.CharField(
        max_length=25,
        choices=[
            ("CALIBRACAO_UNICA", "Aplica-se a esta calibracao especifica"),
            ("CONTRATO_GUARDA_CHUVA", "Aplica-se ao contrato vigente (guarda-chuva)"),
        ],
        default="CALIBRACAO_UNICA",
    )
    nivel_confianca_acordado = models.DecimalField(
        max_digits=5,
        decimal_places=4,
        default="0.9545",
        help_text="Default 95.45% (k=2). Cliente pode pedir outro nivel.",
    )
    texto_canonico_id = models.UUIDField(
        help_text="FK aceite-regra-decisao-v1.0.md (REQUER OAB).",
    )
    texto_hash = models.CharField(max_length=80)
    assinatura_modo = models.CharField(
        max_length=10,
        choices=ASSINATURA_MODO_CHOICES,
    )
    assinatura_payload_encrypted = models.BinaryField(null=True, blank=True)
    ip_hash = models.CharField(max_length=80)
    concedido_em = models.DateTimeField()
    correlation_id = models.UUIDField(default=uuid.uuid4)

    class Meta:
        verbose_name = "Aceite Regra Decisao"
        verbose_name_plural = "Aceites Regra Decisao"
        db_table = "aceite_regra_decisao"
        ordering = ["-concedido_em"]
        indexes = [
            models.Index(
                fields=["tenant", "calibracao"],
                name="aceiterd_tenant_cal_idx",
            ),
        ]

    def __str__(self) -> str:
        return f"AceiteRegraDecisao {self.regra_decisao_escolhida}"
