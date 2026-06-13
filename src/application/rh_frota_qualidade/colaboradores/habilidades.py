"""Use case de registro de habilidades de colaboradores (T-COL-032).

registrar_habilidade — catálogo XOR livre (D-COL-5 / INV-COL-HAB-XOR).

Refs: AC-COL-05; D-COL-5; TL-COL-10.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date
from uuid import UUID, uuid4

from src.domain.rh_frota_qualidade.colaboradores.entities import Habilidade
from src.domain.rh_frota_qualidade.colaboradores.enums import NivelHabilidade
from src.domain.rh_frota_qualidade.colaboradores.erros import ColaboradorInativo
from src.domain.rh_frota_qualidade.colaboradores.regras import validar_catalogo_xor_livre
from src.domain.rh_frota_qualidade.colaboradores.repository import (
    ColaboradorRepository,
    HabilidadeRepository,
)

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ComandoRegistrarHabilidade:
    """Input do use case de registro de habilidade."""

    tenant_id: UUID
    colaborador_id: UUID
    nivel: NivelHabilidade
    data_avaliacao: date
    # Exatamente um dos dois deve ser preenchido (D-COL-5 / XOR)
    catalogo_id: UUID | None = None
    descricao_livre: str | None = None
    evidencia_url: str | None = None


def registrar_habilidade(
    cmd: ComandoRegistrarHabilidade,
    *,
    repo_colab: ColaboradorRepository,
    repo_hab: HabilidadeRepository,
) -> UUID:
    """Registra habilidade para o colaborador (AC-COL-05 / D-COL-5).

    Valida catalogo_id XOR descricao_livre (D-COL-5 / ck_col_hab_xor).

    Returns:
        UUID da habilidade registrada.
    Raises:
        ColaboradorInativo: colaborador desligado ou soft-deletado.
        ValueError: catalogo_id e descricao_livre ambos preenchidos ou ambos None.
    """
    colab = repo_colab.obter(tenant_id=cmd.tenant_id, colaborador_id=cmd.colaborador_id)
    if colab is None or not colab.ativo:
        raise ColaboradorInativo(
            f"Colaborador {cmd.colaborador_id} está inativo (D-COL-3)."
        )

    validar_catalogo_xor_livre(
        catalogo_id=cmd.catalogo_id,
        descricao_livre=cmd.descricao_livre,
    )

    habilidade_id = uuid4()
    habilidade = Habilidade(
        id=habilidade_id,
        colaborador_id=cmd.colaborador_id,
        nivel=cmd.nivel,
        data_avaliacao=cmd.data_avaliacao,
        catalogo_id=cmd.catalogo_id,
        descricao_livre=cmd.descricao_livre,
        evidencia_url=cmd.evidencia_url,
    )

    # Persiste com tenant_id (o HabilidadeRepository.salvar() não tem tenant)
    _salvar_habilidade_com_tenant(habilidade, tenant_id=cmd.tenant_id)

    logger.info(
        "habilidade registrada",
        extra={
            "habilidade_id": str(habilidade_id),
            "colaborador_id": str(cmd.colaborador_id),
            "tenant_id": str(cmd.tenant_id),
        },
    )
    return habilidade_id


def _salvar_habilidade_com_tenant(
    habilidade: Habilidade,
    *,
    tenant_id: UUID,
) -> None:
    """Salva habilidade com tenant_id via ORM direto."""
    from src.infrastructure.colaboradores.models import ColaboradorHabilidade as HabModel

    HabModel.objects.update_or_create(
        id=habilidade.id,
        defaults={
            "colaborador_id": habilidade.colaborador_id,
            "tenant_id": tenant_id,
            "catalogo_id": str(habilidade.catalogo_id) if habilidade.catalogo_id else None,
            "descricao_livre": habilidade.descricao_livre,
            "nivel": habilidade.nivel.value,
            "evidencia_url": habilidade.evidencia_url,
            "data_avaliacao": habilidade.data_avaliacao,
        },
    )
