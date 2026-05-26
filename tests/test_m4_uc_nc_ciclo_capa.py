"""Testes ciclo CAPA NC (P4 Fase 5 Batch H — T-CAL-091..095).

US-CAL-013/014 — cl. 7.10 + cl. 8.7 + INV-CAL-NC-002/003 + P-CAL-A2.

Cobertura:
- abrir: XOR origem + descricao + hash + responsavel_acao_user_id_hash.
- definir_acao_corretiva: CONTIDA -> ACAO_CORRETIVA_DEFINIDA.
- executar_acao: ACAO_CORRETIVA_DEFINIDA -> ACAO_EXECUTADA + INV-NC-002/003.
- verificar_eficacia: ACAO_EXECUTADA -> EFICACIA_VERIFICADA.
- fechar: EFICACIA_VERIFICADA -> FECHADA.
- reabrir: FECHADA -> CONTIDA (cl. 8.7.2).
- Fluxo completo (smoke) + estado-machine guards.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest
from src.application.metrologia.calibracao.nao_conformidade import (
    AbrirNCInput,
    ConflitoEstadoNaoConformidade,
    DefinirAcaoCorretivaInput,
    EstadoInvalidoParaTransicao,
    ExecutarAcaoInput,
    FecharNCInput,
    NaoConformidadeNaoEncontrada,
    ReabrirNCInput,
    VerificarEficaciaInput,
    abrir,
    definir_acao_corretiva,
    executar_acao,
    fechar,
    reabrir,
    verificar_eficacia,
)
from src.domain.metrologia.calibracao.entities import NaoConformidadeSnapshot
from src.domain.metrologia.calibracao.enums import (
    AcaoCorretivaTipo,
    ClienteNotificadoVia,
    DecisaoContinuarOuParar,
    EstadoNaoConformidade,
)

# ----------------------------------------------------------------------
# FakeNaoConformidadeRepository
# ----------------------------------------------------------------------


@dataclass
class FakeNCRepository:
    """In-memory repo de NC — implementa NaoConformidadeRepository."""

    snapshots: dict[UUID, NaoConformidadeSnapshot] = field(default_factory=dict)

    def obter_por_id(self, nc_id: UUID) -> NaoConformidadeSnapshot | None:
        return self.snapshots.get(nc_id)

    def salvar_novo(self, snapshot: NaoConformidadeSnapshot) -> None:
        if snapshot.id in self.snapshots:
            raise ValueError(f"duplicate id {snapshot.id}")
        self.snapshots[snapshot.id] = snapshot

    def transitar_estado(
        self,
        snapshot: NaoConformidadeSnapshot,
        estado_anterior: EstadoNaoConformidade,
    ) -> bool:
        atual = self.snapshots.get(snapshot.id)
        if atual is None or atual.estado != estado_anterior:
            return False
        self.snapshots[snapshot.id] = snapshot
        return True


# ----------------------------------------------------------------------
# Builders
# ----------------------------------------------------------------------


def _abrir_padrao(
    repo: FakeNCRepository, origem_cal: bool = True
) -> UUID:
    """Abre NC em CONTIDA e retorna seu id."""
    out = abrir(
        AbrirNCInput(
            tenant_id=uuid4(),
            calibracao_id=uuid4() if origem_cal else None,
            origem_proficiencia_id=None if origem_cal else uuid4(),
            descricao_canonicalizada=(
                "Desvio significativo detectado em ponto 5kg apos verificacao."
            ),
            descricao_hash="v01$" + "a" * 16,
            responsavel_acao_user_id=uuid4(),
            responsavel_acao_user_id_hash="v01$" + "b" * 16,
            correlation_id=uuid4(),
        ),
        repo,
    )
    return out.snapshot.id


# ======================================================================
# abrir
# ======================================================================


class TestAbrir:
    def test_happy_origem_calibracao(self) -> None:
        repo = FakeNCRepository()
        out = abrir(
            AbrirNCInput(
                tenant_id=uuid4(),
                calibracao_id=uuid4(),
                origem_proficiencia_id=None,
                descricao_canonicalizada=(
                    "NC: leitura inconsistente em ponto 10kg apos 5 medicoes."
                ),
                descricao_hash="v01$abcdefghij",
                responsavel_acao_user_id=uuid4(),
                responsavel_acao_user_id_hash="v01$" + "x" * 16,
                correlation_id=uuid4(),
            ),
            repo,
        )
        assert out.snapshot.estado == EstadoNaoConformidade.CONTIDA
        assert out.snapshot.calibracao_id is not None
        assert out.snapshot.origem_proficiencia_id is None
        assert out.snapshot.decisao_continuar_ou_parar == (
            DecisaoContinuarOuParar.A_DEFINIR
        )
        assert out.snapshot.acao_corretiva_tipo is None

    def test_happy_origem_proficiencia(self) -> None:
        repo = FakeNCRepository()
        out = abrir(
            AbrirNCInput(
                tenant_id=uuid4(),
                calibracao_id=None,
                origem_proficiencia_id=uuid4(),
                descricao_canonicalizada=(
                    "Resultado UNACCEPTABLE em rodada PT-2026-Q1 massa 0-50kg."
                ),
                descricao_hash="v01$abcdefghij",
                responsavel_acao_user_id=uuid4(),
                responsavel_acao_user_id_hash="v01$" + "x" * 16,
                correlation_id=uuid4(),
            ),
            repo,
        )
        assert out.snapshot.calibracao_id is None
        assert out.snapshot.origem_proficiencia_id is not None

    def test_xor_origem_ambas_recusa(self) -> None:
        with pytest.raises(ValueError, match="XOR"):
            AbrirNCInput(
                tenant_id=uuid4(),
                calibracao_id=uuid4(),
                origem_proficiencia_id=uuid4(),  # ambas
                descricao_canonicalizada="a" * 50,
                descricao_hash="v01$x",
                responsavel_acao_user_id=uuid4(),
                responsavel_acao_user_id_hash="v01$y",
                correlation_id=uuid4(),
            )

    def test_xor_origem_nenhuma_recusa(self) -> None:
        with pytest.raises(ValueError, match="XOR"):
            AbrirNCInput(
                tenant_id=uuid4(),
                calibracao_id=None,
                origem_proficiencia_id=None,
                descricao_canonicalizada="a" * 50,
                descricao_hash="v01$x",
                responsavel_acao_user_id=uuid4(),
                responsavel_acao_user_id_hash="v01$y",
                correlation_id=uuid4(),
            )

    def test_descricao_curta_recusa(self) -> None:
        with pytest.raises(ValueError, match="descricao_canonicalizada"):
            AbrirNCInput(
                tenant_id=uuid4(),
                calibracao_id=uuid4(),
                origem_proficiencia_id=None,
                descricao_canonicalizada="curta",
                descricao_hash="v01$x",
                responsavel_acao_user_id=uuid4(),
                responsavel_acao_user_id_hash="v01$y",
                correlation_id=uuid4(),
            )

    def test_hash_responsavel_vazio_recusa(self) -> None:
        with pytest.raises(ValueError, match="responsavel_acao_user_id_hash"):
            AbrirNCInput(
                tenant_id=uuid4(),
                calibracao_id=uuid4(),
                origem_proficiencia_id=None,
                descricao_canonicalizada="a" * 50,
                descricao_hash="v01$x",
                responsavel_acao_user_id=uuid4(),
                responsavel_acao_user_id_hash="",
                correlation_id=uuid4(),
            )


# ======================================================================
# definir_acao_corretiva
# ======================================================================


class TestDefinirAcaoCorretiva:
    def test_happy_contida_para_acao_definida(self) -> None:
        repo = FakeNCRepository()
        nc_id = _abrir_padrao(repo)
        out = definir_acao_corretiva(
            DefinirAcaoCorretivaInput(
                nc_id=nc_id,
                causa_raiz_canonicalizada=(
                    "Padrao de massa estava fora do prazo de verificacao."
                ),
                causa_raiz_hash="v01$causa1",
                acao_corretiva_descricao_hash="v01$acao1",
                acao_corretiva_tipo=AcaoCorretivaTipo.RE_EXECUTAR,
            ),
            repo,
        )
        assert out.snapshot.estado == EstadoNaoConformidade.ACAO_CORRETIVA_DEFINIDA
        assert out.snapshot.acao_corretiva_tipo == AcaoCorretivaTipo.RE_EXECUTAR
        assert out.snapshot.causa_raiz_hash == "v01$causa1"

    def test_nc_nao_encontrada(self) -> None:
        repo = FakeNCRepository()
        with pytest.raises(NaoConformidadeNaoEncontrada):
            definir_acao_corretiva(
                DefinirAcaoCorretivaInput(
                    nc_id=uuid4(),
                    causa_raiz_canonicalizada="a" * 50,
                    causa_raiz_hash="v01$x",
                    acao_corretiva_descricao_hash="v01$y",
                    acao_corretiva_tipo=AcaoCorretivaTipo.RE_EXECUTAR,
                ),
                repo,
            )

    def test_estado_invalido_recusa(self) -> None:
        repo = FakeNCRepository()
        nc_id = _abrir_padrao(repo)
        # Transita pra ACAO_CORRETIVA_DEFINIDA
        definir_acao_corretiva(
            DefinirAcaoCorretivaInput(
                nc_id=nc_id,
                causa_raiz_canonicalizada="a" * 50,
                causa_raiz_hash="v01$x",
                acao_corretiva_descricao_hash="v01$y",
                acao_corretiva_tipo=AcaoCorretivaTipo.RE_EXECUTAR,
            ),
            repo,
        )
        # Segunda chamada — esta em ACAO_CORRETIVA_DEFINIDA
        with pytest.raises(EstadoInvalidoParaTransicao, match="CONTIDA"):
            definir_acao_corretiva(
                DefinirAcaoCorretivaInput(
                    nc_id=nc_id,
                    causa_raiz_canonicalizada="a" * 50,
                    causa_raiz_hash="v01$x2",
                    acao_corretiva_descricao_hash="v01$y2",
                    acao_corretiva_tipo=AcaoCorretivaTipo.AJUSTE_ADMINISTRATIVO,
                ),
                repo,
            )

    def test_causa_raiz_curta_recusa(self) -> None:
        with pytest.raises(ValueError, match="causa_raiz_canonicalizada"):
            DefinirAcaoCorretivaInput(
                nc_id=uuid4(),
                causa_raiz_canonicalizada="curta",
                causa_raiz_hash="v01$x",
                acao_corretiva_descricao_hash="v01$y",
                acao_corretiva_tipo=AcaoCorretivaTipo.RE_EXECUTAR,
            )


# ======================================================================
# executar_acao (INV-CAL-NC-002/003)
# ======================================================================


class TestExecutarAcao:
    def _ate_acao_definida(self, repo: FakeNCRepository) -> UUID:
        nc_id = _abrir_padrao(repo)
        definir_acao_corretiva(
            DefinirAcaoCorretivaInput(
                nc_id=nc_id,
                causa_raiz_canonicalizada="a" * 50,
                causa_raiz_hash="v01$x",
                acao_corretiva_descricao_hash="v01$y",
                acao_corretiva_tipo=AcaoCorretivaTipo.RE_EXECUTAR,
            ),
            repo,
        )
        return nc_id

    def test_happy_continuar_com_controle(self) -> None:
        repo = FakeNCRepository()
        nc_id = self._ate_acao_definida(repo)
        out = executar_acao(
            ExecutarAcaoInput(
                nc_id=nc_id,
                decisao_continuar_ou_parar=DecisaoContinuarOuParar.CONTINUAR_COM_CONTROLE,
                acao_executada_em=datetime(2026, 5, 26, 14, 0, tzinfo=UTC),
                cliente_notificado_em=None,
                cliente_notificado_via=None,
                cliente_notificado_documento_id=None,
            ),
            repo,
        )
        assert out.snapshot.estado == EstadoNaoConformidade.ACAO_EXECUTADA
        # CONTINUAR_COM_CONTROLE nao exige notificacao cliente
        assert out.snapshot.cliente_notificado_em is None

    def test_happy_parar_trabalho_com_notificacao(self) -> None:
        repo = FakeNCRepository()
        nc_id = self._ate_acao_definida(repo)
        out = executar_acao(
            ExecutarAcaoInput(
                nc_id=nc_id,
                decisao_continuar_ou_parar=DecisaoContinuarOuParar.PARAR_TRABALHO,
                acao_executada_em=datetime(2026, 5, 26, 14, 0, tzinfo=UTC),
                cliente_notificado_em=datetime(2026, 5, 26, 14, 30, tzinfo=UTC),
                cliente_notificado_via=ClienteNotificadoVia.EMAIL_PORTAL,
                cliente_notificado_documento_id=uuid4(),
            ),
            repo,
        )
        assert out.snapshot.estado == EstadoNaoConformidade.ACAO_EXECUTADA
        assert out.snapshot.cliente_notificado_em is not None
        assert out.snapshot.cliente_notificado_via == ClienteNotificadoVia.EMAIL_PORTAL

    def test_decisao_a_definir_recusa_inv_nc_002(self) -> None:
        """INV-CAL-NC-002: A_DEFINIR proibido pre-ACAO_EXECUTADA."""
        with pytest.raises(ValueError, match="INV-CAL-NC-002"):
            ExecutarAcaoInput(
                nc_id=uuid4(),
                decisao_continuar_ou_parar=DecisaoContinuarOuParar.A_DEFINIR,
                acao_executada_em=datetime(2026, 5, 26, 14, 0, tzinfo=UTC),
                cliente_notificado_em=None,
                cliente_notificado_via=None,
                cliente_notificado_documento_id=None,
            )

    def test_parar_trabalho_sem_notificacao_recusa_inv_nc_003(self) -> None:
        """INV-CAL-NC-003: PARAR_TRABALHO exige cliente_notificado_em."""
        with pytest.raises(ValueError, match="INV-CAL-NC-003"):
            ExecutarAcaoInput(
                nc_id=uuid4(),
                decisao_continuar_ou_parar=DecisaoContinuarOuParar.PARAR_TRABALHO,
                acao_executada_em=datetime(2026, 5, 26, 14, 0, tzinfo=UTC),
                cliente_notificado_em=None,  # falta
                cliente_notificado_via=ClienteNotificadoVia.EMAIL_PORTAL,
                cliente_notificado_documento_id=uuid4(),
            )

    def test_parar_trabalho_sem_via_recusa(self) -> None:
        with pytest.raises(ValueError, match="cliente_notificado_via"):
            ExecutarAcaoInput(
                nc_id=uuid4(),
                decisao_continuar_ou_parar=DecisaoContinuarOuParar.PARAR_TRABALHO,
                acao_executada_em=datetime(2026, 5, 26, 14, 0, tzinfo=UTC),
                cliente_notificado_em=datetime(2026, 5, 26, 14, 30, tzinfo=UTC),
                cliente_notificado_via=None,  # falta
                cliente_notificado_documento_id=uuid4(),
            )

    def test_datetime_sem_tz_recusa(self) -> None:
        with pytest.raises(ValueError, match="tz-aware"):
            ExecutarAcaoInput(
                nc_id=uuid4(),
                decisao_continuar_ou_parar=DecisaoContinuarOuParar.CONTINUAR_COM_CONTROLE,
                acao_executada_em=datetime(2026, 5, 26, 14, 0),  # sem tz
                cliente_notificado_em=None,
                cliente_notificado_via=None,
                cliente_notificado_documento_id=None,
            )

    def test_estado_contida_recusa(self) -> None:
        repo = FakeNCRepository()
        nc_id = _abrir_padrao(repo)  # esta em CONTIDA
        with pytest.raises(
            EstadoInvalidoParaTransicao, match="ACAO_CORRETIVA_DEFINIDA"
        ):
            executar_acao(
                ExecutarAcaoInput(
                    nc_id=nc_id,
                    decisao_continuar_ou_parar=DecisaoContinuarOuParar.CONTINUAR_COM_CONTROLE,
                    acao_executada_em=datetime(2026, 5, 26, 14, 0, tzinfo=UTC),
                    cliente_notificado_em=None,
                    cliente_notificado_via=None,
                    cliente_notificado_documento_id=None,
                ),
                repo,
            )


# ======================================================================
# verificar_eficacia + fechar
# ======================================================================


def _ate_acao_executada(repo: FakeNCRepository) -> UUID:
    nc_id = _abrir_padrao(repo)
    definir_acao_corretiva(
        DefinirAcaoCorretivaInput(
            nc_id=nc_id,
            causa_raiz_canonicalizada="a" * 50,
            causa_raiz_hash="v01$x",
            acao_corretiva_descricao_hash="v01$y",
            acao_corretiva_tipo=AcaoCorretivaTipo.RE_EXECUTAR,
        ),
        repo,
    )
    executar_acao(
        ExecutarAcaoInput(
            nc_id=nc_id,
            decisao_continuar_ou_parar=DecisaoContinuarOuParar.CONTINUAR_COM_CONTROLE,
            acao_executada_em=datetime(2026, 5, 26, 14, 0, tzinfo=UTC),
            cliente_notificado_em=None,
            cliente_notificado_via=None,
            cliente_notificado_documento_id=None,
        ),
        repo,
    )
    return nc_id


class TestVerificarEficaciaEFechar:
    def test_verificar_eficacia_happy(self) -> None:
        repo = FakeNCRepository()
        nc_id = _ate_acao_executada(repo)
        verificador = uuid4()
        out = verificar_eficacia(
            VerificarEficaciaInput(
                nc_id=nc_id,
                eficacia_verificada_em=datetime(2026, 5, 27, 10, 0, tzinfo=UTC),
                eficacia_verificada_por_user_id=verificador,
            ),
            repo,
        )
        assert out.snapshot.estado == EstadoNaoConformidade.EFICACIA_VERIFICADA
        assert out.snapshot.eficacia_verificada_por_user_id == verificador

    def test_fechar_happy(self) -> None:
        repo = FakeNCRepository()
        nc_id = _ate_acao_executada(repo)
        verificar_eficacia(
            VerificarEficaciaInput(
                nc_id=nc_id,
                eficacia_verificada_em=datetime(2026, 5, 27, 10, 0, tzinfo=UTC),
                eficacia_verificada_por_user_id=uuid4(),
            ),
            repo,
        )
        out = fechar(FecharNCInput(nc_id=nc_id), repo)
        assert out.snapshot.estado == EstadoNaoConformidade.FECHADA
        assert out.snapshot.estado.terminal

    def test_fechar_sem_verificar_recusa(self) -> None:
        repo = FakeNCRepository()
        nc_id = _ate_acao_executada(repo)  # esta em ACAO_EXECUTADA, nao verificada
        with pytest.raises(
            EstadoInvalidoParaTransicao, match="EFICACIA_VERIFICADA"
        ):
            fechar(FecharNCInput(nc_id=nc_id), repo)


# ======================================================================
# reabrir (cl. 8.7.2)
# ======================================================================


class TestReabrir:
    def _fluxo_ate_fechada(self, repo: FakeNCRepository) -> UUID:
        nc_id = _ate_acao_executada(repo)
        verificar_eficacia(
            VerificarEficaciaInput(
                nc_id=nc_id,
                eficacia_verificada_em=datetime(2026, 5, 27, 10, 0, tzinfo=UTC),
                eficacia_verificada_por_user_id=uuid4(),
            ),
            repo,
        )
        fechar(FecharNCInput(nc_id=nc_id), repo)
        return nc_id

    def test_reabrir_volta_para_contida(self) -> None:
        repo = FakeNCRepository()
        nc_id = self._fluxo_ate_fechada(repo)
        out = reabrir(
            ReabrirNCInput(
                nc_id=nc_id,
                motivo_reabertura_canonicalizado=(
                    "Defeito recorrente na mesma grandeza apos 30 dias."
                ),
            ),
            repo,
        )
        # cl. 8.7.2 — reabertura volta a CONTIDA (nao REABERTA standalone)
        assert out.snapshot.estado == EstadoNaoConformidade.CONTIDA
        # Campos do ciclo anterior limpos
        assert out.snapshot.causa_raiz_canonicalizada == ""
        assert out.snapshot.acao_corretiva_tipo is None
        assert out.snapshot.acao_executada_em is None
        assert out.snapshot.eficacia_verificada_em is None
        assert out.snapshot.decisao_continuar_ou_parar == (
            DecisaoContinuarOuParar.A_DEFINIR
        )
        # Motivo eco do caller
        assert out.motivo.startswith("Defeito")

    def test_reabrir_de_contida_recusa(self) -> None:
        """Nao pode reabrir o que nao foi fechado."""
        repo = FakeNCRepository()
        nc_id = _abrir_padrao(repo)
        with pytest.raises(EstadoInvalidoParaTransicao, match="FECHADA"):
            reabrir(
                ReabrirNCInput(
                    nc_id=nc_id,
                    motivo_reabertura_canonicalizado="a" * 50,
                ),
                repo,
            )

    def test_motivo_curto_recusa(self) -> None:
        with pytest.raises(ValueError, match="motivo_reabertura_canonicalizado"):
            ReabrirNCInput(
                nc_id=uuid4(),
                motivo_reabertura_canonicalizado="curto",
            )

    def test_re_executar_ciclo_completo_apos_reabrir(self) -> None:
        """Apos reabrir, NC volta a CONTIDA e ciclo CAPA pode rodar de novo."""
        repo = FakeNCRepository()
        nc_id = self._fluxo_ate_fechada(repo)
        reabrir(
            ReabrirNCInput(
                nc_id=nc_id,
                motivo_reabertura_canonicalizado="a" * 50,
            ),
            repo,
        )
        # Ciclo novo
        definir_acao_corretiva(
            DefinirAcaoCorretivaInput(
                nc_id=nc_id,
                causa_raiz_canonicalizada="b" * 50,
                causa_raiz_hash="v01$novacausa",
                acao_corretiva_descricao_hash="v01$novaacao",
                acao_corretiva_tipo=AcaoCorretivaTipo.AJUSTE_ADMINISTRATIVO,
            ),
            repo,
        )
        snapshot = repo.snapshots[nc_id]
        assert snapshot.estado == EstadoNaoConformidade.ACAO_CORRETIVA_DEFINIDA
        assert snapshot.acao_corretiva_tipo == AcaoCorretivaTipo.AJUSTE_ADMINISTRATIVO


# ======================================================================
# Concorrencia + fluxo completo
# ======================================================================


def test_transitar_estado_mudou_concorrentemente_levanta_conflito() -> None:
    """ConflitoEstadoNaoConformidade quando estado mudou entre obter e transitar."""
    repo = FakeNCRepository()
    nc_id = _abrir_padrao(repo)
    # Simula corrida: outro processo transitou pra ACAO_CORRETIVA_DEFINIDA
    # antes de nos. Mutamos diretamente o estado no repo.
    snap = repo.snapshots[nc_id]
    from dataclasses import replace

    repo.snapshots[nc_id] = replace(
        snap, estado=EstadoNaoConformidade.ACAO_CORRETIVA_DEFINIDA
    )
    # Agora tentamos definir_acao — vai obter snapshot que ja esta em
    # ACAO_CORRETIVA_DEFINIDA, entao na verdade nao levanta ConflitoEstado
    # (levanta EstadoInvalidoParaTransicao). Conflito acontece quando
    # checkamos estado, ele tava CONTIDA, e na hora do UPDATE virou.
    # Forcamos esse caso simulando o obter retornando CONTIDA inicial:
    obter_original = repo.obter_por_id

    chamadas = [0]

    from dataclasses import replace as _replace_dc

    def obter_mutante(nc_id_arg: UUID) -> NaoConformidadeSnapshot | None:
        chamadas[0] += 1
        if chamadas[0] == 1:
            # Primeira chamada (use case): retorna snap CONTIDA do builder
            return _replace_dc(snap, estado=EstadoNaoConformidade.CONTIDA)
        return obter_original(nc_id_arg)

    repo.obter_por_id = obter_mutante  # type: ignore[method-assign]
    with pytest.raises(ConflitoEstadoNaoConformidade):
        definir_acao_corretiva(
            DefinirAcaoCorretivaInput(
                nc_id=nc_id,
                causa_raiz_canonicalizada="a" * 50,
                causa_raiz_hash="v01$x",
                acao_corretiva_descricao_hash="v01$y",
                acao_corretiva_tipo=AcaoCorretivaTipo.RE_EXECUTAR,
            ),
            repo,
        )


def test_fluxo_completo_contida_ate_fechada() -> None:
    """Smoke E2E: abrir -> definir -> executar -> verificar -> fechar."""
    repo = FakeNCRepository()
    nc_id = _abrir_padrao(repo)
    assert repo.snapshots[nc_id].estado == EstadoNaoConformidade.CONTIDA
    definir_acao_corretiva(
        DefinirAcaoCorretivaInput(
            nc_id=nc_id,
            causa_raiz_canonicalizada="a" * 50,
            causa_raiz_hash="v01$x",
            acao_corretiva_descricao_hash="v01$y",
            acao_corretiva_tipo=AcaoCorretivaTipo.RE_EXECUTAR,
        ),
        repo,
    )
    executar_acao(
        ExecutarAcaoInput(
            nc_id=nc_id,
            decisao_continuar_ou_parar=DecisaoContinuarOuParar.CONTINUAR_COM_CONTROLE,
            acao_executada_em=datetime(2026, 5, 26, 14, 0, tzinfo=UTC),
            cliente_notificado_em=None,
            cliente_notificado_via=None,
            cliente_notificado_documento_id=None,
        ),
        repo,
    )
    verificar_eficacia(
        VerificarEficaciaInput(
            nc_id=nc_id,
            eficacia_verificada_em=datetime(2026, 5, 27, 10, 0, tzinfo=UTC),
            eficacia_verificada_por_user_id=uuid4(),
        ),
        repo,
    )
    out = fechar(FecharNCInput(nc_id=nc_id), repo)
    assert out.snapshot.estado == EstadoNaoConformidade.FECHADA
    assert out.snapshot.estado.terminal
