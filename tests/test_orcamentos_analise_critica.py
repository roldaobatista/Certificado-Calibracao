"""Testes PUROS da análise crítica cl. 7.1 — matriz A/B/C/D (T-ORC-033 / Onda 2c-2).

Cobrem a função ``decidir_analise_critica`` (domínio, sem banco) por toda a matriz
de ``docs/faseamento/orcamentos/analise-critica-matriz.md`` + o snapshot_hash
(ADR-0029). Provam INV-ORC-CL71-001 (A fail-closed; perfil indeterminado fail-closed)
na camada de decisão; o E2E (test_orcamentos_fatia2) prova a integração com portas.
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

import pytest
from src.domain.comercial.orcamentos.analise_critica import (
    NORMA_REFERENCIA_CL71,
    TEXTO_RESSALVA_ACREDITACAO_SUSPENSA,
    DecisaoAnaliseCritica,
    ResultadoItemMensurando,
    calcular_snapshot_hash_analise,
    decidir_analise_critica,
)
from src.domain.comercial.orcamentos.enums import (
    SeveridadeRessalva,
    VeredictoAnaliseCritica,
)
from src.domain.comercial.orcamentos.erros import PerfilIndeterminado
from src.domain.comercial.orcamentos.transicoes import (
    TEXTO_RESSALVA_PADRAO_INDISPONIVEL,
)

# ---------------------------------------------------------------------------
# Builders de ResultadoItemMensurando
# ---------------------------------------------------------------------------


def _item_ok() -> ResultadoItemMensurando:
    """Item viável: CMC cobre + procedimento vigente."""
    return ResultadoItemMensurando(
        equipamento_id=uuid4(),
        grandeza="massa",
        faixa_min=Decimal("0"),
        faixa_max=Decimal("200"),
        unidade="kg",
        cobre_cmc=True,
        cmc_reason="",
        procedimento_ok=True,
        procedimento_id=str(uuid4()),
        procedimento_codigo="POP-CAL-0042",
        procedimento_versao="3",
        procedimento_revisao="2",
        procedimento_hash_anexo="sha256:deadbeef",
    )


def _item_sem_cmc() -> ResultadoItemMensurando:
    """Item inviável: fora do escopo CMC (procedimento existe)."""
    return ResultadoItemMensurando(
        equipamento_id=uuid4(),
        grandeza="massa",
        faixa_min=Decimal("0"),
        faixa_max=Decimal("5000"),
        unidade="kg",
        cobre_cmc=False,
        cmc_reason="cmc_fora_do_escopo",
        procedimento_ok=True,
        procedimento_id=str(uuid4()),
        procedimento_codigo="POP-CAL-0042",
        procedimento_versao="3",
        procedimento_revisao="2",
        procedimento_hash_anexo="sha256:deadbeef",
    )


def _item_sem_procedimento() -> ResultadoItemMensurando:
    """Item inviável: sem procedimento vigente (CMC cobre)."""
    return ResultadoItemMensurando(
        equipamento_id=uuid4(),
        grandeza="temperatura",
        faixa_min=Decimal("-40"),
        faixa_max=Decimal("80"),
        unidade="degC",
        cobre_cmc=True,
        cmc_reason="",
        procedimento_ok=False,
    )


# ---------------------------------------------------------------------------
# Perfil indeterminado / inválido → fail-closed
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("perfil", ["", "  ", "X", "Z", "ab"])
def test_perfil_indeterminado_levanta(perfil: str) -> None:
    with pytest.raises(PerfilIndeterminado):
        decidir_analise_critica(perfil=perfil, acreditacao_suspensa=False, resultados=[_item_ok()])


def test_perfil_normalizado_aceita_minuscula_e_espacos() -> None:
    dec = decidir_analise_critica(perfil=" a ", acreditacao_suspensa=False, resultados=[_item_ok()])
    assert dec.perfil_normalizado == "A"


# ---------------------------------------------------------------------------
# Perfil D → desabilitada (não avalia)
# ---------------------------------------------------------------------------


def test_perfil_d_desabilitada_ignora_resultados() -> None:
    dec = decidir_analise_critica(
        perfil="D", acreditacao_suspensa=False, resultados=[_item_sem_cmc()]
    )
    assert dec.veredito is VeredictoAnaliseCritica.DESABILITADA
    assert dec.itens_avaliados == ()
    assert dec.bloqueia is False
    assert dec.severidade is None
    assert dec.exige_confirmacao_ressalvas is False


# ---------------------------------------------------------------------------
# A/B/C sem item de calibração → aprovada (AJUSTE-1)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("perfil", ["A", "B", "C"])
def test_sem_item_calibracao_aprova(perfil: str) -> None:
    dec = decidir_analise_critica(perfil=perfil, acreditacao_suspensa=False, resultados=[])
    assert dec.veredito is VeredictoAnaliseCritica.APROVADA
    assert dec.itens_avaliados == ()
    assert dec.bloqueia is False


# ---------------------------------------------------------------------------
# Perfil A — fail-closed
# ---------------------------------------------------------------------------


def test_perfil_a_todos_ok_com_ressalva_padrao() -> None:
    dec = decidir_analise_critica(
        perfil="A", acreditacao_suspensa=False, resultados=[_item_ok(), _item_ok()]
    )
    assert dec.veredito is VeredictoAnaliseCritica.COM_RESSALVA
    assert dec.severidade is SeveridadeRessalva.MEDIA
    assert dec.bloqueia is False
    assert dec.exige_confirmacao_ressalvas is True
    # Ressalva de padrão não verificável em cada item (GATE-ORC-PADRAO / TL-ORC-10).
    for it in dec.itens_avaliados:
        assert TEXTO_RESSALVA_PADRAO_INDISPONIVEL in it["ressalvas"]


@pytest.mark.parametrize("item_falho", [_item_sem_cmc, _item_sem_procedimento])
def test_perfil_a_algum_falho_reprova(item_falho) -> None:
    dec = decidir_analise_critica(
        perfil="A", acreditacao_suspensa=False, resultados=[_item_ok(), item_falho()]
    )
    assert dec.veredito is VeredictoAnaliseCritica.REPROVADA
    assert dec.bloqueia is True
    assert dec.severidade is None


def test_perfil_a_suspenso_reprova_mesmo_com_itens_ok() -> None:
    dec = decidir_analise_critica(perfil="A", acreditacao_suspensa=True, resultados=[_item_ok()])
    assert dec.veredito is VeredictoAnaliseCritica.REPROVADA
    assert dec.bloqueia is True
    assert TEXTO_RESSALVA_ACREDITACAO_SUSPENSA in dec.itens_avaliados[0]["ressalvas"]


# ---------------------------------------------------------------------------
# Perfil B — fail-open lazy com ressalva media
# ---------------------------------------------------------------------------


def test_perfil_b_todos_ok_aprova() -> None:
    dec = decidir_analise_critica(perfil="B", acreditacao_suspensa=False, resultados=[_item_ok()])
    assert dec.veredito is VeredictoAnaliseCritica.APROVADA
    assert dec.severidade is None
    assert dec.exige_confirmacao_ressalvas is False


def test_perfil_b_algum_falho_com_ressalva_media() -> None:
    dec = decidir_analise_critica(
        perfil="B", acreditacao_suspensa=False, resultados=[_item_sem_cmc()]
    )
    assert dec.veredito is VeredictoAnaliseCritica.COM_RESSALVA
    assert dec.severidade is SeveridadeRessalva.MEDIA
    assert dec.bloqueia is False
    assert dec.exige_confirmacao_ressalvas is True
    assert dec.itens_avaliados[0]["ressalvas"]  # ressalva de falha presente


def test_perfil_b_suspensao_irrelevante() -> None:
    # Suspensão só afeta perfil A; em B é ignorada.
    dec = decidir_analise_critica(perfil="B", acreditacao_suspensa=True, resultados=[_item_ok()])
    assert dec.veredito is VeredictoAnaliseCritica.APROVADA


# ---------------------------------------------------------------------------
# Perfil C — parcial/warning, ressalva baixa
# ---------------------------------------------------------------------------


def test_perfil_c_todos_ok_aprova() -> None:
    dec = decidir_analise_critica(perfil="C", acreditacao_suspensa=False, resultados=[_item_ok()])
    assert dec.veredito is VeredictoAnaliseCritica.APROVADA


def test_perfil_c_algum_falho_com_ressalva_baixa_sem_confirmacao() -> None:
    dec = decidir_analise_critica(
        perfil="C", acreditacao_suspensa=False, resultados=[_item_sem_procedimento()]
    )
    assert dec.veredito is VeredictoAnaliseCritica.COM_RESSALVA
    assert dec.severidade is SeveridadeRessalva.BAIXA
    assert dec.bloqueia is False
    assert dec.exige_confirmacao_ressalvas is False


# ---------------------------------------------------------------------------
# itens_avaliados ricos (C1 / AJUSTE-2)
# ---------------------------------------------------------------------------


def test_itens_avaliados_carregam_registro_probatorio() -> None:
    item = _item_ok()
    dec = decidir_analise_critica(perfil="B", acreditacao_suspensa=False, resultados=[item])
    av = dec.itens_avaliados[0]
    assert av["equipamento_id"] == str(item.equipamento_id)
    assert av["grandeza"] == "massa"
    assert av["faixa_min"] == "0"
    assert av["faixa_max"] == "200"
    assert av["unidade"] == "kg"
    assert av["cobre_cmc"] is True
    assert av["cmc_codigo_ref"] is None  # Wave A — porta não devolve código
    assert av["cmc_reason"] == ""
    assert av["procedimento_ok"] is True
    assert av["procedimento_codigo"] == "POP-CAL-0042"
    assert av["procedimento_versao"] == "3"
    assert av["procedimento_revisao"] == "2"
    assert av["procedimento_hash_anexo"] == "sha256:deadbeef"


# ---------------------------------------------------------------------------
# snapshot_hash — determinismo + formato (ADR-0029)
# ---------------------------------------------------------------------------


def _kwargs_hash(dec: DecisaoAnaliseCritica) -> dict:
    return {
        "orcamento_id": uuid4(),
        "versao_id": uuid4(),
        "perfil": dec.perfil_normalizado,
        "veredito": dec.veredito,
        "norma_referencia": NORMA_REFERENCIA_CL71,
        "itens_avaliados": dec.itens_avaliados,
        "avaliada_em": datetime(2026, 6, 14, 12, 0, tzinfo=UTC),
        "avaliada_por": "user-1",
    }


def test_snapshot_hash_deterministico_e_versionado() -> None:
    dec = decidir_analise_critica(perfil="B", acreditacao_suspensa=False, resultados=[_item_ok()])
    kw = _kwargs_hash(dec)
    h1 = calcular_snapshot_hash_analise(**kw)
    h2 = calcular_snapshot_hash_analise(**kw)
    assert h1 == h2
    assert h1.startswith("v01$")  # VERSAO_HMAC_ATUAL=1, zero-padded


def test_snapshot_hash_muda_com_payload() -> None:
    dec = decidir_analise_critica(perfil="B", acreditacao_suspensa=False, resultados=[_item_ok()])
    kw = _kwargs_hash(dec)
    h1 = calcular_snapshot_hash_analise(**kw)
    h2 = calcular_snapshot_hash_analise(**{**kw, "avaliada_por": "user-2"})
    assert h1 != h2
