"""M7 Fatia 3 (T-PROC-044/045) — wire-in `procedimento_vigente_para` real no
`configurar_calibracao` (TST-005, transição fail-open→fail-closed).

Reusa o harness do teste de use case M4. A 2ª porta `procedimento` é injetada
(adapter real seria `procedimentos_calibracao.query_service.cobre_procedimento`).
Cobre: RBC com procedimento vigente preenche snapshot real; RBC sem procedimento
→ 412 ProcedimentoVigenteAusente; NÃO-RBC nunca chama a porta; ordem
escopo→procedimento (escopo falho para antes); default lazy mantém legado M4.
"""

from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

import pytest
from src.application.metrologia.calibracao.configurar_calibracao import (
    EscopoNaoCobreFaixa,
    ProcedimentoVigenteAusente,
    executar,
)
from src.domain.metrologia.calibracao.enums import EstadoCalibracao, TipoAcreditacao

from tests.test_m4_uc_configurar_calibracao import (
    _criar_calibracao_avulsa,
    _input_avulsa,
)
from tests.test_m4_uc_criar_calibracao import FakeCalibracaoRepository


def _input_rbc(cal_id, **over):
    base = {
        "escopo_id": uuid4(),
        "grandeza_calibrada": "massa",
        "faixa_calibrada_min": Decimal("0"),
        "faixa_calibrada_max": Decimal("100"),
        "unidade_calibrada": "kg",
    }
    base.update(over)
    return _input_avulsa(cal_id, **base)


def _proc_vigente(**_kw):
    return True, {
        "procedimento_id": "11111111-1111-1111-1111-111111111111",
        "codigo": "PC-MASSA-007",
        "versao": "3",
        "numero_revisao": "Rev. 03",
        "hash_anexo": "v01$deadbeef",
    }


def _proc_ausente(**_kw):
    return False, None


def _proc_explode(**_kw):
    raise AssertionError("porta de procedimento NAO deveria ser chamada aqui")


def _cobertura_falha(**_kw):
    return False, "cmc_fora_do_escopo"


# --------------------------------------------------------------------------
class TestWireInProcedimento:
    def test_rbc_com_procedimento_vigente_preenche_snapshot_real(self):
        repo = FakeCalibracaoRepository()
        cal_id = _criar_calibracao_avulsa(repo, tipo_acreditacao=TipoAcreditacao.RBC)
        out = executar(_input_rbc(cal_id), repo, procedimento=_proc_vigente)
        assert out.snapshot.status == EstadoCalibracao.CONFIGURADA
        # snapshot do procedimento veio RESOLVIDO server-side (C-1), não do payload
        assert str(out.snapshot.procedimento_id) == "11111111-1111-1111-1111-111111111111"
        assert out.snapshot.procedimento_versao_snapshot == {
            "codigo": "PC-MASSA-007",
            "versao": "3",
            "numero_revisao": "Rev. 03",
            "hash_anexo": "v01$deadbeef",
        }

    def test_rbc_sem_procedimento_bloqueia_412(self):
        repo = FakeCalibracaoRepository()
        cal_id = _criar_calibracao_avulsa(repo, tipo_acreditacao=TipoAcreditacao.RBC)
        with pytest.raises(ProcedimentoVigenteAusente) as exc:
            executar(_input_rbc(cal_id), repo, procedimento=_proc_ausente)
        assert exc.value.grandeza == "massa"
        assert exc.value.motivo == "procedimento_inexistente"

    def test_nao_rbc_nunca_chama_porta(self):
        repo = FakeCalibracaoRepository()
        cal_id = _criar_calibracao_avulsa(repo, tipo_acreditacao=TipoAcreditacao.NAO_RBC)
        # _proc_explode levantaria se chamado — NÃO-RBC faz short-circuit
        out = executar(_input_avulsa(cal_id), repo, procedimento=_proc_explode)
        assert out.snapshot.status == EstadoCalibracao.CONFIGURADA

    def test_ordem_escopo_antes_de_procedimento(self):
        repo = FakeCalibracaoRepository()
        cal_id = _criar_calibracao_avulsa(repo, tipo_acreditacao=TipoAcreditacao.RBC)
        # escopo falha -> EscopoNaoCobreFaixa ANTES de tocar a porta de procedimento
        with pytest.raises(EscopoNaoCobreFaixa):
            executar(
                _input_rbc(cal_id),
                repo,
                cobertura=_cobertura_falha,
                procedimento=_proc_explode,
            )

    def test_default_lazy_mantem_legado_m4(self):
        """Sem injetar a porta real (default fail-open lazy), RBC não bloqueia e
        mantém o procedimento do input (legado M4 reverde)."""
        repo = FakeCalibracaoRepository()
        cal_id = _criar_calibracao_avulsa(repo, tipo_acreditacao=TipoAcreditacao.RBC)
        inp = _input_rbc(cal_id)
        out = executar(inp, repo)  # default cobertura True + default proc lazy
        assert out.snapshot.status == EstadoCalibracao.CONFIGURADA
        assert out.snapshot.procedimento_id == inp.procedimento_id  # mantido do input
