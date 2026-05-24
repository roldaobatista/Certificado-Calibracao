"""Use case `adicionar_atividade` — T-OS-048 (Fase 5).

Cobre AC-OS-002-1, 2, 4 do PRD. AC-OS-002-3 (predicate
`tenant_tem_rt_ativo_competencia`) eh do CALLER: consumer/view chama
`src.infrastructure.ordens_servico.predicates_os.rt_competencia_cobre`
ANTES de invocar este use case.

Validacoes binarias:
- AC-OS-002-2: OS em CONCLUIDA/FATURADA/PAGA/CANCELADA -> 412
  `OSEmEstadoTerminal`.
- AC-OS-002-4: `sequencia` ≤ menor `sequencia` de atividade CONCLUIDA -> 412
  `SequenciaInvalidaPosTerminal` (linearidade — gate sequencia pos-terminal).

Apos validacoes, persiste `AtividadeDaOS` em PENDENTE + grava
`EventoDeOS(tipo='atividade_adicionada')` na timeline.

Camada APPLICATION pura: recebe `OSRepository` Protocol via DI.
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
)
from src.domain.operacao.os.repository import OSRepository
from src.domain.operacao.os.value_objects import (
    EstadoAtividade,
    EstadoOS,
    TipoAtividade,
    TipoEventoDeOS,
)


@dataclass(frozen=True, slots=True)
class AdicionarAtividadeInput:
    os_id: UUID
    tipo: TipoAtividade
    sequencia: int
    valor_unitario: Decimal
    correlation_id: UUID
    solicitada_em: datetime
    solicitada_por_user_id: UUID | None


@dataclass(frozen=True, slots=True)
class AdicionarAtividadeResultado:
    atividade_id: UUID
    os_id: UUID
    sequencia: int
    correlation_id: UUID


class ErroAdicionarAtividade(Exception):
    """Falha de regra ao adicionar atividade. Caller mapeia HTTP."""

    def __init__(self, codigo: str, http_status: int, detalhe: str = "") -> None:
        super().__init__(f"{codigo}: {detalhe}" if detalhe else codigo)
        self.codigo = codigo
        self.http_status = http_status
        self.detalhe = detalhe


def adicionar_atividade(
    *,
    payload: AdicionarAtividadeInput,
    repository: OSRepository,
) -> AdicionarAtividadeResultado:
    """Adiciona nova `AtividadeDaOS` em PENDENTE a uma OS nao-terminal."""
    os_snapshot = repository.get_os_by_id(payload.os_id)
    if os_snapshot is None:
        raise ErroAdicionarAtividade("OSNaoEncontrada", 404)

    # AC-OS-002-2: estado-maquina nao aceita atividade nova em terminal.
    estados_nao_aceitam = {
        EstadoOS.CONCLUIDA,
        EstadoOS.FATURADA,
        EstadoOS.PAGA,
        EstadoOS.CANCELADA,
    }
    if os_snapshot.estado in estados_nao_aceitam:
        raise ErroAdicionarAtividade(
            "OSEmEstadoTerminal",
            412,
            detalhe=f"estado={os_snapshot.estado.value}; abra reabertura",
        )

    # AC-OS-002-4: sequencia <= menor sequencia de atividade CONCLUIDA -> 412.
    existentes = repository.listar_atividades_por_os(payload.os_id)
    concluidas_seqs = [
        a.sequencia for a in existentes if a.estado == EstadoAtividade.CONCLUIDA
    ]
    if concluidas_seqs and payload.sequencia <= min(concluidas_seqs):
        raise ErroAdicionarAtividade(
            "SequenciaInvalidaPosTerminal",
            412,
            detalhe=f"sequencia={payload.sequencia} <= menor concluida={min(concluidas_seqs)}",
        )

    # Persiste atividade nova.
    atividade_id = uuid4()
    atividade_snapshot = AtividadeSnapshot(
        id=atividade_id,
        tenant_id=os_snapshot.tenant_id,
        os_id=payload.os_id,
        tipo=payload.tipo,
        sequencia=payload.sequencia,
        estado=EstadoAtividade.PENDENTE,
        tecnico_executor_id=None,
        agendada_para=None,
        iniciada_em=None,
        concluida_em=None,
        valor_unitario_snapshot=payload.valor_unitario,
        link_modulo_tecnico_id=None,
        geo_lat=None,
        geo_long=None,
        geo_municipio_hash="",
        equipamento_id_desnormalizado=None,  # trigger preenche
        tipo_bloqueia_concorrencia=False,  # trigger preenche
    )
    repository.salvar_atividade(atividade_snapshot)

    # EventoDeOS — timeline local.
    payload_evento: dict[str, object] = {
        "atividade_id": str(atividade_id),
        "tipo": payload.tipo.value,
        "sequencia": payload.sequencia,
    }
    payload_canonico = json.dumps(payload_evento, sort_keys=True, ensure_ascii=False)
    payload_hash = hashlib.sha256(payload_canonico.encode("utf-8")).hexdigest()  # audit-pii-salt: skip -- payload do EventoDeOS ja sanitizado sem PII cru
    repository.publicar_evento(
        EventoDeOSSnapshot(
            id=uuid4(),
            tenant_id=os_snapshot.tenant_id,
            os_id=payload.os_id,
            atividade_id=atividade_id,
            tipo=TipoEventoDeOS.ATIVIDADE_ADICIONADA,
            payload_hash=payload_hash,
            payload_data=payload_evento,
            correlation_id=payload.correlation_id,
            actor_user_id=payload.solicitada_por_user_id,
            occurred_at=payload.solicitada_em,
            criado_em=payload.solicitada_em,
        )
    )

    return AdicionarAtividadeResultado(
        atividade_id=atividade_id,
        os_id=payload.os_id,
        sequencia=payload.sequencia,
        correlation_id=payload.correlation_id,
    )
