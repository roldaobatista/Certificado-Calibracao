"""TST-004 — classes nomeando cada INV-ECMC-001..009 (M6 P7 / T-ECMC-060).

Convenção do projeto (análoga `test_inv_pad_classes_nomeadas.py` do M5 e
`test_inv_cal_classes_nomeadas.py` do M4): todo INV crítico tem >=1 teste cujo
NOME cita o ID. Cada classe `TestINV_ECMC_NNN` exercita a barreira REAL —
PG-real onde a defesa é trigger/constraint/porta (003/004); puro/Fake onde é
domínio/use case (001/002/005/006/007/008/009).

Escopo CGCRE (perfil A) e capacidade interna (B/C/D) — anti-fraude RBC é o
coração do módulo (FAIL L6 SAN-PERFIL): tenant não-A nunca se passa por
acreditado (INV-ECMC-002).
"""

from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from datetime import UTC, date, datetime
from decimal import Decimal
from uuid import UUID, uuid4

import pytest
from django.db import DatabaseError
from django.utils import timezone
from src.application.metrologia.escopos_cmc import (
    cadastrar_escopo,
    confirmar_escopo_extraido,
)
from src.domain.metrologia.escopos_cmc import cobertura
from src.domain.metrologia.escopos_cmc.entities import (
    EscopoCMCSnapshot,
    EscopoExtraido,
    EscopoUsado,
)
from src.domain.metrologia.escopos_cmc.enums import (
    EstadoEscopo,
    FormaCMC,
    OrigemEscopo,
)
from src.domain.metrologia.escopos_cmc.transicoes import rbc_efetivo
from src.domain.metrologia.value_objects import FaixaMedicao, Grandeza
from src.infrastructure.metrologia.escopos_cmc import query_service
from src.infrastructure.metrologia.escopos_cmc.models import EscopoCMC
from src.infrastructure.multitenant.connection import run_in_tenant_context

from tests.factories import TenantFactory

UTC_AGORA = datetime(2026, 6, 1, tzinfo=UTC)


# --------------------------------------------------------------------------
# Fakes dos Protocols (domínio puro — sem Django)
# --------------------------------------------------------------------------
class _FakeEscopoRepo:
    """EscopoRepository em memória (use case puro)."""

    def __init__(self, *, ja_existe: bool = False):
        self.ja_existe = ja_existe
        self.salvos: list[EscopoCMCSnapshot] = []

    def existe_chave_confirmada(self, **_kw) -> bool:
        return self.ja_existe

    def salvar_novo(self, snapshot: EscopoCMCSnapshot) -> None:
        self.salvos.append(snapshot)


class _FakeExtraidoRepo:
    """EscopoExtraidoRepository em memória com one-shot real."""

    def __init__(self, staging: EscopoExtraido):
        self._staging = staging

    def obter_por_id(self, extraido_id: UUID) -> EscopoExtraido | None:
        return self._staging if self._staging.id == extraido_id else None

    def marcar_confirmado(self, *, extraido_id, confirmado_em, por_id_hash) -> bool:
        if self._staging.confirmado_em is not None:
            return False  # one-shot já gasto
        # simula UPDATE persistido (frozen VO — usa object.__setattr__)
        object.__setattr__(self._staging, "confirmado_em", confirmado_em)
        object.__setattr__(self._staging, "confirmado_por_id_hash", por_id_hash)
        return True


def _input_cadastro(*, perfil: str, rbc_solicitado: bool, **kw):
    base = {
        "tenant_id": uuid4(),
        "grandeza": Grandeza.MASSA,
        "faixa": FaixaMedicao(Decimal("0"), Decimal("1000"), "g"),
        "cmc_forma": FormaCMC.ABSOLUTA,
        "cmc_valor": Decimal("0.001"),
        "cmc_unidade": "g",
        "perfil": perfil,
        "rbc_solicitado": rbc_solicitado,
        "vigencia_inicio": UTC_AGORA,
        "correlation_id": uuid4(),
        "procedimento_id": uuid4(),  # RBC exige procedimento
    }
    base.update(kw)
    return cadastrar_escopo.CadastrarEscopoInput(**base)


# --------------------------------------------------------------------------
# PG-real helper (003/004) — molde test_inv_ecmc_p2_schema_triggers
# --------------------------------------------------------------------------
def _cria_escopo_pg(tenant, *, grandeza="massa", faixa_min="0", faixa_max="1000",
                    unidade="g", cmc_valor="0.001", rbc=True) -> EscopoCMC:
    with run_in_tenant_context(tenant.id):
        return EscopoCMC.objects.create(
            tenant=tenant,
            grandeza=grandeza,
            faixa_min=Decimal(faixa_min),
            faixa_max=Decimal(faixa_max),
            unidade=unidade,
            cmc_forma="ABSOLUTA",
            cmc_valor=Decimal(cmc_valor),
            cmc_unidade=unidade,
            rbc_acreditado=rbc,
            versao=1,
            vigente_a_partir=timezone.now(),
            estado="CONFIRMADO",
            origem="MANUAL",
            vigencia_inicio=timezone.now(),
        )


# ==========================================================================
class TestINV_ECMC_001:
    """Chave natural UNIQUE tenant-scoped — cadastrar chave existente bloqueia."""

    def test_chave_duplicada_bloqueia(self):
        repo = _FakeEscopoRepo(ja_existe=True)
        with pytest.raises(cadastrar_escopo.ChaveDuplicadaError):
            cadastrar_escopo.executar(
                _input_cadastro(perfil="A", rbc_solicitado=True), repo
            )

    def test_chave_inedita_passa(self):
        repo = _FakeEscopoRepo(ja_existe=False)
        out = cadastrar_escopo.executar(
            _input_cadastro(perfil="A", rbc_solicitado=True), repo
        )
        assert out.snapshot.versao == 1
        assert len(repo.salvos) == 1


class TestINV_ECMC_002:
    """rbc_acreditado=True só perfil A; B/C/D forçado False (anti-fraude)."""

    def test_rbc_efetivo_forca_false_para_nao_a(self):
        assert rbc_efetivo(rbc_solicitado=True, perfil="B") is False
        assert rbc_efetivo(rbc_solicitado=True, perfil="C") is False
        assert rbc_efetivo(rbc_solicitado=True, perfil="D") is False
        assert rbc_efetivo(rbc_solicitado=True, perfil="A") is True

    def test_cadastro_perfil_c_solicitando_rbc_persiste_false(self):
        repo = _FakeEscopoRepo()
        out = cadastrar_escopo.executar(
            _input_cadastro(perfil="C", rbc_solicitado=True, procedimento_id=None),
            repo,
        )
        assert out.snapshot.rbc_acreditado is False  # fraude bloqueada

    def test_cadastro_perfil_a_rbc_verdadeiro(self):
        repo = _FakeEscopoRepo()
        out = cadastrar_escopo.executar(
            _input_cadastro(perfil="A", rbc_solicitado=True), repo
        )
        assert out.snapshot.rbc_acreditado is True


class TestINV_ECMC_003:
    """Escopo CONFIRMADO é WORM Padrão B (UPDATE metrológico/DELETE bloqueados)."""

    @pytest.mark.django_db(transaction=True)
    def test_update_cmc_de_confirmado_bloqueia(self):
        tenant = TenantFactory(slug=f"ecmc3a-{uuid4().hex[:6]}")
        escopo = _cria_escopo_pg(tenant)
        with run_in_tenant_context(tenant.id), pytest.raises(DatabaseError):
            EscopoCMC.objects.filter(id=escopo.id).update(cmc_valor=Decimal("9"))

    @pytest.mark.django_db(transaction=True)
    def test_delete_de_confirmado_bloqueia(self):
        tenant = TenantFactory(slug=f"ecmc3b-{uuid4().hex[:6]}")
        escopo = _cria_escopo_pg(tenant)
        with run_in_tenant_context(tenant.id), pytest.raises(DatabaseError):
            EscopoCMC.objects.filter(id=escopo.id).delete()


class TestINV_ECMC_004:
    """Porta cobre() fail-CLOSED real — RBC fora de escopo bloqueia."""

    @pytest.mark.django_db(transaction=True)
    def test_sem_escopo_fail_closed(self):
        tenant = TenantFactory(slug=f"ecmc4a-{uuid4().hex[:6]}")
        with run_in_tenant_context(tenant.id):
            ok, reason = query_service.cobre(
                tenant_id=tenant.id, grandeza="massa",
                faixa_min=Decimal("10"), faixa_max=Decimal("20"),
                unidade="g", data=timezone.now(),
            )
        assert ok is False
        assert reason == cobertura.REASON_FORA_DO_ESCOPO

    @pytest.mark.django_db(transaction=True)
    def test_faixa_fora_do_escopo_bloqueia_dentro_passa(self):
        tenant = TenantFactory(slug=f"ecmc4b-{uuid4().hex[:6]}")
        _cria_escopo_pg(tenant, faixa_min="0", faixa_max="1000")
        agora = timezone.now()
        with run_in_tenant_context(tenant.id):
            dentro, _r1 = query_service.cobre(
                tenant_id=tenant.id, grandeza="massa",
                faixa_min=Decimal("10"), faixa_max=Decimal("20"),
                unidade="g", data=agora,
            )
            fora, r2 = query_service.cobre(
                tenant_id=tenant.id, grandeza="massa",
                faixa_min=Decimal("900"), faixa_max=Decimal("5000"),
                unidade="g", data=agora,
            )
        assert dentro is True
        assert fora is False and r2 == cobertura.REASON_FORA_DO_ESCOPO


class TestINV_ECMC_005:
    """Cobertura por CONTENÇÃO TOTAL — interseção parcial NÃO cobre."""

    def _faixa(self, lo, hi, un="g"):
        return FaixaMedicao(Decimal(lo), Decimal(hi), un)

    def test_dentro_e_borda_cobrem(self):
        escopo = self._faixa("0", "1000")
        assert cobertura.faixa_contida(solicitada=self._faixa("10", "20"), escopo=escopo)
        assert cobertura.faixa_contida(solicitada=self._faixa("0", "1000"), escopo=escopo)

    def test_intersecao_parcial_nao_cobre(self):
        escopo = self._faixa("0", "1000")
        # 900..2000 transborda o superior -> NÃO contido (fraude se passasse)
        ok, reason = cobertura.avaliar_contencao(
            solicitada=self._faixa("900", "2000"), escopo=escopo
        )
        assert ok is False
        assert reason == cobertura.REASON_FORA_DO_ESCOPO

    def test_unidade_divergente_fail_closed(self):
        ok, reason = cobertura.avaliar_contencao(
            solicitada=self._faixa("10", "20", "kg"), escopo=self._faixa("0", "1000", "g")
        )
        assert ok is False
        assert reason == cobertura.REASON_UNIDADE_INCOMPATIVEL


class TestINV_ECMC_006:
    """Vigência canônica ADR-0030 — datetime naive rejeitado; vigente_em correto."""

    def test_vigencia_inicio_naive_rejeitada(self):
        with pytest.raises(ValueError, match="tz-aware"):
            _input_cadastro(
                perfil="A", rbc_solicitado=True,
                vigencia_inicio=datetime(2026, 6, 1),  # naive
            )

    def test_revogado_sai_da_vigencia(self):
        snap = cadastrar_escopo.executar(
            _input_cadastro(perfil="A", rbc_solicitado=True), _FakeEscopoRepo()
        ).snapshot
        # revogado em t0 -> não vigente em t0+
        revogado = replace(snap, revogado_em=UTC_AGORA)
        assert revogado.vigente_em(datetime(2026, 6, 2, tzinfo=UTC)) is False
        assert snap.vigente_em(datetime(2026, 6, 2, tzinfo=UTC)) is True


class TestINV_ECMC_007:
    """Extração nunca auto-persiste — só confirmar promove, e é one-shot."""

    def _staging(self) -> EscopoExtraido:
        return EscopoExtraido(
            id=uuid4(),
            tenant_id=uuid4(),
            origem_pdf_storage_key="key-cgcre-123",
            numero_escopo_cgcre="CRL-0042",
            extraido_em=UTC_AGORA,
            linhas=(),
            confirmado_em=None,
        )

    def test_staging_nasce_nao_confirmado(self):
        st = self._staging()
        assert st.confirmado_em is None  # nunca vigente sem conferência

    def _confirmar(self, staging, perfil="A"):
        repo_ext = _FakeExtraidoRepo(staging)
        repo_esc = _FakeEscopoRepo()
        linha = _input_cadastro(
            perfil=perfil, rbc_solicitado=True, tenant_id=staging.tenant_id
        )
        inp = confirmar_escopo_extraido.ConfirmarEscopoExtraidoInput(
            extraido_id=staging.id,
            tenant_id=staging.tenant_id,
            confirmado_por_id_hash="v1$confereu",
            confirmado_em=UTC_AGORA,
            escopos=(linha,),
        )
        return confirmar_escopo_extraido.executar(inp, repo_ext, repo_esc)

    def test_confirmar_promove_uma_vez_e_marca_origem_pdf(self):
        staging = self._staging()
        out = self._confirmar(staging)
        assert len(out.confirmados) == 1
        assert out.confirmados[0].origem is OrigemEscopo.EXTRACAO_PDF
        assert staging.confirmado_em is not None

    def test_reconfirmar_staging_ja_confirmado_bloqueia(self):
        staging = self._staging()
        self._confirmar(staging)  # 1ª promoção (one-shot gasto)
        with pytest.raises(confirmar_escopo_extraido.ExtraidoJaConfirmado):
            self._confirmar(staging)


class TestINV_ECMC_008:
    """Snapshot EscopoUsado é VO probatório frozen (conteúdo mínimo RBC-NC-06)."""

    def _usado(self) -> EscopoUsado:
        return EscopoUsado(
            escopo_id=uuid4(),
            versao=2,
            numero_escopo_cgcre="CRL-0042",
            grandeza=Grandeza.MASSA,
            faixa_escopo=FaixaMedicao(Decimal("0"), Decimal("1000"), "g"),
            faixa_solicitada=FaixaMedicao(Decimal("10"), Decimal("20"), "g"),
            cmc_forma=FormaCMC.ABSOLUTA,
            cmc_valor=Decimal("0.001"),
            cmc_unidade="g",
            rbc_acreditado=True,
            perfil_no_evento="A",
            data_referencia=date(2026, 6, 1),
            vigencia_inicio=UTC_AGORA,
            contido=True,
        )

    def test_vo_e_imutavel(self):
        usado = self._usado()
        campo = "cmc_valor"  # atributo via variável: frozen dispara em runtime
        with pytest.raises(FrozenInstanceError):
            setattr(usado, campo, Decimal("9"))

    def test_conteudo_probatorio_minimo_presente(self):
        usado = self._usado()
        # versão + CMC-da-época + forma + perfil + contenção — autossuficiente
        assert usado.versao == 2
        assert usado.cmc_forma is FormaCMC.ABSOLUTA
        assert usado.perfil_no_evento == "A"
        assert usado.contido is True


class TestINV_ECMC_009:
    """U ≥ CMC (ILAC-P14 §5.5) — U < CMC bloqueia; menor CMC entre métodos."""

    def test_u_abaixo_do_cmc_bloqueia(self):
        ok, reason = cobertura.avaliar_u_cmc(
            u_reportada=Decimal("0.0005"), cmc_no_ponto=Decimal("0.001")
        )
        assert ok is False
        assert reason == cobertura.REASON_INCERTEZA_ABAIXO_CMC

    def test_u_acima_ou_igual_atende(self):
        atende, _r = cobertura.avaliar_u_cmc(
            u_reportada=Decimal("0.002"), cmc_no_ponto=Decimal("0.001")
        )
        assert atende is True
        # U == CMC é suspeito (cópia cega) mas não bloqueia por si só (RBC-NC-07)
        assert cobertura.u_igual_cmc_suspeita(
            u_reportada=Decimal("0.001"), cmc_no_ponto=Decimal("0.001")
        )

    def test_menor_cmc_entre_metodos(self):
        def _esc(cmc):
            return EscopoCMCSnapshot(
                id=uuid4(), tenant_id=uuid4(), grandeza=Grandeza.MASSA,
                faixa=FaixaMedicao(Decimal("0"), Decimal("1000"), "g"),
                cmc_forma=FormaCMC.ABSOLUTA, cmc_valor=Decimal(cmc), cmc_unidade="g",
                rbc_acreditado=True, versao=1, vigente_a_partir=UTC_AGORA,
                estado=EstadoEscopo.CONFIRMADO, revision=0, vigencia_inicio=UTC_AGORA,
                correlation_id=uuid4(),
            )
        menor = cobertura.menor_cmc_por_faixa(
            [_esc("0.002"), _esc("0.001")], ponto=Decimal("500")
        )
        assert menor == Decimal("0.001")
