"""Entidades persistíveis do domínio caixa_tecnico (Fatia 1a — T-CT-011).

Todos ``frozen + slots`` (imutáveis em memória — molde contas_receber/entities.py).
Todo valor monetário usa ``Dinheiro`` (centavos) — nunca int/Decimal solto.

``Despesa.__post_init__``: valida ``foto_hash is not None`` → ``FotoComprovanteObrigatoria``
(INV-CT-FOTO-001 / D-CT-4).

A LÓGICA de transições vive em ``transicoes_despesa.py`` e ``transicoes_adiantamento.py``
(domínio puro — ADR-0007). A TABELA física e triggers vivem em
``infrastructure/caixa_tecnico/`` (Fatia 1b).

Refs: D-CT-2/3/4/6/7/8/9/11; spec §4.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from uuid import UUID

from src.domain.shared.value_objects import Dinheiro, ReferenciaPIIAnonimizavel

from .enums import (
    CategoriaDespesa,
    DirecaoPrestacao,
    EstadoAdiantamento,
    EstadoDespesa,
    MeioEntrega,
    TipoDespesa,
)
from .erros import FotoComprovanteObrigatoria
from .value_objects import Coordenada, Periodo


@dataclass(frozen=True, slots=True)
class CaixaTecnico:
    """Raiz do agregado por técnico — 1 por ``(tenant_id, tecnico_id)`` (D-CT-2).

    ``desligado_em`` preenchido pelo consumer ``colaborador.desligado``
    (fail-closed — D-CT-11 / T-CT-050). Novo lançamento em caixa desligado
    levanta ``CaixaTecnicoDesligado`` (409) na camada de aplicação.

    ``revision`` para controle de concorrência otimista (molde fiscal).
    """

    caixa_id: UUID
    tenant_id: UUID
    tecnico_referencia: ReferenciaPIIAnonimizavel  # ADR-0032 — colaborador-scoped
    criado_em: datetime
    revision: int
    # fail-closed do consumer colaborador.desligado (D-CT-11)
    desligado_em: datetime | None = None

    @property
    def esta_desligado(self) -> bool:
        """True se o técnico foi desligado e o caixa está bloqueado para novos lançamentos."""
        return self.desligado_em is not None


@dataclass(frozen=True, slots=True)
class Adiantamento:
    """Adiantamento financeiro ao técnico (D-CT-7 / US-CT-001).

    Máquina de estados: solicitado→aprovado→entregue; solicitado→recusado/cancelado.
    ``entregue`` é terminal — ``AdiantamentoNaoCancelavel`` (422) se tentativa de cancelar.
    Alçada: ``Politica.alcada_aprovacao`` validada server-side no use case.
    Liberação PIX manual Wave A (automática Wave B — ADR-0050).
    """

    adiantamento_id: UUID
    tenant_id: UUID
    caixa_id: UUID
    tecnico_referencia: ReferenciaPIIAnonimizavel
    valor: Dinheiro
    estado: EstadoAdiantamento
    meio: MeioEntrega
    solicitado_em: datetime
    criado_em: datetime
    revision: int
    # Campos opcionais
    aprovado_em: datetime | None = None
    entregue_em: datetime | None = None
    recusado_em: datetime | None = None
    cancelado_em: datetime | None = None
    motivo_recusa: str | None = None  # ≥30 chars (validado no use case)
    justificativa: str | None = None  # ≥30 chars (validado no use case)
    aprovado_por_id: UUID | None = None
    entregue_por_id: UUID | None = None


@dataclass(frozen=True, slots=True)
class Despesa:
    """Despesa do técnico de campo — agregado raiz (D-CT-3/4 / US-CT-002).

    ``foto_hash`` OBRIGATÓRIO — ``FotoComprovanteObrigatoria`` (412) levantada no
    ``__post_init__`` (INV-CT-FOTO-001). Sem foto = sem despesa.

    Campos GPS (``coordenada``) preenchidos SOMENTE via opt-in server-side
    (``ConsentimentoGpsPort``) — nunca do payload nem do EXIF (D-CT-6 / INV-LGPD-CONSENT-001).

    ``client_offline_id`` — UUID4 gerado pelo app para idempotência batch (D-CT-5).
    ``os_id`` — vínculo opcional com OS; validado on-write via ``OSReferenciaPort``.
    ``tipo=estorno`` — correção de despesa validada imutável (nova despesa, nunca UPDATE).
    ``acima_limite`` — flag não-bloqueante (financeiro vê na fila — D-CT-9).
    """

    despesa_id: UUID
    tenant_id: UUID
    caixa_id: UUID
    tecnico_referencia: ReferenciaPIIAnonimizavel
    categoria: CategoriaDespesa
    tipo: TipoDespesa
    valor: Dinheiro
    estado: EstadoDespesa
    foto_hash: str  # HMAC-SHA256(bytes_pós-strip, chave_tenant) — NOT NULL
    foto_url: str  # URL content-addressed — NOT NULL
    data: date
    criado_em: datetime
    revision: int
    # Campos opcionais
    descricao: str | None = None
    km_percorridos: int | None = None  # categoria=deslocamento
    coordenada: Coordenada | None = None  # GPS opt-in (retenção curta)
    gps_referencia_pii: ReferenciaPIIAnonimizavel | None = None  # crypto-shredding GPS
    os_id: UUID | None = None  # seam OS (D-CT-11)
    client_offline_id: str | None = None  # UUID4 app — dedup batch (D-CT-5)
    despesa_origem_id: UUID | None = None  # tipo=estorno → despesa que está sendo corrigida
    acima_limite: bool = False  # flag não-bloqueante (D-CT-9)
    motivo_rejeicao: str | None = None  # ≥30 chars, preenchido no rejeitar
    rejeitado_em: datetime | None = None
    validado_em: datetime | None = None
    cancelado_em: datetime | None = None

    def __post_init__(self) -> None:
        # INV-CT-FOTO-001: foto_hash obrigatório
        if not self.foto_hash:
            raise FotoComprovanteObrigatoria(
                "Despesa exige foto_hash — lançamento sem foto-comprovante é proibido "
                "(INV-CT-FOTO-001 / D-CT-4)"
            )


@dataclass(frozen=True, slots=True)
class PrestacaoContas:
    """Prestação de contas do período — WORM conceitual (D-CT-8 / INV-CT-PRESTACAO-001).

    Campos financeiros congelados pós-fecha: ``total_adiantado``, ``total_despesas_validadas``,
    ``saldo_final``, ``direcao``, ``fechada_em`` — trigger PG bloqueia UPDATE nesses campos (Fatia 1b).

    Saldo = ``total_adiantado - total_despesas_validadas`` (D-CT-2 / INV-CT-SALDO-001).
    ``direcao=tenant_deve`` = estado consultável — sem execução de reembolso Wave A
    (GATE-CT-CONTAS-PAGAR). Evento ``caixa_tecnico.prestacao.fechada`` publicado no outbox.
    """

    prestacao_id: UUID
    tenant_id: UUID
    caixa_id: UUID
    tecnico_referencia: ReferenciaPIIAnonimizavel
    periodo: Periodo
    total_adiantado: Dinheiro  # Σ adiantamentos ENTREGUES no período
    total_despesas_validadas: Dinheiro  # Σ despesas VALIDADAS no período
    saldo_final: Dinheiro  # total_adiantado - total_despesas_validadas
    direcao: DirecaoPrestacao  # derivado do saldo_final
    fechada_em: datetime
    criado_em: datetime
    # Campos opcionais
    pdf_url: str | None = None  # gerado sob demanda (WeasyPrint — D-CT-8 / Fatia 3c)
    observacoes: str | None = None


@dataclass(frozen=True, slots=True)
class Politica:
    """Política financeira do caixa do técnico por tenant (D-CT-9).

    ``limite_por_categoria`` — dict CategoriaDespesa → Dinheiro (limite não-bloqueante).
    ``alcada_aprovacao`` — dict papel → Dinheiro (limite de aprovação por papel — D-CT-7).
    ``tarifa_km`` — valor por km para categoria ``deslocamento`` (D-CT-9).
    ``exige_gps`` — tenant exige coordenada GPS nas despesas de campo (D-CT-6).
    ``prazo_prestacao_dias`` — dias para prestação de contas após encerramento do mês (default 30).
    """

    politica_id: UUID
    tenant_id: UUID
    tarifa_km: Dinheiro  # centavos por km
    prazo_prestacao_dias: int = 30
    exige_gps: bool = False
    limite_por_categoria: dict[str, int] | None = None  # CategoriaDespesa.value → centavos
    alcada_aprovacao: dict[str, int] | None = None  # papel → centavos


@dataclass(frozen=True, slots=True)
class ConsentimentoGpsColaborador:
    """Opt-in GPS do colaborador — colaborador-scoped, INSERT-com-vigência (D-CT-6).

    Registro append-only: cada opt-in/revogação é um novo registro com
    ``vigencia_inicio`` e ``revogado_em`` (oposição — art. 18 §2º LGPD).

    Exposta via ``ConsentimentoGpsPort`` — desenhada para promoção a ``shared``
    quando o app-tecnico (N6) nascer (spec §8 ação P3.2).

    IA NUNCA grava opt-in — apenas o fluxo de RH/colaborador (ADV-CT-06).
    Retenção: fechamento da prestação + 90 dias (máx. 6-12m) — D-CT-6.
    """

    consentimento_id: UUID
    tenant_id: UUID
    colaborador_referencia: ReferenciaPIIAnonimizavel
    vigencia_inicio: datetime  # INSERT-com-vigência (RLS v2)
    criado_em: datetime
    # Revogação
    revogado_em: datetime | None = None  # oposição append-only (art. 18 §2º)
    motivo_revogacao: str | None = None

    @property
    def esta_vigente(self) -> bool:
        """True se o consentimento está ativo (não revogado)."""
        return self.revogado_em is None
