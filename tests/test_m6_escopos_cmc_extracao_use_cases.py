"""Use cases da extração PDF — M6 Fatia 4 (T-ECMC-051/052). Fake repo, sem DB.

importar_escopo_pdf (staging RASCUNHO, INV-ECMC-007) + confirmar_escopo_extraido
(reusa cadastrar; origem EXTRACAO_PDF; one-shot; audit). Valores à mão.
"""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest
from src.application.metrologia.escopos_cmc import (
    confirmar_escopo_extraido,
    importar_escopo_pdf,
)
from src.domain.metrologia.escopos_cmc.entities import EscopoExtraido
from src.domain.metrologia.escopos_cmc.enums import OrigemEscopo
from src.domain.metrologia.escopos_cmc.extracao import MapaColunas

from tests.test_m6_escopos_cmc_use_cases_p2 import FakeEscopoRepo, _input_cadastro

_DT = datetime(2026, 1, 1, tzinfo=UTC)
_MAPA = MapaColunas(grandeza=0, faixa=1, unidade=2, cmc=3, metodo=4)
_LINHAS = [
    ["Massa", "0,5 a 200", "kg", "0,1", "PRO-CAL-MASSA-01"],
    ["Temperatura", "(-30 a 660)", "C", "0,05", ""],
]


class FakeExtraidoRepo:
    """EscopoExtraidoRepository em memória (Protocol estrutural)."""

    def __init__(self) -> None:
        self.store: dict[UUID, EscopoExtraido] = {}

    def salvar_novo(self, snapshot: EscopoExtraido) -> None:
        self.store[snapshot.id] = snapshot

    def obter_por_id(self, extraido_id: UUID) -> EscopoExtraido | None:
        return self.store.get(extraido_id)

    def marcar_confirmado(self, *, extraido_id, confirmado_em, por_id_hash) -> bool:
        cur = self.store.get(extraido_id)
        if cur is None or cur.confirmado_em is not None:
            return False
        self.store[extraido_id] = replace(
            cur, confirmado_em=confirmado_em, confirmado_por_id_hash=por_id_hash
        )
        return True


def _input_importar(tenant_id: UUID) -> importar_escopo_pdf.ImportarEscopoPdfInput:
    return importar_escopo_pdf.ImportarEscopoPdfInput(
        tenant_id=tenant_id,
        origem_pdf_storage_key="cgcre/escopo-123.pdf",
        numero_escopo_cgcre="CRL-0123",
        linhas_cruas=_LINHAS,
        mapa_colunas=_MAPA,
        extraido_em=_DT,
        correlation_id=uuid4(),
    )


class TestImportar:
    def test_cria_staging_rascunho_nao_vigente(self) -> None:
        """INV-ECMC-007 — importar grava só staging; NÃO cria escopo_cmc vigente."""
        repo = FakeExtraidoRepo()
        out = importar_escopo_pdf.executar(_input_importar(uuid4()), repo)
        assert out.extraido.confirmado_em is None
        assert len(out.extraido.linhas) == 2
        assert out.extraido.linhas[0].grandeza_texto == "Massa"
        assert repo.store[out.extraido.id] is out.extraido

    def test_extraido_em_naive_recusa(self) -> None:
        # proposital: datetime sem timezone deve ser rejeitado (INV-VIG-004) — a
        # validacao e no __post_init__, logo a construcao do input ja levanta.
        naive = datetime(2026, 1, 1, 0, 0)  # -- testa rejeicao de datetime naive
        with pytest.raises(ValueError, match="tz-aware"):
            replace(_input_importar(uuid4()), extraido_em=naive)


def _input_confirmar(
    extraido_id: UUID, tenant_id: UUID, escopos
) -> confirmar_escopo_extraido.ConfirmarEscopoExtraidoInput:
    return confirmar_escopo_extraido.ConfirmarEscopoExtraidoInput(
        extraido_id=extraido_id,
        tenant_id=tenant_id,
        confirmado_por_id_hash="v01$Y29uZmVyZW50ZQ==",
        confirmado_em=_DT,
        escopos=escopos,
    )


class TestConfirmar:
    def test_promove_para_confirmado_origem_pdf(self) -> None:
        tenant = uuid4()
        rextr = FakeExtraidoRepo()
        resc = FakeEscopoRepo()
        imp = importar_escopo_pdf.executar(_input_importar(tenant), rextr)
        # Conferência humana normalizou 1 linha (perfil A RBC, com procedimento).
        linha = _input_cadastro(tenant, perfil="A", rbc=True, procedimento_id=uuid4())
        out = confirmar_escopo_extraido.executar(
            _input_confirmar(imp.extraido.id, tenant, (linha,)), rextr, resc
        )
        assert len(out.confirmados) == 1
        assert out.confirmados[0].origem is OrigemEscopo.EXTRACAO_PDF
        assert out.confirmados[0].rbc_acreditado is True
        # staging marcado (audit quem/quando).
        st = rextr.obter_por_id(imp.extraido.id)
        assert st is not None and st.confirmado_em == _DT
        assert st.confirmado_por_id_hash == "v01$Y29uZmVyZW50ZQ=="

    def test_extraido_inexistente_recusa(self) -> None:
        with pytest.raises(confirmar_escopo_extraido.ExtraidoNaoEncontrado):
            confirmar_escopo_extraido.executar(
                _input_confirmar(uuid4(), uuid4(), (_input_cadastro(uuid4()),)),
                FakeExtraidoRepo(),
                FakeEscopoRepo(),
            )

    def test_tenant_divergente_recusa(self) -> None:
        tenant = uuid4()
        rextr = FakeExtraidoRepo()
        imp = importar_escopo_pdf.executar(_input_importar(tenant), rextr)
        with pytest.raises(confirmar_escopo_extraido.ExtraidoNaoEncontrado):
            confirmar_escopo_extraido.executar(
                _input_confirmar(imp.extraido.id, uuid4(), (_input_cadastro(uuid4()),)),
                rextr,
                FakeEscopoRepo(),
            )

    def test_ja_confirmado_recusa_one_shot(self) -> None:
        tenant = uuid4()
        rextr = FakeExtraidoRepo()
        resc = FakeEscopoRepo()
        imp = importar_escopo_pdf.executar(_input_importar(tenant), rextr)
        linha = _input_cadastro(tenant, perfil="A", rbc=True, procedimento_id=uuid4())
        confirmar_escopo_extraido.executar(
            _input_confirmar(imp.extraido.id, tenant, (linha,)), rextr, resc
        )
        linha2 = _input_cadastro(tenant, perfil="A", rbc=True, procedimento_id=uuid4())
        with pytest.raises(confirmar_escopo_extraido.ExtraidoJaConfirmado):
            confirmar_escopo_extraido.executar(
                _input_confirmar(imp.extraido.id, tenant, (linha2,)), rextr, resc
            )

    def test_sem_linhas_recusa(self) -> None:
        with pytest.raises(ValueError, match="nenhuma linha"):
            _input_confirmar(uuid4(), uuid4(), ())

    def test_confirmador_vazio_recusa(self) -> None:
        with pytest.raises(ValueError, match="confirmado_por_id_hash"):
            confirmar_escopo_extraido.ConfirmarEscopoExtraidoInput(
                extraido_id=uuid4(),
                tenant_id=uuid4(),
                confirmado_por_id_hash="",
                confirmado_em=_DT,
                escopos=(_input_cadastro(uuid4()),),
            )
