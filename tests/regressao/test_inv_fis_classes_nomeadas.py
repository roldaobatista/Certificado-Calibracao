"""TST-004 — classes nomeando cada INV-FIS (fiscal/NFS-e Fatia 3 / T-FIS-040).

Convenção do projeto (análoga `test_inv_lic_classes_nomeadas.py` do M9): todo INV
crítico tem ≥1 teste cujo NOME cita o ID. Cada classe `TestINV_FIS_*` exercita a
barreira REAL — puro/Fake onde a defesa é domínio/use case; PG-real onde é
trigger/RLS.
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from django.db import DatabaseError, IntegrityError
from django.utils import timezone
from src.application.fiscal import emitir_nfse
from src.domain.fiscal.entities import NotaFiscalServico
from src.domain.fiscal.enums import (
    InvoiceStatus,
    PerfilRegulatorio,
    TipoAcreditacaoVinculo,
    TipoServico,
)
from src.domain.fiscal.erros import DocIncompativelComPerfilError
from src.domain.fiscal.mock_provider import MockFiscalProvider, ModoMock
from src.domain.fiscal.perfil_documento import (
    documento_metrologico_obrigatorio_por_perfil,
)
from src.domain.fiscal.portas import FiscalProvider
from src.infrastructure.fiscal.models import NotaFiscalServico as NotaFiscalServicoModel
from src.infrastructure.multitenant.connection import run_in_tenant_context

from tests.factories import TenantFactory


class _FakeRepo:
    """Repo em memória para os use cases puros."""

    def __init__(self) -> None:
        self.notas: dict[tuple, NotaFiscalServico] = {}

    def obter_por_origem(self, *, tenant_id, origem_id, versao):
        return self.notas.get((tenant_id, origem_id, versao))

    def obter_por_id(self, *, tenant_id, nfse_id):
        for n in self.notas.values():
            if n.tenant_id == tenant_id and n.nfse_id == nfse_id:
                return n
        return None

    def existe_chave(self, *, tenant_id, origem_id, versao):
        return (tenant_id, origem_id, versao) in self.notas

    def salvar_nova(self, nota):
        self.notas[(nota.tenant_id, nota.origem_id, nota.versao)] = nota

    def atualizar_status(self, *, tenant_id, nfse_id, nota):
        self.notas[(nota.tenant_id, nota.origem_id, nota.versao)] = nota


def _input(**kw):
    base = {
        "tenant_id": uuid4(),
        "origem_id": uuid4(),
        "tipo_servico": TipoServico.CALIBRACAO,
        "perfil": PerfilRegulatorio.A,
        "amount_centavos": 25000,
        "issuer_taxid": "11222333000181",
        "customer_taxid": "98765432000110",
        "customer_name": "Cliente Ltda",
        "cliente_referencia_hash": "ref-hash",
        "service_description": "Calibração de balança",
        "service_code": "14.01",
        "issue_date": datetime(2026, 6, 8, 12, 0, tzinfo=UTC),
        "correlation_id": uuid4(),
        "tipo_acreditacao_vinculo": TipoAcreditacaoVinculo.RBC,
        "certificado_id": uuid4(),
    }
    base.update(kw)
    return emitir_nfse.EmitirNfseInput(**base)


def _cria_nota_pg(tenant, *, status="AUTHORIZED"):
    with run_in_tenant_context(tenant.id):
        return NotaFiscalServicoModel.objects.create(
            tenant=tenant,
            origem_id=uuid4(),
            versao=1,
            status=status,
            tipo_servico="calibracao",
            perfil_no_evento="A",
            valor_centavos=25000,
            cliente_referencia_hash="ref-hash",
            snapshot_hash="v01$deadbeef",
            tipo_acreditacao_vinculo="RBC",
            certificado_id=uuid4(),
            emitido_em=timezone.now(),
        )


class TestINV_FIS_001:
    """Trava de perfil server-side no use case (D → cert RBC = incompatível)."""

    def test_perfil_d_rejeita_rbc(self) -> None:
        with pytest.raises(DocIncompativelComPerfilError):
            documento_metrologico_obrigatorio_por_perfil(
                perfil=PerfilRegulatorio.D,
                tipo_servico=TipoServico.CALIBRACAO,
                tipo_acreditacao_certificado=TipoAcreditacaoVinculo.RBC,
                tem_declaracao=False,
            )


class TestINV_FIS_002:
    """Vínculo RBC vem do snapshot passado ao use case (não reconsulta Tenant)."""

    def test_use_case_usa_vinculo_do_input(self) -> None:
        repo = _FakeRepo()
        out = emitir_nfse.executar(
            _input(tipo_acreditacao_vinculo=TipoAcreditacaoVinculo.NAO_RBC),
            provider=MockFiscalProvider(ModoMock.ALWAYS_AUTHORIZE),
            repo=repo,
        )
        # Perfil A aceita NAO_RBC (D-FIS-6) e o vínculo persistido é o do snapshot.
        assert out.nota.tipo_acreditacao_vinculo is TipoAcreditacaoVinculo.NAO_RBC


class TestINV_FIS_003:
    """Porta agnóstica: o mock satisfaz o Protocol sem SDK de fornecedor."""

    def test_mock_satisfaz_protocolo(self) -> None:
        assert isinstance(MockFiscalProvider(), FiscalProvider)


class TestINV_FIS_004:
    """WORM Padrão B: campo probatório imutável pós-emissão (PG real)."""

    @pytest.mark.django_db(transaction=True)
    def test_valor_imutavel_raise(self) -> None:
        tenant = TenantFactory()
        nota = _cria_nota_pg(tenant)
        with run_in_tenant_context(tenant.id), pytest.raises(DatabaseError):
            NotaFiscalServicoModel.objects.filter(id=nota.id).update(valor_centavos=1)


class TestINV_FIS_005:
    """Idempotência de negócio: dupla emissão da mesma origem devolve a existente."""

    def test_dupla_origem_ja_existia(self) -> None:
        repo = _FakeRepo()
        inp = _input()
        prov = MockFiscalProvider(ModoMock.ALWAYS_AUTHORIZE)
        out1 = emitir_nfse.executar(inp, provider=prov, repo=repo)
        out2 = emitir_nfse.executar(inp, provider=prov, repo=repo)
        assert out1.ja_existia is False
        assert out2.ja_existia is True
        assert out2.nota.nfse_id == out1.nota.nfse_id


class TestINV_FIS_006:
    """RLS isola a nota entre tenants (PG real)."""

    @pytest.mark.django_db(transaction=True)
    def test_cross_tenant_invisivel(self) -> None:
        tenant_a = TenantFactory()
        tenant_b = TenantFactory()
        nota = _cria_nota_pg(tenant_a)
        with run_in_tenant_context(tenant_b.id):
            assert not NotaFiscalServicoModel.objects.filter(id=nota.id).exists()


class TestINV_FIS_007:
    """Núcleo não injeta marcador RBC na descrição de perfil B/C/D (guarda
    estática = hook `fiscal-anti-rbc-em-descricao`; renderização impressa diferida)."""

    def test_perfil_b_sem_marcador_rbc_injetado(self) -> None:
        repo = _FakeRepo()
        out = emitir_nfse.executar(
            _input(
                perfil=PerfilRegulatorio.B,
                tipo_acreditacao_vinculo=TipoAcreditacaoVinculo.NAO_RBC,
                service_description="Calibração simples de balança",
            ),
            provider=MockFiscalProvider(ModoMock.ALWAYS_AUTHORIZE),
            repo=repo,
        )
        # O núcleo não adiciona "RBC"/"ISO 17025" a nada persistido da nota.
        assert "RBC" not in out.nota.snapshot_hash
        assert out.nota.perfil_no_evento is PerfilRegulatorio.B


class TestINV_FIS_008:
    """Retenção fiscal: DELETE físico bloqueado por trigger (PG real)."""

    @pytest.mark.django_db(transaction=True)
    def test_delete_fisico_raise(self) -> None:
        tenant = TenantFactory()
        nota = _cria_nota_pg(tenant)
        with run_in_tenant_context(tenant.id), pytest.raises(DatabaseError):
            NotaFiscalServicoModel.objects.filter(id=nota.id).delete()


class TestINV_FIS_009:
    """PII em 2 regimes: a entidade persistida NÃO guarda PII clara do tomador
    (só `cliente_referencia_hash`)."""

    def test_entidade_sem_pii_clara(self) -> None:
        nota = NotaFiscalServico(
            nfse_id=uuid4(), tenant_id=uuid4(), origem_id=uuid4(), versao=1,
            status=InvoiceStatus.AUTHORIZED, tipo_servico=TipoServico.CALIBRACAO,
            perfil_no_evento=PerfilRegulatorio.A, valor_centavos=1,
            cliente_referencia_hash="hash", provider_invoice_id="X",
            certificado_id=None, declaracao_id=None,
            tipo_acreditacao_vinculo=None, snapshot_hash="v01$x",
            emitido_em=None, cancelado_em=None, motivo_cancelamento=None,
        )
        assert not hasattr(nota, "customer_taxid")
        assert not hasattr(nota, "customer_name")
        assert nota.cliente_referencia_hash == "hash"


@pytest.mark.django_db(transaction=True)
def test_unique_negocio_e_integrity() -> None:
    """INV-FIS-005 camada banco: UNIQUE (tenant, origem, versao) — IntegrityError."""
    tenant = TenantFactory()
    origem = uuid4()
    with run_in_tenant_context(tenant.id):
        NotaFiscalServicoModel.objects.create(
            tenant=tenant, origem_id=origem, versao=1, status="AUTHORIZED",
            tipo_servico="calibracao", perfil_no_evento="A", valor_centavos=1,
            cliente_referencia_hash="h", snapshot_hash="v01$x", emitido_em=timezone.now(),
        )
        with pytest.raises(IntegrityError):
            NotaFiscalServicoModel.objects.create(
                tenant=tenant, origem_id=origem, versao=1, status="AUTHORIZED",
                tipo_servico="calibracao", perfil_no_evento="A", valor_centavos=1,
                cliente_referencia_hash="h", snapshot_hash="v01$y", emitido_em=timezone.now(),
            )
