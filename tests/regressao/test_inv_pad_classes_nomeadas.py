"""TST-004 — classes nomeando cada INV-PAD-001..010 (M5 P7 / REGRAS).

Convenção do projeto (análoga `test_inv_cal_classes_nomeadas.py` do M4): todo
INV crítico tem >=1 teste cujo NOME cita o ID. Aqui cada classe `TestINV_PAD_NNN`
exercita a barreira real (PG-real onde a defesa é trigger/constraint/porta; puro
onde é domínio). Foco especial no INV-PAD-007 (auxiliar vencido bloqueia o
principal) — barreira de runtime adicionada no P7.
"""

from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal
from uuid import uuid4

import pytest
from django.db import IntegrityError, transaction
from django.db.utils import InternalError, ProgrammingError
from django.utils import timezone
from src.application.metrologia.padroes import cadastrar_padrao
from src.domain.metrologia.padroes import valor_convencional
from src.domain.metrologia.padroes.enums import EstadoPadrao, VinculacaoCadeia
from src.domain.metrologia.padroes.valor_convencional import (
    CertHistorico,
    DivergenciaImplementacoesError,
)
from src.domain.metrologia.value_objects import (
    FaixaMedicao,
    Grandeza,
    IncertezaExpandida,
)
from src.infrastructure.metrologia.padroes import mappers, query_service
from src.infrastructure.metrologia.padroes.models import (
    PadraoMetrologico,
    VinculoAuxiliar,
)
from src.infrastructure.multitenant.connection import run_in_tenant_context

from tests.factories import TenantFactory

HOJE = date(2026, 6, 1)


def _cria_padrao(tenant, **kw):
    defaults = {
        "tenant": tenant,
        "numero_serie": f"PAD-{uuid4().hex[:8]}",
        "fabricante": "Mettler",
        "modelo": "XPR",
        "subtipo": "PRINCIPAL",
        "grandezas": mappers.grandezas_para_json((Grandeza.MASSA,)),
        "faixas": mappers.faixas_para_json(
            (FaixaMedicao(Decimal("0"), Decimal("1000"), "g"),)
        ),
        "incertezas_certificado": mappers.incertezas_para_json(
            (IncertezaExpandida(Decimal("0.001"), Decimal("2"), Decimal("0.9545"), "g"),)
        ),
        "vinculacao": "INMETRO",
        "classe": "E2",
        "validade_certificado_rastreabilidade": date(2027, 1, 1),
        "proximo_recal": date(2027, 1, 1),
        "intervalo_recal_meses": 12,
        "intervalo_vi_meses": 3,
        "criterio_intervalo": "cl. 6.4.7 historico de estabilidade",
        "estado": "EM_USO",
        "vigencia_inicio": timezone.now(),
    }
    defaults.update(kw)
    with run_in_tenant_context(tenant.id):
        return PadraoMetrologico.objects.create(**defaults)


def _vincula_auxiliar(tenant, principal, auxiliar, revogado=False):
    with run_in_tenant_context(tenant.id):
        return VinculoAuxiliar.objects.create(
            tenant=tenant,
            padrao_principal=principal,
            padrao_auxiliar=auxiliar,
            grandeza_influencia={"simbolo": "T", "nome": "temperatura"},
            vigencia_inicio=timezone.now(),
            revogado_em=timezone.now() if revogado else None,
        )


def _cadastrar_input(**kw):
    base = {
        "tenant_id": uuid4(),
        "numero_serie": "PESO-E2-001",
        "fabricante": "Mettler",
        "modelo": "M-1kg",
        "subtipo": __import__(
            "src.domain.metrologia.padroes.enums", fromlist=["SubtipoPadrao"]
        ).SubtipoPadrao.PRINCIPAL,
        "grandezas": (Grandeza.MASSA,),
        "faixas": (FaixaMedicao(Decimal("0"), Decimal("1"), "kg"),),
        "incertezas_certificado": (
            IncertezaExpandida(Decimal("0.0001"), Decimal("2"), Decimal("0.9545"), "kg"),
        ),
        "vinculacao": VinculacaoCadeia.INMETRO,
        "classe": __import__(
            "src.domain.metrologia.padroes.enums", fromlist=["ClassePadrao"]
        ).ClassePadrao.E2,
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
    return cadastrar_padrao.CadastrarPadraoInput(**base)


class _FakeRepo:
    def __init__(self):
        self.store: dict = {}

    def obter_por_id(self, padrao_id):
        return self.store.get(padrao_id)

    def existe_numero_serie(self, tenant_id, numero_serie):
        return False

    def salvar_novo(self, snapshot):
        self.store[snapshot.id] = snapshot


# --------------------------------------------------------------------------
class TestINV_PAD_001:
    """numero_serie UNIQUE por tenant."""

    @pytest.mark.django_db(transaction=True)
    def test_numero_serie_duplicado_mesmo_tenant_bloqueia(self):
        tenant = TenantFactory(slug=f"inv1-{uuid4().hex[:6]}")
        _cria_padrao(tenant, numero_serie="DUP-001")
        with pytest.raises(IntegrityError), run_in_tenant_context(tenant.id):
            _cria_padrao(tenant, numero_serie="DUP-001")


class TestINV_PAD_002:
    """>=1 grandeza/faixa/incerteza — camada application + CHECK no banco."""

    def test_use_case_rejeita_grandezas_vazias(self):
        with pytest.raises(ValueError, match="INV-PAD-002"):
            _cadastrar_input(grandezas=())

    @pytest.mark.django_db(transaction=True)
    def test_db_check_rejeita_jsonb_vazio(self):
        tenant = TenantFactory(slug=f"inv2-{uuid4().hex[:6]}")
        with pytest.raises(IntegrityError), run_in_tenant_context(tenant.id):
            _cria_padrao(tenant, grandezas=[])


class TestINV_PAD_003:
    """Estado != EM_USO bloqueia uso."""

    @pytest.mark.django_db(transaction=True)
    def test_em_recal_externo_bloqueia(self):
        tenant = TenantFactory(slug=f"inv3-{uuid4().hex[:6]}")
        padrao = _cria_padrao(tenant, estado=EstadoPadrao.EM_RECAL_EXTERNO.value)
        with run_in_tenant_context(tenant.id):
            bloqueado, motivo = query_service.padrao_bloqueado_para_uso(
                padrao.id, hoje=HOJE
            )
        assert bloqueado is True
        assert "EM_USO" in motivo

    @pytest.mark.django_db(transaction=True)
    def test_recal_retornado_pendente_aprovacao_bloqueia(self):
        tenant = TenantFactory(slug=f"inv3b-{uuid4().hex[:6]}")
        padrao = _cria_padrao(
            tenant, estado=EstadoPadrao.RECAL_RETORNADO_PENDENTE_APROVACAO.value
        )
        with run_in_tenant_context(tenant.id):
            bloqueado, _m = query_service.padrao_bloqueado_para_uso(padrao.id, hoje=HOJE)
        assert bloqueado is True


class TestINV_PAD_004:
    """Recal/cert vencido bloqueia."""

    @pytest.mark.django_db(transaction=True)
    def test_proximo_recal_vencido_bloqueia(self):
        tenant = TenantFactory(slug=f"inv4-{uuid4().hex[:6]}")
        padrao = _cria_padrao(tenant, proximo_recal=date(2026, 1, 1))
        with run_in_tenant_context(tenant.id):
            bloqueado, motivo = query_service.padrao_bloqueado_para_uso(
                padrao.id, hoje=HOJE
            )
        assert bloqueado is True
        assert "recal vencido" in motivo

    @pytest.mark.django_db(transaction=True)
    def test_validade_cert_vencida_bloqueia(self):
        tenant = TenantFactory(slug=f"inv4b-{uuid4().hex[:6]}")
        padrao = _cria_padrao(tenant, validade_certificado_rastreabilidade=date(2026, 1, 1))
        with run_in_tenant_context(tenant.id):
            bloqueado, motivo = query_service.padrao_bloqueado_para_uso(
                padrao.id, hoje=HOJE
            )
        assert bloqueado is True
        assert "rastreabilidade vencido" in motivo


class TestINV_PAD_005:
    """vinculacao=RBC exige perfil A."""

    def test_rbc_perfil_nao_a_bloqueia(self):
        with pytest.raises(cadastrar_padrao.PerfilNaoPermiteRBCError):
            cadastrar_padrao.executar(
                _cadastrar_input(
                    vinculacao=VinculacaoCadeia.RBC, tenant_e_perfil_a=False
                ),
                _FakeRepo(),
            )

    def test_rbc_perfil_a_passa(self):
        out = cadastrar_padrao.executar(
            _cadastrar_input(vinculacao=VinculacaoCadeia.RBC, tenant_e_perfil_a=True),
            _FakeRepo(),
        )
        assert out.snapshot.vinculacao == VinculacaoCadeia.RBC


class TestINV_PAD_006:
    """incertezas/validade/proximo_recal só mudam via recal sancionado (trigger GUC)."""

    @pytest.mark.django_db(transaction=True)
    def test_update_direto_incertezas_sem_guc_rejeitado(self):
        tenant = TenantFactory(slug=f"inv6-{uuid4().hex[:6]}")
        padrao = _cria_padrao(tenant)
        nova = mappers.incertezas_para_json(
            (IncertezaExpandida(Decimal("0.999"), Decimal("2"), Decimal("0.9545"), "g"),)
        )
        # UPDATE direto (sem SET LOCAL app.padrao_recal_em_curso) -> trigger PG RAISE.
        with pytest.raises((InternalError, ProgrammingError, IntegrityError)):
            with run_in_tenant_context(tenant.id), transaction.atomic():
                PadraoMetrologico.objects.filter(id=padrao.id).update(
                    incertezas_certificado=nova
                )


class TestINV_PAD_007:
    """Auxiliar vinculado vigente vencido bloqueia o principal (cl. 6.4.5)."""

    @pytest.mark.django_db(transaction=True)
    def test_auxiliar_vencido_bloqueia_principal(self):
        tenant = TenantFactory(slug=f"inv7-{uuid4().hex[:6]}")
        principal = _cria_padrao(tenant)
        auxiliar = _cria_padrao(
            tenant,
            subtipo="AUXILIAR_TERMOMETRICO",
            proximo_recal=date(2026, 1, 1),  # vencido
        )
        _vincula_auxiliar(tenant, principal, auxiliar)
        with run_in_tenant_context(tenant.id):
            bloqueado, motivo = query_service.padrao_bloqueado_para_uso(
                principal.id, hoje=HOJE
            )
        assert bloqueado is True
        assert "INV-PAD-007" in motivo
        assert str(auxiliar.id) in motivo

    @pytest.mark.django_db(transaction=True)
    def test_auxiliar_saudavel_nao_bloqueia_principal(self):
        tenant = TenantFactory(slug=f"inv7b-{uuid4().hex[:6]}")
        principal = _cria_padrao(tenant)
        auxiliar = _cria_padrao(tenant, subtipo="AUXILIAR_TERMOMETRICO")  # saudavel
        _vincula_auxiliar(tenant, principal, auxiliar)
        with run_in_tenant_context(tenant.id):
            bloqueado, motivo = query_service.padrao_bloqueado_para_uso(
                principal.id, hoje=HOJE
            )
        assert bloqueado is False, motivo

    @pytest.mark.django_db(transaction=True)
    def test_vinculo_revogado_nao_bloqueia_mesmo_com_auxiliar_vencido(self):
        tenant = TenantFactory(slug=f"inv7c-{uuid4().hex[:6]}")
        principal = _cria_padrao(tenant)
        auxiliar = _cria_padrao(
            tenant, subtipo="AUXILIAR_TERMOMETRICO", proximo_recal=date(2026, 1, 1)
        )
        _vincula_auxiliar(tenant, principal, auxiliar, revogado=True)  # nao-vigente
        with run_in_tenant_context(tenant.id):
            bloqueado, motivo = query_service.padrao_bloqueado_para_uso(
                principal.id, hoje=HOJE
            )
        assert bloqueado is False, motivo


class TestINV_PAD_008:
    """Carta Shewhart exclusiva de perfil A (bloqueio por carta só sob A)."""

    def _serie_tendencia(self, tenant, padrao):
        from src.infrastructure.metrologia.padroes.models import (
            VerificacaoIntermediaria,
        )

        with run_in_tenant_context(tenant.id):
            for i in range(1, 8):
                VerificacaoIntermediaria.objects.create(
                    tenant=tenant,
                    padrao=padrao,
                    data_vi=datetime(2026, 1, i, tzinfo=UTC),
                    executor_id_hash="v1$e",
                    metodo_canonicalizado="m",
                    metodo_hash="v1$h",
                    resultado="APROVADO",
                    desvio_observado=Decimal(i),
                )

    @pytest.mark.django_db(transaction=True)
    def test_carta_violada_perfil_a_bloqueia(self):
        tenant = TenantFactory(slug=f"inv8a-{uuid4().hex[:6]}")
        padrao = _cria_padrao(tenant)
        self._serie_tendencia(tenant, padrao)
        with run_in_tenant_context(tenant.id):
            bloqueado, _m = query_service.padrao_bloqueado_para_uso(
                padrao.id, tenant_e_perfil_a=True, hoje=HOJE
            )
        assert bloqueado is True

    @pytest.mark.django_db(transaction=True)
    def test_carta_violada_perfil_nao_a_nao_bloqueia(self):
        tenant = TenantFactory(slug=f"inv8b-{uuid4().hex[:6]}")
        padrao = _cria_padrao(tenant)
        self._serie_tendencia(tenant, padrao)
        with run_in_tenant_context(tenant.id):
            bloqueado, motivo = query_service.padrao_bloqueado_para_uso(
                padrao.id, tenant_e_perfil_a=False, hoje=HOJE
            )
        assert bloqueado is False, motivo


class TestINV_PAD_009:
    """Valor convencional por 2 implementações do mesmo mensurando (cl. 7.11)."""

    def test_implementacoes_convergem(self):
        certs = [
            CertHistorico(Decimal("1.0000"), Decimal("0.0010"), 30),
            CertHistorico(Decimal("1.0002"), Decimal("0.0015"), 25),
        ]
        r = valor_convencional.calcular(certs)
        assert r.versao_motor == valor_convencional.VERSAO_MOTOR_VALOR_CONVENCIONAL
        assert r.n_certificados == 2

    def test_divergencia_injetada_levanta(self, monkeypatch):
        # Injeta bug: caminho B retorna valor diferente -> guard anti-divergencia.
        monkeypatch.setattr(
            valor_convencional,
            "_media_ponderada_decomposta",
            lambda certs: Decimal("999"),
        )
        certs = [
            CertHistorico(Decimal("1.0000"), Decimal("0.0010"), 30),
            CertHistorico(Decimal("1.0002"), Decimal("0.0015"), 25),
        ]
        with pytest.raises(DivergenciaImplementacoesError):
            valor_convencional.calcular(certs)


class TestINV_PAD_010:
    """AnaliseCartaControle é WORM (UPDATE/DELETE bloqueados por trigger)."""

    def _cria_analise(self, tenant, padrao):
        from src.infrastructure.metrologia.padroes.models import AnaliseCartaControle

        with run_in_tenant_context(tenant.id):
            return AnaliseCartaControle.objects.create(
                tenant=tenant,
                padrao=padrao,
                regra_violada="REGRA_5_TENDENCIA_7",
                pontos_referenciados_ids=[str(uuid4())],
                linha_central="4",
                ucl="10",
                lcl="-2",
                sigma="2",
                n_pontos=7,
                janela_meses=24,
                versao_motor_shewhart="shewhart-1.0.0",
                decisao_rt="ACEITO_COM_JUSTIFICATIVA",
                justificativa_canonicalizada="tendencia aceita dentro da tolerancia",
                justificativa_hash="v1$j",
            )

    @pytest.mark.django_db(transaction=True)
    def test_update_analise_carta_rejeitado(self):
        from src.infrastructure.metrologia.padroes.models import AnaliseCartaControle

        tenant = TenantFactory(slug=f"inv10a-{uuid4().hex[:6]}")
        padrao = _cria_padrao(tenant)
        analise = self._cria_analise(tenant, padrao)
        with pytest.raises((InternalError, ProgrammingError, IntegrityError)):
            with run_in_tenant_context(tenant.id), transaction.atomic():
                AnaliseCartaControle.objects.filter(id=analise.id).update(
                    decisao_rt="RECALIBRAR"
                )

    @pytest.mark.django_db(transaction=True)
    def test_delete_analise_carta_rejeitado(self):
        from src.infrastructure.metrologia.padroes.models import AnaliseCartaControle

        tenant = TenantFactory(slug=f"inv10b-{uuid4().hex[:6]}")
        padrao = _cria_padrao(tenant)
        analise = self._cria_analise(tenant, padrao)
        with pytest.raises((InternalError, ProgrammingError, IntegrityError)):
            with run_in_tenant_context(tenant.id), transaction.atomic():
                AnaliseCartaControle.objects.filter(id=analise.id).delete()
