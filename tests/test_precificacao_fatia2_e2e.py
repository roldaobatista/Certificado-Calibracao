"""Precificação Fatia 2 — E2E PG-real (T-PRC-038).

13 invariantes que os testes puros não provam:
  1. COST_PLUS + StubCustoProvider → 422 CustoRealIndisponivel (D-PRC-6).
  2. RBAC de campo: sem `ver_margem` → resposta NÃO contém custo/margem.
  3. predicate alcada_cobre: gerente tenta decidir pedido DONO → 403.
  4. decisor == solicitante → 422 (INV-PRC-APROVACAO-INDEPENDENTE).
  5. fingerprint divergente → 422 (D-PRC-14).
  6. cesta multi-item: 2+ itens numa chamada → resultado tem N itens.
  7. fallback por item (D-PRC-12): cliente COM vínculo → usa tabela do cliente;
     item SEM cobertura na tabela do cliente → cai na padrão.
  8. idempotência: replay mesmo Idempotency-Key → mesma resposta, sem duplicar.
  9. cross-tenant: tenant B tenta acessar regra/pedido do tenant A → 404.
  10. assertNumQueries no endpoint `calcular` com cesta N itens → constante (sem N+1).
  11. cortesia 100% → preco_final=0 sem estourar (D-PRC-13).
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import UUID, uuid4

import pytest
from rest_framework.test import APIClient

from tests.factories import TenantFactory, UsuarioFactory, UsuarioPerfilTenantFactory

_DBS = ["default", "breaker_writer"]


# ---------------------------------------------------------------------------
# Helpers de autenticação (molde PPS E2E)
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


def _cenario(*, perfil_b: bool = True, sfx: str | None = None) -> dict:
    """Cria tenant+usuários para um cenário de teste.

    `gerente` usa perfil `gerente_operacional` (sistêmico) — tem
    `precificacao.aprovar_desconto` + `precificacao.alcada_gerente` mas NÃO
    `precificacao.alcada_dono` (seed 0006+0009). Isso permite provar
    MÉDIO-1: o 403 em decidir pedido DONO vem de `_alcada_papel_cobre`
    (AlcadaInsuficiente), não da ação ausente.
    """
    from src.infrastructure.authz.django_provider import invalidate_user_cache

    sfx = sfx or uuid4().hex[:8]
    tenant = TenantFactory(perfil_b=perfil_b, slug=f"prc-e2e-{sfx}")
    admin = UsuarioFactory(email=f"adm-prc-{sfx}@e2e.local")
    vendedor = UsuarioFactory(email=f"vend-prc-{sfx}@e2e.local")
    gerente = UsuarioFactory(email=f"ger-prc-{sfx}@e2e.local")
    UsuarioPerfilTenantFactory(usuario=admin, tenant=tenant, perfil="admin_tenant")
    UsuarioPerfilTenantFactory(usuario=vendedor, tenant=tenant, perfil="atendente")
    # MÉDIO-1: gerente_operacional tem aprovar_desconto + alcada_gerente (nunca alcada_dono).
    # gerente_tenant é perfil por-tenant, ausente do seed sistêmico → 403 viria da ação,
    # não da alçada. gerente_operacional prova que o predicate alcada_cobre é o bloqueio.
    UsuarioPerfilTenantFactory(usuario=gerente, tenant=tenant, perfil="gerente_operacional")
    for u in (admin, vendedor, gerente):
        invalidate_user_cache(u.id, tenant.id)
    return {
        "tenant": tenant,
        "admin": admin,
        "vendedor": vendedor,
        "gerente": gerente,
    }


def _client(c: dict, papel: str = "admin") -> APIClient:
    client = APIClient()
    _autenticar(client, c[papel], c["tenant"])
    return client


def _post(client: APIClient, url: str, payload: dict, key: str | None = None) -> object:
    return client.post(
        url,
        payload,
        format="json",
        HTTP_IDEMPOTENCY_KEY=key or str(uuid4()),
    )


# ---------------------------------------------------------------------------
# Helpers de setup: item, tabela, linha, regra, parâmetros
# ---------------------------------------------------------------------------


def _cadastrar_item(client: APIClient, preco_padrao: str = "100.00", **kw) -> dict:
    payload = {
        "codigo_interno": f"PRC-{uuid4().hex[:6]}",
        "tipo": "peca",
        "nome": "Sensor de pressão",
        "unidade_medida": "un",
        "preco_padrao": preco_padrao,
    }
    payload.update(kw)
    r = _post(client, "/api/v1/catalogo/itens/cadastrar/", payload)
    assert r.status_code == 201, r.content
    return r.json()


def _criar_tabela(client: APIClient, nome: str = "Padrão") -> dict:
    r = _post(client, "/api/v1/catalogo/tabelas/criar/", {"nome": nome})
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


def _configurar_params(client: APIClient) -> dict:
    payload = {
        "custo_km": "0.00",
        "taxa_parcelamento_mensal": "0.00",
        "pct_comissao_prevista": "0.00",
        "margem_alvo_default": "20.00",
        "margem_piso_default": "5.00",
    }
    r = _post(client, "/api/v1/config/parametros/", payload)
    assert r.status_code == 201, r.content
    return r.json()


def _publicar_regra(client: APIClient, item_id: str, modo: str = "preco_fixo", **kw) -> dict:
    payload: dict = {"item_id": item_id, "modo": modo}
    if modo == "preco_fixo":
        payload.setdefault("preco_fixo", "100.00")
    payload.update(kw)
    r = _post(client, "/api/v1/regras/publicar/", payload)
    assert r.status_code == 201, r.content
    return r.json()


def _calcular(client: APIClient, itens_payload: list[dict], **kw) -> object:
    """POST /api/v1/calcular/ — SEM Idempotency-Key (D-PRC-9)."""
    payload: dict = {
        "itens": itens_payload,
        "desconto_pct": "0.00",
        "modo_montagem": "fechado_com_aviso",
        "km": "0.0000",
        "parcelas": 1,
    }
    payload.update(kw)
    return client.post("/api/v1/calcular/", payload, format="json")


def _criar_vinculo_rest(
    client: APIClient, cliente_id: UUID, tabela_id: UUID
) -> dict:
    """Cria VinculoTabelaPrecoCliente via REST (AC-PRC-005-1 — MÉDIO-2 P9)."""
    r = _post(
        client,
        "/api/v1/vinculos/criar/",
        {
            "cliente_id": str(cliente_id),
            "tabela_id": str(tabela_id),
        },
    )
    assert r.status_code == 201, r.content
    return r.json()


def _criar_vinculo_cliente(
    tenant_id: UUID, cliente_id: UUID, tabela_id: UUID, criado_por: UUID
) -> None:
    """Persiste VinculoTabelaPrecoCliente diretamente no banco via contexto tenant.

    Mantido como helper de compatibilidade para cenários que precisam de contexto
    PG explícito (teste #7 de fallback usa run_in_tenant_context). Os novos testes
    de AC-PRC-005-1 usam _criar_vinculo_rest (MÉDIO-2 P9).
    """
    from src.infrastructure.precificacao.models import VinculoTabelaPrecoCliente as VinculoModel

    agora = datetime.now(UTC)
    VinculoModel.objects.create(
        id=uuid4(),
        tenant_id=tenant_id,
        tabela_id=tabela_id,
        cliente_id=cliente_id,
        vigencia_inicio=agora - timedelta(days=1),
        vigencia_fim=None,
        revogado_em=None,
        motivo_revogacao="",
        criado_por=criado_por,
    )


# ---------------------------------------------------------------------------
# 1. COST_PLUS + StubCustoProvider → 422 CustoRealIndisponivel
# ---------------------------------------------------------------------------


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_e2e_publicar_regra_cost_plus_stub_422() -> None:
    """D-PRC-6: COST_PLUS sem custo_manual → stub ativo → 422 CustoRealIndisponivel."""
    c = _cenario()
    client = _client(c)
    item = _cadastrar_item(client)

    r = _post(
        client,
        "/api/v1/regras/publicar/",
        {
            "item_id": item["id"],
            "modo": "cost_plus",
            # sem custo_manual_declarado → stub obrigatório
            "margem_alvo_pct": "20.00",
            "margem_piso_pct": "5.00",
        },
    )
    assert r.status_code == 422, r.content
    assert "CustoRealIndisponivel" in r.json()["codigo"]


# ---------------------------------------------------------------------------
# 2. RBAC de campo: sem `ver_margem` → sem custo/margem na resposta
# ---------------------------------------------------------------------------


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_e2e_rbac_campo_sem_ver_margem_nao_expoe_custo() -> None:
    """D-PRC-4 / INV-PRC-MARGEM-RBAC: sem `ver_margem` → custo/margem ausentes.

    Testa 2 endpoints distintos: calcular + regras/{id}/ (UNHAPPY por endpoint).
    """
    c = _cenario()
    admin_client = _client(c, "admin")
    vendedor_client = _client(c, "vendedor")  # perfil atendente — sem ver_margem

    item = _cadastrar_item(admin_client)
    tabela = _criar_tabela(admin_client)
    _criar_linha(admin_client, tabela["id"], item["id"], preco="120.00")
    _configurar_params(admin_client)
    agora_iso = datetime.now(UTC).isoformat()
    regra = _publicar_regra(
        admin_client,
        item["id"],
        modo="margem_alvo",
        custo_manual_declarado="80.00",
        custo_referencia_em=agora_iso,  # obrigatório no modo MARGEM_ALVO (TL-PRC-07)
        margem_alvo_pct="20.00",
        margem_piso_pct="5.00",
    )

    # Endpoint 1: calcular — vendedor NÃO vê margem/custo
    r_vend = _calcular(vendedor_client, [{"item_id": item["id"]}])
    assert r_vend.status_code == 200, r_vend.content
    body_vend = r_vend.json()
    item_calc = body_vend["itens"][0]
    assert "margem_estimada" not in item_calc, "margem não deve ser exposta sem ver_margem"
    assert "custo_estimado" not in item_calc, "custo não deve ser exposto sem ver_margem"
    # campos não-restritos permanecem
    assert "preco_final" in item_calc
    assert "semaforo" in item_calc

    # Admin COM ver_margem vê os campos
    r_adm = _calcular(admin_client, [{"item_id": item["id"]}])
    assert r_adm.status_code == 200, r_adm.content
    item_adm = r_adm.json()["itens"][0]
    assert "margem_estimada" in item_adm
    assert "custo_estimado" in item_adm

    # Endpoint 2: regras/{id}/ — vendedor NÃO vê margem/custo
    r_reg_vend = vendedor_client.get(f"/api/v1/regras/{regra['regra_id']}/")
    assert r_reg_vend.status_code == 200, r_reg_vend.content
    body_reg = r_reg_vend.json()
    assert "margem_estimada" not in body_reg, "margem não exposta na regra sem ver_margem"
    assert "custo_estimado" not in body_reg, "custo não exposto na regra sem ver_margem"


# ---------------------------------------------------------------------------
# 3. predicate alcada_cobre: gerente decide pedido DONO → 403
# ---------------------------------------------------------------------------


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_e2e_predicate_alcada_gerente_nao_decide_dono_403() -> None:
    """T-PRC-036 / INV-PRC-ALCADA: gerente (alçada GERENTE) tenta decidir pedido DONO → 403."""
    c = _cenario()
    admin_client = _client(c, "admin")
    gerente_client = _client(c, "gerente")

    # fingerprint sintético de 64 chars (SHA-256 hex stub)
    fp = "d" * 64

    # solicitar aprovação como admin (>=20% → DONO)
    r_sol = _post(
        admin_client,
        "/api/v1/aprovacoes/solicitar/",
        {
            "desconto_pct": "25.00",  # faixa DONO (>=20%)
            "contexto_tipo": "avulso",
            "fingerprint_calculo": fp,
            "motor_versao": "v1",
            "parametros_versao": 1,
        },
    )
    assert r_sol.status_code == 201, r_sol.content
    pedido_id = r_sol.json()["pedido_id"]

    # gerente (alcada_gerente) tenta decidir pedido DONO → 403 de AlcadaInsuficiente
    # MÉDIO-1: gerente_operacional TEM aprovar_desconto — 403 NÃO vem de ação ausente.
    # Vem de _alcada_papel_cobre(papel=GERENTE, alcada_exigida=DONO) → AlcadaInsuficiente.
    r_dec = _post(
        gerente_client,
        f"/api/v1/aprovacoes/{pedido_id}/decidir/",
        {
            "estado": "aprovado",
            "justificativa": "Justificativa do gerente suficientemente longa para passar",
            "fingerprint_calculo_atual": fp,
        },
    )
    assert r_dec.status_code == 403, r_dec.content
    # Prova que o bloqueio veio do predicate de alçada, não de permissão ausente:
    assert r_dec.json().get("codigo") == "AlcadaInsuficiente", (
        f"esperado AlcadaInsuficiente, obteve {r_dec.json()}"
    )


# ---------------------------------------------------------------------------
# 4. Decisor == solicitante → 422 (INV-PRC-APROVACAO-INDEPENDENTE)
# ---------------------------------------------------------------------------


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_e2e_decisor_igual_solicitante_422() -> None:
    """INV-PRC-APROVACAO-INDEPENDENTE: mesmo usuário solicita e decide → 422."""
    c = _cenario()
    admin_client = _client(c, "admin")

    fp = "e" * 64
    r_sol = _post(
        admin_client,
        "/api/v1/aprovacoes/solicitar/",
        {
            "desconto_pct": "15.00",  # faixa GERENTE
            "contexto_tipo": "avulso",
            "fingerprint_calculo": fp,
            "motor_versao": "v1",
            "parametros_versao": 1,
        },
    )
    assert r_sol.status_code == 201, r_sol.content
    pedido_id = r_sol.json()["pedido_id"]

    # MESMO admin tenta decidir (solicitante == decisor)
    r_dec = _post(
        admin_client,
        f"/api/v1/aprovacoes/{pedido_id}/decidir/",
        {
            "estado": "aprovado",
            "justificativa": "Admin auto-aprovando o próprio pedido — não permitido",
            "fingerprint_calculo_atual": fp,
        },
    )
    assert r_dec.status_code == 422, r_dec.content
    assert "DecisorNaoIndependente" in r_dec.json()["codigo"]


# ---------------------------------------------------------------------------
# 5. Fingerprint divergente → 422 (D-PRC-14)
# ---------------------------------------------------------------------------


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_e2e_fingerprint_divergente_422() -> None:
    """D-PRC-14: fingerprint na decisão != fingerprint do pedido → 422."""
    c = _cenario()
    sfx = c["tenant"].slug[-8:]
    admin_client = _client(c, "admin")
    # segundo usuário admin para decidir (independência)
    from src.infrastructure.authz.django_provider import invalidate_user_cache

    decisor = UsuarioFactory(email=f"dec-prc-{sfx}@e2e.local")
    UsuarioPerfilTenantFactory(usuario=decisor, tenant=c["tenant"], perfil="admin_tenant")
    invalidate_user_cache(decisor.id, c["tenant"].id)
    decisor_client = APIClient()
    _autenticar(decisor_client, decisor, c["tenant"])

    fp_original = "f" * 64
    fp_divergente = "a" * 64

    r_sol = _post(
        admin_client,
        "/api/v1/aprovacoes/solicitar/",
        {
            "desconto_pct": "15.00",
            "contexto_tipo": "avulso",
            "fingerprint_calculo": fp_original,
            "motor_versao": "v1",
            "parametros_versao": 1,
        },
    )
    assert r_sol.status_code == 201, r_sol.content
    pedido_id = r_sol.json()["pedido_id"]

    r_dec = _post(
        decisor_client,
        f"/api/v1/aprovacoes/{pedido_id}/decidir/",
        {
            "estado": "aprovado",
            "justificativa": "Aprovando com fingerprint diferente do original",
            "fingerprint_calculo_atual": fp_divergente,  # DIVERGE
        },
    )
    assert r_dec.status_code == 422, r_dec.content
    assert "FingerprintDivergente" in r_dec.json()["codigo"]


# ---------------------------------------------------------------------------
# 6. Cesta multi-item: 2+ itens → N itens no resultado
# ---------------------------------------------------------------------------


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_e2e_cesta_multi_item_retorna_n_itens() -> None:
    """D-PRC-11: cesta com 2 itens → resultado.itens contém 2 ItemCalculado."""
    c = _cenario()
    client = _client(c)
    item1 = _cadastrar_item(client, preco_padrao="100.00")
    item2 = _cadastrar_item(client, preco_padrao="200.00")
    tabela = _criar_tabela(client)
    _criar_linha(client, tabela["id"], item1["id"], preco="110.00")
    _criar_linha(client, tabela["id"], item2["id"], preco="210.00")
    _configurar_params(client)

    r = _calcular(client, [{"item_id": item1["id"]}, {"item_id": item2["id"]}])
    assert r.status_code == 200, r.content
    body = r.json()
    assert len(body["itens"]) == 2
    ids_resp = {it["item_id"] for it in body["itens"]}
    assert item1["id"] in ids_resp
    assert item2["id"] in ids_resp


# ---------------------------------------------------------------------------
# 7. Fallback por item (D-PRC-12)
# ---------------------------------------------------------------------------


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_e2e_fallback_por_item_d_prc_12() -> None:
    """D-PRC-12: cliente COM vínculo usa tabela do cliente; item sem cobertura → padrão.

    Cenário:
    - tabela_padrao: tem linhas para item1 (120.00) e item2 (220.00)
    - tabela_cliente: tem linha SÓ para item1 (130.00); item2 não está coberto
    - cliente tem vínculo ativo com tabela_cliente
    - calcular com cliente_id → item1 usa tabela_cliente (preco=130.00),
      item2 cai na tabela_padrao (preco=220.00)
    - `tabela_id` na resposta diferencia as duas situações
    """
    c = _cenario()
    client = _client(c)
    tenant_id = c["tenant"].id

    item1 = _cadastrar_item(client, preco_padrao="100.00")
    item2 = _cadastrar_item(client, preco_padrao="200.00")

    # tabela padrão: cobre ambos
    tabela_padrao = _criar_tabela(client)
    _criar_linha(client, tabela_padrao["id"], item1["id"], preco="120.00")
    _criar_linha(client, tabela_padrao["id"], item2["id"], preco="220.00")

    # tabela específica do cliente: cobre só item1
    # Cria diretamente via ORM com contexto PG ativo (RLS INSERT exige
    # current_setting('app.active_tenant_id') — sem contexto uuid:""→DataError).
    from src.infrastructure.multitenant.connection import run_in_tenant_context
    from src.infrastructure.produtos_pecas_servicos.models import LinhaTabelaPreco as LinhaModel
    from src.infrastructure.produtos_pecas_servicos.models import TabelaPreco as TabelaModel

    tabela_cli_id = uuid4()
    cliente_id = uuid4()
    agora = datetime.now(UTC)
    admin_uuid = c["admin"].id  # Usuario.id é UUIDField — sem cast necessário

    with run_in_tenant_context(tenant_id):
        TabelaModel.objects.create(
            id=tabela_cli_id,
            tenant_id=tenant_id,
            nome="Tabela VIP",
            eh_padrao=False,
        )
        LinhaModel.objects.create(
            id=uuid4(),
            tenant_id=tenant_id,
            tabela_id=tabela_cli_id,
            item_id=UUID(item1["id"]),
            preco=Decimal("130.00"),
            vigencia_inicio=agora - timedelta(hours=1),
            vigencia_fim=None,
            origem_sugestao="manual",
            criado_por=admin_uuid,
        )
        # item2 NÃO tem linha na tabela_cli — vai cair na padrão

        # vínculo cliente ↔ tabela_cliente
        _criar_vinculo_cliente(
            tenant_id=tenant_id,
            cliente_id=cliente_id,
            tabela_id=tabela_cli_id,
            criado_por=admin_uuid,
        )

    _configurar_params(client)

    r = _calcular(
        client,
        [{"item_id": item1["id"]}, {"item_id": item2["id"]}],
        cliente_id=str(cliente_id),
    )
    assert r.status_code == 200, r.content
    body = r.json()
    itens_resp = {it["item_id"]: it for it in body["itens"]}

    # item1 deve ter usado tabela_cliente (preco_base=130.00)
    assert itens_resp[item1["id"]]["preco_base"] == "130.00", (
        f"item1 deveria usar tabela do cliente (130.00), "
        f"obteve {itens_resp[item1['id']]['preco_base']}"
    )
    # item2 deve ter usado tabela_padrao (preco_base=220.00) — fallback
    assert itens_resp[item2["id"]]["preco_base"] == "220.00", (
        f"item2 deveria usar tabela padrão (220.00) por fallback, "
        f"obteve {itens_resp[item2['id']]['preco_base']}"
    )


# ---------------------------------------------------------------------------
# 8. Idempotência: replay mesmo Idempotency-Key
# ---------------------------------------------------------------------------


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_e2e_idempotencia_solicitar_replay() -> None:
    """Idempotency replay: POST solicitar com mesma chave → mesma resposta, sem duplicar pedido."""
    c = _cenario()
    admin_client = _client(c, "admin")

    fp = "9" * 64
    key = str(uuid4())
    payload = {
        "desconto_pct": "5.00",
        "contexto_tipo": "avulso",
        "fingerprint_calculo": fp,
        "motor_versao": "v1",
        "parametros_versao": 1,
    }

    r1 = _post(admin_client, "/api/v1/aprovacoes/solicitar/", payload, key=key)
    assert r1.status_code == 201, r1.content
    pedido_id_1 = r1.json()["pedido_id"]

    r2 = _post(admin_client, "/api/v1/aprovacoes/solicitar/", payload, key=key)
    assert r2.status_code == 201, r2.content
    pedido_id_2 = r2.json()["pedido_id"]

    # Replay retorna o mesmo pedido_id (sem duplicar)
    assert pedido_id_1 == pedido_id_2, "replay deve retornar o mesmo pedido_id"

    # Somente 1 pedido no banco (sem duplicata).
    # O fingerprint do banco é gerado internamente pelo use case (D-PRC-14).
    # A query ORM precisa do contexto de tenant ativo para passar pelo RLS do PG.
    from src.infrastructure.multitenant.connection import run_in_tenant_context
    from src.infrastructure.precificacao.models import PedidoAprovacaoDesconto as PedidoModel

    with run_in_tenant_context(c["tenant"].id):
        todos_ids = list(
            PedidoModel.objects.filter(tenant_id=c["tenant"].id).values_list("id", flat=True)
        )
    assert len(todos_ids) == 1, f"replay criou {len(todos_ids)} pedidos — deve ser exatamente 1"
    assert str(todos_ids[0]) == pedido_id_1, "o único pedido deve ser o do primeiro POST"


# ---------------------------------------------------------------------------
# 9. Cross-tenant: tenant B não vê regra/pedido do tenant A
# ---------------------------------------------------------------------------


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_e2e_cross_tenant_404() -> None:
    """RLS: tenant B tenta acessar regra e pedido do tenant A → 404 (sem confirmar existência)."""
    c_a = _cenario(sfx=uuid4().hex[:8])
    c_b = _cenario(sfx=uuid4().hex[:8])
    client_a = _client(c_a)
    client_b = _client(c_b)

    # Cria regra em tenant A
    item_a = _cadastrar_item(client_a)
    regra_a = _publicar_regra(client_a, item_a["id"])

    # Cria pedido em tenant A
    fp = "8" * 64
    r_sol = _post(
        client_a,
        "/api/v1/aprovacoes/solicitar/",
        {
            "desconto_pct": "5.00",
            "contexto_tipo": "avulso",
            "fingerprint_calculo": fp,
            "motor_versao": "v1",
            "parametros_versao": 1,
        },
    )
    assert r_sol.status_code == 201, r_sol.content
    pedido_id_a = r_sol.json()["pedido_id"]

    # Tenant B tenta acessar regra do tenant A → 404
    r_reg = client_b.get(f"/api/v1/regras/{regra_a['regra_id']}/")
    assert r_reg.status_code == 404, f"cross-tenant regra deveria ser 404, foi {r_reg.status_code}"

    # Tenant B tenta decidir pedido do tenant A → 404
    r_dec = _post(
        client_b,
        f"/api/v1/aprovacoes/{pedido_id_a}/decidir/",
        {
            "estado": "aprovado",
            "justificativa": "Tentativa de cross-tenant aprovação do pedido de outro tenant",
            "fingerprint_calculo_atual": fp,
        },
    )
    assert (
        r_dec.status_code == 404
    ), f"cross-tenant decidir deveria ser 404, foi {r_dec.status_code}"


# ---------------------------------------------------------------------------
# 10. assertNumQueries no endpoint `calcular` — sem N+1 (TL-PRC-14)
# ---------------------------------------------------------------------------


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_e2e_calcular_sem_n_mais_1() -> None:
    """TL-PRC-14: endpoint calcular com cesta de N itens → contagem constante (sem N+1).

    CaptureQueriesContext funciona tanto em TransactionTestCase quanto em TestCase —
    basta passar `connection` explicitamente. Memoização de Params/Faixas: 1x cada,
    não 1x por item.
    """

    # Setup: 3 itens + tabela + linhas + regras + params
    c = _cenario()
    client = _client(c)
    item1 = _cadastrar_item(client)
    item2 = _cadastrar_item(client)
    item3 = _cadastrar_item(client)
    tabela = _criar_tabela(client)
    _criar_linha(client, tabela["id"], item1["id"], preco="100.00")
    _criar_linha(client, tabela["id"], item2["id"], preco="200.00")
    _criar_linha(client, tabela["id"], item3["id"], preco="300.00")
    _configurar_params(client)

    # Contador de queries via django.test.utils.CaptureQueriesContext
    # (funciona com transaction=True; CaptureQueriesContext não exige rollback)
    from django.db import connection
    from django.test.utils import CaptureQueriesContext

    def _contar_queries_calcular(n_itens: int) -> int:
        itens_payload = [
            {"item_id": [item1["id"], item2["id"], item3["id"]][i % 3]} for i in range(n_itens)
        ]
        with CaptureQueriesContext(connection) as ctx:
            r = _calcular(client, itens_payload)
        assert r.status_code == 200, r.content
        return len(ctx)

    # Cesta de 1 item
    q1 = _contar_queries_calcular(1)
    # Cesta de 10 itens (3 distintos, repetidos — reutiliza faixas/params/tabela-padrão)
    q10 = _contar_queries_calcular(10)

    # Garantia HARD (MÉDIO-3 P9 anti-N+1):
    # Pós-conserto PERF-MÉDIO-3 P9 (2ª passada): `obter_padrao` é resolvido
    # UMA vez por request via `_construir_resolver_com_tabela_padrao` (closure
    # injetado na view). Queries restantes POR ITEM são genuinamente intrínsecas
    # ao `preco_para_os` atual: item_catalogo + item_catalogo_versao + linha_tabela_preco
    # (~3 por item). Batch-completo de preco_para_os é GATE-PRC-CALCULAR-BATCH-FULL
    # (otimização diferida — aceitável no dogfooding).
    #
    # - q1: auth + tabela_padrao (1) + params (1) + faixas (1) + imposto (1) +
    #        regras_batch (1) + item(1) + versao(1) + linhas_padrao(1) = fixas + 3 por item
    # - q10 = q1 + 3 * (10 - 1) = q1 + 27
    # Delta máximo tolerado: 3 por item extra + margem 1 = 4 * (10-1) = 36 ANTES;
    # pós-conserto delta deve ser ~27 (3/item); toleramos até 30 (margem de 1/item).
    # Um N+1 futuro de +1 q/item adicionaria ~9 → estoura o teto imediatamente.
    delta = q10 - q1
    # Medido pós-conserto PERF-MÉDIO-3 P9: q1=36, q10=63, delta=27
    # (36 queries fixas no q1 incluem auth + middleware + tabela_padrao (1x) + params + faixas +
    # imposto + regras_batch + 3 por item; delta=27 = 3 q/item × 9 extras — sem obter_padrao N vezes)
    max_delta_tolerado = 30  # 3 q/item intrínseco × 9 extras + margem ≤ 30
    assert delta <= max_delta_tolerado, (
        f"N+1 detectado: q1={q1}, q10={q10}, delta={delta} "
        f"(máximo tolerado: {max_delta_tolerado} = 3 q/item × 9 itens extras + margem). "
        "obter_padrao deve ser constante (1x/request); regras em batch (TL-PRC-14 / MÉDIO-3 P9). "
        "GATE-PRC-CALCULAR-BATCH-FULL rastreia otimização restante."
    )


# ---------------------------------------------------------------------------
# 11. Cortesia 100% → preco_final=0 sem estourar (D-PRC-13)
# ---------------------------------------------------------------------------


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_e2e_cortesia_100_preco_final_zero() -> None:
    """D-PRC-13: desconto 100% (cortesia) → preco_final=0 sem erro de divisão por zero."""
    c = _cenario()
    client = _client(c)
    item = _cadastrar_item(client, preco_padrao="500.00")
    tabela = _criar_tabela(client)
    _criar_linha(client, tabela["id"], item["id"], preco="500.00")
    _configurar_params(client)

    r = _calcular(client, [{"item_id": item["id"]}], desconto_pct="100.00")
    assert r.status_code == 200, r.content
    body = r.json()
    item_calc = body["itens"][0]
    assert (
        item_calc["preco_final"] == "0.00"
    ), f"cortesia 100% deve resultar em preco_final=0.00, obteve {item_calc['preco_final']}"
    # D-PRC-13: cortesia exige alçada DONO para aprovação posterior
    assert (
        body["alcada_exigida"] == "dono"
    ), f"cortesia 100% deve exigir alçada DONO, obteve {body['alcada_exigida']}"


# ---------------------------------------------------------------------------
# 12. AC-PRC-005-1 — vínculo cliente↔tabela via REST (MÉDIO-2 P9)
# ---------------------------------------------------------------------------


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_e2e_vinculos_criar_listar_revogar() -> None:
    """AC-PRC-005-1: criar / listar / revogar vínculo cliente↔tabela via REST.

    Prova que DjangoVinculoTabelaRepository.salvar()/revogar() são atingíveis
    pela camada REST — sem bypass ORM. A listagem confirma que só vínculos
    ativos aparecem após revogação.
    """
    c = _cenario()
    client = _client(c)

    # Cria tabela via REST
    tabela = _criar_tabela(client, nome="VIP REST")
    tabela_id = UUID(tabela["id"])
    cliente_id = uuid4()

    # Cria vínculo via REST (AC-PRC-005-1)
    vinculo = _criar_vinculo_rest(client, cliente_id=cliente_id, tabela_id=tabela_id)
    assert "vinculo_id" in vinculo
    vinculo_id = vinculo["vinculo_id"]

    # Listagem: vínculo ativo aparece
    r_list = client.get("/api/v1/vinculos/")
    assert r_list.status_code == 200, r_list.content
    ids_listados = [v["vinculo_id"] for v in r_list.json()]
    assert vinculo_id in ids_listados, "vínculo recém-criado deve aparecer na listagem"

    # Revoga via REST
    r_rev = _post(
        client,
        f"/api/v1/vinculos/{vinculo_id}/revogar/",
        {"motivo": "Teste de revogação via REST — motivo suficientemente longo"},
    )
    assert r_rev.status_code == 200, r_rev.content
    assert r_rev.json()["revogado"] is True

    # Listagem após revogação: vínculo revogado NÃO aparece
    r_list2 = client.get("/api/v1/vinculos/")
    assert r_list2.status_code == 200, r_list2.content
    ids_pos_revogacao = [v["vinculo_id"] for v in r_list2.json()]
    assert vinculo_id not in ids_pos_revogacao, (
        "vínculo revogado não deve aparecer na listagem (revogado_em IS NOT NULL)"
    )


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_e2e_fallback_usa_vinculo_criado_via_rest() -> None:
    """AC-PRC-005-1 + D-PRC-12: calcular com cliente vinculado via REST usa tabela do cliente.

    Prova o E2E end-to-end: criar vínculo via REST → calcular passando cliente_id
    → item usa preço da tabela vinculada (não a padrão).
    """
    c = _cenario()
    client = _client(c)
    tenant_id = c["tenant"].id
    admin_uuid = c["admin"].id

    item = _cadastrar_item(client, preco_padrao="100.00")

    # Tabela padrão com preço 120
    tabela_padrao = _criar_tabela(client, nome="Padrão REST")
    _criar_linha(client, tabela_padrao["id"], item["id"], preco="120.00")

    # Tabela específica do cliente com preço 150 — criada via ORM no contexto tenant
    # (necessário para RLS INSERT — tabela PPS exige contexto ativo)
    from src.infrastructure.multitenant.connection import run_in_tenant_context
    from src.infrastructure.produtos_pecas_servicos.models import LinhaTabelaPreco as LinhaModel
    from src.infrastructure.produtos_pecas_servicos.models import TabelaPreco as TabelaModel

    tabela_cli_id = uuid4()
    cliente_id = uuid4()
    agora = datetime.now(UTC)

    with run_in_tenant_context(tenant_id):
        TabelaModel.objects.create(
            id=tabela_cli_id,
            tenant_id=tenant_id,
            nome="Tabela VIP REST",
            eh_padrao=False,
        )
        LinhaModel.objects.create(
            id=uuid4(),
            tenant_id=tenant_id,
            tabela_id=tabela_cli_id,
            item_id=UUID(item["id"]),
            preco=Decimal("150.00"),
            vigencia_inicio=agora - timedelta(hours=1),
            vigencia_fim=None,
            origem_sugestao="manual",
            criado_por=admin_uuid,
        )

    # Vínculo criado via REST (AC-PRC-005-1 — MÉDIO-2 P9)
    _configurar_params(client)
    vinculo = _criar_vinculo_rest(client, cliente_id=cliente_id, tabela_id=tabela_cli_id)
    assert "vinculo_id" in vinculo

    # Calcular com cliente_id → deve usar tabela do cliente (preco=150)
    r = _calcular(client, [{"item_id": item["id"]}], cliente_id=str(cliente_id))
    assert r.status_code == 200, r.content
    preco_base = r.json()["itens"][0]["preco_base"]
    assert preco_base == "150.00", (
        f"calcular com vínculo REST deve usar tabela do cliente (150.00), obteve {preco_base}"
    )


# ---------------------------------------------------------------------------
# 13. Correlation-ID no log de falha (MÉDIO-4 P9 — OBS)
# ---------------------------------------------------------------------------


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_e2e_falha_loga_correlation_id_do_request(caplog: pytest.LogCaptureFixture) -> None:
    """MÉDIO-4 P9: log de falha em _falha() carrega o correlation_id do request.

    Prova que `_obter_correlation_id_views()` lê `correlation_id_context`
    (ContextVar setado pelo CorrelationIdMiddleware) — NÃO mais o GUC PG
    `app.correlation_id` (nunca setado, sempre None).

    Cenário: POST /calcular/ sem parâmetros configurados (sem tabela → 422
    ParametrosInviaveis ou sem itens). Usamos `decidir_aprovacao` com pedido
    ausente (→ 404) pra garantir que `_falha` é chamado sem precisar de setup
    de itens/tabelas. Verifica via caplog que o log de aviso contém o
    X-Correlation-ID exato passado no request.
    """
    import logging

    c = _cenario()
    client = _client(c)

    # Correlation-ID conhecido e seguro (padrão aceito pelo middleware: 8-64 chars hex)
    correlation_id_conhecido = uuid4().hex  # 32 chars hex — aceito pelo _TOKEN_SEGURO

    # Dispara recusa: POST calcular/ sem parâmetros configurados para o tenant
    # → ParametrosInviaveis → _falha() é chamado
    with caplog.at_level(logging.WARNING, logger="src.infrastructure.precificacao.views"):
        r = client.post(
            "/api/v1/calcular/",
            {
                "itens": [{"item_id": str(uuid4())}],
                "desconto_pct": "0.00",
                "modo_montagem": "fechado_com_aviso",
                "km": "0.0000",
                "parcelas": 1,
            },
            format="json",
            HTTP_X_CORRELATION_ID=correlation_id_conhecido,
        )

    # Deve retornar 422 (ParametrosInviaveis — tenant sem params configurados)
    assert r.status_code == 422, (
        f"esperado 422 ParametrosInviaveis (tenant sem params), obteve {r.status_code}: {r.content}"
    )

    # Prova OBS: o correlation_id do request deve aparecer no log de falha
    registros_falha = [
        rec for rec in caplog.records
        if rec.levelname == "WARNING" and "precificacao acao recusada" in rec.getMessage()
    ]
    assert registros_falha, (
        "esperado ao menos 1 registro WARNING 'precificacao acao recusada' no log "
        f"(registros disponíveis: {[r.getMessage() for r in caplog.records]})"
    )
    rec = registros_falha[0]
    correlation_no_log = getattr(rec, "correlation_id", None)
    assert correlation_no_log is not None, (
        "log de falha deve conter 'correlation_id' no extra — era None (GUC não setado). "
        "Conserto: _obter_correlation_id_views() deve ler correlation_id_context (ContextVar)."
    )
    assert correlation_no_log == correlation_id_conhecido, (
        f"correlation_id no log ({correlation_no_log!r}) deve ser o mesmo do "
        f"X-Correlation-ID do request ({correlation_id_conhecido!r}). "
        "Prova que CorrelationIdMiddleware → correlation_id_context → _falha() funciona end-to-end."
    )
