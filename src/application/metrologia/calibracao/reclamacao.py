"""Use cases ReclamacaoCalibracao — US-CAL-018 (P4 Fase 5 Batch J — T-CAL-096..098).

ISO 17025 cl. 7.9 + CDC art. 26 — reclamacao formal do cliente sobre
cert emitido. Cliente tem 90 dias apos emissao (vicio aparente) ou apos
ciencia (vicio oculto). Use case `abrir` checa janela CDC ANTES de aceitar.

3 use cases:
  abrir            -> RECEBIDA
  atribuir_rt      RECEBIDA -> EM_ANALISE (RT independente — AC-CAL-018-2)
  responder        EM_ANALISE -> RESPONDIDA (decisao 3 valores)

ACs cobertos:
- AC-CAL-018-1: cert >=90 dias bloqueia (CDC art. 26). Relato >=100 chars
  + hash. Cria em RECEBIDA + publica Calibracao.ReclamacaoAberta
  (caller publica em transacao envolvente).
- AC-CAL-018-2: RT atribuido preferencialmente != revisor_id E !=
  conferente_id da Calibracao original. Use case CHECA segregacao;
  caller fornece rt_atribuido_user_id_hash + flag verificada.
- AC-CAL-018-3: prazo_resposta_dia_util default 15. Alerta P1 quando
  excedido — implementado em job separado (sem use case dedicado).
- AC-CAL-018-4: decisao=PROCEDENTE_RECALL dispara Marco 5 saga recall
  (ADR-0045) — caller publica evento Calibracao.ReclamacaoRespondida.

Sem CAS por revision (ReclamacaoCalibracao nao tem campo revision; usa
guard de estado via transitar_estado).

Permissao caller: AuthorizationProvider.can('reclamacao.<acao>', resource={...}).
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timedelta
from uuid import UUID, uuid4

from src.domain.metrologia.calibracao.entities import ReclamacaoCalibracaoSnapshot
from src.domain.metrologia.calibracao.enums import (
    DecisaoReclamacao,
    EstadoReclamacao,
)
from src.domain.metrologia.calibracao.repository import (
    ReclamacaoCalibracaoRepository,
)

_MIN_CHARS_RELATO = 100
_MIN_CHARS_RESPOSTA = 100
_JANELA_CDC_DIAS = 90  # CDC art. 26


# ===================== Excecoes =====================


class ReclamacaoNaoEncontrada(Exception):
    """ID nao existe no tenant ativo — caller retorna 404."""


class EstadoInvalidoParaTransicaoReclamacao(Exception):
    """Estado atual != esperado — caller retorna 409."""


class ConflitoEstadoReclamacao(Exception):
    """UPDATE atomico perdeu race. Caller decide 409 + reload."""

    def __init__(self, snapshot_atual: ReclamacaoCalibracaoSnapshot) -> None:
        self.snapshot_atual = snapshot_atual
        super().__init__(
            f"ConflitoEstado reclamacao_id={snapshot_atual.id} "
            f"estado_atual={snapshot_atual.estado.value}"
        )


class JanelaCDCExpirada(Exception):
    """Cert emitido ha mais de 90 dias — CDC art. 26 expirou.

    Caller retorna 410 Gone / 412 PrecondicaoFalhou conforme contrato.
    """


class RTNaoIndependenteDaCalibracaoOriginal(Exception):
    """AC-CAL-018-2: RT atribuido coincide com revisor/conferente original.

    Caller retorna 412 RTNaoIndependente.
    """


# ===================== US-CAL-018 abrir =====================


@dataclass(frozen=True, slots=True)
class AbrirReclamacaoInput:
    """Payload de abertura (RECEBIDA)."""

    tenant_id: UUID
    calibracao_id: UUID
    certificado_id: UUID  # FK Certificado (M5)
    cliente_referencia_hash: str  # HashVersionado cliente_id
    relato_canonicalizado: str  # >=100 chars + anti-PII
    relato_hash: str
    aberta_em: datetime  # tz-aware
    certificado_emitido_em: datetime  # tz-aware — pra checar janela CDC
    prazo_resposta_dia_util: int  # default 15 (AC-CAL-018-3)
    correlation_id: UUID

    def __post_init__(self) -> None:
        if len(self.relato_canonicalizado) < _MIN_CHARS_RELATO:
            raise ValueError(
                f"abrir_reclamacao: relato_canonicalizado precisa "
                f">= {_MIN_CHARS_RELATO} chars (AC-CAL-018-1 + anti-PII); "
                f"achou {len(self.relato_canonicalizado)}"
            )
        if not self.relato_hash:
            raise ValueError(
                "abrir_reclamacao: relato_hash obrigatorio (ADR-0064)"
            )
        if not self.cliente_referencia_hash:
            raise ValueError(
                "abrir_reclamacao: cliente_referencia_hash obrigatorio "
                "(ADR-0032 + ADR-0064)"
            )
        if self.aberta_em.tzinfo is None:
            raise ValueError(
                "abrir_reclamacao: aberta_em exige datetime tz-aware (INV-VIG-004)"
            )
        if self.certificado_emitido_em.tzinfo is None:
            raise ValueError(
                "abrir_reclamacao: certificado_emitido_em exige tz-aware"
            )
        if self.prazo_resposta_dia_util < 1:
            raise ValueError(
                f"abrir_reclamacao: prazo_resposta_dia_util deve ser >= 1 "
                f"(achou {self.prazo_resposta_dia_util})"
            )


@dataclass(frozen=True, slots=True)
class AbrirReclamacaoOutput:
    snapshot: ReclamacaoCalibracaoSnapshot


def abrir(
    inp: AbrirReclamacaoInput, repo: ReclamacaoCalibracaoRepository
) -> AbrirReclamacaoOutput:
    """Abre ReclamacaoCalibracao em RECEBIDA. Checa janela CDC art. 26 (90d)."""
    # AC-CAL-018-1 + CDC art. 26: janela 90 dias apos emissao
    janela = timedelta(days=_JANELA_CDC_DIAS)
    if inp.aberta_em - inp.certificado_emitido_em > janela:
        raise JanelaCDCExpirada(
            f"certificado emitido em {inp.certificado_emitido_em.isoformat()}; "
            f"reclamacao aberta em {inp.aberta_em.isoformat()}; janela CDC "
            f"art. 26 = {_JANELA_CDC_DIAS} dias expirou"
        )

    snapshot = ReclamacaoCalibracaoSnapshot(
        id=uuid4(),
        tenant_id=inp.tenant_id,
        calibracao_id=inp.calibracao_id,
        certificado_id=inp.certificado_id,
        cliente_referencia_hash=inp.cliente_referencia_hash,
        relato_canonicalizado=inp.relato_canonicalizado,
        relato_hash=inp.relato_hash,
        estado=EstadoReclamacao.RECEBIDA,
        rt_atribuido_user_id_hash="",
        resposta_canonicalizada="",
        resposta_hash="",
        decisao=None,
        aberta_em=inp.aberta_em,
        prazo_resposta_dia_util=inp.prazo_resposta_dia_util,
        respondida_em=None,
        correlation_id=inp.correlation_id,
    )
    repo.salvar_nova(snapshot)
    return AbrirReclamacaoOutput(snapshot=snapshot)


# ===================== US-CAL-018 atribuir_rt (independente) =====================


@dataclass(frozen=True, slots=True)
class AtribuirRTInput:
    """Payload de atribuicao de RT independente (RECEBIDA -> EM_ANALISE).

    AC-CAL-018-2: RT preferencialmente independente. Caller passa
    `rt_atribuido_user_id` + hashes do revisor/conferente da calibracao
    original. Use case BLOQUEIA se RT == revisor OU RT == conferente
    (regra dura — preferencia vira obrigacao quando ha >=2 RTs disponiveis).

    Para fluxo "unico RT habilitado" (lab pequeno), caller passa
    `permitir_mesmo_rt_excecao=True` documentando a excecao em
    EventoDeCalibracao (analogo ao ADR-0026 da 2a conferencia).
    """

    reclamacao_id: UUID
    rt_atribuido_user_id_hash: str  # HashVersionado do RT
    revisor_original_id_hash: str  # HashVersionado revisor da cal
    conferente_original_id_hash: str  # HashVersionado conferente da cal
    permitir_mesmo_rt_excecao: bool  # documenta excecao quando True

    def __post_init__(self) -> None:
        if not self.rt_atribuido_user_id_hash:
            raise ValueError(
                "atribuir_rt: rt_atribuido_user_id_hash obrigatorio"
            )
        if not self.revisor_original_id_hash or not self.conferente_original_id_hash:
            raise ValueError(
                "atribuir_rt: revisor/conferente original hashes obrigatorios "
                "(AC-CAL-018-2)"
            )


@dataclass(frozen=True, slots=True)
class AtribuirRTOutput:
    snapshot: ReclamacaoCalibracaoSnapshot


def atribuir_rt(
    inp: AtribuirRTInput, repo: ReclamacaoCalibracaoRepository
) -> AtribuirRTOutput:
    """RECEBIDA -> EM_ANALISE. Valida RT independente (AC-CAL-018-2)."""
    atual = repo.obter_por_id(inp.reclamacao_id)
    if atual is None:
        raise ReclamacaoNaoEncontrada(str(inp.reclamacao_id))
    if atual.estado != EstadoReclamacao.RECEBIDA:
        raise EstadoInvalidoParaTransicaoReclamacao(
            f"estado atual={atual.estado.value}; atribuir_rt exige RECEBIDA"
        )

    # AC-CAL-018-2: independencia
    coincide_revisor = (
        inp.rt_atribuido_user_id_hash == inp.revisor_original_id_hash
    )
    coincide_conferente = (
        inp.rt_atribuido_user_id_hash == inp.conferente_original_id_hash
    )
    if (coincide_revisor or coincide_conferente) and not inp.permitir_mesmo_rt_excecao:
        raise RTNaoIndependenteDaCalibracaoOriginal(
            "rt_atribuido_user_id_hash coincide com revisor ou conferente "
            "original (AC-CAL-018-2). Use permitir_mesmo_rt_excecao=True para "
            "casos de unico RT habilitado (excecao documentada)."
        )

    novo = replace(
        atual,
        estado=EstadoReclamacao.EM_ANALISE,
        rt_atribuido_user_id_hash=inp.rt_atribuido_user_id_hash,
    )
    ok = repo.transitar_estado(novo, EstadoReclamacao.RECEBIDA)
    if not ok:
        atualizado = repo.obter_por_id(inp.reclamacao_id)
        raise ConflitoEstadoReclamacao(atualizado or atual)

    return AtribuirRTOutput(snapshot=novo)


# ===================== US-CAL-018 responder =====================


@dataclass(frozen=True, slots=True)
class ResponderReclamacaoInput:
    """Payload de resposta (EM_ANALISE -> RESPONDIDA)."""

    reclamacao_id: UUID
    resposta_canonicalizada: str  # >=100 chars + anti-PII
    resposta_hash: str
    decisao: DecisaoReclamacao
    respondida_em: datetime  # tz-aware

    def __post_init__(self) -> None:
        if len(self.resposta_canonicalizada) < _MIN_CHARS_RESPOSTA:
            raise ValueError(
                f"responder: resposta_canonicalizada precisa "
                f">= {_MIN_CHARS_RESPOSTA} chars (anti-PII + INV-DOC-CANON-001); "
                f"achou {len(self.resposta_canonicalizada)}"
            )
        if not self.resposta_hash:
            raise ValueError("responder: resposta_hash obrigatorio (ADR-0064)")
        if self.respondida_em.tzinfo is None:
            raise ValueError(
                "responder: respondida_em exige tz-aware (INV-VIG-004)"
            )


@dataclass(frozen=True, slots=True)
class ResponderReclamacaoOutput:
    snapshot: ReclamacaoCalibracaoSnapshot
    dispara_recall_m5: bool  # AC-CAL-018-4 — caller publica evento


def responder(
    inp: ResponderReclamacaoInput, repo: ReclamacaoCalibracaoRepository
) -> ResponderReclamacaoOutput:
    """EM_ANALISE -> RESPONDIDA. AC-CAL-018-4: PROCEDENTE_RECALL aciona saga M5."""
    atual = repo.obter_por_id(inp.reclamacao_id)
    if atual is None:
        raise ReclamacaoNaoEncontrada(str(inp.reclamacao_id))
    if atual.estado != EstadoReclamacao.EM_ANALISE:
        raise EstadoInvalidoParaTransicaoReclamacao(
            f"estado atual={atual.estado.value}; responder exige EM_ANALISE"
        )

    novo = replace(
        atual,
        estado=EstadoReclamacao.RESPONDIDA,
        resposta_canonicalizada=inp.resposta_canonicalizada,
        resposta_hash=inp.resposta_hash,
        decisao=inp.decisao,
        respondida_em=inp.respondida_em,
    )
    ok = repo.transitar_estado(novo, EstadoReclamacao.EM_ANALISE)
    if not ok:
        atualizado = repo.obter_por_id(inp.reclamacao_id)
        raise ConflitoEstadoReclamacao(atualizado or atual)

    return ResponderReclamacaoOutput(
        snapshot=novo,
        dispara_recall_m5=inp.decisao.dispara_recall_m5,
    )
