"""Anti-regressao INV-OS-ATIV-003 (Q-OS-05 P5 conserto) — enum FECHADO 6 tipos.

INV-OS-ATIV-003: Toda AtividadeDaOS tem `tipo` em enum FECHADO de 6
valores (`calibracao`, `manutencao_corretiva`, `manutencao_preventiva`,
`instalacao`, `verificacao_inmetro`, `vistoria`). Tipo novo exige ADR
+ migration + atualizacao de hook.

≥3 testes: happy (6 valores enum aceitos), unhappy (tipo invalido
rejeitado), enum estavel (lista nao muda sem ADR-de-mudanca).
"""

from __future__ import annotations

import pytest
from src.domain.operacao.os.value_objects import TipoAtividade


def test_inv_os_ativ_003_happy_6_valores_canonicos():
    """6 tipos canonicos sao membros validos do enum."""
    assert {t.value for t in TipoAtividade} == {
        "calibracao",
        "manutencao_corretiva",
        "manutencao_preventiva",
        "instalacao",
        "verificacao_inmetro",
        "vistoria",
    }


def test_inv_os_ativ_003_unhappy_tipo_invalido_raises():
    with pytest.raises(ValueError):
        TipoAtividade("ensaio_destrutivo")


def test_inv_os_ativ_003_enum_size_fixo_6():
    """Tamanho do enum FECHADO: qualquer mudanca exige ADR + migration + hook."""
    assert len(TipoAtividade) == 6, (
        "INV-OS-ATIV-003 viola: enum mudou sem ADR. Atualize "
        "REGRAS-INEGOCIAVEIS.md + migration + hook enum-tipo-atividade-fechado.sh."
    )
