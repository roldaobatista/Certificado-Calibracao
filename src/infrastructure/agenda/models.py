# ruff: noqa: RUF012 — choices derivados de enum (list mutável ok em Model)
"""Frente agenda — models Django (Fatia 1b, T-AGE-020).

7 tabelas achatadas que espelham as entidades de domínio em
``src/domain/operacao/agenda/entities.py``. Choices 1:1 dos enums via
``_choices(enum)`` (anti-drift). Domain NÃO importa Django — o mapper em
``mappers.py`` converte.

Tabelas:
- ``evento_agenda``                — raiz de agregado; EXCLUDE GIST (0003).
- ``recorrencia_agenda``           — regra RRULE + âncora de materialização.
- ``registro_no_show``             — INSERT-only WORM (trigger 0004).
- ``capacidade_tecnico``           — capacidade diária por técnico.
- ``feriado``                      — seed nacional + custom por tenant.
- ``evento_auditoria_agenda``      — trilha WORM INSERT-only (trigger 0004).
- ``regime_jornada_colaborador``   — override humano de regime (INSERT-only, trigger 0004).

WORM / semântica de imutabilidade:
- ``EventoAuditoriaAgenda`` — INSERT-only puro: block-update + block-delete (trigger 0004).
- ``RegistroNoShow``        — INSERT-only puro: block-update + block-delete (trigger 0004).
- ``RegimeJornadaColaborador`` — INSERT-only puro: block-update + block-delete (trigger 0004).
- ``EventoAgenda``          — mutável controlado (máquina de estados Padrão A — D-AGE-3);
                              move = update timestamps + append EventoAuditoriaAgenda.

Schema-irmãos:
- 0001_initial: CreateModel + índices.
- 0002_rls_policies: RLS pattern v2 (ADR-0002 §6) em TODAS as 7 tabelas.
- 0003_exclusion_overlap: EXCLUDE GIST (tenant_id, tecnico_id, tstzrange '[)') (R1/R12).
- 0004_triggers_worm: INSERT-only em EventoAuditoriaAgenda/RegistroNoShow/RegimeJornada.
- 0005_grants_app_user: GRANT app_user.
- 0006_seed_authz: matriz papel × ação agenda.*.
- 0007_seed_feriados: catálogo nacional BR (D-AGE-10).
"""

from __future__ import annotations

import uuid
from enum import Enum

from django.db import models

from src.domain.operacao.agenda.enums import (
    AcaoAuditoria,
    EstadoEvento,
    FonteRegime,
    MotivoBloqueio,
    RegimeJornada,
    TipoEvento,
)


def _choices(enum_cls: type[Enum]) -> list[tuple[str, str]]:
    """Choices (value, value) a partir do enum de domínio (1:1 anti-drift)."""
    return [(membro.value, str(membro.value)) for membro in enum_cls]


class EventoAgenda(models.Model):
    """Raiz de agregado da agenda (D-AGE-3 / D-AGE-2 / INV-AG-ATIVIDADE-001).

    Invariante via CHECK: ``atividade_id`` NOT NULL quando ``tipo='os'``
    (ADR-0023/0051 — agendar ATIVIDADE, não OS inteira).

    Overlap garantido por EXCLUDE GIST na migration 0003
    (INV-AG-OVERLAP-001 / D-AGE-13 / R1/R12).

    ``revision`` — bump a cada transição de estado (OCC / observabilidade).
    ``aloca_em_umc`` — ativa validação de jornada UMC (D-AGE-4).
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, serialize=False)
    tenant = models.ForeignKey(
        "tenant.tenant",
        on_delete=models.PROTECT,
        related_name="eventos_agenda",
    )
    tecnico_id = models.UUIDField(
        help_text="Colaborador alocado (FK lógica — não FK hard para colaboradores FECHADO).",
        db_index=False,  # cobertura pelo índice composto (tenant, tecnico_id, inicia_at)
    )
    tipo = models.CharField(
        max_length=30,
        choices=_choices(TipoEvento),
        help_text="Tipo do evento (D-AGE-2/3).",
    )
    estado = models.CharField(
        max_length=20,
        choices=_choices(EstadoEvento),
        help_text="Estado da máquina de estados (D-AGE-3 Padrão A).",
    )
    inicia_at = models.DateTimeField(
        help_text="Início do evento (timezone-aware). Componente do EXCLUDE GIST.",
    )
    termina_at = models.DateTimeField(
        help_text="Fim do evento (timezone-aware). Componente do EXCLUDE GIST (half-open).",
    )
    aloca_em_umc = models.BooleanField(
        default=False,
        help_text="Técnico sendo alocado em campo/UMC (ativa validação de jornada UMC — D-AGE-4).",
    )
    criado_por_usuario_id = models.UUIDField(
        help_text="Usuário que criou o evento.",
    )
    # Obrigatório quando tipo='os' (INV-AG-ATIVIDADE-001 — CHECK na migration 0003):
    atividade_id = models.UUIDField(
        null=True,
        blank=True,
        help_text=(
            "FK lógica à AtividadeDaOS (ADR-0023/0051). "
            "NOT NULL quando tipo='os' (CHECK — INV-AG-ATIVIDADE-001)."
        ),
    )
    # Desnormalizado derivado (não é fonte de verdade):
    os_id = models.UUIDField(
        null=True,
        blank=True,
        help_text="OS de origem (desnormalizado derivado — D-AGE-2).",
    )
    motivo_bloqueio = models.CharField(
        max_length=20,
        choices=_choices(MotivoBloqueio),
        blank=True,
        default="",
        help_text="Motivo do bloqueio (só quando tipo='bloqueio' — US-AG-004).",
    )
    descricao_publica = models.TextField(
        blank=True,
        default="",
        help_text="Descrição pública do evento (visível ao cliente em Wave B).",
    )
    recorrencia_id = models.UUIDField(
        null=True,
        blank=True,
        help_text="FK à Recorrencia originadora (None = evento avulso).",
    )
    ocorrencia_dt = models.DateTimeField(
        null=True,
        blank=True,
        help_text=(
            "Data-âncora da ocorrência na série de recorrência. "
            "UNIQUE com recorrencia_id (INV-AG-RECORRENCIA-001 / R10)."
        ),
    )
    confirmar_feriado = models.BooleanField(
        default=False,
        help_text="Confirmação explícita de agendamento em feriado (D-AGE-10).",
    )
    revision = models.IntegerField(
        default=0,
        help_text="Contador de transições de estado (OCC / observabilidade). Bumpa por F('revision')+1.",
    )
    criado_em = models.DateTimeField(auto_now_add=True, db_index=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "evento_agenda"
        verbose_name = "Evento de Agenda"
        verbose_name_plural = "Eventos de Agenda"
        ordering = ["inicia_at"]
        constraints = [
            # INV-AG-ATIVIDADE-001: atividade_id NOT NULL quando tipo='os' (D-AGE-2/ADR-0023).
            models.CheckConstraint(
                condition=(~models.Q(tipo="os") | models.Q(atividade_id__isnull=False)),
                name="chk_agenda_evento_atividade_obrigatoria_quando_os",
            ),
            # INV-AG-RECORRENCIA-001 / R10: unicidade da ocorrência materializada (D-AGE-8).
            models.UniqueConstraint(
                fields=["recorrencia_id", "ocorrencia_dt"],
                condition=models.Q(recorrencia_id__isnull=False),
                name="uq_agenda_evento_recorrencia_ocorrencia",
            ),
        ]
        indexes = [
            # R14: índice principal para listagem de grade + validação de overlap em app-layer.
            models.Index(
                fields=["tenant", "tecnico_id", "inicia_at"],
                name="ag_evt_tec_inicia_idx",
            ),
            models.Index(
                fields=["tenant", "estado"],
                name="ag_evt_tenant_estado_idx",
            ),
            models.Index(
                fields=["tenant", "atividade_id"],
                name="ag_evt_tenant_ativ_idx",
            ),
        ]

    def __str__(self) -> str:
        return f"EventoAgenda({self.id} — {self.tipo}/{self.estado})"


class RecorrenciaAgenda(models.Model):
    """Regra de recorrência de eventos (D-AGE-8 / US-AG-009 / INV-AG-RECORRENCIA-001).

    A materialização de ocorrências é feita por ``materializar_janela``
    (``domain/operacao/agenda/recorrencia.py``) — puro, determinístico,
    idempotente por ``(recorrencia_id, ocorrencia_dt)`` UNIQUE em EventoAgenda.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, serialize=False)
    tenant = models.ForeignKey(
        "tenant.tenant",
        on_delete=models.PROTECT,
        related_name="recorrencias_agenda",
    )
    tecnico_id = models.UUIDField(
        help_text="Colaborador da série recorrente.",
    )
    rrule_str = models.TextField(
        help_text="Regra RRULE RFC 5545 serializada como string.",
    )
    inicia_em = models.DateTimeField(
        help_text="Âncora de início da série recorrente.",
    )
    duracao_minutos = models.IntegerField(
        help_text="Duração de cada ocorrência materializada em minutos.",
    )
    ativo = models.BooleanField(
        default=True,
        help_text="Se False, o job de materialização para de expandir.",
    )
    tipo = models.CharField(
        max_length=30,
        choices=_choices(TipoEvento),
        help_text="Tipo do evento materializado.",
    )
    criado_por_usuario_id = models.UUIDField()
    atividade_id = models.UUIDField(null=True, blank=True)
    os_id = models.UUIDField(null=True, blank=True)
    aloca_em_umc = models.BooleanField(default=False)
    revision = models.IntegerField(default=0)
    criado_em = models.DateTimeField(auto_now_add=True, db_index=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "recorrencia_agenda"
        verbose_name = "Recorrência de Agenda"
        verbose_name_plural = "Recorrências de Agenda"
        ordering = ["-criado_em"]
        indexes = [
            models.Index(
                fields=["tenant", "tecnico_id"],
                name="ag_rec_tenant_tec_idx",
            ),
        ]

    def __str__(self) -> str:
        return f"RecorrenciaAgenda({self.id})"


class RegistroNoShow(models.Model):
    """Registro de no-show INSERT-only WORM (INV-AG-AUDIT-WORM-001 / D-AGE-9).

    Trigger 0004 bloqueia UPDATE e DELETE.
    Quando ``cobrar_cliente=True``, o use case chama ``AReceberPort.criar_titulo_manual``
    e publica ``agenda.no_show.registrado`` (INV-AG-NOSHOW-AR-001).
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, serialize=False)
    tenant = models.ForeignKey(
        "tenant.tenant",
        on_delete=models.PROTECT,
        related_name="registros_no_show",
    )
    evento_id = models.UUIDField(
        help_text="FK lógica ao EventoAgenda que originou o no-show.",
    )
    tecnico_id = models.UUIDField(
        help_text="Técnico que não compareceu.",
    )
    ocorrido_em = models.DateTimeField(
        help_text="Momento em que o no-show foi constatado.",
    )
    custo_estimado = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Custo estimado da visita frustrada (R$, 2 casas decimais).",
    )
    cobrar_cliente = models.BooleanField(
        default=False,
        help_text="Se True, o use case dispara AReceberPort (INV-AG-NOSHOW-AR-001).",
    )
    registrado_por_usuario_id = models.UUIDField(
        help_text="Usuário que registrou o no-show.",
    )
    observacao = models.TextField(
        blank=True,
        default="",
        help_text="Observação livre (sem PII do cliente).",
    )
    criado_em = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = "registro_no_show"
        verbose_name = "Registro de No-Show"
        verbose_name_plural = "Registros de No-Show"
        ordering = ["-criado_em"]
        constraints = [
            # 1 no-show por evento por tenant — fecha o TOCTOU de cobrança dupla
            # sob concorrência (INV-AG-NOSHOW-AR-001). O use case captura o
            # IntegrityError e devolve 409 TransicaoEventoProibida.
            models.UniqueConstraint(
                fields=["tenant", "evento_id"],
                name="uq_no_show_evento",
            ),
        ]
        indexes = [
            models.Index(
                fields=["tenant", "tecnico_id"],
                name="ag_nsh_tenant_tec_idx",
            ),
        ]

    def __str__(self) -> str:
        return f"RegistroNoShow({self.evento_id} — cobrar={self.cobrar_cliente})"


class CapacidadeTecnico(models.Model):
    """Capacidade de trabalho diária configurada por técnico (D-AGE-11 / US-AG-010).

    Default 8h úteis seg-sex (08:00-17:00, 1h almoço) quando não cadastrada.
    Base para o indicador de 75%/90% de horas alocadas.
    ``dias_trabalho`` — máscara bitmask: bit 0=seg, ..., bit 6=dom.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, serialize=False)
    tenant = models.ForeignKey(
        "tenant.tenant",
        on_delete=models.PROTECT,
        related_name="capacidades_tecnico",
    )
    colaborador_id = models.UUIDField(
        help_text="Colaborador técnico (FK lógica — colaboradores FECHADO).",
    )
    horas_uteis_dia = models.IntegerField(
        default=8,
        help_text="Horas úteis por dia de trabalho (default 8).",
    )
    dias_trabalho = models.IntegerField(
        default=0b0011111,  # seg-sex
        help_text="Bitmask: bit 0=seg, ..., bit 6=dom. Default seg-sex (31 = 0b0011111).",
    )
    hora_inicio = models.IntegerField(
        default=8,
        help_text="Hora de início do expediente (0-23). Default 8.",
    )
    hora_fim = models.IntegerField(
        default=17,
        help_text="Hora de fim do expediente (0-23). Default 17.",
    )
    vigencia_inicio = models.DateField(
        help_text="Início da vigência desta configuração.",
    )
    vigencia_fim = models.DateField(
        null=True,
        blank=True,
        help_text="Fim da vigência (None = vigente indefinidamente).",
    )
    criado_por_usuario_id = models.UUIDField()
    revision = models.IntegerField(default=0)
    criado_em = models.DateTimeField(auto_now_add=True, db_index=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "capacidade_tecnico"
        verbose_name = "Capacidade de Técnico"
        verbose_name_plural = "Capacidades de Técnico"
        ordering = ["-vigencia_inicio"]
        indexes = [
            models.Index(
                fields=["tenant", "colaborador_id", "vigencia_inicio"],
                name="ag_cap_tenant_col_idx",
            ),
        ]

    def __str__(self) -> str:
        return f"CapacidadeTecnico({self.colaborador_id} — {self.horas_uteis_dia}h/dia)"


class Feriado(models.Model):
    """Feriado nacional (seed) ou custom por tenant (D-AGE-10 / US-AG-005).

    ``tenant=None`` indica feriado do catálogo nacional (seed — imutável via trigger).
    Agendar em feriado exige ``confirmar_feriado=True`` no EventoAgenda (D-AGE-10).
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, serialize=False)
    tenant = models.ForeignKey(
        "tenant.tenant",
        on_delete=models.PROTECT,
        related_name="feriados_custom",
        null=True,
        blank=True,
        help_text="None = feriado nacional (seed); UUID = custom por tenant.",
    )
    data = models.DateField(
        help_text="Data do feriado.",
    )
    descricao = models.CharField(
        max_length=200,
        help_text="Nome do feriado.",
    )
    nacional = models.BooleanField(
        default=True,
        help_text="True = feriado nacional (seed); False = estadual/municipal/empresa.",
    )
    ativo = models.BooleanField(
        default=True,
        help_text="False = feriado removido do calendário (soft-delete para custom).",
    )
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "feriado"
        verbose_name = "Feriado"
        verbose_name_plural = "Feriados"
        ordering = ["data"]
        constraints = [
            # Unicidade do feriado nacional por data (seed idempotente):
            models.UniqueConstraint(
                fields=["data"],
                condition=models.Q(nacional=True, tenant__isnull=True),
                name="uq_agenda_feriado_nacional_data",
            ),
        ]
        indexes = [
            models.Index(
                fields=["data", "nacional"],
                name="ag_fer_data_nacional_idx",
            ),
            models.Index(
                fields=["tenant", "data"],
                name="ag_fer_tenant_data_idx",
            ),
        ]

    def __str__(self) -> str:
        return f"Feriado({self.data} — {self.descricao})"


class EventoAuditoriaAgenda(models.Model):
    """Trilha de auditoria WORM (INSERT-only — INV-AG-AUDIT-WORM-001).

    Toda transição de estado ou reagendamento gera um registro aqui.
    Trigger 0004 bloqueia UPDATE e DELETE (ADR-0031 Padrão B INSERT-only).
    ``payload_resumo`` — resumo não-PII da mudança.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, serialize=False)
    tenant = models.ForeignKey(
        "tenant.tenant",
        on_delete=models.PROTECT,
        related_name="eventos_auditoria_agenda",
    )
    evento_id = models.UUIDField(
        help_text="FK lógica ao EventoAgenda auditado.",
        db_index=True,
    )
    acao = models.CharField(
        max_length=30,
        choices=_choices(AcaoAuditoria),
        help_text="Ação auditada (INV-AG-AUDIT-WORM-001).",
    )
    actor_usuario_id = models.UUIDField(
        null=True,
        blank=True,
        help_text="Usuário que executou a ação (None = sistema/consumer).",
    )
    occurred_at = models.DateTimeField(
        help_text="Momento em que a ação ocorreu (timezone-aware).",
    )
    payload_resumo = models.TextField(
        blank=True,
        default="",
        help_text="Resumo não-PII da mudança (diff de campos relevantes).",
    )
    criado_em = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = "evento_auditoria_agenda"
        verbose_name = "Evento de Auditoria da Agenda"
        verbose_name_plural = "Eventos de Auditoria da Agenda"
        ordering = ["criado_em"]
        indexes = [
            models.Index(
                fields=["tenant", "evento_id"],
                name="ag_aud_tenant_evento_idx",
            ),
            models.Index(
                fields=["tenant", "criado_em"],
                name="ag_aud_tenant_criado_idx",
            ),
        ]

    def __str__(self) -> str:
        return f"EventoAuditoriaAgenda({self.evento_id} — {self.acao})"


class RegimeJornadaColaborador(models.Model):
    """Override humano de regime de jornada (D-AGE-15 / INV-AG-REGIME-001).

    Mora na agenda (não em colaboradores — colaboradores FECHADO, D-AGE-15).
    INSERT-com-vigência: cada alteração insere nova linha; a vigente é a
    com maior ``vigencia_inicio`` ≤ ``na_data``.

    Trigger 0004 bloqueia UPDATE e DELETE (INSERT-only WORM).

    IA NUNCA grava nesta tabela — só humano (RH/advogado) via
    ``enquadrar_regime`` (T-AGE-036 / INV-AG-REGIME-001).
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, serialize=False)
    tenant = models.ForeignKey(
        "tenant.tenant",
        on_delete=models.PROTECT,
        related_name="regimes_jornada_colaborador",
    )
    colaborador_id = models.UUIDField(
        help_text="Colaborador com enquadramento de regime (FK lógica — colaboradores FECHADO).",
    )
    regime = models.CharField(
        max_length=30,
        choices=_choices(RegimeJornada),
        help_text="Regime de jornada enquadrado (D-AGE-15).",
    )
    vigencia_inicio = models.DateField(
        help_text="Início da vigência do enquadramento.",
    )
    vigencia_fim = models.DateField(
        null=True,
        blank=True,
        help_text="Fim da vigência (None = vigente indefinidamente).",
    )
    definido_por_usuario_id = models.UUIDField(
        help_text="Usuário humano (RH/advogado) que fez o override (INV-AG-REGIME-001).",
    )
    fonte = models.CharField(
        max_length=20,
        choices=_choices(FonteRegime),
        default="override_humano",
        help_text="Fonte do enquadramento — SEMPRE override_humano nesta tabela (INV-AG-REGIME-001).",
    )
    justificativa = models.TextField(
        blank=True,
        default="",
        help_text="Justificativa do enquadramento (recomendado ≥50 chars para rastreabilidade).",
    )
    criado_em = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = "regime_jornada_colaborador"
        verbose_name = "Regime de Jornada de Colaborador"
        verbose_name_plural = "Regimes de Jornada de Colaborador"
        ordering = ["-vigencia_inicio"]
        indexes = [
            models.Index(
                fields=["tenant", "colaborador_id", "vigencia_inicio"],
                name="ag_reg_tenant_col_idx",
            ),
        ]

    def __str__(self) -> str:
        return f"RegimeJornadaColaborador({self.colaborador_id} — {self.regime})"
