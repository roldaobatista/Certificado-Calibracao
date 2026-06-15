"""Templates de orçamento — CRUD + gate selo RBC (T-ORC-039 / US-ORC-005 / D-ORC-13).

Cobre o gate INV-ORC-SELO-RBC (selo só em perfil A) nas duas pontas — função pura de
gate + endpoint REST — além do CRUD completo (criar/listar/retrieve/editar/soft-delete),
idempotência e isolamento cross-tenant (RLS).

Reusa os helpers de `tests/test_orcamentos_fatia2.py`. PG-real (--reuse-db).
"""

from __future__ import annotations

from uuid import uuid4

import pytest
from src.infrastructure.multitenant.connection import run_in_tenant_context

from tests.test_orcamentos_fatia2 import _DBS, _cenario_perfil, _client, _post

_URL = "/api/v1/orcamento-templates/"


# ---------------------------------------------------------------------------
# Gate puro (INV-ORC-SELO-RBC) — sem banco
# ---------------------------------------------------------------------------


def test_inv_orc_selo_rbc_gate_puro_perfil_a_permite() -> None:
    """validar_selo_rbc_permitido: perfil A + selo → não levanta."""
    from src.application.comercial.orcamentos.templates import validar_selo_rbc_permitido

    validar_selo_rbc_permitido(perfil="A", selo_rbc=True)  # não levanta
    validar_selo_rbc_permitido(perfil="B", selo_rbc=False)  # selo off: qualquer perfil


@pytest.mark.parametrize("perfil", ["B", "C", "D"])
def test_inv_orc_selo_rbc_gate_puro_perfil_nao_a_bloqueia(perfil: str) -> None:
    """INV-ORC-SELO-RBC: perfil ≠ A + selo → SeloRbcNaoPermitido."""
    from src.application.comercial.orcamentos.templates import validar_selo_rbc_permitido
    from src.domain.comercial.orcamentos.erros import SeloRbcNaoPermitido

    with pytest.raises(SeloRbcNaoPermitido):
        validar_selo_rbc_permitido(perfil=perfil, selo_rbc=True)


def test_inv_orc_selo_rbc_gate_puro_indeterminado_fail_closed() -> None:
    """INV-ORC-SELO-RBC: perfil vazio + selo → fail-closed (PerfilIndeterminado)."""
    from src.application.comercial.orcamentos.templates import validar_selo_rbc_permitido
    from src.domain.comercial.orcamentos.erros import PerfilIndeterminado

    with pytest.raises(PerfilIndeterminado):
        validar_selo_rbc_permitido(perfil="", selo_rbc=True)


# ---------------------------------------------------------------------------
# CRUD + gate via REST (E2E)
# ---------------------------------------------------------------------------


def _payload(*, nome: str = "Calibracao balanca padrao", selo: bool = False) -> dict:
    return {
        "nome": nome,
        "tipo": "calibracao_balanca",
        "selo_rbc": selo,
        "itens_default": [{"catalogo_item_id": str(uuid4()), "quantidade": "1"}],
        "condicoes_default": {"parcelas": 1, "forma_pagamento": "pix"},
    }


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_criar_template_perfil_d_sem_selo_201() -> None:
    c = _cenario_perfil("D")
    r = _post(_client(c), _URL, _payload(selo=False))
    assert r.status_code == 201, r.content
    body = r.json()
    assert body["selo_rbc"] is False
    assert body["nome"] == "Calibracao balanca padrao"


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_criar_template_perfil_a_com_selo_201() -> None:
    """Perfil A pode criar template com selo RBC (D-ORC-13)."""
    c = _cenario_perfil("A")
    r = _post(_client(c), _URL, _payload(selo=True))
    assert r.status_code == 201, r.content
    assert r.json()["selo_rbc"] is True

    from src.infrastructure.orcamentos.models import Template as TModel

    with run_in_tenant_context(c["tenant"].id):
        assert TModel.objects.filter(tenant=c["tenant"], selo_rbc=True).count() == 1


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_criar_template_perfil_b_com_selo_422() -> None:
    """INV-ORC-SELO-RBC: perfil B + selo RBC → 422 selo_rbc_nao_permitido, nada gravado."""
    c = _cenario_perfil("B")
    r = _post(_client(c), _URL, _payload(selo=True))
    assert r.status_code == 422, r.content
    assert r.json()["codigo"] == "selo_rbc_nao_permitido"

    from src.infrastructure.orcamentos.models import Template as TModel

    with run_in_tenant_context(c["tenant"].id):
        assert TModel.all_objects.filter(tenant=c["tenant"]).count() == 0


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_criar_template_perfil_b_sem_selo_201() -> None:
    """Perfil B SEM selo é permitido (o gate só barra selo=True)."""
    c = _cenario_perfil("B")
    r = _post(_client(c), _URL, _payload(selo=False))
    assert r.status_code == 201, r.content
    assert r.json()["selo_rbc"] is False


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_listar_e_retrieve_template() -> None:
    c = _cenario_perfil("D")
    client = _client(c)
    criado = _post(client, _URL, _payload(nome="Template A")).json()

    lista = client.get(_URL)
    assert lista.status_code == 200, lista.content
    assert any(t["id"] == criado["id"] for t in lista.json())

    det = client.get(f"{_URL}{criado['id']}/")
    assert det.status_code == 200, det.content
    assert det.json()["nome"] == "Template A"


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_editar_template_perfil_b_adiciona_selo_422() -> None:
    """INV-ORC-SELO-RBC: editar template (perfil B) ligando selo RBC → 422."""
    c = _cenario_perfil("B")
    client = _client(c)
    criado = _post(client, _URL, _payload(selo=False)).json()

    r = client.put(
        f"{_URL}{criado['id']}/",
        _payload(nome="Template editado", selo=True),
        format="json",
        HTTP_IDEMPOTENCY_KEY=str(uuid4()),
    )
    assert r.status_code == 422, r.content
    assert r.json()["codigo"] == "selo_rbc_nao_permitido"


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_editar_template_perfil_d_atualiza_nome_200() -> None:
    c = _cenario_perfil("D")
    client = _client(c)
    criado = _post(client, _URL, _payload(nome="Antigo")).json()

    r = client.put(
        f"{_URL}{criado['id']}/",
        _payload(nome="Novo nome"),
        format="json",
        HTTP_IDEMPOTENCY_KEY=str(uuid4()),
    )
    assert r.status_code == 200, r.content
    assert r.json()["nome"] == "Novo nome"


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_soft_delete_template_some_da_listagem_e_retrieve_404() -> None:
    c = _cenario_perfil("D")
    client = _client(c)
    criado = _post(client, _URL, _payload()).json()

    d = client.delete(f"{_URL}{criado['id']}/")
    assert d.status_code == 204, d.content

    # Some da listagem (manager default filtra soft-deletados — Padrão C).
    assert all(t["id"] != criado["id"] for t in client.get(_URL).json())
    # Retrieve do soft-deletado → 404.
    assert client.get(f"{_URL}{criado['id']}/").status_code == 404

    from src.infrastructure.orcamentos.models import Template as TModel

    with run_in_tenant_context(c["tenant"].id):
        # all_objects ainda enxerga (auditoria); deletado_em preenchido.
        obj = TModel.all_objects.get(id=criado["id"])
        assert obj.deletado_em is not None


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_template_cross_tenant_404() -> None:
    """RLS: tenant B não enxerga template do tenant A (retrieve/delete → 404)."""
    ca = _cenario_perfil("D", sfx="tplA")
    cb = _cenario_perfil("D", sfx="tplB")
    criado = _post(_client(ca), _URL, _payload()).json()

    cliente_b = _client(cb)
    assert cliente_b.get(f"{_URL}{criado['id']}/").status_code == 404
    assert cliente_b.delete(f"{_URL}{criado['id']}/").status_code == 404


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_idempotencia_criar_template_nao_duplica() -> None:
    """Replay da mesma Idempotency-Key → mesma resposta, 1 template."""
    c = _cenario_perfil("D")
    client = _client(c)
    key = str(uuid4())
    p = _payload(nome="Idem")
    r1 = client.post(_URL, p, format="json", HTTP_IDEMPOTENCY_KEY=key)
    r2 = client.post(_URL, p, format="json", HTTP_IDEMPOTENCY_KEY=key)
    assert r1.status_code == 201, r1.content
    assert r2.status_code == 201, r2.content

    from src.infrastructure.orcamentos.models import Template as TModel

    with run_in_tenant_context(c["tenant"].id):
        assert TModel.objects.filter(tenant=c["tenant"], nome="Idem").count() == 1
