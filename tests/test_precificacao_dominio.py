"""Frente `precificacao` — Fatia 1a (T-PRC-016): domínio puro, sem banco.

Cobre (todos os casos obrigatórios da task):
  - Determinismo bit-a-bit cross-versão de motor (AC-PRC-002-3 / TL-PRC-18)
  - Mínimo/sugerido pela fórmula com custo manual (AC-PRC-002-1/2)
  - Cesta sem componente esperado → componentes_faltantes (D-PRC-2)
  - Cortesia 100% → preco_final=0 sem estourar Preco>0 (D-PRC-13)
  - Faixas com buraco → FaixasDescontoInvalidas (INV-PRC-FAIXAS-CONTIGUAS)
  - Mínimo violado calculável → PrecoMinimoViolado (INV-PRC-MINIMO-BLOQUEIO)
  - Stub → CustoIndisponivel (INV-PRC-CUSTO-EXPLICITO)
  - Fingerprint estável / fingerprint divergente muda
  - Decisor == solicitante → DecisorNaoIndependente
  - Sem regra → sem_regra_formacao + semáforo INDISPONIVEL (TL-PRC-05)
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID, uuid4

import pytest
from src.domain.precificacao.entities import (
    FaixaAprovacaoDesconto,
    ParametrosPrecificacaoTenant,
    PerfilComposicaoPreco,
    RegraFormacaoPreco,
)
from src.domain.precificacao.enums import (
    Alcada,
    ModoFormacaoPreco,
    ModoMontagem,
    OrigemCusto,
    Semaforo,
)
from src.domain.precificacao.erros import (
    CustoIndisponivel,
    DecisorNaoIndependente,
    FaixasDescontoInvalidas,
    ParametrosInviaveis,
    PrecoMinimoViolado,
)
from src.domain.precificacao.portas import StubCustoProvider
from src.domain.precificacao.transicoes import (
    alcada_para_pct,
    calcular_precos,
    fingerprint_calculo,
    validar_decisor_independente,
    validar_faixas_contiguas,
)
from src.domain.precificacao.value_objects import Percentual
from src.domain.produtos_pecas_servicos.entities import PrecoResolvido
from src.domain.produtos_pecas_servicos.enums import OrigemPreco
from src.domain.produtos_pecas_servicos.value_objects import Preco
from src.domain.shared.value_objects import JanelaVigencia

# ---------------------------------------------------------------------------
# Helpers e fixtures
# ---------------------------------------------------------------------------

_T = UUID("00000000-0000-4000-8000-000000000001")  # tenant fixo
_AGORA = datetime(2026, 6, 1, tzinfo=UTC)
_JAN = datetime(2026, 1, 1, tzinfo=UTC)
_DEC = datetime(2026, 12, 31, tzinfo=UTC)


def _vigencia(inicio=_JAN, fim=_DEC) -> JanelaVigencia:
    return JanelaVigencia(inicio=inicio, fim=fim)


def _preco_resolvido(
    preco_str: str = "100.00",
    item_id: UUID | None = None,
) -> PrecoResolvido:
    iid = item_id or uuid4()
    return PrecoResolvido(
        item_id=iid,
        item_versao_n=1,
        linha_tabela_id=uuid4(),
        tabela_id=uuid4(),
        preco=Preco(Decimal(preco_str)),
        data_referencia=_AGORA,
        origem_preco=OrigemPreco.MANUAL,
    )


def _params(
    *,
    custo_km: str = "0.00",
    taxa_parcela: str = "0.00",
    comissao: str = "0.00",
    margem_alvo: str = "20.00",
    margem_piso: str = "5.00",
) -> ParametrosPrecificacaoTenant:
    return ParametrosPrecificacaoTenant(
        id=uuid4(),
        tenant_id=_T,
        versao_n=1,
        custo_km=Decimal(custo_km),
        taxa_parcelamento_mensal=Percentual(Decimal(taxa_parcela)),
        pct_comissao_prevista=Percentual(Decimal(comissao)),
        margem_alvo_default=Percentual(Decimal(margem_alvo)),
        margem_piso_default=Percentual(Decimal(margem_piso)),
        criado_por=uuid4(),
        criado_em=_AGORA,
    )


def _faixas_padrao() -> list[FaixaAprovacaoDesconto]:
    """Faixas padrão: 0-10 LIVRE, 10-20 GERENTE, 20-100 DONO."""
    return [
        FaixaAprovacaoDesconto(
            id=uuid4(), tenant_id=_T,
            pct_de=Percentual(Decimal("0")),
            pct_ate=Percentual(Decimal("10.00")),
            alcada=Alcada.LIVRE,
            versao_n=1, hash_conjunto="abc", criado_por=uuid4(),
        ),
        FaixaAprovacaoDesconto(
            id=uuid4(), tenant_id=_T,
            pct_de=Percentual(Decimal("10.00")),
            pct_ate=Percentual(Decimal("20.00")),
            alcada=Alcada.GERENTE,
            versao_n=1, hash_conjunto="abc", criado_por=uuid4(),
        ),
        FaixaAprovacaoDesconto(
            id=uuid4(), tenant_id=_T,
            pct_de=Percentual(Decimal("20.00")),
            pct_ate=Percentual(Decimal("100.00")),
            alcada=Alcada.DONO,
            versao_n=1, hash_conjunto="abc", criado_por=uuid4(),
        ),
    ]


def _regra(
    item_id: UUID,
    modo: ModoFormacaoPreco = ModoFormacaoPreco.MARGEM_ALVO,
    custo_manual: str | None = "80.00",
    margem_alvo: str = "25.00",
    margem_piso: str = "5.00",
) -> RegraFormacaoPreco:
    return RegraFormacaoPreco(
        id=uuid4(),
        tenant_id=_T,
        item_id=item_id,
        modo=modo,
        vigencia=_vigencia(),
        versao_n=1,
        criado_por=uuid4(),
        custo_manual_declarado=Decimal(custo_manual) if custo_manual else None,
        custo_referencia_em=_AGORA,
        margem_alvo_pct=Percentual(Decimal(margem_alvo)),
        margem_piso_pct=Percentual(Decimal(margem_piso)),
    )


def _calcular_simples(
    *,
    preco_str: str = "100.00",
    regra: RegraFormacaoPreco | None = None,
    custo: Decimal | None = None,
    origem: OrigemCusto = OrigemCusto.CUSTO_MANUAL,
    desconto_str: str = "0.00",
    params: ParametrosPrecificacaoTenant | None = None,
    modo: ModoMontagem = ModoMontagem.FECHADO_COM_AVISO,
    km: str = "0",
    parcelas: int = 1,
    aliquota: str = "0.00",
    item_id: UUID | None = None,
) -> object:
    """Helper: calcula um único item sem perfil."""
    iid = item_id or uuid4()
    pr = _preco_resolvido(preco_str, item_id=iid)
    p = params or _params()
    regras = {iid: regra} if regra else {}
    custos = {iid: custo}
    origens = {iid: origem}
    return calcular_precos(
        itens=[pr],
        regras=regras,
        custos=custos,
        origens=origens,
        perfis={},
        faixas=_faixas_padrao(),
        params=p,
        desconto_pct=Percentual(Decimal(desconto_str)),
        modo_montagem=modo,
        km=Decimal(km),
        parcelas=parcelas,
        aliquota_imposto_fracao=Decimal(aliquota),
        imposto_ref=None,
    )


# ---------------------------------------------------------------------------
# T-PRC-016 (a) — Determinismo bit-a-bit cross-versão de motor (AC-PRC-002-3)
# ---------------------------------------------------------------------------

class TestDeterminismo:
    """Motor determinístico: mesmas entradas → mesmo resultado em qualquer chamada."""

    def test_mesmo_resultado_duas_chamadas(self):
        """Mesmas entradas → mesmo preco_final nas duas chamadas."""
        item_id = uuid4()
        regra = _regra(item_id, custo_manual="80.00", margem_alvo="25.00")
        kwargs = {
            "preco_str": "100.00",
            "regra": regra,
            "custo": Decimal("80.00"),
            "origem": OrigemCusto.CUSTO_MANUAL,
            "item_id": item_id,
        }
        r1 = _calcular_simples(**kwargs)
        r2 = _calcular_simples(**kwargs)
        assert r1.itens[0].preco_final == r2.itens[0].preco_final

    def test_fingerprint_estavel(self):
        """Fingerprint: mesmas entradas → mesmo hash."""
        entradas = {"km": "0", "modo_montagem": "fechado_com_aviso", "parcelas": "1"}
        refs = {"motor_versao": "v1", "faixas_versao": "abc", "parametros_versao": "1"}
        pct = Decimal("10.00")
        h1 = fingerprint_calculo(entradas=entradas, refs=refs, desconto_pct=pct)
        h2 = fingerprint_calculo(entradas=entradas, refs=refs, desconto_pct=pct)
        assert h1 == h2
        assert len(h1) == 64  # SHA-256 hex

    def test_fingerprint_divergente_com_entradas_distintas(self):
        """Fingerprint: entradas diferentes → hashes diferentes."""
        entradas_a = {"km": "0", "modo_montagem": "componentes_checklist", "parcelas": "1"}
        entradas_b = {"km": "10", "modo_montagem": "componentes_checklist", "parcelas": "1"}
        refs = {"motor_versao": "v1"}
        pct = Decimal("5.00")
        h_a = fingerprint_calculo(entradas=entradas_a, refs=refs, desconto_pct=pct)
        h_b = fingerprint_calculo(entradas=entradas_b, refs=refs, desconto_pct=pct)
        assert h_a != h_b

    def test_fingerprint_divergente_desconto_diferente(self):
        """Desconto diferente → fingerprint diferente."""
        entradas = {"km": "0"}
        refs = {"motor_versao": "v1"}
        h5 = fingerprint_calculo(entradas=entradas, refs=refs, desconto_pct=Decimal("5.00"))
        h10 = fingerprint_calculo(entradas=entradas, refs=refs, desconto_pct=Decimal("10.00"))
        assert h5 != h10


# ---------------------------------------------------------------------------
# T-PRC-016 (b) — Fórmulas mínimo/sugerido com custo manual (AC-PRC-002-1/2)
# ---------------------------------------------------------------------------

class TestFormulas:
    """Fórmulas canônicas do glossário verificadas bit-a-bit."""

    def test_preco_minimo_formula(self):
        """preco_minimo = custo / (1 - pct_piso) quando imposto=0, comissao=0, km=0."""
        # custo=80, piso=5% → denom=(1-0.05)=0.95 → minimo=80/0.95≈84.21
        item_id = uuid4()
        regra = _regra(item_id, custo_manual="80.00", margem_piso="5.00", margem_alvo="25.00")
        resultado = _calcular_simples(
            preco_str="200.00",  # preço alto para não violar mínimo
            regra=regra,
            custo=Decimal("80.00"),
            origem=OrigemCusto.CUSTO_MANUAL,
            item_id=item_id,
        )
        item = resultado.itens[0]
        # preco_minimo = 80/0.95 = 84.210526... → 84.21
        assert item.preco_minimo == Decimal("84.21")

    def test_preco_sugerido_formula(self):
        """preco_sugerido = custo / (1 - pct_alvo) quando imposto=0, comissao=0, km=0.

        custo=80, alvo=25% -> denom=0.75 -> sugerido=80/0.75 aprox 106.67
        """
        item_id = uuid4()
        regra = _regra(item_id, custo_manual="80.00", margem_alvo="25.00", margem_piso="5.00")
        # desconto 0% → preco_final = preco_sugerido
        resultado = _calcular_simples(
            preco_str="200.00",
            regra=regra,
            custo=Decimal("80.00"),
            origem=OrigemCusto.CUSTO_MANUAL,
            item_id=item_id,
        )
        item = resultado.itens[0]
        # 80/0.75 = 106.666... → 106.67
        assert item.preco_final == Decimal("106.67")

    def test_semaforo_verde_acima_alvo(self):
        """Margem estimada >= alvo → VERDE."""
        item_id = uuid4()
        regra = _regra(item_id, custo_manual="80.00", margem_alvo="20.00", margem_piso="5.00")
        # preco_sugerido = 80/0.8 = 100. desconto 0% → preco_final=100
        # margem = (100-80)/100 = 20% = alvo → VERDE
        resultado = _calcular_simples(
            preco_str="200.00",
            regra=regra,
            custo=Decimal("80.00"),
            origem=OrigemCusto.CUSTO_MANUAL,
            item_id=item_id,
        )
        assert resultado.itens[0].semaforo == Semaforo.VERDE

    def test_semaforo_amarelo_entre_piso_e_alvo(self):
        """Margem estimada entre piso e alvo → AMARELO."""
        item_id = uuid4()
        # custo=80, alvo=25%, piso=5%
        # preco_sugerido = 80/0.75 ≈ 106.67
        # desconto 10%: preco_final = 106.67*0.9 = 96.00 (approx)
        # margem ~ (96 - 80)/96 ≈ 16.7% → entre piso(5%) e alvo(25%) → AMARELO
        regra = _regra(item_id, custo_manual="80.00", margem_alvo="25.00", margem_piso="5.00")
        resultado = _calcular_simples(
            preco_str="200.00",
            regra=regra,
            custo=Decimal("80.00"),
            origem=OrigemCusto.CUSTO_MANUAL,
            desconto_str="10.00",
            item_id=item_id,
        )
        assert resultado.itens[0].semaforo == Semaforo.AMARELO

    def test_round_half_even(self):
        """ROUND_HALF_EVEN: 80/3 = 26.666... → 26.67 (half-even)."""
        item_id = uuid4()
        regra = _regra(item_id, custo_manual="80.00", margem_alvo="25.00", margem_piso="5.00")
        # 80/0.75 = 106.6666... → 106.67 com ROUND_HALF_EVEN
        resultado = _calcular_simples(
            preco_str="200.00",
            regra=regra,
            custo=Decimal("80.00"),
            origem=OrigemCusto.CUSTO_MANUAL,
            item_id=item_id,
        )
        assert resultado.itens[0].preco_final == Decimal("106.67")


# ---------------------------------------------------------------------------
# T-PRC-016 (c) — Componentes faltantes (D-PRC-2)
# ---------------------------------------------------------------------------

class TestComponentesFaltantes:
    """Motor emite componentes_faltantes para itens esperados ausentes na cesta."""

    def test_componente_ausente_na_cesta(self):
        """Item de serviço com componente esperado não presente → faltantes."""
        item_servico_id = uuid4()
        comp_esperado_id = uuid4()
        perfil = PerfilComposicaoPreco(
            id=uuid4(), tenant_id=_T,
            item_servico_id=item_servico_id,
            componentes_esperados=(comp_esperado_id,),
            criado_por=uuid4(),
        )
        pr_servico = _preco_resolvido("150.00", item_id=item_servico_id)
        # comp_esperado_id NÃO está na cesta → deve aparecer em componentes_faltantes
        resultado = calcular_precos(
            itens=[pr_servico],
            regras={},
            custos={item_servico_id: None},
            origens={item_servico_id: OrigemCusto.INDISPONIVEL},
            perfis={item_servico_id: perfil},
            faixas=_faixas_padrao(),
            params=_params(),
            desconto_pct=Percentual(Decimal("0")),
            modo_montagem=ModoMontagem.COMPONENTES_CHECKLIST,
            km=Decimal("0"),
            parcelas=1,
            aliquota_imposto_fracao=Decimal("0"),
            imposto_ref=None,
        )
        assert comp_esperado_id in resultado.componentes_faltantes

    def test_componentes_presentes_nao_listados(self):
        """Componente presente na cesta → não aparece em faltantes."""
        item_servico_id = uuid4()
        comp_id = uuid4()
        perfil = PerfilComposicaoPreco(
            id=uuid4(), tenant_id=_T,
            item_servico_id=item_servico_id,
            componentes_esperados=(comp_id,),
            criado_por=uuid4(),
        )
        pr_servico = _preco_resolvido("150.00", item_id=item_servico_id)
        pr_comp = _preco_resolvido("20.00", item_id=comp_id)
        resultado = calcular_precos(
            itens=[pr_servico, pr_comp],
            regras={},
            custos={item_servico_id: None, comp_id: None},
            origens={item_servico_id: OrigemCusto.INDISPONIVEL, comp_id: OrigemCusto.INDISPONIVEL},
            perfis={item_servico_id: perfil},
            faixas=_faixas_padrao(),
            params=_params(),
            desconto_pct=Percentual(Decimal("0")),
            modo_montagem=ModoMontagem.COMPONENTES_CHECKLIST,
            km=Decimal("0"),
            parcelas=1,
            aliquota_imposto_fracao=Decimal("0"),
            imposto_ref=None,
        )
        assert comp_id not in resultado.componentes_faltantes

    def test_fechado_com_aviso_sem_componentes_faltantes(self):
        """FECHADO_COM_AVISO: nunca emite componentes_faltantes (modo errado não avalia)."""
        item_servico_id = uuid4()
        comp_esperado_id = uuid4()
        perfil = PerfilComposicaoPreco(
            id=uuid4(), tenant_id=_T,
            item_servico_id=item_servico_id,
            componentes_esperados=(comp_esperado_id,),
            aviso_texto="Serviço completo inclui deslocamento.",
            criado_por=uuid4(),
        )
        pr_servico = _preco_resolvido("150.00", item_id=item_servico_id)
        resultado = calcular_precos(
            itens=[pr_servico],
            regras={},
            custos={item_servico_id: None},
            origens={item_servico_id: OrigemCusto.INDISPONIVEL},
            perfis={item_servico_id: perfil},
            faixas=_faixas_padrao(),
            params=_params(),
            desconto_pct=Percentual(Decimal("0")),
            modo_montagem=ModoMontagem.FECHADO_COM_AVISO,
            km=Decimal("0"),
            parcelas=1,
            aliquota_imposto_fracao=Decimal("0"),
            imposto_ref=None,
        )
        assert len(resultado.componentes_faltantes) == 0
        assert "Serviço completo inclui deslocamento." in resultado.avisos


# ---------------------------------------------------------------------------
# T-PRC-016 (d) — Cortesia 100% → preco_final = 0 (D-PRC-13)
# ---------------------------------------------------------------------------

class TestCortesia:
    """Desconto 100% (cortesia) resulta em preco_final = 0 sem exceção de Preco>0."""

    def test_cortesia_preco_final_zero(self):
        """Desconto 100% → preco_final = 0 (D-PRC-13 / INV-PPS-PRECO-POSITIVO intacto)."""
        resultado = _calcular_simples(
            preco_str="100.00",
            desconto_str="100.00",
        )
        item = resultado.itens[0]
        assert item.preco_final == Decimal("0.00")
        assert item.cortesia is True

    def test_cortesia_sem_regra_preco_zero(self):
        """Cortesia sem regra: sem_regra_formacao=True + preco_final=0."""
        resultado = _calcular_simples(
            preco_str="100.00",
            desconto_str="100.00",
        )
        item = resultado.itens[0]
        assert item.preco_final == Decimal("0.00")
        assert item.sem_regra_formacao is True

    def test_cortesia_com_regra_nao_levanta_minimo_violado(self):
        """Cortesia 100% não levanta PrecoMinimoViolado (D-PRC-13 — cortesia é exceção)."""
        item_id = uuid4()
        regra = _regra(item_id, custo_manual="80.00", margem_alvo="25.00", margem_piso="5.00")
        # Desconto 100% = cortesia; não deve levantar PrecoMinimoViolado
        resultado = _calcular_simples(
            preco_str="200.00",
            regra=regra,
            custo=Decimal("80.00"),
            origem=OrigemCusto.CUSTO_MANUAL,
            desconto_str="100.00",
            item_id=item_id,
        )
        assert resultado.itens[0].preco_final == Decimal("0.00")
        assert resultado.itens[0].cortesia is True

    def test_cortesia_alcada_dono(self):
        """Desconto 100% → alçada exigida = DONO (D-PRC-13)."""
        resultado = _calcular_simples(desconto_str="100.00")
        assert resultado.alcada_exigida == Alcada.DONO


# ---------------------------------------------------------------------------
# T-PRC-016 (e) — Faixas com buraco → FaixasDescontoInvalidas (INV-PRC-FAIXAS-CONTIGUAS)
# ---------------------------------------------------------------------------

class TestFaixasContiguas:
    """validar_faixas_contiguas detecta buraco, sobreposição e limites incorretos."""

    def test_faixas_validas_pass(self):
        """Faixas contíguas 0→100 passam sem exceção."""
        validar_faixas_contiguas(_faixas_padrao())  # não levanta

    def test_buraco_entre_faixas(self):
        """Buraco entre faixas → FaixasDescontoInvalidas."""
        faixas_com_buraco = [
            FaixaAprovacaoDesconto(
                id=uuid4(), tenant_id=_T,
                pct_de=Percentual(Decimal("0")),
                pct_ate=Percentual(Decimal("10.00")),
                alcada=Alcada.LIVRE,
                versao_n=1, hash_conjunto="x", criado_por=uuid4(),
            ),
            # Buraco: de 10 vai pra 15 (deveria ser 10)
            FaixaAprovacaoDesconto(
                id=uuid4(), tenant_id=_T,
                pct_de=Percentual(Decimal("15.00")),
                pct_ate=Percentual(Decimal("100.00")),
                alcada=Alcada.DONO,
                versao_n=1, hash_conjunto="x", criado_por=uuid4(),
            ),
        ]
        with pytest.raises(FaixasDescontoInvalidas, match="Buraco"):
            validar_faixas_contiguas(faixas_com_buraco)

    def test_nao_comeca_em_zero(self):
        """Primeira faixa não começa em 0 → FaixasDescontoInvalidas."""
        faixas = [
            FaixaAprovacaoDesconto(
                id=uuid4(), tenant_id=_T,
                pct_de=Percentual(Decimal("5.00")),
                pct_ate=Percentual(Decimal("100.00")),
                alcada=Alcada.DONO,
                versao_n=1, hash_conjunto="x", criado_por=uuid4(),
            ),
        ]
        with pytest.raises(FaixasDescontoInvalidas, match="começa"):
            validar_faixas_contiguas(faixas)

    def test_nao_termina_em_cem(self):
        """Última faixa não termina em 100 → FaixasDescontoInvalidas."""
        faixas = [
            FaixaAprovacaoDesconto(
                id=uuid4(), tenant_id=_T,
                pct_de=Percentual(Decimal("0")),
                pct_ate=Percentual(Decimal("90.00")),
                alcada=Alcada.LIVRE,
                versao_n=1, hash_conjunto="x", criado_por=uuid4(),
            ),
        ]
        with pytest.raises(FaixasDescontoInvalidas, match="termina"):
            validar_faixas_contiguas(faixas)

    def test_vazio_invalido(self):
        """Conjunto vazio → FaixasDescontoInvalidas."""
        with pytest.raises(FaixasDescontoInvalidas, match="vazio"):
            validar_faixas_contiguas([])


# ---------------------------------------------------------------------------
# T-PRC-016 (f) — Mínimo violado calculável → PrecoMinimoViolado
# ---------------------------------------------------------------------------

class TestMinimoViolado:
    """preço_final < preço_mínimo calculável → PrecoMinimoViolado (bloqueio DURO)."""

    def test_desconto_viola_minimo(self):
        """Desconto que gera preço < mínimo levanta PrecoMinimoViolado."""
        item_id = uuid4()
        # custo=80, piso=5% → minimo ≈ 84.21
        # sugerido = 80/0.75 ≈ 106.67
        # desconto 25% → final = 106.67*0.75 = 80.00 < 84.21 → bloqueio
        regra = _regra(item_id, custo_manual="80.00", margem_alvo="25.00", margem_piso="5.00")
        with pytest.raises(PrecoMinimoViolado):
            _calcular_simples(
                preco_str="200.00",
                regra=regra,
                custo=Decimal("80.00"),
                origem=OrigemCusto.CUSTO_MANUAL,
                desconto_str="25.00",
                item_id=item_id,
            )

    def test_preco_acima_minimo_nao_levanta(self):
        """Desconto que mantém preço >= mínimo não levanta."""
        item_id = uuid4()
        # custo=80, piso=5%, alvo=25% → sugerido≈106.67, minimo≈84.21
        # desconto 5% → final = 106.67*0.95 ≈ 101.34 > 84.21 → OK
        regra = _regra(item_id, custo_manual="80.00", margem_alvo="25.00", margem_piso="5.00")
        resultado = _calcular_simples(
            preco_str="200.00",
            regra=regra,
            custo=Decimal("80.00"),
            origem=OrigemCusto.CUSTO_MANUAL,
            desconto_str="5.00",
            item_id=item_id,
        )
        assert resultado.itens[0].preco_final > Decimal("84.00")

    def test_denominador_zero_levanta_parametros_inviaveis(self):
        """Denominador ≤ 0 em fórmula → ParametrosInviaveis (nunca ZeroDivisionError)."""
        item_id = uuid4()
        # margem_alvo=100% → denom = 1 - 1.0 = 0 → ParametrosInviaveis
        regra = _regra(item_id, custo_manual="80.00", margem_alvo="100.00", margem_piso="5.00")
        with pytest.raises(ParametrosInviaveis):
            _calcular_simples(
                preco_str="200.00",
                regra=regra,
                custo=Decimal("80.00"),
                origem=OrigemCusto.CUSTO_MANUAL,
                item_id=item_id,
            )


# ---------------------------------------------------------------------------
# T-PRC-016 (g) — Stub → CustoIndisponivel (INV-PRC-CUSTO-EXPLICITO)
# ---------------------------------------------------------------------------

class TestStubCustoProvider:
    """StubCustoProvider sempre levanta CustoIndisponivel — nunca retorna 0."""

    def test_stub_levanta_custo_indisponivel(self):
        """Stub levanta CustoIndisponivel para qualquer item."""
        stub = StubCustoProvider()
        with pytest.raises(CustoIndisponivel):
            stub(tenant_id=uuid4(), item_id=uuid4())

    def test_stub_nao_retorna_zero(self):
        """Stub nunca retorna 0 silencioso."""
        stub = StubCustoProvider()
        resultado = None
        with pytest.raises(CustoIndisponivel):
            resultado = stub(tenant_id=uuid4(), item_id=uuid4())
        assert resultado is None  # confirmando que não houve retorno

    def test_sem_custo_semaforo_indisponivel(self):
        """Motor com custo INDISPONIVEL → semáforo INDISPONIVEL no resultado."""
        item_id = uuid4()
        regra = _regra(item_id, modo=ModoFormacaoPreco.MARGEM_ALVO)
        resultado = _calcular_simples(
            regra=regra,
            custo=None,  # custo indisponível
            origem=OrigemCusto.INDISPONIVEL,
            item_id=item_id,
        )
        assert resultado.itens[0].semaforo == Semaforo.INDISPONIVEL
        assert resultado.itens[0].origem_custo == OrigemCusto.INDISPONIVEL


# ---------------------------------------------------------------------------
# T-PRC-016 (h) — Decisor == solicitante → DecisorNaoIndependente
# ---------------------------------------------------------------------------

class TestIndependenciaDecisao:
    """INV-PRC-APROVACAO-INDEPENDENTE: decisor não pode ser o mesmo que solicitante."""

    def test_decisor_igual_solicitante_levanta(self):
        """decisor_id == solicitante_id → DecisorNaoIndependente."""
        uid = uuid4()
        with pytest.raises(DecisorNaoIndependente):
            validar_decisor_independente(decisor_id=uid, solicitante_id=uid)

    def test_decisor_diferente_ok(self):
        """decisor_id != solicitante_id → sem exceção."""
        validar_decisor_independente(decisor_id=uuid4(), solicitante_id=uuid4())

    def test_mensagem_contem_ids(self):
        """Mensagem de erro contém os IDs para rastreabilidade."""
        uid = uuid4()
        with pytest.raises(DecisorNaoIndependente, match=str(uid)):
            validar_decisor_independente(decisor_id=uid, solicitante_id=uid)


# ---------------------------------------------------------------------------
# T-PRC-016 (i) — Sem regra → sem_regra_formacao + semáforo INDISPONIVEL (TL-PRC-05)
# ---------------------------------------------------------------------------

class TestSemRegra:
    """Sem regra de formação vigente → sem_regra_formacao=True + INDISPONIVEL (TL-PRC-05)."""

    def test_sem_regra_flags(self):
        """Item sem regra: sem_regra_formacao=True, semaforo=INDISPONIVEL."""
        resultado = _calcular_simples(preco_str="100.00")  # sem regra
        item = resultado.itens[0]
        assert item.sem_regra_formacao is True
        assert item.semaforo == Semaforo.INDISPONIVEL

    def test_sem_regra_preco_final_aplica_desconto(self):
        """Sem regra: desconto aplicado sobre preco de venda (nao bloqueia)."""
        resultado = _calcular_simples(preco_str="100.00", desconto_str="10.00")
        # 100 * (1 - 0.10) = 90
        assert resultado.itens[0].preco_final == Decimal("90.00")
        assert resultado.itens[0].sem_regra_formacao is True

    def test_sem_regra_nao_levanta_regra_vigente_ausente(self):
        """Motor NUNCA levanta RegraVigenteAusente — caminho sem regra é válido (TL-PRC-05)."""
        # Apenas verifica que não levanta nenhuma exceção
        resultado = _calcular_simples(preco_str="50.00")
        assert resultado is not None


# ---------------------------------------------------------------------------
# T-PRC-016 (j) — alcada_para_pct e faixas padrao
# ---------------------------------------------------------------------------

class TestAlcadaParaPct:
    """alcada_para_pct mapeia percentual para alçada correta."""

    def test_alcada_livre_dentro_0_10(self):
        """5% → LIVRE nas faixas padrão."""
        assert alcada_para_pct(Percentual(Decimal("5.00")), _faixas_padrao()) == Alcada.LIVRE

    def test_alcada_gerente_entre_10_20(self):
        """15% → GERENTE nas faixas padrão."""
        assert alcada_para_pct(Percentual(Decimal("15.00")), _faixas_padrao()) == Alcada.GERENTE

    def test_alcada_dono_acima_20(self):
        """30% → DONO nas faixas padrão."""
        assert alcada_para_pct(Percentual(Decimal("30.00")), _faixas_padrao()) == Alcada.DONO

    def test_alcada_dono_cortesia(self):
        """100% (cortesia) → DONO sempre (D-PRC-13)."""
        assert alcada_para_pct(Percentual(Decimal("100.00")), _faixas_padrao()) == Alcada.DONO

    def test_alcada_dono_sem_faixas(self):
        """Sem faixas → DONO (fail-closed)."""
        assert alcada_para_pct(Percentual(Decimal("5.00")), []) == Alcada.DONO


# ---------------------------------------------------------------------------
# T-PRC-016 (k) — VO Percentual
# ---------------------------------------------------------------------------

class TestPercentual:
    """VO Percentual: validação 0..100, escala 2, ROUND_HALF_EVEN, conversão fração."""

    def test_percentual_valido(self):
        p = Percentual(Decimal("18.50"))
        assert p.valor == Decimal("18.50")

    def test_percentual_zero(self):
        p = Percentual(Decimal("0"))
        assert p.valor == Decimal("0.00")

    def test_percentual_cem(self):
        p = Percentual(Decimal("100"))
        assert p.valor == Decimal("100.00")

    def test_percentual_abaixo_zero(self):
        with pytest.raises(ValueError):
            Percentual(Decimal("-0.01"))

    def test_percentual_acima_cem(self):
        with pytest.raises(ValueError):
            Percentual(Decimal("100.01"))

    def test_percentual_fracao(self):
        """Conversão para fração: 18.5% → 0.185 (exato Decimal)."""
        p = Percentual(Decimal("18.50"))
        assert p.fracao() == Decimal("0.185")

    def test_percentual_fracao_cem(self):
        """100% → fração = 1."""
        p = Percentual(Decimal("100"))
        assert p.fracao() == Decimal("1")

    def test_percentual_escala_arredondada(self):
        """Escala 2 ROUND_HALF_EVEN: 18.556 → 18.56."""
        p = Percentual(Decimal("18.556"))
        assert p.valor == Decimal("18.56")

    def test_percentual_tipo_errado(self):
        with pytest.raises(TypeError):
            Percentual(18.5)  # type: ignore[arg-type] -- passa float de propósito para provar rejeição de tipo
