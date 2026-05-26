"""Use cases NC ciclo CAPA — US-CAL-013/014 (P4 Fase 5 Batch H — T-CAL-091..095).

Ciclo CAPA cl. 7.10 + cl. 8.7 ISO 17025 (6 estados + REABERTA volta a CONTIDA).

Estado-maquina §4.2:
  abrir            -> CONTIDA
  definir_acao     -> ACAO_CORRETIVA_DEFINIDA
  executar_acao    -> ACAO_EXECUTADA      (INV-CAL-NC-002/003)
  verificar_eficacia -> EFICACIA_VERIFICADA
  fechar           -> FECHADA
  reabrir          -> REABERTA (que efetivamente eh CONTIDA — cl. 8.7.2)

Invariantes cravadas:
- INV-CAL-NC-002: decisao_continuar_ou_parar != A_DEFINIR antes de
  ACAO_EXECUTADA (cl. 7.10.1).
- INV-CAL-NC-003: PARAR_TRABALHO exige cliente_notificado_em NOT NULL
  + cliente_notificado_via cravado.
- INV-DOC-CANON-001: descricao + causa_raiz canonicalizadas + hash.
- P-CAL-A2 (advogado): responsavel_acao_user_id_hash sempre presente;
  responsavel_acao_user_id eh "zona quente" UUID ≤90d.

Sem CAS por revision — NaoConformidade nao tem campo revision; usa
guard de estado (UPDATE ... WHERE estado = esperado). Race -> rowcount=0
-> ConflitoEstado.

Permissao caller: AuthorizationProvider.can('nc.<acao>', resource={...})
ANTES de invocar. Use case nao re-chama provider.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime
from uuid import UUID, uuid4

from src.domain.metrologia.calibracao.entities import NaoConformidadeSnapshot
from src.domain.metrologia.calibracao.enums import (
    AcaoCorretivaTipo,
    ClienteNotificadoVia,
    DecisaoContinuarOuParar,
    EstadoNaoConformidade,
)
from src.domain.metrologia.calibracao.repository import NaoConformidadeRepository

_MIN_CHARS_DESCRICAO = 30
_MIN_CHARS_CAUSA_RAIZ = 30


# ===================== Excecoes =====================


class NaoConformidadeNaoEncontrada(Exception):
    """ID nao existe no tenant ativo (RLS filtrou) — caller retorna 404."""


class EstadoInvalidoParaTransicao(Exception):
    """NC nao esta no estado esperado — caller retorna 409 Conflict."""


class ConflitoEstadoNaoConformidade(Exception):
    """UPDATE atomico perdeu race (estado mudou concorrentemente).

    Caller decide 409 + reload. Carrega snapshot atual.
    """

    def __init__(self, snapshot_atual: NaoConformidadeSnapshot) -> None:
        self.snapshot_atual = snapshot_atual
        super().__init__(
            f"ConflitoEstado nc_id={snapshot_atual.id} "
            f"estado_atual={snapshot_atual.estado.value}"
        )


# ===================== US-CAL-013/014 — abrir_nao_conformidade =====================


@dataclass(frozen=True, slots=True)
class AbrirNCInput:
    """Payload de abertura de NC (cl. 7.10).

    Origem XOR: exatamente UMA de {calibracao_id, origem_proficiencia_id}
    deve ser NOT NULL. CHECK PG migration 0002 reforca.
    """

    tenant_id: UUID
    calibracao_id: UUID | None
    origem_proficiencia_id: UUID | None
    descricao_canonicalizada: str  # >=30 chars + anti-PII + NFC
    descricao_hash: str  # HashVersionado v<NN>$<base64>
    responsavel_acao_user_id: UUID  # zona quente ≤90d
    responsavel_acao_user_id_hash: str  # HashVersionado sempre presente
    correlation_id: UUID

    def __post_init__(self) -> None:
        # XOR origem (ADR-0032 + cl. 7.10)
        tem_cal = self.calibracao_id is not None
        tem_prof = self.origem_proficiencia_id is not None
        if tem_cal == tem_prof:
            raise ValueError(
                "abrir_nao_conformidade: origem XOR — exatamente UMA de "
                "{calibracao_id, origem_proficiencia_id} deve ser NOT NULL"
            )
        if len(self.descricao_canonicalizada) < _MIN_CHARS_DESCRICAO:
            raise ValueError(
                f"abrir_nao_conformidade: descricao_canonicalizada precisa "
                f">= {_MIN_CHARS_DESCRICAO} chars (INV-DOC-CANON-001 + "
                f"anti-PII); achou {len(self.descricao_canonicalizada)}"
            )
        if not self.descricao_hash:
            raise ValueError(
                "abrir_nao_conformidade: descricao_hash obrigatorio (ADR-0064)"
            )
        if not self.responsavel_acao_user_id_hash:
            raise ValueError(
                "abrir_nao_conformidade: responsavel_acao_user_id_hash "
                "obrigatorio (P-CAL-A2 — sempre presente)"
            )


@dataclass(frozen=True, slots=True)
class AbrirNCOutput:
    snapshot: NaoConformidadeSnapshot


def abrir(inp: AbrirNCInput, repo: NaoConformidadeRepository) -> AbrirNCOutput:
    """Abre NC em estado CONTIDA."""
    snapshot = NaoConformidadeSnapshot(
        id=uuid4(),
        tenant_id=inp.tenant_id,
        calibracao_id=inp.calibracao_id,
        origem_proficiencia_id=inp.origem_proficiencia_id,
        descricao_canonicalizada=inp.descricao_canonicalizada,
        descricao_hash=inp.descricao_hash,
        estado=EstadoNaoConformidade.CONTIDA,
        causa_raiz_canonicalizada="",
        causa_raiz_hash="",
        acao_corretiva_descricao_hash="",
        acao_corretiva_tipo=None,
        acao_executada_em=None,
        eficacia_verificada_em=None,
        eficacia_verificada_por_user_id=None,
        responsavel_acao_user_id=inp.responsavel_acao_user_id,
        responsavel_acao_user_id_hash=inp.responsavel_acao_user_id_hash,
        decisao_continuar_ou_parar=DecisaoContinuarOuParar.A_DEFINIR,
        cliente_notificado_em=None,
        cliente_notificado_via=None,
        cliente_notificado_documento_id=None,
        autorizacao_retomada_user_id=None,
        autorizacao_retomada_em=None,
        correlation_id=inp.correlation_id,
    )
    repo.salvar_novo(snapshot)
    return AbrirNCOutput(snapshot=snapshot)


# ===================== definir_acao_corretiva =====================


@dataclass(frozen=True, slots=True)
class DefinirAcaoCorretivaInput:
    nc_id: UUID
    causa_raiz_canonicalizada: str  # >=30 chars
    causa_raiz_hash: str
    acao_corretiva_descricao_hash: str
    acao_corretiva_tipo: AcaoCorretivaTipo

    def __post_init__(self) -> None:
        if len(self.causa_raiz_canonicalizada) < _MIN_CHARS_CAUSA_RAIZ:
            raise ValueError(
                f"definir_acao_corretiva: causa_raiz_canonicalizada precisa "
                f">= {_MIN_CHARS_CAUSA_RAIZ} chars; achou "
                f"{len(self.causa_raiz_canonicalizada)}"
            )
        if not self.causa_raiz_hash:
            raise ValueError(
                "definir_acao_corretiva: causa_raiz_hash obrigatorio"
            )
        if not self.acao_corretiva_descricao_hash:
            raise ValueError(
                "definir_acao_corretiva: acao_corretiva_descricao_hash obrigatorio"
            )


@dataclass(frozen=True, slots=True)
class DefinirAcaoCorretivaOutput:
    snapshot: NaoConformidadeSnapshot


def definir_acao_corretiva(
    inp: DefinirAcaoCorretivaInput,
    repo: NaoConformidadeRepository,
) -> DefinirAcaoCorretivaOutput:
    """CONTIDA -> ACAO_CORRETIVA_DEFINIDA."""
    atual = repo.obter_por_id(inp.nc_id)
    if atual is None:
        raise NaoConformidadeNaoEncontrada(str(inp.nc_id))
    if atual.estado != EstadoNaoConformidade.CONTIDA:
        raise EstadoInvalidoParaTransicao(
            f"estado atual={atual.estado.value}; definir_acao_corretiva exige "
            f"CONTIDA"
        )

    novo = replace(
        atual,
        estado=EstadoNaoConformidade.ACAO_CORRETIVA_DEFINIDA,
        causa_raiz_canonicalizada=inp.causa_raiz_canonicalizada,
        causa_raiz_hash=inp.causa_raiz_hash,
        acao_corretiva_descricao_hash=inp.acao_corretiva_descricao_hash,
        acao_corretiva_tipo=inp.acao_corretiva_tipo,
    )
    ok = repo.transitar_estado(novo, EstadoNaoConformidade.CONTIDA)
    if not ok:
        atualizado = repo.obter_por_id(inp.nc_id)
        raise ConflitoEstadoNaoConformidade(atualizado or atual)

    return DefinirAcaoCorretivaOutput(snapshot=novo)


# ===================== executar_acao (INV-CAL-NC-002/003) =====================


@dataclass(frozen=True, slots=True)
class ExecutarAcaoInput:
    nc_id: UUID
    decisao_continuar_ou_parar: DecisaoContinuarOuParar  # != A_DEFINIR
    acao_executada_em: datetime  # tz-aware
    # INV-CAL-NC-003 (so quando PARAR_TRABALHO):
    cliente_notificado_em: datetime | None  # tz-aware
    cliente_notificado_via: ClienteNotificadoVia | None
    cliente_notificado_documento_id: UUID | None

    def __post_init__(self) -> None:
        # INV-CAL-NC-002: nao pode ser A_DEFINIR
        if self.decisao_continuar_ou_parar == DecisaoContinuarOuParar.A_DEFINIR:
            raise ValueError(
                "executar_acao: decisao_continuar_ou_parar nao pode ser A_DEFINIR "
                "(INV-CAL-NC-002 + cl. 7.10.1)"
            )
        if self.acao_executada_em.tzinfo is None:
            raise ValueError(
                "executar_acao: acao_executada_em exige datetime tz-aware "
                "(INV-VIG-004)"
            )
        # INV-CAL-NC-003: PARAR_TRABALHO exige notificacao completa
        if self.decisao_continuar_ou_parar == DecisaoContinuarOuParar.PARAR_TRABALHO:
            if self.cliente_notificado_em is None:
                raise ValueError(
                    "executar_acao: PARAR_TRABALHO exige cliente_notificado_em "
                    "NOT NULL (INV-CAL-NC-003 + cl. 7.10.2)"
                )
            if self.cliente_notificado_em.tzinfo is None:
                raise ValueError(
                    "executar_acao: cliente_notificado_em exige tz-aware"
                )
            if self.cliente_notificado_via is None:
                raise ValueError(
                    "executar_acao: PARAR_TRABALHO exige cliente_notificado_via "
                    "(INV-CAL-NC-003)"
                )


@dataclass(frozen=True, slots=True)
class ExecutarAcaoOutput:
    snapshot: NaoConformidadeSnapshot


def executar_acao(
    inp: ExecutarAcaoInput,
    repo: NaoConformidadeRepository,
) -> ExecutarAcaoOutput:
    """ACAO_CORRETIVA_DEFINIDA -> ACAO_EXECUTADA."""
    atual = repo.obter_por_id(inp.nc_id)
    if atual is None:
        raise NaoConformidadeNaoEncontrada(str(inp.nc_id))
    if atual.estado != EstadoNaoConformidade.ACAO_CORRETIVA_DEFINIDA:
        raise EstadoInvalidoParaTransicao(
            f"estado atual={atual.estado.value}; executar_acao exige "
            f"ACAO_CORRETIVA_DEFINIDA"
        )

    novo = replace(
        atual,
        estado=EstadoNaoConformidade.ACAO_EXECUTADA,
        decisao_continuar_ou_parar=inp.decisao_continuar_ou_parar,
        acao_executada_em=inp.acao_executada_em,
        cliente_notificado_em=inp.cliente_notificado_em,
        cliente_notificado_via=inp.cliente_notificado_via,
        cliente_notificado_documento_id=inp.cliente_notificado_documento_id,
    )
    ok = repo.transitar_estado(novo, EstadoNaoConformidade.ACAO_CORRETIVA_DEFINIDA)
    if not ok:
        atualizado = repo.obter_por_id(inp.nc_id)
        raise ConflitoEstadoNaoConformidade(atualizado or atual)

    return ExecutarAcaoOutput(snapshot=novo)


# ===================== verificar_eficacia =====================


@dataclass(frozen=True, slots=True)
class VerificarEficaciaInput:
    nc_id: UUID
    eficacia_verificada_em: datetime  # tz-aware
    eficacia_verificada_por_user_id: UUID

    def __post_init__(self) -> None:
        if self.eficacia_verificada_em.tzinfo is None:
            raise ValueError(
                "verificar_eficacia: eficacia_verificada_em exige tz-aware"
            )


@dataclass(frozen=True, slots=True)
class VerificarEficaciaOutput:
    snapshot: NaoConformidadeSnapshot


def verificar_eficacia(
    inp: VerificarEficaciaInput,
    repo: NaoConformidadeRepository,
) -> VerificarEficaciaOutput:
    """ACAO_EXECUTADA -> EFICACIA_VERIFICADA."""
    atual = repo.obter_por_id(inp.nc_id)
    if atual is None:
        raise NaoConformidadeNaoEncontrada(str(inp.nc_id))
    if atual.estado != EstadoNaoConformidade.ACAO_EXECUTADA:
        raise EstadoInvalidoParaTransicao(
            f"estado atual={atual.estado.value}; verificar_eficacia exige "
            f"ACAO_EXECUTADA"
        )

    novo = replace(
        atual,
        estado=EstadoNaoConformidade.EFICACIA_VERIFICADA,
        eficacia_verificada_em=inp.eficacia_verificada_em,
        eficacia_verificada_por_user_id=inp.eficacia_verificada_por_user_id,
    )
    ok = repo.transitar_estado(novo, EstadoNaoConformidade.ACAO_EXECUTADA)
    if not ok:
        atualizado = repo.obter_por_id(inp.nc_id)
        raise ConflitoEstadoNaoConformidade(atualizado or atual)

    return VerificarEficaciaOutput(snapshot=novo)


# ===================== fechar =====================


@dataclass(frozen=True, slots=True)
class FecharNCInput:
    nc_id: UUID


@dataclass(frozen=True, slots=True)
class FecharNCOutput:
    snapshot: NaoConformidadeSnapshot


def fechar(inp: FecharNCInput, repo: NaoConformidadeRepository) -> FecharNCOutput:
    """EFICACIA_VERIFICADA -> FECHADA (terminal)."""
    atual = repo.obter_por_id(inp.nc_id)
    if atual is None:
        raise NaoConformidadeNaoEncontrada(str(inp.nc_id))
    if atual.estado != EstadoNaoConformidade.EFICACIA_VERIFICADA:
        raise EstadoInvalidoParaTransicao(
            f"estado atual={atual.estado.value}; fechar exige EFICACIA_VERIFICADA"
        )

    novo = replace(atual, estado=EstadoNaoConformidade.FECHADA)
    ok = repo.transitar_estado(novo, EstadoNaoConformidade.EFICACIA_VERIFICADA)
    if not ok:
        atualizado = repo.obter_por_id(inp.nc_id)
        raise ConflitoEstadoNaoConformidade(atualizado or atual)

    return FecharNCOutput(snapshot=novo)


# ===================== reabrir (cl. 8.7.2 — volta a CONTIDA) =====================


@dataclass(frozen=True, slots=True)
class ReabrirNCInput:
    nc_id: UUID
    motivo_reabertura_canonicalizado: str  # >=30 chars

    def __post_init__(self) -> None:
        if len(self.motivo_reabertura_canonicalizado) < _MIN_CHARS_DESCRICAO:
            raise ValueError(
                f"reabrir: motivo_reabertura_canonicalizado precisa "
                f">= {_MIN_CHARS_DESCRICAO} chars (anti-PII + INV-DOC-CANON-001)"
            )


@dataclass(frozen=True, slots=True)
class ReabrirNCOutput:
    snapshot: NaoConformidadeSnapshot
    motivo: str  # echo (caller persiste EventoDeCalibracao tipo=nc_reaberta)


def reabrir(
    inp: ReabrirNCInput, repo: NaoConformidadeRepository
) -> ReabrirNCOutput:
    """FECHADA -> CONTIDA (cl. 8.7.2 — reabertura volta a CONTIDA).

    Limpa campos pos-CONTIDA (causa_raiz, acao_*, eficacia_*) para que
    o ciclo CAPA recomece do zero. Mantemos os hashes de auditoria
    pos-fechamento via EventoDeCalibracao (caller persiste).
    """
    atual = repo.obter_por_id(inp.nc_id)
    if atual is None:
        raise NaoConformidadeNaoEncontrada(str(inp.nc_id))
    if atual.estado != EstadoNaoConformidade.FECHADA:
        raise EstadoInvalidoParaTransicao(
            f"estado atual={atual.estado.value}; reabrir exige FECHADA"
        )

    # Volta para CONTIDA (cl. 8.7.2) com campos do ciclo anterior limpos.
    # Auditoria do ciclo antigo fica em EventoDeCalibracao tipo=nc_fechada
    # (caller persiste em transacao envolvente).
    novo = replace(
        atual,
        estado=EstadoNaoConformidade.CONTIDA,
        causa_raiz_canonicalizada="",
        causa_raiz_hash="",
        acao_corretiva_descricao_hash="",
        acao_corretiva_tipo=None,
        acao_executada_em=None,
        eficacia_verificada_em=None,
        eficacia_verificada_por_user_id=None,
        decisao_continuar_ou_parar=DecisaoContinuarOuParar.A_DEFINIR,
        cliente_notificado_em=None,
        cliente_notificado_via=None,
        cliente_notificado_documento_id=None,
        autorizacao_retomada_user_id=None,
        autorizacao_retomada_em=None,
    )
    ok = repo.transitar_estado(novo, EstadoNaoConformidade.FECHADA)
    if not ok:
        atualizado = repo.obter_por_id(inp.nc_id)
        raise ConflitoEstadoNaoConformidade(atualizado or atual)

    return ReabrirNCOutput(
        snapshot=novo, motivo=inp.motivo_reabertura_canonicalizado
    )
