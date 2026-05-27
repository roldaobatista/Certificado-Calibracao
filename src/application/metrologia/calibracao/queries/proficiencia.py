"""T-CAL-110 — ProficienciaPainelQueryService.

Painel de rodadas de Ensaio de Proficiencia (PT/EP) — cl. 7.7.2 + RBC P-CAL-R8.
Agrega rodadas + escore z + impacto NC por rodada.

Budget de performance: <= 500ms na implementacao Django (Fase 8).

Como `RodadaProficiencia` ainda nao tem snapshot canonico em entities.py
(use case `registrarIntercomparacao` US-CAL-014 entregue em Fase 5 Batch
posterior; entidade vai migrar pra entities.py quando o adapter aparecer),
declaramos dataclass local.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from src.domain.metrologia.calibracao.value_objects import (
    ClassificacaoZ,
    EscoreZ,
)


@dataclass(frozen=True, slots=True)
class RodadaProficienciaSnapshot:
    """Snapshot enxuto de RodadaProficiencia para painel."""

    id: UUID
    tenant_id: UUID
    provedor: str  # INMETRO, NMI, IPEM, ABNT, ...
    rodada_referencia: str  # codigo do provedor
    grandeza: str
    valor_atribuido: Decimal
    valor_reportado: Decimal
    incerteza_reportada: Decimal
    incerteza_atribuida: Decimal
    escore_z: Decimal  # calculado pelo use case registrar_intercomparacao
    classificacao_z: ClassificacaoZ
    rodada_em: datetime
    correlation_id: UUID


@dataclass(frozen=True, slots=True)
class ImpactoNCProficienciaSnapshot:
    """Janela de impacto + status (NC ou plano warning)."""

    id: UUID
    tenant_id: UUID
    rodada_id: UUID  # FK RodadaProficiencia
    janela_inicio: datetime
    janela_fim: datetime
    status: str  # 'EM_ANALISE' | 'RECALL_PENDENTE_M5' | 'CONCLUIDO_SEM_RECALL'
    qtde_certificados_afetados: int


@dataclass(frozen=True, slots=True)
class LinhaPainelProficiencia:
    """Linha consolidada (rodada + impacto eventual)."""

    rodada_id: UUID
    tenant_id: UUID
    provedor: str
    rodada_referencia: str
    grandeza: str
    escore_z: Decimal
    classificacao_z: ClassificacaoZ
    rodada_em: datetime
    impacto_status: str | None  # None se sem impacto registrado
    impacto_qtde_certificados: int  # 0 se sem impacto


@dataclass(frozen=True, slots=True)
class PainelProficiencia:
    """Resultado consolidado do painel."""

    linhas: tuple[LinhaPainelProficiencia, ...]
    total_aceitavel: int  # |z| <= 2
    total_warning: int  # 2 < |z| <= 3
    total_unacceptable: int  # |z| > 3
    total_com_impacto_aberto: int

    @property
    def total(self) -> int:
        return len(self.linhas)


def executar(
    *,
    rodadas: list[RodadaProficienciaSnapshot],
    impactos: list[ImpactoNCProficienciaSnapshot] | None = None,
    tenant_id: UUID | None = None,
    grandeza: str | None = None,
) -> PainelProficiencia:
    """Painel de proficiencia + classificacao + impacto NC.

    Args:
      rodadas: snapshots ja carregados.
      impactos: snapshots de impacto (None => sem cruzamento).
      tenant_id: filtro defensivo.
      grandeza: caso-insensitivo, opcional.

    Returns:
      PainelProficiencia ordenado por rodada_em DESC.
    """
    impactos = impactos or []
    grandeza_norm = grandeza.lower().strip() if grandeza else None

    rodadas_filtradas = [
        r
        for r in rodadas
        if (tenant_id is None or r.tenant_id == tenant_id)
        and (grandeza_norm is None or r.grandeza.lower() == grandeza_norm)
    ]
    rodadas_filtradas.sort(key=lambda r: r.rodada_em, reverse=True)

    # Indexa impactos por rodada_id (1 rodada -> 0..1 impacto ativo)
    impacto_por_rodada: dict[UUID, ImpactoNCProficienciaSnapshot] = {}
    for imp in impactos:
        if tenant_id is not None and imp.tenant_id != tenant_id:
            continue
        atual = impacto_por_rodada.get(imp.rodada_id)
        # mantem o ultimo (caso 1:N exista, prevalece o mais recente
        # janela_fim ou ativo)
        if atual is None or imp.janela_fim > atual.janela_fim:
            impacto_por_rodada[imp.rodada_id] = imp

    linhas: list[LinhaPainelProficiencia] = []
    total_aceitavel = 0
    total_warning = 0
    total_unacceptable = 0
    total_impacto_aberto = 0
    for r in rodadas_filtradas:
        imp_assoc = impacto_por_rodada.get(r.id)
        impacto_status = imp_assoc.status if imp_assoc is not None else None
        impacto_qtde = (
            imp_assoc.qtde_certificados_afetados if imp_assoc is not None else 0
        )
        if impacto_status == "RECALL_PENDENTE_M5":
            total_impacto_aberto += 1

        if r.classificacao_z == ClassificacaoZ.ACEITAVEL:
            total_aceitavel += 1
        elif r.classificacao_z == ClassificacaoZ.WARNING:
            total_warning += 1
        elif r.classificacao_z == ClassificacaoZ.UNACCEPTABLE:
            total_unacceptable += 1

        linhas.append(
            LinhaPainelProficiencia(
                rodada_id=r.id,
                tenant_id=r.tenant_id,
                provedor=r.provedor,
                rodada_referencia=r.rodada_referencia,
                grandeza=r.grandeza,
                escore_z=r.escore_z,
                classificacao_z=r.classificacao_z,
                rodada_em=r.rodada_em,
                impacto_status=impacto_status,
                impacto_qtde_certificados=impacto_qtde,
            )
        )

    return PainelProficiencia(
        linhas=tuple(linhas),
        total_aceitavel=total_aceitavel,
        total_warning=total_warning,
        total_unacceptable=total_unacceptable,
        total_com_impacto_aberto=total_impacto_aberto,
    )


__all__ = [
    "EscoreZ",
    "ImpactoNCProficienciaSnapshot",
    "LinhaPainelProficiencia",
    "PainelProficiencia",
    "RodadaProficienciaSnapshot",
    "executar",
]
