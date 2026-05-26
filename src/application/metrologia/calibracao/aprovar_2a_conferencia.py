"""Use case `aprovar_2a_conferencia` — US-CAL-008 (P4 Fase 5 Batch F — T-CAL-090).

Transicao AGUARDANDO_2A_CONFERENCIA -> APROVADA. Cl. 6.2.5 ISO 17025 +
ADR-0026 (excecao 4 condicoes objetivas + limite 5%/mes).

APROVADA eh estado TERMINAL (INV-CAL-WORM-001): trigger PG bloqueia
UPDATE pos-aprovacao (migration 0002). Caller envolve a transacao em
transaction.atomic — UPDATE + INSERT EventoDeCalibracao + INSERT
Excecao2aConferencia (se aplicavel) precisam ser atomicos.

ACs cobertos:
- AC-CAL-008-2: APROVADA libera emissao certificado (caller decide).
- AC-CAL-008-3: registra excecao via Excecao2aConferencia quando
  conferente == revisor; ADR-0026 4 condicoes validadas pelo caller.
- AC-CAL-008-4 (P-CAL-R10 + cl. 6.2.5 + INV-CAL-RT-002):
  captura snapshot_competencia_conferente_json IMUTAVEL + valida
  conferente_id != revisor_id (ou ADR-0026 4 condicoes objetivas).
- INV-CAL-FRAUDE-CONF-001: conferente != revisor E conferente != executor
  (excecao via ADR-0026).
- ADR-0063 Opcao A lazy: predicate `rt_competencia_cobre` invocado pelo
  caller ANTES deste use case (resultado fora do escopo de transacao).

Concorrencia (ADR-0065): CAS via atualizar_com_lock; race -> ConflitoVersao.

Excecao ADR-0026: `excecao_2a_conf_id` UUID quando a 4-condicoes-excecao
foi registrada externamente; predicate aceita o motivo da whitelist
(EXCECOES_2A_CONFERENCIA) — caller assegurou que limite 5%/mes nao foi
ultrapassado antes de chamar este use case (AC-CAL-008-5).
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from uuid import UUID

from src.application.metrologia.calibracao.aprovar_revisao import (
    ExcecaoAdr0026Invalida,
)
from src.application.metrologia.calibracao.configurar_calibracao import (
    CalibracaoNaoEncontrada,
    ConflitoVersaoCalibracao,
)
from src.domain.metrologia.calibracao.entities import CalibracaoSnapshot
from src.domain.metrologia.calibracao.enums import EstadoCalibracao
from src.domain.metrologia.calibracao.repository import CalibracaoRepository


class EstadoInvalidoParaAprovar2aConferencia(Exception):
    """Calibracao nao esta em AGUARDANDO_2A_CONFERENCIA — caller retorna 409."""


class FraudeConferenteEhRevisorOuExecutor(Exception):
    """INV-CAL-FRAUDE-CONF-001 — conferente == revisor OU conferente == executor
    sem excecao ADR-0026. Caller retorna 422 RTSemSegregacao."""


class Excecao2aConferenciaSemRegistro(Exception):
    """Quando conferente == revisor com excecao_motivo, exige
    excecao_2a_conf_id FK p/ entidade Excecao2aConferencia (ADR-0026 +
    AC-CAL-008-3 + AC-CAL-008-5 limite 5%/mes)."""


@dataclass(frozen=True, slots=True)
class Aprovar2aConferenciaInput:
    """Payload da 2a conferencia (US-CAL-008)."""

    calibracao_id: UUID
    revision_esperada: int
    conferente_id: UUID  # RT logado que esta aprovando a 2a conferencia
    # Snapshot imutavel da competencia (AC-CAL-008-4)
    snapshot_competencia_conferente_json: dict[str, object]
    # ADR-0026: se conferente == revisor (ou == executor), exige motivo+FK
    excecao_motivo: str | None = None
    excecao_2a_conf_id: UUID | None = None

    def __post_init__(self) -> None:
        if not self.snapshot_competencia_conferente_json:
            raise ValueError(
                "aprovar_2a_conferencia: snapshot_competencia_conferente_json "
                "obrigatorio (AC-CAL-008-4 + INV-CAL-RT-002)"
            )
        chaves_obrigatorias = {
            "grandeza",
            "faixa_min",
            "faixa_max",
            "vigencia_inicio",
            "vigencia_fim",
            "rt_competencia_id",
        }
        if not chaves_obrigatorias.issubset(
            self.snapshot_competencia_conferente_json.keys()
        ):
            faltando = sorted(
                chaves_obrigatorias
                - set(self.snapshot_competencia_conferente_json.keys())
            )
            raise ValueError(
                f"aprovar_2a_conferencia: snapshot_competencia_conferente_json "
                f"sem chaves obrigatorias {faltando} (AC-CAL-008-4)"
            )
        # excecao_motivo sem FK = configuracao incompleta
        if self.excecao_motivo is not None and self.excecao_2a_conf_id is None:
            raise ValueError(
                "aprovar_2a_conferencia: excecao_motivo sem excecao_2a_conf_id; "
                "ADR-0026 exige registro formal de Excecao2aConferencia"
            )
        # FK sem motivo = configuracao incompleta inversa
        if self.excecao_2a_conf_id is not None and self.excecao_motivo is None:
            raise ValueError(
                "aprovar_2a_conferencia: excecao_2a_conf_id sem excecao_motivo "
                "(ADR-0026 codigo obrigatorio na whitelist)"
            )


@dataclass(frozen=True, slots=True)
class Aprovar2aConferenciaOutput:
    snapshot: CalibracaoSnapshot


def executar(
    inp: Aprovar2aConferenciaInput,
    repo: CalibracaoRepository,
) -> Aprovar2aConferenciaOutput:
    """Aprova 2a conferencia: AGUARDANDO_2A_CONFERENCIA -> APROVADA via CAS."""
    from src.infrastructure.calibracao.predicates_calibracao import (
        EXCECOES_2A_CONFERENCIA,
        pode_aprovar_revisao_2a_conferencia,
    )

    atual = repo.obter_por_id(inp.calibracao_id)
    if atual is None:
        raise CalibracaoNaoEncontrada(str(inp.calibracao_id))

    if atual.status != EstadoCalibracao.AGUARDANDO_2A_CONFERENCIA:
        raise EstadoInvalidoParaAprovar2aConferencia(
            f"status atual={atual.status.value}; aprovar_2a_conferencia exige "
            f"AGUARDANDO_2A_CONFERENCIA (INV-CAL-WORM-001)"
        )

    if atual.executor_id is None or atual.revisor_id is None:
        # Fluxo incompleto: executor+revisor deviam estar cravados das fases
        # anteriores (iniciar_leituras US-CAL-004 + aprovar_revisao US-CAL-007).
        raise EstadoInvalidoParaAprovar2aConferencia(
            "aprovar_2a_conferencia: calibracao sem executor_id+revisor_id; "
            "INV-CAL-FRAUDE-CONF-001 exige ambos cravados antes da 2a conferencia"
        )

    # ADR-0026: valida excecao (se fornecida)
    if inp.excecao_motivo is not None:
        if inp.excecao_motivo not in EXCECOES_2A_CONFERENCIA:
            raise ExcecaoAdr0026Invalida(
                f"excecao_motivo={inp.excecao_motivo} fora da whitelist "
                f"{sorted(EXCECOES_2A_CONFERENCIA)} (ADR-0026)"
            )

    # Segregacao funcoes cl. 6.2.5 + INV-CAL-FRAUDE-CONF-001
    permitido, motivo = pode_aprovar_revisao_2a_conferencia(
        {
            "action": "2a_conferencia",
            "executor_id": atual.executor_id,
            "revisor_id": atual.revisor_id,
            "conferente_id": inp.conferente_id,
            "excecao_motivo": inp.excecao_motivo,
        }
    )
    if not permitido:
        raise FraudeConferenteEhRevisorOuExecutor(
            f"predicate pode_aprovar_revisao_2a_conferencia = {motivo}"
        )

    # Guardrail final: se conferente == revisor OU conferente == executor,
    # excecao_2a_conf_id eh OBRIGATORIA (predicate ja permitiu via excecao
    # mas precisamos do FK pra rastrear no limite 5%/mes — AC-CAL-008-5).
    conferente_colide = (
        inp.conferente_id == atual.revisor_id
        or inp.conferente_id == atual.executor_id
    )
    if conferente_colide and inp.excecao_2a_conf_id is None:
        raise Excecao2aConferenciaSemRegistro(
            "conferente_id colide com revisor/executor: "
            "ADR-0026 exige excecao_2a_conf_id (FK Excecao2aConferencia) "
            "alem do excecao_motivo (AC-CAL-008-3 + AC-CAL-008-5 5%/mes)"
        )

    novo = replace(
        atual,
        status=EstadoCalibracao.APROVADA,
        revision=atual.revision + 1,
        conferente_id=inp.conferente_id,
        snapshot_competencia_conferente_json=dict(
            inp.snapshot_competencia_conferente_json
        ),
        excecao_2a_conf_id=inp.excecao_2a_conf_id,
    )

    ok = repo.atualizar_com_lock(novo, inp.revision_esperada)
    if not ok:
        atualizado = repo.obter_por_id(inp.calibracao_id)
        snapshot_para_excecao = atualizado if atualizado is not None else atual
        raise ConflitoVersaoCalibracao(snapshot_para_excecao)

    return Aprovar2aConferenciaOutput(snapshot=novo)
