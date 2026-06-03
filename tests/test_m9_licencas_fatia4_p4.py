"""M9 Fatia 4 — US-LIC-004 histórico + US-LIC-005 ART/RRT (T-LIC-060). TST-004/005.

Puros: `signatario_apto`/`documentos_signatario_vencidos` (fronteira HARD-409 só
ART/RRT/cert digital; revogado ignorado; vencimento na `data`). PG-real (API):
endpoint `historico` (revisões append-only listadas) + `signatario-apto`
(ART vencida → inapto; vigente/ausente → apto).
"""

from __future__ import annotations

from datetime import date
from uuid import uuid4

import pytest
from rest_framework.test import APIClient
from src.application.metrologia.licencas_acreditacoes.verificar_signatario import (
    DocumentoSignatarioSnapshot,
    documentos_signatario_vencidos,
    signatario_apto,
)
from src.domain.metrologia.licencas_acreditacoes.enums import TipoDocumentoRegulatorio

from tests.test_m9_licencas_api_p2 import _autenticar, _cad_payload, _cenario, _post

_DBS = ["default", "breaker_writer"]


def _sig(tipo: TipoDocumentoRegulatorio, vig_fim: date, **kw):
    base = {
        "documento_id": uuid4(),
        "tipo": tipo,
        "numero": "DOC-1",
        "vigencia_fim": vig_fim,
    }
    base.update(kw)
    return DocumentoSignatarioSnapshot(**base)


class TestSignatarioPuro:
    def test_art_vencida_inapto(self) -> None:
        hoje = date(2026, 6, 1)
        snaps = [_sig(TipoDocumentoRegulatorio.ART, date(2026, 5, 1))]
        assert signatario_apto(snaps, data=hoje) is False
        assert len(documentos_signatario_vencidos(snaps, data=hoje)) == 1

    def test_art_vigente_apto(self) -> None:
        hoje = date(2026, 6, 1)
        snaps = [_sig(TipoDocumentoRegulatorio.ART, date(2027, 1, 1))]
        assert signatario_apto(snaps, data=hoje) is True

    def test_sem_documentos_apto(self) -> None:
        assert signatario_apto([], data=date(2026, 6, 1)) is True

    def test_revogada_ignorada(self) -> None:
        hoje = date(2026, 6, 1)
        snaps = [_sig(TipoDocumentoRegulatorio.RRT, date(2026, 5, 1), revogado=True)]
        assert signatario_apto(snaps, data=hoje) is True

    def test_acreditacao_cgcre_nao_e_hard(self) -> None:
        # Acreditação CGCRE vencida REBAIXA (não HARD-409) — não entra no veredito.
        hoje = date(2026, 6, 1)
        snaps = [
            _sig(TipoDocumentoRegulatorio.ACREDITACAO_CGCRE, date(2026, 5, 1)),
            _sig(TipoDocumentoRegulatorio.ALVARA, date(2026, 5, 1)),
        ]
        assert signatario_apto(snaps, data=hoje) is True

    def test_cert_digital_a3_vencido_inapto(self) -> None:
        hoje = date(2026, 6, 1)
        snaps = [_sig(TipoDocumentoRegulatorio.CERT_DIGITAL_A3, date(2026, 1, 1))]
        assert signatario_apto(snaps, data=hoje) is False


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_historico_lista_revisoes_append_only():
    c = _cenario("d")
    client = APIClient()
    _autenticar(client, c["admin"], c["tenant"])
    r = _post(client, "/api/v1/licencas/cadastrar/", _cad_payload(numero="ALV-HIST"))
    doc_id = r.json()["id"]
    _post(
        client, f"/api/v1/licencas/{doc_id}/renovar/",
        {
            "nova_vigencia_inicio": "2027-01-01", "nova_vigencia_fim": "2028-01-01",
            "anexo_id": str(uuid4()), "anexo_sha256": "d" * 64,
            "motivo": "RENOVACAO", "correlation_id": str(uuid4()),
        },
    )
    h = client.get(f"/api/v1/licencas/{doc_id}/historico/")
    assert h.status_code == 200, h.content
    body = h.json()
    assert body["total_revisoes"] == 2
    assert [rv["numero_revisao"] for rv in body["revisoes"]] == [1, 2]
    assert all("criado_em" in rv and "anexo_sha256" in rv for rv in body["revisoes"])


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_signatario_apto_art_vencida_inapto():
    c = _cenario("a")
    client = APIClient()
    _autenticar(client, c["admin"], c["tenant"])
    # ART já vencida (vigência no passado — cadastro permite; status = VENCIDO).
    r = _post(
        client, "/api/v1/licencas/cadastrar/",
        _cad_payload(
            tipo="ART", numero="ART-VENC", orgao_emissor="CREA",
            vigencia_inicio="2020-01-01", vigencia_fim="2021-01-01",
        ),
    )
    assert r.status_code == 201, r.content
    g = client.get("/api/v1/licencas/signatario-apto/")
    assert g.status_code == 200, g.content
    body = g.json()
    assert body["apto"] is False
    assert len(body["documentos_vencidos"]) == 1
    assert body["documentos_vencidos"][0]["tipo"] == "ART"


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_signatario_apto_sem_docs_apto():
    c = _cenario("a")
    client = APIClient()
    _autenticar(client, c["admin"], c["tenant"])
    g = client.get("/api/v1/licencas/signatario-apto/")
    assert g.status_code == 200, g.content
    assert g.json()["apto"] is True


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_signatario_apto_data_passada_ainda_vigente():
    c = _cenario("a")
    client = APIClient()
    _autenticar(client, c["admin"], c["tenant"])
    _post(
        client, "/api/v1/licencas/cadastrar/",
        _cad_payload(
            tipo="ART", numero="ART-FUT", orgao_emissor="CREA",
            vigencia_inicio="2026-01-01", vigencia_fim="2027-01-01",
        ),
    )
    # Numa data dentro da vigência → apto.
    g = client.get("/api/v1/licencas/signatario-apto/?data=2026-06-01")
    assert g.status_code == 200, g.content
    assert g.json()["apto"] is True
