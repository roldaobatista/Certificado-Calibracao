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

from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

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


def _cenario_perfil(perfil: str, *, sfx: str | None = None) -> dict:
    """Cenário com perfil regulatório explícito (A/B/C/D) — análise crítica 2c-2."""
    from src.infrastructure.authz.django_provider import invalidate_user_cache

    sfx = sfx or uuid4().hex[:8]
    trait = {"A": "perfil_a", "B": "perfil_b", "C": "perfil_c", "D": "perfil_d"}[perfil]
    tenant = TenantFactory(slug=f"orc-e2e-{sfx}", **{trait: True})
    admin = UsuarioFactory(email=f"adm-orc-{sfx}@e2e.local")
    UsuarioPerfilTenantFactory(usuario=admin, tenant=tenant, perfil="admin_tenant")
    invalidate_user_cache(admin.id, tenant.id)
    return {"tenant": tenant, "admin": admin}


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
            **_MENSURANDO,
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
            **_MENSURANDO,
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
            **_MENSURANDO,
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
            **_MENSURANDO,
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


# ===========================================================================
# Onda 2b — enviar / recusar / cancelar / expirar
# ===========================================================================


_MENSURANDO = {
    "grandeza_solicitada": "massa",
    "faixa_solicitada_min": "0",
    "faixa_solicitada_max": "30",
    "unidade_solicitada": "kg",
}


def _adicionar_item_calib(client, orc_id, item_id, *, desconto="0", qty="1"):
    return _post(
        client,
        f"/api/v1/orcamentos/{orc_id}/itens/",
        {
            "catalogo_item_id": item_id,
            "descricao": "Calibracao balanca",
            "quantidade": qty,
            "desconto_pct": desconto,
            "equipamento_id": str(uuid4()),
            "tipo_atividade_alvo": "calibracao",
            **_MENSURANDO,
        },
    )


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_enviar_gera_link_congela_versao_e_evento() -> None:
    c = _cenario()
    client = _client(c)
    cliente = _criar_cliente(c["tenant"], c["admin"])
    item = _setup_catalogo(client, preco="150.00")
    orc = _criar_orcamento(client, cliente.id).json()
    assert _adicionar_item_calib(client, orc["id"], item["id"]).status_code == 201

    r = _post(client, f"/api/v1/orcamentos/{orc['id']}/enviar/", {})
    assert r.status_code == 200, r.content
    body = r.json()
    assert body["orcamento"]["estado"] == "enviado"
    assert len(body["link"]["token"]) >= 20  # token urlsafe(32) ~ 43 chars
    assert body["link"]["orcamento_id"] == orc["id"]

    from src.infrastructure.audit.models import BusOutbox
    from src.infrastructure.orcamentos.models import VersaoOrcamento as VModel

    with run_in_tenant_context(c["tenant"].id):
        versao = VModel.objects.get(orcamento_id=orc["id"])
        assert versao.snapshot != {}, "versao deve congelar o snapshot ao enviar (D-ORC-8)"
        assert versao.snapshot["itens"], "snapshot deve conter os itens"
        n_evt = BusOutbox.objects.filter(
            tenant_id=c["tenant"].id,
            acao="orcamento.enviado",
            causation_id=UUID(orc["id"]),
        ).count()
        assert n_evt == 1, f"esperado 1 evento orcamento.enviado, achou {n_evt}"


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_enviar_sem_itens_422() -> None:
    c = _cenario()
    client = _client(c)
    cliente = _criar_cliente(c["tenant"], c["admin"])
    orc = _criar_orcamento(client, cliente.id).json()

    r = _post(client, f"/api/v1/orcamentos/{orc['id']}/enviar/", {})
    assert r.status_code == 422, r.content
    assert r.json()["codigo"] == "orcamento_sem_itens"


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_recusar_revoga_link_e_publica_evento() -> None:
    c = _cenario()
    client = _client(c)
    cliente = _criar_cliente(c["tenant"], c["admin"])
    item = _setup_catalogo(client, preco="150.00")
    orc = _criar_orcamento(client, cliente.id).json()
    _adicionar_item_calib(client, orc["id"], item["id"])
    _post(client, f"/api/v1/orcamentos/{orc['id']}/enviar/", {})

    r = _post(
        client,
        f"/api/v1/orcamentos/{orc['id']}/recusar/",
        {"motivo": "Cliente optou por outro fornecedor"},
    )
    assert r.status_code == 200, r.content
    assert r.json()["estado"] == "recusado"

    from src.infrastructure.audit.models import BusOutbox
    from src.infrastructure.orcamentos.models import LinkPublico as LinkModel

    with run_in_tenant_context(c["tenant"].id):
        # link revogado (nenhum ativo)
        ativos = LinkModel.objects.filter(orcamento_id=orc["id"], revogado_em__isnull=True).count()
        assert ativos == 0, "link deve ser revogado ao recusar"
        n_evt = BusOutbox.objects.filter(
            tenant_id=c["tenant"].id, acao="orcamento.recusado", causation_id=UUID(orc["id"])
        ).count()
        assert n_evt == 1


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_cancelar_rascunho_200() -> None:
    c = _cenario()
    client = _client(c)
    cliente = _criar_cliente(c["tenant"], c["admin"])
    orc = _criar_orcamento(client, cliente.id).json()

    r = _post(client, f"/api/v1/orcamentos/{orc['id']}/cancelar/", {"motivo": "desistencia"})
    assert r.status_code == 200, r.content
    assert r.json()["estado"] == "cancelado"


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_cancelar_enviado_409_transicao_proibida() -> None:
    c = _cenario()
    client = _client(c)
    cliente = _criar_cliente(c["tenant"], c["admin"])
    item = _setup_catalogo(client, preco="150.00")
    orc = _criar_orcamento(client, cliente.id).json()
    _adicionar_item_calib(client, orc["id"], item["id"])
    _post(client, f"/api/v1/orcamentos/{orc['id']}/enviar/", {})

    # enviado -> cancelado nao e transicao valida (D-ORC-3) -> 409
    r = _post(client, f"/api/v1/orcamentos/{orc['id']}/cancelar/", {})
    assert r.status_code == 409, r.content
    assert r.json()["codigo"] == "transicao_proibida"


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_cancelar_convertido_409() -> None:
    c = _cenario()
    client = _client(c)
    cliente = _criar_cliente(c["tenant"], c["admin"])
    orc = _criar_orcamento(client, cliente.id).json()

    # forca estado convertido (saga real = Onda 2c/2d); trigger 0004 permite
    # transicao DE estado nao-terminal -> convertido.
    from src.infrastructure.orcamentos.models import Orcamento as OrcModel

    with run_in_tenant_context(c["tenant"].id):
        OrcModel.objects.filter(id=orc["id"]).update(estado="convertido")

    r = _post(client, f"/api/v1/orcamentos/{orc['id']}/cancelar/", {})
    assert r.status_code == 409, r.content
    assert r.json()["codigo"] == "orcamento_convertido"


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_expirar_vencidos_idempotente() -> None:
    c = _cenario()
    client = _client(c)
    cliente = _criar_cliente(c["tenant"], c["admin"])
    item = _setup_catalogo(client, preco="150.00")
    orc = _criar_orcamento(client, cliente.id).json()
    _adicionar_item_calib(client, orc["id"], item["id"])
    _post(client, f"/api/v1/orcamentos/{orc['id']}/enviar/", {})

    # move a janela inteira para o passado (criar exige validade futura; simula
    # vencimento). inicio < fim < agora — respeita INV-VIG-001 (inicio <= fim).
    from src.infrastructure.orcamentos.models import Orcamento as OrcModel

    agora = datetime.now(UTC)
    with run_in_tenant_context(c["tenant"].id):
        OrcModel.objects.filter(id=orc["id"]).update(
            validade_inicio=agora - timedelta(days=40),
            validade_fim=agora - timedelta(days=1),
        )

    r1 = _post(client, "/api/v1/orcamentos/expirar-vencidos/", {})
    assert r1.status_code == 200, r1.content
    assert r1.json()["total"] == 1
    assert orc["id"] in r1.json()["expirados"]

    # idempotente: 2a varredura (nova chave) nao reprocessa ja-expirados
    r2 = _post(client, "/api/v1/orcamentos/expirar-vencidos/", {})
    assert r2.status_code == 200, r2.content
    assert r2.json()["total"] == 0

    r_get = client.get(f"/api/v1/orcamentos/{orc['id']}/")
    assert r_get.json()["estado"] == "expirado"

    from src.infrastructure.audit.models import BusOutbox

    with run_in_tenant_context(c["tenant"].id):
        n_evt = BusOutbox.objects.filter(
            tenant_id=c["tenant"].id, acao="orcamento.expirado", causation_id=UUID(orc["id"])
        ).count()
        assert n_evt == 1, "expirar deve publicar exatamente 1 evento orcamento.expirado"


# ===========================================================================
# Onda 2c-1 — item de calibracao declara o mensurando (D-ORC-5 / consultor-rbc)
# ===========================================================================


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_adicionar_item_calibracao_sem_mensurando_422() -> None:
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
            "descricao": "Calibracao sem mensurando",
            "quantidade": "1",
            "equipamento_id": str(uuid4()),
            "tipo_atividade_alvo": "calibracao",
            # SEM grandeza/faixa/unidade — deve ser rejeitado
        },
    )
    assert r.status_code == 422, r.content
    assert "mensurando" in str(r.json())


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_adicionar_item_calibracao_grandeza_invalida_422() -> None:
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
            "descricao": "Calibracao grandeza invalida",
            "quantidade": "1",
            "equipamento_id": str(uuid4()),
            "tipo_atividade_alvo": "calibracao",
            "grandeza_solicitada": "banana",  # nao e Grandeza valida (fail-fast C3)
            "faixa_solicitada_min": "0",
            "faixa_solicitada_max": "30",
            "unidade_solicitada": "kg",
        },
    )
    assert r.status_code == 422, r.content
    assert "grandeza_solicitada" in str(r.json())


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_item_comercial_com_mensurando_422() -> None:
    """Mensurando so e valido em item de calibracao (consultor-rbc C2)."""
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
            "descricao": "Deslocamento com mensurando indevido",
            "quantidade": "1",
            "tipo_item_comercial": "deslocamento",
            "grandeza_solicitada": "massa",
            "faixa_solicitada_min": "0",
            "faixa_solicitada_max": "30",
            "unidade_solicitada": "kg",
        },
    )
    assert r.status_code == 422, r.content
    assert "mensurando" in str(r.json())


# ===========================================================================
# Onda 2c-2 — aprovacao interna + analise critica cl. 7.1 (T-ORC-033)
# ===========================================================================


def _criar_enviar_com_calib(perfil: str) -> tuple[dict, APIClient, dict]:
    """Cria orcamento com 1 item de calibracao e envia. Retorna (cenario, client, orc)."""
    c = _cenario_perfil(perfil)
    client = _client(c)
    cliente = _criar_cliente(c["tenant"], c["admin"])
    item = _setup_catalogo(client, preco="150.00")
    orc = _criar_orcamento(client, cliente.id).json()
    add = _adicionar_item_calib(client, orc["id"], item["id"])
    assert add.status_code == 201, add.content
    orc["_equipamento_id"] = add.json()["item"]["equipamento_id"]
    env = _post(client, f"/api/v1/orcamentos/{orc['id']}/enviar/", {})
    assert env.status_code == 200, env.content
    return c, client, orc


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_aprovar_perfil_d_desabilitada_publica_envelope() -> None:
    """Perfil D: analise desabilitada -> aprova -> envelope orcamento.aprovado (D-ORC-6)."""
    c, client, orc = _criar_enviar_com_calib("D")

    r = _post(client, f"/api/v1/orcamentos/{orc['id']}/aprovar/", {})
    assert r.status_code == 200, r.content
    body = r.json()
    assert body["orcamento"]["estado"] == "aprovado_pendente_os"
    assert body["analise_critica"]["veredito"] == "desabilitada"
    assert body["analise_critica"]["itens_avaliados"] == []
    assert body["analise_critica"]["snapshot_hash"].startswith("v01$")

    from src.infrastructure.audit.models import BusOutbox
    from src.infrastructure.orcamentos.models import AnaliseCriticaOrcamento as AModel

    with run_in_tenant_context(c["tenant"].id):
        assert AModel.objects.filter(orcamento_id=orc["id"]).count() == 1
        aprovado = BusOutbox.objects.filter(
            tenant_id=c["tenant"].id,
            acao="orcamento.aprovado",
            causation_id=UUID(orc["id"]),
        )
        assert aprovado.count() == 1
        # publicar_evento envolve o payload em envelope_jsonb={..., "payload": {...}}.
        payload = aprovado.first().envelope_jsonb["payload"]
        # Equipamento POR ITEM no envelope (item de calibracao vira atividade).
        assert payload["itens"][0]["equipamento_id"] == orc["_equipamento_id"]
        assert payload["analise_critica_id"] is not None
        assert payload["analise_critica_snapshot_hash"].startswith("v01$")
        # Sem evento de reprovada quando desabilitada.
        assert not BusOutbox.objects.filter(
            acao="orcamento.analise_critica_reprovada", causation_id=UUID(orc["id"])
        ).exists()


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_aprovar_perfil_a_sem_cmc_reprova_422_grava_worm() -> None:
    """Perfil A fail-closed: item sem CMC/procedimento -> 422 + WORM + evento (INV-ORC-CL71)."""
    c, client, orc = _criar_enviar_com_calib("A")

    r = _post(client, f"/api/v1/orcamentos/{orc['id']}/aprovar/", {})
    assert r.status_code == 422, r.content
    body = r.json()
    assert body["codigo"] == "analise_critica_reprovada"
    assert body["analise_critica"]["veredito"] == "reprovada"
    # NAO transicionou — permanece enviado (fail-closed).
    assert body["orcamento"]["estado"] == "enviado"

    from src.infrastructure.audit.models import BusOutbox
    from src.infrastructure.orcamentos.models import AnaliseCriticaOrcamento as AModel
    from src.infrastructure.orcamentos.models import Orcamento as OModel

    with run_in_tenant_context(c["tenant"].id):
        # Analise WORM gravada mesmo reprovando (AJUSTE-1) — a transacao COMMITOU.
        assert AModel.objects.filter(orcamento_id=orc["id"]).count() == 1
        assert OModel.objects.get(id=orc["id"]).estado == "enviado"
        assert (
            BusOutbox.objects.filter(
                acao="orcamento.analise_critica_reprovada", causation_id=UUID(orc["id"])
            ).count()
            == 1
        )
        # Reprovada NUNCA publica orcamento.aprovado.
        assert not BusOutbox.objects.filter(
            acao="orcamento.aprovado", causation_id=UUID(orc["id"])
        ).exists()


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_aprovar_idempotente_nao_duplica_analise() -> None:
    """Replay da mesma Idempotency-Key -> mesma resposta, sem 2a analise WORM."""
    c, client, orc = _criar_enviar_com_calib("D")
    key = str(uuid4())
    url = f"/api/v1/orcamentos/{orc['id']}/aprovar/"

    r1 = client.post(url, {}, format="json", HTTP_IDEMPOTENCY_KEY=key)
    r2 = client.post(url, {}, format="json", HTTP_IDEMPOTENCY_KEY=key)
    assert r1.status_code == 200, r1.content
    assert r2.status_code == 200, r2.content

    from src.infrastructure.audit.models import BusOutbox
    from src.infrastructure.orcamentos.models import AnaliseCriticaOrcamento as AModel

    with run_in_tenant_context(c["tenant"].id):
        assert AModel.objects.filter(orcamento_id=orc["id"]).count() == 1
        assert (
            BusOutbox.objects.filter(
                acao="orcamento.aprovado", causation_id=UUID(orc["id"])
            ).count()
            == 1
        )


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_aprovar_rascunho_409_transicao_proibida() -> None:
    """Aprovar orcamento ainda em rascunho (nao enviado) -> 409 (D-ORC-3)."""
    c = _cenario_perfil("D")
    client = _client(c)
    cliente = _criar_cliente(c["tenant"], c["admin"])
    item = _setup_catalogo(client)
    orc = _criar_orcamento(client, cliente.id).json()
    assert _adicionar_item_calib(client, orc["id"], item["id"]).status_code == 201

    r = _post(client, f"/api/v1/orcamentos/{orc['id']}/aprovar/", {})
    assert r.status_code == 409, r.content
    assert r.json()["codigo"] == "transicao_proibida"


# ===========================================================================
# Onda 2d — consumer os.aberta fecha a saga (T-ORC-035 / D-ORC-14)
# ===========================================================================


def _aprovar_para_pendente_os(perfil: str = "D") -> tuple[dict, dict]:
    """Cria→item→envia→aprova (perfil D) -> orçamento em aprovado_pendente_os."""
    c, client, orc = _criar_enviar_com_calib(perfil)
    r = _post(client, f"/api/v1/orcamentos/{orc['id']}/aprovar/", {})
    assert r.status_code == 200, r.content
    assert r.json()["orcamento"]["estado"] == "aprovado_pendente_os"
    return c, orc


def _envelope_os_aberta(tenant_id, orcamento_id: str | None, *, numero_os: str = "OS-2026-000123"):
    payload: dict = {"numero_os": numero_os, "atividades_planejadas": [], "itens_comerciais_count": 0}
    if orcamento_id is not None:
        payload["orcamento_id"] = orcamento_id
    return {
        "event_id": str(uuid4()),
        "correlation_id": str(uuid4()),
        "tenant_id": str(tenant_id),
        "acao": "os.aberta",
        "payload": payload,
    }


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_consumer_os_aberta_converte_orcamento() -> None:
    """os.aberta com orcamento_id -> aprovado_pendente_os→convertido + evento."""
    from src.infrastructure.audit.models import BusOutbox
    from src.infrastructure.orcamentos.consumers.os_aberta import handle_os_aberta
    from src.infrastructure.orcamentos.models import Orcamento as OModel

    c, orc = _aprovar_para_pendente_os()
    with run_in_tenant_context(c["tenant"].id):
        handle_os_aberta(_envelope_os_aberta(c["tenant"].id, orc["id"]))
        assert OModel.objects.get(id=orc["id"]).estado == "convertido"
        eventos = BusOutbox.objects.filter(
            acao="orcamento.convertido", causation_id=UUID(orc["id"])
        )
        assert eventos.count() == 1
        assert eventos.first().envelope_jsonb["payload"]["numero_os"] == "OS-2026-000123"


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_consumer_os_aberta_avulsa_sem_orcamento_id_noop() -> None:
    """OS avulsa publica os.aberta SEM orcamento_id -> no-op (TL-ORC ALTO-1)."""
    from src.infrastructure.audit.models import BusOutbox
    from src.infrastructure.orcamentos.consumers.os_aberta import handle_os_aberta

    c = _cenario_perfil("D")
    with run_in_tenant_context(c["tenant"].id):
        # Não deve levantar nem publicar nada.
        handle_os_aberta(_envelope_os_aberta(c["tenant"].id, None))
        assert not BusOutbox.objects.filter(acao="orcamento.convertido").exists()


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_consumer_os_aberta_replay_idempotente() -> None:
    """Replay do MESMO event_id -> 1 conversão, 1 evento (consumer_idempotente)."""
    from src.infrastructure.audit.models import BusOutbox
    from src.infrastructure.orcamentos.consumers.os_aberta import handle_os_aberta
    from src.infrastructure.orcamentos.models import Orcamento as OModel

    c, orc = _aprovar_para_pendente_os()
    envelope = _envelope_os_aberta(c["tenant"].id, orc["id"])
    with run_in_tenant_context(c["tenant"].id):
        handle_os_aberta(envelope)
        handle_os_aberta(envelope)  # replay mesmo event_id
        assert OModel.objects.get(id=orc["id"]).estado == "convertido"
        assert (
            BusOutbox.objects.filter(
                acao="orcamento.convertido", causation_id=UUID(orc["id"])
            ).count()
            == 1
        )


def _envelope_anonimizacao(tenant_id, cliente_id):
    return {
        "event_id": str(uuid4()),
        "correlation_id": str(uuid4()),
        "tenant_id": str(tenant_id),
        "acao": "cliente.dados_anonimizados",
        "payload": {"cliente_id": str(cliente_id), "tenant_id": str(tenant_id)},
    }


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_consumer_cliente_anonimizado_cancela_rascunho_expira_enviado() -> None:
    """Anonimização: rascunho→cancelado; enviado→expirado + link revogado (Roldão 2026-06-15)."""
    from src.infrastructure.orcamentos.consumers.cliente_anonimizado import (
        handle_cliente_anonimizado,
    )
    from src.infrastructure.orcamentos.models import LinkPublico as LinkModel
    from src.infrastructure.orcamentos.models import Orcamento as OModel

    c = _cenario_perfil("D")
    client = _client(c)
    cliente = _criar_cliente(c["tenant"], c["admin"])
    item = _setup_catalogo(client)

    orc_rascunho = _criar_orcamento(client, cliente.id).json()
    assert _adicionar_item_calib(client, orc_rascunho["id"], item["id"]).status_code == 201

    orc_enviado = _criar_orcamento(client, cliente.id).json()
    assert _adicionar_item_calib(client, orc_enviado["id"], item["id"]).status_code == 201
    assert _post(client, f"/api/v1/orcamentos/{orc_enviado['id']}/enviar/", {}).status_code == 200

    with run_in_tenant_context(c["tenant"].id):
        handle_cliente_anonimizado(_envelope_anonimizacao(c["tenant"].id, cliente.id))
        assert OModel.objects.get(id=orc_rascunho["id"]).estado == "cancelado"
        assert OModel.objects.get(id=orc_enviado["id"]).estado == "expirado"
        # Link público do enviado foi revogado (corta exposição de PII — LGPD).
        link = LinkModel.objects.get(orcamento_id=orc_enviado["id"])
        assert link.revogado_em is not None


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_consumer_cliente_anonimizado_preserva_aprovado_pendente_os() -> None:
    """Anonimização preserva orçamento já aprovado (documento consolidado)."""
    from src.infrastructure.orcamentos.consumers.cliente_anonimizado import (
        handle_cliente_anonimizado,
    )
    from src.infrastructure.orcamentos.models import Orcamento as OModel

    c = _cenario_perfil("D")
    client = _client(c)
    cliente = _criar_cliente(c["tenant"], c["admin"])
    item = _setup_catalogo(client)
    orc = _criar_orcamento(client, cliente.id).json()
    assert _adicionar_item_calib(client, orc["id"], item["id"]).status_code == 201
    assert _post(client, f"/api/v1/orcamentos/{orc['id']}/enviar/", {}).status_code == 200
    assert _post(client, f"/api/v1/orcamentos/{orc['id']}/aprovar/", {}).status_code == 200

    with run_in_tenant_context(c["tenant"].id):
        handle_cliente_anonimizado(_envelope_anonimizacao(c["tenant"].id, cliente.id))
        assert OModel.objects.get(id=orc["id"]).estado == "aprovado_pendente_os"


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_consumer_cliente_anonimizado_replay_idempotente() -> None:
    """Replay do mesmo event_id não reprocessa (consumer_idempotente)."""
    from src.infrastructure.orcamentos.consumers.cliente_anonimizado import (
        handle_cliente_anonimizado,
    )
    from src.infrastructure.orcamentos.models import Orcamento as OModel

    c = _cenario_perfil("D")
    client = _client(c)
    cliente = _criar_cliente(c["tenant"], c["admin"])
    item = _setup_catalogo(client)
    orc_rascunho = _criar_orcamento(client, cliente.id).json()
    assert _adicionar_item_calib(client, orc_rascunho["id"], item["id"]).status_code == 201

    envelope = _envelope_anonimizacao(c["tenant"].id, cliente.id)
    with run_in_tenant_context(c["tenant"].id):
        handle_cliente_anonimizado(envelope)
        handle_cliente_anonimizado(envelope)  # replay
        assert OModel.objects.get(id=orc_rascunho["id"]).estado == "cancelado"


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_consumer_os_aberta_ja_convertido_event_id_novo_noop() -> None:
    """2º os.aberta (event_id novo) p/ orçamento já convertido -> não republica."""
    from src.infrastructure.audit.models import BusOutbox
    from src.infrastructure.orcamentos.consumers.os_aberta import handle_os_aberta
    from src.infrastructure.orcamentos.models import Orcamento as OModel

    c, orc = _aprovar_para_pendente_os()
    with run_in_tenant_context(c["tenant"].id):
        handle_os_aberta(_envelope_os_aberta(c["tenant"].id, orc["id"]))
        # 2º evento distinto (event_id novo), mesmo orçamento já convertido.
        handle_os_aberta(_envelope_os_aberta(c["tenant"].id, orc["id"]))
        assert OModel.objects.get(id=orc["id"]).estado == "convertido"
        assert (
            BusOutbox.objects.filter(
                acao="orcamento.convertido", causation_id=UUID(orc["id"])
            ).count()
            == 1
        )
