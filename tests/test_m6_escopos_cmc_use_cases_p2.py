"""Use cases escopos-cmc — M6 Fatia 2 (T-ECMC-020..023). Fake repo, sem DB.

cadastrar (perfil A RBC / B-C-D capacidade interna anti-fraude) + revisar (nova
versão preserva anterior) + revogar (one-shot). Valores conferidos à mão.
"""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID, uuid4

import pytest
from src.application.metrologia.escopos_cmc import (
    cadastrar_escopo,
    revisar_escopo,
    revogar_escopo,
)
from src.domain.metrologia.escopos_cmc.entities import EscopoCMCSnapshot
from src.domain.metrologia.escopos_cmc.enums import EstadoEscopo, FormaCMC
from src.domain.metrologia.value_objects import FaixaMedicao, Grandeza

_DT = datetime(2026, 1, 1, tzinfo=UTC)
_DT2 = datetime(2026, 6, 1, tzinfo=UTC)


class FakeEscopoRepo:
    """EscopoRepository em memória (Protocol estrutural — runtime_checkable)."""

    def __init__(self) -> None:
        self.store: dict[UUID, EscopoCMCSnapshot] = {}

    def obter_por_id(self, escopo_id: UUID) -> EscopoCMCSnapshot | None:
        return self.store.get(escopo_id)

    def _mesma_chave(self, s, tenant_id, grandeza, faixa, procedimento_id) -> bool:
        return (
            s.tenant_id == tenant_id
            and s.grandeza == grandeza
            and s.faixa == faixa
            and s.procedimento_id == procedimento_id
        )

    def existe_chave_confirmada(self, *, tenant_id, grandeza, faixa, procedimento_id, versao) -> bool:
        return any(
            self._mesma_chave(s, tenant_id, grandeza, faixa, procedimento_id) and s.versao == versao
            for s in self.store.values()
        )

    def proxima_versao(self, *, tenant_id, grandeza, faixa, procedimento_id) -> int:
        versoes = [
            s.versao
            for s in self.store.values()
            if self._mesma_chave(s, tenant_id, grandeza, faixa, procedimento_id)
        ]
        return (max(versoes) + 1) if versoes else 1

    def salvar_novo(self, snapshot: EscopoCMCSnapshot) -> None:
        self.store[snapshot.id] = snapshot

    def atualizar_com_lock(self, snapshot, revision_anterior) -> bool:
        cur = self.store.get(snapshot.id)
        if cur is None or cur.revision != revision_anterior:
            return False
        self.store[snapshot.id] = replace(snapshot, revision=revision_anterior + 1)
        return True

    def revogar(self, *, escopo_id, revogado_em, motivo) -> bool:
        cur = self.store.get(escopo_id)
        if cur is None or cur.revogado_em is not None:
            return False
        self.store[escopo_id] = replace(
            cur, estado=EstadoEscopo.REVOGADO, revogado_em=revogado_em, motivo_revogacao=motivo
        )
        return True

    def encerrar_vigencia(self, *, escopo_id, vigencia_fim, revision_anterior) -> bool:
        cur = self.store.get(escopo_id)
        if cur is None or cur.revision != revision_anterior or cur.vigencia_fim is not None:
            return False
        self.store[escopo_id] = replace(
            cur, vigencia_fim=vigencia_fim, revision=revision_anterior + 1
        )
        return True

    def listar_confirmados_vigentes(self, *, tenant_id, grandeza, em) -> list[EscopoCMCSnapshot]:
        return [
            s
            for s in self.store.values()
            if s.tenant_id == tenant_id and s.grandeza == grandeza and s.consultavel(em)
        ]


def _input_cadastro(tenant_id, *, perfil="A", rbc=True, procedimento_id=None, forma=FormaCMC.ABSOLUTA, coef=None):
    return cadastrar_escopo.CadastrarEscopoInput(
        tenant_id=tenant_id,
        grandeza=Grandeza.MASSA,
        faixa=FaixaMedicao(Decimal("0"), Decimal("1000"), "g"),
        cmc_forma=forma,
        cmc_valor=Decimal("0.001"),
        cmc_unidade="g",
        perfil=perfil,
        rbc_solicitado=rbc,
        vigencia_inicio=_DT,
        correlation_id=uuid4(),
        cmc_coef_relativo=coef,
        procedimento_id=procedimento_id,
    )


class TestCadastrar:
    def test_perfil_a_cria_escopo_rbc(self) -> None:
        repo = FakeEscopoRepo()
        out = cadastrar_escopo.executar(
            _input_cadastro(uuid4(), perfil="A", rbc=True, procedimento_id=uuid4()), repo
        )
        assert out.snapshot.rbc_acreditado is True
        assert out.snapshot.versao == 1
        assert out.snapshot.estado is EstadoEscopo.CONFIRMADO

    def test_perfil_b_forca_rbc_false_anti_fraude(self) -> None:
        repo = FakeEscopoRepo()
        out = cadastrar_escopo.executar(
            _input_cadastro(uuid4(), perfil="B", rbc=True), repo
        )
        # B/C/D nunca RBC, mesmo solicitando — capacidade interna (ADR-0075)
        assert out.snapshot.rbc_acreditado is False

    def test_rbc_sem_procedimento_bloqueia(self) -> None:
        repo = FakeEscopoRepo()
        with pytest.raises(cadastrar_escopo.ProcedimentoObrigatorioParaRBCError):
            cadastrar_escopo.executar(
                _input_cadastro(uuid4(), perfil="A", rbc=True, procedimento_id=None), repo
            )

    def test_chave_duplicada_bloqueia(self) -> None:
        repo = FakeEscopoRepo()
        tid = uuid4()
        proc = uuid4()
        cadastrar_escopo.executar(_input_cadastro(tid, perfil="A", procedimento_id=proc), repo)
        with pytest.raises(cadastrar_escopo.ChaveDuplicadaError):
            cadastrar_escopo.executar(_input_cadastro(tid, perfil="A", procedimento_id=proc), repo)

    def test_relativa_sem_coef_levanta_no_input(self) -> None:
        with pytest.raises(ValueError, match="cmc_coef_relativo"):
            _input_cadastro(uuid4(), forma=FormaCMC.RELATIVA_LINEAR, coef=None, procedimento_id=uuid4())


class TestRevisar:
    def test_revisa_cria_v2_e_encerra_v1(self) -> None:
        repo = FakeEscopoRepo()
        tid = uuid4()
        v1 = cadastrar_escopo.executar(
            _input_cadastro(tid, perfil="A", procedimento_id=uuid4()), repo
        ).snapshot
        out = revisar_escopo.executar(
            revisar_escopo.RevisarEscopoInput(
                tenant_id=tid,
                escopo_id_atual=v1.id,
                cmc_forma=FormaCMC.ABSOLUTA,
                cmc_valor=Decimal("0.0005"),  # melhorou a CMC
                cmc_unidade="g",
                vigencia_inicio=_DT2,
                correlation_id=uuid4(),
            ),
            repo,
        )
        assert out.nova_versao.versao == 2
        assert out.nova_versao.cmc_valor == Decimal("0.0005")
        # v1 preservada (não apagada) e com vigência encerrada em _DT2
        v1_atual = repo.obter_por_id(v1.id)
        assert v1_atual is not None
        assert v1_atual.vigencia_fim == _DT2

    def test_revisar_inexistente_bloqueia(self) -> None:
        repo = FakeEscopoRepo()
        with pytest.raises(revisar_escopo.EscopoNaoEncontradoError):
            revisar_escopo.executar(
                revisar_escopo.RevisarEscopoInput(
                    tenant_id=uuid4(), escopo_id_atual=uuid4(),
                    cmc_forma=FormaCMC.ABSOLUTA, cmc_valor=Decimal("0.001"),
                    cmc_unidade="g", vigencia_inicio=_DT2, correlation_id=uuid4(),
                ),
                repo,
            )

    def test_revisar_revogado_bloqueia(self) -> None:
        repo = FakeEscopoRepo()
        tid = uuid4()
        v1 = cadastrar_escopo.executar(
            _input_cadastro(tid, perfil="A", procedimento_id=uuid4()), repo
        ).snapshot
        repo.revogar(escopo_id=v1.id, revogado_em=_DT2, motivo="revogado por supervisao CGCRE")
        with pytest.raises(revisar_escopo.EscopoNaoRevisavelError):
            revisar_escopo.executar(
                revisar_escopo.RevisarEscopoInput(
                    tenant_id=tid, escopo_id_atual=v1.id,
                    cmc_forma=FormaCMC.ABSOLUTA, cmc_valor=Decimal("0.001"),
                    cmc_unidade="g", vigencia_inicio=_DT2, correlation_id=uuid4(),
                ),
                repo,
            )


class TestRevogar:
    def test_revoga_com_sucesso(self) -> None:
        repo = FakeEscopoRepo()
        tid = uuid4()
        v1 = cadastrar_escopo.executar(
            _input_cadastro(tid, perfil="A", procedimento_id=uuid4()), repo
        ).snapshot
        out = revogar_escopo.executar(
            revogar_escopo.RevogarEscopoInput(
                tenant_id=tid, escopo_id=v1.id,
                motivo="revogado por reducao de escopo CGCRE 2026", revogado_em=_DT2,
            ),
            repo,
        )
        assert out.escopo_id == v1.id
        assert repo.obter_por_id(v1.id).estado is EstadoEscopo.REVOGADO

    def test_motivo_curto_bloqueia_no_input(self) -> None:
        with pytest.raises(ValueError, match=">= 10"):
            revogar_escopo.RevogarEscopoInput(
                tenant_id=uuid4(), escopo_id=uuid4(), motivo="curto", revogado_em=_DT2
            )

    def test_revogar_ja_revogado_bloqueia(self) -> None:
        repo = FakeEscopoRepo()
        tid = uuid4()
        v1 = cadastrar_escopo.executar(
            _input_cadastro(tid, perfil="A", procedimento_id=uuid4()), repo
        ).snapshot
        inp = revogar_escopo.RevogarEscopoInput(
            tenant_id=tid, escopo_id=v1.id,
            motivo="revogado por supervisao CGCRE 2026", revogado_em=_DT2,
        )
        revogar_escopo.executar(inp, repo)
        with pytest.raises(revogar_escopo.JaRevogadoError):
            revogar_escopo.executar(inp, repo)


def test_fake_repo_satisfaz_protocol() -> None:
    """Garante que o Fake implementa o Protocol (runtime_checkable)."""
    from src.domain.metrologia.escopos_cmc.repository import EscopoRepository

    assert isinstance(FakeEscopoRepo(), EscopoRepository)
