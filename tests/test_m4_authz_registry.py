"""Contrato authz M4 calibracao APOS consolidacao da porta REST (ADR-0073 Opcao A).

ATUALIZADO 2026-06 (consolidacao da porta REST do Marco 4 + review tech-lead):
os 3 predicates ABAC que ANTES eram bound aqui (cmc_cobre,
procedimento_vigente_para, pode_aprovar_revisao_2a_conferencia) foram
DESVINCULADOS do authz (`CalibracaoConfig.ready()` nao registra mais nada).

Por que mudou (ADR-0073 — "validacao metrologica no USE CASE, nao no permission
layer DRF"):
- `cmc_cobre`/`procedimento_vigente_para`: cobertura metrologica migrou pros use
  cases via portas `escopos_cmc.cobre`/`procedimentos.cobre_procedimento`
  (GATE-CAL-CMC-PREDICATE + GATE-CAL-PROC-VIGENTE-PREDICATE FECHADOS). O binding
  exigia resource {grandeza,faixa,...} que o ViewSet nao alimenta — retornava
  `cmc_resource_invalido` => 403 espurio, FECHANDO a porta REST de configurar.
- `pode_aprovar_revisao_2a_conferencia`: segregacao cl. 6.2.5 exige `executor_id`
  da Calibracao PERSISTIDA (ADR-0073 §2 manda no use case). Os use cases
  `aprovar_revisao`/`aprovar_2a_conferencia` JA invocam o predicate com o
  `executor_id` real => 422 FraudeRevisorEhExecutor/FraudeConferente. O binding
  no authz MASCARAVA esse 422 com um 403 (resource invalido).

Estes testes agora TRAVAM o contrato novo (predicates NAO bound) e pegam
RE-BINDING acidental — alerta explicito do tech-lead. O comportamento das
FUNCOES dos predicates (puras) segue coberto em test_m4_predicates_calibracao.py;
o enforcement ponta-a-ponta no use case em test_m7_wire_in_configurar_p3.py +
test_m4_uc_aprovar_revisao.py.
"""

from __future__ import annotations

from src.infrastructure.authz.predicates import get_predicates, predicates_aplicaveis

# Sem pytest.mark.django_db — registry eh estrutura in-memory populada por
# AppConfig.ready() no import do Django settings; nao depende de DB.

_PREDICATES_DESVINCULADOS_ADR0073 = {
    "cmc_cobre",
    "procedimento_vigente_para",
    "pode_aprovar_revisao_2a_conferencia",
}


def test_predicates_metrologicos_nao_bound_no_authz() -> None:
    """ADR-0073 Opcao A: nenhum dos 3 predicates M4 fica registrado no authz.

    Validacao de cobertura/competencia/segregacao vive nos use cases com estado
    server-side. Se algum reaparecer aqui = regressao de re-binding (reabre o
    403-espurio + mascara o 422 de dominio).
    """
    registry = get_predicates()
    presentes = _PREDICATES_DESVINCULADOS_ADR0073 & set(registry)
    assert presentes == set(), (
        f"Predicates M4 RE-BOUND no authz (viola ADR-0073 Opcao A): {presentes}. "
        "Cobertura metrologica + segregacao cl. 6.2.5 sao enforcadas nos use "
        "cases (configurar_calibracao / aprovar_revisao / aprovar_2a_conferencia), "
        "nao no permission layer. Conferir src/infrastructure/calibracao/apps.py."
    )


def test_acoes_m4_nao_tem_predicate_aplicavel() -> None:
    """As acoes antes gated por predicate agora sao RBAC puro (sem ABAC)."""
    for acao in (
        "calibracao.configurar",
        "calibracao.iniciar_leituras",
        "calibracao.aprovar_revisao",
        "calibracao.aprovar_2a_conferencia",
    ):
        aplicaveis = predicates_aplicaveis(acao)
        nomes_m4 = {p.nome for p in aplicaveis} & _PREDICATES_DESVINCULADOS_ADR0073
        assert nomes_m4 == set(), (
            f"{acao} ainda tem predicate ABAC M4 aplicavel: {nomes_m4} "
            "(deveria ser RBAC puro pos-ADR-0073)."
        )


def test_subcontratar_segue_rbac_puro() -> None:
    """calibracao.subcontratar nunca teve ABAC — segue so RBAC (matriz seed)."""
    aplicaveis = predicates_aplicaveis("calibracao.subcontratar")
    nomes_m4 = {p.nome for p in aplicaveis} & _PREDICATES_DESVINCULADOS_ADR0073
    assert nomes_m4 == set()
