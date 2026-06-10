"""TST-004 — classes nomeando cada INV da frente configuracoes-sistema (T-CFG-040).

Convenção do projeto (análoga `test_inv_fis_classes_nomeadas.py`): todo INV
crítico tem ≥1 teste cujo NOME cita o ID. Cada classe `TestINV_*` exercita a
barreira REAL — PG-real onde a defesa é trigger/constraint/RLS; puro onde é
domínio/use case. Cobre: INV-CFG-NUM-ATOMICA, INV-CFG-IMPOSTO-IMUTAVEL,
INV-CFG-IMPOSTO-SEM-SOBREPOSICAO + as reusadas INV-028/036/037.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from django.db import DatabaseError, IntegrityError
from django.utils import timezone

from src.domain.configuracoes_sistema.enums import RegimeNumeracao, TipoDocumento
from src.domain.configuracoes_sistema.transicoes import regime_numeracao_do_tipo
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

CNPJ_A = "11222333000181"
CNPJ_B = "11444777000161"
_INICIO = datetime(2026, 1, 1, tzinfo=UTC)


def _empresa(tenant, *, cnpj=CNPJ_A):
    with run_in_tenant_context(tenant.id):
        return Empresa.objects.create(
            tenant=tenant,
            razao_social="Empresa Teste LTDA",
            cnpj=cnpj,
            regime_tributario="simples_nacional",
        )


def _imposto(tenant, *, inicio=_INICIO, fim=None):
    with run_in_tenant_context(tenant.id):
        return Imposto.objects.create(
            tenant=tenant,
            tipo="iss",
            aliquota="5.0000",
            vigencia_inicio=inicio,
            vigencia_fim=fim,
        )


def _serie(tenant, *, tipo="fatura", prefixo="FAT", regime="gap_less"):
    with run_in_tenant_context(tenant.id):
        return SerieDocumento.objects.create(
            tenant=tenant, tipo=tipo, prefixo=prefixo, regime_numeracao=regime
        )


class TestINV_CFG_NUM_ATOMICA:
    """Reserva atômica sem duplicata; gap-less denso (ADR-0080)."""

    def test_regime_derivado_do_tipo_nunca_do_caller(self) -> None:
        assert regime_numeracao_do_tipo(TipoDocumento.FATURA) is RegimeNumeracao.GAP_LESS
        assert (
            regime_numeracao_do_tipo(TipoDocumento.CERTIFICADO)
            is RegimeNumeracao.GAP_LESS
        )
        for tipo in (
            TipoDocumento.OS,
            TipoDocumento.ORCAMENTO,
            TipoDocumento.RECIBO,
            TipoDocumento.INTERNO,
        ):
            assert regime_numeracao_do_tipo(tipo) is RegimeNumeracao.BURACOS_ACEITOS

    @pytest.mark.django_db(transaction=True)
    def test_gap_less_consecutividade_trigger_rejeita_buraco(self) -> None:
        tenant = TenantFactory()
        serie = _serie(tenant)
        with run_in_tenant_context(tenant.id), pytest.raises(DatabaseError):
            NumeroDocumentoReservado.objects.create(
                tenant=tenant,
                serie_id=serie.id,
                ano=0,
                sequencial=7,  # max+1 seria 1
                ttl_expira_em=timezone.now() + timedelta(minutes=5),
            )

    @pytest.mark.django_db(transaction=True)
    def test_confirmacao_one_shot_e_delete_de_confirmado_bloqueado(self) -> None:
        tenant = TenantFactory()
        serie = _serie(tenant)
        repo = DjangoSerieDocumentoRepository()
        with run_in_tenant_context(tenant.id):
            reserva = repo.reservar_numero(tenant_id=tenant.id, serie_id=serie.id)
            assert reserva.sequencial == 1
            assert reserva.reserva_id is not None
            # CFG-IDEMP-01: confirmação endereça pela PK da reserva (molde M8).
            assert repo.confirmar_numero(tenant_id=tenant.id, reserva_id=reserva.reserva_id)
            # one-shot: 2ª confirmação recusada
            assert not repo.confirmar_numero(
                tenant_id=tenant.id, reserva_id=reserva.reserva_id
            )
            # número confirmado é preservado (cancelamento não devolve)
            with pytest.raises(DatabaseError):
                NumeroDocumentoReservado.objects.filter(
                    serie_id=serie.id, sequencial=1
                ).delete()

    @pytest.mark.django_db(transaction=True)
    def test_unique_chave_reserva_sem_duplicata(self) -> None:
        tenant = TenantFactory()
        serie = _serie(tenant)
        with run_in_tenant_context(tenant.id):
            NumeroDocumentoReservado.objects.create(
                tenant=tenant,
                serie_id=serie.id,
                ano=0,
                sequencial=1,
                ttl_expira_em=timezone.now() + timedelta(minutes=5),
            )
            with pytest.raises(IntegrityError):
                NumeroDocumentoReservado.objects.create(
                    tenant=tenant,
                    serie_id=serie.id,
                    ano=0,
                    sequencial=1,
                    ttl_expira_em=timezone.now() + timedelta(minutes=5),
                )


class TestINV_CFG_IMPOSTO_IMUTAVEL:
    """Linha versionada: campos probatórios congelados; one-shot; sem DELETE."""

    @pytest.mark.django_db(transaction=True)
    def test_update_de_aliquota_bloqueado(self) -> None:
        tenant = TenantFactory()
        imposto = _imposto(tenant)
        with run_in_tenant_context(tenant.id), pytest.raises(DatabaseError):
            Imposto.objects.filter(id=imposto.id).update(aliquota="9.0000")

    @pytest.mark.django_db(transaction=True)
    def test_delete_fisico_bloqueado_retencao_5a(self) -> None:
        tenant = TenantFactory()
        imposto = _imposto(tenant)
        with run_in_tenant_context(tenant.id), pytest.raises(DatabaseError):
            Imposto.objects.filter(id=imposto.id).delete()

    @pytest.mark.django_db(transaction=True)
    def test_vigencia_fim_one_shot(self) -> None:
        tenant = TenantFactory()
        imposto = _imposto(tenant)
        fim = _INICIO + timedelta(days=150)
        with run_in_tenant_context(tenant.id):
            assert Imposto.objects.filter(id=imposto.id).update(vigencia_fim=fim) == 1
            with pytest.raises(DatabaseError):
                Imposto.objects.filter(id=imposto.id).update(
                    vigencia_fim=fim + timedelta(days=1)
                )

    @pytest.mark.django_db(transaction=True)
    def test_revogacao_one_shot(self) -> None:
        tenant = TenantFactory()
        imposto = _imposto(tenant)
        with run_in_tenant_context(tenant.id):
            assert (
                Imposto.objects.filter(id=imposto.id).update(
                    revogado_em=timezone.now(),
                    motivo_revogacao="linha cadastrada com aliquota errada",
                )
                == 1
            )
            with pytest.raises(DatabaseError):
                Imposto.objects.filter(id=imposto.id).update(
                    motivo_revogacao="tentativa de reescrever o motivo"
                )


class TestINV_CFG_IMPOSTO_SEM_SOBREPOSICAO:
    """Exclusion btree_gist: vigente-em-D determinístico."""

    @pytest.mark.django_db(transaction=True)
    def test_sobreposicao_mesmo_tipo_filial_null_rejeitada(self) -> None:
        tenant = TenantFactory()
        _imposto(tenant, inicio=_INICIO, fim=None)
        with pytest.raises(IntegrityError):
            _imposto(tenant, inicio=_INICIO + timedelta(days=30), fim=None)

    @pytest.mark.django_db(transaction=True)
    def test_encadeamento_half_open_aceito(self) -> None:
        tenant = TenantFactory()
        meio = _INICIO + timedelta(days=120)
        _imposto(tenant, inicio=_INICIO, fim=meio)
        assert _imposto(tenant, inicio=meio, fim=None).id is not None

    @pytest.mark.django_db(transaction=True)
    def test_linha_revogada_sai_da_constraint(self) -> None:
        tenant = TenantFactory()
        errada = _imposto(tenant, inicio=_INICIO, fim=None)
        with run_in_tenant_context(tenant.id):
            Imposto.objects.filter(id=errada.id).update(
                revogado_em=timezone.now(),
                motivo_revogacao="aliquota digitada errada no cadastro",
            )
        assert _imposto(tenant, inicio=_INICIO, fim=None).id != errada.id


class TestINV_028:
    """proximo_numero nunca diminui (exceção única: reset anual TL-07)."""

    @pytest.mark.django_db(transaction=True)
    def test_decremento_rejeitado(self) -> None:
        tenant = TenantFactory()
        serie = _serie(tenant, tipo="os", prefixo="OS", regime="buracos_aceitos")
        with run_in_tenant_context(tenant.id):
            SerieDocumento.objects.filter(id=serie.id).update(proximo_numero=50)
            with pytest.raises(DatabaseError):
                SerieDocumento.objects.filter(id=serie.id).update(proximo_numero=10)

    @pytest.mark.django_db(transaction=True)
    def test_reset_anual_legitimo_permitido(self) -> None:
        tenant = TenantFactory()
        with run_in_tenant_context(tenant.id):
            serie = SerieDocumento.objects.create(
                tenant=tenant,
                tipo="orcamento",
                prefixo="ORC",
                regime_numeracao="buracos_aceitos",
                reset_anual=True,
                proximo_numero=99,
                ano_corrente=2026,
            )
            n = SerieDocumento.objects.filter(id=serie.id).update(
                proximo_numero=2, ano_corrente=2027
            )
            assert n == 1

    @pytest.mark.django_db(transaction=True)
    def test_tipo_prefixo_regime_imutaveis(self) -> None:
        tenant = TenantFactory()
        serie = _serie(tenant, tipo="os", prefixo="OS", regime="buracos_aceitos")
        with run_in_tenant_context(tenant.id), pytest.raises(DatabaseError):
            SerieDocumento.objects.filter(id=serie.id).update(
                tipo="fatura", regime_numeracao="gap_less"
            )


class TestINV_036:
    """CNPJ único por tenant (empresa)."""

    @pytest.mark.django_db(transaction=True)
    def test_cnpj_duplicado_no_tenant_rejeitado(self) -> None:
        tenant = TenantFactory()
        _empresa(tenant, cnpj=CNPJ_A)
        with pytest.raises(IntegrityError):
            _empresa(tenant, cnpj=CNPJ_A)


class TestINV_037:
    """Exatamente 1 matriz por empresa (≤1 no banco; ≥1 no domínio)."""

    @pytest.mark.django_db(transaction=True)
    def test_segunda_matriz_rejeitada_unique_parcial(self) -> None:
        tenant = TenantFactory()
        empresa = _empresa(tenant)
        with run_in_tenant_context(tenant.id):
            Filial.objects.create(
                tenant=tenant,
                empresa=empresa,
                cnpj=CNPJ_A,
                nome="Matriz",
                eh_matriz=True,
            )
            with pytest.raises(IntegrityError):
                Filial.objects.create(
                    tenant=tenant,
                    empresa=empresa,
                    cnpj=CNPJ_B,
                    nome="Outra",
                    eh_matriz=True,
                )
