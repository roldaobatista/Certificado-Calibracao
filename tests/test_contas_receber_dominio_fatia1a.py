"""Frente contas-receber — Fatia 1a (T-CR-016): domínio puro.

Sem Django, sem PG — NUNCA @pytest.mark.django_db.
Molde: tests/test_fiscal_dominio_fatia1a.py.

Cobre (plan §2 / tasks T-CR-016):
  - Máquina de estados: happy (parametrize) + unhappy (transições proibidas).
  - Juros sobre SALDO com pagamento parcial (R12).
  - Grace por perfil (4 perfis A/B/C/D).
  - Conversão de valor nas bordas ("0.10", "100.005", zero, negativo).
  - Categoria perfil-aware: happy (derivação) + mismatch CALIBRACAO_RBC fora de A.
  - MockPaymentGatewayProvider 4 modos.
  - Protocols `PaymentGatewayProvider` e `TituloRepository` são @runtime_checkable.
  - Entidades frozen: tentar mutar → FrozenInstanceError.
"""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import UTC, date, datetime
from decimal import Decimal
from uuid import UUID, uuid4

import pytest
from src.domain.contas_receber.categoria import (
    categoria_permitida,
    categoria_por_perfil_evento,
)
from src.domain.contas_receber.conversao import valor_decimal_str_para_dinheiro
from src.domain.contas_receber.entities import OverrideBloqueio, Pagamento, Titulo
from src.domain.contas_receber.enums import (
    CategoriaReceita,
    EstadoTitulo,
    MeioCobranca,
    OrigemPagamento,
    OrigemTitulo,
)
from src.domain.contas_receber.erros import (
    CategoriaReceitaExigePerfilA,
    GatewayIndisponivel,
    PerfilIndeterminado,
    TituloComPagamentoParcial,
    TransicaoProibida,
    WebhookHMACInvalido,
)
from src.domain.contas_receber.grace import grace_period_por_perfil
from src.domain.contas_receber.juros import calcular_valor_atualizado
from src.domain.contas_receber.mock_provider import MockPaymentGatewayProvider, ModoMock
from src.domain.contas_receber.portas import PaymentGatewayProvider, TituloRepository
from src.domain.contas_receber.transicoes import pode_cancelar, validar_transicao
from src.domain.contas_receber.value_objects import RegraJurosMulta
from src.domain.shared.value_objects import Dinheiro, ReferenciaPIIAnonimizavel

# ============================================================
# Helpers de fábrica
# ============================================================

_REF_CLIENTE = ReferenciaPIIAnonimizavel(
    uuid_atual_id=uuid4(),
    hash_original="a" * 64,
    key_id="v1",
)

_REGRA_PADRAO = RegraJurosMulta(
    juros_ao_mes_pct=Decimal("1.0"),
    multa_pct=Decimal("2.0"),
)


def _titulo(
    *,
    estado: EstadoTitulo = EstadoTitulo.EMITIDO,
    valor_centavos: int = 10_000,  # R$ 100,00
    data_vencimento: date = date(2026, 6, 1),
    meio: MeioCobranca = MeioCobranca.PIX,
    categoria: CategoriaReceita = CategoriaReceita.CALIBRACAO_NAO_RBC,
    perfil: str = "B",
) -> Titulo:
    return Titulo(
        titulo_id=uuid4(),
        tenant_id=uuid4(),
        cliente_referencia=_REF_CLIENTE,
        valor_original=Dinheiro(valor_centavos),
        data_emissao=date(2026, 5, 1),
        data_vencimento=data_vencimento,
        estado=estado,
        meio=meio,
        categoria_receita=categoria,
        perfil_no_evento=perfil,
        origem=OrigemTitulo.MANUAL,
        revision=1,
        criado_em=datetime(2026, 5, 1, tzinfo=UTC),
    )


def _pagamento(titulo: Titulo, valor_centavos: int) -> Pagamento:
    return Pagamento(
        pagamento_id=uuid4(),
        titulo_id=titulo.titulo_id,
        valor=Dinheiro(valor_centavos),
        data=date(2026, 5, 15),
        origem=OrigemPagamento.MANUAL,
        valor_atualizado_snapshot_em_pagamento=Dinheiro(valor_centavos),
        criado_em=datetime(2026, 5, 15, tzinfo=UTC),
    )


# ============================================================
# T-CR-016 — Enums: str, Enum OK
# ============================================================


def test_enums_sao_str_enum() -> None:
    assert EstadoTitulo.EMITIDO == "emitido"
    assert MeioCobranca.PIX == "pix"
    assert CategoriaReceita.CALIBRACAO_RBC == "CALIBRACAO_RBC"
    assert OrigemTitulo.OS == "os"
    assert OrigemPagamento.WEBHOOK_GATEWAY == "webhook_gateway"


# ============================================================
# T-CR-016 — Entidades frozen: mutar → FrozenInstanceError
# ============================================================


def test_titulo_frozen_levanta_ao_mutar() -> None:
    """frozen=True + slots=True: setattr em campo existente levanta FrozenInstanceError."""
    t = _titulo()
    assert not hasattr(t, "__dict__")  # slots: sem __dict__
    with pytest.raises(FrozenInstanceError):
        # setattr em campo existente de dataclass frozen → FrozenInstanceError
        setattr(t, "estado", EstadoTitulo.PAGO)  # noqa: B010 - setattr intencional prova barreira frozen runtime


def test_pagamento_frozen_levanta_ao_mutar() -> None:
    """Pagamento com frozen+slots: setattr em campo existente levanta FrozenInstanceError."""
    t = _titulo()
    p = _pagamento(t, 5_000)
    assert not hasattr(p, "__dict__")  # slots: sem __dict__
    with pytest.raises(FrozenInstanceError):
        setattr(p, "valor", Dinheiro(9_999))  # noqa: B010 - setattr intencional prova barreira frozen runtime


def test_override_bloqueio_frozen_levanta_ao_mutar() -> None:
    """OverrideBloqueio com frozen+slots: setattr em campo existente levanta FrozenInstanceError."""
    ob = OverrideBloqueio(
        override_id=uuid4(),
        titulo_id=uuid4(),
        cliente_id=uuid4(),
        novo_prazo_max_dias=30,
        justificativa="j" * 100,
        a3_signature_id="ref-wave-a",
        usuario_id=uuid4(),
        perfil_no_evento="A",
        criado_em=datetime(2026, 6, 1, tzinfo=UTC),
    )
    assert not hasattr(ob, "__dict__")  # slots: sem __dict__
    with pytest.raises(FrozenInstanceError):
        setattr(ob, "novo_prazo_max_dias", 91)  # noqa: B010 - setattr intencional prova barreira frozen runtime


# ============================================================
# T-CR-016 — Máquina de estados: happy
# ============================================================


@pytest.mark.parametrize(
    ("de", "para"),
    [
        (EstadoTitulo.EMITIDO, EstadoTitulo.PAGO),
        (EstadoTitulo.EMITIDO, EstadoTitulo.PARCIALMENTE_PAGO),
        (EstadoTitulo.EMITIDO, EstadoTitulo.VENCIDO),
        (EstadoTitulo.EMITIDO, EstadoTitulo.CANCELADO),
        (EstadoTitulo.VENCIDO, EstadoTitulo.PAGO),
        (EstadoTitulo.VENCIDO, EstadoTitulo.PARCIALMENTE_PAGO),
        (EstadoTitulo.VENCIDO, EstadoTitulo.CANCELADO),
        (EstadoTitulo.PARCIALMENTE_PAGO, EstadoTitulo.PAGO),
        (EstadoTitulo.PARCIALMENTE_PAGO, EstadoTitulo.VENCIDO),
        (EstadoTitulo.PARCIALMENTE_PAGO, EstadoTitulo.CANCELADO),
    ],
)
def test_transicoes_validas(de: EstadoTitulo, para: EstadoTitulo) -> None:
    validar_transicao(de, para)  # não levanta


# ============================================================
# T-CR-016 — Máquina de estados: unhappy (transições proibidas)
# ============================================================


@pytest.mark.parametrize(
    ("de", "para"),
    [
        # Terminais não saem
        (EstadoTitulo.PAGO, EstadoTitulo.EMITIDO),
        (EstadoTitulo.PAGO, EstadoTitulo.CANCELADO),
        (EstadoTitulo.CANCELADO, EstadoTitulo.EMITIDO),
        (EstadoTitulo.CANCELADO, EstadoTitulo.PAGO),
        # Retrogressões inválidas
        (EstadoTitulo.VENCIDO, EstadoTitulo.EMITIDO),
        (EstadoTitulo.PARCIALMENTE_PAGO, EstadoTitulo.EMITIDO),
    ],
)
def test_transicoes_proibidas(de: EstadoTitulo, para: EstadoTitulo) -> None:
    with pytest.raises(TransicaoProibida):
        validar_transicao(de, para)


# ============================================================
# T-CR-016 — pode_cancelar
# ============================================================


def test_pode_cancelar_sem_pagamentos_ok() -> None:
    t = _titulo()
    assert pode_cancelar(t, []) is True


def test_pode_cancelar_com_pagamento_levanta() -> None:
    t = _titulo()
    p = _pagamento(t, 3_000)
    with pytest.raises(TituloComPagamentoParcial):
        pode_cancelar(t, [p])


# ============================================================
# T-CR-016 — Juros sobre SALDO com pagamento parcial (R12)
# ============================================================


def test_juros_sem_atraso_devolve_saldo_sem_correcao() -> None:
    """Antes do vencimento: saldo puro, sem juros nem multa."""
    t = _titulo(valor_centavos=10_000, data_vencimento=date(2026, 6, 15))
    resultado = calcular_valor_atualizado(t, [], date(2026, 6, 10), _REGRA_PADRAO)
    assert resultado.centavos == 10_000


def test_juros_no_vencimento_sem_correcao() -> None:
    """No dia do vencimento: sem juros (atraso = 0)."""
    t = _titulo(valor_centavos=10_000, data_vencimento=date(2026, 6, 15))
    resultado = calcular_valor_atualizado(t, [], date(2026, 6, 15), _REGRA_PADRAO)
    assert resultado.centavos == 10_000


def test_juros_apos_vencimento_aplica_multa_e_juros() -> None:
    """D+30: 2% multa + 1% de juros sobre valor total."""
    t = _titulo(valor_centavos=10_000, data_vencimento=date(2026, 6, 1))
    # D+30 = 2026-07-01
    resultado = calcular_valor_atualizado(t, [], date(2026, 7, 1), _REGRA_PADRAO)
    # multa = 10000 * 2% = 200
    # juros = 10000 * 1% * (30/30) = 100
    # total = 10000 + 200 + 100 = 10300
    assert resultado.centavos == 10_300


def test_juros_incide_sobre_saldo_nao_sobre_total() -> None:
    """R12: juros calculado sobre SALDO (valor_original - pagamentos), não sobre valor_original."""
    t = _titulo(valor_centavos=10_000, data_vencimento=date(2026, 6, 1))
    # Pagamento parcial de R$40,00 (4000 centavos)
    p = _pagamento(t, 4_000)
    # D+30: saldo = 6000
    # multa = 6000 * 2% = 120
    # juros = 6000 * 1% * (30/30) = 60
    # total = 6000 + 120 + 60 = 6180
    resultado = calcular_valor_atualizado(t, [p], date(2026, 7, 1), _REGRA_PADRAO)
    assert resultado.centavos == 6_180


def test_juros_saldo_quitado_devolve_zero() -> None:
    """Pagamento integral: saldo zero → retorna Dinheiro(0)."""
    t = _titulo(valor_centavos=10_000, data_vencimento=date(2026, 6, 1))
    p = _pagamento(t, 10_000)
    resultado = calcular_valor_atualizado(t, [p], date(2026, 7, 1), _REGRA_PADRAO)
    assert resultado.centavos == 0


def test_juros_d1_aplica_multa_e_juros_proporcional() -> None:
    """D+1: multa full (2%) + juros proporcional de 1 dia."""
    t = _titulo(valor_centavos=10_000, data_vencimento=date(2026, 6, 1))
    resultado = calcular_valor_atualizado(t, [], date(2026, 6, 2), _REGRA_PADRAO)
    # multa = 200
    # juros = 10000 * 0.01 * (1/30) = 3.333... → 3 (ROUND_HALF_UP: 3.33 arredonda p/ 3)
    assert resultado.centavos == 10_203


def test_juros_multiplos_pagamentos_parciais() -> None:
    """Múltiplos pagamentos parciais somados antes de calcular o saldo."""
    t = _titulo(valor_centavos=10_000, data_vencimento=date(2026, 6, 1))
    p1 = _pagamento(t, 2_000)
    p2 = _pagamento(t, 1_000)
    # saldo = 10000 - 2000 - 1000 = 7000
    # D+30: multa = 7000 * 2% = 140, juros = 7000 * 1% = 70
    # total = 7000 + 140 + 70 = 7210
    resultado = calcular_valor_atualizado(t, [p1, p2], date(2026, 7, 1), _REGRA_PADRAO)
    assert resultado.centavos == 7_210


# ============================================================
# T-CR-016 — Grace por perfil (4 perfis)
# ============================================================


@pytest.mark.parametrize(
    ("perfil", "dias_esperados"),
    [
        ("A", 45),
        ("B", 20),
        ("C", 30),
        ("D", 7),
    ],
)
def test_grace_period_por_perfil(perfil: str, dias_esperados: int) -> None:
    assert grace_period_por_perfil(perfil) == dias_esperados


def test_grace_period_perfil_desconhecido_levanta() -> None:
    with pytest.raises(PerfilIndeterminado):
        grace_period_por_perfil("Z")


def test_grace_period_case_insensitive() -> None:
    """Aceita minúsculo (normaliza internamente)."""
    assert grace_period_por_perfil("a") == 45
    assert grace_period_por_perfil("d") == 7


# ============================================================
# T-CR-016 — Conversão de valor nas bordas (R9)
# ============================================================


def test_conversao_valor_simples() -> None:
    assert valor_decimal_str_para_dinheiro("1234.56").centavos == 123_456


def test_conversao_valor_zero_virgula_dez() -> None:
    """ "0.10" → 10 centavos."""
    assert valor_decimal_str_para_dinheiro("0.10").centavos == 10


def test_conversao_valor_arredondamento_half_up() -> None:
    """ "100.005" → 10001 centavos (ROUND_HALF_UP)."""
    assert valor_decimal_str_para_dinheiro("100.005").centavos == 10_001


def test_conversao_valor_zero() -> None:
    """ "0" → 0 centavos."""
    assert valor_decimal_str_para_dinheiro("0").centavos == 0


def test_conversao_valor_zero_duplo() -> None:
    """ "0.00" → 0 centavos."""
    assert valor_decimal_str_para_dinheiro("0.00").centavos == 0


def test_conversao_valor_negativo_levanta() -> None:
    with pytest.raises(ValueError, match="negativo"):
        valor_decimal_str_para_dinheiro("-10.00")


def test_conversao_valor_vazio_levanta() -> None:
    with pytest.raises(ValueError):
        valor_decimal_str_para_dinheiro("")


def test_conversao_valor_invalido_levanta() -> None:
    with pytest.raises(ValueError):
        valor_decimal_str_para_dinheiro("abc")


def test_conversao_preserva_moeda() -> None:
    d = valor_decimal_str_para_dinheiro("10.00", moeda="USD")
    assert d.moeda == "USD"
    assert d.centavos == 1_000


# ============================================================
# T-CR-016 — Categoria perfil-aware: derivação automática
# ============================================================


def test_categoria_por_perfil_a_retorna_rbc() -> None:
    assert categoria_por_perfil_evento("A") is CategoriaReceita.CALIBRACAO_RBC


def test_categoria_por_perfil_b_retorna_nao_rbc() -> None:
    assert categoria_por_perfil_evento("B") is CategoriaReceita.CALIBRACAO_NAO_RBC


def test_categoria_por_perfil_c_retorna_nao_rbc() -> None:
    assert categoria_por_perfil_evento("C") is CategoriaReceita.CALIBRACAO_NAO_RBC


def test_categoria_por_perfil_d_retorna_basica() -> None:
    assert categoria_por_perfil_evento("D") is CategoriaReceita.CALIBRACAO_BASICA


def test_categoria_por_perfil_desconhecido_levanta() -> None:
    with pytest.raises(PerfilIndeterminado):
        categoria_por_perfil_evento("X")


# ============================================================
# T-CR-016 — categoria_permitida: mismatch CALIBRACAO_RBC fora de A
# ============================================================


def test_categoria_rbc_perfil_a_permitida() -> None:
    assert categoria_permitida(CategoriaReceita.CALIBRACAO_RBC, "A") is True


@pytest.mark.parametrize("perfil", ["B", "C", "D"])
def test_categoria_rbc_fora_de_perfil_a_levanta(perfil: str) -> None:
    with pytest.raises(CategoriaReceitaExigePerfilA):
        categoria_permitida(CategoriaReceita.CALIBRACAO_RBC, perfil)


@pytest.mark.parametrize(
    ("categoria", "perfil"),
    [
        (CategoriaReceita.CALIBRACAO_NAO_RBC, "B"),
        (CategoriaReceita.CALIBRACAO_BASICA, "D"),
        (CategoriaReceita.MANUTENCAO_CORRETIVA, "A"),
        (CategoriaReceita.PECA_REVENDA, "D"),
        (CategoriaReceita.OUTROS, "C"),
    ],
)
def test_categorias_nao_rbc_sao_permitidas_em_qualquer_perfil(
    categoria: CategoriaReceita, perfil: str
) -> None:
    assert categoria_permitida(categoria, perfil) is True


# ============================================================
# T-CR-016 — MockPaymentGatewayProvider: 4 modos
# ============================================================


def _ids_cobranca() -> tuple[UUID, date]:
    return uuid4(), date(2026, 7, 1)


def test_mock_always_confirm_cria_cobranca() -> None:
    titulo_id, vencimento = _ids_cobranca()
    mock = MockPaymentGatewayProvider(ModoMock.ALWAYS_CONFIRM)
    result = mock.criar_cobranca(titulo_id, Dinheiro(10_000), vencimento, "pix")
    assert result.gateway_id.startswith("MOCK-")
    assert result.qr_code is not None


def test_mock_always_confirm_boleto_tem_linha_digitavel() -> None:
    titulo_id, vencimento = _ids_cobranca()
    mock = MockPaymentGatewayProvider(ModoMock.ALWAYS_CONFIRM)
    result = mock.criar_cobranca(titulo_id, Dinheiro(10_000), vencimento, "boleto")
    assert result.linha_digitavel is not None


def test_mock_pending_then_confirm_retorna_pending() -> None:
    titulo_id, vencimento = _ids_cobranca()
    mock = MockPaymentGatewayProvider(ModoMock.PENDING_THEN_CONFIRM)
    result = mock.criar_cobranca(titulo_id, Dinheiro(10_000), vencimento, "pix")
    assert "PENDING" in result.gateway_id


def test_mock_always_reject_levanta_gateway_indisponivel() -> None:
    titulo_id, vencimento = _ids_cobranca()
    mock = MockPaymentGatewayProvider(ModoMock.ALWAYS_REJECT)
    with pytest.raises(GatewayIndisponivel):
        mock.criar_cobranca(titulo_id, Dinheiro(10_000), vencimento, "pix")


def test_mock_network_timeout_levanta_gateway_indisponivel() -> None:
    titulo_id, vencimento = _ids_cobranca()
    mock = MockPaymentGatewayProvider(ModoMock.NETWORK_TIMEOUT)
    with pytest.raises(GatewayIndisponivel):
        mock.criar_cobranca(titulo_id, Dinheiro(10_000), vencimento, "pix")


def test_mock_gateway_id_deterministico() -> None:
    """Mesmo payload → mesmo gateway_id."""
    titulo_id = uuid4()
    vencimento = date(2026, 7, 1)
    mock1 = MockPaymentGatewayProvider(ModoMock.ALWAYS_CONFIRM)
    mock2 = MockPaymentGatewayProvider(ModoMock.ALWAYS_CONFIRM)
    r1 = mock1.criar_cobranca(titulo_id, Dinheiro(10_000), vencimento, "pix")
    r2 = mock2.criar_cobranca(titulo_id, Dinheiro(10_000), vencimento, "pix")
    assert r1.gateway_id == r2.gateway_id


def test_mock_webhook_hmac_invalido_signature_vazia() -> None:
    mock = MockPaymentGatewayProvider()
    payload = b"ev1|gw1|1000|2026-07-01"
    with pytest.raises(WebhookHMACInvalido):
        mock.verificar_webhook(payload, "")


def test_mock_webhook_hmac_valido() -> None:
    mock = MockPaymentGatewayProvider()
    payload = b"ev-001|MOCK-abc12345|5000|2026-07-01"
    resultado = mock.verificar_webhook(payload, "qualquer-assinatura-nao-vazia")
    assert resultado.gateway_event_id == "ev-001"
    assert resultado.titulo_gateway_id == "MOCK-abc12345"
    assert resultado.valor_pago.centavos == 5_000
    assert resultado.data_pagamento == date(2026, 7, 1)


def test_mock_criar_recorrencia_always_confirm() -> None:
    titulo_id = uuid4()
    mock = MockPaymentGatewayProvider(ModoMock.ALWAYS_CONFIRM)
    result = mock.criar_recorrencia(titulo_id, "CONV-PIX-001", Dinheiro(5_000), date(2026, 7, 1))
    assert result.convenio_id.startswith("CONV-PIX-001")
    assert result.primeiro_vencimento == date(2026, 7, 1)


def test_mock_criar_recorrencia_reject_levanta() -> None:
    titulo_id = uuid4()
    mock = MockPaymentGatewayProvider(ModoMock.ALWAYS_REJECT)
    with pytest.raises(GatewayIndisponivel):
        mock.criar_recorrencia(titulo_id, "CONV-PIX-001", Dinheiro(5_000), date(2026, 7, 1))


# ============================================================
# T-CR-016 — Protocols @runtime_checkable
# ============================================================


def test_mock_satisfaz_protocol_payment_gateway_provider() -> None:
    """MockPaymentGatewayProvider satisfaz PaymentGatewayProvider estruturalmente."""
    assert isinstance(MockPaymentGatewayProvider(), PaymentGatewayProvider)


def test_objeto_sem_metodos_nao_satisfaz_payment_gateway() -> None:
    class Stub:
        pass

    assert not isinstance(Stub(), PaymentGatewayProvider)


def test_titulo_repository_e_runtime_checkable() -> None:
    """TituloRepository é @runtime_checkable (contrato reconciliado na Fatia 2a)."""

    class DummyRepo:
        def obter_por_id(self, *, tenant_id: UUID, titulo_id: UUID) -> Titulo | None:
            return None

        def salvar_novo_titulo(self, titulo: Titulo) -> None:
            pass

        def atualizar_titulo(self, *, tenant_id: UUID, titulo: Titulo) -> None:
            pass

        def atualizar_titulo_cancelado(
            self, *, tenant_id: UUID, titulo: Titulo, cancelado_em: datetime
        ) -> None:
            pass

        def existe_titulo_ativo_para_os(self, *, tenant_id: UUID, os_id: UUID) -> bool:
            return False

        def listar_por_tenant(
            self,
            *,
            tenant_id: UUID,
            estado: str | None = None,
            cliente_atual_id: UUID | None = None,
        ) -> list[Titulo]:
            return []

        def salvar_pagamento(self, *, tenant_id: UUID, pagamento: Pagamento) -> None:
            pass

        def listar_pagamentos(self, *, tenant_id: UUID, titulo_id: UUID) -> list[Pagamento]:
            return []

        def existe_gateway_event(self, *, tenant_id: UUID, gateway_event_id: str) -> bool:
            return False

    assert isinstance(DummyRepo(), TituloRepository)


# ============================================================
# T-CR-016 — Value Objects (RegraJurosMulta)
# ============================================================


def test_regra_juros_multa_defaults() -> None:
    r = RegraJurosMulta()
    assert r.juros_ao_mes_pct == Decimal("1.0")
    assert r.multa_pct == Decimal("2.0")


def test_regra_juros_multa_negativo_levanta() -> None:
    with pytest.raises(ValueError):
        RegraJurosMulta(juros_ao_mes_pct=Decimal("-0.1"))


def test_dinheiro_reutilizado_de_shared() -> None:
    """Confirma que Dinheiro é o de shared (não foi recriado)."""
    from src.domain.shared.value_objects import Dinheiro as DinheiroShared

    assert Dinheiro is DinheiroShared


def test_referencia_pii_anonimizavel_reutilizada_de_shared() -> None:
    from src.domain.shared.value_objects import (
        ReferenciaPIIAnonimizavel as RefShared,
    )

    assert ReferenciaPIIAnonimizavel is RefShared


# ============================================================
# T-CR-016 — Erros com reason estável
# ============================================================


def test_erros_tem_reason_estavel() -> None:
    from src.domain.contas_receber.erros import (
        ClienteObrigatorio,
        ConvenioPixAusente,
        JustificativaInsuficiente,
        OverrideForaDeAlcada,
    )
    from src.domain.contas_receber.erros import (
        GatewayIndisponivel as GI,
    )
    from src.domain.contas_receber.erros import (
        PerfilIndeterminado as PI,
    )
    from src.domain.contas_receber.erros import (
        TituloComPagamentoParcial as TCP,
    )
    from src.domain.contas_receber.erros import (
        TransicaoProibida as TP,
    )
    from src.domain.contas_receber.erros import (
        WebhookHMACInvalido as WHI,
    )

    assert ClienteObrigatorio.reason == "CLIENTE_OBRIGATORIO"
    assert CategoriaReceitaExigePerfilA.reason == "CATEGORIA_RECEITA_EXIGE_PERFIL_A"
    assert GI.reason == "GATEWAY_INDISPONIVEL"
    assert ConvenioPixAusente.reason == "CONVENIO_PIX_AUSENTE"
    assert TP.reason == "TRANSICAO_PROIBIDA"
    assert TCP.reason == "TITULO_COM_PAGAMENTO_PARCIAL"
    assert WHI.reason == "WEBHOOK_HMAC_INVALIDO"
    assert PI.reason == "PERFIL_INDETERMINADO"
    assert OverrideForaDeAlcada.reason == "OVERRIDE_FORA_DE_ALCADA"
    assert JustificativaInsuficiente.reason == "JUSTIFICATIVA_INSUFICIENTE"


# ============================================================
# T-CR-016 — Titulo: propriedades derivadas
# ============================================================


def test_titulo_e_terminal_pago() -> None:
    t = _titulo(estado=EstadoTitulo.PAGO)
    assert t.e_terminal is True


def test_titulo_e_terminal_cancelado() -> None:
    t = _titulo(estado=EstadoTitulo.CANCELADO)
    assert t.e_terminal is True


def test_titulo_nao_terminal_emitido() -> None:
    t = _titulo(estado=EstadoTitulo.EMITIDO)
    assert t.e_terminal is False


def test_titulo_cobranca_emitida_sem_gateway() -> None:
    t = _titulo()
    assert t.cobranca_emitida is False


def test_titulo_cobranca_emitida_com_gateway() -> None:
    t = Titulo(
        titulo_id=uuid4(),
        tenant_id=uuid4(),
        cliente_referencia=_REF_CLIENTE,
        valor_original=Dinheiro(10_000),
        data_emissao=date(2026, 5, 1),
        data_vencimento=date(2026, 6, 1),
        estado=EstadoTitulo.EMITIDO,
        meio=MeioCobranca.PIX,
        categoria_receita=CategoriaReceita.CALIBRACAO_NAO_RBC,
        perfil_no_evento="B",
        origem=OrigemTitulo.MANUAL,
        revision=1,
        criado_em=datetime(2026, 5, 1, tzinfo=UTC),
        gateway_externo_id="MOCK-abc12345",
    )
    assert t.cobranca_emitida is True
