"""Testes P1 — maquina de estados + entidades + Protocols (T-PAD-002/006/007)."""

from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal
from uuid import uuid4

import pytest
from src.domain.metrologia.padroes.entities import (
    PadraoMetrologicoSnapshot,
    PadraoUsadoSnapshot,
)
from src.domain.metrologia.padroes.enums import (
    ClassePadrao,
    EstadoPadrao,
    SubtipoPadrao,
    VinculacaoCadeia,
)
from src.domain.metrologia.padroes.transicoes import (
    TransicaoInvalidaError,
    pode_transicionar,
    validar_transicao,
)
from src.domain.metrologia.value_objects import (
    FaixaMedicao,
    Grandeza,
    IncertezaExpandida,
)


class TestTransicoes:
    def test_em_uso_para_recal_valida(self) -> None:
        assert pode_transicionar(EstadoPadrao.EM_USO, EstadoPadrao.EM_RECAL_EXTERNO)

    def test_recal_volta_via_pendente_aprovacao_c4(self) -> None:
        # C-4 FURO-1: recal NAO volta direto a EM_USO; passa por PENDENTE.
        assert not pode_transicionar(
            EstadoPadrao.EM_RECAL_EXTERNO, EstadoPadrao.EM_USO
        )
        assert pode_transicionar(
            EstadoPadrao.EM_RECAL_EXTERNO,
            EstadoPadrao.RECAL_RETORNADO_PENDENTE_APROVACAO,
        )
        assert pode_transicionar(
            EstadoPadrao.RECAL_RETORNADO_PENDENTE_APROVACAO, EstadoPadrao.EM_USO
        )

    def test_sucateado_terminal(self) -> None:
        for e in EstadoPadrao:
            assert not pode_transicionar(EstadoPadrao.SUCATEADO, e)

    def test_validar_transicao_invalida_levanta(self) -> None:
        with pytest.raises(TransicaoInvalidaError, match="Transicao invalida"):
            validar_transicao(EstadoPadrao.EM_USO, EstadoPadrao.EM_USO)

    def test_baixado_reversivel(self) -> None:
        assert pode_transicionar(EstadoPadrao.BAIXADO, EstadoPadrao.EM_USO)
        assert pode_transicionar(EstadoPadrao.BAIXADO, EstadoPadrao.SUCATEADO)


def _padrao() -> PadraoMetrologicoSnapshot:
    return PadraoMetrologicoSnapshot(
        id=uuid4(),
        tenant_id=uuid4(),
        numero_serie="PESO-E2-001",
        fabricante="Mettler",
        modelo="M-1kg",
        subtipo=SubtipoPadrao.PRINCIPAL,
        grandezas=(Grandeza.MASSA,),
        faixas=(FaixaMedicao(Decimal("0"), Decimal("1"), "kg"),),
        incertezas_certificado=(
            IncertezaExpandida(Decimal("0.0001"), Decimal("2"), Decimal("0.9545"), "kg"),
        ),
        vinculacao=VinculacaoCadeia.RBC,
        classe=ClassePadrao.E2,
        cert_externo_storage_key="key-opaca-123",
        validade_certificado_rastreabilidade=date(2027, 5, 1),
        proximo_recal=date(2027, 4, 1),
        intervalo_recal_meses=12,
        intervalo_vi_meses=6,
        criterio_intervalo="Analise de risco cl. 6.4.7 + historico de estabilidade.",
        estado=EstadoPadrao.EM_USO,
        revision=0,
        rastreabilidade_origem_revogada=False,
        vigencia_inicio=datetime(2026, 5, 1, tzinfo=UTC),
        correlation_id=uuid4(),
    )


class TestEntidades:
    def test_padrao_snapshot_constroi_e_eh_frozen(self) -> None:
        p = _padrao()
        assert p.numero_serie == "PESO-E2-001"
        assert p.estado == EstadoPadrao.EM_USO
        with pytest.raises(AttributeError):
            p.numero_serie = "OUTRO"  # type: ignore[misc]

    def test_padrao_usado_snapshot_leituras_ambientais_default_vazio(self) -> None:
        p = _padrao()
        usado = PadraoUsadoSnapshot(
            padrao_id=p.id,
            numero_serie=p.numero_serie,
            fabricante=p.fabricante,
            modelo=p.modelo,
            classe=p.classe,
            vinculacao=p.vinculacao,
            grandezas=p.grandezas,
            faixas=p.faixas,
            incertezas_certificado=p.incertezas_certificado,
            validade_certificado_rastreabilidade=p.validade_certificado_rastreabilidade,
        )
        assert usado.leituras_ambientais_auxiliares == ()


class TestProtocols:
    def test_fake_implementa_padrao_repository(self) -> None:
        from src.domain.metrologia.padroes.repository import PadraoRepository

        class FakePadraoRepo:
            def obter_por_id(self, padrao_id):
                return None

            def existe_numero_serie(self, tenant_id, numero_serie):
                return False

            def salvar_novo(self, snapshot):
                return None

            def atualizar_com_lock(self, snapshot, revision_anterior):
                return True

        assert isinstance(FakePadraoRepo(), PadraoRepository)
