"""API /api/v1/catalogo/ — testes E2E Fatia 2 (T-PPS-030..035) em PG real.

Cobre o que os puros não provam: authz por papel (atendente 403), UNIQUE/
exclusion/CHECK reais por baixo dos use cases, Idempotency replay (resumo B9),
cross-tenant 404, **regressão INV-026 DURA** (consulta histórica `preco-vigente`
NÃO muda após nova versão/linha — TL-PPS-08) e **concorrência 2 criar-versão
simultâneos** (advisory lock 880_403 serializa; densidade max+1 sem buraco).
"""

from __future__ import annotations

import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID, uuid4

import pytest
from rest_framework.test import APIClient
from src.application.produtos_pecas_servicos import item as uc_item
from src.infrastructure.authz.django_provider import invalidate_user_cache
from src.infrastructure.produtos_pecas_servicos.repositories import (
    DjangoItemCatalogoRepository,
)

from tests.factories import (
    TenantFactory,
    UsuarioFactory,
    UsuarioPerfilTenantFactory,
)

_DBS = ["default", "breaker_writer"]


def _autenticar(client: APIClient, usuario, tenant) -> None:
    from django_otp import DEVICE_ID_SESSION_KEY
    from django_otp.plugins.otp_totp.models import TOTPDevice

    device, _ = TOTPDevice.objects.get_or_create(
        user=usuario, name="default", defaults={"confirmed": True}
    )
    if not device.confirmed:
        device.confirmed = True
        device.save()
    client.force_login(usuario)
    session = client.session
    session[DEVICE_ID_SESSION_KEY] = device.persistent_id
    session.save()
    client.defaults["HTTP_X_AFERE_ACTIVE_TENANT"] = str(tenant.id)


def _cenario():
    sfx = uuid4().hex[:8]
    tenant = TenantFactory(perfil_a=True, slug=f"pps-api-{sfx}")
    admin = UsuarioFactory(email=f"adm-{sfx}@pps.local")
    atendente = UsuarioFactory(email=f"ate-{sfx}@pps.local")
    UsuarioPerfilTenantFactory(usuario=admin, tenant=tenant, perfil="admin_tenant")
    UsuarioPerfilTenantFactory(usuario=atendente, tenant=tenant, perfil="atendente")
    for u in (admin, atendente):
        invalidate_user_cache(u.id, tenant.id)
    return {"tenant": tenant, "admin": admin, "atendente": atendente}


def _client(c, papel="admin") -> APIClient:
    client = APIClient()
    _autenticar(client, c[papel], c["tenant"])
    return client


def _post(client, url, payload, key=None):
    return client.post(url, payload, format="json", HTTP_IDEMPOTENCY_KEY=key or str(uuid4()))


def _payload_item(**kw):
    base = {
        "codigo_interno": f"P-{uuid4().hex[:6]}",
        "tipo": "peca",
        "nome": "Célula de carga 50kg",
        "unidade_medida": "un",
        "preco_padrao": "123.45",
    }
    base.update(kw)
    return base


def _cadastrar_item(client, **kw) -> dict:
    r = _post(client, "/api/v1/catalogo/itens/cadastrar/", _payload_item(**kw))
    assert r.status_code == 201, r.content
    return r.json()


def _criar_tabela(client) -> dict:
    r = _post(client, "/api/v1/catalogo/tabelas/criar/", {"nome": "Padrão"})
    assert r.status_code == 201, r.content
    return r.json()


def _criar_linha(client, tabela_id, item_id, preco="150.00", **kw) -> dict:
    payload = {"item_id": item_id, "preco": preco}
    payload.update(kw)
    r = _post(client, f"/api/v1/catalogo/tabelas/{tabela_id}/criar-linha/", payload)
    assert r.status_code == 201, r.content
    return r.json()


# === item (US-CAT-001/002/005) ===


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_cadastrar_item_e_retrieve():
    client = _client(_cenario())
    body = _cadastrar_item(client)
    assert body["status"] == "ativo"
    assert body["versao"]["versao_n"] == 1
    g = client.get(f"/api/v1/catalogo/itens/{body['id']}/")
    assert g.status_code == 200, g.content
    assert g.json()["versoes"][0]["preco_padrao"] == "123.45"


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_codigo_duplicado_409():
    client = _client(_cenario())
    body = _cadastrar_item(client)
    r = _post(
        client,
        "/api/v1/catalogo/itens/cadastrar/",
        _payload_item(codigo_interno=body["codigo_interno"]),
    )
    assert r.status_code == 409, r.content


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_atendente_nao_edita_403_mas_ve_200():
    c = _cenario()
    admin = _client(c)
    body = _cadastrar_item(admin)
    atendente = _client(c, "atendente")
    r = _post(atendente, "/api/v1/catalogo/itens/cadastrar/", _payload_item())
    assert r.status_code == 403
    g = atendente.get(f"/api/v1/catalogo/itens/{body['id']}/")
    assert g.status_code == 200  # catalogo.ver — seleção em OS


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_cross_tenant_404():
    c1, c2 = _cenario(), _cenario()
    body = _cadastrar_item(_client(c1))
    g = _client(c2).get(f"/api/v1/catalogo/itens/{body['id']}/")
    assert g.status_code == 404  # RLS — nem confirma existência


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_nova_versao_retroativa_422():
    client = _client(_cenario())
    body = _cadastrar_item(client)
    r = _post(
        client,
        f"/api/v1/catalogo/itens/{body['id']}/nova-versao/",
        {"preco_padrao": "200.00", "vigencia_inicio": "2026-01-01T00:00:00Z"},
    )
    assert r.status_code == 422, r.content


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_inativar_some_da_venda_nova():
    client = _client(_cenario())
    body = _cadastrar_item(client)
    r = _post(client, f"/api/v1/catalogo/itens/{body['id']}/inativar/", {})
    assert r.status_code == 200, r.content
    assert r.json()["status"] == "inativo"
    # nova versão de preço em item inativo → 422
    r2 = _post(
        client,
        f"/api/v1/catalogo/itens/{body['id']}/nova-versao/",
        {"preco_padrao": "200.00"},
    )
    assert r2.status_code == 422


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_idempotency_replay_devolve_resumo_reduzido():
    client = _client(_cenario())
    payload = _payload_item()
    key = str(uuid4())
    r1 = _post(client, "/api/v1/catalogo/itens/cadastrar/", payload, key=key)
    assert r1.status_code == 201
    r2 = _post(client, "/api/v1/catalogo/itens/cadastrar/", payload, key=key)
    assert r2.status_code == 201
    # B9: replay = resumo persistido sem texto livre (não o body completo).
    assert r2.json()["item_id"] == r1.json()["id"]
    assert "versao" not in r2.json()


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_sem_idempotency_key_400():
    client = _client(_cenario())
    r = client.post("/api/v1/catalogo/itens/cadastrar/", _payload_item(), format="json")
    assert r.status_code == 400, r.content


# === kit (US-CAT-003) ===


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_montar_kit_e_porta_exige_linha_propria():
    c = _cenario()
    client = _client(c)
    kit = _cadastrar_item(client, codigo_interno=f"K-{uuid4().hex[:6]}", tipo="kit")
    p1 = _cadastrar_item(client, preco_padrao="10.00")
    r = _post(
        client,
        f"/api/v1/catalogo/itens/{kit['id']}/montar-kit/",
        {"componentes": [{"item_filho_id": p1["id"], "quantidade": "2.000"}]},
    )
    assert r.status_code == 200, r.content
    tabela = _criar_tabela(client)
    # kit SEM linha própria → fail-closed 422 (TL-PPS-09)
    g = client.get(
        "/api/v1/catalogo/tabelas/preco-vigente/", {"item_id": kit["id"]}
    )
    assert g.status_code == 422
    assert g.json()["codigo"] == "PRECO_TABELA_AUSENTE"
    # linha própria sem preço → default sugerido = soma das partes (20.00)
    linha = _criar_linha(client, tabela["id"], kit["id"], preco=None)
    assert linha["preco"] == "20.00"
    assert linha["origem_sugestao"] == "soma_partes"
    g2 = client.get(
        "/api/v1/catalogo/tabelas/preco-vigente/", {"item_id": kit["id"]}
    )
    assert g2.status_code == 200, g2.content
    assert g2.json()["preco"] == "20.00"
    assert g2.json()["composicao_resolvida"][0]["quantidade"] == "2.000"


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_kit_dentro_de_kit_422():
    client = _client(_cenario())
    kit = _cadastrar_item(client, codigo_interno=f"K-{uuid4().hex[:6]}", tipo="kit")
    kit2 = _cadastrar_item(client, codigo_interno=f"K-{uuid4().hex[:6]}", tipo="kit")
    r = _post(
        client,
        f"/api/v1/catalogo/itens/{kit['id']}/montar-kit/",
        {"componentes": [{"item_filho_id": kit2["id"], "quantidade": "1.000"}]},
    )
    assert r.status_code == 422, r.content


# === porta preco-vigente (ADR-0081) ===


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_porta_resolve_venda_e_nao_lista():
    client = _client(_cenario())
    item = _cadastrar_item(client, preco_padrao="123.45")
    tabela = _criar_tabela(client)
    _criar_linha(client, tabela["id"], item["id"], preco="150.00")
    g = client.get("/api/v1/catalogo/tabelas/preco-vigente/", {"item_id": item["id"]})
    assert g.status_code == 200, g.content
    body = g.json()
    assert body["preco"] == "150.00"  # VENDA, não 123.45 da lista (D-PPS-2)
    assert body["item_versao_n"] == 1
    assert body["tabela_id"] == tabela["id"]
    assert body["linha_tabela_id"]


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_porta_sem_linha_422_fail_closed():
    client = _client(_cenario())
    item = _cadastrar_item(client)
    _criar_tabela(client)
    g = client.get("/api/v1/catalogo/tabelas/preco-vigente/", {"item_id": item["id"]})
    assert g.status_code == 422
    assert g.json()["codigo"] == "PRECO_TABELA_AUSENTE"


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_regressao_inv026_dura_consulta_historica_nao_muda():
    """TL-PPS-08: `preco-vigente(D)` responde IGUAL antes e depois de nova
    versão de lista E de troca de linha de venda (encerrar+criar)."""
    client = _client(_cenario())
    item = _cadastrar_item(client, preco_padrao="100.00")
    tabela = _criar_tabela(client)
    linha1 = _criar_linha(client, tabela["id"], item["id"], preco="150.00")

    d_historico = datetime.now(UTC).isoformat()  # APÓS criação, ANTES das mudanças
    consulta = {"item_id": item["id"], "data_referencia": d_historico}
    antes = client.get("/api/v1/catalogo/tabelas/preco-vigente/", consulta)
    assert antes.status_code == 200, antes.content
    assert antes.json()["preco"] == "150.00"

    # muda a LISTA (nova versão) e a VENDA (encerra linha1 + cria linha2)
    r = _post(
        client,
        f"/api/v1/catalogo/itens/{item['id']}/nova-versao/",
        {"preco_padrao": "110.00"},
    )
    assert r.status_code == 201, r.content
    corte = datetime.now(UTC).isoformat()
    r = _post(
        client,
        f"/api/v1/catalogo/tabelas/{tabela['id']}/encerrar-linha/",
        {"linha_id": linha1["id"], "fim": corte},
    )
    assert r.status_code == 200, r.content
    _criar_linha(client, tabela["id"], item["id"], preco="180.00", vigencia_inicio=corte)

    depois = client.get("/api/v1/catalogo/tabelas/preco-vigente/", consulta)
    assert depois.status_code == 200, depois.content
    # REGRESSÃO DURA: mesma resposta, mesmas refs probatórias.
    assert depois.json() == antes.json()
    # consulta SEM data (agora) resolve a nova venda
    atual = client.get("/api/v1/catalogo/tabelas/preco-vigente/", {"item_id": item["id"]})
    assert atual.json()["preco"] == "180.00"
    assert atual.json()["item_versao_n"] == 2


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_corrigir_linha_revoga_e_porta_resolve_substituta():
    """D-PPS-8 ponta-a-ponta: a CORREÇÃO (≠ mudança de preço) é o único
    caminho que muda resposta histórica — auditada via revogação+motivo."""
    client = _client(_cenario())
    item = _cadastrar_item(client)
    tabela = _criar_tabela(client)
    linha1 = _criar_linha(client, tabela["id"], item["id"], preco="510.00")  # erro de digitação
    r = _post(
        client,
        f"/api/v1/catalogo/tabelas/{tabela['id']}/corrigir-linha/",
        {
            "linha_id": linha1["id"],
            "preco": "150.00",
            "motivo": "preço digitado errado (510 em vez de 150)",
        },
    )
    assert r.status_code == 201, r.content
    assert r.json()["linha_revogada_id"] == linha1["id"]
    g = client.get("/api/v1/catalogo/tabelas/preco-vigente/", {"item_id": item["id"]})
    assert g.status_code == 200
    assert g.json()["preco"] == "150.00"
    assert g.json()["linha_tabela_id"] == r.json()["id"]  # substituta, não a revogada


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_segunda_tabela_padrao_422_e_linha_sobreposta_422():
    client = _client(_cenario())
    item = _cadastrar_item(client)
    tabela = _criar_tabela(client)
    r = _post(client, "/api/v1/catalogo/tabelas/criar/", {"nome": "Outra"})
    assert r.status_code == 422, r.content
    _criar_linha(client, tabela["id"], item["id"])
    r2 = _post(
        client,
        f"/api/v1/catalogo/tabelas/{tabela['id']}/criar-linha/",
        {"item_id": item["id"], "preco": "99.00"},
    )
    assert r2.status_code == 422, r2.content


# === concorrência (D-PPS-4 — advisory lock 880_403) ===


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_concorrencia_2_criar_versao_simultaneos_densidade_preservada():
    """2 threads criam versão no MESMO item ao mesmo tempo: o advisory lock
    serializa → ambas passam, `versao_n` denso {1,2,3}, zero violação da
    exclusion (sem 'buraco' nem duplicata)."""
    from django.db import connections, transaction
    from src.infrastructure.multitenant.connection import run_in_tenant_context

    c = _cenario()
    client = _client(c)
    item = _cadastrar_item(client, preco_padrao="100.00")
    tenant_id = c["tenant"].id
    item_id = UUID(item["id"])

    barreira = threading.Barrier(2)
    erros: list[Exception] = []

    def worker(preco: str) -> None:
        try:
            barreira.wait(timeout=10)
            with run_in_tenant_context(tenant_id):
                with transaction.atomic():
                    uc_item.nova_versao_preco(
                        uc_item.NovaVersaoPrecoInput(
                            tenant_id=tenant_id,
                            item_id=item_id,
                            preco_padrao=Decimal(preco),
                            criado_por=c["admin"].id,
                            agora=datetime.now(UTC),
                        ),
                        repo=DjangoItemCatalogoRepository(),
                    )
        except Exception as exc:  # — coletado e re-lançado no assert
            erros.append(exc)
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=2) as ex:
        for f in [ex.submit(worker, "110.00"), ex.submit(worker, "120.00")]:
            f.result()

    assert erros == [], f"corrida não serializada: {erros}"
    g = client.get(f"/api/v1/catalogo/itens/{item_id}/")
    versoes = g.json()["versoes"]
    assert sorted(v["versao_n"] for v in versoes) == [1, 2, 3]  # densa, sem buraco
    abertas = [v for v in versoes if v["vigencia_fim"] is None and v["revogado_em"] is None]
    assert len(abertas) == 1  # só a última vigente aberta


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_corrigir_versao_com_motivo_longo_500_chars_201():
    """P9 SEG-M1: motivo no teto do serializer (500) + prefixo de correção
    cabem na coluna ampliada (600) — antes era DataError 500 com chave presa."""
    client = _client(_cenario())
    body = _cadastrar_item(client)
    versao_id = body["versao"]["id"]
    r = _post(
        client,
        f"/api/v1/catalogo/itens/{body['id']}/corrigir-versao/",
        {"versao_id": versao_id, "motivo": "m" * 500, "preco_padrao": "111.00"},
    )
    assert r.status_code == 201, r.content
    assert r.json()["versao_revogada_id"] == versao_id
