"""Frente `configuracoes-sistema` — Fatia 1b (T-CFG-020..028): schema PG-real.

Cobre o COMPORTAMENTO em PG real (o que o drill estrutural não garante):
- RLS FORCE + 4 policies + isolamento cross-tenant (INV-TENANT-001/002).
- INV-036: CNPJ de empresa único por tenant; INV-037: ≤1 matriz (UNIQUE parcial).
- INV-CFG-IMPOSTO-IMUTAVEL: campo probatório imutável RAISE; DELETE físico RAISE;
  `vigencia_fim`/`revogado_em` one-shot.
- INV-CFG-IMPOSTO-SEM-SOBREPOSICAO: exclusion btree_gist (overlap RAISE; encadeado
  half-open OK; linha REVOGADA sai da constraint).
- INV-028: decremento de `proximo_numero` RAISE; reset anual legítimo OK;
  tipo/prefixo/regime imutáveis (ADR-0080).
- INV-CFG-NUM-ATOMICA (gap-less, motor M8): reserva densa 1,2,...; consecutividade
  no INSERT; confirmação one-shot; DELETE de confirmado RAISE; reserva expirada
  devolve o número; UNIQUE parcial da chave de série com filial NULL.

Cada RAISE aborta a transação PG → cada cenário em teste isolado (TST-004).
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from django.db import DatabaseError, IntegrityError, connection
from django.utils import timezone
from src.infrastructure.configuracoes_sistema.models import (
    Empresa,
    Filial,
    Imposto,
    NumeroDocumentoReservado,
    SerieDocumento,
)
from src.infrastructure.configuracoes_sistema.repositories import (
    DjangoSerieDocumentoRepository,
)
from src.infrastructure.multitenant.connection import run_in_tenant_context

from tests.factories import TenantFactory

TABELAS = (
    "empresa",
    "filial",
    "imposto",
    "serie_documento",
    "numero_documento_reservado",
)

# CNPJs com DV válido (VO ADR-0017) — clássicos de teste, não-reais.
CNPJ_A = "11222333000181"
CNPJ_B = "11444777000161"

_INICIO_2026 = datetime(2026, 1, 1, tzinfo=UTC)
_MEIO_2026 = datetime(2026, 6, 1, tzinfo=UTC)


def _cria_empresa(tenant, *, cnpj: str = CNPJ_A) -> Empresa:
    with run_in_tenant_context(tenant.id):
        return Empresa.objects.create(
            tenant=tenant,
            razao_social="Balanças Solution LTDA",
            cnpj=cnpj,
            regime_tributario="simples_nacional",
        )


def _cria_imposto(
    tenant,
    *,
    tipo: str = "iss",
    inicio=_INICIO_2026,
    fim=None,
) -> Imposto:
    with run_in_tenant_context(tenant.id):
        return Imposto.objects.create(
            tenant=tenant,
            tipo=tipo,
            aliquota="5.0000",
            vigencia_inicio=inicio,
            vigencia_fim=fim,
        )


def _cria_serie(
    tenant,
    *,
    tipo: str = "os",
    prefixo: str = "OS",
    regime: str = "buracos_aceitos",
    reset_anual: bool = False,
) -> SerieDocumento:
    with run_in_tenant_context(tenant.id):
        return SerieDocumento.objects.create(
            tenant=tenant,
            tipo=tipo,
            prefixo=prefixo,
            regime_numeracao=regime,
            reset_anual=reset_anual,
        )


# === estrutura (INV-TENANT-001/002) ===


@pytest.mark.django_db
def test_rls_force_e_4_policies_nas_5_tabelas() -> None:
    with connection.cursor() as cur:
        for tabela in TABELAS:
            cur.execute(
                "SELECT relrowsecurity, relforcerowsecurity FROM pg_class c "
                "JOIN pg_namespace n ON c.relnamespace=n.oid "
                "WHERE n.nspname='public' AND c.relname=%s",
                [tabela],
            )
            enabled, forced = cur.fetchone()
            cur.execute("SELECT COUNT(*) FROM pg_policies WHERE tablename=%s", [tabela])
            n_pol = cur.fetchone()[0]
            assert enabled, f"INV-TENANT-001: {tabela} sem RLS"
            assert forced, f"INV-TENANT-002: {tabela} sem FORCE"
            assert n_pol >= 4, f"{tabela} com <4 policies ({n_pol})"


# === RLS cross-tenant ===


@pytest.mark.django_db(transaction=True)
def test_rls_isola_empresa_entre_tenants() -> None:
    tenant_a = TenantFactory()
    tenant_b = TenantFactory()
    empresa_a = _cria_empresa(tenant_a)
    with run_in_tenant_context(tenant_b.id):
        assert not Empresa.objects.filter(id=empresa_a.id).exists()
    with run_in_tenant_context(tenant_a.id):
        assert Empresa.objects.filter(id=empresa_a.id).exists()


# === INV-036: CNPJ único por tenant ===


@pytest.mark.django_db(transaction=True)
def test_cnpj_empresa_duplicado_no_tenant_raise() -> None:
    tenant = TenantFactory()
    _cria_empresa(tenant, cnpj=CNPJ_A)
    with pytest.raises(IntegrityError):
        _cria_empresa(tenant, cnpj=CNPJ_A)


@pytest.mark.django_db(transaction=True)
def test_cnpj_igual_em_tenants_diferentes_ok() -> None:
    empresa_1 = _cria_empresa(TenantFactory(), cnpj=CNPJ_A)
    empresa_2 = _cria_empresa(TenantFactory(), cnpj=CNPJ_A)
    assert empresa_1.id != empresa_2.id


# === INV-037: <=1 matriz por empresa (UNIQUE parcial) ===


@pytest.mark.django_db(transaction=True)
def test_segunda_matriz_raise() -> None:
    tenant = TenantFactory()
    empresa = _cria_empresa(tenant)
    with run_in_tenant_context(tenant.id):
        Filial.objects.create(
            tenant=tenant, empresa=empresa, cnpj=CNPJ_A, nome="Matriz", eh_matriz=True
        )
        with pytest.raises(IntegrityError):
            Filial.objects.create(
                tenant=tenant, empresa=empresa, cnpj=CNPJ_B, nome="Outra", eh_matriz=True
            )


# === INV-CFG-IMPOSTO-IMUTAVEL ===


@pytest.mark.django_db(transaction=True)
def test_aliquota_imutavel_raise() -> None:
    tenant = TenantFactory()
    imposto = _cria_imposto(tenant)
    with run_in_tenant_context(tenant.id), pytest.raises(DatabaseError):
        Imposto.objects.filter(id=imposto.id).update(aliquota="7.0000")


@pytest.mark.django_db(transaction=True)
def test_delete_fisico_imposto_raise() -> None:
    tenant = TenantFactory()
    imposto = _cria_imposto(tenant)
    with run_in_tenant_context(tenant.id), pytest.raises(DatabaseError):
        Imposto.objects.filter(id=imposto.id).delete()


@pytest.mark.django_db(transaction=True)
def test_encerrar_vigencia_null_para_data_ok_e_one_shot() -> None:
    tenant = TenantFactory()
    imposto = _cria_imposto(tenant)
    with run_in_tenant_context(tenant.id):
        n = Imposto.objects.filter(id=imposto.id).update(vigencia_fim=_MEIO_2026)
        assert n == 1
    with run_in_tenant_context(tenant.id), pytest.raises(DatabaseError):
        Imposto.objects.filter(id=imposto.id).update(vigencia_fim=_MEIO_2026 + timedelta(days=30))


# === INV-CFG-IMPOSTO-SEM-SOBREPOSICAO (exclusion btree_gist) ===


@pytest.mark.django_db(transaction=True)
def test_vigencia_sobreposta_mesmo_tipo_raise() -> None:
    tenant = TenantFactory()
    _cria_imposto(tenant, inicio=_INICIO_2026, fim=None)  # aberta
    with pytest.raises(IntegrityError):
        _cria_imposto(tenant, inicio=_MEIO_2026, fim=None)


@pytest.mark.django_db(transaction=True)
def test_vigencia_encadeada_half_open_ok() -> None:
    tenant = TenantFactory()
    _cria_imposto(tenant, inicio=_INICIO_2026, fim=_MEIO_2026)
    imposto_2 = _cria_imposto(tenant, inicio=_MEIO_2026, fim=None)
    assert imposto_2.id is not None


@pytest.mark.django_db(transaction=True)
def test_linha_revogada_sai_da_exclusion() -> None:
    tenant = TenantFactory()
    errada = _cria_imposto(tenant, inicio=_INICIO_2026, fim=None)
    with run_in_tenant_context(tenant.id):
        n = Imposto.objects.filter(id=errada.id).update(
            revogado_em=timezone.now(),
            motivo_revogacao="aliquota digitada errada no cadastro",
        )
        assert n == 1
    corrigida = _cria_imposto(tenant, inicio=_INICIO_2026, fim=None)
    assert corrigida.id != errada.id


# === INV-028: proximo_numero nunca diminui (serie_documento) ===


@pytest.mark.django_db(transaction=True)
def test_decremento_proximo_numero_raise() -> None:
    tenant = TenantFactory()
    serie = _cria_serie(tenant)
    with run_in_tenant_context(tenant.id):
        SerieDocumento.objects.filter(id=serie.id).update(proximo_numero=10)
        with pytest.raises(DatabaseError):
            SerieDocumento.objects.filter(id=serie.id).update(proximo_numero=5)


@pytest.mark.django_db(transaction=True)
def test_tipo_e_regime_imutaveis_raise() -> None:
    tenant = TenantFactory()
    serie = _cria_serie(tenant, tipo="os", regime="buracos_aceitos")
    with run_in_tenant_context(tenant.id), pytest.raises(DatabaseError):
        SerieDocumento.objects.filter(id=serie.id).update(tipo="fatura")


@pytest.mark.django_db(transaction=True)
def test_chave_serie_global_unica_com_filial_null_raise() -> None:
    tenant = TenantFactory()
    _cria_serie(tenant, tipo="os", prefixo="OS")
    with pytest.raises(IntegrityError):
        _cria_serie(tenant, tipo="os", prefixo="OS")


# === ADR-0080: regime BURACOS_ACEITOS (UPDATE atômico + reset anual TL-07) ===


@pytest.mark.django_db(transaction=True)
def test_buracos_aceitos_aloca_sequencial() -> None:
    tenant = TenantFactory()
    serie = _cria_serie(tenant, tipo="os", regime="buracos_aceitos")
    repo = DjangoSerieDocumentoRepository()
    with run_in_tenant_context(tenant.id):
        r1 = repo.reservar_numero(tenant_id=tenant.id, serie_id=serie.id)
        assert r1.sequencial == 1
        assert r1.reserva_id is None  # buracos-aceitos: nada a confirmar
        assert repo.reservar_numero(tenant_id=tenant.id, serie_id=serie.id).sequencial == 2


@pytest.mark.django_db(transaction=True)
def test_reset_anual_volta_para_1_sem_violar_inv028() -> None:
    tenant = TenantFactory()
    serie = _cria_serie(tenant, tipo="orcamento", prefixo="ORC", reset_anual=True)
    repo = DjangoSerieDocumentoRepository()
    with run_in_tenant_context(tenant.id):
        assert (
            repo.reservar_numero(tenant_id=tenant.id, serie_id=serie.id, ano=2026).sequencial
            == 1
        )
        assert (
            repo.reservar_numero(tenant_id=tenant.id, serie_id=serie.id, ano=2026).sequencial
            == 2
        )
        # Virada de ano: contador reinicia (TL-07) — trigger INV-028 permite
        # porque ano_corrente troca junto.
        assert (
            repo.reservar_numero(tenant_id=tenant.id, serie_id=serie.id, ano=2027).sequencial
            == 1
        )


# === ADR-0080: regime GAP_LESS (motor M8 — INV-CFG-NUM-ATOMICA) ===


@pytest.mark.django_db(transaction=True)
def test_gap_less_reserva_densa_e_confirmacao_one_shot() -> None:
    tenant = TenantFactory()
    serie = _cria_serie(tenant, tipo="fatura", prefixo="FAT", regime="gap_less")
    repo = DjangoSerieDocumentoRepository()
    with run_in_tenant_context(tenant.id):
        r1 = repo.reservar_numero(tenant_id=tenant.id, serie_id=serie.id)
        assert r1.sequencial == 1
        assert r1.reserva_id is not None  # gap-less: alvo do confirmar
        r2 = repo.reservar_numero(tenant_id=tenant.id, serie_id=serie.id)
        assert r2.sequencial == 2
        assert repo.confirmar_numero(tenant_id=tenant.id, reserva_id=r1.reserva_id)
        # One-shot: segunda confirmação da mesma reserva é recusada.
        assert not repo.confirmar_numero(tenant_id=tenant.id, reserva_id=r1.reserva_id)


@pytest.mark.django_db(transaction=True)
def test_gap_less_reserva_expirada_devolve_numero() -> None:
    tenant = TenantFactory()
    serie = _cria_serie(tenant, tipo="fatura", prefixo="FAT", regime="gap_less")
    repo = DjangoSerieDocumentoRepository()
    with run_in_tenant_context(tenant.id):
        r_velha = repo.reservar_numero(tenant_id=tenant.id, serie_id=serie.id)
        assert r_velha.sequencial == 1
        # Reserva não-confirmada expira (TTL no passado) → número volta à sequência.
        NumeroDocumentoReservado.objects.filter(serie_id=serie.id, sequencial=1).update(
            ttl_expira_em=timezone.now() - timedelta(minutes=1)
        )
        r_nova = repo.reservar_numero(tenant_id=tenant.id, serie_id=serie.id)
        assert r_nova.sequencial == 1
        # CFG-IDEMP-01: a reserva NOVA tem id próprio — confirmar com o id da
        # reserva expirada NÃO confirma a reserva viva de fluxo alheio.
        assert r_nova.reserva_id != r_velha.reserva_id
        assert r_velha.reserva_id is not None
        assert not repo.confirmar_numero(tenant_id=tenant.id, reserva_id=r_velha.reserva_id)
        viva = NumeroDocumentoReservado.objects.get(id=r_nova.reserva_id)
        assert viva.confirmado is False


@pytest.mark.django_db(transaction=True)
def test_gap_less_menor_livre_sql_equivale_ao_dominio_com_buraco() -> None:
    """PERF M7 (auditoria P9): o menor-livre via SQL anti-join deve equivaler ao
    `proximo_sequencial` puro do domínio — inclusive com BURACO interno entre
    confirmados (reserva 2 confirma; 1 e 3 expiram → livre=1, não 3; o atalho
    MAX(confirmado)+1 daria 3 e furaria a densidade)."""
    from src.domain.metrologia.certificados.numeracao import proximo_sequencial

    tenant = TenantFactory()
    serie = _cria_serie(tenant, tipo="fatura", prefixo="FAT", regime="gap_less")
    repo = DjangoSerieDocumentoRepository()
    with run_in_tenant_context(tenant.id):
        r1 = repo.reservar_numero(tenant_id=tenant.id, serie_id=serie.id)
        r2 = repo.reservar_numero(tenant_id=tenant.id, serie_id=serie.id)
        r3 = repo.reservar_numero(tenant_id=tenant.id, serie_id=serie.id)
        assert (r1.sequencial, r2.sequencial, r3.sequencial) == (1, 2, 3)
        assert r2.reserva_id is not None
        assert repo.confirmar_numero(tenant_id=tenant.id, reserva_id=r2.reserva_id)
        # 1 e 3 expiram → buraco interno {2 confirmado}.
        NumeroDocumentoReservado.objects.filter(
            serie_id=serie.id, sequencial__in=(1, 3)
        ).update(ttl_expira_em=timezone.now() - timedelta(minutes=1))

        # Oráculo puro do domínio sobre o conjunto vivo pós-liberação ({2}).
        assert proximo_sequencial([2]) == 1

        r4 = repo.reservar_numero(tenant_id=tenant.id, serie_id=serie.id)
        assert r4.sequencial == 1  # SQL == domínio: preenche o buraco
        r5 = repo.reservar_numero(tenant_id=tenant.id, serie_id=serie.id)
        assert r5.sequencial == proximo_sequencial([1, 2]) == 3
        r6 = repo.reservar_numero(tenant_id=tenant.id, serie_id=serie.id)
        assert r6.sequencial == proximo_sequencial([1, 2, 3]) == 4


@pytest.mark.django_db(transaction=True)
def test_gap_less_insert_fora_de_sequencia_raise() -> None:
    tenant = TenantFactory()
    serie = _cria_serie(tenant, tipo="certificado", prefixo="CERT", regime="gap_less")
    with run_in_tenant_context(tenant.id), pytest.raises(DatabaseError):
        NumeroDocumentoReservado.objects.create(
            tenant=tenant,
            serie_id=serie.id,
            ano=0,
            sequencial=5,  # max+1 seria 1 — buraco proibido
            ttl_expira_em=timezone.now() + timedelta(minutes=5),
        )


@pytest.mark.django_db(transaction=True)
def test_gap_less_delete_confirmado_raise() -> None:
    tenant = TenantFactory()
    serie = _cria_serie(tenant, tipo="fatura", prefixo="FAT", regime="gap_less")
    repo = DjangoSerieDocumentoRepository()
    with run_in_tenant_context(tenant.id):
        r = repo.reservar_numero(tenant_id=tenant.id, serie_id=serie.id)
        assert r.reserva_id is not None
        assert repo.confirmar_numero(tenant_id=tenant.id, reserva_id=r.reserva_id)
        with pytest.raises(DatabaseError):
            NumeroDocumentoReservado.objects.filter(serie_id=serie.id, sequencial=1).delete()


# === regressão de derivação (domínio × choices do model) ===


@pytest.mark.django_db(transaction=True)
def test_reservar_em_serie_inexistente_raise() -> None:
    tenant = TenantFactory()
    repo = DjangoSerieDocumentoRepository()
    with run_in_tenant_context(tenant.id), pytest.raises(LookupError):
        repo.reservar_numero(tenant_id=tenant.id, serie_id=uuid4())
