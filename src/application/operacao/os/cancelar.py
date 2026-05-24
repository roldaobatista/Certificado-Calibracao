"""Use cases `cancelar_atividade` + `cancelar_os` — T-OS-070/072 (Fase 5).

Cobertura PRD US-OS-008..011:
- `cancelar_atividade`: atividade nao-terminal -> CANCELADA. Publica
  `OS.EscopoAlterado` (ADR-0042 + INV-OS-FAT-001) com valor_total_atualizado
  recalculado quando OS ja foi minimamente atribuida.
- `cancelar_os`: OS nao-terminal -> CANCELADA. Cascateia: todas atividades
  nao-terminais -> CANCELADA. Publica `OS.Cancelada`.

Recebe `MotivoCancelamento` VO (>=30 chars + anti-PII via INV-OS-TXT-001).
Use case puro.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4

from src.domain.operacao.os.entities import (
    AtividadeSnapshot,
    EventoDeOSSnapshot,
    OSSnapshot,
)
from src.domain.operacao.os.regras import calcular_valor_total_atualizado
from src.domain.operacao.os.repository import OSRepository
from src.domain.operacao.os.value_objects import (
    EstadoAtividade,
    EstadoOS,
    MotivoCancelamento,
    TipoEventoDeOS,
)

# =============================================================
# cancelar_atividade
# =============================================================


@dataclass(frozen=True, slots=True)
class CancelarAtividadeInput:
    atividade_id: UUID
    usuario_id: UUID
    motivo: MotivoCancelamento
    correlation_id: UUID
    cancelada_em: datetime


@dataclass(frozen=True, slots=True)
class CancelarAtividadeResultado:
    atividade_id: UUID
    os_id: UUID
    valor_total_atualizado: Decimal
    correlation_id: UUID


class ErroCancelar(Exception):
    def __init__(self, codigo: str, http_status: int, detalhe: str = "") -> None:
        super().__init__(f"{codigo}: {detalhe}" if detalhe else codigo)
        self.codigo = codigo
        self.http_status = http_status
        self.detalhe = detalhe


def cancelar_atividade(
    *,
    payload: CancelarAtividadeInput,
    repository: OSRepository,
) -> CancelarAtividadeResultado:
    """Transiciona atividade nao-terminal -> CANCELADA + recalcula valor OS."""
    atividade = repository.get_atividade_by_id(payload.atividade_id)
    if atividade is None:
        raise ErroCancelar("AtividadeNaoEncontrada", 404)
    if atividade.estado.terminal:
        raise ErroCancelar(
            "AtividadeJaTerminal",
            412,
            detalhe=f"estado={atividade.estado.value}",
        )

    motivo_hash = hashlib.sha256(
        payload.motivo.texto.encode("utf-8")
    ).hexdigest()  # audit-pii-salt: skip -- VO MotivoCancelamento bloqueia PII; integrity hash

    atividade_cancelada = AtividadeSnapshot(
        id=atividade.id,
        tenant_id=atividade.tenant_id,
        os_id=atividade.os_id,
        tipo=atividade.tipo,
        sequencia=atividade.sequencia,
        estado=EstadoAtividade.CANCELADA,
        tecnico_executor_id=atividade.tecnico_executor_id,
        agendada_para=atividade.agendada_para,
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
    repository.salvar_atividade(atividade_cancelada)

    # Recalcula valor_total_atualizado (INV-OS-FAT-001).
    todas = repository.listar_atividades_por_os(atividade.os_id)
    novo_valor = calcular_valor_total_atualizado(todas)
    os_snapshot = repository.get_os_by_id(atividade.os_id)
    if os_snapshot is None:
        raise ErroCancelar("OSNaoEncontrada", 404)
    os_atualizada = OSSnapshot(
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
        estado=os_snapshot.estado,
        tipo_predominante=os_snapshot.tipo_predominante,
        nao_conformidade_global=os_snapshot.nao_conformidade_global,
        valor_total=os_snapshot.valor_total,
        valor_total_atualizado=novo_valor,
        analise_critica_id=os_snapshot.analise_critica_id,
        analise_critica_snapshot_hash=os_snapshot.analise_critica_snapshot_hash,
        regra_decisao_acordada=os_snapshot.regra_decisao_acordada,
        criada_em=os_snapshot.criada_em,
        atualizada_em=payload.cancelada_em,
        criada_por_user_id=os_snapshot.criada_por_user_id,
    )
    repository.salvar_os(os_atualizada)

    # EventoDeOS — atividade_cancelada + os_escopo_alterado (ADR-0042).
    cancel_payload: dict[str, object] = {
        "atividade_id": str(atividade.id),
        "motivo_hash": motivo_hash,
        "tipo": atividade.tipo.value,
    }
    cancel_canonico = json.dumps(cancel_payload, sort_keys=True, ensure_ascii=False)
    cancel_hash = hashlib.sha256(cancel_canonico.encode("utf-8")).hexdigest()  # audit-pii-salt: skip -- payload sanitizado
    repository.publicar_evento(
        EventoDeOSSnapshot(
            id=uuid4(),
            tenant_id=atividade.tenant_id,
            os_id=atividade.os_id,
            atividade_id=atividade.id,
            tipo=TipoEventoDeOS.ATIVIDADE_CANCELADA,
            payload_hash=cancel_hash,
            payload_data=cancel_payload,
            correlation_id=payload.correlation_id,
            actor_user_id=payload.usuario_id,
            occurred_at=payload.cancelada_em,
            criado_em=payload.cancelada_em,
        )
    )

    # OS.EscopoAlterado (INV-OS-FAT-001 / ADR-0042).
    escopo_payload: dict[str, object] = {
        "valor_total_atualizado": str(novo_valor),
        "atividade_removida_id": str(atividade.id),
    }
    escopo_canonico = json.dumps(escopo_payload, sort_keys=True, ensure_ascii=False)
    escopo_hash = hashlib.sha256(escopo_canonico.encode("utf-8")).hexdigest()  # audit-pii-salt: skip -- payload sanitizado
    repository.publicar_evento(
        EventoDeOSSnapshot(
            id=uuid4(),
            tenant_id=atividade.tenant_id,
            os_id=atividade.os_id,
            atividade_id=None,
            tipo=TipoEventoDeOS.OS_ESCOPO_ALTERADO,
            payload_hash=escopo_hash,
            payload_data=escopo_payload,
            correlation_id=payload.correlation_id,
            actor_user_id=payload.usuario_id,
            occurred_at=payload.cancelada_em,
            criado_em=payload.cancelada_em,
        )
    )

    return CancelarAtividadeResultado(
        atividade_id=atividade.id,
        os_id=atividade.os_id,
        valor_total_atualizado=novo_valor,
        correlation_id=payload.correlation_id,
    )


# =============================================================
# cancelar_os
# =============================================================


@dataclass(frozen=True, slots=True)
class CancelarOSInput:
    os_id: UUID
    usuario_id: UUID
    motivo: MotivoCancelamento
    correlation_id: UUID
    cancelada_em: datetime


@dataclass(frozen=True, slots=True)
class CancelarOSResultado:
    os_id: UUID
    atividades_canceladas: tuple[UUID, ...]
    correlation_id: UUID


def cancelar_os(
    *,
    payload: CancelarOSInput,
    repository: OSRepository,
) -> CancelarOSResultado:
    """Cancela OS + cascateia atividades nao-terminais."""
    os_snapshot = repository.get_os_by_id(payload.os_id)
    if os_snapshot is None:
        raise ErroCancelar("OSNaoEncontrada", 404)
    if os_snapshot.estado.terminal:
        raise ErroCancelar(
            "OSJaTerminal",
            412,
            detalhe=f"estado={os_snapshot.estado.value}",
        )

    motivo_hash = hashlib.sha256(
        payload.motivo.texto.encode("utf-8")
    ).hexdigest()  # audit-pii-salt: skip -- VO bloqueia PII; integrity hash

    # Cascateia atividades nao-terminais.
    atividades = repository.listar_atividades_por_os(payload.os_id)
    canceladas: list[UUID] = []
    for atividade in atividades:
        if atividade.estado.terminal:
            continue
        cancelada = AtividadeSnapshot(
            id=atividade.id,
            tenant_id=atividade.tenant_id,
            os_id=atividade.os_id,
            tipo=atividade.tipo,
            sequencia=atividade.sequencia,
            estado=EstadoAtividade.CANCELADA,
            tecnico_executor_id=atividade.tecnico_executor_id,
            agendada_para=atividade.agendada_para,
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
        repository.salvar_atividade(cancelada)
        canceladas.append(atividade.id)

    # Recalcula valor (sum atividades nao-canceladas).
    todas = repository.listar_atividades_por_os(payload.os_id)
    novo_valor = calcular_valor_total_atualizado(todas)

    os_cancelada = OSSnapshot(
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
        estado=EstadoOS.CANCELADA,
        tipo_predominante=os_snapshot.tipo_predominante,
        nao_conformidade_global=os_snapshot.nao_conformidade_global,
        valor_total=os_snapshot.valor_total,
        valor_total_atualizado=novo_valor,
        analise_critica_id=os_snapshot.analise_critica_id,
        analise_critica_snapshot_hash=os_snapshot.analise_critica_snapshot_hash,
        regra_decisao_acordada=os_snapshot.regra_decisao_acordada,
        criada_em=os_snapshot.criada_em,
        atualizada_em=payload.cancelada_em,
        criada_por_user_id=os_snapshot.criada_por_user_id,
    )
    repository.salvar_os(os_cancelada)

    ev_payload: dict[str, object] = {
        "motivo_hash": motivo_hash,
        "atividades_canceladas": [str(aid) for aid in canceladas],
        "valor_total_atualizado": str(novo_valor),
    }
    ev_canonico = json.dumps(ev_payload, sort_keys=True, ensure_ascii=False)
    ev_hash = hashlib.sha256(ev_canonico.encode("utf-8")).hexdigest()  # audit-pii-salt: skip -- payload sanitizado
    repository.publicar_evento(
        EventoDeOSSnapshot(
            id=uuid4(),
            tenant_id=os_snapshot.tenant_id,
            os_id=payload.os_id,
            atividade_id=None,
            tipo=TipoEventoDeOS.OS_CANCELADA,
            payload_hash=ev_hash,
            payload_data=ev_payload,
            correlation_id=payload.correlation_id,
            actor_user_id=payload.usuario_id,
            occurred_at=payload.cancelada_em,
            criado_em=payload.cancelada_em,
        )
    )

    return CancelarOSResultado(
        os_id=payload.os_id,
        atividades_canceladas=tuple(canceladas),
        correlation_id=payload.correlation_id,
    )
