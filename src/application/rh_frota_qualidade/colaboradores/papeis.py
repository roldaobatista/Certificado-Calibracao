"""Use cases de atribuição e revogação de papéis de colaboradores (T-COL-031).

atribuir_papel — SIGNATARIO: valida identidade+escopo via RTCompetencia por
                 usuario_id (D-COL-11 / INV-COL-SIGNATARIO-IDENTIDADE/-ESCOPO);
                 DONO: advisory lock + partial unique → 409 DonoJaExiste;
                 MOTORISTA_UMC: pendencia_cnh sem erro (R-COL-1).
revogar_papel  — seta revogado_em, nunca apaga linha (D-COL-4 / audit).

Integração signatário↔RT (Risco 1 / TL-COL-01):
  - Busca RT por `usuario_id` (mesmo campo em `ResponsavelTecnicoTenant`).
  - Verifica RTCompetencia vigente com mesmo `usuario_id` (casa PESSOA).
  - Import local de predicates do RT para evitar ciclo domain↔infra.

Refs: AC-COL-03; D-COL-4/11; INV-COL-SIGNATARIO-*/DONO-UNICO; R-COL-1;
      TL-COL-01/11; ADR-0065.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import UTC, date, datetime
from uuid import UUID, uuid4

from src.domain.rh_frota_qualidade.colaboradores.entities import PapelColaboradorAtribuido
from src.domain.rh_frota_qualidade.colaboradores.enums import PapelColaborador
from src.domain.rh_frota_qualidade.colaboradores.erros import (
    ColaboradorInativo,
)
from src.domain.rh_frota_qualidade.colaboradores.regras import (
    pendencia_cnh_motorista,
    pode_atribuir_signatario,
    validar_dono_unico,
)
from src.domain.rh_frota_qualidade.colaboradores.repository import (
    ColaboradorRepository,
    PapelRepository,
)

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ComandoAtribuirPapel:
    """Input do use case de atribuição de papel."""

    tenant_id: UUID
    colaborador_id: UUID
    papel: PapelColaborador
    data_inicio: date
    data_fim: date | None = None
    # Para SIGNATARIO: RT que casa com colaborador.usuario_id
    responsabilidade_tecnica_id: UUID | None = None
    # Para MOTORISTA_UMC: informa se tem CNH
    tem_cnh: bool = True
    # Perfil regulatório do tenant (ADR-0067)
    perfil_tenant: str = "A"


@dataclass(frozen=True)
class ComandoRevogarPapel:
    """Input do use case de revogação de papel."""

    tenant_id: UUID
    colaborador_id: UUID
    papel_id: UUID


def _verificar_signatario_rt(
    *,
    usuario_id: UUID | None,
    tenant_id: UUID,
    data_inicio: date,
) -> tuple[bool, bool]:
    """Verifica identidade e escopo via RTCompetencia por usuario_id.

    Integração signatário↔RT (TL-COL-01 / Risco 1):
    - Busca RT do tenant com o mesmo usuario_id (casa a PESSOA).
    - Verifica RTCompetencia vigente na data de atribuição.

    Returns:
        (rt_casa, escopo_vigente) — ambos False se usuario_id é None.
    """
    if usuario_id is None:
        return False, False

    # Import local: infra → não deve ser importada no domínio ou application
    from django.db.models import Q

    from src.infrastructure.responsavel_tecnico.models import (
        ResponsavelTecnicoTenant,
        RTCompetencia,
    )

    rt = (
        ResponsavelTecnicoTenant.objects.filter(
            tenant_id=tenant_id,
            usuario_id=usuario_id,
            encerrado_em__isnull=True,
        )
        .only("id")
        .first()
    )
    if rt is None:
        # Não existe RT vigente com esse usuario_id → não casa
        return False, False

    # Escopo vigente: qualquer competência ativa na data de atribuição
    escopo_vigente = (
        RTCompetencia.objects.filter(
            tenant_id=tenant_id,
            rt_id=rt.id,
            declarado_em__lte=data_inicio,
        )
        .filter(Q(vigente_ate__isnull=True) | Q(vigente_ate__gte=data_inicio))
        .exists()
    )
    return True, escopo_vigente


def atribuir_papel(
    cmd: ComandoAtribuirPapel,
    *,
    repo_colab: ColaboradorRepository,
    repo_papel: PapelRepository,
) -> UUID:
    """Atribui papel de negócio ao colaborador (AC-COL-03 / D-COL-4).

    Lógica por papel:
    - SIGNATARIO: valida usuario_id + RTCompetencia vigente por usuario_id
      (INV-COL-SIGNATARIO-IDENTIDADE/-ESCOPO / D-COL-11 / TL-COL-01).
    - DONO: advisory lock (TL-COL-11) + validação domínio → 409 DonoJaExiste.
    - MOTORISTA_UMC: pendencia_cnh=True se sem CNH (R-COL-1 — sem erro).
    - Outros: atribuição direta.

    Returns:
        UUID do papel atribuído.
    Raises:
        ColaboradorInativo: colaborador desligado ou soft-deletado.
        SignatarioSemUsuario: SIGNATARIO sem usuario_id.
        SignatarioRtNaoCasa: RTCompetencia não casa com usuario_id.
        SignatarioSemEscopo: escopo do RT não vigente.
        DonoJaExiste: já existe DONO ativo no tenant.
    """
    colab = repo_colab.obter(tenant_id=cmd.tenant_id, colaborador_id=cmd.colaborador_id)
    if colab is None or not colab.ativo:
        raise ColaboradorInativo(
            f"Colaborador {cmd.colaborador_id} está inativo ou não existe "
            "(D-COL-3 / INV-COLABORADOR-INATIVO)."
        )

    pendencia_cnh = False
    responsabilidade_tecnica_id = cmd.responsabilidade_tecnica_id

    if cmd.papel == PapelColaborador.SIGNATARIO:
        # Valida identidade + escopo via RTCompetencia por usuario_id (TL-COL-01)
        rt_casa, escopo_vigente = _verificar_signatario_rt(
            usuario_id=colab.usuario_id,
            tenant_id=cmd.tenant_id,
            data_inicio=cmd.data_inicio,
        )
        pode_atribuir_signatario(
            usuario_id=colab.usuario_id,
            rt_casa=rt_casa,
            escopo_vigente=escopo_vigente,
            perfil_tenant=cmd.perfil_tenant,
        )
        # responsabilidade_tecnica_id validado pelo caller (view) ou opcional aqui

    elif cmd.papel == PapelColaborador.DONO:
        # Advisory lock antes da verificação (serializa concorrência — ADR-0065)
        repo_papel.travar_dono_por_tenant(tenant_id=cmd.tenant_id)
        dono_ja_existe = repo_papel.existe_dono_ativo(tenant_id=cmd.tenant_id)
        validar_dono_unico(dono_ja_existe=dono_ja_existe)

    elif cmd.papel == PapelColaborador.MOTORISTA_UMC:
        # R-COL-1: salva com pendência se sem CNH, SEM levantar erro
        pendencia_cnh = pendencia_cnh_motorista(tem_cnh=cmd.tem_cnh)
        if pendencia_cnh:
            logger.info(
                "motorista_umc atribuido com pendencia_cnh",
                extra={
                    "colaborador_id": str(cmd.colaborador_id),
                    "tenant_id": str(cmd.tenant_id),
                },
            )

    papel_id = uuid4()
    papel = PapelColaboradorAtribuido(
        id=papel_id,
        colaborador_id=cmd.colaborador_id,
        papel=cmd.papel,
        data_inicio=cmd.data_inicio,
        data_fim=cmd.data_fim,
        revogado_em=None,
        responsabilidade_tecnica_id=responsabilidade_tecnica_id,
        pendencia_cnh=pendencia_cnh,
    )
    # Persiste com tenant_id (corrige o "None" do repositório base)
    _salvar_papel_com_tenant(papel, tenant_id=cmd.tenant_id, repo_papel=repo_papel)

    logger.info(
        "papel atribuido",
        extra={
            "papel_id": str(papel_id),
            "colaborador_id": str(cmd.colaborador_id),
            "papel": cmd.papel.value,
            "tenant_id": str(cmd.tenant_id),
        },
    )
    return papel_id


def _salvar_papel_com_tenant(
    papel: PapelColaboradorAtribuido,
    *,
    tenant_id: UUID,
    repo_papel: PapelRepository,
) -> None:
    """Salva papel no banco com tenant_id correto.

    O DjangoPapelRepository.salvar() tem `tenant_id: None` como placeholder.
    Aqui injetamos o tenant diretamente via ORM (lição do modelo 1b).
    """
    # Import local para não criar dependência circular app → infra no topo
    from src.infrastructure.colaboradores.models import ColaboradorPapel as PapelModel

    PapelModel.objects.update_or_create(
        id=papel.id,
        defaults={
            "colaborador_id": papel.colaborador_id,
            "tenant_id": tenant_id,
            "papel": papel.papel.value,
            "data_inicio": papel.data_inicio,
            "data_fim": papel.data_fim,
            "revogado_em": papel.revogado_em,
            "responsabilidade_tecnica_id": papel.responsabilidade_tecnica_id,
            "pendencia_cnh": papel.pendencia_cnh,
        },
    )


def revogar_papel(
    cmd: ComandoRevogarPapel,
    *,
    repo_colab: ColaboradorRepository,
    repo_papel: PapelRepository,
) -> None:
    """Revoga papel (D-COL-4): seta revogado_em, nunca apaga linha (audit).

    Raises:
        ColaboradorInativo: colaborador desligado ou soft-deletado.
    """
    colab = repo_colab.obter(tenant_id=cmd.tenant_id, colaborador_id=cmd.colaborador_id)
    if colab is None or not colab.ativo:
        raise ColaboradorInativo(
            f"Colaborador {cmd.colaborador_id} está inativo (D-COL-3)."
        )

    revogado_em = datetime.now(UTC)
    repo_papel.revogar(
        tenant_id=cmd.tenant_id,
        papel_id=cmd.papel_id,
        revogado_em=revogado_em,
    )

    logger.info(
        "papel revogado",
        extra={
            "papel_id": str(cmd.papel_id),
            "colaborador_id": str(cmd.colaborador_id),
            "tenant_id": str(cmd.tenant_id),
        },
    )
