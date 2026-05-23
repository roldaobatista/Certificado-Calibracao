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
        help_text="Cada tenant tem 6 entradas. Seed inicial via data migration.",
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
