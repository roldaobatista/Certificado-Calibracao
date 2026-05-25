"""Marco 3 — modelos Django operacao/os (T-OS-001 minimal).

Estado inicial:
- OS (ordens_servico.OS) — entidade raiz; sequence global os_numero_seq_global +
  UNIQUE(tenant, numero_os) (ADR-0056 + INV-OS-NUM-001).
- AtividadeDaOS (ordens_servico.AtividadeDaOS) — N por OS (ADR-0023).

Demais entidades (Aceite, Consentimento, EvidenciaFoto, Dispensa,
Evento, Checklist, TipoAtividadeConfig, SLA, NaoConformidade) entram
em migrations subsequentes (T-OS-004..011).

RLS policies + triggers + unique partial index = T-OS-002+T-OS-003.
"""

from __future__ import annotations

import uuid

from django.db import models


class OS(models.Model):
    """Ordem de Servico — container comercial/financeiro/atendimento (ADR-0023)."""

    id = models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)
    tenant = models.ForeignKey(
        "tenant.Tenant",
        on_delete=models.PROTECT,
        related_name="ordens_servico",
    )
    numero_os = models.BigIntegerField(
        help_text=(
            "Gerado por sequence global os_numero_seq_global no DEFAULT da migration "
            "(ADR-0056 + INV-OS-NUM-001). UNIQUE(tenant, numero_os). Buracos por rollback aceitos."
        ),
    )
    cliente = models.ForeignKey(
        "clientes.Cliente",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        db_constraint=False,
        related_name="ordens_servico",
        help_text="Pode ficar NULL pos-anonimizacao (ADR-0032 + INV-OS-ANON-001).",
    )
    cliente_referencia_hash = models.CharField(
        max_length=64,
        help_text="HMAC-SHA256 do cliente_id original — preserva audit pos-anonimizacao (ADR-0032).",
    )
    cliente_key_id = models.CharField(max_length=40, help_text="KMS key id usada no hash.")
    equipamento = models.ForeignKey(
        "equipamentos.Equipamento",
        on_delete=models.PROTECT,
        related_name="ordens_servico",
        help_text="INV-OS-EQP-001: equipamento BAIXADO/DESCARTADO bloqueia abertura.",
    )
    orcamento_origem_id = models.UUIDField(
        null=True,
        blank=True,
        help_text="FK orcamento (db_constraint=False ate modulo Orcamentos chegar). NULL em OS avulsa (US-OS-015).",
    )
    os_origem = models.ForeignKey(
        "self",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="reaberturas",
        help_text="FK reabertura (US-OS-006).",
    )
    sucessao_societaria_id = models.UUIDField(
        null=True,
        blank=True,
        help_text="FK SucessaoSocietaria (a criar GATE-OS-SUCESSAO-EVIDENCIA Wave A) em reabertura cross-cliente M&A (INV-OS-SUC-001).",
    )
    estado = models.CharField(
        max_length=20,
        default="rascunho",
        choices=[
            ("rascunho", "Rascunho"),
            ("agendada", "Agendada"),
            ("em_execucao", "Em execucao"),
            ("concluida", "Concluida"),
            ("cancelada", "Cancelada"),
            ("faturada", "Faturada"),
            ("paga", "Paga"),
        ],
        help_text="Estado COMPUTADO a partir das atividades (INV-OS-ATIV-001).",
    )
    tipo_predominante = models.CharField(
        max_length=30,
        blank=True,
        default="",
        help_text="Calculado em transicao para CONCLUIDA. Regra de empate: calibracao sempre vence.",
    )
    nao_conformidade_global = models.BooleanField(
        default=False,
        help_text="True quando >=1 AtividadeDaOS em NAO_CONFORME.",
    )
    valor_total = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0,
        help_text="Snapshot inicial vindo do orcamento.",
    )
    valor_total_atualizado = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0,
        help_text="Recalculado a cada cancelamento parcial — ADR-0042 + INV-OS-FAT-001.",
    )
    analise_critica_id = models.UUIDField(
        null=True,
        blank=True,
        help_text="cl. 7.1 ISO 17025 (P-OS-R2 + INV-OS-ANAL-001). NOT NULL em produtiva; nullable agora p/ migration; T-OS-046 cria validacao 412 OrcamentoSemAnaliseCritica.",
    )
    analise_critica_snapshot_hash = models.CharField(
        max_length=64,
        blank=True,
        default="",
        help_text="Snapshot probatorio do momento da abertura (INV-DOC-CANON-001).",
    )
    regra_decisao_acordada = models.CharField(
        max_length=20,
        blank=True,
        default="",
        help_text="Snapshot cl. 7.1.3 (ADR-0024). Overridable por cliente em M4 calibracao.",
    )
    equipamento_recebimento_id = models.UUIDField(
        null=True,
        blank=True,
        help_text=(
            "FK EquipamentoRecebimento (db_constraint=False — modulo equipamentos M2 traz). "
            "cl. 7.5 ISO 17025 (P-OS-R4). NULL em OS de campo; NOT NULL em OS de bancada (T-OS-047)."
        ),
    )
    criada_em = models.DateTimeField(auto_now_add=True, db_index=True)
    atualizada_em = models.DateTimeField(auto_now=True)
    criada_por_user_id = models.UUIDField(
        null=True,
        blank=True,
        help_text="Quem abriu (auditoria + cl. 7.1 capacidade_tecnica_confirmada_por em US-OS-015).",
    )

    class Meta:
        app_label = "ordens_servico"
        db_table = "ordens_servico"
        verbose_name = "Ordem de Servico"
        verbose_name_plural = "Ordens de Servico"
        ordering = ["-criada_em"]
        constraints = [
            models.UniqueConstraint(
                fields=["tenant", "numero_os"],
                name="uq_ordens_servico_numero_por_tenant",
            ),
        ]
        indexes = [
            models.Index(fields=["tenant", "estado", "criada_em"], name="os_tenant_est_cri_idx"),
            models.Index(fields=["tenant", "cliente"], name="os_tenant_cliente_idx"),
            models.Index(fields=["tenant", "equipamento"], name="os_tenant_equip_idx"),
        ]

    def __str__(self) -> str:
        return f"OS-{self.numero_os} ({self.estado})"


class AtividadeDaOS(models.Model):
    """Atividade individual dentro de OS (ADR-0023). 1 OS contem N atividades."""

    id = models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)
    tenant = models.ForeignKey(
        "tenant.Tenant",
        on_delete=models.PROTECT,
        related_name="atividades_os",
        help_text="Herda da OS (INV-OS-ATIV-002 cross-tenant proibido).",
    )
    os = models.ForeignKey(
        OS,
        on_delete=models.PROTECT,
        related_name="atividades",
    )
    tipo = models.CharField(
        max_length=30,
        choices=[
            ("calibracao", "Calibracao"),
            ("manutencao_corretiva", "Manutencao corretiva"),
            ("manutencao_preventiva", "Manutencao preventiva"),
            ("instalacao", "Instalacao"),
            ("verificacao_inmetro", "Verificacao INMETRO"),
            ("vistoria", "Vistoria"),
        ],
        help_text="Enum fechado de 6 valores (INV-OS-ATIV-003).",
    )
    sequencia = models.IntegerField(help_text="Ordem de execucao; gate sequencia ADR-0041.")
    estado = models.CharField(
        max_length=20,
        default="pendente",
        choices=[
            ("pendente", "Pendente"),
            ("agendada", "Agendada"),
            ("em_execucao", "Em execucao"),
            ("concluida", "Concluida"),
            ("nao_conforme", "Nao conforme"),
            ("cancelada", "Cancelada"),
        ],
    )
    tecnico_executor_id = models.UUIDField(
        null=True,
        blank=True,
        help_text="FK user.id (db_constraint=False). Executor designado eh unico autorizado (INV-OS-ATIV-005).",
    )
    agendada_para = models.DateTimeField(null=True, blank=True)
    iniciada_em = models.DateTimeField(null=True, blank=True)
    concluida_em = models.DateTimeField(null=True, blank=True)
    valor_unitario_snapshot = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0,
        help_text="Snapshot do preco no momento (US-OS-015 + INV-CLI-PRICE-001).",
    )
    link_modulo_tecnico_id = models.UUIDField(
        null=True,
        blank=True,
        help_text=(
            "FK reversa para Calibracao/Manutencao (db_constraint=False). "
            "Preenchido em <=janela_tenant via INV-OS-CAL-LINK-001 (default 72h alerta / 15 dias NC RBC perfil A)."
        ),
    )
    geo_lat = models.FloatField(
        null=True,
        blank=True,
        help_text="Opt-in (RAT-07 + INV-OS-GEO-001). TTL 5a pos-conclusao via job os-geo-truncamento (P-OS-A2).",
    )
    geo_long = models.FloatField(null=True, blank=True)
    geo_municipio_hash = models.CharField(
        max_length=64,
        blank=True,
        default="",
        help_text="Hash do municipio (preservado mesmo pos-TTL — INV-OS-GEO-001 item d).",
    )
    # ===== INV-OS-CONC-001 (ADR-0041) - desnormalizacao pra unique partial index =====
    # Copiados via trigger BEFORE INSERT a partir de OS.equipamento_id e
    # TipoAtividadeConfig.tipo_bloqueia_concorrencia. NUNCA editar manualmente -
    # sao snapshot imutavel pos-INSERT.
    equipamento_id_desnormalizado = models.UUIDField(
        null=True,
        blank=True,
        help_text=(
            "Desnormalizado de OS.equipamento_id via trigger BEFORE INSERT. "
            "Existe em atividade_da_os porque o unique partial index "
            "INV-OS-CONC-001 exige todas as colunas na mesma tabela."
        ),
    )
    tipo_bloqueia_concorrencia = models.BooleanField(
        default=False,
        help_text=(
            "Desnormalizado de TipoAtividadeConfig.tipo_bloqueia_concorrencia "
            "via trigger BEFORE INSERT. True = entra no unique partial index "
            "idx_atividade_em_execucao_por_equip (INV-OS-CONC-001 + ADR-0041)."
        ),
    )
    # ===== ADR-0063 Opcao A lazy (cross-marco M3->M4 calibracao) =====
    # Plugado por Marco 4 quando tipo='calibracao': predicate
    # rt_competencia_cobre passa a verificar a grandeza efetiva. Em
    # Marco 3, fica vazio (fail-open controlado pelos 3 use cases que
    # carregam executor — atribuir_tecnico/iniciar_atividade/transferir_tecnico).
    # Bloqueio efetivo automatico quando preenchido por Calibracao.
    grandeza = models.CharField(
        max_length=50,
        blank=True,
        default="",
        help_text=(
            "ADR-0063 Opcao A lazy — preenchido quando tipo='calibracao' por "
            "Calibracao.grandeza (Marco 4). Vazio em Marco 3 (fail-open). "
            "Predicate rt_competencia_cobre(grandeza) consulta este campo."
        ),
    )

    class Meta:
        app_label = "ordens_servico"
        db_table = "atividade_da_os"
        verbose_name = "Atividade da OS"
        verbose_name_plural = "Atividades da OS"
        ordering = ["os", "sequencia"]
        indexes = [
            models.Index(fields=["tenant", "os", "sequencia"], name="atv_tenant_os_seq_idx"),
            models.Index(
                fields=["tenant", "tecnico_executor_id", "estado"],
                name="atv_tenant_tec_est_idx",
            ),
        ]

    def __str__(self) -> str:
        return f"AtividadeDaOS({self.tipo}#{self.sequencia} {self.estado})"


class TipoAtividadeConfig(models.Model):
    """Configuracao por tipo de atividade (ADR-0023 + ADR-0041 + ADR-0024).

    Tabela seed com 6 tipos fixos (INV-OS-ATIV-003). Flags governam
    comportamento de validacao:

    - `requer_competencia_rt`: predicate `rt_competencia_cobre` exigido
      (calibracao, verificacao_inmetro). Origem: INV-CAL-RT-001 + cl. 6.2.
    - `tipo_bloqueia_concorrencia`: matriz tipo x tipo ADR-0041. True =
      atividade entra na unique partial index `equipamento_em_execucao`.
    - `executa_em_campo`: tecnico vai ate o cliente (true) ou bancada
      no laboratorio (false). Governa US-OS-001-8 (equipamento_recebimento
      so obrigatorio em OS de bancada).
    - `prazo_link_calibracao_alerta_h`: janela INV-OS-CAL-LINK-001 antes
      do alerta P2 (default RBC perfil A: 72h; perfis B/C/D: 7 dias =
      168h). NULL = nao se aplica (so tipo=calibracao).
    - `prazo_link_calibracao_nc_dias_uteis`: dias uteis ate NC automatica
      por link faltando (default A: 15 dias; B/C/D: 30 dias). NULL =
      nao se aplica.
    """

    tenant = models.ForeignKey(
        "tenant.Tenant",
        on_delete=models.PROTECT,
        related_name="tipos_atividade_config",
        help_text="Cada tenant tem 6 entradas. Seed inicial via data migration.",  # mantém alinhado com migration 0003
    )
    tipo = models.CharField(
        max_length=30,
        choices=[
            ("calibracao", "Calibracao"),
            ("manutencao_corretiva", "Manutencao corretiva"),
            ("manutencao_preventiva", "Manutencao preventiva"),
            ("instalacao", "Instalacao"),
            ("verificacao_inmetro", "Verificacao INMETRO"),
            ("vistoria", "Vistoria"),
        ],
    )
    requer_competencia_rt = models.BooleanField(
        default=False,
        help_text="Predicate rt_competencia_cobre exigido (INV-CAL-RT-001 + cl. 6.2).",
    )
    tipo_bloqueia_concorrencia = models.BooleanField(
        default=False,
        help_text="Matriz ADR-0041. True = entra na unique partial index INV-OS-CONC-001.",
    )
    executa_em_campo = models.BooleanField(
        default=False,
        help_text="True = tecnico vai ao cliente; False = bancada laboratorio.",
    )
    prazo_link_calibracao_alerta_h = models.IntegerField(
        null=True,
        blank=True,
        help_text="Watchdog os-calibracao-link: horas ate alerta P2. NULL se tipo != calibracao.",
    )
    prazo_link_calibracao_nc_dias_uteis = models.IntegerField(
        null=True,
        blank=True,
        help_text="Watchdog os-calibracao-link: dias uteis ate NC automatica.",
    )
    deletado_em = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Padrao C soft-delete (ADR-0031). UNIQUE parcial WHERE deletado_em IS NULL.",
    )
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = "ordens_servico"
        db_table = "tipo_atividade_config"
        verbose_name = "Configuracao de tipo de atividade"
        verbose_name_plural = "Configuracoes de tipos de atividade"
        ordering = ["tenant", "tipo"]
        constraints = [
            models.UniqueConstraint(
                fields=("tenant", "tipo"),
                condition=models.Q(deletado_em__isnull=True),
                name="uq_tipo_atividade_config_por_tenant_ativos",
            ),
        ]

    def __str__(self) -> str:
        return f"TipoAtividadeConfig({self.tipo} tenant={self.tenant_id})"


class ConsentimentoBiometriaTouch(models.Model):
    """LGPD art. 11 II "a" (P-OS-A1 + INV-OS-CONSBIO-001).

    Entidade imutavel (Padrao B ADR-0031). FK 1:1 obrigatoria de
    AceiteAtividade quando captura biometria touch. Sem o consentimento
    pre-gravado, AceiteAtividade nao pode ser criada -> 412
    ConsentimentoBiometriaAusente.

    Texto canonico do consentimento mora em
    `docs/conformidade/comum/termos/consentimento-biometria-touch.md`
    (REQUER OAB — GATE-OS-CONSBIO-TEXTO-OAB pre-1o tenant externo).

    Trigger PG bloqueia UPDATE/DELETE pos-INSERT (audit-immutability).
    """

    id = models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)
    tenant = models.ForeignKey(
        "tenant.Tenant",
        on_delete=models.PROTECT,
        related_name="consentimentos_biometria_touch",
    )
    atividade = models.ForeignKey(
        AtividadeDaOS,
        on_delete=models.PROTECT,
        related_name="consentimentos_biometria",
        help_text="Atividade que vai gerar o AceiteAtividade (FK reversa 1:1).",
    )
    cliente_referencia_hash = models.CharField(
        max_length=64,
        help_text="HMAC-SHA256 do cliente_id original (ADR-0032).",
    )
    cliente_key_id = models.CharField(max_length=40)
    texto_canonico_id = models.UUIDField(
        help_text=(
            "FK -> docs/conformidade/comum/termos/consentimento-biometria-touch.md "
            "(db_constraint=False ate modulo termos existir). REQUER OAB."
        ),
    )
    texto_hash = models.CharField(
        max_length=64,
        help_text="SHA-256 do texto canonico exibido (INV-DOC-CANON-001).",
    )
    versao_politica = models.CharField(
        max_length=20,
        help_text="Semver da Politica de Privacidade vigente no momento.",
    )
    concedido_em = models.DateTimeField(
        help_text="Timestamp do toque no botao 'concordo e assino' (SEPARADO de 'concluir').",
    )
    tela_renderizada_evidencia = models.BinaryField(
        null=True,
        blank=True,
        help_text="Screenshot opcional da tela exibida (RIPD pode exigir).",
    )
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = "ordens_servico"
        db_table = "consentimento_biometria_touch"
        verbose_name = "Consentimento de biometria touch"
        verbose_name_plural = "Consentimentos de biometria touch"
        ordering = ["-criado_em"]
        constraints = [
            # 1 consentimento ativo por atividade (FK 1:1 enforced).
            models.UniqueConstraint(
                fields=("atividade",),
                name="uq_consentimento_biometria_por_atividade",
            ),
        ]
        indexes = [
            models.Index(fields=["tenant", "atividade"], name="cbio_tenant_atv_idx"),
        ]

    def __str__(self) -> str:
        return f"ConsentimentoBiometriaTouch(atv={self.atividade_id} v={self.versao_politica})"


class AceiteAtividade(models.Model):
    """Aceite do cliente para uma AtividadeDaOS (US-OS-004 + US-OS-013).

    Entidade imutavel Padrao B (ADR-0031). Quando captura biometria
    touch, exige `consentimento_id` NOT NULL (INV-OS-CONSBIO-001 + LGPD
    art. 11 II "a"). Texto canonicalizado (INV-DOC-CANON-001 + ADR-0029).
    Biometria cifrada com `BIOMETRIA_KEY_<tenant_id>` (INV-OS-ACEITE-BIO-001).

    Trigger PG bloqueia UPDATE/DELETE pos-INSERT — registro probatorio
    25a WORM equivalente.
    """

    id = models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)
    tenant = models.ForeignKey(
        "tenant.Tenant",
        on_delete=models.PROTECT,
        related_name="aceites_atividade",
    )
    atividade = models.ForeignKey(
        AtividadeDaOS,
        on_delete=models.PROTECT,
        related_name="aceites",
    )
    consentimento = models.ForeignKey(
        ConsentimentoBiometriaTouch,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="aceite",
        help_text=(
            "FK 1:1 NOT NULL quando ha biometria touch (INV-OS-CONSBIO-001). "
            "NULL apenas em aceites SEM biometria (cenario US-OS-013 dispensa)."
        ),
    )
    cliente_referencia_hash = models.CharField(
        max_length=64,
        help_text="HMAC-SHA256 do cliente_id original (ADR-0032).",
    )
    cliente_key_id = models.CharField(max_length=40)
    texto_canonicalizado = models.TextField(
        help_text="UTF-8 sem BOM + LF + NFC + marcadores <<<CORPO INICIO/FIM>>> (ADR-0029).",
    )
    texto_hash = models.CharField(
        max_length=64,
        help_text="SHA-256 do texto pos-canonicalizacao (INV-DOC-CANON-001).",
    )
    biometria_payload_encrypted = models.BinaryField(
        null=True,
        blank=True,
        help_text=(
            "Cifrado com BIOMETRIA_KEY_<tenant_id> (INV-OS-ACEITE-BIO-001). "
            "NULL em aceites SEM biometria (caso de dispensa US-OS-013)."
        ),
    )
    biometria_key_id = models.CharField(
        max_length=40,
        blank=True,
        default="",
        help_text="Id da chave KMS dedicada por tenant. Vazio se sem biometria.",
    )
    coletado_em = models.DateTimeField(help_text="Timestamp servidor da coleta.")
    geo_lat = models.FloatField(
        null=True,
        blank=True,
        help_text="Opt-in (RAT-07 + INV-OS-GEO-001). Mesma precisao limitada da atividade.",
    )
    geo_long = models.FloatField(null=True, blank=True)
    geo_municipio_hash = models.CharField(max_length=64, blank=True, default="")
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = "ordens_servico"
        db_table = "aceite_atividade"
        verbose_name = "Aceite de atividade"
        verbose_name_plural = "Aceites de atividade"
        ordering = ["-criado_em"]
        constraints = [
            # Cada atividade tem no maximo 1 aceite ativo (INV-OS-ATIV-001).
            models.UniqueConstraint(
                fields=("atividade",),
                name="uq_aceite_por_atividade",
            ),
        ]
        indexes = [
            models.Index(fields=["tenant", "atividade"], name="aceite_tenant_atv_idx"),
        ]

    def __str__(self) -> str:
        bio = "bio" if self.biometria_payload_encrypted else "sem-bio"
        return f"AceiteAtividade({self.atividade_id} {bio})"


class EvidenciaFotoAtividade(models.Model):
    """Foto de evidencia da AtividadeDaOS (P-OS-T5 + INV-OS-SYNC-001).

    Padrao B append-only via trigger:
    - INSERT permitido em qualquer estado da atividade (inclusive
      terminal — gera EventoDeOS tipo='foto_evidencia_tardia' em T-OS-008).
    - UPDATE bloqueado exceto setar `revogado_em` (LGPD art. 18 — face
      cliente). UPDATE de outro campo -> RAISE EXCEPTION.
    - DELETE bloqueado.

    INV-OS-SYNC-001 (reescrito P-OS-T5): foto enviada nunca eh descartada
    no merge LWW; entra na galeria com `vencedora_lww=False` se necessario
    (LWW so para campos escalares da atividade).
    """

    TIPO_CHOICES = [
        ("checklist_item", "Item de checklist"),
        ("conclusao", "Conclusao"),
        ("nc", "Nao conformidade"),
        ("no_show", "No-show"),
        ("recusa_aceite", "Recusa de aceite"),
    ]

    id = models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)
    tenant = models.ForeignKey(
        "tenant.Tenant",
        on_delete=models.PROTECT,
        related_name="evidencias_foto",
    )
    atividade = models.ForeignKey(
        AtividadeDaOS,
        on_delete=models.PROTECT,
        related_name="evidencias_foto",
    )
    tipo = models.CharField(max_length=30, choices=TIPO_CHOICES)
    b2_uri = models.TextField(
        help_text="URL Backblaze B2 WORM (foto armazenada imutavel 25a).",
    )
    foto_sha256 = models.CharField(
        max_length=64,
        help_text="SHA-256 da foto pos EXIF strip (cadeia probatoria).",
    )
    client_event_id = models.UUIDField(
        help_text="UUID gerado pelo client (sync mobile ADR-0027).",
    )
    client_event_created_at = models.DateTimeField(
        help_text="Timestamp do client no momento da captura (offline-first).",
    )
    enviada_em = models.DateTimeField(help_text="Timestamp do servidor no upload.")
    tecnico_executor_id = models.UUIDField(
        null=True,
        blank=True,
        help_text="FK user.id (db_constraint=False); pode ser diferente do tecnico_executor_id atual da atividade.",
    )
    geo_lat = models.FloatField(null=True, blank=True)
    geo_long = models.FloatField(null=True, blank=True)
    geo_municipio_hash = models.CharField(max_length=64, blank=True, default="")
    revogado_em = models.DateTimeField(
        null=True,
        blank=True,
        help_text="LGPD art. 18 (face cliente). Unico campo mutavel via UPDATE.",
    )
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = "ordens_servico"
        db_table = "evidencia_foto_atividade"
        verbose_name = "Evidencia foto de atividade"
        verbose_name_plural = "Evidencias foto de atividade"
        ordering = ["-criado_em"]
        constraints = [
            # client_event_id deve ser unico por tenant — anti-duplicacao no sync.
            models.UniqueConstraint(
                fields=("tenant", "client_event_id"),
                name="uq_evidencia_foto_client_event_por_tenant",
            ),
        ]
        indexes = [
            models.Index(fields=["tenant", "atividade"], name="evid_tenant_atv_idx"),
            models.Index(fields=["tenant", "atividade", "tipo"], name="evid_tenant_atv_tip_idx"),
        ]

    def __str__(self) -> str:
        rev = " REVOGADA" if self.revogado_em else ""
        return f"EvidenciaFoto({self.tipo} atv={self.atividade_id}{rev})"


class EventoDeOS(models.Model):
    """Timeline de eventos da OS/atividade — Padrao B append-only.

    INV-OS-AUD-001: payload sanitizado NA ESCRITA — proibe `cliente_id`,
    `tecnico_id`, `ator_id` UUID cru; so `*_hash` HMAC. `razao_*` cru
    proibido; so hash. Geo precisao alta proibida. Texto livre fora
    de `descricao_hash` validado anti-PII (INV-OS-TXT-001).

    Trigger PG: UPDATE/DELETE bloqueados (append-only). Pos-INSERT eh
    audit imutavel 25a.
    """

    TIPO_CHOICES = [
        ("atividade_adicionada", "Atividade adicionada"),
        ("atividade_iniciada", "Atividade iniciada"),
        ("atividade_concluida", "Atividade concluida"),
        ("atividade_nao_conforme", "Atividade nao conforme"),
        ("atividade_nc_resolvida", "Atividade NC resolvida"),
        ("atividade_cancelada", "Atividade cancelada"),
        ("atividade_reagendada", "Atividade reagendada"),
        ("atividade_tecnico_transferido", "Tecnico transferido"),
        ("no_show_cliente", "No-show cliente"),
        ("dispensa_aceite_emitida", "Dispensa de aceite emitida"),
        ("foto_evidencia_tardia", "Foto evidencia em atividade terminal"),
        ("watchdog_estendido", "Watchdog cal-link estendido"),
        ("os_aberta", "OS aberta"),
        ("os_atribuida", "OS atribuida"),
        ("os_concluida", "OS concluida"),
        ("os_cancelada", "OS cancelada"),
        ("os_reaberta", "OS reaberta"),
        ("os_escopo_alterado", "OS escopo alterado (ADR-0042)"),
        ("sla_breach", "SLA quebrado"),
    ]

    id = models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)
    tenant = models.ForeignKey(
        "tenant.Tenant",
        on_delete=models.PROTECT,
        related_name="eventos_os",
    )
    os = models.ForeignKey(
        OS,
        on_delete=models.PROTECT,
        related_name="eventos",
    )
    atividade = models.ForeignKey(
        AtividadeDaOS,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="eventos",
        help_text="Opcional; preenchido quando o evento eh de atividade especifica.",
    )
    tipo = models.CharField(max_length=40, choices=TIPO_CHOICES)
    payload_hash = models.CharField(
        max_length=64,
        help_text="SHA-256 do payload sanitizado (INV-OS-AUD-001 + INV-DOC-CANON-001).",
    )
    payload_data = models.JSONField(
        default=dict,
        help_text=(
            "Payload sanitizado — NAO contem PII cru. Hashes em vez de "
            "cliente_id/tecnico_id/ator_id. Helper unico "
            "audit/event_helpers.publicar_evento garante sanitizacao."
        ),
    )
    correlation_id = models.UUIDField(
        help_text="Correlation ID propagado entre modulos (ADR-0033 bus envelope v10).",
    )
    actor_user_id = models.UUIDField(
        null=True,
        blank=True,
        help_text="User que disparou (NULL em jobs automaticos: watchdog, retry).",
    )
    occurred_at = models.DateTimeField(
        help_text="Timestamp do evento de negocio (pode preceder criado_em em sync mobile).",
    )
    criado_em = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        app_label = "ordens_servico"
        db_table = "evento_de_os"
        verbose_name = "Evento de OS"
        verbose_name_plural = "Eventos de OS"
        ordering = ["-occurred_at"]
        indexes = [
            models.Index(fields=["tenant", "os", "occurred_at"], name="evt_os_tenant_os_occ_idx"),
            models.Index(fields=["tenant", "atividade", "occurred_at"], name="evt_os_tenant_atv_idx"),
            models.Index(fields=["tenant", "tipo", "occurred_at"], name="evt_os_tenant_tip_idx"),
            models.Index(fields=["tenant", "correlation_id"], name="evt_os_tenant_corr_idx"),
        ]

    def __str__(self) -> str:
        return f"EventoDeOS({self.tipo} os={self.os_id} @{self.occurred_at:%Y-%m-%d %H:%M})"


class DispensaAceiteAtividade(models.Model):
    """Dispensa formal de aceite do cliente (US-OS-013 + P-OS-A4).

    Entidade imutavel Padrao B. Exigida pelo CDC art. 39 / parecer
    advogado P-OS-A4:

    - `precedente_tipo` obrigatorio: dispensa SO permitida apos
      no-show registrado (US-OS-014) OU recusa explicita gravada
      (foto/audio do cliente recusando — opt-in).
    - `a3_assinatura_hash` obrigatorio: assinatura A3 do gerente
      (nao basta sessao autenticada).
    - `termo_pdf_b2_uri` + `termo_pdf_sha256`: TermoDispensaAceite
      canonicalizado (INV-DOC-CANON-001 + ADR-0029).

    REQUER OAB: modelo do TermoDispensaAceite em
    `docs/conformidade/comum/termos/` (GATE-OS-CONSBIO-TEXTO-OAB).

    Trigger PG bloqueia UPDATE/DELETE pos-INSERT.
    """

    PRECEDENTE_CHOICES = [
        ("no_show", "No-show do cliente"),
        ("recusa_explicita", "Recusa explicita gravada"),
        ("impossibilidade_tecnica", "Impossibilidade tecnica de captura"),
    ]

    id = models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)
    tenant = models.ForeignKey(
        "tenant.Tenant",
        on_delete=models.PROTECT,
        related_name="dispensas_aceite",
    )
    atividade = models.ForeignKey(
        AtividadeDaOS,
        on_delete=models.PROTECT,
        related_name="dispensas_aceite",
    )
    motivo_hash = models.CharField(
        max_length=64,
        help_text=(
            "SHA-256 do motivo livre (anti-PII INV-OS-TXT-001). "
            "Texto cru NUNCA persistido — soh em B2 WORM se necessario."
        ),
    )
    autorizado_por_gerente_id = models.UUIDField(
        help_text="FK user.id (db_constraint=False). Papel gerente verificado em camada de aplicacao.",
    )
    a3_assinatura_hash = models.CharField(
        max_length=64,
        help_text="SHA-256 da assinatura A3 do gerente (P-OS-A4 — nao basta sessao autenticada).",
    )
    a3_certificado_emissor_hash = models.CharField(
        max_length=64,
        help_text="Hash do AC emissor (ICP-Brasil); valida cadeia OCSP/CRL em camada de aplicacao.",
    )
    a3_assinada_em = models.DateTimeField(help_text="Timestamp da assinatura A3.")
    termo_pdf_b2_uri = models.TextField(
        help_text="URL Backblaze B2 WORM do TermoDispensaAceite (REQUER OAB modelo).",
    )
    termo_pdf_sha256 = models.CharField(
        max_length=64,
        help_text="SHA-256 do PDF (INV-DOC-CANON-001 — prova determinística 25a).",
    )
    precedente_tipo = models.CharField(
        max_length=30,
        choices=PRECEDENTE_CHOICES,
        help_text="Obrigatorio (P-OS-A4). Sem precedente -> 412 DispensaSemPrecedente.",
    )
    precedente_evento_id = models.UUIDField(
        null=True,
        blank=True,
        help_text=(
            "FK -> EventoDeOS (precedente=no_show) ou EvidenciaFotoAtividade "
            "(precedente=recusa_explicita). db_constraint=False — FK polimorfica."
        ),
    )
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = "ordens_servico"
        db_table = "dispensa_aceite_atividade"
        verbose_name = "Dispensa de aceite de atividade"
        verbose_name_plural = "Dispensas de aceite de atividade"
        ordering = ["-criado_em"]
        constraints = [
            models.UniqueConstraint(
                fields=("atividade",),
                name="uq_dispensa_aceite_por_atividade",
            ),
        ]
        indexes = [
            models.Index(fields=["tenant", "atividade"], name="disp_tenant_atv_idx"),
        ]

    def __str__(self) -> str:
        return f"DispensaAceite(atv={self.atividade_id} prec={self.precedente_tipo})"


class ChecklistDaAtividade(models.Model):
    """Item de checklist de uma AtividadeDaOS (US-OS-004 conclusao).

    Padrao A (ADR-0031) — estado por item. Mutavel via UPDATE
    controlado em service layer; cada item caminha pendente ->
    preenchido (ou nao_aplicavel). Atividade so conclui quando todos
    itens em estado terminal (preenchido | nao_aplicavel).

    Texto cru NUNCA persistido — `descricao_hash` + `valor_hash`
    canonicalizados (INV-OS-TXT-001 + INV-DOC-CANON-001). Texto
    publico fica em `valor_publico` (numero, OK/NOK, enum — nunca PII).
    """

    ESTADO_CHOICES = [
        ("pendente", "Pendente"),
        ("preenchido", "Preenchido"),
        ("nao_aplicavel", "Nao aplicavel"),
    ]

    id = models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)
    tenant = models.ForeignKey(
        "tenant.Tenant",
        on_delete=models.PROTECT,
        related_name="checklist_atividades",
    )
    atividade = models.ForeignKey(
        AtividadeDaOS,
        on_delete=models.PROTECT,
        related_name="checklist_itens",
    )
    ordem = models.IntegerField(help_text="Sequencia de apresentacao do item.")
    descricao_hash = models.CharField(
        max_length=64,
        help_text="SHA-256 da descricao canonicalizada (INV-DOC-CANON-001).",
    )
    descricao_publica = models.CharField(
        max_length=200,
        help_text="Descricao curta sem PII (rotulo do item — ex: 'Leitura padrao 1 kg').",
    )
    estado = models.CharField(
        max_length=20,
        choices=ESTADO_CHOICES,
        default="pendente",
    )
    valor_hash = models.CharField(
        max_length=64,
        blank=True,
        default="",
        help_text="Hash do valor cru preenchido (anti-PII). Vazio em pendente/nao_aplicavel.",
    )
    valor_publico = models.CharField(
        max_length=200,
        blank=True,
        default="",
        help_text="Valor exibivel sem PII (numero, OK/NOK, enum).",
    )
    preenchido_por_user_id = models.UUIDField(null=True, blank=True)
    preenchido_em = models.DateTimeField(null=True, blank=True)
    evidencia_foto = models.ForeignKey(
        EvidenciaFotoAtividade,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="checklist_itens",
        help_text="Opcional — foto vinculada ao item (ex: foto de display).",
    )
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = "ordens_servico"
        db_table = "checklist_da_atividade"
        verbose_name = "Item de checklist de atividade"
        verbose_name_plural = "Itens de checklist de atividade"
        ordering = ["atividade", "ordem"]
        constraints = [
            models.UniqueConstraint(
                fields=("atividade", "ordem"),
                name="uq_checklist_atividade_ordem",
            ),
        ]
        indexes = [
            models.Index(fields=["tenant", "atividade", "estado"], name="chk_tenant_atv_est_idx"),
        ]

    def __str__(self) -> str:
        return f"Checklist[{self.ordem}] atv={self.atividade_id} {self.estado}"


class NaoConformidadeAtividade(models.Model):
    """NC em atividade (US-OS-005 + P-OS-R5 RBC + cl. 8.7 ISO 17025).

    Padrao B (ADR-0031) — trigger PG bloqueia UPDATE pos-INSERT salvo
    transicao para campos CAPA via service controlado.

    Cobertura cl. 8.7 (P-OS-R5): ciclo CAPA completo obrigatorio para
    `resolverNC` (AC-OS-005-5):
    - causa_raiz_hash ≠ NULL
    - acao_corretiva_descricao_hash ≠ NULL
    - eficacia_verificada_em ≠ NULL
    - eficacia_verificada_por_user_id ≠ NULL
    Ausente -> 412 CAPAIncompleto.
    """

    id = models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)
    tenant = models.ForeignKey(
        "tenant.Tenant",
        on_delete=models.PROTECT,
        related_name="nao_conformidades",
    )
    atividade = models.ForeignKey(
        AtividadeDaOS,
        on_delete=models.PROTECT,
        related_name="nao_conformidades",
    )
    razao_nao_conformidade_hash = models.CharField(
        max_length=64,
        help_text="SHA-256 do texto cru (anti-PII INV-OS-TXT-001).",
    )
    marcada_em = models.DateTimeField(help_text="Timestamp da marcacao NC.")
    marcada_por_user_id = models.UUIDField(
        help_text="FK user.id (db_constraint=False). Metrologista ou RT.",
    )
    # Campos CAPA (P-OS-R5 + cl. 8.7).
    registro_capa_id = models.UUIDField(
        null=True,
        blank=True,
        help_text=(
            "FK -> qualidade.registro_capa (Wave B; db_constraint=False). "
            "Preenchido por consumer reverso quando modulo qualidade nascer "
            "(GATE-RBC-CAPA-1)."
        ),
    )
    causa_raiz_hash = models.CharField(
        max_length=64,
        blank=True,
        default="",
        help_text="Anti-PII (INV-OS-TXT-001). Obrigatorio em resolverNC.",
    )
    acao_corretiva_descricao_hash = models.CharField(
        max_length=64,
        blank=True,
        default="",
        help_text="Anti-PII. Obrigatorio em resolverNC.",
    )
    eficacia_verificada_em = models.DateTimeField(null=True, blank=True)
    eficacia_verificada_por_user_id = models.UUIDField(
        null=True,
        blank=True,
        help_text="Geralmente RT ou gerente_qualidade — predicate ABAC valida.",
    )
    revogado_em = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Raro — apenas se NC foi marcada por engano (audit preserva).",
    )
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = "ordens_servico"
        db_table = "nao_conformidade_atividade"
        verbose_name = "Nao conformidade de atividade"
        verbose_name_plural = "Nao conformidades de atividade"
        ordering = ["-criado_em"]
        constraints = [
            models.UniqueConstraint(
                fields=("atividade",),
                condition=models.Q(revogado_em__isnull=True),
                name="uq_nc_ativa_por_atividade",
            ),
        ]
        indexes = [
            models.Index(fields=["tenant", "atividade"], name="nc_tenant_atv_idx"),
        ]

    def __str__(self) -> str:
        resolvida = " resolvida" if self.eficacia_verificada_em else ""
        return f"NaoConformidade atv={self.atividade_id}{resolvida}"


class SLAContrato(models.Model):
    """Contrato de SLA do tenant com cliente (US-OS-007 saga 4).

    Padrao A com vigencia (ADR-0030 JanelaVigencia). Suporta multiplos
    SLAs vigentes simultaneos (ex: 1 SLA por categoria de servico). Usado
    em US-OS-007 cancelarOS: se OS tem SLA contratual prioridade alta|
    emergencia, dispara consumer `comercial/sla-breach`.
    """

    PRIORIDADE_CHOICES = [
        ("baixa", "Baixa"),
        ("normal", "Normal"),
        ("alta", "Alta"),
        ("emergencia", "Emergencia"),
    ]

    id = models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)
    tenant = models.ForeignKey(
        "tenant.Tenant",
        on_delete=models.PROTECT,
        related_name="sla_contratos",
    )
    cliente = models.ForeignKey(
        "clientes.Cliente",
        on_delete=models.PROTECT,
        db_constraint=False,
        related_name="sla_contratos",
    )
    prioridade = models.CharField(max_length=20, choices=PRIORIDADE_CHOICES, default="normal")
    prazo_atendimento_horas = models.IntegerField(
        help_text="Horas a partir de OSAberta para atribuirTecnico (US-OS-002b).",
    )
    prazo_conclusao_horas = models.IntegerField(
        help_text="Horas a partir de OSAberta para concluirAtividade da ultima atividade.",
    )
    descricao_publica = models.CharField(
        max_length=200,
        blank=True,
        default="",
        help_text="Descricao sem PII (categoria de servico).",
    )
    vigencia_inicio = models.DateTimeField(help_text="ADR-0030 JanelaVigencia.")
    vigencia_fim = models.DateTimeField(null=True, blank=True, help_text="NULL = aberta.")
    revogado_em = models.DateTimeField(null=True, blank=True)
    motivo_revogacao_hash = models.CharField(max_length=64, blank=True, default="")
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = "ordens_servico"
        db_table = "sla_contrato"
        verbose_name = "Contrato de SLA"
        verbose_name_plural = "Contratos de SLA"
        ordering = ["-vigencia_inicio"]
        indexes = [
            models.Index(fields=["tenant", "cliente", "vigencia_inicio"], name="sla_tenant_cli_vig_idx"),
        ]

    def __str__(self) -> str:
        return f"SLA cli={self.cliente_id} prio={self.prioridade}"
