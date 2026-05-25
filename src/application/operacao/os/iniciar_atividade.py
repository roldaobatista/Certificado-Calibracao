"""Use case `iniciar_atividade` — T-OS-055 (Fase 5).

Cobre AC-OS-003-1 (happy) + AC-OS-003-4 (gate sequencia N-1) do PRD.
AC-OS-003-2/3 (idempotency-key) e AC-OS-003-6 (rt_competencia_cobre na
data de inicio) sao do CALLER (view/consumer).

Regras:
- Atividade em PENDENTE ou AGENDADA + OS nao-terminal -> EM_EXECUCAO.
- AC-OS-003-1: 1a atividade transitando -> OS vai pra EM_EXECUCAO.
- AC-OS-003-4: atividade N-1 nao-terminal bloqueia inicio da N -> 412
  `SequenciaPendente`.
- AC-OS-003-5: geo opt-in preserva precisao limitada (validacao no caller —
  geo_municipio_hash precomputado).
- INV-OS-ATIV-005: so `tecnico_executor_id` pode iniciar.

Use case puro.
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
from src.domain.operacao.os.regras import atividade_pode_ser_iniciada_por
from src.domain.operacao.os.repository import OSRepository
from src.domain.operacao.os.value_objects import (
    EstadoAtividade,
    EstadoOS,
    TipoEventoDeOS,
)


@dataclass(frozen=True, slots=True)
class IniciarAtividadeInput:
    atividade_id: UUID
    usuario_id: UUID
    correlation_id: UUID
    client_event_id: UUID  # AC-OS-003-1 — UUID gerado pelo client (sync mobile)
    iniciada_em: datetime
    geo_lat: float | None = None
    geo_long: float | None = None
    geo_municipio_hash: str = ""


@dataclass(frozen=True, slots=True)
class IniciarAtividadeResultado:
    atividade_id: UUID
    os_id: UUID
    os_transitou_para_em_execucao: bool
    correlation_id: UUID


class ErroIniciarAtividade(Exception):
    def __init__(self, codigo: str, http_status: int, detalhe: str = "") -> None:
        super().__init__(f"{codigo}: {detalhe}" if detalhe else codigo)
        self.codigo = codigo
        self.http_status = http_status
        self.detalhe = detalhe


def iniciar_atividade(
    *,
    payload: IniciarAtividadeInput,
    repository: OSRepository,
) -> IniciarAtividadeResultado:
    """Transiciona atividade PENDENTE/AGENDADA -> EM_EXECUCAO.

    AC-OS-003-6 (PRD modificado por ADR-0063): predicate
    `rt_competencia_cobre` re-validado na data de inicio. Fail-open
    controlado em Marco 3 (grandeza nao persistida — diferido Marco 4).
    """
    from src.infrastructure.ordens_servico.predicates_os import (
        rt_competencia_cobre,
    )

    atividade = repository.get_atividade_by_id(payload.atividade_id)
    if atividade is None:
        raise ErroIniciarAtividade("AtividadeNaoEncontrada", 404)

    if not atividade_pode_ser_iniciada_por(atividade, payload.usuario_id):
        # INV-OS-ATIV-005: executor designado eh unico autorizado.
        if atividade.tecnico_executor_id != payload.usuario_id:
            raise ErroIniciarAtividade("NaoEExecutor", 403)
        raise ErroIniciarAtividade(
            "AtividadeEmEstadoIncompativel",
            412,
            detalhe=f"estado={atividade.estado.value}",
        )

    # AC-OS-003-6 + ADR-0063: re-valida predicate na data atual.
    permitido, motivo = rt_competencia_cobre(
        {
            "tenant_id": atividade.tenant_id,
            "executor_user_id": payload.usuario_id,
            "grandeza": "",  # ADR-0063 — diferido Marco 4
        }
    )
    if not permitido:
        raise ErroIniciarAtividade(
            "ExecutorSemCompetencia",
            422,
            detalhe=f"predicate rt_competencia_cobre = {motivo}",
        )

    os_snapshot = repository.get_os_by_id(atividade.os_id)
    if os_snapshot is None:
        raise ErroIniciarAtividade("OSNaoEncontrada", 404)
    if os_snapshot.estado in {
        EstadoOS.CONCLUIDA,
        EstadoOS.FATURADA,
        EstadoOS.PAGA,
        EstadoOS.CANCELADA,
    }:
        raise ErroIniciarAtividade(
            "OSEmEstadoTerminal",
            412,
            detalhe=f"estado={os_snapshot.estado.value}",
        )

    # AC-OS-003-4: gate sequencia N-1 — anteriores devem estar terminais.
    irmas = repository.listar_atividades_por_os(atividade.os_id)
    anteriores_nao_terminais = [
        a
        for a in irmas
        if a.sequencia < atividade.sequencia and not a.estado.terminal
    ]
    if anteriores_nao_terminais:
        pendentes_seqs = sorted(a.sequencia for a in anteriores_nao_terminais)
        raise ErroIniciarAtividade(
            "SequenciaPendente",
            412,
            detalhe=f"anteriores_nao_terminais={pendentes_seqs}",
        )

    # Transicao.
    atualizada = AtividadeSnapshot(
        id=atividade.id,
        tenant_id=atividade.tenant_id,
        os_id=atividade.os_id,
        tipo=atividade.tipo,
        sequencia=atividade.sequencia,
        estado=EstadoAtividade.EM_EXECUCAO,
        tecnico_executor_id=atividade.tecnico_executor_id,
        agendada_para=atividade.agendada_para,
        iniciada_em=payload.iniciada_em,
        concluida_em=None,
        valor_unitario_snapshot=atividade.valor_unitario_snapshot,
        link_modulo_tecnico_id=atividade.link_modulo_tecnico_id,
        geo_lat=payload.geo_lat,
        geo_long=payload.geo_long,
        geo_municipio_hash=payload.geo_municipio_hash,
        equipamento_id_desnormalizado=atividade.equipamento_id_desnormalizado,
        tipo_bloqueia_concorrencia=atividade.tipo_bloqueia_concorrencia,
    )
    repository.salvar_atividade(atualizada)

    # OS RASCUNHO/AGENDADA -> EM_EXECUCAO se primeira a iniciar.
    transitou_os = False
    if os_snapshot.estado in {EstadoOS.RASCUNHO, EstadoOS.AGENDADA}:
        os_em_exec = OSSnapshot(
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
            estado=EstadoOS.EM_EXECUCAO,
            tipo_predominante=os_snapshot.tipo_predominante,
            nao_conformidade_global=os_snapshot.nao_conformidade_global,
            valor_total=os_snapshot.valor_total,
            valor_total_atualizado=os_snapshot.valor_total_atualizado,
            analise_critica_id=os_snapshot.analise_critica_id,
            analise_critica_snapshot_hash=os_snapshot.analise_critica_snapshot_hash,
            regra_decisao_acordada=os_snapshot.regra_decisao_acordada,
            criada_em=os_snapshot.criada_em,
            atualizada_em=payload.iniciada_em,
            criada_por_user_id=os_snapshot.criada_por_user_id,
        )
        repository.salvar_os(os_em_exec)
        transitou_os = True

    payload_evento: dict[str, object] = {
        "atividade_id": str(atividade.id),
        "client_event_id": str(payload.client_event_id),
        "os_transitou_para_em_execucao": transitou_os,
    }
    payload_canonico = json.dumps(payload_evento, sort_keys=True, ensure_ascii=False)
    payload_hash = hashlib.sha256(payload_canonico.encode("utf-8")).hexdigest()  # audit-pii-salt: skip -- payload sanitizado sem PII
    repository.publicar_evento(
        EventoDeOSSnapshot(
            id=uuid4(),
            tenant_id=atividade.tenant_id,
            os_id=atividade.os_id,
            atividade_id=atividade.id,
            tipo=TipoEventoDeOS.ATIVIDADE_INICIADA,
            payload_hash=payload_hash,
            payload_data=payload_evento,
            correlation_id=payload.correlation_id,
            actor_user_id=payload.usuario_id,
            occurred_at=payload.iniciada_em,
            criado_em=payload.iniciada_em,
        )
    )

    return IniciarAtividadeResultado(
        atividade_id=atividade.id,
        os_id=atividade.os_id,
        os_transitou_para_em_execucao=transitou_os,
        correlation_id=payload.correlation_id,
    )
