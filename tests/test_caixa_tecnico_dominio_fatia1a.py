"""Testes do domínio puro caixa_tecnico — Fatia 1a (T-CT-016).

Cobre todos os pontos (a)..(h) do AC de T-CT-016:

(a) Máquina de estados despesa:
    - happy: pendente→validada, pendente→cancelada
    - unhappy: validada→rejeitada → TransicaoInvalida
    - reapresentação: rejeitada→pendente → OK
    - todas as transições proibidas parametrizadas

(b) Máquina de estados adiantamento:
    - happy: solicitado→aprovado→entregue
    - entregue→cancelado → AdiantamentoNaoCancelavel
    - solicitado→recusado → OK
    - todas as proibidas parametrizadas

(c) calcular_saldo com N operações mistas

(d) valor_deslocamento bordas (km=0, tarifa=0)

(e) Despesa sem foto_hash → FotoComprovanteObrigatoria

(f) Periodo(de=d, ate=d) → ValueError (mesma data inválida)

(g) Protocols runtime_checkable

(h) ResultadoSaldo derivação automática de direcao (3 casos)

AC: pytest tests/test_caixa_tecnico_dominio_fatia1a.py --no-cov verde, zero skips.
"""

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime

import pytest
from src.domain.caixa_tecnico.enums import (
    CategoriaDespesa,
    DirecaoPrestacao,
    EstadoAdiantamento,
    EstadoDespesa,
    MeioEntrega,
    TipoDespesa,
)
from src.domain.caixa_tecnico.erros import (
    AdiantamentoNaoCancelavel,
    CaixaTecnicoDesligado,
    FotoComprovanteObrigatoria,
    LoteExcedido,
    PeriodoPrestacaoFechado,
    TransicaoInvalida,
)
from src.domain.caixa_tecnico.portas import (
    ColaboradorCaixaPort,
    ColaboradorReferenciadoPort,
    ConsentimentoGpsPort,
    FotoComprovanteStoragePort,
    OSReferenciaPort,
)
from src.domain.caixa_tecnico.regras.calcular_saldo import calcular_saldo
from src.domain.caixa_tecnico.regras.deslocamento import valor_deslocamento
from src.domain.caixa_tecnico.transicoes_adiantamento import (
    validar_transicao as validar_transicao_adian,
)
from src.domain.caixa_tecnico.transicoes_despesa import (
    validar_transicao as validar_transicao_despesa,
)
from src.domain.caixa_tecnico.value_objects import Coordenada, Periodo, ResultadoSaldo
from src.domain.shared.value_objects import Dinheiro, ReferenciaPIIAnonimizavel

# ---------------------------------------------------------------------------
# Helpers de fixture
# ---------------------------------------------------------------------------

_TENANT = uuid.uuid4()
_TECNICO = uuid.uuid4()


def _ref_pii() -> ReferenciaPIIAnonimizavel:
    return ReferenciaPIIAnonimizavel(
        uuid_atual_id=_TECNICO,
        hash_original="a" * 64,
        key_id="v1",
    )


def _make_despesa(
    estado: EstadoDespesa = EstadoDespesa.PENDENTE,
    foto_hash: str | None = "hash_valido_abc123",
    valor_centavos: int = 100_00,
) -> object:
    """Cria stub mínimo de Despesa para testes de regras puras."""
    from src.domain.caixa_tecnico.entities import Despesa

    return Despesa(
        despesa_id=uuid.uuid4(),
        tenant_id=_TENANT,
        caixa_id=uuid.uuid4(),
        tecnico_referencia=_ref_pii(),
        categoria=CategoriaDespesa.ALIMENTACAO,
        tipo=TipoDespesa.NORMAL,
        valor=Dinheiro(valor_centavos),
        estado=estado,
        foto_hash=foto_hash or "hash_placeholder",  # __post_init__ já validou
        foto_url="http://storage/foto.jpg",
        data=date.today(),
        criado_em=datetime.now(UTC),
        revision=1,
    )


def _make_adiantamento(
    estado: EstadoAdiantamento = EstadoAdiantamento.SOLICITADO,
    valor_centavos: int = 500_00,
) -> object:
    """Cria stub mínimo de Adiantamento para testes de regras puras."""
    from src.domain.caixa_tecnico.entities import Adiantamento

    return Adiantamento(
        adiantamento_id=uuid.uuid4(),
        tenant_id=_TENANT,
        caixa_id=uuid.uuid4(),
        tecnico_referencia=_ref_pii(),
        valor=Dinheiro(valor_centavos),
        estado=estado,
        meio=MeioEntrega.PIX,
        solicitado_em=datetime.now(UTC),
        criado_em=datetime.now(UTC),
        revision=1,
    )


# ===========================================================================
# (a) Máquina de estados da DESPESA
# ===========================================================================


class TestMaquinaEstadosDespesa:
    """(a) Máquina de estados despesa — happy, unhappy, reapresentação e parametrizado."""

    def test_pendente_para_validada_ok(self) -> None:
        """Happy: pendente → validada é transição válida."""
        validar_transicao_despesa(EstadoDespesa.PENDENTE, EstadoDespesa.VALIDADA)

    def test_pendente_para_rejeitada_ok(self) -> None:
        """Happy: pendente → rejeitada é transição válida."""
        validar_transicao_despesa(EstadoDespesa.PENDENTE, EstadoDespesa.REJEITADA)

    def test_pendente_para_cancelada_ok(self) -> None:
        """Happy: pendente → cancelada é transição válida."""
        validar_transicao_despesa(EstadoDespesa.PENDENTE, EstadoDespesa.CANCELADA)

    def test_reapresentacao_rejeitada_para_pendente_ok(self) -> None:
        """Reapresentação (US-CT-007): rejeitada → pendente é transição válida (R3).

        Trigger PG NÃO dispara nessa transição — teste explícito obrigatório (TL-CT-05).
        """
        validar_transicao_despesa(EstadoDespesa.REJEITADA, EstadoDespesa.PENDENTE)

    def test_validada_para_rejeitada_levanta_transicao_invalida(self) -> None:
        """Unhappy: validada → rejeitada é proibida (WORM terminal)."""
        with pytest.raises(TransicaoInvalida):
            validar_transicao_despesa(EstadoDespesa.VALIDADA, EstadoDespesa.REJEITADA)

    def test_validada_para_pendente_levanta_transicao_invalida(self) -> None:
        """Unhappy: validada → pendente é proibida (WORM terminal)."""
        with pytest.raises(TransicaoInvalida):
            validar_transicao_despesa(EstadoDespesa.VALIDADA, EstadoDespesa.PENDENTE)

    def test_cancelada_para_pendente_levanta_transicao_invalida(self) -> None:
        """Unhappy: cancelada → pendente é proibida (terminal)."""
        with pytest.raises(TransicaoInvalida):
            validar_transicao_despesa(EstadoDespesa.CANCELADA, EstadoDespesa.PENDENTE)

    @pytest.mark.parametrize(
        ("de", "para"),
        [
            # Saída de terminais
            (EstadoDespesa.VALIDADA, EstadoDespesa.PENDENTE),
            (EstadoDespesa.VALIDADA, EstadoDespesa.REJEITADA),
            (EstadoDespesa.VALIDADA, EstadoDespesa.CANCELADA),
            (EstadoDespesa.CANCELADA, EstadoDespesa.PENDENTE),
            (EstadoDespesa.CANCELADA, EstadoDespesa.VALIDADA),
            (EstadoDespesa.CANCELADA, EstadoDespesa.REJEITADA),
            # Transições não mapeadas
            (EstadoDespesa.REJEITADA, EstadoDespesa.VALIDADA),
            (EstadoDespesa.REJEITADA, EstadoDespesa.CANCELADA),
        ],
    )
    def test_transicoes_proibidas_parametrizadas(
        self,
        de: EstadoDespesa,
        para: EstadoDespesa,
    ) -> None:
        """Parametrizado: todas as transições proibidas levantam TransicaoInvalida."""
        with pytest.raises(TransicaoInvalida):
            validar_transicao_despesa(de, para)


# ===========================================================================
# (b) Máquina de estados do ADIANTAMENTO
# ===========================================================================


class TestMaquinaEstadosAdiantamento:
    """(b) Máquina de estados adiantamento — happy, entregue imutável e parametrizado."""

    def test_solicitado_para_aprovado_ok(self) -> None:
        """Happy: solicitado → aprovado."""
        validar_transicao_adian(EstadoAdiantamento.SOLICITADO, EstadoAdiantamento.APROVADO)

    def test_aprovado_para_entregue_ok(self) -> None:
        """Happy: aprovado → entregue."""
        validar_transicao_adian(EstadoAdiantamento.APROVADO, EstadoAdiantamento.ENTREGUE)

    def test_solicitado_para_recusado_ok(self) -> None:
        """Happy: solicitado → recusado."""
        validar_transicao_adian(EstadoAdiantamento.SOLICITADO, EstadoAdiantamento.RECUSADO)

    def test_solicitado_para_cancelado_ok(self) -> None:
        """Happy: solicitado → cancelado."""
        validar_transicao_adian(EstadoAdiantamento.SOLICITADO, EstadoAdiantamento.CANCELADO)

    def test_entregue_para_cancelado_levanta_nao_cancelavel(self) -> None:
        """Unhappy: entregue → cancelado levanta AdiantamentoNaoCancelavel (422).

        AC T-CT-014: NÃO levanta TransicaoInvalida genérica — é erro semântico específico.
        """
        with pytest.raises(AdiantamentoNaoCancelavel):
            validar_transicao_adian(EstadoAdiantamento.ENTREGUE, EstadoAdiantamento.CANCELADO)

    def test_entregue_para_qualquer_estado_levanta_nao_cancelavel(self) -> None:
        """Entregue é terminal especial: qualquer saída → AdiantamentoNaoCancelavel."""
        for destino in EstadoAdiantamento:
            if destino != EstadoAdiantamento.ENTREGUE:
                with pytest.raises(AdiantamentoNaoCancelavel):
                    validar_transicao_adian(EstadoAdiantamento.ENTREGUE, destino)

    def test_nao_cancelavel_e_subclasse_correta(self) -> None:
        """AdiantamentoNaoCancelavel tem http_status=422."""
        err = AdiantamentoNaoCancelavel("teste")
        assert err.http_status == 422

    @pytest.mark.parametrize(
        ("de", "para"),
        [
            # Saída de terminais recusado/cancelado
            (EstadoAdiantamento.RECUSADO, EstadoAdiantamento.APROVADO),
            (EstadoAdiantamento.RECUSADO, EstadoAdiantamento.SOLICITADO),
            (EstadoAdiantamento.CANCELADO, EstadoAdiantamento.APROVADO),
            (EstadoAdiantamento.CANCELADO, EstadoAdiantamento.SOLICITADO),
            # Transições não mapeadas
            (EstadoAdiantamento.APROVADO, EstadoAdiantamento.RECUSADO),
            (EstadoAdiantamento.APROVADO, EstadoAdiantamento.CANCELADO),
            (EstadoAdiantamento.SOLICITADO, EstadoAdiantamento.ENTREGUE),
        ],
    )
    def test_transicoes_proibidas_parametrizadas(
        self,
        de: EstadoAdiantamento,
        para: EstadoAdiantamento,
    ) -> None:
        """Parametrizado: transições proibidas (exceto de entregue) → TransicaoInvalida."""
        with pytest.raises(TransicaoInvalida):
            validar_transicao_adian(de, para)


# ===========================================================================
# (c) calcular_saldo — N operações mistas
# ===========================================================================


class TestCalcularSaldo:
    """(c) calcular_saldo — consistência com N operações mistas."""

    def test_saldo_ac_basico(self) -> None:
        """AC T-CT-013: adiant_500 + despesa_300 → saldo=200, direcao=tenant_deve."""
        adian = _make_adiantamento(EstadoAdiantamento.ENTREGUE, valor_centavos=500_00)
        despesa = _make_despesa(EstadoDespesa.VALIDADA, valor_centavos=300_00)

        resultado = calcular_saldo([adian], [despesa])

        assert resultado.saldo_final.centavos == 200_00
        assert resultado.direcao == DirecaoPrestacao.TENANT_DEVE

    def test_saldo_tecnico_deve(self) -> None:
        """Despesas > adiantamentos → tecnico_deve."""
        adian = _make_adiantamento(EstadoAdiantamento.ENTREGUE, valor_centavos=100_00)
        despesas = [
            _make_despesa(EstadoDespesa.VALIDADA, valor_centavos=80_00),
            _make_despesa(EstadoDespesa.VALIDADA, valor_centavos=70_00),
        ]

        resultado = calcular_saldo([adian], despesas)

        assert resultado.saldo_final.centavos == -50_00
        assert resultado.direcao == DirecaoPrestacao.TECNICO_DEVE

    def test_saldo_quitado(self) -> None:
        """Adiantamentos == despesas → quitado."""
        adian = _make_adiantamento(EstadoAdiantamento.ENTREGUE, valor_centavos=200_00)
        despesa = _make_despesa(EstadoDespesa.VALIDADA, valor_centavos=200_00)

        resultado = calcular_saldo([adian], [despesa])

        assert resultado.saldo_final.centavos == 0
        assert resultado.direcao == DirecaoPrestacao.QUITADO

    def test_ignora_adiantamentos_nao_entregues(self) -> None:
        """Adiantamentos solicitados/aprovados/recusados/cancelados NÃO entram no saldo."""
        adians = [
            _make_adiantamento(EstadoAdiantamento.SOLICITADO, valor_centavos=1000_00),
            _make_adiantamento(EstadoAdiantamento.APROVADO, valor_centavos=500_00),
            _make_adiantamento(EstadoAdiantamento.RECUSADO, valor_centavos=300_00),
            _make_adiantamento(EstadoAdiantamento.CANCELADO, valor_centavos=200_00),
            _make_adiantamento(EstadoAdiantamento.ENTREGUE, valor_centavos=150_00),
        ]

        resultado = calcular_saldo(adians, [])

        assert resultado.total_adiantado.centavos == 150_00

    def test_ignora_despesas_nao_validadas(self) -> None:
        """Despesas pendentes/rejeitadas/canceladas NÃO entram no saldo."""
        despesas = [
            _make_despesa(EstadoDespesa.PENDENTE, valor_centavos=500_00),
            _make_despesa(EstadoDespesa.REJEITADA, valor_centavos=300_00),
            _make_despesa(EstadoDespesa.CANCELADA, valor_centavos=200_00),
            _make_despesa(EstadoDespesa.VALIDADA, valor_centavos=100_00),
        ]

        resultado = calcular_saldo([], despesas)

        assert resultado.total_despesas.centavos == 100_00

    def test_listas_vazias(self) -> None:
        """Sem operações → saldo=0, direcao=quitado."""
        resultado = calcular_saldo([], [])

        assert resultado.saldo_final.centavos == 0
        assert resultado.direcao == DirecaoPrestacao.QUITADO

    def test_multiplas_operacoes(self) -> None:
        """N operações mistas: consistência de soma."""
        adians = [
            _make_adiantamento(EstadoAdiantamento.ENTREGUE, valor_centavos=300_00),
            _make_adiantamento(EstadoAdiantamento.ENTREGUE, valor_centavos=200_00),
            _make_adiantamento(EstadoAdiantamento.SOLICITADO, valor_centavos=999_00),  # ignorado
        ]
        despesas = [
            _make_despesa(EstadoDespesa.VALIDADA, valor_centavos=100_00),
            _make_despesa(EstadoDespesa.VALIDADA, valor_centavos=150_00),
            _make_despesa(EstadoDespesa.PENDENTE, valor_centavos=999_00),  # ignorada
        ]

        resultado = calcular_saldo(adians, despesas)

        # total_adiantado = 300+200 = 500
        # total_despesas  = 100+150 = 250
        # saldo_final     = 500-250 = 250 → tenant_deve
        assert resultado.total_adiantado.centavos == 500_00
        assert resultado.total_despesas.centavos == 250_00
        assert resultado.saldo_final.centavos == 250_00
        assert resultado.direcao == DirecaoPrestacao.TENANT_DEVE


# ===========================================================================
# (d) valor_deslocamento — bordas
# ===========================================================================


class TestValorDeslocamento:
    """(d) valor_deslocamento — AC e bordas."""

    def test_ac_basico(self) -> None:
        """AC T-CT-013: valor_deslocamento(10, Dinheiro(150)) → Dinheiro(1500)."""
        resultado = valor_deslocamento(10, Dinheiro(150))
        assert resultado.centavos == 1500

    def test_km_zero(self) -> None:
        """Borda: km=0 → Dinheiro(0) sem erro."""
        resultado = valor_deslocamento(0, Dinheiro(150))
        assert resultado.centavos == 0

    def test_tarifa_zero(self) -> None:
        """Borda: tarifa=0 → Dinheiro(0) sem erro."""
        resultado = valor_deslocamento(10, Dinheiro(0))
        assert resultado.centavos == 0

    def test_ambos_zero(self) -> None:
        """Borda: km=0 e tarifa=0 → Dinheiro(0)."""
        resultado = valor_deslocamento(0, Dinheiro(0))
        assert resultado.centavos == 0

    def test_km_negativo_levanta_value_error(self) -> None:
        """km negativo é inválido (sem sentido de negócio)."""
        with pytest.raises(ValueError):
            valor_deslocamento(-1, Dinheiro(100))

    def test_resultado_correto_varios_kms(self) -> None:
        """Verificação: 100 km × R$2,50/km (250 centavos) = R$250,00 (25000 centavos)."""
        resultado = valor_deslocamento(100, Dinheiro(250))
        assert resultado.centavos == 25_000


# ===========================================================================
# (e) Despesa sem foto_hash → FotoComprovanteObrigatoria
# ===========================================================================


class TestDespesaSemFoto:
    """(e) Despesa.__post_init__ valida foto_hash obrigatório (INV-CT-FOTO-001)."""

    def test_foto_hash_none_levanta_erro(self) -> None:
        """foto_hash=None → FotoComprovanteObrigatoria (412)."""
        from src.domain.caixa_tecnico.entities import Despesa

        with pytest.raises(FotoComprovanteObrigatoria):
            Despesa(
                despesa_id=uuid.uuid4(),
                tenant_id=_TENANT,
                caixa_id=uuid.uuid4(),
                tecnico_referencia=_ref_pii(),
                categoria=CategoriaDespesa.ALIMENTACAO,
                tipo=TipoDespesa.NORMAL,
                valor=Dinheiro(100_00),
                estado=EstadoDespesa.PENDENTE,
                foto_hash=None,  # type: ignore[arg-type]
                foto_url="http://storage/foto.jpg",
                data=date.today(),
                criado_em=datetime.now(UTC),
                revision=1,
            )

    def test_foto_hash_string_vazia_levanta_erro(self) -> None:
        """foto_hash='' → FotoComprovanteObrigatoria (412)."""
        from src.domain.caixa_tecnico.entities import Despesa

        with pytest.raises(FotoComprovanteObrigatoria):
            Despesa(
                despesa_id=uuid.uuid4(),
                tenant_id=_TENANT,
                caixa_id=uuid.uuid4(),
                tecnico_referencia=_ref_pii(),
                categoria=CategoriaDespesa.ALIMENTACAO,
                tipo=TipoDespesa.NORMAL,
                valor=Dinheiro(100_00),
                estado=EstadoDespesa.PENDENTE,
                foto_hash="",  # vazio
                foto_url="http://storage/foto.jpg",
                data=date.today(),
                criado_em=datetime.now(UTC),
                revision=1,
            )

    def test_foto_hash_valido_cria_despesa_ok(self) -> None:
        """Com foto_hash preenchido, Despesa é criada sem erro."""
        despesa = _make_despesa(foto_hash="abc123hash_valido")
        assert despesa.foto_hash == "abc123hash_valido"

    def test_erro_tem_http_status_412(self) -> None:
        """FotoComprovanteObrigatoria.http_status == 412."""
        err = FotoComprovanteObrigatoria("sem foto")
        assert err.http_status == 412


# ===========================================================================
# (f) Periodo — validação de datas
# ===========================================================================


class TestPeriodo:
    """(f) Periodo valida de < ate."""

    def test_mesma_data_levanta_value_error(self) -> None:
        """Periodo(de=d, ate=d) → ValueError (intervalo vazio)."""
        d = date(2026, 6, 1)
        with pytest.raises(ValueError):
            Periodo(de=d, ate=d)

    def test_de_maior_que_ate_levanta_value_error(self) -> None:
        """Periodo invertido → ValueError."""
        with pytest.raises(ValueError):
            Periodo(de=date(2026, 6, 30), ate=date(2026, 6, 1))

    def test_periodo_valido_ok(self) -> None:
        """Periodo com de < ate é criado sem erro."""
        p = Periodo(de=date(2026, 6, 1), ate=date(2026, 6, 30))
        assert p.de < p.ate

    def test_contem_data_dentro(self) -> None:
        """Periodo.contem() retorna True para data dentro do intervalo."""
        p = Periodo(de=date(2026, 6, 1), ate=date(2026, 6, 30))
        assert p.contem(date(2026, 6, 15)) is True

    def test_nao_contem_data_fora(self) -> None:
        """Periodo.contem() retorna False para data fora do intervalo."""
        p = Periodo(de=date(2026, 6, 1), ate=date(2026, 6, 30))
        assert p.contem(date(2026, 7, 1)) is False


# ===========================================================================
# (f+) Coordenada — validação de limites geográficos
# ===========================================================================


class TestCoordenada:
    """Coordenada valida limites geográficos."""

    def test_lat_acima_de_90_levanta_value_error(self) -> None:
        with pytest.raises(ValueError):
            Coordenada(lat=91.0, lng=0.0)

    def test_lat_abaixo_de_menos_90_levanta_value_error(self) -> None:
        with pytest.raises(ValueError):
            Coordenada(lat=-91.0, lng=0.0)

    def test_lng_acima_de_180_levanta_value_error(self) -> None:
        with pytest.raises(ValueError):
            Coordenada(lat=0.0, lng=181.0)

    def test_lng_abaixo_de_menos_180_levanta_value_error(self) -> None:
        with pytest.raises(ValueError):
            Coordenada(lat=0.0, lng=-181.0)

    def test_coordenada_valida_ok(self) -> None:
        """Cuiabá/MT — coordenada real válida."""
        c = Coordenada(lat=-15.601411, lng=-56.097892)
        assert c.lat == pytest.approx(-15.601411)

    def test_limites_exatos_validos(self) -> None:
        """Coordenadas nos limites exatos são válidas."""
        Coordenada(lat=90.0, lng=180.0)
        Coordenada(lat=-90.0, lng=-180.0)


# ===========================================================================
# (g) Protocols runtime_checkable
# ===========================================================================


class TestProtocolsRuntimeCheckable:
    """(g) Protocols são @runtime_checkable."""

    def test_foto_storage_port_runtime_checkable(self) -> None:
        """FotoComprovanteStoragePort é verificável em runtime."""

        class FakeFotoStorage:
            def validar_e_processar(self, bytes_foto, mime_type):
                return (b"bytes", "hash")

            def salvar(self, tenant_id, foto_hash, bytes_limpos):
                return "http://url"

        assert isinstance(FakeFotoStorage(), FotoComprovanteStoragePort)

    def test_os_referencia_port_runtime_checkable(self) -> None:
        """OSReferenciaPort é verificável em runtime."""

        class FakeOSRef:
            def existe_os(self, os_id, tenant_id):
                return True

        assert isinstance(FakeOSRef(), OSReferenciaPort)

    def test_consentimento_gps_port_runtime_checkable(self) -> None:
        """ConsentimentoGpsPort é verificável em runtime."""

        class FakeGps:
            def opt_in_vigente(self, tenant_id, colaborador_id, na_data):
                return True

        assert isinstance(FakeGps(), ConsentimentoGpsPort)

    def test_colaborador_caixa_port_runtime_checkable(self) -> None:
        """ColaboradorCaixaPort é verificável em runtime."""

        class FakeColaborador:
            def e_tecnico(self, tenant_id, colaborador_id):
                return True

        assert isinstance(FakeColaborador(), ColaboradorCaixaPort)

    def test_colaborador_referenciado_port_runtime_checkable(self) -> None:
        """ColaboradorReferenciadoPort é verificável em runtime."""

        class FakeRef:
            def esta_referenciado(self, tenant_id, colaborador_id):
                return False

        assert isinstance(FakeRef(), ColaboradorReferenciadoPort)

    def test_objeto_sem_metodo_nao_implementa_protocol(self) -> None:
        """Objeto sem método do Protocol não implementa a porta."""

        class Vazio:
            pass

        assert not isinstance(Vazio(), FotoComprovanteStoragePort)


# ===========================================================================
# (h) ResultadoSaldo — derivação automática de direcao (3 casos)
# ===========================================================================


class TestResultadoSaldo:
    """(h) ResultadoSaldo.calcular() deriva direcao nos 3 casos."""

    def test_saldo_positivo_tenant_deve(self) -> None:
        """Saldo > 0 → tenant_deve (técnico gastou menos que adiantado)."""
        r = ResultadoSaldo.calcular(Dinheiro(500_00), Dinheiro(300_00))
        assert r.saldo_final.centavos == 200_00
        assert r.direcao == DirecaoPrestacao.TENANT_DEVE

    def test_saldo_negativo_tecnico_deve(self) -> None:
        """Saldo < 0 → tecnico_deve (técnico gastou mais que adiantado)."""
        r = ResultadoSaldo.calcular(Dinheiro(100_00), Dinheiro(300_00))
        assert r.saldo_final.centavos == -200_00
        assert r.direcao == DirecaoPrestacao.TECNICO_DEVE

    def test_saldo_zero_quitado(self) -> None:
        """Saldo == 0 → quitado."""
        r = ResultadoSaldo.calcular(Dinheiro(200_00), Dinheiro(200_00))
        assert r.saldo_final.centavos == 0
        assert r.direcao == DirecaoPrestacao.QUITADO

    def test_resultado_saldo_campos_corretos(self) -> None:
        """ResultadoSaldo.calcular() preenche todos os campos corretamente."""
        r = ResultadoSaldo.calcular(Dinheiro(500_00), Dinheiro(300_00))
        assert r.total_adiantado.centavos == 500_00
        assert r.total_despesas.centavos == 300_00
        assert r.saldo_final.centavos == 200_00


# ===========================================================================
# Testes adicionais de erros (http_status corretos)
# ===========================================================================


class TestErrosHttpStatus:
    """Verifica que todos os erros têm http_status correto (T-CT-015)."""

    @pytest.mark.parametrize(
        ("erro_cls", "status_esperado"),
        [
            (FotoComprovanteObrigatoria, 412),
            (AdiantamentoNaoCancelavel, 422),
            (PeriodoPrestacaoFechado, 422),
            (TransicaoInvalida, 422),
            (LoteExcedido, 413),
            (CaixaTecnicoDesligado, 409),
        ],
    )
    def test_http_status_correto(self, erro_cls, status_esperado) -> None:
        """Cada erro de domínio tem o http_status esperado."""
        err = erro_cls("mensagem de teste")
        assert err.http_status == status_esperado

    def test_gps_consentimento_ausente_status_403(self) -> None:
        """GpsConsentimentoAusente.http_status == 403."""
        from src.domain.caixa_tecnico.erros import GpsConsentimentoAusente

        err = GpsConsentimentoAusente("ausente")
        assert err.http_status == 403

    def test_despesa_validada_imutavel_status_409(self) -> None:
        """DespesaValidadaImutavel.http_status == 409."""
        from src.domain.caixa_tecnico.erros import DespesaValidadaImutavel

        err = DespesaValidadaImutavel("imutável")
        assert err.http_status == 409

    def test_foto_duplicada_status_409(self) -> None:
        """FotoDuplicada.http_status == 409."""
        from src.domain.caixa_tecnico.erros import FotoDuplicada

        err = FotoDuplicada("duplicada")
        assert err.http_status == 409


# ===========================================================================
# Testes de enums (T-CT-010 — AC: EstadoDespesa('validada') funciona)
# ===========================================================================


class TestEnums:
    """T-CT-010 AC: enums funcionam via valor string."""

    def test_estado_despesa_por_valor_string(self) -> None:
        assert EstadoDespesa("validada") == EstadoDespesa.VALIDADA

    def test_estado_adiantamento_por_valor_string(self) -> None:
        assert EstadoAdiantamento("entregue") == EstadoAdiantamento.ENTREGUE

    def test_todos_enums_sao_str(self) -> None:
        """Todos os enums são str — serialização JSON nativa."""
        from src.domain.caixa_tecnico.enums import (
            CategoriaDespesa,
            DirecaoPrestacao,
            MeioEntrega,
            TipoDespesa,
        )

        for enum_cls in [
            CategoriaDespesa,
            TipoDespesa,
            EstadoDespesa,
            EstadoAdiantamento,
            MeioEntrega,
            DirecaoPrestacao,
        ]:
            for membro in enum_cls:
                assert isinstance(membro, str), f"{enum_cls.__name__}.{membro} não é str"
