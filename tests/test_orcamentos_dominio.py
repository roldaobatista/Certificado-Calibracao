"""Testes puros do domínio Orçamentos — T-ORC-015.

SEM @django_db. Exercita:
  - Máquina de estados happy (transições válidas).
  - Máquina de estados unhappy (transição proibida levanta TransicaoProibida).
  - Tradução de enum TipoAtividadeAlvo → TipoAtividade (todos os 5 casos).
  - TipoAtividadeAlvo NÃO tem valor "outro".
  - ``montar_envelope_orcamento_aprovado``:
      * Item técnico: tipo traduzido + equipamento_id como str.
      * Item comercial: equipamento_id None + placeholder.
      * valor_total e UUIDs como str.
  - INV-ORC-MARGEM-OFF: ItemOrcamento não tem atributo de margem/custo.

Refs:
  T-ORC-015, D-ORC-3, D-ORC-6, D-ORC-16, INV-ORC-MARGEM-OFF,
  INV-ORC-EQUIP-ITEM, INV-ORC-APROVADO-ENVELOPE
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID, uuid4

import pytest
from src.domain.comercial.orcamentos.entities import (
    AnaliseCriticaOrcamento,
    ItemOrcamento,
    Orcamento,
)
from src.domain.comercial.orcamentos.enums import (
    EstadoOrcamento,
    TipoAtividadeAlvo,
    VeredictoAnaliseCritica,
)
from src.domain.comercial.orcamentos.erros import TransicaoProibida
from src.domain.comercial.orcamentos.transicoes import (
    TRANSICOES_VALIDAS,
    montar_envelope_orcamento_aprovado,
    pode_transicionar,
    traduzir_tipo_atividade_alvo,
    validar_transicao,
)
from src.domain.comercial.orcamentos.value_objects import CondicoesPagamento, Desconto
from src.domain.operacao.os.value_objects import TipoAtividade, TipoItemComercial
from src.domain.produtos_pecas_servicos.entities import PrecoResolvido
from src.domain.produtos_pecas_servicos.enums import OrigemPreco
from src.domain.produtos_pecas_servicos.value_objects import Preco
from src.domain.shared.value_objects import Dinheiro, JanelaVigencia

UTC = UTC


def _din(centavos: int) -> Dinheiro:
    """Atalho de teste: Dinheiro em centavos (BRL)."""
    return Dinheiro(centavos)


# =====================================================================
# HELPERS / FIXTURES
# =====================================================================

def _preco_resolvido(valor: str = "150.00") -> PrecoResolvido:
    """Factory mínima de PrecoResolvido para testes."""
    return PrecoResolvido(
        item_id=uuid4(),
        item_versao_n=1,
        linha_tabela_id=uuid4(),
        tabela_id=uuid4(),
        preco=Preco(Decimal(valor)),
        data_referencia=datetime(2026, 1, 1, tzinfo=UTC),
        origem_preco=OrigemPreco.MANUAL,
    )


def _orcamento(liquido: int = 30000) -> Orcamento:
    """Factory mínima de Orcamento para testes."""
    from src.domain.comercial.orcamentos.value_objects import CondicoesPagamento

    return Orcamento(
        id=uuid4(),
        tenant_id=uuid4(),
        cliente_atual_id=uuid4(),
        cliente_referencia_hash="a" * 64,
        cliente_key_id="v1",
        numero=1,
        estado=EstadoOrcamento.APROVADO_PENDENTE_OS,
        validade=JanelaVigencia(inicio=datetime(2026, 1, 1, tzinfo=UTC)),
        total_bruto=_din(30000),
        descontos=_din(0),
        impostos=_din(0),
        liquido=_din(liquido),
        comissao_prevista=_din(1500),
        condicoes_pagamento=CondicoesPagamento.a_vista_pix(),
        criado_em=datetime(2026, 1, 1, tzinfo=UTC),
        criado_por=uuid4(),
    )


def _item_tecnico(sequencia: int = 1) -> ItemOrcamento:
    """ItemOrcamento com equipamento_id (item técnico de calibração)."""
    return ItemOrcamento(
        id=uuid4(),
        versao_id=uuid4(),
        tenant_id=uuid4(),
        catalogo_item_id=uuid4(),
        sequencia=sequencia,
        preco_resolvido=_preco_resolvido("150.00"),
        preco_final=_din(15000),
        desconto_pct=Decimal("0"),
        desconto_valor=_din(0),
        quantidade=Decimal("1"),
        total=_din(15000),
        semaforo="verde",
        descricao_snapshot="Calibração balança 500kg",
        equipamento_id=uuid4(),
        tipo_atividade_alvo=TipoAtividadeAlvo.CALIBRACAO,
        tipo_item_comercial=None,
        grandeza_solicitada="massa",
        faixa_solicitada_min=Decimal("0"),
        faixa_solicitada_max=Decimal("500"),
        unidade_solicitada="kg",
    )


def _item_comercial(sequencia: int = 2) -> ItemOrcamento:
    """ItemOrcamento sem equipamento_id (item comercial)."""
    return ItemOrcamento(
        id=uuid4(),
        versao_id=uuid4(),
        tenant_id=uuid4(),
        catalogo_item_id=uuid4(),
        sequencia=sequencia,
        preco_resolvido=_preco_resolvido("50.00"),
        preco_final=_din(5000),
        desconto_pct=Decimal("0"),
        desconto_valor=_din(0),
        quantidade=Decimal("1"),
        total=_din(5000),
        semaforo="verde",
        descricao_snapshot="Taxa de visita",
        equipamento_id=None,
        tipo_atividade_alvo=None,
        tipo_item_comercial=TipoItemComercial.TAXA_VISITA,
    )


def _analise_critica(orcamento_id: UUID, veredito: VeredictoAnaliseCritica) -> AnaliseCriticaOrcamento:
    return AnaliseCriticaOrcamento(
        id=uuid4(),
        orcamento_id=orcamento_id,
        versao_id=uuid4(),
        tenant_id=uuid4(),
        perfil_no_evento="A",
        veredito=veredito,
        norma_referencia="ISO/IEC 17025:2017 cl. 7.1.1",
        itens_avaliados=(
            {
                "equipamento_id": str(uuid4()),
                "grandeza": "massa",
                "faixa_min": "0",
                "faixa_max": "500",
                "unidade": "kg",
                "cobre_cmc": True,
                "cmc_codigo_ref": "CMC-0001",
                "procedimento_ok": True,
                "procedimento_id": str(uuid4()),
                "procedimento_codigo": "POP-CAL-0042 rev.3",
                "procedimento_versao": "3",
                "ressalvas": [],
            },
        ),
        snapshot_hash="b" * 64,
        avaliada_em=datetime(2026, 1, 2, tzinfo=UTC),
        avaliada_por=str(uuid4()),
    )


# =====================================================================
# TESTES — MÁQUINA DE ESTADOS
# =====================================================================


class TestMaquinaDeEstados:
    """D-ORC-3 — transições válidas e proibidas."""

    def test_rascunho_pode_ir_para_enviado(self):
        assert pode_transicionar(EstadoOrcamento.RASCUNHO, EstadoOrcamento.ENVIADO)

    def test_rascunho_pode_ser_cancelado(self):
        assert pode_transicionar(EstadoOrcamento.RASCUNHO, EstadoOrcamento.CANCELADO)

    def test_enviado_pode_ir_para_aprovado(self):
        assert pode_transicionar(EstadoOrcamento.ENVIADO, EstadoOrcamento.APROVADO)

    def test_enviado_pode_ser_recusado(self):
        assert pode_transicionar(EstadoOrcamento.ENVIADO, EstadoOrcamento.RECUSADO)

    def test_enviado_pode_expirar(self):
        assert pode_transicionar(EstadoOrcamento.ENVIADO, EstadoOrcamento.EXPIRADO)

    def test_aprovado_vai_para_pendente_os(self):
        assert pode_transicionar(EstadoOrcamento.APROVADO, EstadoOrcamento.APROVADO_PENDENTE_OS)

    def test_pendente_os_vira_convertido(self):
        assert pode_transicionar(
            EstadoOrcamento.APROVADO_PENDENTE_OS, EstadoOrcamento.CONVERTIDO
        )

    def test_convertido_e_terminal(self):
        """INV-ORC-CONVERTIDO-TERMINAL: convertido não transiciona para nada."""
        for destino in EstadoOrcamento:
            assert not pode_transicionar(EstadoOrcamento.CONVERTIDO, destino), (
                f"convertido → {destino.value} deveria ser proibido"
            )

    def test_aprovado_nao_pode_voltar_para_rascunho(self):
        assert not pode_transicionar(EstadoOrcamento.APROVADO, EstadoOrcamento.RASCUNHO)

    def test_validar_transicao_levanta_transicao_proibida(self):
        with pytest.raises(TransicaoProibida) as exc_info:
            validar_transicao(EstadoOrcamento.CONVERTIDO, EstadoOrcamento.RASCUNHO)
        assert "convertido" in str(exc_info.value)
        assert "rascunho" in str(exc_info.value)

    def test_validar_transicao_ok_nao_levanta(self):
        # Não deve levantar
        validar_transicao(EstadoOrcamento.RASCUNHO, EstadoOrcamento.ENVIADO)

    def test_todos_os_estados_tem_entrada_no_grafo(self):
        """Garantia de completude do grafo — todos os estados cobertos."""
        for estado in EstadoOrcamento:
            assert estado in TRANSICOES_VALIDAS, (
                f"EstadoOrcamento.{estado.name} sem entrada em TRANSICOES_VALIDAS"
            )

    def test_estados_terminais_tem_frozenset_vazio(self):
        terminais = [
            EstadoOrcamento.CONVERTIDO,
            EstadoOrcamento.RECUSADO,
            EstadoOrcamento.EXPIRADO,
            EstadoOrcamento.CANCELADO,
        ]
        for estado in terminais:
            assert TRANSICOES_VALIDAS[estado] == frozenset(), (
                f"{estado.value} deveria ter frozenset vazio (terminal)"
            )


# =====================================================================
# TESTES — TRADUÇÃO DE ENUM (D-ORC-16)
# =====================================================================


class TestTraducaoEnum:
    """D-ORC-16 — mapa fechado TipoAtividadeAlvo → TipoAtividade."""

    def test_calibracao(self):
        assert traduzir_tipo_atividade_alvo(TipoAtividadeAlvo.CALIBRACAO) == TipoAtividade.CALIBRACAO

    def test_manutencao_vai_para_corretiva(self):
        """manutencao → MANUTENCAO_CORRETIVA (default D-ORC-16; PREVENTIVA é agenda interna)."""
        assert traduzir_tipo_atividade_alvo(TipoAtividadeAlvo.MANUTENCAO) == TipoAtividade.MANUTENCAO_CORRETIVA

    def test_instalacao(self):
        assert traduzir_tipo_atividade_alvo(TipoAtividadeAlvo.INSTALACAO) == TipoAtividade.INSTALACAO

    def test_verificacao_vai_para_verificacao_inmetro(self):
        assert traduzir_tipo_atividade_alvo(TipoAtividadeAlvo.VERIFICACAO) == TipoAtividade.VERIFICACAO_INMETRO

    def test_vistoria(self):
        assert traduzir_tipo_atividade_alvo(TipoAtividadeAlvo.VISTORIA) == TipoAtividade.VISTORIA

    def test_tipo_atividade_alvo_nao_tem_outro(self):
        """D-ORC-16 — NÃO existe TipoAtividadeAlvo.OUTRO."""
        valores = {e.value for e in TipoAtividadeAlvo}
        assert "outro" not in valores, (
            "TipoAtividadeAlvo não deve ter 'outro' — itens comerciais não têm tipo_atividade_alvo (D-ORC-16)"
        )

    def test_todos_os_5_valores_estao_mapeados(self):
        """Todos os valores de TipoAtividadeAlvo devem ter mapeamento."""
        for alvo in TipoAtividadeAlvo:
            resultado = traduzir_tipo_atividade_alvo(alvo)
            assert isinstance(resultado, TipoAtividade), (
                f"TipoAtividadeAlvo.{alvo.name} retornou {resultado!r}"
            )


# =====================================================================
# TESTES — MONTAGEM DO ENVELOPE (D-ORC-6 / INV-ORC-APROVADO-ENVELOPE)
# =====================================================================


class TestMontagemEnvelope:
    """Contrato exato do payload orcamento.aprovado (D-ORC-6)."""

    def test_item_tecnico_tem_tipo_traduzido_e_equipamento_id(self):
        """Item com equipamento_id → tipo traduzido + equipamento_id como str."""
        orc = _orcamento()
        equip_id = uuid4()
        item = ItemOrcamento(
            id=uuid4(),
            versao_id=uuid4(),
            tenant_id=orc.tenant_id,
            catalogo_item_id=uuid4(),
            sequencia=1,
            preco_resolvido=_preco_resolvido("200.00"),
            preco_final=_din(20000),
            desconto_pct=Decimal("0"),
            desconto_valor=_din(0),
            quantidade=Decimal("1"),
            total=_din(20000),
            semaforo="verde",
            descricao_snapshot="Calibração balança",
            equipamento_id=equip_id,
            tipo_atividade_alvo=TipoAtividadeAlvo.CALIBRACAO,
            grandeza_solicitada="massa",
            faixa_solicitada_min=Decimal("0"),
            faixa_solicitada_max=Decimal("500"),
            unidade_solicitada="kg",
        )

        envelope = montar_envelope_orcamento_aprovado(
            orcamento=orc,
            itens=[item],
            analise_critica=None,
        )

        itens = envelope["itens"]
        assert len(itens) == 1
        it = itens[0]
        assert it["tipo"] == TipoAtividade.CALIBRACAO.value
        assert it["equipamento_id"] == str(equip_id)
        assert it["sequencia"] == 1
        assert isinstance(it["valor_unitario"], str)
        assert it["valor_unitario"] == "200.00"

    def test_item_comercial_tem_equipamento_id_none(self):
        """Item sem equipamento_id → equipamento_id=None + placeholder + descricao."""
        orc = _orcamento()
        item = ItemOrcamento(
            id=uuid4(),
            versao_id=uuid4(),
            tenant_id=orc.tenant_id,
            catalogo_item_id=uuid4(),
            sequencia=2,
            preco_resolvido=_preco_resolvido("50.00"),
            preco_final=_din(5000),
            desconto_pct=Decimal("0"),
            desconto_valor=_din(0),
            quantidade=Decimal("1"),
            total=_din(5000),
            semaforo="verde",
            descricao_snapshot="Taxa de visita técnica",
            equipamento_id=None,
            tipo_atividade_alvo=None,
            tipo_item_comercial=TipoItemComercial.TAXA_VISITA,
        )

        envelope = montar_envelope_orcamento_aprovado(
            orcamento=orc,
            itens=[item],
            analise_critica=None,
        )

        itens = envelope["itens"]
        assert len(itens) == 1
        it = itens[0]
        assert it["equipamento_id"] is None
        assert it["sequencia"] == 2
        # Placeholder para GATE-ORC-ITEMCOMERCIAL-DESCRICAO
        assert it["tipo"] == "vistoria"
        # Campo aditivo com a descrição do snapshot
        assert it["descricao"] == "Taxa de visita técnica"
        assert it["requer_recebimento"] is False

    def test_valor_total_e_string(self):
        """valor_total deve ser str (Decimal como str — evita float no JSON)."""
        orc = _orcamento(liquido=30000)  # R$ 300,00
        envelope = montar_envelope_orcamento_aprovado(
            orcamento=orc,
            itens=[],
            analise_critica=None,
        )
        assert isinstance(envelope["valor_total"], str)
        assert envelope["valor_total"] == "300.00"

    def test_uuids_sao_string(self):
        """Todos os UUIDs no envelope devem ser str, não UUID."""
        orc = _orcamento()
        envelope = montar_envelope_orcamento_aprovado(
            orcamento=orc,
            itens=[],
            analise_critica=None,
        )
        assert isinstance(envelope["orcamento_id"], str)
        assert isinstance(envelope["tenant_id"], str)
        # Valida que são UUIDs válidos
        UUID(envelope["orcamento_id"])
        UUID(envelope["tenant_id"])

    def test_header_equipamento_id_sempre_none(self):
        """Header equipamento_id = None em orçamentos v2 (D-ORC-6 — legado v1)."""
        orc = _orcamento()
        envelope = montar_envelope_orcamento_aprovado(
            orcamento=orc,
            itens=[],
            analise_critica=None,
        )
        assert envelope["equipamento_id"] is None

    def test_analise_critica_popula_id_e_hash(self):
        orc = _orcamento()
        analise = _analise_critica(orc.id, VeredictoAnaliseCritica.APROVADA)

        envelope = montar_envelope_orcamento_aprovado(
            orcamento=orc,
            itens=[],
            analise_critica=analise,
        )
        assert envelope["analise_critica_id"] == str(analise.id)
        assert envelope["analise_critica_snapshot_hash"] == analise.snapshot_hash

    def test_sem_analise_critica_campos_ausentes(self):
        orc = _orcamento()
        envelope = montar_envelope_orcamento_aprovado(
            orcamento=orc,
            itens=[],
            analise_critica=None,
        )
        assert envelope["analise_critica_id"] is None
        assert envelope["analise_critica_snapshot_hash"] == ""

    def test_bifurcacao_tecnico_e_comercial_juntos(self):
        """Envelope com 1 item técnico + 1 item comercial (INV-ORC-EQUIP-ITEM)."""
        orc = _orcamento()
        item_tec = _item_tecnico(sequencia=1)
        item_com = _item_comercial(sequencia=2)

        envelope = montar_envelope_orcamento_aprovado(
            orcamento=orc,
            itens=[item_tec, item_com],
            analise_critica=None,
        )

        itens = envelope["itens"]
        assert len(itens) == 2

        tec = itens[0]
        assert tec["equipamento_id"] == str(item_tec.equipamento_id)
        assert tec["tipo"] == TipoAtividade.CALIBRACAO.value

        com = itens[1]
        assert com["equipamento_id"] is None
        assert com["tipo"] == "vistoria"  # placeholder

    def test_abertura_at_e_iso_string(self):
        orc = _orcamento()
        t = datetime(2026, 6, 14, 12, 0, 0, tzinfo=UTC)
        envelope = montar_envelope_orcamento_aprovado(
            orcamento=orc,
            itens=[],
            analise_critica=None,
            abertura_at=t,
        )
        assert isinstance(envelope["abertura_at"], str)
        # Deve parsear de volta sem erro
        datetime.fromisoformat(envelope["abertura_at"])


# =====================================================================
# TESTES — INV-ORC-MARGEM-OFF
# =====================================================================


class TestMargemOff:
    """INV-ORC-MARGEM-OFF — ItemOrcamento não tem atributo de margem/custo."""

    def test_item_orcamento_nao_tem_margem(self):
        item = _item_tecnico()
        assert not hasattr(item, "margem"), (
            "ItemOrcamento não deve ter atributo 'margem' (INV-ORC-MARGEM-OFF)"
        )

    def test_item_orcamento_nao_tem_custo(self):
        item = _item_tecnico()
        assert not hasattr(item, "custo"), (
            "ItemOrcamento não deve ter atributo 'custo' (INV-ORC-MARGEM-OFF)"
        )

    def test_item_orcamento_nao_tem_custo_unitario(self):
        item = _item_tecnico()
        assert not hasattr(item, "custo_unitario"), (
            "ItemOrcamento não deve ter atributo 'custo_unitario' (INV-ORC-MARGEM-OFF)"
        )

    def test_item_orcamento_nao_tem_markup(self):
        item = _item_tecnico()
        assert not hasattr(item, "markup"), (
            "ItemOrcamento não deve ter atributo 'markup' (INV-ORC-MARGEM-OFF)"
        )


# =====================================================================
# TESTES — VALUE OBJECTS
# =====================================================================


class TestDesconto:
    def test_por_percentual(self):
        d = Desconto.por_percentual(Decimal("10"))
        assert d.percentual == Decimal("10")
        assert d.valor_centavos == 0

    def test_por_valor(self):
        d = Desconto.por_valor(500)
        assert d.valor_centavos == 500
        assert d.percentual == Decimal("0")

    def test_percentual_fora_de_range_levanta(self):
        with pytest.raises(ValueError, match="0, 100"):
            Desconto(percentual=Decimal("101"), valor_centavos=0)

    def test_desconto_vazio_levanta(self):
        with pytest.raises(ValueError, match="0 e valor_centavos=0"):
            Desconto(percentual=Decimal("0"), valor_centavos=0)

    def test_valor_negativo_levanta(self):
        with pytest.raises(ValueError, match="negativo"):
            Desconto(percentual=Decimal("0"), valor_centavos=-1)


class TestCondicoesPagamento:
    def test_a_vista_pix(self):
        c = CondicoesPagamento.a_vista_pix()
        assert c.parcelas == 1
        assert c.forma_pagamento == "pix"

    def test_parcelado(self):
        c = CondicoesPagamento.parcelado(3, "boleto")
        assert c.parcelas == 3
        assert c.forma_pagamento == "boleto"

    def test_forma_invalida_levanta(self):
        with pytest.raises(ValueError, match="inválida"):
            CondicoesPagamento(parcelas=1, forma_pagamento="bitcoin")

    def test_parcelas_zero_levanta(self):
        with pytest.raises(ValueError, match="≥ 1"):
            CondicoesPagamento(parcelas=0, forma_pagamento="pix")

    def test_observacoes_longas_levanta(self):
        with pytest.raises(ValueError, match="300 chars"):
            CondicoesPagamento(
                parcelas=1,
                forma_pagamento="pix",
                observacoes="x" * 301,
            )


# =====================================================================
# TESTES — ENTIDADE ItemOrcamento (consistência interna)
# =====================================================================


class TestItemOrcamentoConsistencia:
    """INV-ORC-EQUIP-ITEM — consistência entre equipamento_id e tipo_atividade_alvo."""

    def test_tecnico_sem_tipo_atividade_levanta(self):
        with pytest.raises(ValueError, match="tipo_atividade_alvo"):
            ItemOrcamento(
                id=uuid4(),
                versao_id=uuid4(),
                tenant_id=uuid4(),
                catalogo_item_id=uuid4(),
                sequencia=1,
                preco_resolvido=_preco_resolvido(),
                preco_final=_din(10000),
                desconto_pct=Decimal("0"),
                desconto_valor=_din(0),
                quantidade=Decimal("1"),
                total=_din(10000),
                semaforo="verde",
                descricao_snapshot="desc",
                equipamento_id=uuid4(),   # preenchido
                tipo_atividade_alvo=None, # mas sem tipo → inválido
            )

    def test_comercial_com_tipo_atividade_levanta(self):
        with pytest.raises(ValueError, match="equipamento_id"):
            ItemOrcamento(
                id=uuid4(),
                versao_id=uuid4(),
                tenant_id=uuid4(),
                catalogo_item_id=uuid4(),
                sequencia=1,
                preco_resolvido=_preco_resolvido(),
                preco_final=_din(10000),
                desconto_pct=Decimal("0"),
                desconto_valor=_din(0),
                quantidade=Decimal("1"),
                total=_din(10000),
                semaforo="verde",
                descricao_snapshot="desc",
                equipamento_id=None,                            # sem equipamento
                tipo_atividade_alvo=TipoAtividadeAlvo.VISTORIA, # mas com tipo → inválido
            )
