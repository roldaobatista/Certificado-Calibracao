# ruff: noqa: RUF012 — choices derivados de enum (list mutável ok em Model)
"""Frente caixa_tecnico — models Django (Fatia 1b, T-CT-020).

6 tabelas achatadas que espelham as entidades de domínio em
``src/domain/caixa_tecnico/entities.py``. Choices 1:1 dos enums via
``_choices(enum)`` (anti-drift). Domain NÃO importa Django — o mapper em
``mappers.py`` converte.

Tabelas:
- ``caixa_tecnico``              — raiz por técnico; saldo DERIVADO (D-CT-2).
- ``adiantamento_caixa``         — máquina de estados (D-CT-7).
- ``despesa_caixa``              — raiz com WORM pós-validada (D-CT-3/4).
- ``prestacao_contas_caixa``     — WORM financeiro pós-fechamento (D-CT-8).
- ``politica_caixa``             — configuração por tenant (D-CT-9).
- ``consentimento_gps_colaborador`` — opt-in GPS append-only (D-CT-6).

WORM / imutabilidade:
- ``DespesaCaixa``          — campos financeiros imutáveis pós ``estado='validada'``
                              (trigger 0003 anti-mutação + block-delete sempre).
- ``PrestacaoContasCaixa``  — campos financeiros congelados pós-fechamento
                              (trigger 0003 WORM financeiro).
- ``ConsentimentoGpsColaborador`` — INSERT-only com vigência (append-only; não WORM PG).

Padrão soft-delete:
- ``CaixaTecnico``             — Padrão A (máquina implícita via desligado_em).
                                 # soft-delete-padrao: A -- desligado_em = fail-closed consumer
- ``AdiantamentoCaixa``        — Padrão A (máquina de estados EstadoAdiantamento).
                                 # soft-delete-padrao: A -- máquina de estados EstadoAdiantamento
- ``DespesaCaixa``             — Padrão A (máquina de estados EstadoDespesa com cancelada).
                                 # soft-delete-padrao: A -- máquina de estados EstadoDespesa
- ``PrestacaoContasCaixa``     — Padrão B (INSERT-only WORM via trigger 0003).
                                 # soft-delete-padrao: B -- INSERT-only WORM pós-fechamento
- ``PoliticaCaixa``            — Padrão C (mutável controlado por tenant).
                                 # soft-delete-padrao: C -- configuração mutável por tenant
- ``ConsentimentoGpsColaborador`` — Padrão B (append-only; revogado_em one-shot).
                                    # soft-delete-padrao: B -- append-only INSERT-with-vigencia

Vigência canônica (ADR-0030):
- ``ConsentimentoGpsColaborador``: vigencia_inicio + revogado_em são os campos
  canônicos de vigência (ADR-0030). NÃO usa VO JanelaVigencia no model pq é tabela
  achatada SQL — a entidade de domínio encapsula a semântica via ``esta_vigente``.
  # vigencia-canonica: skip -- tabela achatada SQL; domínio encapsula via ConsentimentoGpsColaborador.esta_vigente (D-CT-6/ADR-0030)

Schema-irmãos:
- 0001_initial: CreateModel 6 tabelas + índices.
- 0002_rls_policies: RLS pattern v2 (ADR-0002 §6) em TODAS as 6 tabelas.
- 0003_triggers_worm: anti-mutação despesa validada + block-delete + PrestacaoContas WORM.
- 0004_constraints: UNIQUE parcial foto_hash + client_offline_id.
- 0005_grants_app_user: GRANT app_user.
- 0006_seed_authz: matriz papel × ação caixa_tecnico.*.
"""

from __future__ import annotations

import uuid
from enum import Enum

from django.db import models

from src.domain.caixa_tecnico.enums import (
    CategoriaDespesa,
    DirecaoPrestacao,
    EstadoAdiantamento,
    EstadoDespesa,
    MeioEntrega,
    TipoDespesa,
)


def _choices(enum_cls: type[Enum]) -> list[tuple[str, str]]:
    """Choices (value, value) a partir do enum de domínio (1:1 anti-drift)."""
    return [(membro.value, str(membro.value)) for membro in enum_cls]


class CaixaTecnico(models.Model):
    """Raiz de caixa por técnico (D-CT-2 / INV-CT-SALDO-001).

    Saldo NÃO é campo persistido — é DERIVADO on-read pela função de domínio
    ``calcular_saldo`` (D-CT-2). A tentativa de persisti-lo violaria a
    invariante de consistência com adiantamentos e despesas.

    ``desligado_em`` — preenchido pelo consumer ``colaborador.desligado``
    (fail-closed). Novos lançamentos bloqueados quando preenchido (D-CT-11).

    ``tecnico_referencia_hash`` + ``tecnico_key_id`` — ADR-0032: FK lógica
    anonimizável ao colaborador (PII).

    # soft-delete-padrao: A -- desligado_em = fail-closed consumer colaborador.desligado
    # fk-pii-anonimizavel: skip -- tecnico_referencia_hash + tecnico_key_id já implementam ADR-0032
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, serialize=False)
    tenant = models.ForeignKey(
        "tenant.tenant",
        on_delete=models.PROTECT,
        related_name="caixas_tecnico",
    )
    tecnico_referencia_hash = models.CharField(
        max_length=80,
        help_text="HMAC do técnico — pseudônimo na trilha (ADR-0032). Imutável, NOT NULL.",
    )
    tecnico_key_id = models.CharField(
        max_length=10,
        help_text="Versão da chave HMAC (ex: v1, v2 — ADR-0064 / rotação anual).",
    )
    desligado_em = models.DateTimeField(
        null=True,
        blank=True,
        help_text=(
            "Preenchido pelo consumer colaborador.desligado (D-CT-11). "
            "Fail-closed: novos lançamentos bloqueados quando presente."
        ),
    )
    criado_em = models.DateTimeField(auto_now_add=True, db_index=True)
    revision = models.IntegerField(
        default=0,
        help_text="Contador de transições (observabilidade / OCC). Bumpa por F('revision')+1.",
    )

    class Meta:
        db_table = "caixa_tecnico"
        verbose_name = "Caixa do Técnico"
        verbose_name_plural = "Caixas de Técnicos"
        ordering = ["-criado_em"]
        constraints = [
            # INV-CT-CAIXA-UNICO: 1 caixa por técnico por tenant.
            models.UniqueConstraint(
                fields=["tenant", "tecnico_referencia_hash"],
                name="uq_ct_caixa_tecnico_hash",
            ),
        ]
        indexes = [
            models.Index(
                fields=["tenant", "tecnico_referencia_hash"],
                name="ct_caixa_tenant_hash_idx",
            ),
        ]

    def __str__(self) -> str:
        return f"CaixaTecnico({self.id} — {self.tecnico_referencia_hash[:8]}...)"


class AdiantamentoCaixa(models.Model):
    """Adiantamento financeiro ao técnico (D-CT-7 / US-CT-001..003).

    Máquina de estados: solicitado → aprovado → entregue (terminal).
                        solicitado → recusado (terminal).
                        solicitado/aprovado → cancelado (terminal).

    ``aprovado_por_id`` / ``entregue_por_id`` — ID concreto do usuário
    (ato gerencial rastreável, não PII anônima).

    # soft-delete-padrao: A -- máquina de estados EstadoAdiantamento (cancelado/recusado/entregue = terminal)
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, serialize=False)
    tenant = models.ForeignKey(
        "tenant.tenant",
        on_delete=models.PROTECT,
        related_name="adiantamentos_caixa",
    )
    caixa = models.ForeignKey(
        CaixaTecnico,
        on_delete=models.PROTECT,
        related_name="adiantamentos",
    )
    tecnico_referencia_hash = models.CharField(
        max_length=80,
        help_text="HMAC do técnico — cópia desnormalizada para trilha (ADR-0032).",
    )
    tecnico_key_id = models.CharField(
        max_length=10,
        help_text="Versão da chave HMAC (ADR-0064).",
    )
    valor = models.BigIntegerField(
        help_text="Valor do adiantamento em centavos (Dinheiro BRL).",
    )
    estado = models.CharField(
        max_length=20,
        choices=_choices(EstadoAdiantamento),
        help_text="Estado da máquina de estados (D-CT-7).",
    )
    meio = models.CharField(
        max_length=20,
        choices=_choices(MeioEntrega),
        help_text="Meio de entrega do adiantamento (US-CT-001).",
    )
    solicitado_em = models.DateTimeField(
        help_text="Momento da solicitação do adiantamento.",
    )
    aprovado_em = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Momento da aprovação (None se ainda não aprovado).",
    )
    entregue_em = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Momento da entrega (None se ainda não entregue — estado terminal).",
    )
    recusado_em = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Momento da recusa (terminal).",
    )
    cancelado_em = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Momento do cancelamento (terminal).",
    )
    motivo_recusa = models.TextField(
        blank=True,
        default="",
        help_text="Motivo da recusa (obrigatório quando recusado).",
    )
    justificativa = models.TextField(
        blank=True,
        default="",
        help_text="Justificativa do solicitante.",
    )
    aprovado_por_id = models.UUIDField(
        null=True,
        blank=True,
        help_text="ID concreto do usuário que aprovou (ato gerencial rastreável).",
    )
    entregue_por_id = models.UUIDField(
        null=True,
        blank=True,
        help_text="ID concreto do usuário que confirmou a entrega.",
    )
    criado_em = models.DateTimeField(auto_now_add=True, db_index=True)
    revision = models.IntegerField(
        default=0,
        help_text="Contador de transições (OCC).",
    )

    class Meta:
        db_table = "adiantamento_caixa"
        verbose_name = "Adiantamento de Caixa"
        verbose_name_plural = "Adiantamentos de Caixa"
        ordering = ["-solicitado_em"]
        indexes = [
            models.Index(
                fields=["tenant", "caixa", "estado"],
                name="ct_adian_caixa_estado_idx",
            ),
            models.Index(
                fields=["tenant", "solicitado_em"],
                name="ct_adian_solicitado_idx",
            ),
        ]

    def __str__(self) -> str:
        return f"AdiantamentoCaixa({self.id} — {self.estado})"


class DespesaCaixa(models.Model):
    """Despesa do técnico de campo (D-CT-3/4 / US-CT-005..008).

    Raiz da agregado de despesa. ``foto_hash`` e ``foto_url`` são NOT NULL —
    foto-comprovante obrigatória (D-CT-4 / INV-CT-FOTO-001).

    Estado: pendente → validada (WORM) | rejeitada → pendente (reapresentação)
                     | cancelada (terminal).

    ``despesa_origem_id`` — FK lógica para estorno (tipo=estorno referencia original).
    ``acima_limite``      — flag calculada na regra de negócio; NÃO bloqueia (D-CT-9).
    ``gps_lat`` / ``gps_lng`` — opt-in server-side (D-CT-6); NULL quando sem consentimento.

    # soft-delete-padrao: A -- máquina de estados EstadoDespesa (validada/cancelada = terminal)
    # fk-pii-anonimizavel: skip -- tecnico_referencia_hash + tecnico_key_id já implementam ADR-0032
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, serialize=False)
    tenant = models.ForeignKey(
        "tenant.tenant",
        on_delete=models.PROTECT,
        related_name="despesas_caixa",
    )
    caixa = models.ForeignKey(
        CaixaTecnico,
        on_delete=models.PROTECT,
        related_name="despesas",
    )
    tecnico_referencia_hash = models.CharField(
        max_length=80,
        help_text="HMAC do técnico — trilha imutável (ADR-0032).",
    )
    tecnico_key_id = models.CharField(
        max_length=10,
        help_text="Versão da chave HMAC (ADR-0064).",
    )
    categoria = models.CharField(
        max_length=20,
        choices=_choices(CategoriaDespesa),
        help_text="Categoria da despesa (D-CT-9 / US-CT-005).",
    )
    tipo = models.CharField(
        max_length=10,
        choices=_choices(TipoDespesa),
        default=TipoDespesa.NORMAL.value,
        help_text="normal | estorno (D-CT-3).",
    )
    valor = models.BigIntegerField(
        help_text="Valor em centavos (Dinheiro BRL).",
    )
    estado = models.CharField(
        max_length=10,
        choices=_choices(EstadoDespesa),
        default=EstadoDespesa.PENDENTE.value,
        help_text="Estado da máquina de estados (D-CT-3).",
    )
    # foto-comprovante obrigatória (D-CT-4 / INV-CT-FOTO-001) — NOT NULL em domínio e schema
    foto_hash = models.CharField(
        max_length=80,
        help_text="HMAC-SHA256 dos bytes pós-EXIF-strip (content-address por tenant — D-CT-4/ADR-0064).",
    )
    foto_url = models.URLField(
        max_length=500,
        help_text="URL relativa da foto content-addressed (D-CT-4).",
    )
    data = models.DateField(
        help_text="Data da despesa (informada pelo técnico).",
    )
    descricao = models.TextField(
        blank=True,
        default="",
        help_text="Descrição livre da despesa.",
    )
    km_percorridos = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Km rodados (obrigatório quando categoria=deslocamento — D-CT-9).",
    )
    # GPS opt-in server-side (D-CT-6 / INV-LGPD-CONSENT-001)
    gps_lat = models.DecimalField(
        max_digits=10,
        decimal_places=7,
        null=True,
        blank=True,
        help_text="Latitude GPS (opt-in server-side — D-CT-6). NULL sem consentimento.",
    )
    gps_lng = models.DecimalField(
        max_digits=10,
        decimal_places=7,
        null=True,
        blank=True,
        help_text="Longitude GPS (opt-in server-side — D-CT-6). NULL sem consentimento.",
    )
    # retenção curta de gps_referencia_pii: fechamento + 90 dias (crypto-shredding)
    gps_referencia_pii = models.CharField(
        max_length=80,
        blank=True,
        default="",
        help_text="Hash PII da referência GPS (retenção curta — D-CT-6/ADR-0021).",
    )
    os_id = models.UUIDField(
        null=True,
        blank=True,
        help_text="FK lógica à OS vinculada (rastro histórico — D-CT-11).",
    )
    # idempotência offline (D-CT-5 / INV-CT-OFFLINE-001)
    client_offline_id = models.CharField(
        max_length=120,
        blank=True,
        default="",
        help_text="ID gerado pelo cliente offline (idempotência dupla-camada — D-CT-5).",
    )
    despesa_origem_id = models.UUIDField(
        null=True,
        blank=True,
        help_text="FK lógica à despesa original (tipo=estorno — D-CT-3).",
    )
    acima_limite = models.BooleanField(
        default=False,
        help_text="Flag calculada: despesa acima do limite configurado (D-CT-9 — não bloqueia).",
    )
    motivo_rejeicao = models.TextField(
        blank=True,
        default="",
        help_text="Motivo da rejeição (obrigatório quando rejeitada).",
    )
    rejeitado_em = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Momento da rejeição.",
    )
    validado_em = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Momento da validação (WORM — trigger bloqueia UPDATE pós-validada).",
    )
    cancelado_em = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Momento do cancelamento (terminal).",
    )
    criado_em = models.DateTimeField(auto_now_add=True, db_index=True)
    revision = models.IntegerField(
        default=0,
        help_text="Contador de transições (OCC).",
    )

    class Meta:
        db_table = "despesa_caixa"
        verbose_name = "Despesa de Caixa"
        verbose_name_plural = "Despesas de Caixa"
        ordering = ["-data", "-criado_em"]
        indexes = [
            models.Index(
                fields=["tenant", "caixa", "estado"],
                name="ct_desp_caixa_estado_idx",
            ),
            models.Index(
                fields=["tenant", "data"],
                name="ct_desp_tenant_data_idx",
            ),
            models.Index(
                fields=["tenant", "os_id"],
                name="ct_desp_tenant_os_idx",
            ),
        ]

    def __str__(self) -> str:
        return f"DespesaCaixa({self.id} — {self.categoria}/{self.estado})"


class PrestacaoContasCaixa(models.Model):
    """Prestação de contas fechada (D-CT-8 / US-CT-010 / INV-CT-PRESTACAO-001).

    INSERT-only WORM pós-fechamento: trigger 0003 congela campos financeiros
    (total_adiantado, total_despesas_validadas, saldo_final, direcao, fechada_em)
    após INSERT — UPDATE nesses campos = RAISE.

    Período delimitado por ``periodo_de`` / ``periodo_ate`` (valor de
    ``Periodo`` achatado). Após fechamento, novos lançamentos no período
    são bloqueados (PeriodoPrestacaoFechado — domínio).

    # soft-delete-padrao: B -- INSERT-only WORM pós-fechamento (campos financeiros congelados)
    # fk-pii-anonimizavel: skip -- tecnico_referencia_hash + tecnico_key_id já implementam ADR-0032
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, serialize=False)
    tenant = models.ForeignKey(
        "tenant.tenant",
        on_delete=models.PROTECT,
        related_name="prestacoes_contas_caixa",
    )
    caixa = models.ForeignKey(
        CaixaTecnico,
        on_delete=models.PROTECT,
        related_name="prestacoes_contas",
    )
    tecnico_referencia_hash = models.CharField(
        max_length=80,
        help_text="HMAC do técnico — cópia imutável na trilha (ADR-0032).",
    )
    tecnico_key_id = models.CharField(
        max_length=10,
        help_text="Versão da chave HMAC (ADR-0064).",
    )
    # Periodo achatado (D-CT-8)
    periodo_de = models.DateField(
        help_text="Início do período coberto (Periodo.de achatado).",
    )
    periodo_ate = models.DateField(
        help_text="Fim do período coberto (Periodo.ate achatado).",
    )
    # campos financeiros — WORM pós-fechamento (trigger 0003)
    total_adiantado = models.BigIntegerField(
        help_text="Total de adiantamentos entregues no período (centavos). WORM pós-fechamento.",
    )
    total_despesas_validadas = models.BigIntegerField(
        help_text="Total de despesas validadas no período (centavos). WORM pós-fechamento.",
    )
    saldo_final = models.BigIntegerField(
        help_text="Saldo final = total_adiantado - total_despesas_validadas (centavos). WORM.",
    )
    direcao = models.CharField(
        max_length=20,
        choices=_choices(DirecaoPrestacao),
        help_text="Direção do saldo (D-CT-8). WORM pós-fechamento.",
    )
    fechada_em = models.DateTimeField(
        help_text="Momento do fechamento (WORM — trigger bloqueia sobrescrita).",
    )
    pdf_url = models.URLField(
        max_length=500,
        blank=True,
        default="",
        help_text="URL do PDF gerado (Fatia 3c — WeasyPrint).",
    )
    observacoes = models.TextField(
        blank=True,
        default="",
        help_text="Observações livres do gestor.",
    )
    criado_em = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = "prestacao_contas_caixa"
        verbose_name = "Prestação de Contas de Caixa"
        verbose_name_plural = "Prestações de Contas de Caixa"
        ordering = ["-fechada_em"]
        indexes = [
            models.Index(
                fields=["tenant", "caixa"],
                name="ct_prest_tenant_caixa_idx",
            ),
            models.Index(
                fields=["tenant", "periodo_de"],
                name="ct_prest_tenant_periodo_idx",
            ),
        ]

    def __str__(self) -> str:
        return f"PrestacaoContasCaixa({self.id} — {self.periodo_de}..{self.periodo_ate})"


class PoliticaCaixa(models.Model):
    """Política de caixa por tenant (D-CT-9 / US-CT-011).

    Configuração mutável: tarifa_km, prazo, exige_gps, limites por categoria,
    alçada de aprovação de adiantamentos.

    ``limite_por_categoria`` — JSON com {categoria: centavos}. NULL = sem limite.
    ``alcada_aprovacao``     — centavos; acima disso exige aprovação explícita.

    # soft-delete-padrao: C -- configuração mutável por tenant (sem deleção lógica)
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, serialize=False)
    tenant = models.ForeignKey(
        "tenant.tenant",
        on_delete=models.PROTECT,
        related_name="politicas_caixa",
    )
    tarifa_km = models.BigIntegerField(
        null=True,
        blank=True,
        help_text="Tarifa por km rodado em centavos (D-CT-9). NULL = km automático desabilitado.",
    )
    prazo_prestacao_dias = models.IntegerField(
        default=30,
        help_text="Prazo máximo para fechar prestação (dias). Default 30.",
    )
    exige_gps = models.BooleanField(
        default=False,
        help_text="Tenant exige GPS nas despesas de deslocamento (D-CT-6 / D-CT-9).",
    )
    limite_por_categoria = models.JSONField(
        null=True,
        blank=True,
        help_text="Mapa {categoria: centavos} de limite por categoria. NULL = sem limite (D-CT-9).",
    )
    alcada_aprovacao = models.BigIntegerField(
        null=True,
        blank=True,
        help_text="Centavos; adiantamentos acima disso exigem aprovação explícita (D-CT-7/D-CT-9).",
    )
    criado_em = models.DateTimeField(auto_now_add=True, db_index=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "politica_caixa"
        verbose_name = "Política de Caixa"
        verbose_name_plural = "Políticas de Caixa"
        ordering = ["-criado_em"]
        indexes = [
            models.Index(
                fields=["tenant"],
                name="ct_pol_tenant_idx",
            ),
        ]

    def __str__(self) -> str:
        return f"PoliticaCaixa({self.id} — tenant={self.tenant_id})"


class ConsentimentoGpsColaborador(models.Model):
    """Opt-in GPS do colaborador — INSERT-com-vigência, append-only (D-CT-6).

    NUNCA atualizado pela IA. Só RH/colaborador via fluxo próprio (ADV-CT-06).
    A linha vigente é a com maior ``vigencia_inicio`` ≤ data_consulta
    sem ``revogado_em`` preenchido.

    ``colaborador_referencia_hash`` + ``colaborador_key_id`` — ADR-0032:
    FK lógica anonimizável ao colaborador (PII).

    Vigência canônica (ADR-0030):
      - ``vigencia_inicio``: início da vigência do consentimento.
      - ``revogado_em``: one-shot revogação (sem re-ativação na mesma linha).
    Tabela achatada SQL; a entidade de domínio encapsula a lógica via
    ``ConsentimentoGpsColaborador.esta_vigente``.
    # vigencia-canonica: skip -- tabela achatada SQL; domínio encapsula via ConsentimentoGpsColaborador.esta_vigente (D-CT-6/ADR-0030)

    # soft-delete-padrao: B -- append-only INSERT-with-vigencia; revogado_em one-shot
    # fk-pii-anonimizavel: skip -- colaborador_referencia_hash + colaborador_key_id já implementam ADR-0032
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, serialize=False)
    tenant = models.ForeignKey(
        "tenant.tenant",
        on_delete=models.PROTECT,
        related_name="consentimentos_gps_colaborador",
    )
    colaborador_referencia_hash = models.CharField(
        max_length=80,
        help_text="HMAC do colaborador — pseudônimo na trilha (ADR-0032). Imutável, NOT NULL.",
    )
    colaborador_key_id = models.CharField(
        max_length=10,
        help_text="Versão da chave HMAC (ADR-0064).",
    )
    vigencia_inicio = models.DateTimeField(
        help_text="Início da vigência do consentimento GPS (ADR-0030).",
    )
    revogado_em = models.DateTimeField(
        null=True,
        blank=True,
        help_text=(
            "Momento da revogação do consentimento (one-shot — sem re-ativação nesta linha). "
            "Vigência canônica ADR-0030."
        ),
    )
    motivo_revogacao = models.TextField(
        blank=True,
        default="",
        help_text="Motivo da revogação (LGPD — recomendado ≥10 chars).",
    )
    criado_em = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = "consentimento_gps_colaborador"
        verbose_name = "Consentimento GPS do Colaborador"
        verbose_name_plural = "Consentimentos GPS dos Colaboradores"
        ordering = ["-vigencia_inicio"]
        indexes = [
            models.Index(
                fields=["tenant", "colaborador_referencia_hash", "vigencia_inicio"],
                name="ct_cgps_tenant_col_vig_idx",
            ),
        ]

    def __str__(self) -> str:
        return f"ConsentimentoGpsColaborador({self.id} — vigente_desde={self.vigencia_inicio})"
