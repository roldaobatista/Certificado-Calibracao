"""Orcamentos Fatia 2 / Onda 2a — E2E PG-real (T-ORC-030/031/037 parcial).

Cobre o que os testes puros nao provam (banco COM dados, RLS, RBAC, idempotencia):
  1. criar orcamento rascunho (numero reservado via SerieDocumento lazy) -> 201.
  2. cliente bloqueado / inexistente -> 422 (D-ORC-4).
  3. adicionar item de calibracao SEM regra de formacao -> semaforo "indisponivel"
     persiste (prova o conserto REGRA #0 do campo max_length=10->15).
  4. adicionar item comercial (sem equipamento) -> 201 (bifurcacao INV-ORC-EQUIP-ITEM).
  5. totais coerentes: liquido == total_bruto - descontos (imposto por dentro).
  6. bifurcacao invalida (equipamento sem tipo_atividade_alvo) -> 422.
  7. cross-tenant: tenant B adiciona item em orcamento de A -> 404 (RLS).
  8. RBAC: comissao_prevista so com orcamento.ver_margem.
"""

from __future__ import annotations

from uuid import uuid4

import pytest
from rest_framework.test import APIClient
from src.infrastructure.multitenant.connection import run_in_tenant_context

from tests.factories import TenantFactory, UsuarioFactory, UsuarioPerfilTenantFactory

_DBS = ["default", "breaker_writer"]


# ---------------------------------------------------------------------------
# Autenticacao + cenario (molde precificacao E2E)
# ---------------------------------------------------------------------------


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


def _cenario(*, sfx: str | None = None) -> dict:
    from src.infrastructure.authz.django_provider import invalidate_user_cache

    sfx = sfx or uuid4().hex[:8]
    tenant = TenantFactory(perfil_b=True, slug=f"orc-e2e-{sfx}")
    admin = UsuarioFactory(email=f"adm-orc-{sfx}@e2e.local")
    atendente = UsuarioFactory(email=f"atd-orc-{sfx}@e2e.local")
    UsuarioPerfilTenantFactory(usuario=admin, tenant=tenant, perfil="admin_tenant")
    UsuarioPerfilTenantFactory(usuario=atendente, tenant=tenant, perfil="atendente")
    for u in (admin, atendente):
        invalidate_user_cache(u.id, tenant.id)
    return {"tenant": tenant, "admin": admin, "atendente": atendente}


def _client(c: dict, papel: str = "admin") -> APIClient:
    client = APIClient()
    _autenticar(client, c[papel], c["tenant"])
    return client


def _post(client: APIClient, url: str, payload: dict, key: str | None = None):
    return client.post(url, payload, format="json", HTTP_IDEMPOTENCY_KEY=key or str(uuid4()))


# ---------------------------------------------------------------------------
# Setup: cliente (ORM), catalogo + tabela + linha + params (REST precificacao)
# ---------------------------------------------------------------------------


def _criar_cliente(tenant, usuario):
    from src.infrastructure.clientes.models import Cliente, TipoPessoa

    with run_in_tenant_context(tenant.id, usuario_id=usuario.id):
        return Cliente.objects.create(
            tenant=tenant,
            tipo_pessoa=TipoPessoa.PJ,
            documento="11222333000181",
            nome="Cliente Orcamento Teste",
            aceite_lgpd_dispensa_motivo="pj_sem_pf_associada",
        )


def _bloquear_cliente(tenant, cliente, usuario) -> None:
    from src.infrastructure.clientes.models import ClienteBloqueio

    with run_in_tenant_context(tenant.id, usuario_id=usuario.id):
        ClienteBloqueio.objects.create(
            tenant=tenant,
            cliente=cliente,
            motivo_categoria="manual_inadimplencia",
            justificativa_bruta="Cliente nao pagou 3 faturas e nao respondeu contato algum",
            confirmacao_comunicacao_previa=True,
            bloqueado_por_usuario_id=usuario.id,
        )


def _cadastrar_item(client: APIClient, preco_padrao: str = "150.00") -> dict:
    r = _post(
        client,
        "/api/v1/catalogo/itens/cadastrar/",
        {
            "codigo_interno": f"ORC-{uuid4().hex[:6]}",
            "tipo": "servico",
            "nome": "Calibracao balanca",
            "unidade_medida": "un",
            "preco_padrao": preco_padrao,
        },
    )
    assert r.status_code == 201, r.content
    return r.json()


def _criar_tabela(client: APIClient) -> dict:
    r = _post(client, "/api/v1/catalogo/tabelas/criar/", {"nome": "Padrao"})
    assert r.status_code == 201, r.content
    return r.json()


def _criar_linha(client: APIClient, tabela_id: str, item_id: str, preco: str = "150.00") -> dict:
    r = _post(
        client,
        f"/api/v1/catalogo/tabelas/{tabela_id}/criar-linha/",
        {"item_id": item_id, "preco": preco},
    )
    assert r.status_code == 201, r.content
    return r.json()


def _configurar_params(client: APIClient) -> None:
    r = _post(
        client,
        "/api/v1/config/parametros/",
        {
            "custo_km": "0.00",
            "taxa_parcelamento_mensal": "0.00",
            "pct_comissao_prevista": "0.00",
            "margem_alvo_default": "20.00",
            "margem_piso_default": "5.00",
        },
    )
    assert r.status_code == 201, r.content


def _setup_catalogo(client: APIClient, preco: str = "150.00") -> dict:
    item = _cadastrar_item(client, preco_padrao=preco)
    tabela = _criar_tabela(client)
    _criar_linha(client, tabela["id"], item["id"], preco=preco)
    _configurar_params(client)
    return item


def _criar_orcamento(client: APIClient, cliente_id) -> object:
    return _post(
        client,
        "/api/v1/orcamentos/",
        {"cliente_id": str(cliente_id), "validade_dias": 30},
    )


# ---------------------------------------------------------------------------
# 1. Criar orcamento rascunho
# ---------------------------------------------------------------------------


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_criar_orcamento_rascunho_201() -> None:
    c = _cenario()
    client = _client(c)
    cliente = _criar_cliente(c["tenant"], c["admin"])

    r = _criar_orcamento(client, cliente.id)
    assert r.status_code == 201, r.content
    body = r.json()
    assert body["estado"] == "rascunho"
    assert isinstance(body["numero"], int) and body["numero"] >= 1
    assert body["cliente_atual_id"] == str(cliente.id)
    assert body["total_bruto"]["centavos"] == 0

    # retrieve devolve o orcamento (com lista de itens vazia)
    r_get = client.get(f"/api/v1/orcamentos/{body['id']}/")
    assert r_get.status_code == 200, r_get.content
    assert r_get.json()["itens"] == []


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_numero_incrementa_entre_orcamentos() -> None:
    c = _cenario()
    client = _client(c)
    cliente = _criar_cliente(c["tenant"], c["admin"])

    n1 = _criar_orcamento(client, cliente.id).json()["numero"]
    n2 = _criar_orcamento(client, cliente.id).json()["numero"]
    assert n2 == n1 + 1, f"numeracao densa esperada: {n1} -> {n2}"


# ---------------------------------------------------------------------------
# 2. Cliente bloqueado / inexistente -> 422
# ---------------------------------------------------------------------------


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_criar_orcamento_cliente_bloqueado_422() -> None:
    c = _cenario()
    client = _client(c)
    cliente = _criar_cliente(c["tenant"], c["admin"])
    _bloquear_cliente(c["tenant"], cliente, c["admin"])

    r = _criar_orcamento(client, cliente.id)
    assert r.status_code == 422, r.content
    assert r.json()["codigo"] == "cliente_bloqueado"


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_criar_orcamento_cliente_inexistente_422() -> None:
    c = _cenario()
    client = _client(c)
    r = _criar_orcamento(client, uuid4())
    assert r.status_code == 422, r.content
    assert r.json()["codigo"] == "cliente_bloqueado"


# ---------------------------------------------------------------------------
# 3. Adicionar item de calibracao -> semaforo "indisponivel" persiste
# ---------------------------------------------------------------------------


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_adicionar_item_calibracao_semaforo_indisponivel() -> None:
    """Conserto REGRA #0: sem regra de formacao -> Semaforo.INDISPONIVEL (12 chars).

    Prova que o campo `semaforo` (ampliado 10->15) aceita "indisponivel" — antes
    estouraria DataError no INSERT.
    """
    c = _cenario()
    client = _client(c)
    cliente = _criar_cliente(c["tenant"], c["admin"])
    item = _setup_catalogo(client, preco="150.00")

    orc = _criar_orcamento(client, cliente.id).json()
    equipamento_id = str(uuid4())

    r = _post(
        client,
        f"/api/v1/orcamentos/{orc['id']}/itens/",
        {
            "catalogo_item_id": item["id"],
            "descricao": "Calibracao balanca 30kg",
            "quantidade": "1",
            "desconto_pct": "0",
            "equipamento_id": equipamento_id,
            "tipo_atividade_alvo": "calibracao",
        },
    )
    assert r.status_code == 201, r.content
    body = r.json()
    assert body["item"]["semaforo"] == "indisponivel"
    assert body["item"]["equipamento_id"] == equipamento_id
    assert body["item"]["tipo_atividade_alvo"] == "calibracao"
    assert body["item"]["preco_final"]["centavos"] == 15000  # 150.00
    assert body["orcamento"]["liquido"]["centavos"] == 15000


# ---------------------------------------------------------------------------
# 4. Item comercial (sem equipamento) -> 201
# ---------------------------------------------------------------------------


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_adicionar_item_comercial_sem_equipamento() -> None:
    c = _cenario()
    client = _client(c)
    cliente = _criar_cliente(c["tenant"], c["admin"])
    item = _setup_catalogo(client, preco="80.00")

    orc = _criar_orcamento(client, cliente.id).json()
    r = _post(
        client,
        f"/api/v1/orcamentos/{orc['id']}/itens/",
        {
            "catalogo_item_id": item["id"],
            "descricao": "Deslocamento ate o cliente",
            "quantidade": "1",
            "tipo_item_comercial": "deslocamento",
        },
    )
    assert r.status_code == 201, r.content
    body = r.json()
    assert body["item"]["equipamento_id"] is None
    assert body["item"]["tipo_item_comercial"] == "deslocamento"
    assert body["item"]["tipo_atividade_alvo"] is None


# ---------------------------------------------------------------------------
# 5. Totais coerentes: liquido == total_bruto - descontos
# ---------------------------------------------------------------------------


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_totais_coerentes_com_desconto() -> None:
    c = _cenario()
    client = _client(c)
    cliente = _criar_cliente(c["tenant"], c["admin"])
    item = _setup_catalogo(client, preco="150.00")

    orc = _criar_orcamento(client, cliente.id).json()
    r = _post(
        client,
        f"/api/v1/orcamentos/{orc['id']}/itens/",
        {
            "catalogo_item_id": item["id"],
            "descricao": "Servico com desconto",
            "quantidade": "2",
            "desconto_pct": "10",
            "equipamento_id": str(uuid4()),
            "tipo_atividade_alvo": "calibracao",
        },
    )
    assert r.status_code == 201, r.content
    o = r.json()["orcamento"]
    bruto = o["total_bruto"]["centavos"]
    descontos = o["descontos"]["centavos"]
    liquido = o["liquido"]["centavos"]
    # preco 150, desconto 10% -> final 135/un * 2 = 270 (27000); bruto 300 (30000); desc 30 (3000)
    assert liquido == 27000, o
    assert bruto == 30000, o
    assert descontos == 3000, o
    assert liquido == bruto - descontos, "liquido deve ser bruto - descontos (imposto por dentro)"


# ---------------------------------------------------------------------------
# 6. Bifurcacao invalida -> 422 (serializer)
# ---------------------------------------------------------------------------


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_item_equipamento_sem_tipo_atividade_422() -> None:
    c = _cenario()
    client = _client(c)
    cliente = _criar_cliente(c["tenant"], c["admin"])
    item = _setup_catalogo(client)

    orc = _criar_orcamento(client, cliente.id).json()
    r = _post(
        client,
        f"/api/v1/orcamentos/{orc['id']}/itens/",
        {
            "catalogo_item_id": item["id"],
            "descricao": "Item invalido",
            "quantidade": "1",
            "equipamento_id": str(uuid4()),
            # falta tipo_atividade_alvo
        },
    )
    assert r.status_code == 422, r.content
    assert "tipo_atividade_alvo" in r.json()


# ---------------------------------------------------------------------------
# 7. Cross-tenant -> 404
# ---------------------------------------------------------------------------


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_cross_tenant_adicionar_item_404() -> None:
    c_a = _cenario()
    c_b = _cenario()
    client_a = _client(c_a)
    client_b = _client(c_b)

    cliente_a = _criar_cliente(c_a["tenant"], c_a["admin"])
    item_a = _setup_catalogo(client_a)
    orc_a = _criar_orcamento(client_a, cliente_a.id).json()

    r = _post(
        client_b,
        f"/api/v1/orcamentos/{orc_a['id']}/itens/",
        {
            "catalogo_item_id": item_a["id"],
            "descricao": "tentativa cross-tenant",
            "quantidade": "1",
            "tipo_item_comercial": "outro",
        },
    )
    assert r.status_code == 404, f"cross-tenant deveria ser 404, foi {r.status_code}: {r.content}"


# ---------------------------------------------------------------------------
# 8. RBAC: comissao_prevista so com orcamento.ver_margem
# ---------------------------------------------------------------------------


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_rbac_comissao_so_com_ver_margem() -> None:
    c = _cenario()
    admin_client = _client(c, "admin")
    atendente_client = _client(c, "atendente")
    cliente = _criar_cliente(c["tenant"], c["admin"])

    orc = _criar_orcamento(admin_client, cliente.id).json()

    # admin (gerente/admin tem ver_margem) ve comissao_prevista
    r_adm = admin_client.get(f"/api/v1/orcamentos/{orc['id']}/")
    assert r_adm.status_code == 200, r_adm.content
    assert "comissao_prevista" in r_adm.json()

    # atendente NAO ve comissao
    r_atd = atendente_client.get(f"/api/v1/orcamentos/{orc['id']}/")
    assert r_atd.status_code == 200, r_atd.content
    assert "comissao_prevista" not in r_atd.json()


# ---------------------------------------------------------------------------
# 9. Editar item: reprecifica + preserva sequencia + recompoe totais
# ---------------------------------------------------------------------------


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_editar_item_reprecifica_e_recompoe_totais() -> None:
    c = _cenario()
    client = _client(c)
    cliente = _criar_cliente(c["tenant"], c["admin"])
    item = _setup_catalogo(client, preco="150.00")
    orc = _criar_orcamento(client, cliente.id).json()

    r_add = _post(
        client,
        f"/api/v1/orcamentos/{orc['id']}/itens/",
        {
            "catalogo_item_id": item["id"],
            "descricao": "Calibracao",
            "quantidade": "1",
            "desconto_pct": "0",
            "equipamento_id": str(uuid4()),
            "tipo_atividade_alvo": "calibracao",
        },
    )
    assert r_add.status_code == 201, r_add.content
    item_id = r_add.json()["item"]["id"]
    sequencia = r_add.json()["item"]["sequencia"]

    r_ed = _post(
        client,
        f"/api/v1/orcamentos/{orc['id']}/itens/{item_id}/editar/",
        {
            "catalogo_item_id": item["id"],
            "descricao": "Calibracao reprecificada",
            "quantidade": "2",
            "desconto_pct": "10",
            "equipamento_id": str(uuid4()),
            "tipo_atividade_alvo": "calibracao",
        },
    )
    assert r_ed.status_code == 200, r_ed.content
    body = r_ed.json()
    assert body["item"]["id"] == item_id
    assert body["item"]["sequencia"] == sequencia  # preservada
    assert body["item"]["desconto_pct"] == "10.00"
    # 150 -10% = 135/un * 2 = 270 (27000); bruto 300 (30000); desc 30 (3000)
    assert body["orcamento"]["liquido"]["centavos"] == 27000
    assert body["orcamento"]["total_bruto"]["centavos"] == 30000
    assert body["orcamento"]["descontos"]["centavos"] == 3000


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_editar_item_inexistente_404() -> None:
    c = _cenario()
    client = _client(c)
    cliente = _criar_cliente(c["tenant"], c["admin"])
    item = _setup_catalogo(client)
    orc = _criar_orcamento(client, cliente.id).json()

    r = _post(
        client,
        f"/api/v1/orcamentos/{orc['id']}/itens/{uuid4()}/editar/",
        {
            "catalogo_item_id": item["id"],
            "descricao": "item inexistente",
            "quantidade": "1",
            "tipo_item_comercial": "outro",
        },
    )
    assert r.status_code == 404, r.content
    assert r.json()["codigo"] == "item_orcamento_nao_encontrado"


# ---------------------------------------------------------------------------
# 10. Idempotencia: replay (mesma chave) nao reincrementa numero
# ---------------------------------------------------------------------------


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_replay_mesma_chave_nao_reincrementa_numero() -> None:
    c = _cenario()
    client = _client(c)
    cliente = _criar_cliente(c["tenant"], c["admin"])
    payload = {"cliente_id": str(cliente.id), "validade_dias": 30}
    key = str(uuid4())

    r1 = _post(client, "/api/v1/orcamentos/", payload, key=key)
    assert r1.status_code == 201, r1.content
    n1 = r1.json()["numero"]

    # mesma chave + mesmo payload -> replay (resposta cacheada, sem reservar numero)
    r2 = _post(client, "/api/v1/orcamentos/", payload, key=key)
    assert r2.status_code == 201, r2.content
    assert r2.json()["numero"] == n1

    # nova chave -> novo orcamento; numero = n1+1 (replay nao queimou numero)
    r3 = _post(client, "/api/v1/orcamentos/", payload, key=str(uuid4()))
    assert r3.status_code == 201, r3.content
    assert r3.json()["numero"] == n1 + 1

    from src.infrastructure.orcamentos.models import Orcamento as OrcModel

    with run_in_tenant_context(c["tenant"].id):
        total = OrcModel.objects.filter(tenant_id=c["tenant"].id).count()
    assert total == 2, f"replay nao deve criar orcamento extra (esperado 2, obteve {total})"
