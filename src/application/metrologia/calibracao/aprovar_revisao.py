"""Use case `aprovar_revisao` — US-CAL-007 (P4 Fase 5 Batch F — T-CAL-088).

Transicao EM_REVISAO_1 -> AGUARDANDO_2A_CONFERENCIA. Cl. 7.8 ISO 17025.

ACs cobertos:
- AC-CAL-007-3 (ADR-0026): se revisor=executor, exige `excecao_motivo`
  da whitelist EXCECOES_2A_CONFERENCIA. Predicate
  `pode_aprovar_revisao_2a_conferencia` invocado AQUI (action=revisao).
- AC-CAL-007-5 (P-CAL-R10 + cl. 6.2 + INV-CAL-RT-002 + INV-CAL-FRAUDE-REV-001):
  captura `snapshot_competencia_revisor_json` IMUTAVEL (grandeza, faixa,
  vigencia da RTCompetencia do revisor NA DATA da aprovacao).
- ADR-0063 Opcao A lazy: caller invoca predicate `rt_competencia_cobre`
  ANTES de chamar este use case. Use case nao re-chama (fora do escopo
  de transacao — predicate consulta RT competencia que vive em modulo
  separado).

Concorrencia (ADR-0065): CAS via atualizar_com_lock; race -> ConflitoVersao.

Permissao caller: AuthorizationProvider.can('calibracao.aprovar_revisao',
resource={tenant_id, calibracao_id, executor_id, revisor_id, excecao_motivo}).

Invariantes:
- INV-CAL-FRAUDE-REV-001: revisor != executor (excecao ADR-0026 4 condicoes).
- INV-CAL-RT-002: snapshot_competencia_revisor_json NOT NULL pos-transicao.
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


class EstadoInvalidoParaAprovarRevisao(Exception):
    """Calibracao nao esta em EM_REVISAO_1 — caller retorna 409 Conflict."""


class FraudeRevisorEhExecutor(Exception):
    """INV-CAL-FRAUDE-REV-001: revisor == executor sem excecao ADR-0026.

    Caller retorna 422 RTSemSegregacao com codigo
    `fraude_revisor_eh_executor`.
    """


class ExcecaoAdr0026Invalida(Exception):
    """`excecao_motivo` fora da whitelist EXCECOES_2A_CONFERENCIA."""


@dataclass(frozen=True, slots=True)
class AprovarRevisaoInput:
    """Payload de aprovacao de revisao (US-CAL-007)."""

    calibracao_id: UUID
    revision_esperada: int
    revisor_id: UUID  # RT logado que esta aprovando (cl. 6.2)
    # Snapshot imutavel da competencia do revisor NA DATA (AC-CAL-007-5)
    # Caller monta este JSON a partir de RTCompetencia (M2 + ADR-0022).
    # Deve conter pelo menos: grandeza, faixa_min, faixa_max, vigencia_inicio,
    # vigencia_fim, rt_competencia_id (UUID da carta competencia).
    snapshot_competencia_revisor_json: dict[str, object]
    # ADR-0026: se revisor == executor, motivo obrigatorio (whitelist).
    excecao_motivo: str | None = None

    def __post_init__(self) -> None:
        if not self.snapshot_competencia_revisor_json:
            raise ValueError(
                "aprovar_revisao: snapshot_competencia_revisor_json obrigatorio "
                "(AC-CAL-007-5 + INV-CAL-RT-002)"
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
            self.snapshot_competencia_revisor_json.keys()
        ):
            faltando = sorted(
                chaves_obrigatorias - set(self.snapshot_competencia_revisor_json.keys())
            )
            raise ValueError(
                f"aprovar_revisao: snapshot_competencia_revisor_json sem chaves "
                f"obrigatorias {faltando} (AC-CAL-007-5)"
            )


@dataclass(frozen=True, slots=True)
class AprovarRevisaoOutput:
    snapshot: CalibracaoSnapshot


def executar(
    inp: AprovarRevisaoInput,
    repo: CalibracaoRepository,
) -> AprovarRevisaoOutput:
    """Aprova revisao: EM_REVISAO_1 -> AGUARDANDO_2A_CONFERENCIA via CAS."""
    # Import local pra nao acoplar dominio com infrastructure no top-level
    from src.infrastructure.calibracao.predicates_calibracao import (
        EXCECOES_2A_CONFERENCIA,
        pode_aprovar_revisao_2a_conferencia,
    )

    atual = repo.obter_por_id(inp.calibracao_id)
    if atual is None:
        raise CalibracaoNaoEncontrada(str(inp.calibracao_id))

    if atual.status != EstadoCalibracao.EM_REVISAO_1:
        raise EstadoInvalidoParaAprovarRevisao(
            f"status atual={atual.status.value}; aprovar_revisao exige "
            f"EM_REVISAO_1 (INV-CAL-WORM-001)"
        )

    if atual.executor_id is None:
        # Configuracao errada do fluxo: deveriamos ter executor_id setado
        # quando iniciar_leituras US-CAL-004 rodou. Sem isso, segregacao
        # cl. 6.2.5 nao eh verificavel — bloqueia.
        raise EstadoInvalidoParaAprovarRevisao(
            "aprovar_revisao: calibracao sem executor_id (INV-CAL-FRAUDE-EXEC-001 "
            "exige executor cravado em iniciar_leituras)"
        )

    # ADR-0026 — valida excecao se fornecida
    if inp.excecao_motivo is not None and inp.excecao_motivo not in EXCECOES_2A_CONFERENCIA:
        raise ExcecaoAdr0026Invalida(
            f"excecao_motivo={inp.excecao_motivo} fora da whitelist "
            f"{sorted(EXCECOES_2A_CONFERENCIA)} (ADR-0026)"
        )

    # Segregacao funcoes cl. 6.2.5 + INV-CAL-FRAUDE-REV-001
    permitido, motivo = pode_aprovar_revisao_2a_conferencia(
        {
            "action": "revisao",
            "executor_id": atual.executor_id,
            "revisor_id": inp.revisor_id,
            "excecao_motivo": inp.excecao_motivo,
        }
    )
    if not permitido:
        raise FraudeRevisorEhExecutor(
            f"predicate pode_aprovar_revisao_2a_conferencia = {motivo}"
        )

    novo = replace(
        atual,
        status=EstadoCalibracao.AGUARDANDO_2A_CONFERENCIA,
        revision=atual.revision + 1,
        revisor_id=inp.revisor_id,
        snapshot_competencia_revisor_json=dict(inp.snapshot_competencia_revisor_json),
    )

    ok = repo.atualizar_com_lock(novo, inp.revision_esperada)
    if not ok:
        atualizado = repo.obter_por_id(inp.calibracao_id)
        snapshot_para_excecao = atualizado if atualizado is not None else atual
        raise ConflitoVersaoCalibracao(snapshot_para_excecao)

    return AprovarRevisaoOutput(snapshot=novo)
