"""Use cases `marcar_nao_conformidade` + `resolver_nc` — T-OS-064/065 (Fase 5).

Cobre AC-OS-005-1, 2, 3, 4, 5 do PRD.

AC-OS-005-1: tipo=calibracao em EM_EXECUCAO + razao (>=30 chars, anti-PII via
MotivoCancelamento VO INV-OS-TXT-001) -> atividade NAO_CONFORME + bloqueia
emissao certificado (campo `nao_conformidade_global` da OS).

AC-OS-005-3 + AC-OS-005-5 (P-OS-R5 cl. 8.7 CAPA completo): resolverNC exige
TODOS de: causa_raiz_hash, acao_corretiva_descricao_hash, eficacia_verificada_em,
eficacia_verificada_por_user_id; ausente -> 412 CAPAIncompleto.
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
    NaoConformidadeAtividadeSnapshot,
    OSSnapshot,
)
from src.domain.operacao.os.repository import OSRepository
from src.domain.operacao.os.value_objects import (
    EstadoAtividade,
    MotivoCancelamento,
    TipoAtividade,
    TipoEventoDeOS,
)

# Tipos que aceitam marcacao de NC (AC-OS-005-1 menciona calibracao; estendido
# pra os tipos regulados a partir do PRD §6.1). Vistoria/instalacao seguem
# regra de NC operacional em US-OS-008 (cancelamento), nao aqui.
_TIPOS_ACEITAM_NC: frozenset[TipoAtividade] = frozenset(
    {TipoAtividade.CALIBRACAO, TipoAtividade.VERIFICACAO_INMETRO}
)


@dataclass(frozen=True, slots=True)
class MarcarNCInput:
    atividade_id: UUID
    usuario_id: UUID
    razao: MotivoCancelamento
    correlation_id: UUID
    marcada_em: datetime


@dataclass(frozen=True, slots=True)
class MarcarNCResultado:
    nc_id: UUID
    atividade_id: UUID
    correlation_id: UUID


class ErroMarcarNC(Exception):
    def __init__(self, codigo: str, http_status: int, detalhe: str = "") -> None:
        super().__init__(f"{codigo}: {detalhe}" if detalhe else codigo)
        self.codigo = codigo
        self.http_status = http_status
        self.detalhe = detalhe


def marcar_nao_conformidade(
    *,
    payload: MarcarNCInput,
    repository: OSRepository,
) -> MarcarNCResultado:
    """Transiciona atividade EM_EXECUCAO -> NAO_CONFORME + cria NaoConformidadeAtividade."""
    atividade = repository.get_atividade_by_id(payload.atividade_id)
    if atividade is None:
        raise ErroMarcarNC("AtividadeNaoEncontrada", 404)

    if atividade.tipo not in _TIPOS_ACEITAM_NC:
        raise ErroMarcarNC(
            "TipoNaoAceitaNC",
            422,
            detalhe=f"tipo={atividade.tipo.value}; NC formal apenas em calibracao/verif INMETRO",
        )

    if atividade.estado != EstadoAtividade.EM_EXECUCAO:
        raise ErroMarcarNC(
            "AtividadeEmEstadoIncompativel",
            412,
            detalhe=f"estado={atividade.estado.value}; marcar NC so em EM_EXECUCAO",
        )

    if atividade.tecnico_executor_id != payload.usuario_id:
        # INV-OS-ATIV-005 — executor designado eh unico autorizado.
        raise ErroMarcarNC("NaoEExecutor", 403)

    razao_hash = hashlib.sha256(
        payload.razao.texto.encode("utf-8")  # ja anti-PII via VO
    ).hexdigest()  # audit-pii-salt: skip -- VO MotivoCancelamento ja bloqueia PII; hash eh integrity-check

    # Atividade -> NAO_CONFORME.
    atividade_nc = AtividadeSnapshot(
        id=atividade.id,
        tenant_id=atividade.tenant_id,
        os_id=atividade.os_id,
        tipo=atividade.tipo,
        sequencia=atividade.sequencia,
        estado=EstadoAtividade.NAO_CONFORME,
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
    repository.salvar_atividade(atividade_nc)

    # Cria NaoConformidadeAtividade (CAPA aberto — todos os campos NULL).
    nc_id = uuid4()
    nc_snapshot = NaoConformidadeAtividadeSnapshot(
        id=nc_id,
        tenant_id=atividade.tenant_id,
        atividade_id=atividade.id,
        razao_nao_conformidade_hash=razao_hash,
        marcada_em=payload.marcada_em,
        marcada_por_user_id=payload.usuario_id,
        registro_capa_id=None,
        causa_raiz_hash="",
        acao_corretiva_descricao_hash="",
        eficacia_verificada_em=None,
        eficacia_verificada_por_user_id=None,
        revogado_em=None,
        criado_em=payload.marcada_em,
    )
    repository.salvar_nc(nc_snapshot)

    # AC-OS-005-2: OS ganha nao_conformidade_global=True.
    os_snapshot = repository.get_os_by_id(atividade.os_id)
    if os_snapshot is not None and not os_snapshot.nao_conformidade_global:
        os_marcada = OSSnapshot(
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
            nao_conformidade_global=True,
            valor_total=os_snapshot.valor_total,
            valor_total_atualizado=os_snapshot.valor_total_atualizado,
            analise_critica_id=os_snapshot.analise_critica_id,
            analise_critica_snapshot_hash=os_snapshot.analise_critica_snapshot_hash,
            regra_decisao_acordada=os_snapshot.regra_decisao_acordada,
            criada_em=os_snapshot.criada_em,
            atualizada_em=payload.marcada_em,
            criada_por_user_id=os_snapshot.criada_por_user_id,
        )
        repository.salvar_os(os_marcada)

    # EventoDeOS — atividade_nao_conforme.
    ev_payload: dict[str, object] = {
        "atividade_id": str(atividade.id),
        "nc_id": str(nc_id),
        "razao_hash": razao_hash,
    }
    ev_canonico = json.dumps(ev_payload, sort_keys=True, ensure_ascii=False)
    ev_hash = hashlib.sha256(ev_canonico.encode("utf-8")).hexdigest()  # audit-pii-salt: skip -- payload sanitizado sem PII
    repository.publicar_evento(
        EventoDeOSSnapshot(
            id=uuid4(),
            tenant_id=atividade.tenant_id,
            os_id=atividade.os_id,
            atividade_id=atividade.id,
            tipo=TipoEventoDeOS.ATIVIDADE_NAO_CONFORME,
            payload_hash=ev_hash,
            payload_data=ev_payload,
            correlation_id=payload.correlation_id,
            actor_user_id=payload.usuario_id,
            occurred_at=payload.marcada_em,
            criado_em=payload.marcada_em,
        )
    )

    return MarcarNCResultado(
        nc_id=nc_id,
        atividade_id=atividade.id,
        correlation_id=payload.correlation_id,
    )


# =============================================================
# resolver_nc — ciclo CAPA P-OS-R5 cl. 8.7
# =============================================================


@dataclass(frozen=True, slots=True)
class ResolverNCInput:
    atividade_id: UUID
    usuario_id: UUID  # eficacia_verificada_por_user_id
    causa_raiz: MotivoCancelamento  # >=30 chars anti-PII
    acao_corretiva: MotivoCancelamento  # >=30 chars anti-PII
    correlation_id: UUID
    eficacia_verificada_em: datetime


@dataclass(frozen=True, slots=True)
class ResolverNCResultado:
    nc_id: UUID
    atividade_id: UUID
    correlation_id: UUID


class ErroResolverNC(Exception):
    def __init__(self, codigo: str, http_status: int, detalhe: str = "") -> None:
        super().__init__(f"{codigo}: {detalhe}" if detalhe else codigo)
        self.codigo = codigo
        self.http_status = http_status
        self.detalhe = detalhe


def resolver_nc(
    *,
    payload: ResolverNCInput,
    repository: OSRepository,
) -> ResolverNCResultado:
    """Resolve NC (ciclo CAPA completo) — atividade NAO_CONFORME -> EM_EXECUCAO."""
    nc = repository.get_nc_ativa_por_atividade(payload.atividade_id)
    if nc is None:
        raise ErroResolverNC("NCNaoEncontrada", 404)

    atividade = repository.get_atividade_by_id(payload.atividade_id)
    if atividade is None:
        raise ErroResolverNC("AtividadeNaoEncontrada", 404)
    if atividade.estado != EstadoAtividade.NAO_CONFORME:
        raise ErroResolverNC(
            "AtividadeEmEstadoIncompativel",
            412,
            detalhe=f"estado={atividade.estado.value}; resolverNC so em NAO_CONFORME",
        )

    # CAPA completo (P-OS-R5 + AC-OS-005-5).
    causa_raiz_hash = hashlib.sha256(
        payload.causa_raiz.texto.encode("utf-8")
    ).hexdigest()  # audit-pii-salt: skip -- VO bloqueia PII; integrity hash
    acao_corretiva_hash = hashlib.sha256(
        payload.acao_corretiva.texto.encode("utf-8")
    ).hexdigest()  # audit-pii-salt: skip -- VO bloqueia PII; integrity hash

    nc_resolvida = NaoConformidadeAtividadeSnapshot(
        id=nc.id,
        tenant_id=nc.tenant_id,
        atividade_id=nc.atividade_id,
        razao_nao_conformidade_hash=nc.razao_nao_conformidade_hash,
        marcada_em=nc.marcada_em,
        marcada_por_user_id=nc.marcada_por_user_id,
        registro_capa_id=nc.registro_capa_id,
        causa_raiz_hash=causa_raiz_hash,
        acao_corretiva_descricao_hash=acao_corretiva_hash,
        eficacia_verificada_em=payload.eficacia_verificada_em,
        eficacia_verificada_por_user_id=payload.usuario_id,
        revogado_em=nc.revogado_em,
        criado_em=nc.criado_em,
    )
    if not nc_resolvida.capa_completo:
        raise ErroResolverNC(
            "CAPAIncompleto",
            412,
            detalhe="exige causa_raiz_hash + acao_corretiva_descricao_hash + eficacia_verificada_em + eficacia_verificada_por_user_id",
        )
    repository.salvar_nc(nc_resolvida)

    # Atividade volta EM_EXECUCAO.
    atividade_voltou = AtividadeSnapshot(
        id=atividade.id,
        tenant_id=atividade.tenant_id,
        os_id=atividade.os_id,
        tipo=atividade.tipo,
        sequencia=atividade.sequencia,
        estado=EstadoAtividade.EM_EXECUCAO,
        tecnico_executor_id=atividade.tecnico_executor_id,
        agendada_para=atividade.agendada_para,
        iniciada_em=atividade.iniciada_em,
        concluida_em=None,
        valor_unitario_snapshot=atividade.valor_unitario_snapshot,
        link_modulo_tecnico_id=atividade.link_modulo_tecnico_id,
        geo_lat=atividade.geo_lat,
        geo_long=atividade.geo_long,
        geo_municipio_hash=atividade.geo_municipio_hash,
        equipamento_id_desnormalizado=atividade.equipamento_id_desnormalizado,
        tipo_bloqueia_concorrencia=atividade.tipo_bloqueia_concorrencia,
    )
    repository.salvar_atividade(atividade_voltou)

    # EventoDeOS — atividade_nc_resolvida.
    ev_payload: dict[str, object] = {
        "atividade_id": str(atividade.id),
        "nc_id": str(nc.id),
        "causa_raiz_hash": causa_raiz_hash,
        "acao_corretiva_hash": acao_corretiva_hash,
    }
    ev_canonico = json.dumps(ev_payload, sort_keys=True, ensure_ascii=False)
    ev_hash = hashlib.sha256(ev_canonico.encode("utf-8")).hexdigest()  # audit-pii-salt: skip -- payload sanitizado
    repository.publicar_evento(
        EventoDeOSSnapshot(
            id=uuid4(),
            tenant_id=atividade.tenant_id,
            os_id=atividade.os_id,
            atividade_id=atividade.id,
            tipo=TipoEventoDeOS.ATIVIDADE_NC_RESOLVIDA,
            payload_hash=ev_hash,
            payload_data=ev_payload,
            correlation_id=payload.correlation_id,
            actor_user_id=payload.usuario_id,
            occurred_at=payload.eficacia_verificada_em,
            criado_em=payload.eficacia_verificada_em,
        )
    )

    return ResolverNCResultado(
        nc_id=nc.id,
        atividade_id=atividade.id,
        correlation_id=payload.correlation_id,
    )
