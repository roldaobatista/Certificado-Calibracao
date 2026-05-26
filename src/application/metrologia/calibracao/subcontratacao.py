"""Use cases subcontratacao ISO 17025 cl. 6.6 — US-CAL-017
(P4 Fase 5 Batch I — T-CAL-093/094).

2 transicoes principais:
  subcontratar_calibracao    CONFIGURADA -> AGUARDANDO_SUBCONTRATADO
  registrar_recebimento_*    AGUARDANDO_SUBCONTRATADO -> RECEBIDA_DO_SUBCONTRATADO

ACs cobertos:
- AC-CAL-017-1: motivo_canonicalizado >=30 chars + hash + subcontratado_id +
  aceite_subcontratacao_id obrigatorios.
- AC-CAL-017-2: status -> AGUARDANDO_SUBCONTRATADO + evento
  Calibracao.SubcontratadaParaLab (caller publica em transacao envolvente).
- AC-CAL-017-3: certificado_subcontratado_snapshot_json cravado imutavel
  na recepcao.
- AC-CAL-017-7 (P-CAL-A1 + Lei 14.063 art. 4o): se assinatura_modo=TOUCH,
  exige declaracao_aceite_touch_alto_risco_id NOT NULL.
- AC-CAL-017-8 (P-CAL-A1 + LGPD art. 33): se eh_pais_estrangeiro=True,
  exige dpa_clausulas_internacionais_id NOT NULL.
- INV-CAL-FRAUDE-RECEB-001: recebedor_user_id cravado em
  registrar_recebimento_subcontratado (caller assegura == request.user.id).

Validacoes feitas pelo CALLER (fora deste use case):
- INV-CAL-SUBC-001: consentimento cliente (caller passa aceite_id de
  AceiteSubcontratacao ja persistido — caller validou hash+IP+timestamp).
- INV-CAL-SUBC-002: acreditacao vigente do subcontratado (caller consulta
  LaboratorioSubcontratado.acreditacoes_vigentes na data).
- INV-CAL-SUBC-005: cliente nao em inadimplencia dura (caller checa).

Permissao caller: AuthorizationProvider.can('calibracao.subcontratar' /
'calibracao.registrar_recebimento_subcontratado', resource={tenant_id,
calibracao_id}).
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from uuid import UUID

from src.application.metrologia.calibracao.configurar_calibracao import (
    CalibracaoNaoEncontrada,
    ConflitoVersaoCalibracao,
)
from src.domain.metrologia.calibracao.entities import CalibracaoSnapshot
from src.domain.metrologia.calibracao.enums import EstadoCalibracao
from src.domain.metrologia.calibracao.repository import CalibracaoRepository

_MIN_CHARS_MOTIVO_SUBC = 30


class EstadoInvalidoParaSubcontratar(Exception):
    """Calibracao nao esta em CONFIGURADA — caller retorna 409."""


class EstadoInvalidoParaRegistrarRecebimento(Exception):
    """Calibracao nao esta em AGUARDANDO_SUBCONTRATADO — caller retorna 409."""


class TransferenciaInternacionalSemBaseLGPD(Exception):
    """AC-CAL-017-8 + LGPD art. 33 — caller retorna 412
    SubcontratadoForaBR_TransferenciaInternacionalSemBase."""


class AssinaturaTouchAltoRiscoSemDeclaracao(Exception):
    """AC-CAL-017-7 + Lei 14.063 art. 4o — caller retorna 412
    TouchAltoRiscoSemDeclaracao."""


# =====================================================================
# subcontratar_calibracao (T-CAL-093)
# =====================================================================


@dataclass(frozen=True, slots=True)
class SubcontratarCalibracaoInput:
    """Payload de subcontratacao (CONFIGURADA -> AGUARDANDO_SUBCONTRATADO)."""

    calibracao_id: UUID
    revision_esperada: int
    subcontratado_id: UUID  # FK LaboratorioSubcontratado (caller validou vigencia)
    aceite_subcontratacao_id: UUID  # FK AceiteSubcontratacao (caller persistiu)
    motivo_canonicalizado: str  # >=30 chars + anti-PII + NFC
    motivo_hash: str  # HashVersionado v<NN>$<base64>
    # AC-CAL-017-8: transferencia internacional (LGPD art. 33)
    eh_pais_estrangeiro: bool
    dpa_clausulas_internacionais_id: UUID | None
    # AC-CAL-017-7: assinatura TOUCH em vez de A3 (Lei 14.063 art. 4o)
    assinatura_modo: str  # "A3" (default) ou "TOUCH"
    declaracao_aceite_touch_alto_risco_id: UUID | None

    def __post_init__(self) -> None:
        if len(self.motivo_canonicalizado) < _MIN_CHARS_MOTIVO_SUBC:
            raise ValueError(
                f"subcontratar_calibracao: motivo_canonicalizado precisa "
                f">= {_MIN_CHARS_MOTIVO_SUBC} chars (AC-CAL-017-1 + anti-PII); "
                f"achou {len(self.motivo_canonicalizado)}"
            )
        if not self.motivo_hash:
            raise ValueError(
                "subcontratar_calibracao: motivo_hash obrigatorio (ADR-0064)"
            )
        if self.assinatura_modo not in {"A3", "TOUCH"}:
            raise ValueError(
                f"subcontratar_calibracao: assinatura_modo deve ser 'A3' ou "
                f"'TOUCH' (achou '{self.assinatura_modo}')"
            )
        # AC-CAL-017-7: TOUCH exige declaracao adicional
        if (
            self.assinatura_modo == "TOUCH"
            and self.declaracao_aceite_touch_alto_risco_id is None
        ):
            raise ValueError(
                "subcontratar_calibracao: assinatura_modo=TOUCH exige "
                "declaracao_aceite_touch_alto_risco_id NOT NULL "
                "(AC-CAL-017-7 + Lei 14.063 art. 4o)"
            )


@dataclass(frozen=True, slots=True)
class SubcontratarCalibracaoOutput:
    snapshot: CalibracaoSnapshot


def subcontratar_calibracao(
    inp: SubcontratarCalibracaoInput,
    repo: CalibracaoRepository,
) -> SubcontratarCalibracaoOutput:
    """CONFIGURADA -> AGUARDANDO_SUBCONTRATADO via CAS."""
    atual = repo.obter_por_id(inp.calibracao_id)
    if atual is None:
        raise CalibracaoNaoEncontrada(str(inp.calibracao_id))

    # Apenas CONFIGURADA aceita transicao pra subcontratado (ver
    # EstadoCalibracao.aceita_subcontratacao)
    if not atual.status.aceita_subcontratacao:
        raise EstadoInvalidoParaSubcontratar(
            f"status atual={atual.status.value}; subcontratar_calibracao exige "
            f"CONFIGURADA (INV-CAL-WORM-001)"
        )

    # AC-CAL-017-8 + LGPD art. 33 (transferencia internacional)
    if inp.eh_pais_estrangeiro and inp.dpa_clausulas_internacionais_id is None:
        raise TransferenciaInternacionalSemBaseLGPD(
            "subcontratado em pais estrangeiro exige dpa_clausulas_internacionais_id "
            "NOT NULL (AC-CAL-017-8 + LGPD art. 33). Caller retorna 412 "
            "SubcontratadoForaBR_TransferenciaInternacionalSemBase."
        )

    # Defesa em profundidade: validador __post_init__ ja cobre, mas a
    # excecao especifica facilita o caller traduzir pra 412.
    if (
        inp.assinatura_modo == "TOUCH"
        and inp.declaracao_aceite_touch_alto_risco_id is None
    ):
        raise AssinaturaTouchAltoRiscoSemDeclaracao(
            "assinatura_modo=TOUCH exige declaracao_aceite_touch_alto_risco_id "
            "(AC-CAL-017-7 + Lei 14.063 art. 4o)"
        )

    novo = replace(
        atual,
        status=EstadoCalibracao.AGUARDANDO_SUBCONTRATADO,
        revision=atual.revision + 1,
        subcontratado_id=inp.subcontratado_id,
        aceite_subcontratacao_id=inp.aceite_subcontratacao_id,
    )

    ok = repo.atualizar_com_lock(novo, inp.revision_esperada)
    if not ok:
        atualizado = repo.obter_por_id(inp.calibracao_id)
        snapshot_para_excecao = atualizado if atualizado is not None else atual
        raise ConflitoVersaoCalibracao(snapshot_para_excecao)

    return SubcontratarCalibracaoOutput(snapshot=novo)


# =====================================================================
# registrar_recebimento_subcontratado (T-CAL-094)
# =====================================================================


@dataclass(frozen=True, slots=True)
class RegistrarRecebimentoSubcontratadoInput:
    """Payload AGUARDANDO_SUBCONTRATADO -> RECEBIDA_DO_SUBCONTRATADO."""

    calibracao_id: UUID
    revision_esperada: int
    recebedor_user_id: UUID  # INV-CAL-FRAUDE-RECEB-001 (caller checou == user)
    # Snapshot imutavel do cert externo (AC-CAL-017-3 + INV-CAL-SUBC-003).
    # Caller monta a partir do PDF anexo + num cert externo + escopo declarado.
    # Deve incluir pelo menos: numero_cert_externo, data_servico, grandeza,
    # faixa_min, faixa_max, escopo_subcontratado, rt_subcontratado.
    certificado_subcontratado_snapshot_json: dict[str, object]

    def __post_init__(self) -> None:
        if not self.certificado_subcontratado_snapshot_json:
            raise ValueError(
                "registrar_recebimento_subcontratado: "
                "certificado_subcontratado_snapshot_json obrigatorio "
                "(AC-CAL-017-3 + INV-CAL-SUBC-003)"
            )
        chaves_obrigatorias = {
            "numero_cert_externo",
            "data_servico",
            "grandeza",
            "faixa_min",
            "faixa_max",
            "escopo_subcontratado",
            "rt_subcontratado",
        }
        if not chaves_obrigatorias.issubset(
            self.certificado_subcontratado_snapshot_json.keys()
        ):
            faltando = sorted(
                chaves_obrigatorias
                - set(self.certificado_subcontratado_snapshot_json.keys())
            )
            raise ValueError(
                f"registrar_recebimento_subcontratado: certificado snapshot "
                f"sem chaves obrigatorias {faltando} (AC-CAL-017-3)"
            )


@dataclass(frozen=True, slots=True)
class RegistrarRecebimentoSubcontratadoOutput:
    snapshot: CalibracaoSnapshot


def registrar_recebimento_subcontratado(
    inp: RegistrarRecebimentoSubcontratadoInput,
    repo: CalibracaoRepository,
) -> RegistrarRecebimentoSubcontratadoOutput:
    """AGUARDANDO_SUBCONTRATADO -> RECEBIDA_DO_SUBCONTRATADO via CAS."""
    atual = repo.obter_por_id(inp.calibracao_id)
    if atual is None:
        raise CalibracaoNaoEncontrada(str(inp.calibracao_id))

    if atual.status != EstadoCalibracao.AGUARDANDO_SUBCONTRATADO:
        raise EstadoInvalidoParaRegistrarRecebimento(
            f"status atual={atual.status.value}; registrar_recebimento_subcontratado "
            f"exige AGUARDANDO_SUBCONTRATADO (INV-CAL-WORM-001)"
        )

    # Defensivo: se subcontratado_id eh None, fluxo esta corrompido
    # (deveriamos ter passado por subcontratar_calibracao antes).
    if atual.subcontratado_id is None:
        raise EstadoInvalidoParaRegistrarRecebimento(
            "registrar_recebimento_subcontratado: calibracao sem subcontratado_id "
            "(fluxo subcontratacao nao iniciado — INV-CAL-SUBC-001)"
        )

    novo = replace(
        atual,
        status=EstadoCalibracao.RECEBIDA_DO_SUBCONTRATADO,
        revision=atual.revision + 1,
        certificado_subcontratado_snapshot_json=dict(
            inp.certificado_subcontratado_snapshot_json
        ),
        recebedor_user_id=inp.recebedor_user_id,
    )

    ok = repo.atualizar_com_lock(novo, inp.revision_esperada)
    if not ok:
        atualizado = repo.obter_por_id(inp.calibracao_id)
        snapshot_para_excecao = atualizado if atualizado is not None else atual
        raise ConflitoVersaoCalibracao(snapshot_para_excecao)

    return RegistrarRecebimentoSubcontratadoOutput(snapshot=novo)
