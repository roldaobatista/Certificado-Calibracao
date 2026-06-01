"""M8 Fatia 1b (T-CER-020..028) — drill PG-real de schema + RLS + WORM + repos.

Cobre o COMPORTAMENTO em PG real (o que o drill estrutural e o hook não garantem):
- INV-CER-WORM-001: ponto_reconciliado + analise_reconciliacao_cert append-only
  (DELETE/UPDATE RAISE); certificado emitido imutável nos campos técnicos; transição
  emitido→substituida one-shot permitida; revogado_em one-shot.
- INV-025 INTACTO: cert emitido REAL ainda trava mutação de tag do equipamento
  (contrato cross-app preservado — ADR-0078).
- choice `substituida` presente no constraint (pré-requisito Fatia 2).
- INV-TENANT: RLS isola ponto/analise entre tenants.
- Repos round-trip (salvar_novo atômico cert + N pontos; marcar_substituida; análise).

GATE-CER-DRILL-LOCAL. Cada RAISE aborta a transação PG → cada `raises` isolado.
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

import pytest
from django.db import DatabaseError, IntegrityError, connection
from django.utils import timezone
from src.domain.metrologia.certificados.entities import (
    AnaliseReconciliacaoCertificado,
    CertificadoSnapshot,
    PontoReconciliadoSnapshot,
)
from src.domain.metrologia.certificados.enums import (
    CategoriaMotivoExclusao,
    ClassificacaoPonto,
    DecisaoReconciliacaoRT,
    EstadoCertificado,
    TipoAcreditacao,
)
from src.infrastructure.certificados.models import (
    AnaliseReconciliacaoCert,
    Certificado,
    PontoReconciliado,
    StatusCertificado,
)
from src.infrastructure.clientes.models import Cliente, TipoPessoa
from src.infrastructure.equipamentos.models import Equipamento
from src.infrastructure.metrologia.certificados.repositories import (
    DjangoAnaliseReconciliacaoRepository,
    DjangoCertificadoRepository,
)
from src.infrastructure.multitenant.connection import run_in_tenant_context

from tests.factories import TenantFactory


def _cenario(slug_prefix: str):
    sfx = uuid4().hex[:8]
    tenant = TenantFactory(slug=f"{slug_prefix}-{sfx}")
    with run_in_tenant_context(tenant.id):
        cliente = Cliente.objects.create(
            tenant=tenant,
            tipo_pessoa=TipoPessoa.PJ,
            documento="11222333000181",
            nome="Cliente Cert M8",
            aceite_lgpd_dispensa_motivo="pj_sem_pf_associada",
        )
        equipamento = Equipamento.objects.create(
            tenant=tenant,
            tag=f"CERT-{sfx}",
            numero_serie=f"NS-{sfx}",
            fabricante="Toledo",
            modelo="Prix 4",
            cliente_atual=cliente,
            perfil_tenant_snapshot={"perfil": "A"},
        )
    return tenant, equipamento


def _cert_snapshot(tenant_id, equipamento_id, *, calibracao_id, cert_id, numero_interno=1, versao=1):
    return CertificadoSnapshot(
        id=cert_id,
        tenant_id=tenant_id,
        calibracao_id=calibracao_id,
        equipamento_id=equipamento_id,
        numero_interno=numero_interno,
        numero_certificado=f"BALANCAS-2026-{numero_interno:06d}",
        versao=versao,
        versao_anterior_id=None,
        status=EstadoCertificado.EMITIDO,
        perfil_emissor_no_momento="A",
        faixa_certificado_min=Decimal("100"),
        faixa_certificado_max=Decimal("500"),
        tipo_acreditacao=TipoAcreditacao.RBC,
        snapshot_equipamento_json={"tag": "CERT"},
        snapshot_padroes_usados_json=[{"padrao_id": "p1", "calibracao_padrao_vigencia_fim": "2027-01-01"}],
        cliente_ref_hash="v01$cli",
        reconciliacao_hash="v01$recon",
        emitido_em=timezone.now(),
        correlation_id=uuid4(),
        regra_decisao_snapshot=None,
    )


def _ponto_snapshot(tenant_id, cert_id, ponto="100"):
    return PontoReconciliadoSnapshot(
        id=uuid4(),
        tenant_id=tenant_id,
        certificado_id=cert_id,
        ponto_calibracao=Decimal(ponto),
        valor_reportado=Decimal(ponto),
        U_no_ponto=Decimal("0.8"),
        k_no_ponto=Decimal("2"),
        nivel_confianca_no_ponto=Decimal("0.9545"),
        grau_liberdade_efetivo_no_ponto=Decimal("60"),
        cmc_no_ponto=Decimal("0.5"),
        classificacao=ClassificacaoPonto.RBC_OK,
        u_igual_cmc_suspeita=False,
        incluido_no_certificado=True,
        ressalva_nao_rbc="",
    )


def _emitir_real(tenant, equipamento, calibracao_id=None):
    cid = uuid4()
    calibracao_id = calibracao_id or uuid4()
    repo = DjangoCertificadoRepository()
    snap = _cert_snapshot(tenant.id, equipamento.id, calibracao_id=calibracao_id, cert_id=cid)
    with run_in_tenant_context(tenant.id):
        repo.salvar_novo(snap, [_ponto_snapshot(tenant.id, cid)])
    return cid, calibracao_id


# =============================================================
# Estrutura — RLS + FORCE + policies nas 2 tabelas novas
# =============================================================
@pytest.mark.django_db
def test_tabelas_reconciliacao_tem_rls_force_e_policies():
    for tabela in ("ponto_reconciliado", "analise_reconciliacao_cert"):
        with connection.cursor() as cur:
            cur.execute(
                "SELECT relrowsecurity, relforcerowsecurity FROM pg_class c "
                "JOIN pg_namespace n ON c.relnamespace=n.oid "
                "WHERE n.nspname='public' AND c.relkind='r' AND c.relname=%s",
                [tabela],
            )
            enabled, force = cur.fetchone()
            cur.execute(
                "SELECT COUNT(*) FROM pg_policies WHERE schemaname='public' AND tablename=%s",
                [tabela],
            )
            n = cur.fetchone()[0]
        assert enabled, f"INV-TENANT-001: {tabela} sem RLS"
        assert force, f"INV-TENANT-002: {tabela} sem FORCE"
        assert n >= 4, f"{tabela} com <4 policies"


@pytest.mark.django_db
def test_choice_substituida_presente_no_constraint():
    """Pré-requisito da Fatia 2 (reemissão grava status=substituida)."""
    valores = {v for v, _ in StatusCertificado.choices}
    assert "substituida" in valores
    assert "emitido" in valores  # INV-025 contrato intocado


# =============================================================
# INV-CER-WORM-001 — ponto_reconciliado / analise append-only
# =============================================================
@pytest.mark.django_db(transaction=True)
def test_ponto_reconciliado_delete_bloqueia():
    tenant, eq = _cenario("certdel")
    cid, _ = _emitir_real(tenant, eq)
    with run_in_tenant_context(tenant.id), pytest.raises(DatabaseError):
        PontoReconciliado.objects.filter(certificado_id=cid).delete()


@pytest.mark.django_db(transaction=True)
def test_ponto_reconciliado_update_bloqueia():
    tenant, eq = _cenario("certupd")
    cid, _ = _emitir_real(tenant, eq)
    with run_in_tenant_context(tenant.id), pytest.raises(DatabaseError):
        PontoReconciliado.objects.filter(certificado_id=cid).update(u_no_ponto=Decimal("9"))


@pytest.mark.django_db(transaction=True)
def test_analise_reconciliacao_append_only():
    tenant, eq = _cenario("certana")
    calib = uuid4()
    repo = DjangoAnaliseReconciliacaoRepository()
    dec = AnaliseReconciliacaoCertificado(
        id=uuid4(), tenant_id=tenant.id, calibracao_id=calib, ponto_calibracao=Decimal("100"),
        decisao_rt=DecisaoReconciliacaoRT.EXCLUIR_PONTO,
        categoria_motivo=CategoriaMotivoExclusao.U_MAIOR_QUE_CMC_BUG,
        justificativa_canonicalizada="exclusao do ponto por bug de cmc otimista",
        justificativa_hash="v01$j", criado_em=datetime(2026, 5, 31, tzinfo=UTC),
        correlation_id=uuid4(),
    )
    with run_in_tenant_context(tenant.id):
        repo.salvar_decisao(dec)
    with run_in_tenant_context(tenant.id), pytest.raises(DatabaseError):
        AnaliseReconciliacaoCert.objects.filter(id=dec.id).delete()
    with run_in_tenant_context(tenant.id), pytest.raises(DatabaseError):
        AnaliseReconciliacaoCert.objects.filter(id=dec.id).update(decisao_rt="ABORTAR")


# =============================================================
# INV-CER-WORM-001 — certificado emitido imutável (WORM seletivo)
# =============================================================
@pytest.mark.django_db(transaction=True)
def test_certificado_update_campo_tecnico_bloqueia():
    tenant, eq = _cenario("certwt")
    cid, _ = _emitir_real(tenant, eq)
    with run_in_tenant_context(tenant.id), pytest.raises(DatabaseError):
        Certificado.all_objects.filter(id=cid).update(reconciliacao_hash="v01$ADULTERADO")


@pytest.mark.django_db(transaction=True)
def test_certificado_emitido_para_substituida_permitido():
    tenant, eq = _cenario("certsub")
    cid, _ = _emitir_real(tenant, eq)
    repo = DjangoCertificadoRepository()
    with run_in_tenant_context(tenant.id):
        ok = repo.marcar_substituida(certificado_id=cid, revision_anterior=0)
        assert ok
        assert Certificado.all_objects.get(id=cid).status == "substituida"


@pytest.mark.django_db(transaction=True)
def test_certificado_revogado_em_one_shot():
    tenant, eq = _cenario("certrev")
    cid, _ = _emitir_real(tenant, eq)
    with run_in_tenant_context(tenant.id):
        # ligar revogado_em (NULL→valor) é permitido
        Certificado.all_objects.filter(id=cid).update(
            status="revogado", revogado_em=timezone.now()
        )
    with run_in_tenant_context(tenant.id), pytest.raises(DatabaseError):
        # re-mexer em revogado_em (one-shot) bloqueia
        Certificado.all_objects.filter(id=cid).update(revogado_em=timezone.now())


# =============================================================
# INV-025 INTACTO — cert emitido REAL ainda trava equipamento
# =============================================================
@pytest.mark.django_db(transaction=True)
def test_inv_025_intacto_com_cert_emitido_real():
    tenant, eq = _cenario("cert025")
    _emitir_real(tenant, eq)
    with run_in_tenant_context(tenant.id), pytest.raises(DatabaseError):
        Equipamento.objects.filter(id=eq.id).update(tag="TAG-MUDADA")


# =============================================================
# INV-TENANT — RLS isola ponto/analise entre tenants
# =============================================================
@pytest.mark.django_db(transaction=True)
def test_rls_isola_ponto_cross_tenant():
    ta, eqa = _cenario("certta")
    tb, _ = _cenario("certtb")
    cid, _ = _emitir_real(ta, eqa)
    with run_in_tenant_context(tb.id):
        assert not PontoReconciliado.objects.filter(certificado_id=cid).exists()
    with run_in_tenant_context(ta.id):
        assert PontoReconciliado.objects.filter(certificado_id=cid).exists()


# =============================================================
# Repos — round-trip + idempotência (T-CER-027b)
# =============================================================
@pytest.mark.django_db(transaction=True)
def test_repo_salvar_novo_e_obter_por_id_round_trip():
    tenant, eq = _cenario("certrt")
    cid, calib = _emitir_real(tenant, eq)
    repo = DjangoCertificadoRepository()
    with run_in_tenant_context(tenant.id):
        snap = repo.obter_por_id(cid)
        assert snap is not None
        assert snap.tipo_acreditacao is TipoAcreditacao.RBC
        assert snap.status is EstadoCertificado.EMITIDO
        assert snap.faixa_certificado_min == Decimal("100")
        assert snap.snapshot_padroes_usados_json[0]["padrao_id"] == "p1"
        assert repo.existe_chave(tenant_id=tenant.id, calibracao_id=calib, versao=1)


@pytest.mark.django_db(transaction=True)
def test_repo_analise_listar_e_mapa_por_ponto():
    tenant, _ = _cenario("certam")
    calib = uuid4()
    repo = DjangoAnaliseReconciliacaoRepository()
    dec = AnaliseReconciliacaoCertificado(
        id=uuid4(), tenant_id=tenant.id, calibracao_id=calib, ponto_calibracao=Decimal("100"),
        decisao_rt=DecisaoReconciliacaoRT.EMITIR_NAO_RBC_NO_PONTO,
        categoria_motivo=CategoriaMotivoExclusao.OUTRO,
        justificativa_canonicalizada="ponto reportado sem selo rbc por estar fora do escopo",
        justificativa_hash="v01$j", criado_em=datetime(2026, 5, 31, tzinfo=UTC),
        correlation_id=uuid4(), ressalva_nao_rbc="ponto não coberto pela acreditação RBC",
    )
    with run_in_tenant_context(tenant.id):
        repo.salvar_decisao(dec)
        assert repo.existe_decisao_para_ponto(
            tenant_id=tenant.id, calibracao_id=calib, ponto_calibracao=Decimal("100")
        )
        mapa = repo.obter_decisao_por_ponto(tenant_id=tenant.id, calibracao_id=calib)
        assert Decimal("100") in mapa
        assert mapa[Decimal("100")].ressalva_nao_rbc.startswith("ponto não")


@pytest.mark.django_db(transaction=True)
def test_unique_ponto_por_certificado():
    tenant, eq = _cenario("certuq")
    cid, _ = _emitir_real(tenant, eq)
    # 2º ponto com mesmo ponto_calibracao no mesmo certificado → UNIQUE viola
    with run_in_tenant_context(tenant.id), pytest.raises(IntegrityError):
        PontoReconciliado.objects.create(
            id=uuid4(), tenant=tenant, certificado_id=cid,
            ponto_calibracao=Decimal("100"), valor_reportado=Decimal("100"),
            u_no_ponto=Decimal("0.8"), k_no_ponto=Decimal("2"),
            nivel_confianca_no_ponto=Decimal("0.9545"),
            grau_liberdade_efetivo_no_ponto=Decimal("60"),
            classificacao="RBC_OK",
        )
