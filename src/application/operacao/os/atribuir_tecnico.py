"""Use case `atribuir_tecnico` — T-OS-052 (Fase 5).

Cobre AC-OS-002b-1 do PRD. AC-OS-002b-2 (UMC Lei 13.103), AC-OS-002b-3
(RBAC executor designado em iniciar — INV-OS-ATIV-005) e AC-OS-002b-4
(predicate `rt_competencia_cobre` na atribuicao) sao do CALLER.

Modelo:
- Recebe `os_id` + dict {atividade_id: executor_user_id} + agendamento (opcional).
- Para cada atribuicao: atividade vira AGENDADA (de PENDENTE) com `tecnico_executor_id`.
- Quando TODAS as atividades estao em estado >= AGENDADA, OS transita RASCUNHO -> AGENDADA.
- Grava `EventoDeOS(tipo='os_atribuida')` na timeline.

Use case puro: predicates de competencia ou agenda UMC sao do caller.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID, uuid4

from src.domain.operacao.os.entities import (
    AtividadeSnapshot,
    EventoDeOSSnapshot,
    OSSnapshot,
)
from src.domain.operacao.os.repository import OSRepository
from src.domain.operacao.os.value_objects import (
    EstadoAtividade,
    EstadoOS,
    TipoEventoDeOS,
)


@dataclass(frozen=True, slots=True)
class AtribuicaoAtividade:
    atividade_id: UUID
    tecnico_executor_id: UUID
    agendada_para: datetime | None = None


@dataclass(frozen=True, slots=True)
class AtribuirTecnicoInput:
    os_id: UUID
    atribuicoes: tuple[AtribuicaoAtividade, ...]
    correlation_id: UUID
    solicitada_em: datetime
    solicitada_por_user_id: UUID | None


@dataclass(frozen=True, slots=True)
class AtribuirTecnicoResultado:
    os_id: UUID
    os_transitou_para_agendada: bool
    atividades_atribuidas: tuple[UUID, ...]
    correlation_id: UUID


class ErroAtribuirTecnico(Exception):
    def __init__(self, codigo: str, http_status: int, detalhe: str = "") -> None:
        super().__init__(f"{codigo}: {detalhe}" if detalhe else codigo)
        self.codigo = codigo
        self.http_status = http_status
        self.detalhe = detalhe


def atribuir_tecnico(
    *,
    payload: AtribuirTecnicoInput,
    repository: OSRepository,
) -> AtribuirTecnicoResultado:
    """Atribui tecnico_executor a N atividades + transita OS RASCUNHO -> AGENDADA
    quando todas atividades sao AGENDADA+."""
    os_snapshot = repository.get_os_by_id(payload.os_id)
    if os_snapshot is None:
        raise ErroAtribuirTecnico("OSNaoEncontrada", 404)

    if os_snapshot.estado not in {EstadoOS.RASCUNHO, EstadoOS.AGENDADA}:
        raise ErroAtribuirTecnico(
            "OSEmEstadoIncompativel",
            412,
            detalhe=f"estado={os_snapshot.estado.value}; atribuicao so em RASCUNHO/AGENDADA",
        )

    if not payload.atribuicoes:
        raise ErroAtribuirTecnico("AtribuicoesVazias", 400)

    atribuicoes_por_atividade = {a.atividade_id: a for a in payload.atribuicoes}
    atividades_existentes = repository.listar_atividades_por_os(payload.os_id)
    if not atividades_existentes:
        raise ErroAtribuirTecnico("OSSemAtividades", 412)

    # Valida que toda atribuicao corresponde a uma atividade da OS.
    ids_existentes = {a.id for a in atividades_existentes}
    desconhecidas = set(atribuicoes_por_atividade.keys()) - ids_existentes
    if desconhecidas:
        raise ErroAtribuirTecnico(
            "AtividadeNaoPertenceAOS",
            422,
            detalhe=f"atividades_desconhecidas={sorted(str(d) for d in desconhecidas)}",
        )

    # Aplica atribuicoes.
    aplicadas: list[UUID] = []
    for atividade in atividades_existentes:
        atrib = atribuicoes_por_atividade.get(atividade.id)
        if atrib is None:
            continue
        if atividade.estado not in {EstadoAtividade.PENDENTE, EstadoAtividade.AGENDADA}:
            raise ErroAtribuirTecnico(
                "AtividadeEmEstadoIncompativel",
                412,
                detalhe=f"atividade={atividade.id} estado={atividade.estado.value}",
            )
        atualizada = AtividadeSnapshot(
            id=atividade.id,
            tenant_id=atividade.tenant_id,
            os_id=atividade.os_id,
            tipo=atividade.tipo,
            sequencia=atividade.sequencia,
            estado=EstadoAtividade.AGENDADA,
            tecnico_executor_id=atrib.tecnico_executor_id,
            agendada_para=atrib.agendada_para,
            iniciada_em=atividade.iniciada_em,
            concluida_em=atividade.concluida_em,
            valor_unitario_snapshot=atividade.valor_unitario_snapshot,
            link_modulo_tecnico_id=atividade.link_modulo_tecnico_id,
            geo_lat=atividade.geo_lat,
            geo_long=atividade.geo_long,
            geo_municipio_hash=atividade.geo_municipio_hash,
            equipamento_id_desnormalizado=atividade.equipamento_id_desnormalizado,
            tipo_bloqueia_concorrencia=atividade.tipo_bloqueia_concorrencia,
        )
        repository.salvar_atividade(atualizada)
        aplicadas.append(atividade.id)

    # OS transita RASCUNHO -> AGENDADA quando TODAS atividades >= AGENDADA.
    atividades_pos = repository.listar_atividades_por_os(payload.os_id)
    todas_agendadas = all(
        a.estado
        in {
            EstadoAtividade.AGENDADA,
            EstadoAtividade.EM_EXECUCAO,
            EstadoAtividade.CONCLUIDA,
            EstadoAtividade.NAO_CONFORME,
            EstadoAtividade.CANCELADA,
        }
        for a in atividades_pos
    )
    transitou = False
    if todas_agendadas and os_snapshot.estado == EstadoOS.RASCUNHO:
        os_agendada = OSSnapshot(
            id=os_snapshot.id,
            tenant_id=os_snapshot.tenant_id,
            numero_os=os_snapshot.numero_os,
            cliente_id=os_snapshot.cliente_id,
            cliente_referencia_hash=os_snapshot.cliente_referencia_hash,
            cliente_key_id=os_snapshot.cliente_key_id,
            equipamento_id=os_snapshot.equipamento_id,
            equipamento_recebimento_id=os_snapshot.equipamento_recebimento_id,
            orcamento_origem_id=os_snapshot.orcamento_origem_id,
            os_origem_id=os_snapshot.os_origem_id,
            sucessao_societaria_id=os_snapshot.sucessao_societaria_id,
            estado=EstadoOS.AGENDADA,
            tipo_predominante=os_snapshot.tipo_predominante,
            nao_conformidade_global=os_snapshot.nao_conformidade_global,
            valor_total=os_snapshot.valor_total,
            valor_total_atualizado=os_snapshot.valor_total_atualizado,
            analise_critica_id=os_snapshot.analise_critica_id,
            analise_critica_snapshot_hash=os_snapshot.analise_critica_snapshot_hash,
            regra_decisao_acordada=os_snapshot.regra_decisao_acordada,
            criada_em=os_snapshot.criada_em,
            atualizada_em=payload.solicitada_em,
            criada_por_user_id=os_snapshot.criada_por_user_id,
        )
        repository.salvar_os(os_agendada)
        transitou = True

    # EventoDeOS — timeline.
    payload_evento: dict[str, object] = {
        "atividades_atribuidas": [str(aid) for aid in aplicadas],
        "os_transitou_para_agendada": transitou,
    }
    payload_canonico = json.dumps(payload_evento, sort_keys=True, ensure_ascii=False)
    payload_hash = hashlib.sha256(payload_canonico.encode("utf-8")).hexdigest()  # audit-pii-salt: skip -- payload sanitizado sem PII cru
    repository.publicar_evento(
        EventoDeOSSnapshot(
            id=uuid4(),
            tenant_id=os_snapshot.tenant_id,
            os_id=payload.os_id,
            atividade_id=None,
            tipo=TipoEventoDeOS.OS_ATRIBUIDA,
            payload_hash=payload_hash,
            payload_data=payload_evento,
            correlation_id=payload.correlation_id,
            actor_user_id=payload.solicitada_por_user_id,
            occurred_at=payload.solicitada_em,
            criado_em=payload.solicitada_em,
        )
    )

    return AtribuirTecnicoResultado(
        os_id=payload.os_id,
        os_transitou_para_agendada=transitou,
        atividades_atribuidas=tuple(aplicadas),
        correlation_id=payload.correlation_id,
    )
