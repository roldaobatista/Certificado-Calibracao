"""Testes ReclamacaoCalibracao — US-CAL-018 (Batch J — T-CAL-096..098).

ISO 17025 cl. 7.9 + CDC art. 26.

Cobre:
- abrir: janela CDC 90d + relato + hash + cliente_referencia_hash.
- atribuir_rt: AC-CAL-018-2 (independencia revisor/conferente) + excecao.
- responder: decisao 3 valores + AC-CAL-018-4 (recall M5).
- Smoke E2E.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest
from src.application.metrologia.calibracao.reclamacao import (
    AbrirReclamacaoInput,
    AtribuirRTInput,
    ConflitoEstadoReclamacao,
    EstadoInvalidoParaTransicaoReclamacao,
    JanelaCDCExpirada,
    ReclamacaoNaoEncontrada,
    ResponderReclamacaoInput,
    RTNaoIndependenteDaCalibracaoOriginal,
    abrir,
    atribuir_rt,
    responder,
)
from src.domain.metrologia.calibracao.entities import (
    ReclamacaoCalibracaoSnapshot,
)
from src.domain.metrologia.calibracao.enums import (
    DecisaoReclamacao,
    EstadoReclamacao,
)

# ----------------------------------------------------------------------
# FakeReclamacaoCalibracaoRepository
# ----------------------------------------------------------------------


@dataclass
class FakeReclamacaoRepository:
    snapshots: dict[UUID, ReclamacaoCalibracaoSnapshot] = field(default_factory=dict)

    def obter_por_id(
        self, reclamacao_id: UUID
    ) -> ReclamacaoCalibracaoSnapshot | None:
        return self.snapshots.get(reclamacao_id)

    def salvar_nova(self, snapshot: ReclamacaoCalibracaoSnapshot) -> None:
        if snapshot.id in self.snapshots:
            raise ValueError(f"duplicate id {snapshot.id}")
        self.snapshots[snapshot.id] = snapshot

    def transitar_estado(
        self,
        snapshot: ReclamacaoCalibracaoSnapshot,
        estado_anterior: EstadoReclamacao,
    ) -> bool:
        atual = self.snapshots.get(snapshot.id)
        if atual is None or atual.estado != estado_anterior:
            return False
        self.snapshots[snapshot.id] = snapshot
        return True


# ----------------------------------------------------------------------
# Builders
# ----------------------------------------------------------------------


def _input_abrir_padrao(
    cert_emitido: datetime | None = None,
    aberta_em: datetime | None = None,
) -> AbrirReclamacaoInput:
    cert_emitido_real = cert_emitido or datetime(2026, 5, 1, 12, 0, tzinfo=UTC)
    aberta_real = aberta_em or datetime(2026, 5, 26, 12, 0, tzinfo=UTC)
    return AbrirReclamacaoInput(
        tenant_id=uuid4(),
        calibracao_id=uuid4(),
        certificado_id=uuid4(),
        cliente_referencia_hash="v01$" + "c" * 16,
        relato_canonicalizado=(
            "Cliente alega que valor reportado no certificado nao "
            "corresponde a leitura efetiva do instrumento; pediu re-medicao."
        ) * 2,  # >100 chars
        relato_hash="v01$relato123",
        aberta_em=aberta_real,
        certificado_emitido_em=cert_emitido_real,
        prazo_resposta_dia_util=15,
        correlation_id=uuid4(),
    )


def _abrir_recebida(repo: FakeReclamacaoRepository) -> UUID:
    out = abrir(_input_abrir_padrao(), repo)
    return out.snapshot.id


# ======================================================================
# abrir
# ======================================================================


class TestAbrir:
    def test_happy(self) -> None:
        repo = FakeReclamacaoRepository()
        out = abrir(_input_abrir_padrao(), repo)
        assert out.snapshot.estado == EstadoReclamacao.RECEBIDA
        assert out.snapshot.decisao is None
        assert out.snapshot.respondida_em is None
        assert out.snapshot.rt_atribuido_user_id_hash == ""

    def test_janela_cdc_90d_expirou(self) -> None:
        repo = FakeReclamacaoRepository()
        cert = datetime(2026, 2, 1, 12, 0, tzinfo=UTC)
        aberta = datetime(2026, 5, 26, 12, 0, tzinfo=UTC)  # ~114 dias depois
        with pytest.raises(JanelaCDCExpirada, match="90 dias"):
            abrir(
                _input_abrir_padrao(cert_emitido=cert, aberta_em=aberta),
                repo,
            )

    def test_janela_cdc_borda_exata_90d_aceita(self) -> None:
        """Dia 90 inclusive deve aceitar; dia 91 deve recusar."""
        repo = FakeReclamacaoRepository()
        cert = datetime(2026, 2, 1, 12, 0, tzinfo=UTC)
        aberta_dentro = cert + timedelta(days=90)
        out = abrir(
            _input_abrir_padrao(cert_emitido=cert, aberta_em=aberta_dentro),
            repo,
        )
        assert out.snapshot.estado == EstadoReclamacao.RECEBIDA

    def test_janela_cdc_91d_recusa(self) -> None:
        repo = FakeReclamacaoRepository()
        cert = datetime(2026, 2, 1, 12, 0, tzinfo=UTC)
        aberta_fora = cert + timedelta(days=91)
        with pytest.raises(JanelaCDCExpirada):
            abrir(
                _input_abrir_padrao(cert_emitido=cert, aberta_em=aberta_fora),
                repo,
            )

    def test_relato_curto_recusa(self) -> None:
        with pytest.raises(ValueError, match="relato_canonicalizado"):
            AbrirReclamacaoInput(
                tenant_id=uuid4(),
                calibracao_id=uuid4(),
                certificado_id=uuid4(),
                cliente_referencia_hash="v01$x",
                relato_canonicalizado="curto demais",
                relato_hash="v01$x",
                aberta_em=datetime(2026, 5, 26, 12, 0, tzinfo=UTC),
                certificado_emitido_em=datetime(2026, 5, 1, 12, 0, tzinfo=UTC),
                prazo_resposta_dia_util=15,
                correlation_id=uuid4(),
            )

    def test_aberta_em_sem_tz_recusa(self) -> None:
        with pytest.raises(ValueError, match="aberta_em"):
            AbrirReclamacaoInput(
                tenant_id=uuid4(),
                calibracao_id=uuid4(),
                certificado_id=uuid4(),
                cliente_referencia_hash="v01$x",
                relato_canonicalizado="a" * 120,
                relato_hash="v01$x",
                aberta_em=datetime(2026, 5, 26, 12, 0),  # sem tz
                certificado_emitido_em=datetime(2026, 5, 1, 12, 0, tzinfo=UTC),
                prazo_resposta_dia_util=15,
                correlation_id=uuid4(),
            )

    def test_cliente_referencia_hash_vazio_recusa(self) -> None:
        with pytest.raises(ValueError, match="cliente_referencia_hash"):
            AbrirReclamacaoInput(
                tenant_id=uuid4(),
                calibracao_id=uuid4(),
                certificado_id=uuid4(),
                cliente_referencia_hash="",
                relato_canonicalizado="a" * 120,
                relato_hash="v01$x",
                aberta_em=datetime(2026, 5, 26, 12, 0, tzinfo=UTC),
                certificado_emitido_em=datetime(2026, 5, 1, 12, 0, tzinfo=UTC),
                prazo_resposta_dia_util=15,
                correlation_id=uuid4(),
            )


# ======================================================================
# atribuir_rt
# ======================================================================


class TestAtribuirRT:
    def test_happy_rt_independente(self) -> None:
        repo = FakeReclamacaoRepository()
        reclamacao_id = _abrir_recebida(repo)
        rt_independente = "v01$" + "z" * 16
        out = atribuir_rt(
            AtribuirRTInput(
                reclamacao_id=reclamacao_id,
                rt_atribuido_user_id_hash=rt_independente,
                revisor_original_id_hash="v01$" + "r" * 16,
                conferente_original_id_hash="v01$" + "c" * 16,
                permitir_mesmo_rt_excecao=False,
            ),
            repo,
        )
        assert out.snapshot.estado == EstadoReclamacao.EM_ANALISE
        assert out.snapshot.rt_atribuido_user_id_hash == rt_independente

    def test_rt_eh_revisor_original_bloqueia_AC_018_2(self) -> None:
        repo = FakeReclamacaoRepository()
        reclamacao_id = _abrir_recebida(repo)
        revisor = "v01$" + "r" * 16
        with pytest.raises(RTNaoIndependenteDaCalibracaoOriginal):
            atribuir_rt(
                AtribuirRTInput(
                    reclamacao_id=reclamacao_id,
                    rt_atribuido_user_id_hash=revisor,  # coincide com revisor
                    revisor_original_id_hash=revisor,
                    conferente_original_id_hash="v01$" + "c" * 16,
                    permitir_mesmo_rt_excecao=False,
                ),
                repo,
            )

    def test_rt_eh_conferente_original_bloqueia_AC_018_2(self) -> None:
        repo = FakeReclamacaoRepository()
        reclamacao_id = _abrir_recebida(repo)
        conferente = "v01$" + "c" * 16
        with pytest.raises(RTNaoIndependenteDaCalibracaoOriginal):
            atribuir_rt(
                AtribuirRTInput(
                    reclamacao_id=reclamacao_id,
                    rt_atribuido_user_id_hash=conferente,
                    revisor_original_id_hash="v01$" + "r" * 16,
                    conferente_original_id_hash=conferente,
                    permitir_mesmo_rt_excecao=False,
                ),
                repo,
            )

    def test_rt_coincide_com_excecao_aceita(self) -> None:
        """Lab pequeno com unico RT — excecao documentada permite."""
        repo = FakeReclamacaoRepository()
        reclamacao_id = _abrir_recebida(repo)
        unico_rt = "v01$" + "r" * 16
        out = atribuir_rt(
            AtribuirRTInput(
                reclamacao_id=reclamacao_id,
                rt_atribuido_user_id_hash=unico_rt,
                revisor_original_id_hash=unico_rt,  # coincide
                conferente_original_id_hash="v01$" + "c" * 16,
                permitir_mesmo_rt_excecao=True,  # excecao documentada
            ),
            repo,
        )
        assert out.snapshot.estado == EstadoReclamacao.EM_ANALISE

    def test_reclamacao_nao_encontrada(self) -> None:
        repo = FakeReclamacaoRepository()
        with pytest.raises(ReclamacaoNaoEncontrada):
            atribuir_rt(
                AtribuirRTInput(
                    reclamacao_id=uuid4(),
                    rt_atribuido_user_id_hash="v01$" + "z" * 16,
                    revisor_original_id_hash="v01$" + "r" * 16,
                    conferente_original_id_hash="v01$" + "c" * 16,
                    permitir_mesmo_rt_excecao=False,
                ),
                repo,
            )

    def test_estado_em_analise_recusa_segunda_atribuicao(self) -> None:
        repo = FakeReclamacaoRepository()
        reclamacao_id = _abrir_recebida(repo)
        atribuir_rt(
            AtribuirRTInput(
                reclamacao_id=reclamacao_id,
                rt_atribuido_user_id_hash="v01$" + "z" * 16,
                revisor_original_id_hash="v01$" + "r" * 16,
                conferente_original_id_hash="v01$" + "c" * 16,
                permitir_mesmo_rt_excecao=False,
            ),
            repo,
        )
        # Tenta atribuir de novo — esta em EM_ANALISE
        with pytest.raises(
            EstadoInvalidoParaTransicaoReclamacao, match="RECEBIDA"
        ):
            atribuir_rt(
                AtribuirRTInput(
                    reclamacao_id=reclamacao_id,
                    rt_atribuido_user_id_hash="v01$" + "novoRT16chars",
                    revisor_original_id_hash="v01$" + "r" * 16,
                    conferente_original_id_hash="v01$" + "c" * 16,
                    permitir_mesmo_rt_excecao=False,
                ),
                repo,
            )

    def test_input_sem_hashes_obrigatorios_recusa(self) -> None:
        with pytest.raises(ValueError, match="revisor"):
            AtribuirRTInput(
                reclamacao_id=uuid4(),
                rt_atribuido_user_id_hash="v01$z",
                revisor_original_id_hash="",  # falta
                conferente_original_id_hash="v01$c",
                permitir_mesmo_rt_excecao=False,
            )


# ======================================================================
# responder
# ======================================================================


def _ate_em_analise(repo: FakeReclamacaoRepository) -> UUID:
    reclamacao_id = _abrir_recebida(repo)
    atribuir_rt(
        AtribuirRTInput(
            reclamacao_id=reclamacao_id,
            rt_atribuido_user_id_hash="v01$" + "z" * 16,
            revisor_original_id_hash="v01$" + "r" * 16,
            conferente_original_id_hash="v01$" + "c" * 16,
            permitir_mesmo_rt_excecao=False,
        ),
        repo,
    )
    return reclamacao_id


class TestResponder:
    def test_happy_improcedente(self) -> None:
        repo = FakeReclamacaoRepository()
        reclamacao_id = _ate_em_analise(repo)
        out = responder(
            ResponderReclamacaoInput(
                reclamacao_id=reclamacao_id,
                resposta_canonicalizada=(
                    "Apos analise tecnica do RT independente, conclui-se que "
                    "o procedimento foi seguido corretamente conforme NIT-DICLA-030; "
                    "alegacao do cliente nao se sustenta tecnicamente."
                ),
                resposta_hash="v01$resp1",
                decisao=DecisaoReclamacao.IMPROCEDENTE,
                respondida_em=datetime(2026, 6, 5, 14, 0, tzinfo=UTC),
            ),
            repo,
        )
        assert out.snapshot.estado == EstadoReclamacao.RESPONDIDA
        assert out.snapshot.decisao == DecisaoReclamacao.IMPROCEDENTE
        assert not out.dispara_recall_m5

    def test_procedente_recall_dispara_flag_recall_m5(self) -> None:
        """AC-CAL-018-4: PROCEDENTE_RECALL sinaliza saga recall M5."""
        repo = FakeReclamacaoRepository()
        reclamacao_id = _ate_em_analise(repo)
        out = responder(
            ResponderReclamacaoInput(
                reclamacao_id=reclamacao_id,
                resposta_canonicalizada=(
                    "Verificou-se que padrao utilizado estava fora do prazo de "
                    "verificacao na data do servico — cert sera revogado e "
                    "calibracao refeita com padrao adequado."
                ),
                resposta_hash="v01$resp_recall",
                decisao=DecisaoReclamacao.PROCEDENTE_RECALL,
                respondida_em=datetime(2026, 6, 5, 14, 0, tzinfo=UTC),
            ),
            repo,
        )
        assert out.snapshot.decisao == DecisaoReclamacao.PROCEDENTE_RECALL
        assert out.dispara_recall_m5

    def test_procedente_errata_nao_dispara_recall(self) -> None:
        repo = FakeReclamacaoRepository()
        reclamacao_id = _ate_em_analise(repo)
        out = responder(
            ResponderReclamacaoInput(
                reclamacao_id=reclamacao_id,
                resposta_canonicalizada=(
                    "Verificou-se erro tipografico em valor reportado; sera "
                    "emitida errata pontual mantendo numero do certificado original "
                    "conforme procedimento de errata cl. 7.9."
                ),
                resposta_hash="v01$resp_errata",
                decisao=DecisaoReclamacao.PROCEDENTE_ERRATA,
                respondida_em=datetime(2026, 6, 5, 14, 0, tzinfo=UTC),
            ),
            repo,
        )
        assert out.snapshot.decisao == DecisaoReclamacao.PROCEDENTE_ERRATA
        assert not out.dispara_recall_m5

    def test_resposta_curta_recusa(self) -> None:
        with pytest.raises(ValueError, match="resposta_canonicalizada"):
            ResponderReclamacaoInput(
                reclamacao_id=uuid4(),
                resposta_canonicalizada="curta",
                resposta_hash="v01$x",
                decisao=DecisaoReclamacao.IMPROCEDENTE,
                respondida_em=datetime(2026, 6, 5, 14, 0, tzinfo=UTC),
            )

    def test_respondida_em_sem_tz_recusa(self) -> None:
        with pytest.raises(ValueError, match="respondida_em"):
            ResponderReclamacaoInput(
                reclamacao_id=uuid4(),
                resposta_canonicalizada="a" * 120,
                resposta_hash="v01$x",
                decisao=DecisaoReclamacao.IMPROCEDENTE,
                respondida_em=datetime(2026, 6, 5, 14, 0),  # sem tz
            )

    def test_estado_recebida_recusa(self) -> None:
        """Nao pode responder sem atribuir RT antes."""
        repo = FakeReclamacaoRepository()
        reclamacao_id = _abrir_recebida(repo)  # esta em RECEBIDA
        with pytest.raises(
            EstadoInvalidoParaTransicaoReclamacao, match="EM_ANALISE"
        ):
            responder(
                ResponderReclamacaoInput(
                    reclamacao_id=reclamacao_id,
                    resposta_canonicalizada="a" * 120,
                    resposta_hash="v01$x",
                    decisao=DecisaoReclamacao.IMPROCEDENTE,
                    respondida_em=datetime(2026, 6, 5, 14, 0, tzinfo=UTC),
                ),
                repo,
            )

    def test_conflito_estado(self) -> None:
        repo = FakeReclamacaoRepository()
        reclamacao_id = _ate_em_analise(repo)
        # Simula corrida: outro processo muda pra RESPONDIDA
        snap = repo.snapshots[reclamacao_id]
        repo.snapshots[reclamacao_id] = replace(
            snap, estado=EstadoReclamacao.RESPONDIDA
        )
        # Tenta responder normalmente — vai obter RESPONDIDA -> EstadoInvalido
        with pytest.raises(
            EstadoInvalidoParaTransicaoReclamacao, match="EM_ANALISE"
        ):
            responder(
                ResponderReclamacaoInput(
                    reclamacao_id=reclamacao_id,
                    resposta_canonicalizada="a" * 120,
                    resposta_hash="v01$x",
                    decisao=DecisaoReclamacao.IMPROCEDENTE,
                    respondida_em=datetime(2026, 6, 5, 14, 0, tzinfo=UTC),
                ),
                repo,
            )


def test_conflito_estado_via_mock_simula_race() -> None:
    """ConflitoEstadoReclamacao quando estado muda entre obter e transitar."""
    repo = FakeReclamacaoRepository()
    reclamacao_id = _ate_em_analise(repo)
    snap = repo.snapshots[reclamacao_id]
    obter_original = repo.obter_por_id
    chamadas = [0]

    def obter_mutante(rid: UUID) -> ReclamacaoCalibracaoSnapshot | None:
        chamadas[0] += 1
        if chamadas[0] == 1:
            # 1a chamada: retorna EM_ANALISE
            return replace(snap, estado=EstadoReclamacao.EM_ANALISE)
        return obter_original(rid)

    repo.obter_por_id = obter_mutante  # type: ignore[method-assign]
    # Estado real no repo: muda pra RESPONDIDA antes do UPDATE
    repo.snapshots[reclamacao_id] = replace(
        snap, estado=EstadoReclamacao.RESPONDIDA
    )
    with pytest.raises(ConflitoEstadoReclamacao):
        responder(
            ResponderReclamacaoInput(
                reclamacao_id=reclamacao_id,
                resposta_canonicalizada="a" * 120,
                resposta_hash="v01$x",
                decisao=DecisaoReclamacao.IMPROCEDENTE,
                respondida_em=datetime(2026, 6, 5, 14, 0, tzinfo=UTC),
            ),
            repo,
        )


# ======================================================================
# Fluxo completo
# ======================================================================


def test_fluxo_completo_abrir_atribuir_responder() -> None:
    """Smoke E2E: abrir -> atribuir_rt -> responder (PROCEDENTE_RECALL)."""
    repo = FakeReclamacaoRepository()
    inp_abrir = _input_abrir_padrao()
    out1 = abrir(inp_abrir, repo)
    assert out1.snapshot.estado == EstadoReclamacao.RECEBIDA

    rt_hash = "v01$" + "z" * 16
    out2 = atribuir_rt(
        AtribuirRTInput(
            reclamacao_id=out1.snapshot.id,
            rt_atribuido_user_id_hash=rt_hash,
            revisor_original_id_hash="v01$" + "r" * 16,
            conferente_original_id_hash="v01$" + "c" * 16,
            permitir_mesmo_rt_excecao=False,
        ),
        repo,
    )
    assert out2.snapshot.estado == EstadoReclamacao.EM_ANALISE
    assert out2.snapshot.rt_atribuido_user_id_hash == rt_hash

    out3 = responder(
        ResponderReclamacaoInput(
            reclamacao_id=out1.snapshot.id,
            resposta_canonicalizada=(
                "Reclamacao procedente — padrao estava fora de prazo de "
                "verificacao; certificado sera revogado e calibracao refeita."
            ),
            resposta_hash="v01$resp",
            decisao=DecisaoReclamacao.PROCEDENTE_RECALL,
            respondida_em=datetime(2026, 6, 10, 14, 0, tzinfo=UTC),
        ),
        repo,
    )
    assert out3.snapshot.estado == EstadoReclamacao.RESPONDIDA
    assert out3.snapshot.estado.terminal
    assert out3.dispara_recall_m5
