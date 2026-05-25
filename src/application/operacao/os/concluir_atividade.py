"""Use case `concluir_atividade` — T-OS-059..060 (Fase 5).

Cobre AC-OS-004-1 (happy), AC-OS-004-3 (OS->CONCLUIDA + tipo_predominante),
AC-OS-004-4 (403 NaoEExecutor).

ACs deferidos (caller responsavel ou outra fatia):
- AC-OS-004-2 (checklist 100% preenchido): caller faz pre-check com
  `repository.listar_checklist_por_atividade` antes; aqui o use case
  CONFIRMA via repository (412 ChecklistIncompleto se algum estado=PENDENTE).
- AC-OS-004-5 (watchdog cal-link): job procrastinate Fase 7 (T-OS-061).
- AC-OS-004-6 (portal-cliente + OmniChannel): consumer bus Wave A.
- AC-OS-004-7 (consentimento biometria touch antes de aceite): cobre em
  `coletar_aceite_atividade` (T-OS-063, Bloco 4); aqui o use case so VERIFICA
  presenca de aceite quando tipo exigir.

Use case puro. Caller (consumer/view) que aplica `audit/event_helpers.
publicar_evento(acao='AtividadeConcluida', ...)` pro bus.
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
from src.domain.operacao.os.regras import (
    atividade_pode_ser_concluida_por,
    calcular_tipo_predominante,
    os_deve_transitar_concluida,
)
from src.domain.operacao.os.repository import OSRepository
from src.domain.operacao.os.value_objects import (
    EstadoAtividade,
    EstadoChecklistItem,
    EstadoOS,
    TipoAtividade,
    TipoEventoDeOS,
)

# Tipos que exigem AceiteAtividade antes de concluir (regra de negocio).
_TIPOS_EXIGEM_ACEITE: frozenset[TipoAtividade] = frozenset(
    {
        TipoAtividade.CALIBRACAO,
        TipoAtividade.VERIFICACAO_INMETRO,
        TipoAtividade.MANUTENCAO_CORRETIVA,
        TipoAtividade.INSTALACAO,
    }
)


@dataclass(frozen=True, slots=True)
class ConcluirAtividadeInput:
    atividade_id: UUID
    usuario_id: UUID
    correlation_id: UUID
    concluida_em: datetime
    aceite_dispensado: bool = False


@dataclass(frozen=True, slots=True)
class ConcluirAtividadeResultado:
    atividade_id: UUID
    os_id: UUID
    os_transitou_para_concluida: bool
    tipo_predominante: str
    correlation_id: UUID


class ErroConcluirAtividade(Exception):
    def __init__(self, codigo: str, http_status: int, detalhe: str = "") -> None:
        super().__init__(f"{codigo}: {detalhe}" if detalhe else codigo)
        self.codigo = codigo
        self.http_status = http_status
        self.detalhe = detalhe


def concluir_atividade(
    *,
    payload: ConcluirAtividadeInput,
    repository: OSRepository,
) -> ConcluirAtividadeResultado:
    """Transiciona atividade EM_EXECUCAO -> CONCLUIDA + agrega OS quando todas terminais."""
    atividade = repository.get_atividade_by_id(payload.atividade_id)
    if atividade is None:
        raise ErroConcluirAtividade("AtividadeNaoEncontrada", 404)

    # AC-OS-004-4: executor designado eh unico autorizado.
    if not atividade_pode_ser_concluida_por(atividade, payload.usuario_id):
        if atividade.tecnico_executor_id != payload.usuario_id:
            raise ErroConcluirAtividade("NaoEExecutor", 403)
        raise ErroConcluirAtividade(
            "AtividadeEmEstadoIncompativel",
            412,
            detalhe=f"estado={atividade.estado.value}; concluir so de EM_EXECUCAO",
        )

    # AC-OS-004-2: checklist 100% (qualquer item PENDENTE -> 412).
    checklist = repository.listar_checklist_por_atividade(payload.atividade_id)
    pendentes = [c for c in checklist if c.estado == EstadoChecklistItem.PENDENTE]
    if pendentes:
        raise ErroConcluirAtividade(
            "ChecklistIncompleto",
            412,
            detalhe=f"itens_pendentes={[c.ordem for c in pendentes]}",
        )

# AC-OS-004-1: tipo que exige aceite -> precisa AceiteAtividade OU DispensaAceiteAtividade.
    # PROD-M3-04 (P5 conserto 2026-05-24): dispensa eh CONSULTADA no repository
    # em vez de confiar no flag boolean enviado pelo caller. O flag continua
    # aceito como override explicito (legitimo pra fluxos de retry/dogfooding
    # onde dispensa ainda nao foi gravada). Padrao recomendado: caller NAO
    # passa flag — use case consulta dispensa real.
    aceite_dispensado_efetivo = payload.aceite_dispensado
    if atividade.tipo in _TIPOS_EXIGEM_ACEITE and not aceite_dispensado_efetivo:
        dispensa = repository.get_dispensa_por_atividade(payload.atividade_id)
        if dispensa is not None:
            aceite_dispensado_efetivo = True
    if atividade.tipo in _TIPOS_EXIGEM_ACEITE and not aceite_dispensado_efetivo:
        aceite = repository.get_aceite_por_atividade(payload.atividade_id)
        if aceite is None:
            raise ErroConcluirAtividade(
                "AceiteAusente",
                412,
                detalhe=f"tipo={atividade.tipo.value} exige aceite OU dispensa formal",
            )

    # Transicao da atividade.
    atualizada = AtividadeSnapshot(
        id=atividade.id,
        tenant_id=atividade.tenant_id,
        os_id=atividade.os_id,
        tipo=atividade.tipo,
        sequencia=atividade.sequencia,
        estado=EstadoAtividade.CONCLUIDA,
        tecnico_executor_id=atividade.tecnico_executor_id,
        agendada_para=atividade.agendada_para,
        iniciada_em=atividade.iniciada_em,
        concluida_em=payload.concluida_em,
        valor_unitario_snapshot=atividade.valor_unitario_snapshot,
        link_modulo_tecnico_id=atividade.link_modulo_tecnico_id,
        geo_lat=atividade.geo_lat,
        geo_long=atividade.geo_long,
        geo_municipio_hash=atividade.geo_municipio_hash,
        equipamento_id_desnormalizado=atividade.equipamento_id_desnormalizado,
        tipo_bloqueia_concorrencia=atividade.tipo_bloqueia_concorrencia,
    )
    repository.salvar_atividade(atualizada)

    # AC-OS-004-3: OS transita para CONCLUIDA se TODAS atividades terminais.
    os_snapshot = repository.get_os_by_id(atividade.os_id)
    if os_snapshot is None:
        raise ErroConcluirAtividade("OSNaoEncontrada", 404)
    todas_atividades = repository.listar_atividades_por_os(atividade.os_id)
    transitou_os = False
    tipo_predominante = os_snapshot.tipo_predominante
    if os_deve_transitar_concluida(todas_atividades):
        tipo_predominante = calcular_tipo_predominante(todas_atividades)
        os_concluida = OSSnapshot(
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
            estado=EstadoOS.CONCLUIDA,
            tipo_predominante=tipo_predominante,
            nao_conformidade_global=any(
                a.estado == EstadoAtividade.NAO_CONFORME for a in todas_atividades
            ),
            valor_total=os_snapshot.valor_total,
            valor_total_atualizado=os_snapshot.valor_total_atualizado,
            analise_critica_id=os_snapshot.analise_critica_id,
            analise_critica_snapshot_hash=os_snapshot.analise_critica_snapshot_hash,
            regra_decisao_acordada=os_snapshot.regra_decisao_acordada,
            criada_em=os_snapshot.criada_em,
            atualizada_em=payload.concluida_em,
            criada_por_user_id=os_snapshot.criada_por_user_id,
        )
        repository.salvar_os(os_concluida)
        transitou_os = True

    # EventoDeOS — atividade concluida (sempre) + os concluida (condicional).
    ev_payload: dict[str, object] = {
        "atividade_id": str(atividade.id),
        "tipo": atividade.tipo.value,
        "os_transitou_para_concluida": transitou_os,
    }
    ev_canonico = json.dumps(ev_payload, sort_keys=True, ensure_ascii=False)
    ev_hash = hashlib.sha256(ev_canonico.encode("utf-8")).hexdigest()  # audit-pii-salt: skip -- payload sanitizado
    repository.publicar_evento(
        EventoDeOSSnapshot(
            id=uuid4(),
            tenant_id=atividade.tenant_id,
            os_id=atividade.os_id,
            atividade_id=atividade.id,
            tipo=TipoEventoDeOS.ATIVIDADE_CONCLUIDA,
            payload_hash=ev_hash,
            payload_data=ev_payload,
            correlation_id=payload.correlation_id,
            actor_user_id=payload.usuario_id,
            occurred_at=payload.concluida_em,
            criado_em=payload.concluida_em,
        )
    )

    if transitou_os:
        os_ev_payload: dict[str, object] = {
            "tipo_predominante": tipo_predominante,
            "nao_conformidade_global": any(
                a.estado == EstadoAtividade.NAO_CONFORME for a in todas_atividades
            ),
        }
        os_canonico = json.dumps(os_ev_payload, sort_keys=True, ensure_ascii=False)
        os_hash = hashlib.sha256(os_canonico.encode("utf-8")).hexdigest()  # audit-pii-salt: skip -- payload sanitizado
        repository.publicar_evento(
            EventoDeOSSnapshot(
                id=uuid4(),
                tenant_id=atividade.tenant_id,
                os_id=atividade.os_id,
                atividade_id=None,
                tipo=TipoEventoDeOS.OS_CONCLUIDA,
                payload_hash=os_hash,
                payload_data=os_ev_payload,
                correlation_id=payload.correlation_id,
                actor_user_id=payload.usuario_id,
                occurred_at=payload.concluida_em,
                criado_em=payload.concluida_em,
            )
        )

    return ConcluirAtividadeResultado(
        atividade_id=atividade.id,
        os_id=atividade.os_id,
        os_transitou_para_concluida=transitou_os,
        tipo_predominante=tipo_predominante,
        correlation_id=payload.correlation_id,
    )
