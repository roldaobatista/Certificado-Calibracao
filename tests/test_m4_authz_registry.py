"""Testes registro ABAC M4 calibracao (P4 Fase 4 Batch B — T-CAL-069..075).

Verifica que CalibracaoConfig.ready() registrou os 3 predicates
(cmc_cobre, procedimento_vigente_para, pode_aprovar_revisao_2a_conferencia)
no registry authz com escopo correto.

Por que importante:
- Sem o ready() rodando, predicate cmc_cobre nao bloqueia configuracao
  fora do CMC — RBC com falso positivo em escopo CGCRE = risco regulatorio.
- Sem escopo declarado, predicate poderia rodar em acoes nao-calibracao
  (ex: cliente.criar) — bug FB-A1 reportado no T-FB-01.

Padroes:
  - Testa apenas o registry; comportamento dos predicates ja coberto em
    test_m4_predicates_calibracao.py.
  - Sem chamadas a DB (registry eh estrutura in-memory).
"""

from __future__ import annotations

from src.infrastructure.authz.predicates import get_predicates, predicates_aplicaveis

# Sem pytest.mark.django_db — registry eh estrutura in-memory populada por
# AppConfig.ready() no import do Django settings; nao depende de DB.


def test_cmc_cobre_registrado_com_escopo_correto() -> None:
    """cmc_cobre aplica em calibracao.configurar + iniciar_leituras."""
    registry = get_predicates()
    assert "cmc_cobre" in registry, (
        "cmc_cobre nao foi registrado — CalibracaoConfig.ready() nao rodou "
        "ou esta com erro. Conferir src/infrastructure/calibracao/apps.py."
    )
    pred = registry["cmc_cobre"]
    assert pred.aplica("calibracao.configurar")
    assert pred.aplica("calibracao.iniciar_leituras")


def test_procedimento_vigente_para_registrado_so_em_configurar() -> None:
    """procedimento_vigente_para aplica APENAS em calibracao.configurar."""
    registry = get_predicates()
    assert "procedimento_vigente_para" in registry
    pred = registry["procedimento_vigente_para"]
    assert pred.aplica("calibracao.configurar")
    # NAO aplica em iniciar (snapshot ja cravado em configurar)
    assert not pred.aplica("calibracao.iniciar_leituras")


def test_pode_aprovar_revisao_registrado_nas_duas_aprovacoes() -> None:
    """pode_aprovar_revisao_2a_conferencia aplica nas 2 aprovacoes (cl. 6.2.5)."""
    registry = get_predicates()
    assert "pode_aprovar_revisao_2a_conferencia" in registry
    pred = registry["pode_aprovar_revisao_2a_conferencia"]
    assert pred.aplica("calibracao.aprovar_revisao")
    assert pred.aplica("calibracao.aprovar_2a_conferencia")


def test_predicates_nao_vazam_em_acoes_nao_calibracao() -> None:
    """Predicates M4 NAO aplicam em acoes fora de calibracao.*."""
    registry = get_predicates()
    for nome_pred in [
        "cmc_cobre",
        "procedimento_vigente_para",
        "pode_aprovar_revisao_2a_conferencia",
    ]:
        if nome_pred not in registry:
            continue
        pred = registry[nome_pred]
        # Acoes de outros modulos NAO devem disparar predicates M4
        assert not pred.aplica("os.criar")
        assert not pred.aplica("clientes.criar")
        assert not pred.aplica("certificado.emitir")
        assert not pred.aplica("equipamentos.criar")


def test_predicates_aplicaveis_em_configurar() -> None:
    """predicates_aplicaveis('calibracao.configurar') retorna 2 predicates."""
    aplicaveis = predicates_aplicaveis("calibracao.configurar")
    nomes = {p.nome for p in aplicaveis}
    # cmc_cobre + procedimento_vigente_para (Fase 4 atual; mais virao em Fase 5)
    assert "cmc_cobre" in nomes
    assert "procedimento_vigente_para" in nomes


def test_predicates_aplicaveis_em_aprovar_revisao() -> None:
    aplicaveis = predicates_aplicaveis("calibracao.aprovar_revisao")
    nomes = {p.nome for p in aplicaveis}
    assert "pode_aprovar_revisao_2a_conferencia" in nomes
    # cmc_cobre NAO aplica em aprovar (RBC ja validado em configurar)
    assert "cmc_cobre" not in nomes


def test_predicates_aplicaveis_em_acao_sem_predicate_retorna_lista_vazia() -> None:
    """ABAC neutro pra actions sem predicate aplicavel — segue RBAC."""
    # calibracao.subcontratar nao tem predicate ABAC (so RBAC matriz authz)
    aplicaveis = predicates_aplicaveis("calibracao.subcontratar")
    nomes_m4 = {p.nome for p in aplicaveis} & {
        "cmc_cobre",
        "procedimento_vigente_para",
        "pode_aprovar_revisao_2a_conferencia",
    }
    # Nenhum predicate M4 aplica em subcontratar
    assert nomes_m4 == set()


def test_registry_tem_3_predicates_m4() -> None:
    """Exatamente 3 predicates M4 registrados nesta release."""
    registry = get_predicates()
    nomes_m4 = {"cmc_cobre", "procedimento_vigente_para", "pode_aprovar_revisao_2a_conferencia"}
    presentes_m4 = nomes_m4 & set(registry)
    assert presentes_m4 == nomes_m4, (
        f"Predicates M4 ausentes: {nomes_m4 - presentes_m4}"
    )
