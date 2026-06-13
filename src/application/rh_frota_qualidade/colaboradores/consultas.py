"""Use cases de consulta — elegíveis e comissão vigente (T-COL-033).

consultar_elegiveis — DTO allowlist mínimo (INV-COL-ELEGIVEIS-MINIMO):
                      colaborador_id, nome_exibicao, papel, habilidades, ativo.
                      Filtra no banco (só ativos com papel + habilidade).
                      NUNCA PII fora da allowlist (ADV-COL-04 / Risco 3).

comissao_vigente    — {pct_default, vigente_desde} (D-COL-9 / AC-COL-04).

Refs: AC-COL-02/04/05; D-COL-7/9; INV-COL-ELEGIVEIS-MINIMO; ADV-COL-04.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from uuid import UUID

from src.domain.rh_frota_qualidade.colaboradores.enums import (
    NivelHabilidade,
    PapelColaborador,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# DTOs allowlist (INV-COL-ELEGIVEIS-MINIMO)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class HabilidadeElegivelDTO:
    """Habilidade mínima para o DTO de elegível (sem PII)."""

    nivel: NivelHabilidade
    descricao: str  # codigo do catálogo OU descricao_livre


@dataclass(frozen=True)
class ElegivelDTO:
    """DTO mínimo para /elegiveis (INV-COL-ELEGIVEIS-MINIMO / ADV-COL-04).

    Allowlist fechada: NUNCA CPF/e-mail/telefone/documentos/comissão/foto/
    vínculo/observação fora deste DTO (Risco 3 / spec §7).
    """

    colaborador_id: UUID
    nome_exibicao: str
    papel: PapelColaborador | None  # None se sem papel ativo
    habilidades: list[HabilidadeElegivelDTO]
    ativo: bool


@dataclass(frozen=True)
class ComissaoVigenteDTO:
    """Resultado de comissao_vigente (D-COL-9 / AC-COL-04)."""

    pct_default: Decimal
    vigente_desde: date  # = data_admissao (ponto de origem do percentual default)


# ---------------------------------------------------------------------------
# Use cases
# ---------------------------------------------------------------------------


def consultar_elegiveis(
    *,
    tenant_id: UUID,
    papel: PapelColaborador | None = None,
    habilidade_codigo: str | None = None,
) -> list[ElegivelDTO]:
    """Retorna colaboradores ativos elegíveis (AC-COL-02/05 / D-COL-7).

    Filtra diretamente no banco (anti-N+1). Retorna DTO allowlist — NUNCA
    CPF/e-mail/telefone/documentos/comissão/foto/vínculo/observação
    (INV-COL-ELEGIVEIS-MINIMO / ADV-COL-04 / Risco 3).

    Args:
        tenant_id:        UUID do tenant (RLS contexto).
        papel:            Filtra por papel ativo (opcional).
        habilidade_codigo: Filtra por código do catálogo (opcional).

    Returns:
        Lista de ElegivelDTO (vazia se nenhum elegível).
    """
    from django.db.models import Prefetch

    from src.infrastructure.colaboradores.models import (
        Colaborador as ColaboradorModel,
    )
    from src.infrastructure.colaboradores.models import (
        ColaboradorHabilidade as HabModel,
    )
    from src.infrastructure.colaboradores.models import (
        ColaboradorPapel as PapelModel,
    )

    # Prefetch papéis e habilidades em batch (anti-N+1 / TL-COL-12)
    qs = (
        ColaboradorModel.ativos.filter(tenant_id=tenant_id)
        .prefetch_related(
            Prefetch(
                "papeis",
                queryset=PapelModel.objects.filter(
                    data_fim__isnull=True,
                    revogado_em__isnull=True,
                ),
                to_attr="_papeis_ativos",
            ),
            Prefetch(
                "habilidades",
                queryset=HabModel.objects.select_related("catalogo"),
                to_attr="_habilidades_lista",
            ),
        )
    )

    if papel is not None:
        qs = qs.filter(
            papeis__papel=papel.value,
            papeis__data_fim__isnull=True,
            papeis__revogado_em__isnull=True,
        ).distinct()

    if habilidade_codigo is not None:
        qs = qs.filter(habilidades__catalogo_id=habilidade_codigo).distinct()

    resultado: list[ElegivelDTO] = []
    for colab in qs:
        papeis_ativos: list[PapelModel] = getattr(colab, "_papeis_ativos", [])
        habilidades_lista: list[HabModel] = getattr(colab, "_habilidades_lista", [])

        papel_principal: PapelColaborador | None = None
        if papeis_ativos:
            from src.domain.rh_frota_qualidade.colaboradores.enums import PapelColaborador
            papel_principal = PapelColaborador(papeis_ativos[0].papel)

        habilidades_dto = [
            HabilidadeElegivelDTO(
                nivel=NivelHabilidade(h.nivel),
                descricao=str(h.catalogo_id) if h.catalogo_id else (h.descricao_livre or ""),
            )
            for h in habilidades_lista
        ]

        resultado.append(
            ElegivelDTO(
                colaborador_id=colab.id,
                nome_exibicao=colab.nome,
                papel=papel_principal,
                habilidades=habilidades_dto,
                ativo=True,
            )
        )

    return resultado


def comissao_vigente(
    *,
    tenant_id: UUID,
    colaborador_id: UUID,
) -> ComissaoVigenteDTO | None:
    """Retorna percentual de comissão default e data de vigência (D-COL-9 / AC-COL-04).

    `vigente_desde` = data_admissao (origem do percentual default).
    Override por OS e cálculo pertencem ao módulo `comissoes` (D-COL-9).

    Returns:
        ComissaoVigenteDTO ou None se colaborador não encontrado.
    """
    from src.infrastructure.colaboradores.models import Colaborador as ColaboradorModel

    colab = (
        ColaboradorModel.objects.filter(
            tenant_id=tenant_id, id=colaborador_id
        )
        .only("comissao_default_pct", "data_admissao")
        .first()
    )
    if colab is None:
        return None

    return ComissaoVigenteDTO(
        pct_default=colab.comissao_default_pct,
        vigente_desde=colab.data_admissao,
    )
