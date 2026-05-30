"""API /api/v1/escopos-cmc/ extração PDF — E2E M6 Fatia 4 (T-ECMC-053).

Cobre: importar-extracao (staging RASCUNHO, INV-ECMC-007) + confirmar-extraido
(promove a escopos CONFIRMADO, perfil A RBC) + one-shot (re-confirmar 409) +
Idempotency-Key obrigatória + authz (atendente não importa).
"""

from __future__ import annotations

from uuid import uuid4

import pytest
from rest_framework.test import APIClient

from tests.test_m6_escopos_cmc_api_p2 import (
    _DBS,
    _autenticar,
    _cenario,
    _payload,
    _post,
)


def _payload_importar(**kw):
    base = {
        "origem_pdf_storage_key": "cgcre/escopo-1.pdf",
        "numero_escopo_cgcre": "CRL-0001",
        "linhas_cruas": [
            ["Massa", "0,5 a 200", "kg", "0,1", "PRO-CAL-MASSA-01"],
            ["Temperatura", "(-30 a 660)", "C", "0,05", ""],
        ],
        "mapa_colunas": {"grandeza": 0, "faixa": 1, "unidade": 2, "cmc": 3, "metodo": 4},
        "correlation_id": str(uuid4()),
    }
    base.update(kw)
    return base


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_importar_extracao_cria_staging():
    c = _cenario(slug_perfil_a=True)
    client = APIClient()
    _autenticar(client, c["admin"], c["tenant"])
    r = _post(client, "/api/v1/escopos-cmc/importar-extracao/", _payload_importar())
    assert r.status_code == 201, r.content
    body = r.json()
    assert body["confirmado_em"] is None  # INV-ECMC-007 — staging, não vigente
    assert len(body["linhas"]) == 2
    assert body["linhas"][0]["grandeza_texto"] == "Massa"
    assert body["linhas"][0]["faixa_min"] == "0.5"
    assert body["linhas"][0]["confianca"] == "1"


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_importar_sem_idempotency_falha():
    c = _cenario(slug_perfil_a=True)
    client = APIClient()
    _autenticar(client, c["admin"], c["tenant"])
    r = client.post(
        "/api/v1/escopos-cmc/importar-extracao/",
        _payload_importar(),
        format="json",
    )
    assert r.status_code in (400, 428), r.content


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_atendente_nao_importa_403():
    c = _cenario(slug_perfil_a=True)
    client = APIClient()
    _autenticar(client, c["atendente"], c["tenant"])
    r = _post(client, "/api/v1/escopos-cmc/importar-extracao/", _payload_importar())
    assert r.status_code == 403, r.content


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_confirmar_extraido_promove_e_one_shot():
    c = _cenario(slug_perfil_a=True)
    client = APIClient()
    _autenticar(client, c["admin"], c["tenant"])
    imp = _post(
        client, "/api/v1/escopos-cmc/importar-extracao/", _payload_importar()
    )
    assert imp.status_code == 201, imp.content
    extraido_id = imp.json()["id"]

    url = f"/api/v1/escopos-cmc/{extraido_id}/confirmar-extraido/"
    # Conferência humana normalizou 1 linha (perfil A RBC, com procedimento).
    r = _post(client, url, {"escopos": [_payload()]})
    assert r.status_code == 201, r.content
    body = r.json()
    assert body["extraido_id"] == extraido_id
    assert len(body["confirmados"]) == 1
    assert body["confirmados"][0]["rbc_acreditado"] is True
    assert body["confirmados"][0]["versao"] == 1

    # one-shot: re-confirmar o mesmo staging -> 409.
    r2 = _post(client, url, {"escopos": [_payload()]})
    assert r2.status_code == 409, r2.content


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_confirmar_extraido_inexistente_404():
    c = _cenario(slug_perfil_a=True)
    client = APIClient()
    _autenticar(client, c["admin"], c["tenant"])
    url = f"/api/v1/escopos-cmc/{uuid4()}/confirmar-extraido/"
    r = _post(client, url, {"escopos": [_payload()]})
    assert r.status_code == 404, r.content
