"""Testes P3 — use cases do M5 padroes (T-PAD-020..029).

Puros (sem Django): Fake repositories implementam os Protocols de dominio com
CAS optimistic real (revision). Cobrem happy + unhappy + invariantes
(INV-PAD-001/002/003/005/006/008) + maquina de estados + Shewhart trigger.
"""

from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal
from uuid import UUID, uuid4

import pytest
from src.application.metrologia.padroes import (
    aprovar_recal_rt,
    baixar_padrao,
    cadastrar_padrao,
    calcular_valor_convencional,
    registrar_analise_carta_controle,
    registrar_intercomparacao,
    registrar_recal_envio,
    registrar_recal_retorno,
    registrar_verificacao_intermediaria,
    revogar_rastreabilidade_origem,
)
from src.domain.metrologia.padroes.entities import (
    AnaliseCartaControleSnapshot,
    IntercomparacaoPTSnapshot,
    PadraoMetrologicoSnapshot,
    RecalExternoPadraoSnapshot,
    VerificacaoIntermediariaSnapshot,
)
from src.domain.metrologia.padroes.enums import (
    ClassePadrao,
    DecisaoRTCarta,
    EstadoPadrao,
    RegraWesternElectric,
    ResultadoPT,
    ResultadoVI,
    StatusRecal,
    SubtipoPadrao,
    VinculacaoCadeia,
)
from src.domain.metrologia.padroes.valor_convencional import CertHistorico
from src.domain.metrologia.value_objects import (
    FaixaMedicao,
    Grandeza,
    IncertezaExpandida,
)

TENANT = uuid4()


# --------------------------------------------------------------------------
# Fakes (Protocols)
# --------------------------------------------------------------------------
class FakePadraoRepo:
    def __init__(self) -> None:
        self.store: dict[UUID, PadraoMetrologicoSnapshot] = {}
        self.series: set[tuple[UUID, str]] = set()
        self.aplicar_recal_chamado = False
        # Simula corrida: outra transacao bumpou a revision entre o read e o
        # write -> CAS falha (rowcount=0). Exercita o ramo ConflitoVersaoError.
        self.forcar_conflito = False

    def obter_por_id(self, padrao_id: UUID) -> PadraoMetrologicoSnapshot | None:
        return self.store.get(padrao_id)

    def existe_numero_serie(self, tenant_id: UUID, numero_serie: str) -> bool:
        return (tenant_id, numero_serie) in self.series

    def salvar_novo(self, snapshot: PadraoMetrologicoSnapshot) -> None:
        self.store[snapshot.id] = snapshot
        self.series.add((snapshot.tenant_id, snapshot.numero_serie))

    def atualizar_com_lock(
        self, snapshot: PadraoMetrologicoSnapshot, revision_anterior: int
    ) -> bool:
        if self.forcar_conflito:
            return False
        atual = self.store.get(snapshot.id)
        if atual is None or atual.revision != revision_anterior:
            return False
        self.store[snapshot.id] = snapshot
        return True

    def aplicar_recal_aprovado(
        self, snapshot: PadraoMetrologicoSnapshot, revision_anterior: int
    ) -> bool:
        self.aplicar_recal_chamado = True
        return self.atualizar_com_lock(snapshot, revision_anterior)


class FakeRecalRepo:
    def __init__(self) -> None:
        self.store: dict[UUID, RecalExternoPadraoSnapshot] = {}

    def salvar_novo(self, snapshot: RecalExternoPadraoSnapshot) -> None:
        self.store[snapshot.id] = snapshot

    def obter_por_id(self, recal_id: UUID) -> RecalExternoPadraoSnapshot | None:
        return self.store.get(recal_id)

    def ultimo_do_padrao(self, padrao_id: UUID) -> RecalExternoPadraoSnapshot | None:
        recais = [r for r in self.store.values() if r.padrao_id == padrao_id]
        return recais[-1] if recais else None

    def atualizar_retorno_e_aprovacao(
        self, snapshot: RecalExternoPadraoSnapshot
    ) -> None:
        self.store[snapshot.id] = snapshot


class FakeVIRepo:
    def __init__(self) -> None:
        self.itens: list[VerificacaoIntermediariaSnapshot] = []

    def salvar_nova(self, snapshot: VerificacaoIntermediariaSnapshot) -> None:
        self.itens.append(snapshot)

    def listar_por_padrao(
        self, padrao_id: UUID
    ) -> list[VerificacaoIntermediariaSnapshot]:
        return sorted(
            (v for v in self.itens if v.padrao_id == padrao_id),
            key=lambda v: v.data_vi,
        )


class FakePTRepo:
    def __init__(self) -> None:
        self.store: dict[UUID, IntercomparacaoPTSnapshot] = {}

    def salvar_nova(self, snapshot: IntercomparacaoPTSnapshot) -> None:
        self.store[snapshot.id] = snapshot

    def obter_por_id(self, pt_id: UUID) -> IntercomparacaoPTSnapshot | None:
        return self.store.get(pt_id)

    def atualizar_resultado(self, snapshot: IntercomparacaoPTSnapshot) -> None:
        self.store[snapshot.id] = snapshot


class FakeAnaliseRepo:
    def __init__(self) -> None:
        self.itens: list[AnaliseCartaControleSnapshot] = []

    def salvar_nova(self, snapshot: AnaliseCartaControleSnapshot) -> None:
        self.itens.append(snapshot)

    def listar_por_padrao(
        self, padrao_id: UUID
    ) -> list[AnaliseCartaControleSnapshot]:
        return [a for a in self.itens if a.padrao_id == padrao_id]


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------
def _cadastrar_input(**kw: object) -> cadastrar_padrao.CadastrarPadraoInput:
    base: dict[str, object] = {
        "tenant_id": TENANT,
        "numero_serie": "PESO-E2-001",
        "fabricante": "Mettler",
        "modelo": "M-1kg",
        "subtipo": SubtipoPadrao.PRINCIPAL,
        "grandezas": (Grandeza.MASSA,),
        "faixas": (FaixaMedicao(Decimal("0"), Decimal("1"), "kg"),),
        "incertezas_certificado": (
            IncertezaExpandida(Decimal("0.0001"), Decimal("2"), Decimal("0.9545"), "kg"),
        ),
        "vinculacao": VinculacaoCadeia.INMETRO,
        "classe": ClassePadrao.E2,
        "cert_externo_storage_key": "key-123",
        "validade_certificado_rastreabilidade": date(2027, 5, 1),
        "proximo_recal": date(2027, 4, 1),
        "intervalo_recal_meses": 12,
        "intervalo_vi_meses": 6,
        "criterio_intervalo": "Analise de risco cl. 6.4.7.",
        "vigencia_inicio": datetime(2026, 5, 1, tzinfo=UTC),
        "correlation_id": uuid4(),
        "tenant_e_perfil_a": True,
    }
    base.update(kw)
    return cadastrar_padrao.CadastrarPadraoInput(**base)  # type: ignore[arg-type]


def _cadastra_padrao(repo: FakePadraoRepo, **kw: object) -> PadraoMetrologicoSnapshot:
    out = cadastrar_padrao.executar(_cadastrar_input(**kw), repo)
    return out.snapshot


# --------------------------------------------------------------------------
# T-PAD-020 cadastrar_padrao
# --------------------------------------------------------------------------
class TestCadastrarPadrao:
    def test_happy(self) -> None:
        repo = FakePadraoRepo()
        snap = _cadastra_padrao(repo)
        assert snap.estado == EstadoPadrao.EM_USO
        assert snap.revision == 0
        assert repo.obter_por_id(snap.id) is not None

    def test_inv_pad_001_numero_serie_duplicado(self) -> None:
        repo = FakePadraoRepo()
        _cadastra_padrao(repo)
        with pytest.raises(cadastrar_padrao.NumeroSerieDuplicadoError):
            _cadastra_padrao(repo)

    def test_inv_pad_002_incertezas_vazias_bloqueia(self) -> None:
        with pytest.raises(ValueError, match="INV-PAD-002"):
            _cadastrar_input(incertezas_certificado=())

    def test_inv_pad_002_grandezas_vazias_bloqueia(self) -> None:
        with pytest.raises(ValueError, match="INV-PAD-002"):
            _cadastrar_input(grandezas=())

    def test_inv_pad_005_rbc_sem_perfil_a_bloqueia(self) -> None:
        repo = FakePadraoRepo()
        with pytest.raises(cadastrar_padrao.PerfilNaoPermiteRBCError):
            _cadastra_padrao(
                repo, vinculacao=VinculacaoCadeia.RBC, tenant_e_perfil_a=False
            )

    def test_inv_pad_005_rbc_com_perfil_a_passa(self) -> None:
        repo = FakePadraoRepo()
        snap = _cadastra_padrao(
            repo, vinculacao=VinculacaoCadeia.RBC, tenant_e_perfil_a=True
        )
        assert snap.vinculacao == VinculacaoCadeia.RBC


# --------------------------------------------------------------------------
# T-PAD-021/022/023 recal
# --------------------------------------------------------------------------
class TestRecal:
    def _setup(self) -> tuple[FakePadraoRepo, FakeRecalRepo, PadraoMetrologicoSnapshot]:
        rp, rr = FakePadraoRepo(), FakeRecalRepo()
        padrao = _cadastra_padrao(rp)
        return rp, rr, padrao

    def test_envio_transiciona_em_recal(self) -> None:
        rp, rr, padrao = self._setup()
        out = registrar_recal_envio.executar(
            registrar_recal_envio.RegistrarRecalEnvioInput(
                tenant_id=TENANT,
                padrao_id=padrao.id,
                enviado_em=datetime(2026, 6, 1, tzinfo=UTC),
                lab_externo="Lab RBC",
                responsavel_envio_id_hash="v1$resp",
            ),
            rp,
            rr,
        )
        assert out.padrao.estado == EstadoPadrao.EM_RECAL_EXTERNO
        assert out.recal.status == StatusRecal.ENVIADO

    def test_envio_bloqueia_se_rastreabilidade_revogada(self) -> None:
        rp, rr, padrao = self._setup()
        # liga a flag via use case dedicado (estado real do repo)
        revogar_rastreabilidade_origem.executar(
            revogar_rastreabilidade_origem.RevogarRastreabilidadeInput(
                tenant_id=TENANT, padrao_id=padrao.id, motivo="origem perdeu CGCRE"
            ),
            rp,
        )
        with pytest.raises(registrar_recal_envio.RastreabilidadeRevogadaError):
            registrar_recal_envio.executar(
                registrar_recal_envio.RegistrarRecalEnvioInput(
                    tenant_id=TENANT,
                    padrao_id=padrao.id,
                    enviado_em=datetime(2026, 6, 1, tzinfo=UTC),
                    lab_externo="Lab",
                    responsavel_envio_id_hash="v1$r",
                ),
                rp,
                rr,
            )

    def _enviar(
        self, rp: FakePadraoRepo, rr: FakeRecalRepo, padrao: PadraoMetrologicoSnapshot
    ) -> UUID:
        out = registrar_recal_envio.executar(
            registrar_recal_envio.RegistrarRecalEnvioInput(
                tenant_id=TENANT,
                padrao_id=padrao.id,
                enviado_em=datetime(2026, 6, 1, tzinfo=UTC),
                lab_externo="Lab RBC",
                responsavel_envio_id_hash="v1$resp",
            ),
            rp,
            rr,
        )
        return out.recal.id

    def test_retorno_normal_vai_pendente_aprovacao(self) -> None:
        rp, rr, padrao = self._setup()
        recal_id = self._enviar(rp, rr, padrao)
        out = registrar_recal_retorno.executar(
            registrar_recal_retorno.RegistrarRecalRetornoInput(
                tenant_id=TENANT,
                recal_id=recal_id,
                status=StatusRecal.RETORNADO,
                retornado_em=datetime(2026, 7, 1, tzinfo=UTC),
                incertezas_novas=(
                    IncertezaExpandida(Decimal("0.0002"), Decimal("2"), Decimal("0.9545"), "kg"),
                ),
                validade_nova=date(2028, 7, 1),
                valor_convencional_novo=Decimal("1.0000"),
            ),
            rp,
            rr,
        )
        assert out.padrao.estado == EstadoPadrao.RECAL_RETORNADO_PENDENTE_APROVACAO

    def test_retorno_incompleto_bloqueia(self) -> None:
        rp, rr, padrao = self._setup()
        recal_id = self._enviar(rp, rr, padrao)
        with pytest.raises(registrar_recal_retorno.RetornoIncompletoError):
            registrar_recal_retorno.executar(
                registrar_recal_retorno.RegistrarRecalRetornoInput(
                    tenant_id=TENANT,
                    recal_id=recal_id,
                    status=StatusRecal.RETORNADO,
                    retornado_em=datetime(2026, 7, 1, tzinfo=UTC),
                ),
                rp,
                rr,
            )

    def test_extraviado_vai_baixado(self) -> None:
        rp, rr, padrao = self._setup()
        recal_id = self._enviar(rp, rr, padrao)
        out = registrar_recal_retorno.executar(
            registrar_recal_retorno.RegistrarRecalRetornoInput(
                tenant_id=TENANT,
                recal_id=recal_id,
                status=StatusRecal.EXTRAVIADO_NO_TRANSPORTE,
                retornado_em=datetime(2026, 7, 1, tzinfo=UTC),
            ),
            rp,
            rr,
        )
        assert out.padrao.estado == EstadoPadrao.BAIXADO
        assert out.padrao.revogado_em is not None

    def test_aprovar_recal_libera_em_uso_e_aplica_incertezas(self) -> None:
        rp, rr, padrao = self._setup()
        recal_id = self._enviar(rp, rr, padrao)
        registrar_recal_retorno.executar(
            registrar_recal_retorno.RegistrarRecalRetornoInput(
                tenant_id=TENANT,
                recal_id=recal_id,
                status=StatusRecal.RETORNADO,
                retornado_em=datetime(2026, 7, 1, tzinfo=UTC),
                incertezas_novas=(
                    IncertezaExpandida(Decimal("0.0002"), Decimal("2"), Decimal("0.9545"), "kg"),
                ),
                validade_nova=date(2028, 7, 1),
                valor_convencional_novo=Decimal("1.0000"),
            ),
            rp,
            rr,
        )
        out = aprovar_recal_rt.executar(
            aprovar_recal_rt.AprovarRecalRTInput(
                tenant_id=TENANT,
                recal_id=recal_id,
                aprovado=True,
                aprovado_rt_id_hash="v1$rt",
                decidido_em=datetime(2026, 7, 2, tzinfo=UTC),
                proximo_recal_novo=date(2028, 6, 1),
            ),
            rp,
            rr,
        )
        assert out.padrao.estado == EstadoPadrao.EM_USO
        assert rp.aplicar_recal_chamado is True
        assert out.padrao.validade_certificado_rastreabilidade == date(2028, 7, 1)

    def test_cas_conflito_de_versao_no_envio_levanta(self) -> None:
        # CAS optimistic real: revision divergente (corrida) -> ConflitoVersaoError.
        rp, rr, padrao = self._setup()
        rp.forcar_conflito = True
        with pytest.raises(registrar_recal_envio.ConflitoVersaoError):
            registrar_recal_envio.executar(
                registrar_recal_envio.RegistrarRecalEnvioInput(
                    tenant_id=TENANT,
                    padrao_id=padrao.id,
                    enviado_em=datetime(2026, 6, 1, tzinfo=UTC),
                    lab_externo="Lab RBC",
                    responsavel_envio_id_hash="v1$resp",
                ),
                rp,
                rr,
            )

    def test_rejeitar_recal_volta_em_recal(self) -> None:
        rp, rr, padrao = self._setup()
        recal_id = self._enviar(rp, rr, padrao)
        registrar_recal_retorno.executar(
            registrar_recal_retorno.RegistrarRecalRetornoInput(
                tenant_id=TENANT,
                recal_id=recal_id,
                status=StatusRecal.RETORNADO,
                retornado_em=datetime(2026, 7, 1, tzinfo=UTC),
                incertezas_novas=(
                    IncertezaExpandida(Decimal("0.0002"), Decimal("2"), Decimal("0.9545"), "kg"),
                ),
                validade_nova=date(2028, 7, 1),
                valor_convencional_novo=Decimal("1.0000"),
            ),
            rp,
            rr,
        )
        out = aprovar_recal_rt.executar(
            aprovar_recal_rt.AprovarRecalRTInput(
                tenant_id=TENANT,
                recal_id=recal_id,
                aprovado=False,
                aprovado_rt_id_hash="v1$rt",
                decidido_em=datetime(2026, 7, 2, tzinfo=UTC),
            ),
            rp,
            rr,
        )
        assert out.padrao.estado == EstadoPadrao.EM_RECAL_EXTERNO
        assert rp.aplicar_recal_chamado is False


# --------------------------------------------------------------------------
# T-PAD-024 VI + Shewhart
# --------------------------------------------------------------------------
class TestVerificacaoIntermediaria:
    def _vi_input(self, padrao_id: UUID, **kw: object) -> registrar_verificacao_intermediaria.RegistrarVIInput:
        base: dict[str, object] = {
            "tenant_id": TENANT,
            "padrao_id": padrao_id,
            "data_vi": datetime(2026, 6, 1, tzinfo=UTC),
            "executor_id_hash": "v1$exec",
            "metodo_canonicalizado": "comparacao com padrao E1",
            "metodo_hash": "v1$m",
            "resultado": ResultadoVI.APROVADO,
            "tenant_e_perfil_a": True,
        }
        base.update(kw)
        return registrar_verificacao_intermediaria.RegistrarVIInput(**base)  # type: ignore[arg-type]

    def test_vi_aprovado_grava(self) -> None:
        rp, rv = FakePadraoRepo(), FakeVIRepo()
        padrao = _cadastra_padrao(rp)
        out = registrar_verificacao_intermediaria.executar(
            self._vi_input(padrao.id), rp, rv
        )
        assert out.vi.resultado == ResultadoVI.APROVADO
        assert out.violacoes == ()

    def test_vi_reprovado_sem_acao_corretiva_bloqueia(self) -> None:
        rp, rv = FakePadraoRepo(), FakeVIRepo()
        padrao = _cadastra_padrao(rp)
        with pytest.raises(
            registrar_verificacao_intermediaria.AcaoCorretivaObrigatoriaError
        ):
            registrar_verificacao_intermediaria.executar(
                self._vi_input(padrao.id, resultado=ResultadoVI.REPROVADO), rp, rv
            )

    def test_perfil_nao_a_nao_roda_shewhart(self) -> None:
        rp, rv = FakePadraoRepo(), FakeVIRepo()
        padrao = _cadastra_padrao(rp)
        out = registrar_verificacao_intermediaria.executar(
            self._vi_input(
                padrao.id, tenant_e_perfil_a=False, desvio_observado=Decimal("100")
            ),
            rp,
            rv,
        )
        assert out.limites is None
        assert out.violacoes == ()

    def test_shewhart_detecta_tendencia_7_pontos(self) -> None:
        rp, rv = FakePadraoRepo(), FakeVIRepo()
        padrao = _cadastra_padrao(rp)
        # 6 VIs historicas com desvios crescentes 1..6 (datas crescentes).
        for i in range(1, 7):
            rv.salvar_nova(
                VerificacaoIntermediariaSnapshot(
                    id=uuid4(),
                    tenant_id=TENANT,
                    padrao_id=padrao.id,
                    data_vi=datetime(2026, 1, i, tzinfo=UTC),
                    executor_id_hash="v1$e",
                    metodo_canonicalizado="m",
                    metodo_hash="v1$h",
                    resultado=ResultadoVI.APROVADO,
                    criado_em=datetime(2026, 1, i, tzinfo=UTC),
                    desvio_observado=Decimal(i),
                )
            )
        out = registrar_verificacao_intermediaria.executar(
            self._vi_input(
                padrao.id,
                data_vi=datetime(2026, 1, 7, tzinfo=UTC),
                desvio_observado=Decimal("7"),
            ),
            rp,
            rv,
        )
        assert out.limites is not None
        regras = {v.regra for v in out.violacoes}
        assert RegraWesternElectric.REGRA_5_TENDENCIA_7 in regras
        assert out.serie_vi_ids[-1] == out.vi.id


# --------------------------------------------------------------------------
# T-PAD-025 intercomparacao
# --------------------------------------------------------------------------
class TestIntercomparacao:
    def test_inicio_nao_perfil_a_bloqueia(self) -> None:
        rp, rpt = FakePadraoRepo(), FakePTRepo()
        padrao = _cadastra_padrao(rp)
        with pytest.raises(registrar_intercomparacao.PerfilNaoPermitePTError):
            registrar_intercomparacao.executar_inicio(
                registrar_intercomparacao.IniciarPTInput(
                    tenant_id=TENANT,
                    padrao_id=padrao.id,
                    lab_organizador="INMETRO",
                    protocolo="PT-1",
                    data_inicio=datetime(2026, 6, 1, tzinfo=UTC),
                    tenant_e_perfil_a=False,
                ),
                rp,
                rpt,
            )

    def test_inicio_e_resultado_ciclo_completo(self) -> None:
        rp, rpt = FakePadraoRepo(), FakePTRepo()
        padrao = _cadastra_padrao(rp)
        ini = registrar_intercomparacao.executar_inicio(
            registrar_intercomparacao.IniciarPTInput(
                tenant_id=TENANT,
                padrao_id=padrao.id,
                lab_organizador="INMETRO",
                protocolo="PT-1",
                data_inicio=datetime(2026, 6, 1, tzinfo=UTC),
                tenant_e_perfil_a=True,
            ),
            rp,
            rpt,
        )
        assert ini.padrao.estado == EstadoPadrao.INTERCOMPARACAO_PT_EM_CURSO
        res = registrar_intercomparacao.executar_resultado(
            registrar_intercomparacao.RegistrarResultadoPTInput(
                tenant_id=TENANT,
                pt_id=ini.pt.id,
                resultado=ResultadoPT.APROVADO,
                data_resultado=datetime(2026, 8, 1, tzinfo=UTC),
                zeta_score=Decimal("0.5"),
            ),
            rp,
            rpt,
        )
        assert res.padrao.estado == EstadoPadrao.EM_USO
        assert res.pt.resultado == ResultadoPT.APROVADO


# --------------------------------------------------------------------------
# T-PAD-026 analise carta controle
# --------------------------------------------------------------------------
class TestAnaliseCartaControle:
    def _input(self, padrao_id: UUID, **kw: object) -> registrar_analise_carta_controle.RegistrarAnaliseCartaInput:
        base: dict[str, object] = {
            "tenant_id": TENANT,
            "padrao_id": padrao_id,
            "regra_violada": RegraWesternElectric.REGRA_5_TENDENCIA_7,
            "pontos_referenciados_ids": (uuid4(),),
            "linha_central": Decimal("4"),
            "ucl": Decimal("10"),
            "lcl": Decimal("-2"),
            "sigma": Decimal("2"),
            "n_pontos": 7,
            "janela_meses": 24,
            "versao_motor_shewhart": "shewhart-1.0.0",
            "decisao_rt": DecisaoRTCarta.RECALIBRAR,
            "justificativa_canonicalizada": "tendencia detectada — recalibrar",
            "justificativa_hash": "v1$j",
            "criado_em": datetime(2026, 8, 1, tzinfo=UTC),
            "tenant_e_perfil_a": True,
        }
        base.update(kw)
        return registrar_analise_carta_controle.RegistrarAnaliseCartaInput(**base)  # type: ignore[arg-type]

    def test_perfil_a_registra(self) -> None:
        rp, ra = FakePadraoRepo(), FakeAnaliseRepo()
        padrao = _cadastra_padrao(rp)
        out = registrar_analise_carta_controle.executar(self._input(padrao.id), rp, ra)
        assert out.analise.decisao_rt == DecisaoRTCarta.RECALIBRAR
        assert len(ra.listar_por_padrao(padrao.id)) == 1

    def test_nao_perfil_a_bloqueia(self) -> None:
        rp, ra = FakePadraoRepo(), FakeAnaliseRepo()
        padrao = _cadastra_padrao(rp)
        with pytest.raises(
            registrar_analise_carta_controle.PerfilNaoPermiteCartaError
        ):
            registrar_analise_carta_controle.executar(
                self._input(padrao.id, tenant_e_perfil_a=False), rp, ra
            )


# --------------------------------------------------------------------------
# T-PAD-027 valor convencional
# --------------------------------------------------------------------------
class TestValorConvencional:
    def test_calcula_perfil_ab(self) -> None:
        out = calcular_valor_convencional.executar(
            calcular_valor_convencional.CalcularValorConvencionalInput(
                certs=(
                    CertHistorico(Decimal("1.0000"), Decimal("0.0002"), 30),
                    CertHistorico(Decimal("1.0001"), Decimal("0.0003"), 25),
                ),
                tenant_e_perfil_a_ou_b=True,
            )
        )
        assert out.resultado.n_certificados == 2
        assert out.resultado.U_expandida > 0

    def test_nao_perfil_ab_bloqueia(self) -> None:
        with pytest.raises(
            calcular_valor_convencional.PerfilNaoPermiteSegundoCaminhoError
        ):
            calcular_valor_convencional.executar(
                calcular_valor_convencional.CalcularValorConvencionalInput(
                    certs=(CertHistorico(Decimal("1.0"), Decimal("0.001"), None),),
                    tenant_e_perfil_a_ou_b=False,
                )
            )


# --------------------------------------------------------------------------
# T-PAD-028 baixar/sucatar
# --------------------------------------------------------------------------
class TestBaixarSucatar:
    def test_baixar_happy(self) -> None:
        rp = FakePadraoRepo()
        padrao = _cadastra_padrao(rp)
        out = baixar_padrao.executar(
            baixar_padrao.BaixarPadraoInput(
                tenant_id=TENANT,
                padrao_id=padrao.id,
                sucatar=False,
                motivo_revogacao="fora de uso por decisao tecnica",
                responsavel_rt_id_hash="v1$rt",
                revogado_em=datetime(2026, 9, 1, tzinfo=UTC),
                tem_calibracao_em_curso=False,
            ),
            rp,
        )
        assert out.padrao.estado == EstadoPadrao.BAIXADO
        assert out.padrao.revogado_em is not None

    def test_inv_pad_003_calibracao_em_curso_bloqueia(self) -> None:
        rp = FakePadraoRepo()
        padrao = _cadastra_padrao(rp)
        with pytest.raises(baixar_padrao.CalibracaoEmCursoError):
            baixar_padrao.executar(
                baixar_padrao.BaixarPadraoInput(
                    tenant_id=TENANT,
                    padrao_id=padrao.id,
                    sucatar=True,
                    motivo_revogacao="descarte definitivo do padrao",
                    responsavel_rt_id_hash="v1$rt",
                    revogado_em=datetime(2026, 9, 1, tzinfo=UTC),
                    tem_calibracao_em_curso=True,
                ),
                rp,
            )


# --------------------------------------------------------------------------
# T-PAD-029 revogar rastreabilidade
# --------------------------------------------------------------------------
class TestRevogarRastreabilidade:
    def test_liga_flag(self) -> None:
        rp = FakePadraoRepo()
        padrao = _cadastra_padrao(rp)
        out = revogar_rastreabilidade_origem.executar(
            revogar_rastreabilidade_origem.RevogarRastreabilidadeInput(
                tenant_id=TENANT,
                padrao_id=padrao.id,
                motivo="origem perdeu acreditacao CGCRE",
            ),
            rp,
        )
        assert out.padrao.rastreabilidade_origem_revogada is True

    def test_idempotente_ja_revogada_bloqueia(self) -> None:
        rp = FakePadraoRepo()
        padrao = _cadastra_padrao(rp)
        revogar_rastreabilidade_origem.executar(
            revogar_rastreabilidade_origem.RevogarRastreabilidadeInput(
                tenant_id=TENANT, padrao_id=padrao.id, motivo="origem invalida agora"
            ),
            rp,
        )
        with pytest.raises(revogar_rastreabilidade_origem.JaRevogadaError):
            revogar_rastreabilidade_origem.executar(
                revogar_rastreabilidade_origem.RevogarRastreabilidadeInput(
                    tenant_id=TENANT, padrao_id=padrao.id, motivo="tentativa repetida"
                ),
                rp,
            )
