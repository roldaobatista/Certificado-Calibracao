"""Use cases avancados — Bloco 5+6 da Fase 5 (T-OS-066/077/078/079/082/083).

Use cases puros agregados:

- `reabrir_os` (T-OS-066): OS terminal -> cria NOVA OS com `os_origem_id` +
  clona atividades em PENDENTE.
- `transferir_tecnico` (T-OS-078): atividade nao-terminal -> atualiza
  `tecnico_executor_id` + motivo + EventoDeOS.
- `reagendar_atividade` (T-OS-077): atividade PENDENTE/AGENDADA ->
  atualiza `agendada_para` + EventoDeOS.
- `dispensar_aceite_cliente` (T-OS-079): cria DispensaAceiteAtividade
  (Padrao B imutavel) com precedente (no-show/recusa) + a3_assinatura_hash
  + termo_pdf canonicalizado.
- `marcar_no_show` (T-OS-082): atividade AGENDADA -> permanece PENDENTE/
  AGENDADA + EventoDeOS no_show_cliente + foto evidencia + aviso terceiros
  ack.
- `criar_os_avulsa` (T-OS-083): cria OS sem orcamento_origem +
  valor_unitario_snapshot da tabela vigente.

Para `dispensar_aceite_cliente`: precedente (no-show OU recusa explicita)
eh validado pelo CALLER via predicates_os.pode_dispensar_aceite.
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
    DispensaAceiteAtividadeSnapshot,
    EventoDeOSSnapshot,
    EvidenciaFotoAtividadeSnapshot,
    OSSnapshot,
)
from src.domain.operacao.os.repository import OSRepository
from src.domain.operacao.os.value_objects import (
    EstadoAtividade,
    EstadoOS,
    MotivoCancelamento,
    PrecedenteDispensa,
    TipoAtividade,
    TipoEventoDeOS,
    TipoFotoEvidencia,
)

# =============================================================
# reabrir_os
# =============================================================


@dataclass(frozen=True, slots=True)
class ReabrirOSInput:
    os_origem_id: UUID
    motivo: MotivoCancelamento
    garantia_procedente: bool
    chamado_origem_id: UUID | None
    sucessao_societaria_id: UUID | None
    correlation_id: UUID
    reaberta_em: datetime
    reaberta_por_user_id: UUID | None


@dataclass(frozen=True, slots=True)
class ReabrirOSResultado:
    os_id_nova: UUID
    numero_os_nova: int
    os_origem_id: UUID
    atividades_clonadas: tuple[UUID, ...]
    correlation_id: UUID


class ErroReabrir(Exception):
    def __init__(self, codigo: str, http_status: int, detalhe: str = "") -> None:
        super().__init__(f"{codigo}: {detalhe}" if detalhe else codigo)
        self.codigo = codigo
        self.http_status = http_status
        self.detalhe = detalhe


def reabrir_os(
    *,
    payload: ReabrirOSInput,
    repository: OSRepository,
) -> ReabrirOSResultado:
    """Cria nova OS-filha + clona atividades em PENDENTE (sequencia=1..N)."""
    os_mae = repository.get_os_by_id(payload.os_origem_id)
    if os_mae is None:
        raise ErroReabrir("OSMaeNaoEncontrada", 404)
    # AC-OS-006-1: so reabre CONCLUIDA/FATURADA/PAGA.
    if os_mae.estado not in {EstadoOS.CONCLUIDA, EstadoOS.FATURADA, EstadoOS.PAGA}:
        raise ErroReabrir(
            "OSMaeNaoTerminal",
            412,
            detalhe=f"estado={os_mae.estado.value}; reabrir so CONCLUIDA/FATURADA/PAGA",
        )

    # AC-OS-006-6/7 — INV-OS-SUC-001: cliente anonimizado precisa de
    # sucessao_societaria_id.
    if os_mae.cliente_id is None and payload.sucessao_societaria_id is None:
        raise ErroReabrir(
            "ClienteAnonimizadoSemSucessao",
            412,
            detalhe="OS-mae em cliente anonimizado exige sucessao_societaria_id",
        )

    novo_numero = repository.proximo_numero_os()
    os_id_nova = uuid4()
    nova = OSSnapshot(
        id=os_id_nova,
        tenant_id=os_mae.tenant_id,  # AC-OS-006-2: mesmo tenant
        numero_os=novo_numero,
        cliente_id=os_mae.cliente_id,
        cliente_referencia_hash=os_mae.cliente_referencia_hash,  # preserva
        cliente_key_id=os_mae.cliente_key_id,
        equipamento_id=os_mae.equipamento_id,
        equipamento_recebimento_id=os_mae.equipamento_recebimento_id,
        orcamento_origem_id=None,
        os_origem_id=os_mae.id,
        sucessao_societaria_id=payload.sucessao_societaria_id,
        estado=EstadoOS.RASCUNHO,
        tipo_predominante="",
        nao_conformidade_global=False,
        valor_total=Decimal("0"),
        valor_total_atualizado=Decimal("0"),
        analise_critica_id=os_mae.analise_critica_id,
        analise_critica_snapshot_hash=os_mae.analise_critica_snapshot_hash,
        regra_decisao_acordada=os_mae.regra_decisao_acordada,
        criada_em=payload.reaberta_em,
        atualizada_em=payload.reaberta_em,
        criada_por_user_id=payload.reaberta_por_user_id,
    )
    repository.salvar_os(nova)

    # Clona atividades (PENDENTE + sequencia=1..N).
    atividades_mae = repository.listar_atividades_por_os(os_mae.id)
    clonadas: list[UUID] = []
    valor_total_novo = Decimal("0")
    for idx, ativ in enumerate(atividades_mae, start=1):
        clone_id = uuid4()
        clone = AtividadeSnapshot(
            id=clone_id,
            tenant_id=os_mae.tenant_id,
            os_id=os_id_nova,
            tipo=ativ.tipo,
            sequencia=idx,
            estado=EstadoAtividade.PENDENTE,
            tecnico_executor_id=None,
            agendada_para=None,
            iniciada_em=None,
            concluida_em=None,
            valor_unitario_snapshot=ativ.valor_unitario_snapshot,
            link_modulo_tecnico_id=None,
            geo_lat=None,
            geo_long=None,
            geo_municipio_hash="",
            equipamento_id_desnormalizado=None,
            tipo_bloqueia_concorrencia=False,
        )
        repository.salvar_atividade(clone)
        clonadas.append(clone_id)
        valor_total_novo += ativ.valor_unitario_snapshot

    # Atualiza valor total da OS-filha.
    nova_com_valor = OSSnapshot(
        id=nova.id,
        tenant_id=nova.tenant_id,
        numero_os=nova.numero_os,
        cliente_id=nova.cliente_id,
        cliente_referencia_hash=nova.cliente_referencia_hash,
        cliente_key_id=nova.cliente_key_id,
        equipamento_id=nova.equipamento_id,
        equipamento_recebimento_id=nova.equipamento_recebimento_id,
        orcamento_origem_id=nova.orcamento_origem_id,
        os_origem_id=nova.os_origem_id,
        sucessao_societaria_id=nova.sucessao_societaria_id,
        estado=nova.estado,
        tipo_predominante=nova.tipo_predominante,
        nao_conformidade_global=nova.nao_conformidade_global,
        valor_total=valor_total_novo,
        valor_total_atualizado=valor_total_novo,
        analise_critica_id=nova.analise_critica_id,
        analise_critica_snapshot_hash=nova.analise_critica_snapshot_hash,
        regra_decisao_acordada=nova.regra_decisao_acordada,
        criada_em=nova.criada_em,
        atualizada_em=nova.atualizada_em,
        criada_por_user_id=nova.criada_por_user_id,
    )
    repository.salvar_os(nova_com_valor)

    # EventoDeOS reaberta (na OS-FILHA, nao na mae).
    ev_payload: dict[str, object] = {
        "os_origem_id": str(os_mae.id),
        "chamado_origem_id": str(payload.chamado_origem_id)
        if payload.chamado_origem_id
        else None,
        "garantia_procedente": payload.garantia_procedente,
        "sucessao_societaria_id": str(payload.sucessao_societaria_id)
        if payload.sucessao_societaria_id
        else None,
    }
    ev_canonico = json.dumps(ev_payload, sort_keys=True, ensure_ascii=False)
    ev_hash = hashlib.sha256(ev_canonico.encode("utf-8")).hexdigest()  # audit-pii-salt: skip -- payload sanitizado
    repository.publicar_evento(
        EventoDeOSSnapshot(
            id=uuid4(),
            tenant_id=os_mae.tenant_id,
            os_id=os_id_nova,
            atividade_id=None,
            tipo=TipoEventoDeOS.OS_REABERTA,
            payload_hash=ev_hash,
            payload_data=ev_payload,
            correlation_id=payload.correlation_id,
            actor_user_id=payload.reaberta_por_user_id,
            occurred_at=payload.reaberta_em,
            criado_em=payload.reaberta_em,
        )
    )

    return ReabrirOSResultado(
        os_id_nova=os_id_nova,
        numero_os_nova=novo_numero,
        os_origem_id=os_mae.id,
        atividades_clonadas=tuple(clonadas),
        correlation_id=payload.correlation_id,
    )


# =============================================================
# transferir_tecnico
# =============================================================


@dataclass(frozen=True, slots=True)
class TransferirTecnicoInput:
    atividade_id: UUID
    novo_tecnico_id: UUID
    motivo: MotivoCancelamento
    correlation_id: UUID
    transferida_em: datetime
    solicitada_por_user_id: UUID | None


@dataclass(frozen=True, slots=True)
class TransferirTecnicoResultado:
    atividade_id: UUID
    novo_tecnico_id: UUID
    correlation_id: UUID


class ErroTransferir(Exception):
    def __init__(self, codigo: str, http_status: int, detalhe: str = "") -> None:
        super().__init__(f"{codigo}: {detalhe}" if detalhe else codigo)
        self.codigo = codigo
        self.http_status = http_status
        self.detalhe = detalhe


def transferir_tecnico(
    *,
    payload: TransferirTecnicoInput,
    repository: OSRepository,
) -> TransferirTecnicoResultado:
    """Atualiza tecnico_executor_id em atividade PENDENTE/AGENDADA."""
    atividade = repository.get_atividade_by_id(payload.atividade_id)
    if atividade is None:
        raise ErroTransferir("AtividadeNaoEncontrada", 404)
    if atividade.estado not in {EstadoAtividade.PENDENTE, EstadoAtividade.AGENDADA}:
        raise ErroTransferir(
            "AtividadeEmEstadoIncompativel",
            412,
            detalhe=f"estado={atividade.estado.value}; transferencia so em PENDENTE/AGENDADA",
        )

    motivo_hash = hashlib.sha256(
        payload.motivo.texto.encode("utf-8")
    ).hexdigest()  # audit-pii-salt: skip -- VO bloqueia PII; integrity hash

    atualizada = AtividadeSnapshot(
        id=atividade.id,
        tenant_id=atividade.tenant_id,
        os_id=atividade.os_id,
        tipo=atividade.tipo,
        sequencia=atividade.sequencia,
        estado=atividade.estado,
        tecnico_executor_id=payload.novo_tecnico_id,
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
    repository.salvar_atividade(atualizada)

    ev_payload: dict[str, object] = {
        "atividade_id": str(atividade.id),
        "motivo_hash": motivo_hash,
    }
    ev_canonico = json.dumps(ev_payload, sort_keys=True, ensure_ascii=False)
    ev_hash = hashlib.sha256(ev_canonico.encode("utf-8")).hexdigest()  # audit-pii-salt: skip -- payload sanitizado
    repository.publicar_evento(
        EventoDeOSSnapshot(
            id=uuid4(),
            tenant_id=atividade.tenant_id,
            os_id=atividade.os_id,
            atividade_id=atividade.id,
            tipo=TipoEventoDeOS.ATIVIDADE_TECNICO_TRANSFERIDO,
            payload_hash=ev_hash,
            payload_data=ev_payload,
            correlation_id=payload.correlation_id,
            actor_user_id=payload.solicitada_por_user_id,
            occurred_at=payload.transferida_em,
            criado_em=payload.transferida_em,
        )
    )

    return TransferirTecnicoResultado(
        atividade_id=atividade.id,
        novo_tecnico_id=payload.novo_tecnico_id,
        correlation_id=payload.correlation_id,
    )


# =============================================================
# reagendar_atividade
# =============================================================


@dataclass(frozen=True, slots=True)
class ReagendarAtividadeInput:
    atividade_id: UUID
    nova_agendada_para: datetime
    correlation_id: UUID
    solicitada_em: datetime
    solicitada_por_user_id: UUID | None


@dataclass(frozen=True, slots=True)
class ReagendarAtividadeResultado:
    atividade_id: UUID
    nova_agendada_para: datetime
    correlation_id: UUID


def reagendar_atividade(
    *,
    payload: ReagendarAtividadeInput,
    repository: OSRepository,
) -> ReagendarAtividadeResultado:
    atividade = repository.get_atividade_by_id(payload.atividade_id)
    if atividade is None:
        raise ErroTransferir("AtividadeNaoEncontrada", 404)
    if atividade.estado not in {EstadoAtividade.PENDENTE, EstadoAtividade.AGENDADA}:
        raise ErroTransferir(
            "AtividadeEmEstadoIncompativel",
            412,
            detalhe=f"estado={atividade.estado.value}; reagendar so em PENDENTE/AGENDADA",
        )

    atualizada = AtividadeSnapshot(
        id=atividade.id,
        tenant_id=atividade.tenant_id,
        os_id=atividade.os_id,
        tipo=atividade.tipo,
        sequencia=atividade.sequencia,
        estado=atividade.estado,
        tecnico_executor_id=atividade.tecnico_executor_id,
        agendada_para=payload.nova_agendada_para,
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

    ev_payload: dict[str, object] = {
        "atividade_id": str(atividade.id),
        "nova_agendada_para": payload.nova_agendada_para.isoformat(),
    }
    ev_canonico = json.dumps(ev_payload, sort_keys=True, ensure_ascii=False)
    ev_hash = hashlib.sha256(ev_canonico.encode("utf-8")).hexdigest()  # audit-pii-salt: skip -- payload sanitizado
    repository.publicar_evento(
        EventoDeOSSnapshot(
            id=uuid4(),
            tenant_id=atividade.tenant_id,
            os_id=atividade.os_id,
            atividade_id=atividade.id,
            tipo=TipoEventoDeOS.ATIVIDADE_REAGENDADA,
            payload_hash=ev_hash,
            payload_data=ev_payload,
            correlation_id=payload.correlation_id,
            actor_user_id=payload.solicitada_por_user_id,
            occurred_at=payload.solicitada_em,
            criado_em=payload.solicitada_em,
        )
    )

    return ReagendarAtividadeResultado(
        atividade_id=atividade.id,
        nova_agendada_para=payload.nova_agendada_para,
        correlation_id=payload.correlation_id,
    )


# =============================================================
# dispensar_aceite_cliente
# =============================================================


@dataclass(frozen=True, slots=True)
class DispensarAceiteInput:
    atividade_id: UUID
    motivo: MotivoCancelamento
    autorizado_por_gerente_id: UUID
    a3_assinatura_hash: str
    a3_certificado_emissor_hash: str
    a3_assinada_em: datetime
    termo_pdf_b2_uri: str
    termo_pdf_sha256: str
    precedente_tipo: PrecedenteDispensa
    precedente_evento_id: UUID | None
    correlation_id: UUID
    solicitada_em: datetime


@dataclass(frozen=True, slots=True)
class DispensarAceiteResultado:
    dispensa_id: UUID
    atividade_id: UUID
    correlation_id: UUID


class ErroDispensar(Exception):
    def __init__(self, codigo: str, http_status: int, detalhe: str = "") -> None:
        super().__init__(f"{codigo}: {detalhe}" if detalhe else codigo)
        self.codigo = codigo
        self.http_status = http_status
        self.detalhe = detalhe


def dispensar_aceite_cliente(
    *,
    payload: DispensarAceiteInput,
    repository: OSRepository,
) -> DispensarAceiteResultado:
    """Cria DispensaAceiteAtividade (Padrao B imutavel) — P-OS-A4 + CDC art. 39."""
    atividade = repository.get_atividade_by_id(payload.atividade_id)
    if atividade is None:
        raise ErroDispensar("AtividadeNaoEncontrada", 404)
    if atividade.estado != EstadoAtividade.EM_EXECUCAO:
        raise ErroDispensar(
            "AtividadeEmEstadoIncompativel",
            412,
            detalhe=f"estado={atividade.estado.value}; dispensa so em EM_EXECUCAO",
        )

    # AC-OS-013-5 (P-OS-A4): dispensa exige precedente (no-show OU recusa OU
    # impossibilidade) + a3_assinatura_hash NAO VAZIA + termo_pdf canonicalizado.
    if not payload.a3_assinatura_hash:
        raise ErroDispensar(
            "A3AssinaturaAusente", 412, detalhe="P-OS-A4 exige A3 gerente"
        )
    if not payload.termo_pdf_sha256 or not payload.termo_pdf_b2_uri:
        raise ErroDispensar(
            "TermoPDFAusente",
            412,
            detalhe="P-OS-A4 exige TermoDispensaAceite canonicalizado",
        )
    if (
        payload.precedente_tipo
        in {PrecedenteDispensa.NO_SHOW, PrecedenteDispensa.RECUSA_EXPLICITA}
        and payload.precedente_evento_id is None
    ):
        raise ErroDispensar(
            "DispensaSemPrecedente",
            412,
            detalhe="precedente_tipo no_show/recusa exige precedente_evento_id",
        )

    # Existe ja?
    existente = repository.get_dispensa_por_atividade(payload.atividade_id)
    if existente is not None:
        raise ErroDispensar("DispensaJaEmitida", 409)

    motivo_hash = hashlib.sha256(
        payload.motivo.texto.encode("utf-8")
    ).hexdigest()  # audit-pii-salt: skip -- VO bloqueia PII; integrity hash

    dispensa_id = uuid4()
    snapshot = DispensaAceiteAtividadeSnapshot(
        id=dispensa_id,
        tenant_id=atividade.tenant_id,
        atividade_id=atividade.id,
        motivo_hash=motivo_hash,
        autorizado_por_gerente_id=payload.autorizado_por_gerente_id,
        a3_assinatura_hash=payload.a3_assinatura_hash,
        a3_certificado_emissor_hash=payload.a3_certificado_emissor_hash,
        a3_assinada_em=payload.a3_assinada_em,
        termo_pdf_b2_uri=payload.termo_pdf_b2_uri,
        termo_pdf_sha256=payload.termo_pdf_sha256,
        precedente_tipo=payload.precedente_tipo,
        precedente_evento_id=payload.precedente_evento_id,
        criado_em=payload.solicitada_em,
    )
    repository.salvar_dispensa(snapshot)

    ev_payload: dict[str, object] = {
        "atividade_id": str(atividade.id),
        "dispensa_id": str(dispensa_id),
        "precedente_tipo": payload.precedente_tipo.value,
    }
    ev_canonico = json.dumps(ev_payload, sort_keys=True, ensure_ascii=False)
    ev_hash = hashlib.sha256(ev_canonico.encode("utf-8")).hexdigest()  # audit-pii-salt: skip -- payload sanitizado
    repository.publicar_evento(
        EventoDeOSSnapshot(
            id=uuid4(),
            tenant_id=atividade.tenant_id,
            os_id=atividade.os_id,
            atividade_id=atividade.id,
            tipo=TipoEventoDeOS.DISPENSA_ACEITE_EMITIDA,
            payload_hash=ev_hash,
            payload_data=ev_payload,
            correlation_id=payload.correlation_id,
            actor_user_id=payload.autorizado_por_gerente_id,
            occurred_at=payload.solicitada_em,
            criado_em=payload.solicitada_em,
        )
    )

    return DispensarAceiteResultado(
        dispensa_id=dispensa_id,
        atividade_id=atividade.id,
        correlation_id=payload.correlation_id,
    )


# =============================================================
# marcar_no_show
# =============================================================


@dataclass(frozen=True, slots=True)
class MarcarNoShowInput:
    atividade_id: UUID
    tecnico_user_id: UUID
    foto_b2_uri: str
    foto_sha256: str
    client_event_id: UUID
    client_event_created_at: datetime
    aviso_terceiros_acknowledged: bool
    correlation_id: UUID
    ocorrido_em: datetime
    geo_lat: float | None = None
    geo_long: float | None = None
    geo_municipio_hash: str = ""


@dataclass(frozen=True, slots=True)
class MarcarNoShowResultado:
    atividade_id: UUID
    foto_id: UUID
    correlation_id: UUID


class ErroNoShow(Exception):
    def __init__(self, codigo: str, http_status: int, detalhe: str = "") -> None:
        super().__init__(f"{codigo}: {detalhe}" if detalhe else codigo)
        self.codigo = codigo
        self.http_status = http_status
        self.detalhe = detalhe


def marcar_no_show(
    *,
    payload: MarcarNoShowInput,
    repository: OSRepository,
) -> MarcarNoShowResultado:
    """Registra no-show + foto evidencia (Padrao B append-only)."""
    atividade = repository.get_atividade_by_id(payload.atividade_id)
    if atividade is None:
        raise ErroNoShow("AtividadeNaoEncontrada", 404)
    if atividade.estado != EstadoAtividade.AGENDADA:
        raise ErroNoShow(
            "AtividadeEmEstadoIncompativel",
            412,
            detalhe=f"estado={atividade.estado.value}; no-show so em AGENDADA",
        )

    # AC-OS-014-3 (P-OS-A5): aviso terceiros obrigatorio antes de salvar foto.
    if not payload.aviso_terceiros_acknowledged:
        raise ErroNoShow(
            "AvisoTerceirosNaoReconhecido",
            412,
            detalhe="P-OS-A5 exige aviso UX explicito antes da foto",
        )

    foto_id = uuid4()
    foto_snapshot = EvidenciaFotoAtividadeSnapshot(
        id=foto_id,
        tenant_id=atividade.tenant_id,
        atividade_id=atividade.id,
        tipo=TipoFotoEvidencia.NO_SHOW,
        b2_uri=payload.foto_b2_uri,
        foto_sha256=payload.foto_sha256,
        client_event_id=payload.client_event_id,
        client_event_created_at=payload.client_event_created_at,
        enviada_em=payload.ocorrido_em,
        tecnico_executor_id=payload.tecnico_user_id,
        geo_lat=payload.geo_lat,
        geo_long=payload.geo_long,
        geo_municipio_hash=payload.geo_municipio_hash,
        revogado_em=None,
        criado_em=payload.ocorrido_em,
    )
    repository.salvar_evidencia_foto(foto_snapshot)

    ev_payload: dict[str, object] = {
        "atividade_id": str(atividade.id),
        "foto_id": str(foto_id),
        "foto_sha256": payload.foto_sha256,
    }
    ev_canonico = json.dumps(ev_payload, sort_keys=True, ensure_ascii=False)
    ev_hash = hashlib.sha256(ev_canonico.encode("utf-8")).hexdigest()  # audit-pii-salt: skip -- payload sanitizado
    repository.publicar_evento(
        EventoDeOSSnapshot(
            id=uuid4(),
            tenant_id=atividade.tenant_id,
            os_id=atividade.os_id,
            atividade_id=atividade.id,
            tipo=TipoEventoDeOS.NO_SHOW_CLIENTE,
            payload_hash=ev_hash,
            payload_data=ev_payload,
            correlation_id=payload.correlation_id,
            actor_user_id=payload.tecnico_user_id,
            occurred_at=payload.ocorrido_em,
            criado_em=payload.ocorrido_em,
        )
    )

    return MarcarNoShowResultado(
        atividade_id=atividade.id,
        foto_id=foto_id,
        correlation_id=payload.correlation_id,
    )


# =============================================================
# criar_os_avulsa
# =============================================================


@dataclass(frozen=True, slots=True)
class ItemOSAvulsa:
    tipo: TipoAtividade
    sequencia: int
    valor_unitario_snapshot: Decimal  # da tabela vigente NA DATA (INV-CLI-PRICE-001)
    requer_recebimento: bool


@dataclass(frozen=True, slots=True)
class CriarOSAvulsaInput:
    tenant_id: UUID
    cliente_id: UUID
    cliente_referencia_hash: str
    cliente_key_id: str
    equipamento_id: UUID
    equipamento_recebimento_id: UUID | None
    itens: tuple[ItemOSAvulsa, ...]
    analise_critica_inline_id: UUID  # AC-OS-001-7 — analise inline obrigatoria
    analise_critica_snapshot_hash: str
    regra_decisao_acordada: str
    correlation_id: UUID
    criada_em: datetime
    criada_por_user_id: UUID | None


@dataclass(frozen=True, slots=True)
class CriarOSAvulsaResultado:
    os_id: UUID
    numero_os: int
    atividades_planejadas: tuple[UUID, ...]
    correlation_id: UUID


class ErroOSAvulsa(Exception):
    def __init__(self, codigo: str, http_status: int, detalhe: str = "") -> None:
        super().__init__(f"{codigo}: {detalhe}" if detalhe else codigo)
        self.codigo = codigo
        self.http_status = http_status
        self.detalhe = detalhe


def criar_os_avulsa(
    *,
    payload: CriarOSAvulsaInput,
    repository: OSRepository,
) -> CriarOSAvulsaResultado:
    """Cria OS sem orcamento_origem (balcao) + atividades com preco vigente."""
    if not payload.itens:
        raise ErroOSAvulsa("OSSemItens", 400)
    if any(item.valor_unitario_snapshot <= Decimal("0") for item in payload.itens):
        # AC-OS-015-2: tabela ausente -> caller deve mapear; aqui detectamos
        # valor_unitario_snapshot = 0 como sinal de ausencia.
        raise ErroOSAvulsa(
            "PrecoTabelaAusente",
            422,
            detalhe="valor_unitario_snapshot zero detectado em ao menos 1 item",
        )

    if (
        any(item.requer_recebimento for item in payload.itens)
        and payload.equipamento_recebimento_id is None
    ):
        raise ErroOSAvulsa("EquipamentoSemRecebimentoRegistrado", 412)

    numero_os = repository.proximo_numero_os()
    os_id = uuid4()
    valor_total = sum(
        (item.valor_unitario_snapshot for item in payload.itens), start=Decimal("0")
    )

    os_snapshot = OSSnapshot(
        id=os_id,
        tenant_id=payload.tenant_id,
        numero_os=numero_os,
        cliente_id=payload.cliente_id,
        cliente_referencia_hash=payload.cliente_referencia_hash,
        cliente_key_id=payload.cliente_key_id,
        equipamento_id=payload.equipamento_id,
        equipamento_recebimento_id=payload.equipamento_recebimento_id,
        orcamento_origem_id=None,  # avulsa
        os_origem_id=None,
        sucessao_societaria_id=None,
        estado=EstadoOS.RASCUNHO,
        tipo_predominante="",
        nao_conformidade_global=False,
        valor_total=valor_total,
        valor_total_atualizado=valor_total,
        analise_critica_id=payload.analise_critica_inline_id,
        analise_critica_snapshot_hash=payload.analise_critica_snapshot_hash,
        regra_decisao_acordada=payload.regra_decisao_acordada,
        criada_em=payload.criada_em,
        atualizada_em=payload.criada_em,
        criada_por_user_id=payload.criada_por_user_id,
    )
    repository.salvar_os(os_snapshot)

    planejadas: list[UUID] = []
    for item in payload.itens:
        ativ_id = uuid4()
        ativ = AtividadeSnapshot(
            id=ativ_id,
            tenant_id=payload.tenant_id,
            os_id=os_id,
            tipo=item.tipo,
            sequencia=item.sequencia,
            estado=EstadoAtividade.PENDENTE,
            tecnico_executor_id=None,
            agendada_para=None,
            iniciada_em=None,
            concluida_em=None,
            valor_unitario_snapshot=item.valor_unitario_snapshot,
            link_modulo_tecnico_id=None,
            geo_lat=None,
            geo_long=None,
            geo_municipio_hash="",
            equipamento_id_desnormalizado=None,
            tipo_bloqueia_concorrencia=False,
        )
        repository.salvar_atividade(ativ)
        planejadas.append(ativ_id)

    ev_payload: dict[str, object] = {
        "numero_os": numero_os,
        "balcao": True,
        "atividades": [str(aid) for aid in planejadas],
    }
    ev_canonico = json.dumps(ev_payload, sort_keys=True, ensure_ascii=False)
    ev_hash = hashlib.sha256(ev_canonico.encode("utf-8")).hexdigest()  # audit-pii-salt: skip -- payload sanitizado
    repository.publicar_evento(
        EventoDeOSSnapshot(
            id=uuid4(),
            tenant_id=payload.tenant_id,
            os_id=os_id,
            atividade_id=None,
            tipo=TipoEventoDeOS.OS_ABERTA,
            payload_hash=ev_hash,
            payload_data=ev_payload,
            correlation_id=payload.correlation_id,
            actor_user_id=payload.criada_por_user_id,
            occurred_at=payload.criada_em,
            criado_em=payload.criada_em,
        )
    )

    return CriarOSAvulsaResultado(
        os_id=os_id,
        numero_os=numero_os,
        atividades_planejadas=tuple(planejadas),
        correlation_id=payload.correlation_id,
    )
