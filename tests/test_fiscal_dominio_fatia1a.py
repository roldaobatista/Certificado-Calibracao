"""Frente fiscal/NFS-e — Fatia 1a (T-FIS-010..015): domínio puro.

Sem Django, sem PG: VOs agnósticos, porta `FiscalProvider` (mock determinístico,
4 modos), entidade `NotaFiscalServico`, máquina de estados (D-FIS-3/4), trava de
perfil pura (D-FIS-5/6/7), hash probatório determinístico, Protocols.
"""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

import pytest
from src.domain.fiscal.entities import NotaFiscalServico
from src.domain.fiscal.enums import (
    InvoiceStatus,
    PerfilRegulatorio,
    TipoAcreditacaoVinculo,
    TipoServico,
)
from src.domain.fiscal.erros import (
    DocIncompativelComPerfilError,
    DocMetrologicoObrigatorioError,
    MotivoCancelamentoInvalidoError,
    ProviderTimeoutError,
    TransicaoInvalidaError,
)
from src.domain.fiscal.mock_provider import MockFiscalProvider, ModoMock
from src.domain.fiscal.perfil_documento import (
    documento_metrologico_obrigatorio_por_perfil,
)
from src.domain.fiscal.portas import FiscalProvider
from src.domain.fiscal.repository import NotaFiscalServicoRepository
from src.domain.fiscal.transicoes import (
    snapshot_hash_nfse,
    validar_motivo_cancelamento,
    validar_transicao,
)
from src.domain.fiscal.value_objects import InvoicePayload, InvoiceResult


def _payload(**over: object) -> InvoicePayload:
    base: dict[str, object] = {
        "tenant_id": uuid4(),
        "issuer_taxid": "11222333000181",
        "customer_taxid": "98765432000110",
        "customer_name": "Cliente Exemplo Ltda",
        "service_description": "Calibração de balança",
        "service_code": "14.01",
        "amount": Decimal("250.00"),
        "issue_date": datetime(2026, 6, 8, 12, 0, tzinfo=UTC),
    }
    base.update(over)
    return InvoicePayload(**base)


# --- T-FIS-010 VOs ---


def test_invoice_payload_frozen_e_metadata_default() -> None:
    p = _payload()
    assert p.metadata == {}
    with pytest.raises(FrozenInstanceError):  # frozen: atribuição proibida em runtime
        p.amount = Decimal("1")


def test_invoice_result_campos_br_so_em_metadata() -> None:
    # D-FIS-1: VO agnóstico não tem atributo nomeado BR.
    r = InvoiceResult(invoice_id="X", status=InvoiceStatus.AUTHORIZED)
    assert not hasattr(r, "chave_acesso_44")
    assert not hasattr(r, "numero")
    assert r.metadata == {}


# --- T-FIS-011/012 porta + mock (4 modos determinísticos) ---


def test_mock_satisfaz_protocolo() -> None:
    assert isinstance(MockFiscalProvider(), FiscalProvider)


def test_mock_always_authorize() -> None:
    r = MockFiscalProvider(ModoMock.ALWAYS_AUTHORIZE).emit_invoice(_payload())
    assert r.status is InvoiceStatus.AUTHORIZED
    assert r.authorization_code
    assert r.metadata.get("chave_acesso_44")  # campo BR só em metadata


def test_mock_always_reject() -> None:
    r = MockFiscalProvider(ModoMock.ALWAYS_REJECT).emit_invoice(_payload())
    assert r.status is InvoiceStatus.REJECTED
    assert r.rejection_reason


def test_mock_pending_then_authorize() -> None:
    prov = MockFiscalProvider(ModoMock.PENDING_THEN_AUTHORIZE)
    r = prov.emit_invoice(_payload())
    assert r.status is InvoiceStatus.PENDING
    assert prov.query_status(r.invoice_id) is InvoiceStatus.AUTHORIZED


def test_mock_network_timeout_levanta() -> None:
    with pytest.raises(ProviderTimeoutError):
        MockFiscalProvider(ModoMock.NETWORK_TIMEOUT).emit_invoice(_payload())


def test_mock_id_deterministico_por_payload() -> None:
    p = _payload()
    a = MockFiscalProvider().emit_invoice(p)
    b = MockFiscalProvider().emit_invoice(p)
    assert a.invoice_id == b.invoice_id


def test_mock_id_nao_depende_do_tomador() -> None:
    # id derivado só de campos não-PII: mesmo tenant/service/amount/data →
    # mesmo id, mesmo trocando o tomador.
    p1 = _payload(customer_taxid="11111111111", customer_name="A")
    p2 = _payload(
        tenant_id=p1.tenant_id,
        customer_taxid="22222222222",
        customer_name="B",
    )
    id1 = MockFiscalProvider().emit_invoice(p1).invoice_id
    id2 = MockFiscalProvider().emit_invoice(p2).invoice_id
    assert id1 == id2


# --- T-FIS-013 máquina de estados ---


@pytest.mark.parametrize(
    ("atual", "novo"),
    [
        (InvoiceStatus.PENDING, InvoiceStatus.AUTHORIZED),
        (InvoiceStatus.PENDING, InvoiceStatus.REJECTED),
        (InvoiceStatus.AUTHORIZED, InvoiceStatus.CANCELED),
    ],
)
def test_transicoes_validas(atual: InvoiceStatus, novo: InvoiceStatus) -> None:
    validar_transicao(atual, novo)  # não levanta


@pytest.mark.parametrize(
    ("atual", "novo"),
    [
        (InvoiceStatus.REJECTED, InvoiceStatus.AUTHORIZED),
        (InvoiceStatus.CANCELED, InvoiceStatus.AUTHORIZED),
        (InvoiceStatus.AUTHORIZED, InvoiceStatus.REJECTED),
        (InvoiceStatus.PENDING, InvoiceStatus.CANCELED),
    ],
)
def test_transicoes_invalidas(atual: InvoiceStatus, novo: InvoiceStatus) -> None:
    with pytest.raises(TransicaoInvalidaError):
        validar_transicao(atual, novo)


def test_motivo_cancelamento_curto_falha() -> None:
    with pytest.raises(MotivoCancelamentoInvalidoError):
        validar_motivo_cancelamento("muito curto")


def test_motivo_cancelamento_ok() -> None:
    validar_motivo_cancelamento("erro de digitação no valor do serviço prestado X")


# --- T-FIS-013 hash probatório determinístico ---


def test_snapshot_hash_deterministico_e_versionado() -> None:
    kw: dict[str, object] = {
        "tenant_id": str(uuid4()),
        "origem_id": str(uuid4()),
        "versao": 1,
        "tipo_servico": "calibracao",
        "perfil_no_evento": "A",
        "valor_centavos": 25000,
        "cliente_referencia_hash": "abc",
        "provider_invoice_id": "PROV-1",
        "certificado_id": str(uuid4()),
        "declaracao_id": None,
        "tipo_acreditacao_vinculo": "RBC",
        "status": "AUTHORIZED",
    }
    h1 = snapshot_hash_nfse(**kw)
    h2 = snapshot_hash_nfse(**kw)
    assert h1 == h2
    assert h1.startswith("v01$")  # hash versionado v<NN>$ (ADR-0064)


# --- T-FIS-014 trava de perfil (D-FIS-5/6/7) ---


def test_perfil_a_aceita_rbc() -> None:
    documento_metrologico_obrigatorio_por_perfil(
        perfil=PerfilRegulatorio.A,
        tipo_servico=TipoServico.CALIBRACAO,
        tipo_acreditacao_certificado=TipoAcreditacaoVinculo.RBC,
        tem_declaracao=False,
    )


def test_perfil_a_aceita_nao_rbc_d_fis_6() -> None:
    # D-FIS-6: lab acreditado pode faturar calibração não-RBC.
    documento_metrologico_obrigatorio_por_perfil(
        perfil=PerfilRegulatorio.A,
        tipo_servico=TipoServico.CALIBRACAO,
        tipo_acreditacao_certificado=TipoAcreditacaoVinculo.NAO_RBC,
        tem_declaracao=False,
    )


def test_perfil_a_sem_certificado_falha() -> None:
    with pytest.raises(DocMetrologicoObrigatorioError):
        documento_metrologico_obrigatorio_por_perfil(
            perfil=PerfilRegulatorio.A,
            tipo_servico=TipoServico.CALIBRACAO,
            tipo_acreditacao_certificado=None,
            tem_declaracao=False,
        )


@pytest.mark.parametrize("perfil", [PerfilRegulatorio.B, PerfilRegulatorio.C])
def test_perfil_bc_rejeita_rbc(perfil: PerfilRegulatorio) -> None:
    # AC-FIS-001-8: perfil B/C não pode referenciar certificado RBC.
    with pytest.raises(DocIncompativelComPerfilError):
        documento_metrologico_obrigatorio_por_perfil(
            perfil=perfil,
            tipo_servico=TipoServico.CALIBRACAO,
            tipo_acreditacao_certificado=TipoAcreditacaoVinculo.RBC,
            tem_declaracao=False,
        )


@pytest.mark.parametrize("perfil", [PerfilRegulatorio.B, PerfilRegulatorio.C])
def test_perfil_bc_aceita_simples(perfil: PerfilRegulatorio) -> None:
    documento_metrologico_obrigatorio_por_perfil(
        perfil=perfil,
        tipo_servico=TipoServico.CALIBRACAO,
        tipo_acreditacao_certificado=TipoAcreditacaoVinculo.NAO_RBC,
        tem_declaracao=False,
    )


def test_perfil_d_aceita_declaracao() -> None:
    documento_metrologico_obrigatorio_por_perfil(
        perfil=PerfilRegulatorio.D,
        tipo_servico=TipoServico.CALIBRACAO,
        tipo_acreditacao_certificado=None,
        tem_declaracao=True,
    )


def test_perfil_d_rejeita_rbc() -> None:
    with pytest.raises(DocIncompativelComPerfilError):
        documento_metrologico_obrigatorio_por_perfil(
            perfil=PerfilRegulatorio.D,
            tipo_servico=TipoServico.CALIBRACAO,
            tipo_acreditacao_certificado=TipoAcreditacaoVinculo.RBC,
            tem_declaracao=False,
        )


def test_perfil_d_sem_documento_falha() -> None:
    with pytest.raises(DocMetrologicoObrigatorioError):
        documento_metrologico_obrigatorio_por_perfil(
            perfil=PerfilRegulatorio.D,
            tipo_servico=TipoServico.CALIBRACAO,
            tipo_acreditacao_certificado=None,
            tem_declaracao=False,
        )


def test_servico_nao_calibracao_dispensa_vinculo() -> None:
    # Manutenção: vínculo metrológico opcional — não levanta mesmo sem documento.
    documento_metrologico_obrigatorio_por_perfil(
        perfil=PerfilRegulatorio.A,
        tipo_servico=TipoServico.MANUTENCAO,
        tipo_acreditacao_certificado=None,
        tem_declaracao=False,
    )


# --- T-FIS-013 entidade ---


def test_nota_valor_decimal_e_terminal() -> None:
    nota = NotaFiscalServico(
        nfse_id=uuid4(),
        tenant_id=uuid4(),
        origem_id=uuid4(),
        versao=1,
        status=InvoiceStatus.REJECTED,
        tipo_servico=TipoServico.CALIBRACAO,
        perfil_no_evento=PerfilRegulatorio.A,
        valor_centavos=25000,
        cliente_referencia_hash="abc",
        provider_invoice_id=None,
        certificado_id=uuid4(),
        declaracao_id=None,
        tipo_acreditacao_vinculo=TipoAcreditacaoVinculo.RBC,
        snapshot_hash="v1$deadbeef",
        emitido_em=None,
        cancelado_em=None,
        motivo_cancelamento=None,
    )
    assert nota.valor_decimal == Decimal("250.00")
    assert nota.e_terminal is True


# --- T-FIS-015 Protocols ---


def test_repository_protocol_runtime_checkable() -> None:
    class _Fake:
        def obter_por_id(self, *, tenant_id, nfse_id):
            return None

        def existe_chave(self, *, tenant_id, origem_id, versao):
            return False

        def obter_por_origem(self, *, tenant_id, origem_id, versao):
            return None

        def salvar_nova(self, nota):
            return None

        def atualizar_status(self, *, tenant_id, nfse_id, nota):
            return None

    assert isinstance(_Fake(), NotaFiscalServicoRepository)
