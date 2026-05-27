"""Testes dos 3 predicates ABAC M4 calibracao (T-CAL-037..039).

Cobre:
  - cmc_cobre (RETROFIT Sprint 2 ADR-0067 — le perfil de Tenant via ContextVar)
  - procedimento_vigente_para (STUB Wave A — fail-open;
    DENY se tenant_id ausente)
  - pode_aprovar_revisao_2a_conferencia (REAL — segregacao funcoes
    cl. 6.2.5 + ADR-0026 excecao 4 condicoes)

**RETROFIT 2026-05-27 (T-SAN-PERFIL-018 / Sprint 2 ADR-0067):**
`cmc_cobre` deixou de ler `tipo_acreditacao` do payload (FAIL L6 — fraude
documental viavel) e passou a consultar `Tenant.perfil_regulatorio` via
ContextVar `perfil_tenant_context`. Os testes precisam popular o ContextVar
ANTES de chamar o predicate. Pattern:

    from src.infrastructure.multitenant.context import perfil_tenant_context
    token = perfil_tenant_context.set("A")
    try:
        ok, motivo = cmc_cobre({...})
    finally:
        perfil_tenant_context.reset(token)

Padroes:
  - TST-005: >=1 happy + >=1 borda por predicate.
  - Predicates puros (sem DB): testaveis sem Django.
"""

from __future__ import annotations

from contextlib import contextmanager
from uuid import uuid4

from src.infrastructure.calibracao.predicates_calibracao import (
    EXCECOES_2A_CONFERENCIA,
    cmc_cobre,
    pode_aprovar_revisao_2a_conferencia,
    procedimento_vigente_para,
)
from src.infrastructure.multitenant.context import perfil_tenant_context


@contextmanager
def _perfil(perfil: str):
    """Helper context manager pra popular `perfil_tenant_context` em teste."""
    token = perfil_tenant_context.set(perfil)
    try:
        yield
    finally:
        perfil_tenant_context.reset(token)


# =====================================================================
# cmc_cobre (T-CAL-037 + RETROFIT T-SAN-PERFIL-018)
# =====================================================================


class TestCmcCobre:
    def test_nao_aplica_em_tenant_nao_rbc(self) -> None:
        """Perfil B (rastreavel nao-acreditado) — predicate nao aplica CMC."""
        with _perfil("B"):
            ok, motivo = cmc_cobre(
                {
                    "tenant_id": uuid4(),
                    "grandeza": "massa",
                }
            )
        assert ok is True
        assert motivo == ""

    def test_nao_aplica_em_tenant_perfil_d(self) -> None:
        """Perfil D (comercial puro) — predicate nao aplica CMC."""
        with _perfil("D"):
            ok, motivo = cmc_cobre({"tenant_id": uuid4()})
        assert ok is True
        assert motivo == ""

    def test_rbc_sem_grandeza_recusa(self) -> None:
        """Tenant Perfil A precisa declarar grandeza pra validar CMC."""
        with _perfil("A"):
            ok, motivo = cmc_cobre(
                {
                    "tenant_id": uuid4(),
                    "grandeza": "",
                }
            )
        assert ok is False
        assert motivo == "cmc_grandeza_resource_ausente"

    def test_resource_invalido_sem_tenant_id(self) -> None:
        with _perfil("A"):
            ok, motivo = cmc_cobre({"grandeza": "massa"})
        assert ok is False
        assert motivo == "cmc_resource_invalido"

    def test_rbc_com_grandeza_passa_stub_wave_a(self) -> None:
        """Perfil A — STUB ADR-0066: fail-open lazy ate modulo `escopos-cmc`."""
        with _perfil("A"):
            ok, motivo = cmc_cobre(
                {
                    "tenant_id": uuid4(),
                    "grandeza": "massa",
                    "faixa_min": "0",
                    "faixa_max": "200",
                    "data": "2026-05-25",
                }
            )
        assert ok is True
        assert motivo == ""

    def test_perfil_indisponivel_bloqueia(self) -> None:
        """T-SAN-PERFIL-018 / INV-TENANT-PERFIL-004 — sem ContextVar nem DB,
        predicate fail-closed."""
        # NAO popular o ContextVar — fora de request middleware ele fica vazio.
        # Sem active_tenant_context tambem, helper retorna "" e predicate DENY.
        ok, motivo = cmc_cobre(
            {
                "tenant_id": uuid4(),
                "grandeza": "massa",
            }
        )
        assert ok is False
        assert motivo == "tenant_perfil_indisponivel"

    def test_fraude_payload_rbc_em_tenant_nao_a_bloqueia(self) -> None:
        """T-SAN-PERFIL-018 / AC-002-2 — FAIL L6 fechado.

        Operador autenticado em tenant Perfil B envia payload com
        `tipo_acreditacao=RBC` (compat-shim legacy). Sistema detecta divergencia
        e responde DENY com reason `tipo_acreditacao_divergente_do_tenant`.
        View handler grava evento WORM `tentativa_downgrade_perfil`.
        """
        with _perfil("B"):
            ok, motivo = cmc_cobre(
                {
                    "tenant_id": uuid4(),
                    "tipo_acreditacao": "RBC",
                    "grandeza": "massa",
                }
            )
        assert ok is False
        assert motivo == "tipo_acreditacao_divergente_do_tenant"

    def test_fraude_payload_rbc_em_tenant_d_bloqueia(self) -> None:
        """T-SAN-PERFIL-018 — perfil D nao pode emitir RBC mesmo com payload."""
        with _perfil("D"):
            ok, motivo = cmc_cobre(
                {
                    "tenant_id": uuid4(),
                    "tipo_acreditacao": "RBC",
                    "grandeza": "massa",
                }
            )
        assert ok is False
        assert motivo == "tipo_acreditacao_divergente_do_tenant"

    def test_payload_rbc_em_tenant_a_continua_aceito(self) -> None:
        """T-SAN-PERFIL-018 — payload com tipo_acreditacao=RBC em tenant
        Perfil A nao quebra (compat-shim emite WARN log mas aceita)."""
        with _perfil("A"):
            ok, motivo = cmc_cobre(
                {
                    "tenant_id": uuid4(),
                    "tipo_acreditacao": "RBC",  # divergencia OK
                    "grandeza": "massa",
                }
            )
        assert ok is True
        assert motivo == ""


# =====================================================================
# procedimento_vigente_para (T-CAL-038)
# =====================================================================


class TestProcedimentoVigentePara:
    def test_nao_aplica_sem_grandeza(self) -> None:
        # Atividade nao-calibracao (sem grandeza) -> predicate nao aplica
        ok, motivo = procedimento_vigente_para(
            {"tenant_id": uuid4()}
        )
        assert ok is True
        assert motivo == ""

    def test_grandeza_vazia_nao_aplica(self) -> None:
        ok, motivo = procedimento_vigente_para(
            {"tenant_id": uuid4(), "grandeza": ""}
        )
        assert ok is True
        assert motivo == ""

    def test_passa_stub_wave_a(self) -> None:
        # STUB Wave A: fail-open ate modulo `procedimentos_tecnicos` chegar
        ok, motivo = procedimento_vigente_para(
            {
                "tenant_id": uuid4(),
                "grandeza": "temperatura",
                "data": "2026-05-25",
            }
        )
        assert ok is True
        assert motivo == ""

    def test_resource_invalido_sem_tenant_id(self) -> None:
        ok, motivo = procedimento_vigente_para({"grandeza": "massa"})
        assert ok is False
        assert motivo == "procedimento_resource_invalido"

    def test_grandeza_normalizada_lowercase(self) -> None:
        # MASSA vira massa internamente (defensivo)
        ok, motivo = procedimento_vigente_para(
            {"tenant_id": uuid4(), "grandeza": "MASSA"}
        )
        assert ok is True
        assert motivo == ""


# =====================================================================
# pode_aprovar_revisao_2a_conferencia (T-CAL-039) — REAL
# =====================================================================


class TestPodeAprovarRevisao:
    def test_happy_revisor_diferente_executor(self) -> None:
        executor = uuid4()
        revisor = uuid4()
        assert executor != revisor
        ok, motivo = pode_aprovar_revisao_2a_conferencia(
            {
                "action": "revisao",
                "executor_id": executor,
                "revisor_id": revisor,
            }
        )
        assert ok is True
        assert motivo == ""

    def test_fraude_revisor_eh_executor(self) -> None:
        mesmo = uuid4()
        ok, motivo = pode_aprovar_revisao_2a_conferencia(
            {
                "action": "revisao",
                "executor_id": mesmo,
                "revisor_id": mesmo,
            }
        )
        assert ok is False
        assert motivo == "fraude_revisor_eh_executor"

    def test_revisor_eh_executor_com_excecao_adr_0026_passa(self) -> None:
        # ADR-0026: 4 condicoes objetivas permitem revisor=executor
        mesmo = uuid4()
        ok, motivo = pode_aprovar_revisao_2a_conferencia(
            {
                "action": "revisao",
                "executor_id": mesmo,
                "revisor_id": mesmo,
                "excecao_motivo": "TENANT_PEQUENO_5_CAL_MES",
            }
        )
        assert ok is True
        assert motivo == ""

    def test_excecao_codigo_invalido(self) -> None:
        ok, motivo = pode_aprovar_revisao_2a_conferencia(
            {
                "action": "revisao",
                "executor_id": uuid4(),
                "revisor_id": uuid4(),
                "excecao_motivo": "CODIGO_INVENTADO_NA_HORA",
            }
        )
        assert ok is False
        assert motivo == "excecao_adr_0026_invalida"


class TestPodeAprovar2aConferencia:
    def test_happy_3_pessoas_diferentes(self) -> None:
        executor = uuid4()
        revisor = uuid4()
        conferente = uuid4()
        ok, motivo = pode_aprovar_revisao_2a_conferencia(
            {
                "action": "2a_conferencia",
                "executor_id": executor,
                "revisor_id": revisor,
                "conferente_id": conferente,
            }
        )
        assert ok is True
        assert motivo == ""

    def test_fraude_conferente_eh_executor(self) -> None:
        executor = uuid4()
        revisor = uuid4()
        ok, motivo = pode_aprovar_revisao_2a_conferencia(
            {
                "action": "2a_conferencia",
                "executor_id": executor,
                "revisor_id": revisor,
                "conferente_id": executor,  # = executor
            }
        )
        assert ok is False
        assert motivo == "fraude_conferente_eh_revisor_ou_executor"

    def test_fraude_conferente_eh_revisor(self) -> None:
        executor = uuid4()
        revisor = uuid4()
        ok, motivo = pode_aprovar_revisao_2a_conferencia(
            {
                "action": "2a_conferencia",
                "executor_id": executor,
                "revisor_id": revisor,
                "conferente_id": revisor,  # = revisor
            }
        )
        assert ok is False
        assert motivo == "fraude_conferente_eh_revisor_ou_executor"

    def test_resource_invalido_sem_revisor(self) -> None:
        ok, motivo = pode_aprovar_revisao_2a_conferencia(
            {
                "action": "2a_conferencia",
                "executor_id": uuid4(),
                "conferente_id": uuid4(),
            }
        )
        assert ok is False
        assert motivo == "revisao_conferencia_resource_invalido"

    def test_excecao_adr_0026_passa_em_2a_conferencia(self) -> None:
        # ADR-0026: as 4 condicoes valem tanto pra revisao quanto p/ 2a
        mesmo = uuid4()
        ok, motivo = pode_aprovar_revisao_2a_conferencia(
            {
                "action": "2a_conferencia",
                "executor_id": mesmo,
                "revisor_id": mesmo,
                "conferente_id": mesmo,
                "excecao_motivo": "GRANDEZA_RT_UNICO_TENANT",
            }
        )
        assert ok is True
        assert motivo == ""


class TestActionInvalida:
    def test_action_desconhecida_recusa(self) -> None:
        ok, motivo = pode_aprovar_revisao_2a_conferencia(
            {
                "action": "validacao_externa",
                "executor_id": uuid4(),
            }
        )
        assert ok is False
        assert motivo == "revisao_conferencia_resource_invalido"

    def test_action_ausente_recusa(self) -> None:
        ok, motivo = pode_aprovar_revisao_2a_conferencia(
            {"executor_id": uuid4()}
        )
        assert ok is False
        assert motivo == "revisao_conferencia_resource_invalido"


def test_lista_excecoes_adr_0026_completa() -> None:
    """Sanity: 4 codigos previstos em ADR-0026 estao na whitelist."""
    assert "TENANT_PEQUENO_5_CAL_MES" in EXCECOES_2A_CONFERENCIA
    assert "GRANDEZA_RT_UNICO_TENANT" in EXCECOES_2A_CONFERENCIA
    assert "CALIBRACAO_URGENTE_RECALL" in EXCECOES_2A_CONFERENCIA
    assert "DOC_TECNICA_AUTO_SUFICIENTE" in EXCECOES_2A_CONFERENCIA
    assert len(EXCECOES_2A_CONFERENCIA) == 4
