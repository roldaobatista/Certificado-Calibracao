"""Query agregadora OS visao 360 — T-OS-085 (P-OS-T4 p95 ≤300ms).

Carrega OS + atividades + aceites + dispensas + NCs ativas + ultima foto
de cada atividade + tipo_predominante calculado.

Usa repository.listar_* + 1 join leve via repository — nao faz SQL raw aqui
(camada APPLICATION). Otimizacao futura via raw `jsonb_agg` em
infrastructure layer eh deferida pra Wave A quando volume justificar.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from src.domain.operacao.os.repository import OSRepository


@dataclass(frozen=True, slots=True)
class AtividadeVisao360:
    atividade_id: UUID
    tipo: str
    sequencia: int
    estado: str
    tecnico_executor_id: UUID | None
    agendada_para: datetime | None
    iniciada_em: datetime | None
    concluida_em: datetime | None
    valor_unitario_snapshot: Decimal
    tem_aceite: bool
    tem_dispensa: bool
    tem_nc_ativa: bool
    qtd_fotos: int


@dataclass(frozen=True, slots=True)
class OSVisao360:
    os_id: UUID
    numero_os: int
    tenant_id: UUID
    cliente_id: UUID | None
    cliente_referencia_hash: str
    equipamento_id: UUID | None  # NULL em OS multi-equipamento (ADR-0082 / D-OSME-2)
    equipamento_recebimento_id: UUID | None
    orcamento_origem_id: UUID | None
    os_origem_id: UUID | None
    estado: str
    tipo_predominante: str
    nao_conformidade_global: bool
    valor_total: Decimal
    valor_total_atualizado: Decimal
    criada_em: datetime
    atualizada_em: datetime
    atividades: tuple[AtividadeVisao360, ...]


def visao_360_da_os(os_id: UUID, repository: OSRepository) -> OSVisao360 | None:
    """Retorna visao agregada da OS ou None se nao existir."""
    os_snap = repository.get_os_by_id(os_id)
    if os_snap is None:
        return None

    atividades_snap = repository.listar_atividades_por_os(os_id)
    atividades_visao: list[AtividadeVisao360] = []
    for ativ in atividades_snap:
        aceite = repository.get_aceite_por_atividade(ativ.id)
        dispensa = repository.get_dispensa_por_atividade(ativ.id)
        nc_ativa = repository.get_nc_ativa_por_atividade(ativ.id)
        fotos = repository.listar_evidencias_foto_por_atividade(ativ.id)
        fotos_validas = [f for f in fotos if f.revogado_em is None]
        atividades_visao.append(
            AtividadeVisao360(
                atividade_id=ativ.id,
                tipo=ativ.tipo.value,
                sequencia=ativ.sequencia,
                estado=ativ.estado.value,
                tecnico_executor_id=ativ.tecnico_executor_id,
                agendada_para=ativ.agendada_para,
                iniciada_em=ativ.iniciada_em,
                concluida_em=ativ.concluida_em,
                valor_unitario_snapshot=ativ.valor_unitario_snapshot,
                tem_aceite=aceite is not None,
                tem_dispensa=dispensa is not None,
                tem_nc_ativa=nc_ativa is not None,
                qtd_fotos=len(fotos_validas),
            )
        )

    return OSVisao360(
        os_id=os_snap.id,
        numero_os=os_snap.numero_os,
        tenant_id=os_snap.tenant_id,
        cliente_id=os_snap.cliente_id,
        cliente_referencia_hash=os_snap.cliente_referencia_hash,
        equipamento_id=os_snap.equipamento_id,
        equipamento_recebimento_id=os_snap.equipamento_recebimento_id,
        orcamento_origem_id=os_snap.orcamento_origem_id,
        os_origem_id=os_snap.os_origem_id,
        estado=os_snap.estado.value,
        tipo_predominante=os_snap.tipo_predominante,
        nao_conformidade_global=os_snap.nao_conformidade_global,
        valor_total=os_snap.valor_total,
        valor_total_atualizado=os_snap.valor_total_atualizado,
        criada_em=os_snap.criada_em,
        atualizada_em=os_snap.atualizada_em,
        atividades=tuple(sorted(atividades_visao, key=lambda a: a.sequencia)),
    )
