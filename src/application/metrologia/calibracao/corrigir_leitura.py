"""Use case `corrigir_leitura` — rasura digital cl. 7.5 (P4 Fase 5 Batch D — T-CAL-088).

INSERT em LeituraCorrecao preservando valor_original da Leitura.
NAO muta a Leitura (INV-CAL-WORM-001).

Estados permitidos da Calibracao (AC-CAL-004-7):
  - CONFIGURADA (raro mas possivel — corrige antes de iniciar leituras
    se houver Leitura criada em rascunho via outro caminho).
  - EM_EXECUCAO (caminho normal — corrige enquanto registra leituras).

Estados que recusam (apos revisao):
  - EM_REVISAO_1, AGUARDANDO_2A_CONFERENCIA, APROVADA, REJEITADA, etc.
  - Apos EM_REVISAO_1 a correcao exige reabertura formal via CAPA
    (gera NaoConformidade — fluxo de marcar_nao_conformidade).

INV-CAL-FRAUDE-COR-001: caller valida que corretor_id_hash bate com
HashVersionado(request.user.id). Use case nao faz essa validacao
diretamente — recebe hash pronto.

Regras (validadas em __post_init__ do Input):
- valor_corrigido != valor_original (sem rasura inocua).
- razao_correcao_canonicalizada >= 30 chars (cl. 7.5 exige justificativa
  substancial).
- razao_correcao_hash + corretor_id_hash nao vazios (ADR-0064).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4

from src.domain.metrologia.calibracao.entities import LeituraCorrecaoSnapshot
from src.domain.metrologia.calibracao.enums import EstadoCalibracao
from src.domain.metrologia.calibracao.repository import (
    CalibracaoRepository,
    LeituraCorrecaoRepository,
    LeituraRepository,
)

# Estados em que correcao eh permitida (AC-CAL-004-7).
_ESTADOS_CORRECAO_PERMITIDA: frozenset[EstadoCalibracao] = frozenset({
    EstadoCalibracao.CONFIGURADA,
    EstadoCalibracao.EM_EXECUCAO,
})

# Razao minima cl. 7.5 — auditoria CGCRE exige justificativa substancial.
_MIN_CHARS_RAZAO = 30


class LeituraNaoEncontrada(Exception):
    """leitura_id nao existe no tenant ativo (RLS filtrou)."""


class CalibracaoEstadoNaoPermiteCorrigir(Exception):
    """Calibracao em estado pos-revisao — caller orienta abrir NC formal."""


@dataclass(frozen=True, slots=True)
class CorrigirLeituraInput:
    """Payload de correcao (cl. 7.5 rasura digital)."""

    leitura_id: UUID
    valor_corrigido: Decimal
    razao_correcao_canonicalizada: str
    razao_correcao_hash: str
    corretor_id_hash: str  # caller calcula = HashVersionado(request.user.id)
    corrigido_em: datetime  # UTC-aware
    correlation_id: UUID

    def __post_init__(self) -> None:
        if not isinstance(self.valor_corrigido, Decimal):
            raise TypeError(
                f"corrigir_leitura: valor_corrigido deve ser Decimal "
                f"(achou {type(self.valor_corrigido).__name__}) — INV-CAL-INC-003"
            )
        if len(self.razao_correcao_canonicalizada) < _MIN_CHARS_RAZAO:
            raise ValueError(
                f"corrigir_leitura: razao_correcao precisa >= {_MIN_CHARS_RAZAO} "
                f"chars (cl. 7.5 ISO 17025); achou "
                f"{len(self.razao_correcao_canonicalizada)}"
            )
        if not self.razao_correcao_hash:
            raise ValueError(
                "corrigir_leitura: razao_correcao_hash obrigatorio "
                "(INV-DOC-CANON-001 + ADR-0064)"
            )
        if not self.corretor_id_hash:
            raise ValueError(
                "corrigir_leitura: corretor_id_hash obrigatorio "
                "(INV-CAL-FRAUDE-COR-001 + ADR-0064)"
            )
        if self.corrigido_em.tzinfo is None:
            raise ValueError(
                "corrigir_leitura: corrigido_em exige datetime tz-aware "
                "(INV-VIG-004)"
            )


@dataclass(frozen=True, slots=True)
class CorrigirLeituraOutput:
    snapshot: LeituraCorrecaoSnapshot


def executar(
    inp: CorrigirLeituraInput,
    calibracao_repo: CalibracaoRepository,
    leitura_repo: LeituraRepository,
    correcao_repo: LeituraCorrecaoRepository,
) -> CorrigirLeituraOutput:
    """Aplica rasura digital sobre uma Leitura, preservando valor_original.

    Levanta:
      LeituraNaoEncontrada — leitura_id invalido OU cross-tenant.
      CalibracaoEstadoNaoPermiteCorrigir — calibracao em estado >=
        EM_REVISAO_1 (caller orienta abrir NC formal).
      ValueError — valor_corrigido == valor_original (rasura inocua
        proibida — INV-CAL-WORM-001).
    """
    leitura = leitura_repo.obter_por_id(inp.leitura_id)
    if leitura is None:
        raise LeituraNaoEncontrada(str(inp.leitura_id))

    if leitura.valor_lido == inp.valor_corrigido:
        raise ValueError(
            "corrigir_leitura: valor_corrigido == valor_original — rasura "
            "inocua proibida (INV-CAL-WORM-001)"
        )

    calibracao = calibracao_repo.obter_por_id(leitura.calibracao_id)
    if calibracao is None:
        # Defensivo: leitura existe mas calibracao sumiu (cenario raro)
        raise LeituraNaoEncontrada(
            f"calibracao_id={leitura.calibracao_id} nao encontrada"
        )

    if calibracao.status not in _ESTADOS_CORRECAO_PERMITIDA:
        raise CalibracaoEstadoNaoPermiteCorrigir(
            f"status atual={calibracao.status.value}; corrigir_leitura exige "
            f"status IN {sorted(s.value for s in _ESTADOS_CORRECAO_PERMITIDA)} "
            f"(AC-CAL-004-7). Apos revisao, abra NC formal via marcar_nc."
        )

    snapshot = LeituraCorrecaoSnapshot(
        id=uuid4(),
        tenant_id=leitura.tenant_id,
        leitura_id=leitura.id,
        valor_original=leitura.valor_lido,  # snapshot ANTES da rasura
        valor_corrigido=inp.valor_corrigido,
        razao_correcao_canonicalizada=inp.razao_correcao_canonicalizada,
        razao_correcao_hash=inp.razao_correcao_hash,
        corretor_id_hash=inp.corretor_id_hash,
        corrigido_em=inp.corrigido_em,
        correlation_id=inp.correlation_id,
    )

    correcao_repo.salvar_nova(snapshot)
    return CorrigirLeituraOutput(snapshot=snapshot)
