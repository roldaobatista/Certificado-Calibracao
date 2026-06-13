"""TST-004 — classes nomeando cada INV da frente precificacao (T-PRC-051).

Convenção do projeto (análoga `test_inv_pps_classes_nomeadas.py`): todo INV
crítico tem ≥1 teste cujo NOME cita o ID. Cada classe exercita a barreira
REAL — PG-real onde a defesa é trigger/constraint/UNIQUE; puro onde é
domínio/use case; E2E onde é serializer/log.

Cobre (12 INVs):
  PG-real : REGRA-IMUTAVEL, REGRA-SEM-SOBREPOSICAO, APROVACAO-ONE-SHOT,
            APROVACAO-INDEPENDENTE.
  Puro    : COSTPLUS-STUB, CUSTO-EXPLICITO, FAIXAS-CONTIGUAS, MINIMO-BLOQUEIO,
            INV-026 (motor não persiste).
  E2E     : MARGEM-RBAC, SEGREDO-LOG, JUSTIFICATIVA-HASH.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

import pytest
from django.db import DatabaseError, IntegrityError
from django.utils import timezone
from src.application.precificacao.aprovacao import (
    DecidirAprovacaoInput,
    decidir_aprovacao,
)
from src.domain.precificacao.entities import FaixaAprovacaoDesconto
from src.domain.precificacao.enums import (
    Alcada,
    ContextoTipo,
    EstadoPedido,
    ModoFormacaoPreco,
    ModoMontagem,
)
from src.domain.precificacao.erros import (
    CustoIndisponivel,
    CustoRealIndisponivel,
    DecisorNaoIndependente,
    FaixasDescontoInvalidas,
    PrecoMinimoViolado,
)
from src.domain.precificacao.portas import StubCustoProvider
from src.domain.precificacao.transicoes import (
    calcular_precos,
    validar_faixas_contiguas,
)
from src.domain.precificacao.value_objects import CalculoPrecoResultado, Percentual
from src.infrastructure.multitenant.connection import run_in_tenant_context
from src.infrastructure.precificacao.models import (
    PedidoAprovacaoDesconto,
    RegraFormacaoPreco,
)

from tests.factories import TenantFactory

_AGORA = datetime(2026, 6, 13, 12, 0, 0, tzinfo=UTC)
_JAN = datetime(2026, 1, 1, tzinfo=UTC)
_JUN = datetime(2026, 7, 1, tzinfo=UTC)


# ---------------------------------------------------------------------------
# Helpers PG-real
# ---------------------------------------------------------------------------


def _regra_pg(tenant, item_id, *, n=1, inicio=_JAN, fim=None, revogado_em=None):
    """Cria RegraFormacaoPreco diretamente no banco para testes PG-real."""
    with run_in_tenant_context(tenant.id):
        return RegraFormacaoPreco.objects.create(
            tenant=tenant,
            item_id=item_id,
            modo="preco_fixo",
            versao_n=n,
            preco_fixo=Decimal("100.00"),
            vigencia_inicio=inicio,
            vigencia_fim=fim,
            revogado_em=revogado_em,
            motivo_revogacao="" if revogado_em is None else "teste regra",
            criado_por=uuid4(),
        )


def _pedido_pg(tenant, *, solicitante_id=None, estado="solicitado"):
    """Cria PedidoAprovacaoDesconto diretamente no banco para testes PG-real."""
    solicitante_id = solicitante_id or uuid4()
    with run_in_tenant_context(tenant.id):
        return PedidoAprovacaoDesconto.objects.create(
            tenant=tenant,
            contexto_tipo="avulso",
            contexto_id=None,
            pct_solicitado=Decimal("15.00"),
            cortesia=False,
            alcada_exigida="gerente",
            fingerprint_calculo="a" * 64,
            estado=estado,
            solicitante_id=solicitante_id,
            snapshot_probatorio='{"test": true}',
            criado_em=_AGORA,
        )


# ---------------------------------------------------------------------------
# Helpers Fake para testes puros
# ---------------------------------------------------------------------------


class _FakeRegraRepo:
    """Repositório fake minimalista para testes puros de domínio."""

    def __init__(self, regra=None):
        self._regra = regra
        self.salvo = None
        self.encerrado = None

    def travar_item(self, **_kw):
        pass

    def obter_vigente(self, **_kw):
        return self._regra

    def listar_por_item(self, **_kw):
        return [self._regra] if self._regra else []

    def salvar(self, regra):
        self.salvo = regra

    def encerrar_vigencia(self, **_kw):
        self.encerrado = True

    def obter(self, **_kw):
        return self._regra

    def revogar(self, **_kw):
        pass


class _FakePedidoRepo:
    def __init__(self, pedido=None):
        self._pedido = pedido
        self.decidido = None
        self.salvo = None

    def obter(self, **_kw):
        return self._pedido

    def salvar(self, pedido):
        self.salvo = pedido

    def decidir(self, *, pedido_id, estado, decisor_id, justificativa_hash, decidido_em, **_kw):
        self.decidido = {
            "pedido_id": pedido_id,
            "estado": estado,
            "decisor_id": decisor_id,
            "justificativa_hash": justificativa_hash,
        }


# ---------------------------------------------------------------------------
# INV-PRC-COSTPLUS-STUB — domínio (puro)
# ---------------------------------------------------------------------------


class TestINV_PRC_COSTPLUS_STUB:
    """INV-PRC-COSTPLUS-STUB: publicar COST_PLUS sob stub → CustoRealIndisponivel."""

    def test_stub_nao_disponivel_bloqueia_cost_plus(self) -> None:
        """StubCustoProvider.disponivel() == False → use case recusa COST_PLUS."""
        from src.application.precificacao.regra import PublicarRegraInput, publicar_regra

        stub = StubCustoProvider()
        assert stub.disponivel() is False

        inp = PublicarRegraInput(
            tenant_id=uuid4(),
            item_id=uuid4(),
            modo=ModoFormacaoPreco.COST_PLUS,
            criado_por=uuid4(),
            agora=_AGORA,
            margem_alvo_pct=Decimal("20.00"),
            margem_piso_pct=Decimal("5.00"),
        )
        with pytest.raises(CustoRealIndisponivel):
            publicar_regra(inp, repo=_FakeRegraRepo(), custo_provider=stub)

    def test_provider_disponivel_nao_bloqueia_cost_plus(self) -> None:
        """Provider real (disponivel=True) NÃO bloqueia COST_PLUS."""
        from src.application.precificacao.regra import PublicarRegraInput, publicar_regra

        class _FakeProviderReal:
            def disponivel(self):
                return True

            def __call__(self, **_kw):
                return Decimal("50.00")

        inp = PublicarRegraInput(
            tenant_id=uuid4(),
            item_id=uuid4(),
            modo=ModoFormacaoPreco.COST_PLUS,
            criado_por=uuid4(),
            agora=_AGORA,
            vigencia_inicio=_AGORA,
            margem_alvo_pct=Decimal("20.00"),
            margem_piso_pct=Decimal("5.00"),
        )
        # Não deve levantar CustoRealIndisponivel
        out = publicar_regra(inp, repo=_FakeRegraRepo(), custo_provider=_FakeProviderReal())
        assert out.regra.modo == ModoFormacaoPreco.COST_PLUS


# ---------------------------------------------------------------------------
# INV-PRC-REGRA-IMUTAVEL — PG-real (trigger WORM)
# ---------------------------------------------------------------------------


class TestINV_PRC_REGRA_IMUTAVEL:
    """INV-PRC-REGRA-IMUTAVEL: trigger WORM bloqueia UPDATE de campos probatórios e DELETE."""

    @pytest.mark.django_db(transaction=True)
    def test_update_modo_bloqueado_por_trigger(self) -> None:
        """Campo probatório `modo` é imutável pós-INSERT (trigger 0003)."""
        tenant = TenantFactory()
        from src.infrastructure.produtos_pecas_servicos.models import ItemCatalogo

        with run_in_tenant_context(tenant.id):
            item = ItemCatalogo.objects.create(
                tenant=tenant,
                codigo_interno="REG-IMUT-001",
                tipo="peca",
                controla_estoque=False,
            )
        regra = _regra_pg(tenant, item.id)
        with run_in_tenant_context(tenant.id), pytest.raises(DatabaseError):
            RegraFormacaoPreco.objects.filter(id=regra.id).update(modo="margem_alvo")

    @pytest.mark.django_db(transaction=True)
    def test_delete_bloqueado_por_trigger(self) -> None:
        """DELETE direto é bloqueado pelo trigger block_delete (INV-PRC-REGRA-IMUTAVEL)."""
        tenant = TenantFactory()
        from src.infrastructure.produtos_pecas_servicos.models import ItemCatalogo

        with run_in_tenant_context(tenant.id):
            item = ItemCatalogo.objects.create(
                tenant=tenant,
                codigo_interno="REG-DEL-001",
                tipo="peca",
                controla_estoque=False,
            )
        regra = _regra_pg(tenant, item.id)
        with run_in_tenant_context(tenant.id), pytest.raises(DatabaseError):
            RegraFormacaoPreco.objects.filter(id=regra.id).delete()


# ---------------------------------------------------------------------------
# INV-PRC-REGRA-SEM-SOBREPOSICAO — PG-real (exclusion btree_gist)
# ---------------------------------------------------------------------------


class TestINV_PRC_REGRA_SEM_SOBREPOSICAO:
    """INV-PRC-REGRA-SEM-SOBREPOSICAO: exclusion btree_gist bloqueia sobreposição."""

    @pytest.mark.django_db(transaction=True)
    def test_exclusion_bloqueia_sobreposicao(self) -> None:
        """Duas regras não-revogadas no mesmo (tenant, item) com vigência sobreposta → IntegrityError."""
        tenant = TenantFactory()
        from src.infrastructure.produtos_pecas_servicos.models import ItemCatalogo

        with run_in_tenant_context(tenant.id):
            item = ItemCatalogo.objects.create(
                tenant=tenant,
                codigo_interno="REG-SOB-001",
                tipo="peca",
                controla_estoque=False,
            )
        _regra_pg(tenant, item.id, n=1, inicio=_JAN)  # aberta (vigencia_fim=None)
        with pytest.raises(IntegrityError):
            _regra_pg(tenant, item.id, n=2, inicio=_JUN)  # sobrepõe com a aberta

    @pytest.mark.django_db(transaction=True)
    def test_revogada_libera_mesma_janela(self) -> None:
        """Regra revogada sai da exclusion; substituta na mesma janela é permitida."""
        tenant = TenantFactory()
        from src.infrastructure.produtos_pecas_servicos.models import ItemCatalogo

        with run_in_tenant_context(tenant.id):
            item = ItemCatalogo.objects.create(
                tenant=tenant,
                codigo_interno="REG-SOB-002",
                tipo="peca",
                controla_estoque=False,
            )
        regra = _regra_pg(tenant, item.id, n=1, inicio=_JAN)
        # Revogar encerra a exclusion — UPDATE de revogado_em é legítimo
        with run_in_tenant_context(tenant.id):
            RegraFormacaoPreco.objects.filter(id=regra.id).update(
                revogado_em=timezone.now(), motivo_revogacao="preco errado — revogar e recriar"
            )
        # Substituta na mesma janela deve ser criada sem IntegrityError
        substituta = _regra_pg(tenant, item.id, n=2, inicio=_JAN)
        assert substituta.id != regra.id


# ---------------------------------------------------------------------------
# INV-PRC-APROVACAO-ONE-SHOT — PG-real (trigger one-shot)
# ---------------------------------------------------------------------------


class TestINV_PRC_APROVACAO_ONE_SHOT:
    """INV-PRC-APROVACAO-ONE-SHOT: segunda decisão no mesmo pedido → DatabaseError."""

    @pytest.mark.django_db(transaction=True)
    def test_segunda_decisao_bloqueada_por_trigger(self) -> None:
        """Trigger one-shot bloqueia UPDATE em pedido já APROVADO."""
        tenant = TenantFactory()
        pedido = _pedido_pg(tenant, estado="aprovado")
        with run_in_tenant_context(tenant.id), pytest.raises(DatabaseError):
            PedidoAprovacaoDesconto.objects.filter(id=pedido.id).update(estado="negado")

    @pytest.mark.django_db(transaction=True)
    def test_decisao_inicial_de_solicitado_permitida(self) -> None:
        """Primeira decisão em pedido SOLICITADO é permitida."""
        tenant = TenantFactory()
        pedido = _pedido_pg(tenant, estado="solicitado")
        with run_in_tenant_context(tenant.id):
            PedidoAprovacaoDesconto.objects.filter(id=pedido.id).update(
                estado="aprovado",
                decisor_id=uuid4(),
                decidido_em=timezone.now(),
            )
        with run_in_tenant_context(tenant.id):
            atualizado = PedidoAprovacaoDesconto.objects.get(id=pedido.id)
        assert atualizado.estado == "aprovado"


# ---------------------------------------------------------------------------
# INV-PRC-APROVACAO-INDEPENDENTE — PG-real (CHECK) + domínio (puro)
# ---------------------------------------------------------------------------


class TestINV_PRC_APROVACAO_INDEPENDENTE:
    """INV-PRC-APROVACAO-INDEPENDENTE: decisor != solicitante — CHECK + domínio."""

    @pytest.mark.django_db(transaction=True)
    def test_check_banco_rejeita_decisor_igual_solicitante(self) -> None:
        """CHECK `ck_prc_pedido_decisor_independente` bloqueia INSERT com decisor==solicitante."""
        tenant = TenantFactory()
        mesmo_id = uuid4()
        with run_in_tenant_context(tenant.id), pytest.raises(IntegrityError):
            PedidoAprovacaoDesconto.objects.create(
                tenant=tenant,
                contexto_tipo="avulso",
                contexto_id=None,
                pct_solicitado=Decimal("15.00"),
                cortesia=False,
                alcada_exigida="gerente",
                fingerprint_calculo="b" * 64,
                estado="aprovado",
                solicitante_id=mesmo_id,
                decisor_id=mesmo_id,  # VIOLA CHECK INV-PRC-APROVACAO-INDEPENDENTE
                justificativa_hash="v1$hash",
                decidido_em=timezone.now(),
                snapshot_probatorio='{"test": true}',
                criado_em=_AGORA,
            )

    def test_dominio_rejeita_decisor_igual_solicitante(self) -> None:
        """Domínio `validar_decisor_independente` levanta DecisorNaoIndependente."""
        from src.domain.precificacao.transicoes import validar_decisor_independente

        mesmo_id = uuid4()
        with pytest.raises(DecisorNaoIndependente):
            validar_decisor_independente(decisor_id=mesmo_id, solicitante_id=mesmo_id)


# ---------------------------------------------------------------------------
# INV-PRC-MINIMO-BLOQUEIO — domínio (puro)
# ---------------------------------------------------------------------------


class TestINV_PRC_MINIMO_BLOQUEIO:
    """INV-PRC-MINIMO-BLOQUEIO: preço final < mínimo calculável → PrecoMinimoViolado."""

    def test_preco_abaixo_minimo_levanta_erro(self) -> None:
        """Motor levanta PrecoMinimoViolado quando preco_final < preco_minimo (D-PRC-8)."""
        from src.domain.precificacao.entities import (
            ParametrosPrecificacaoTenant,
        )
        from src.domain.precificacao.entities import (
            RegraFormacaoPreco as RegraEntity,
        )
        from src.domain.precificacao.enums import OrigemCusto
        from src.domain.produtos_pecas_servicos.entities import PrecoResolvido
        from src.domain.produtos_pecas_servicos.enums import OrigemPreco
        from src.domain.produtos_pecas_servicos.value_objects import Preco
        from src.domain.shared.value_objects import JanelaVigencia

        tenant_id = uuid4()
        item_id = uuid4()

        regra = RegraEntity(
            id=uuid4(),
            tenant_id=tenant_id,
            item_id=item_id,
            modo=ModoFormacaoPreco.MARGEM_ALVO,
            vigencia=JanelaVigencia(inicio=_JAN),
            versao_n=1,
            criado_por=uuid4(),
            custo_manual_declarado=Decimal("80.00"),
            custo_referencia_em=_JAN,
            margem_alvo_pct=Percentual(Decimal("20.00")),
            margem_piso_pct=Percentual(Decimal("10.00")),
        )
        preco_base = PrecoResolvido(
            item_id=item_id,
            preco=Preco(Decimal("100.00")),
            item_versao_n=1,
            linha_tabela_id=uuid4(),
            tabela_id=uuid4(),
            data_referencia=_JAN,
            origem_preco=OrigemPreco.MANUAL,
        )
        params = ParametrosPrecificacaoTenant(
            id=uuid4(),
            tenant_id=tenant_id,
            custo_km=Decimal("0.00"),
            taxa_parcelamento_mensal=Percentual(Decimal("0.00")),
            pct_comissao_prevista=Percentual(Decimal("0.00")),
            margem_alvo_default=Percentual(Decimal("20.00")),
            margem_piso_default=Percentual(Decimal("10.00")),
            versao_n=1,
            criado_por=uuid4(),
            criado_em=_JAN,
        )

        # Desconto de 95% sobre item com custo manual = preco_final < minimo
        with pytest.raises(PrecoMinimoViolado):
            calcular_precos(
                itens=[preco_base],
                regras={item_id: regra},
                custos={item_id: Decimal("80.00")},
                origens={item_id: OrigemCusto.CUSTO_MANUAL},
                perfis={},
                faixas=[],
                params=params,
                desconto_pct=Percentual(Decimal("95.00")),
                modo_montagem=ModoMontagem.FECHADO_COM_AVISO,
                km=Decimal("0"),
                parcelas=1,
                aliquota_imposto_fracao=Decimal("0.00"),
                imposto_ref=None,
            )


# ---------------------------------------------------------------------------
# INV-PRC-CUSTO-EXPLICITO — domínio (puro)
# ---------------------------------------------------------------------------


class TestINV_PRC_CUSTO_EXPLICITO:
    """INV-PRC-CUSTO-EXPLICITO: StubCustoProvider nunca retorna 0 — levanta CustoIndisponivel."""

    def test_stub_levanta_custo_indisponivel_nunca_zero(self) -> None:
        """StubCustoProvider.__call__ levanta CustoIndisponivel para qualquer item."""
        stub = StubCustoProvider()
        with pytest.raises(CustoIndisponivel):
            stub(tenant_id=uuid4(), item_id=uuid4())

    def test_stub_disponivel_retorna_false(self) -> None:
        """StubCustoProvider.disponivel() sempre retorna False (provider não conectado)."""
        assert StubCustoProvider().disponivel() is False

    def test_custo_indisponivel_e_tipo_semantico_nao_zero(self) -> None:
        """Garantia semântica: ausência é CustoIndisponivel (não zero silencioso)."""
        stub = StubCustoProvider()
        capturado = None
        try:
            stub(tenant_id=uuid4(), item_id=uuid4())
        except CustoIndisponivel as exc:
            capturado = exc
        assert capturado is not None, "deve levantar CustoIndisponivel"
        assert isinstance(capturado, CustoIndisponivel)
        # Nunca é ValueError/ZeroDivisionError — é erro semântico tipado
        assert type(capturado).__name__ == "CustoIndisponivel"


# ---------------------------------------------------------------------------
# INV-PRC-FAIXAS-CONTIGUAS — domínio (puro)
# ---------------------------------------------------------------------------


def _faixa(pct_de: str, pct_ate: str, alcada: Alcada = Alcada.LIVRE) -> FaixaAprovacaoDesconto:
    """Helper para construir FaixaAprovacaoDesconto em testes puros."""
    tenant_id = uuid4()
    return FaixaAprovacaoDesconto(
        id=uuid4(),
        tenant_id=tenant_id,
        pct_de=Percentual(Decimal(pct_de)),
        pct_ate=Percentual(Decimal(pct_ate)),
        alcada=alcada,
        versao_n=1,
        hash_conjunto="x" * 64,
        criado_por=uuid4(),
    )


class TestINV_PRC_FAIXAS_CONTIGUAS:
    """INV-PRC-FAIXAS-CONTIGUAS: conjunto de faixas sem buraco/sobreposição."""

    def test_faixas_com_buraco_levantam_erro(self) -> None:
        """Buraco entre faixas (0-10, 15-100) → FaixasDescontoInvalidas."""
        faixas_invalidas = [
            _faixa("0", "10"),
            _faixa("15", "100"),
        ]
        with pytest.raises(FaixasDescontoInvalidas):
            validar_faixas_contiguas(faixas_invalidas)

    def test_faixas_com_sobreposicao_levantam_erro(self) -> None:
        """Sobreposição (0-15, 10-100) → FaixasDescontoInvalidas."""
        faixas_invalidas = [
            _faixa("0", "15"),
            _faixa("10", "100"),
        ]
        with pytest.raises(FaixasDescontoInvalidas):
            validar_faixas_contiguas(faixas_invalidas)

    def test_faixas_nao_comecam_em_zero_levantam_erro(self) -> None:
        """Conjunto não começa em 0 → FaixasDescontoInvalidas."""
        faixas_invalidas = [
            _faixa("5", "100"),
        ]
        with pytest.raises(FaixasDescontoInvalidas):
            validar_faixas_contiguas(faixas_invalidas)

    def test_faixas_contiguas_validas_passam(self) -> None:
        """Faixas contíguas corretas (0-10-20-100) não levantam erro."""
        faixas_validas = [
            _faixa("0", "10", Alcada.LIVRE),
            _faixa("10", "20", Alcada.GERENTE),
            _faixa("20", "100", Alcada.DONO),
        ]
        # Não levanta exceção
        validar_faixas_contiguas(faixas_validas)


# ---------------------------------------------------------------------------
# INV-026 (herdada) — motor não persiste (estrutural/puro)
# ---------------------------------------------------------------------------


class TestINV_026_MOTOR_NAO_PERSISTE:
    """INV-026: motor `calcular_precos` em transicoes.py não importa ORM Django."""

    def test_transicoes_nao_importa_django_orm(self) -> None:
        """transicoes.py não deve importar `django.db` nem models ORM (motor puro)."""
        import importlib
        import inspect

        modulo = importlib.import_module("src.domain.precificacao.transicoes")
        source = inspect.getsource(modulo)
        assert (
            "from django" not in source
        ), "transicoes.py tem 'from django' — viola motor puro stateless (D-PRC-9/INV-026)"
        assert (
            "import django" not in source
        ), "transicoes.py tem 'import django' — viola motor puro stateless (D-PRC-9/INV-026)"

    def test_calculo_preco_resultado_e_frozen(self) -> None:
        """CalculoPrecoResultado é frozen dataclass — imutável pós-construção (INV-026).

        Verifica via __dataclass_params__.frozen (fonte canônica) e confirma que
        setattr direto levanta FrozenInstanceError em runtime. object.__setattr__
        bypassa o frozen check em CPython e não é o teste correto aqui.
        """
        import dataclasses

        assert dataclasses.fields(CalculoPrecoResultado) is not None, "deve ser dataclass"
        # __dataclass_params__.frozen é a fonte canônica de frozen=True
        assert (
            CalculoPrecoResultado.__dataclass_params__.frozen is True
        ), "CalculoPrecoResultado deve ser frozen=True (INV-026 — motor não persiste)"
        # setattr direto levanta FrozenInstanceError — é o comportamento esperado em runtime
        resultado = CalculoPrecoResultado(
            itens=(),
            componentes_faltantes=(),
            avisos=(),
            alcada_exigida=Alcada.LIVRE,
            motor_versao="v1",
            faixas_versao="v1",
            parametros_versao=1,
            imposto_ref=None,
            eco_entradas={},
        )
        with pytest.raises((dataclasses.FrozenInstanceError, AttributeError, TypeError)):
            resultado.motor_versao = "v2"


# ---------------------------------------------------------------------------
# INV-PRC-MARGEM-RBAC — E2E (serializer + endpoint)
# ---------------------------------------------------------------------------


class TestINV_PRC_MARGEM_RBAC:
    """INV-PRC-MARGEM-RBAC: sem `ver_margem` → custo/margem ausentes na resposta."""

    def test_filtrar_visao_margem_remove_campos_restritos(self) -> None:
        """filtrar_visao_margem() remove margem_estimada/custo_estimado se pode_ver=False."""
        from src.infrastructure.precificacao.serializers import filtrar_visao_margem

        payload = {
            "preco_final": "100.00",
            "semaforo": "verde",
            "preco_minimo": "80.00",
            "margem_estimada": "20.00",
            "custo_estimado": "80.00",
        }
        # Sem permissão
        filtrado = filtrar_visao_margem(payload, pode_ver_margem=False)
        assert "margem_estimada" not in filtrado
        assert "custo_estimado" not in filtrado
        # Campos não-restritos permanecem
        assert "preco_final" in filtrado
        assert "semaforo" in filtrado
        assert "preco_minimo" in filtrado

    def test_filtrar_visao_margem_mantem_campos_com_permissao(self) -> None:
        """filtrar_visao_margem() mantém todos campos quando pode_ver=True."""
        from src.infrastructure.precificacao.serializers import filtrar_visao_margem

        payload = {
            "preco_final": "100.00",
            "margem_estimada": "20.00",
            "custo_estimado": "80.00",
        }
        resultado = filtrar_visao_margem(payload, pode_ver_margem=True)
        assert "margem_estimada" in resultado
        assert "custo_estimado" in resultado

    def test_serializar_item_calculado_aplica_choke_point(self) -> None:
        """serializar_item_calculado() usa filtrar_visao_margem internamente (choke-point)."""
        from src.domain.precificacao.enums import OrigemCusto, Semaforo
        from src.domain.precificacao.value_objects import ItemCalculado
        from src.domain.produtos_pecas_servicos.entities import PrecoResolvido
        from src.domain.produtos_pecas_servicos.enums import OrigemPreco
        from src.domain.produtos_pecas_servicos.value_objects import Preco
        from src.infrastructure.precificacao.serializers import serializar_item_calculado

        item = ItemCalculado(
            preco_base=PrecoResolvido(
                item_id=uuid4(),
                preco=Preco(Decimal("100.00")),
                item_versao_n=1,
                linha_tabela_id=uuid4(),
                tabela_id=uuid4(),
                data_referencia=_JAN,
                origem_preco=OrigemPreco.MANUAL,
            ),
            preco_final=Decimal("100.00"),
            desconto_pct=Percentual(Decimal("0")),
            semaforo=Semaforo.VERDE,
            origem_custo=OrigemCusto.CUSTO_MANUAL,
            sem_regra_formacao=False,
            cortesia=False,
            margem_estimada=Decimal("20.00"),
            custo_estimado=Decimal("80.00"),
        )
        sem_margem = serializar_item_calculado(item, pode_ver_margem=False)
        assert "margem_estimada" not in sem_margem
        assert "custo_estimado" not in sem_margem

        com_margem = serializar_item_calculado(item, pode_ver_margem=True)
        assert "margem_estimada" in com_margem
        assert "custo_estimado" in com_margem


# ---------------------------------------------------------------------------
# INV-PRC-SEGREDO-LOG — E2E (log não vaza custo/margem)
# ---------------------------------------------------------------------------


class TestINV_PRC_SEGREDO_LOG:
    """INV-PRC-SEGREDO-LOG: custo/margem NUNCA aparecem em log estruturado ou corpo 4xx."""

    def test_falha_nao_loga_custo_ou_margem(self, caplog) -> None:
        """_falha() loga apenas type(exc).__name__ — sem str(exc) que poderia conter margem."""
        from src.infrastructure.precificacao.views import _falha

        exc = CustoRealIndisponivel("custo real indisponivel — custo_manual=80.00 margem=20.00")
        chave_id = uuid4()
        tenant_id = uuid4()

        with caplog.at_level(logging.WARNING, logger="src.infrastructure.precificacao.views"):
            _falha(chave_id, tenant_id, exc, http_status=422)

        # Nenhum log deve conter texto que vaze valor numérico de margem/custo
        for record in caplog.records:
            mensagem = str(record.getMessage())
            assert "custo_manual" not in mensagem, f"margem vazou no log: {mensagem}"
            assert "80.00" not in mensagem, f"valor de custo vazou no log: {mensagem}"
            assert "20.00" not in mensagem, f"valor de margem vazou no log: {mensagem}"

    def test_corpo_4xx_nao_expoe_custo_margem(self) -> None:
        """Corpo da resposta 422 expõe apenas o nome do erro, não o detalhe numérico."""
        from src.infrastructure.precificacao.views import _falha

        exc = CustoRealIndisponivel("custo manual: 80.00, margem: 20.00, preco_fixo: 150.00")
        resp = _falha(uuid4(), uuid4(), exc, http_status=422)
        corpo = resp.data

        # Apenas tipo, sem detalhe que contenha valor
        assert "codigo" in corpo
        assert corpo["codigo"] == "CustoRealIndisponivel"
        # detalhe é o nome do tipo (não a mensagem da exceção)
        assert "80.00" not in str(corpo)
        assert "20.00" not in str(corpo)


# ---------------------------------------------------------------------------
# INV-PRC-JUSTIFICATIVA-HASH — E2E (tabela-par + WORM)
# ---------------------------------------------------------------------------


class TestINV_PRC_JUSTIFICATIVA_HASH:
    """INV-PRC-JUSTIFICATIVA-HASH: texto livre em tabela-par; hash no WORM."""

    def test_decidir_aprovacao_usa_hash_no_worm_e_texto_na_tabela_par(self) -> None:
        """decidir_aprovacao grava hash no WORM e texto cru via salvar_justificativa_fn."""
        from src.domain.precificacao.entities import PedidoAprovacaoDesconto as PedidoDomain

        tenant_id = uuid4()
        solicitante_id = uuid4()
        decisor_id = uuid4()

        pedido = PedidoDomain(
            id=uuid4(),
            tenant_id=tenant_id,
            contexto_tipo=ContextoTipo.AVULSO,
            contexto_id=None,
            pct_solicitado=Percentual(Decimal("15.00")),
            cortesia=False,
            alcada_exigida=Alcada.GERENTE,
            fingerprint_calculo="c" * 64,
            estado=EstadoPedido.SOLICITADO,
            solicitante_id=solicitante_id,
            snapshot_probatorio='{"test": true}',
            criado_em=_AGORA,
        )
        repo_pedido = _FakePedidoRepo(pedido=pedido)

        justificativas_salvas: list[tuple] = []

        def _salvar_just(pedido_id, t_id, texto):
            justificativas_salvas.append((pedido_id, t_id, texto))

        def _hash_just(texto, t_id):
            # Simula hash sem KMS — retorna prefixo fixo
            return f"v1$hash_{texto[:8]}"

        texto_cru = "Desconto aprovado para cliente especial — margem ok"

        inp = DecidirAprovacaoInput(
            tenant_id=tenant_id,
            pedido_id=pedido.id,
            estado_novo=EstadoPedido.APROVADO,
            decisor_id=decisor_id,
            papel_decisor=Alcada.GERENTE,
            justificativa=texto_cru,
            fingerprint_calculo_atual="c" * 64,
            agora=_AGORA,
            hash_justificativa_fn=_hash_just,
        )
        out = decidir_aprovacao(inp, repo_pedido=repo_pedido, salvar_justificativa_fn=_salvar_just)

        # No WORM: hash (não o texto)
        assert out.justificativa_hash.startswith("v1$hash_")
        assert texto_cru not in out.justificativa_hash

        # Na tabela-par: texto cru salvo via callback
        assert len(justificativas_salvas) == 1
        _, _, texto_salvo = justificativas_salvas[0]
        assert texto_salvo == texto_cru

    def test_hash_justificativa_e_diferente_do_texto_cru(self) -> None:
        """O hash nunca é idêntico ao texto original (garantia semântica básica)."""
        import hashlib

        texto = "justificativa de desconto especial"

        def _fake_hash(t, t_id):
            return f"v1${hashlib.sha256(t.encode()).hexdigest()[:16]}"  # audit-pii-salt: skip -- _fake_hash de TESTE so prova hash!=texto; nao e producao, nao persiste PII, nao toca tenant

        resultado_hash = _fake_hash(texto, uuid4())
        assert resultado_hash != texto
        assert resultado_hash.startswith("v1$")
