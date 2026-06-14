"""Query agregadora OS visao 360 — T-OS-085 (P-OS-T4 p95 ≤300ms).

Carrega OS + atividades + aceites + dispensas + NCs ativas + ultima foto
de cada atividade. `tipo_predominante` e lido do snapshot da OS (calculado na
transicao -> CONCLUIDA, nao aqui).

T-OSME-035 (ADR-0082): agrega equipamentos_distintos das atividades e lista
itens_comerciais (AC-OSME-006-1).

Custo de queries O(1) no numero de atividades (ADR-0082 P9 — anti-N+1):
OS + atividades + 4 mapas agregados (aceites/dispensas/NCs/fotos) + itens
comerciais = 7 queries fixas, independente de quantas atividades a OS tem.
Camada APPLICATION — nao faz SQL raw aqui; os mapas vem do repository.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from src.domain.operacao.os.entities import ItemComercialOSSnapshot
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
    # ADR-0082 / D-OSME-1: equipamento_id proprio da atividade (NOT NULL em
    # atividade tecnica; None apenas em contexto legado de fallback via trigger).
    equipamento_id: UUID | None
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
    # ADR-0082 / AC-OSME-006-1: equipamentos distintos das atividades tecnicas.
    # Conjunto ordenado para serialização determinística.
    equipamentos_distintos: tuple[UUID, ...]
    # AC-OSME-006-1: itens comerciais como linhas proprias (D-OSME-3).
    # Nao embutidos no total — aparecem explicitamente para o caller.
    itens_comerciais: tuple[ItemComercialOSSnapshot, ...]


def visao_360_da_os(os_id: UUID, repository: OSRepository) -> OSVisao360 | None:
    """Retorna visao agregada da OS ou None se nao existir."""
    os_snap = repository.get_os_by_id(os_id)
    if os_snap is None:
        return None

    atividades_snap = repository.listar_atividades_por_os(os_id)
    # Anti-N+1 (ADR-0082 P9): aceites/dispensas/NCs/fotos de TODAS as atividades
    # vem em 4 queries agregadas (uma por entidade), nao 4 por atividade. A visao
    # 360 fica O(1) em queries — critico para OS multi-equipamento (N atividades).
    aceites = repository.mapa_aceites_por_os(os_id)
    dispensas = repository.mapa_dispensas_por_os(os_id)
    ncs_ativas = repository.mapa_ncs_ativas_por_os(os_id)
    fotos_por_ativ = repository.mapa_evidencias_foto_por_os(os_id)

    atividades_visao: list[AtividadeVisao360] = []
    # Coleta equipamentos distintos no mesmo loop (sem query extra).
    equipamentos_vistos: dict[UUID, None] = {}  # dict preserva ordem de insercao
    for ativ in atividades_snap:
        fotos_validas = [
            f for f in fotos_por_ativ.get(ativ.id, []) if f.revogado_em is None
        ]
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
                equipamento_id=ativ.equipamento_id,
                tem_aceite=ativ.id in aceites,
                tem_dispensa=ativ.id in dispensas,
                tem_nc_ativa=ativ.id in ncs_ativas,
                qtd_fotos=len(fotos_validas),
            )
        )
        if ativ.equipamento_id is not None:
            equipamentos_vistos[ativ.equipamento_id] = None

    # 1 query extra para itens comerciais (AC-OSME-006-1 — linha propria na OS).
    itens_comerciais = repository.listar_itens_comerciais_por_os(os_id)

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
        equipamentos_distintos=tuple(equipamentos_vistos.keys()),
        itens_comerciais=tuple(itens_comerciais),
    )
