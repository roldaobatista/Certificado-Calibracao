"""Entidades persistíveis do domínio contas-receber (Fatia 1a — T-CR-011).

Agregado raiz `Titulo` (= "ContasReceber" do PRD) + filhos `Parcela`, `Pagamento`,
`OverrideBloqueio`. Todos `frozen + slots` (imutáveis em memória — D-CR-2).

Todo valor monetário usa `Dinheiro` (centavos) — NUNCA int/Decimal solto (lição
de orçamentos; R9). `ReferenciaPIIAnonimizavel` de `shared` para o cliente (D-CR-16).

A LÓGICA de transições vive em `transicoes.py` (domínio puro, ADR-0007/0072);
a TABELA física e os triggers vivem em `infrastructure/contas_receber/` (Fatia 1b).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from uuid import UUID

from src.domain.shared.value_objects import Dinheiro, ReferenciaPIIAnonimizavel

from .enums import (
    CategoriaReceita,
    EstadoTitulo,
    MeioCobranca,
    OrigemPagamento,
    OrigemTitulo,
)


@dataclass(frozen=True, slots=True)
class Titulo:
    """Título a receber — agregado raiz (D-CR-2 / spec §4).

    Idempotência de negócio:
      - Por `(tenant_id, os_id_origem) WHERE estado != cancelado` para títulos de OS
        (INV-CR-OS-TITULO-UNICO / R6).
      - `perfil_no_evento` imutável (CHAR(1) — cravado no INSERT — D-CR-6 /
        INV-FIN-SNAPSHOT-PERFIL-001).
      - `cliente_referencia` = `ReferenciaPIIAnonimizavel` (ADR-0032 / D-CR-16).

    Campos de cobrança (gateway):
      - `gateway_externo_id NOT NULL` ⟺ cobrança emitida (derivado — não é estado).
      - `convenio_pix_id NOT NULL` obrigatório se `meio=pix_recorrente` (INV-FIN-GW-002).

    `revision` para OCC (controle de concorrência otimista — molde fiscal).
    """

    titulo_id: UUID
    tenant_id: UUID
    cliente_referencia: ReferenciaPIIAnonimizavel  # hash + key_id (D-CR-16)
    valor_original: Dinheiro  # sempre centavos
    data_emissao: date
    data_vencimento: date
    estado: EstadoTitulo
    meio: MeioCobranca
    categoria_receita: CategoriaReceita
    perfil_no_evento: str  # CHAR(1): A/B/C/D — snapshot imutável (D-CR-6)
    origem: OrigemTitulo
    revision: int
    criado_em: datetime
    # Campos opcionais
    data_baixa: date | None = None
    os_id_origem: UUID | None = None
    nfse_id_origem: UUID | None = None
    gateway_externo_id: str | None = None
    convenio_pix_id: str | None = None  # NOT NULL se meio=pix_recorrente
    linha_digitavel: str | None = None
    qr_code: str | None = None
    tx_id: str | None = None
    desconto_pontualidade_pct: int | None = None  # percentual em bps (0-10000)
    numero_sequencial_tenant: int | None = None  # GAP_LESS se exigência contábil (D-CR-18)

    @property
    def e_terminal(self) -> bool:
        """Título pago ou cancelado não aceita mais transições."""
        return self.estado in (EstadoTitulo.PAGO, EstadoTitulo.CANCELADO)

    @property
    def cobranca_emitida(self) -> bool:
        """Derivado de `gateway_externo_id NOT NULL` (não é estado — D-CR-3)."""
        return self.gateway_externo_id is not None


@dataclass(frozen=True, slots=True)
class Parcela:
    """Sub-entidade de parcelamento simples (D-CR-15).

    N parcelas iguais emitidas junto com o título.
    Baixa parcial com título sucessor = Wave B.
    """

    parcela_id: UUID
    titulo_id: UUID
    numero: int  # 1-based
    valor: Dinheiro  # centavos
    vencimento: date
    status: str  # "aberta" | "paga" | "cancelada" — sem enum próprio para simplicidade


@dataclass(frozen=True, slots=True)
class Pagamento:
    """Evento de pagamento INSERT-only (INV-CR-PAGAMENTO-WORM / D-CR-8).

    Imutável na tabela física via trigger block-update/delete (Fatia 1b).
    `valor_atualizado_snapshot_em_pagamento` = snapshot de M-FIN-002 (valor com
    juros/multa no momento da baixa, calculado por `calcular_valor_atualizado`).
    `gateway_event_id` para idempotência de webhook (INV-FIN-GW-001 / R10).
    """

    pagamento_id: UUID
    titulo_id: UUID
    valor: Dinheiro  # valor efetivamente pago (centavos)
    data: date
    origem: OrigemPagamento
    valor_atualizado_snapshot_em_pagamento: Dinheiro  # snapshot com juros/multa
    criado_em: datetime
    gateway_event_id: str | None = None  # idempotência webhook
    comprovante_url: str | None = None


@dataclass(frozen=True, slots=True)
class OverrideBloqueio:
    """Override de bloqueio de inadimplência — WORM Padrão B (INSERT-only) (D-CR-10).

    Exige papel `gerente_financeiro`/`admin_tenant`.
    `justificativa` ≥100 chars + filtro anti-PII (INV-CR-OVERRIDE-ANTI-PII / D-CR-20).
    `novo_prazo_max_dias` ≤90 (AC-CR-010-5).
    `a3_signature_id` = referência Wave A (A3 real = GATE-CR-A3).
    Limite 5%/mês dos bloqueios por tenant (R-CR-NOVO-4 / ADR-0043 §3).
    """

    override_id: UUID
    titulo_id: UUID
    cliente_id: UUID  # id concreto do cliente no momento (não hash)
    novo_prazo_max_dias: int  # ≤90
    justificativa: str  # ≥100 chars, anti-PII
    a3_signature_id: str  # ref Wave A (sem verificação real — GATE-CR-A3)
    usuario_id: UUID
    perfil_no_evento: str  # CHAR(1) snapshot (D-CR-6)
    criado_em: datetime
