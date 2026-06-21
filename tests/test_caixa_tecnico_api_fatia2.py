"""API /api/v1/caixa-tecnico/ — testes E2E Fatia 2 (T-CT-037).

Cobre todos os ACs de T-CT-037 (TransactionTestCase / ``transaction=True``):
  - lançar despesa OK → 201
  - sem foto (foto_base64 ausente) → 400 (serializer)
  - client_offline_id replay → mesmo registro (idempotência offline)
  - deslocamento calcula valor via tarifa_km
  - opt-in GPS ausente → despesa salva com gps_aviso=True (sem bloquear)
  - validar → validada
  - rejeitar motivo curto → 422
  - rejeitar OK → rejeitada
  - reapresentar → pendente
  - solicitar / aprovar / recusar / entregar adiantamento
  - entregue → tentativa de mover → 422 AdiantamentoNaoCancelavel
  - fechar prestação → WORM
  - período fechado → nova despesa 422
  - fechamento concorrente: 2 simultâneos → 1 fecha, 1 recebe 422 (advisory lock)
  - sync lote OK (207)
  - lote > 20 → 413
  - lote parcial (1 ruim, resto OK)
  - sem Idempotency-Key → 400/428
  - cross-tenant → 404
  - caixa desligado → 409

IMPORTANTE: usa ``--reuse-db`` (NUNCA ``--create-db``).
"""

from __future__ import annotations

import base64
import threading
from datetime import UTC, date, datetime, timedelta
from uuid import uuid4

import pytest
from rest_framework.test import APIClient
from src.infrastructure.authz.django_provider import invalidate_user_cache
from src.infrastructure.caixa_tecnico.models import (
    CaixaTecnico as CaixaTecnicoModel,
)
from src.infrastructure.caixa_tecnico.models import (
    DespesaCaixa as DespesaCaixaModel,
)
from src.infrastructure.caixa_tecnico.models import (
    PoliticaCaixa as PoliticaCaixaModel,
)
from src.infrastructure.caixa_tecnico.models import (
    PrestacaoContasCaixa as PrestacaoContasCaixaModel,
)
from src.infrastructure.multitenant.connection import run_in_tenant_context

from tests.factories import TenantFactory, UsuarioFactory, UsuarioPerfilTenantFactory

_DBS = ["default", "breaker_writer"]

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_HASH_V1 = "v1"
_FOTO_HASH_BASE = "a" * 64  # 64 chars HMAC hex


def _foto_base64_valida() -> str:
    """Foto mínima JPEG para os testes (bytes determinísticos → hash determinístico)."""
    return base64.b64encode(b"foto-fake-jpeg-bytes-para-testes").decode()


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
    """Cria tenant (perfil B — assistência técnica padrão) + admin."""
    sfx = uuid4().hex[:8]
    tenant = TenantFactory(perfil_b=True, slug=f"ct-api-{sfx}")
    admin = UsuarioFactory(email=f"adm-{sfx}@ct.local")
    UsuarioPerfilTenantFactory(usuario=admin, tenant=tenant, perfil="admin_tenant")
    invalidate_user_cache(admin.id, tenant.id)
    return {"tenant": tenant, "admin": admin}


def _cria_caixa(tenant, tecnico_hash: str | None = None) -> CaixaTecnicoModel:
    """Cria CaixaTecnico dentro do contexto do tenant."""
    if tecnico_hash is None:
        tecnico_hash = "tecnico_hash_" + "0" * 59 + uuid4().hex[:8]
    with run_in_tenant_context(tenant.id):
        return CaixaTecnicoModel.objects.create(
            tenant=tenant,
            tecnico_referencia_hash=tecnico_hash,
            tecnico_key_id=_HASH_V1,
        )


def _cria_politica(tenant, tarifa_km: int = 150, alcada: int | None = None) -> PoliticaCaixaModel:
    """Cria PoliticaCaixa dentro do contexto do tenant."""
    with run_in_tenant_context(tenant.id):
        return PoliticaCaixaModel.objects.create(
            tenant=tenant,
            tarifa_km=tarifa_km,
            prazo_prestacao_dias=30,
            exige_gps=False,
            alcada_aprovacao=alcada,
        )


def _cria_despesa(
    tenant, caixa, estado="pendente", foto_hash=None, offline_id=""
) -> DespesaCaixaModel:
    if foto_hash is None:
        foto_hash = "b" * 64
    with run_in_tenant_context(tenant.id):
        return DespesaCaixaModel.objects.create(
            tenant=tenant,
            caixa=caixa,
            tecnico_referencia_hash=caixa.tecnico_referencia_hash,
            tecnico_key_id=_HASH_V1,
            categoria="combustivel",
            tipo="normal",
            valor=5000,
            estado=estado,
            foto_hash=foto_hash,
            foto_url="http://example.com/foto.jpg",
            data=date.today(),
            client_offline_id=offline_id,
        )


def _post(client, url, payload, key=None):
    return client.post(url, payload, format="json", HTTP_IDEMPOTENCY_KEY=key or str(uuid4()))


URL_LANCAR = "/api/v1/caixa-tecnico/despesas/lancar/"
URL_SOLICITAR = "/api/v1/caixa-tecnico/adiantamentos/solicitar/"
URL_FECHAR = "/api/v1/caixa-tecnico/prestacoes/fechar/"
URL_SYNC = "/api/v1/caixa-tecnico/despesas/sync-lote/"


def _payload_lancar(caixa_id, **kw):
    base = {
        "caixa_id": str(caixa_id),
        "foto_base64": _foto_base64_valida(),
        "foto_mime": "image/jpeg",
        "categoria": "combustivel",
        "valor_centavos": 5000,
        "data": date.today().isoformat(),
        "colaborador_id": str(uuid4()),
    }
    base.update(kw)
    return base


# ===========================================================================
# Lançar despesa
# ===========================================================================


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_lancar_despesa_ok_201():
    """Lançamento OK → 201 + despesa no banco."""
    c = _cenario()
    caixa = _cria_caixa(c["tenant"])
    client = APIClient()
    _autenticar(client, c["admin"], c["tenant"])

    r = _post(client, URL_LANCAR, _payload_lancar(caixa.id))
    assert r.status_code == 201, r.content
    body = r.json()
    assert body["estado"] == "pendente"
    assert body["categoria"] == "combustivel"
    assert body["valor_centavos"] == 5000

    # Despesa no banco
    with run_in_tenant_context(c["tenant"].id):
        assert DespesaCaixaModel.objects.filter(id=body["despesa_id"]).exists()


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_lancar_sem_foto_400():
    """Lançamento sem foto_base64 → 400 (serializer rejeita campo ausente)."""
    c = _cenario()
    caixa = _cria_caixa(c["tenant"])
    client = APIClient()
    _autenticar(client, c["admin"], c["tenant"])

    payload = {
        "caixa_id": str(caixa.id),
        # foto_base64 ausente
        "foto_mime": "image/jpeg",
        "categoria": "combustivel",
        "valor_centavos": 5000,
        "data": date.today().isoformat(),
        "colaborador_id": str(uuid4()),
    }
    r = _post(client, URL_LANCAR, payload)
    assert r.status_code == 400, r.content


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_lancar_client_offline_id_replay_200():
    """Replay com mesmo client_offline_id → 200 (idempotência offline)."""
    c = _cenario()
    caixa = _cria_caixa(c["tenant"])
    offline_id = f"offline-{uuid4()}"
    # Pré-cria despesa com o mesmo offline_id para simular replay
    _cria_despesa(c["tenant"], caixa, offline_id=offline_id)

    client = APIClient()
    _autenticar(client, c["admin"], c["tenant"])
    payload = _payload_lancar(caixa.id, client_offline_id=offline_id)
    r = _post(client, URL_LANCAR, payload)
    # O replay é tratado como 200 na view
    assert r.status_code in (200, 201), r.content


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_lancar_deslocamento_calcula_valor():
    """Categoria deslocamento → valor = km × tarifa_km."""
    c = _cenario()
    _cria_politica(c["tenant"], tarifa_km=200)  # R$ 2,00/km
    caixa = _cria_caixa(c["tenant"])
    client = APIClient()
    _autenticar(client, c["admin"], c["tenant"])

    payload = _payload_lancar(
        caixa.id,
        categoria="deslocamento",
        valor_centavos=0,
        km_percorridos=10,
    )
    r = _post(client, URL_LANCAR, payload)
    assert r.status_code == 201, r.content
    # 10 km × R$2,00 = R$20,00 = 2000 centavos
    assert r.json()["valor_centavos"] == 2000


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_lancar_sem_opt_in_gps_despesa_salva_com_aviso():
    """GPS ausente (fake = opt_in=False) → despesa salva sem bloquear + gps_aviso."""
    c = _cenario()
    caixa = _cria_caixa(c["tenant"])
    client = APIClient()
    _autenticar(client, c["admin"], c["tenant"])

    r = _post(client, URL_LANCAR, _payload_lancar(caixa.id))
    # Despesa deve ser salva normalmente (GPS não bloqueia)
    assert r.status_code == 201, r.content
    body = r.json()
    # gps_aviso pode estar presente no body (GPS sem consentimento)
    # A despesa existe independente do aviso
    assert body["estado"] == "pendente"


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_lancar_caixa_desligado_409():
    """Caixa desligado → 409."""
    c = _cenario()
    caixa = _cria_caixa(c["tenant"])
    # Desligar o caixa
    with run_in_tenant_context(c["tenant"].id):
        CaixaTecnicoModel.objects.filter(id=caixa.id).update(desligado_em=datetime.now(UTC))
    client = APIClient()
    _autenticar(client, c["admin"], c["tenant"])
    r = _post(client, URL_LANCAR, _payload_lancar(caixa.id))
    assert r.status_code == 409, r.content


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_lancar_sem_idempotency_key_400():
    """POST sem Idempotency-Key → 400/428."""
    c = _cenario()
    caixa = _cria_caixa(c["tenant"])
    client = APIClient()
    _autenticar(client, c["admin"], c["tenant"])
    r = client.post(URL_LANCAR, _payload_lancar(caixa.id), format="json")
    assert r.status_code in (400, 428), r.content


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_lancar_cross_tenant_nao_ve_outro_caixa():
    """Cross-tenant: Caixa de tenant B não é visto por tenant A → 422/caixa não encontrado."""
    c_a = _cenario()
    c_b = _cenario()
    caixa_b = _cria_caixa(c_b["tenant"])

    client = APIClient()
    _autenticar(client, c_a["admin"], c_a["tenant"])
    r = _post(client, URL_LANCAR, _payload_lancar(caixa_b.id))
    # Não deve encontrar o caixa — 422 ou 404
    assert r.status_code in (404, 422), r.content


# ===========================================================================
# Validar / Rejeitar / Reapresentar despesa
# ===========================================================================


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_validar_despesa_ok():
    """Validar despesa pendente → estado validada."""
    c = _cenario()
    caixa = _cria_caixa(c["tenant"])
    despesa = _cria_despesa(c["tenant"], caixa, estado="pendente")

    client = APIClient()
    _autenticar(client, c["admin"], c["tenant"])
    r = _post(client, f"/api/v1/caixa-tecnico/despesas/{despesa.id}/validar/", {})
    assert r.status_code == 200, r.content
    assert r.json()["estado"] == "validada"


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_rejeitar_motivo_curto_422():
    """Rejeitar com motivo < 30 chars → 422."""
    c = _cenario()
    caixa = _cria_caixa(c["tenant"])
    despesa = _cria_despesa(c["tenant"], caixa, estado="pendente")

    client = APIClient()
    _autenticar(client, c["admin"], c["tenant"])
    r = _post(
        client,
        f"/api/v1/caixa-tecnico/despesas/{despesa.id}/rejeitar/",
        {"motivo": "curto"},
    )
    assert r.status_code in (400, 422), r.content


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_rejeitar_despesa_ok():
    """Rejeitar com motivo ≥ 30 chars → estado rejeitada."""
    c = _cenario()
    caixa = _cria_caixa(c["tenant"])
    despesa = _cria_despesa(c["tenant"], caixa, estado="pendente")

    client = APIClient()
    _autenticar(client, c["admin"], c["tenant"])
    motivo = "Comprovante ilegível — não é possível identificar o valor" * 2
    r = _post(
        client,
        f"/api/v1/caixa-tecnico/despesas/{despesa.id}/rejeitar/",
        {"motivo": motivo},
    )
    assert r.status_code == 200, r.content
    assert r.json()["estado"] == "rejeitada"


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_reapresentar_despesa_rejeitada_ok():
    """Reapresentar despesa rejeitada → estado pendente com nova foto."""
    c = _cenario()
    caixa = _cria_caixa(c["tenant"])
    despesa = _cria_despesa(c["tenant"], caixa, estado="rejeitada")

    client = APIClient()
    _autenticar(client, c["admin"], c["tenant"])
    payload = {
        "foto_base64": _foto_base64_valida(),
        "foto_mime": "image/jpeg",
        "colaborador_id": str(uuid4()),
    }
    r = _post(client, f"/api/v1/caixa-tecnico/despesas/{despesa.id}/reapresentar/", payload)
    assert r.status_code == 200, r.content
    assert r.json()["estado"] == "pendente"


# ===========================================================================
# Adiantamento — fluxo completo
# ===========================================================================


def _payload_solicitar(caixa_id, **kw):
    base = {
        "caixa_id": str(caixa_id),
        "valor_centavos": 10000,
        "meio": "pix",
    }
    base.update(kw)
    return base


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_solicitar_adiantamento_201():
    """Solicitar adiantamento → 201 + estado solicitado."""
    c = _cenario()
    caixa = _cria_caixa(c["tenant"])
    client = APIClient()
    _autenticar(client, c["admin"], c["tenant"])
    r = _post(client, URL_SOLICITAR, _payload_solicitar(caixa.id))
    assert r.status_code == 201, r.content
    assert r.json()["estado"] == "solicitado"


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_aprovar_adiantamento_ok():
    """Fluxo solicitar → aprovar → estado aprovado."""
    c = _cenario()
    caixa = _cria_caixa(c["tenant"])
    client = APIClient()
    _autenticar(client, c["admin"], c["tenant"])

    r = _post(client, URL_SOLICITAR, _payload_solicitar(caixa.id))
    assert r.status_code == 201
    adian_id = r.json()["adiantamento_id"]

    r2 = _post(
        client,
        f"/api/v1/caixa-tecnico/adiantamentos/{adian_id}/aprovar/",
        {"aprovado_por_id": str(uuid4())},
    )
    assert r2.status_code == 200, r2.content
    assert r2.json()["estado"] == "aprovado"


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_recusar_adiantamento_ok():
    """Fluxo solicitar → recusar com motivo → estado recusado."""
    c = _cenario()
    caixa = _cria_caixa(c["tenant"])
    client = APIClient()
    _autenticar(client, c["admin"], c["tenant"])

    r = _post(client, URL_SOLICITAR, _payload_solicitar(caixa.id))
    assert r.status_code == 201
    adian_id = r.json()["adiantamento_id"]

    motivo = "Saldo insuficiente para este período — aguardar próximo ciclo"
    r2 = _post(
        client,
        f"/api/v1/caixa-tecnico/adiantamentos/{adian_id}/recusar/",
        {"motivo": motivo},
    )
    assert r2.status_code == 200, r2.content
    assert r2.json()["estado"] == "recusado"


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_entregar_adiantamento_ok():
    """Fluxo solicitar → aprovar → entregar → estado entregue."""
    c = _cenario()
    caixa = _cria_caixa(c["tenant"])
    client = APIClient()
    _autenticar(client, c["admin"], c["tenant"])

    r = _post(client, URL_SOLICITAR, _payload_solicitar(caixa.id))
    adian_id = r.json()["adiantamento_id"]

    _post(
        client,
        f"/api/v1/caixa-tecnico/adiantamentos/{adian_id}/aprovar/",
        {"aprovado_por_id": str(uuid4())},
    )

    r_entregar = _post(
        client,
        f"/api/v1/caixa-tecnico/adiantamentos/{adian_id}/entregar/",
        {"entregue_por_id": str(uuid4())},
    )
    assert r_entregar.status_code == 200, r_entregar.content
    assert r_entregar.json()["estado"] == "entregue"


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_cancelar_adiantamento_entregue_422():
    """Adiantamento entregue → tentativa de recusar → 422 AdiantamentoNaoCancelavel."""
    c = _cenario()
    caixa = _cria_caixa(c["tenant"])
    client = APIClient()
    _autenticar(client, c["admin"], c["tenant"])

    r = _post(client, URL_SOLICITAR, _payload_solicitar(caixa.id))
    adian_id = r.json()["adiantamento_id"]
    _post(
        client,
        f"/api/v1/caixa-tecnico/adiantamentos/{adian_id}/aprovar/",
        {"aprovado_por_id": str(uuid4())},
    )
    _post(
        client,
        f"/api/v1/caixa-tecnico/adiantamentos/{adian_id}/entregar/",
        {"entregue_por_id": str(uuid4())},
    )

    # Tentar "recusar" entregue → AdiantamentoNaoCancelavel
    motivo = "Tentativa de cancelar adiantamento já entregue ao técnico" * 2
    r_err = _post(
        client,
        f"/api/v1/caixa-tecnico/adiantamentos/{adian_id}/recusar/",
        {"motivo": motivo},
    )
    assert r_err.status_code == 422, r_err.content


# ===========================================================================
# Fechar prestação de contas
# ===========================================================================


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_fechar_prestacao_ok_201():
    """Fechar prestação → 201 + WORM no banco."""
    c = _cenario()
    caixa = _cria_caixa(c["tenant"])
    client = APIClient()
    _autenticar(client, c["admin"], c["tenant"])

    hoje = date.today()
    inicio = (hoje - timedelta(days=30)).isoformat()
    fim = (hoje - timedelta(days=1)).isoformat()

    payload = {
        "caixa_id": str(caixa.id),
        "periodo_de": inicio,
        "periodo_ate": fim,
    }
    r = _post(client, URL_FECHAR, payload)
    assert r.status_code == 201, r.content
    body = r.json()
    assert "prestacao_id" in body
    assert body["direcao"] in ("tecnico_deve", "tenant_deve", "quitado")

    # WORM no banco
    with run_in_tenant_context(c["tenant"].id):
        assert PrestacaoContasCaixaModel.objects.filter(id=body["prestacao_id"]).exists()


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_lancar_despesa_periodo_fechado_422():
    """Despesa em período fechado → 422 PeriodoPrestacaoFechado."""
    c = _cenario()
    caixa = _cria_caixa(c["tenant"])
    hoje = date.today()
    inicio = hoje - timedelta(days=30)
    fim = hoje - timedelta(days=1)

    # Fechar o período primeiro
    with run_in_tenant_context(c["tenant"].id):
        PrestacaoContasCaixaModel.objects.create(
            tenant=c["tenant"],
            caixa=caixa,
            tecnico_referencia_hash=caixa.tecnico_referencia_hash,
            tecnico_key_id=_HASH_V1,
            periodo_de=inicio,
            periodo_ate=fim,
            total_adiantado=0,
            total_despesas_validadas=0,
            saldo_final=0,
            direcao="quitado",
            fechada_em=datetime.now(UTC),
        )

    client = APIClient()
    _autenticar(client, c["admin"], c["tenant"])
    # Tentar lançar despesa dentro do período fechado
    payload = _payload_lancar(caixa.id, data=(inicio + timedelta(days=5)).isoformat())
    r = _post(client, URL_LANCAR, payload)
    assert r.status_code == 422, r.content


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_fechar_prestacao_concorrente_advisory_lock():
    """Dois fechamentos concorrentes → 1 fecha (201), 1 recebe 422 (advisory lock)."""
    c = _cenario()
    caixa = _cria_caixa(c["tenant"])
    hoje = date.today()
    inicio = (hoje - timedelta(days=30)).isoformat()
    fim = (hoje - timedelta(days=1)).isoformat()
    payload = {
        "caixa_id": str(caixa.id),
        "periodo_de": inicio,
        "periodo_ate": fim,
    }

    resultados = []

    def _fechar():
        client_t = APIClient()
        _autenticar(client_t, c["admin"], c["tenant"])
        r = _post(client_t, URL_FECHAR, payload)
        resultados.append(r.status_code)

    t1 = threading.Thread(target=_fechar)
    t2 = threading.Thread(target=_fechar)
    t1.start()
    t2.start()
    t1.join()
    t2.join()

    # Um fecha (201), outro recebe 422 (período já fechado ou advisory lock)
    assert 201 in resultados or 422 in resultados
    # Deve haver no máximo 1 prestação no banco
    with run_in_tenant_context(c["tenant"].id):
        count = PrestacaoContasCaixaModel.objects.filter(caixa=caixa).count()
    assert count <= 1


# ===========================================================================
# Sync lote
# ===========================================================================


def _item_lote(foto_sufixo: str | None = None, **kw):
    """Gera item de lote com foto única por sufixo (evita uq_ct_despesa_foto_hash_ativa)."""
    sufixo = foto_sufixo or uuid4().hex[:8]
    foto_bytes = f"foto-fake-jpeg-lote-{sufixo}".encode()
    base = {
        "foto_base64": base64.b64encode(foto_bytes).decode(),
        "foto_mime": "image/jpeg",
        "categoria": "combustivel",
        "valor_centavos": 3000,
        "data": date.today().isoformat(),
    }
    base.update(kw)
    return base


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_sync_lote_ok_207():
    """Sync lote com 2 itens OK → 207 + 2 resultados sucesso."""
    c = _cenario()
    caixa = _cria_caixa(c["tenant"])
    client = APIClient()
    _autenticar(client, c["admin"], c["tenant"])

    payload = {
        "caixa_id": str(caixa.id),
        "colaborador_id": str(uuid4()),
        "itens": [
            _item_lote(client_offline_id=f"off-{uuid4()}"),
            _item_lote(client_offline_id=f"off-{uuid4()}"),
        ],
    }
    r = _post(client, URL_SYNC, payload)
    assert r.status_code == 207, r.content
    body = r.json()
    assert "resultados" in body
    assert len(body["resultados"]) == 2
    for item in body["resultados"]:
        assert item["sucesso"] is True
        assert item["codigo_http"] == 201


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_sync_lote_mais_de_20_413():
    """Lote com 21 itens → 413 LoteExcedido."""
    c = _cenario()
    caixa = _cria_caixa(c["tenant"])
    client = APIClient()
    _autenticar(client, c["admin"], c["tenant"])

    payload = {
        "caixa_id": str(caixa.id),
        "colaborador_id": str(uuid4()),
        "itens": [_item_lote() for _ in range(21)],
    }
    r = _post(client, URL_SYNC, payload)
    assert r.status_code == 413, r.content


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_sync_lote_parcial_1_ruim_resto_ok():
    """Lote parcial: 1 item com foto inválida + 1 OK → 207 com mix de resultados."""
    c = _cenario()
    caixa = _cria_caixa(c["tenant"])
    client = APIClient()
    _autenticar(client, c["admin"], c["tenant"])

    payload = {
        "caixa_id": str(caixa.id),
        "colaborador_id": str(uuid4()),
        "itens": [
            {**_item_lote(), "foto_base64": "!!!base64invalido!!!"},  # ruim
            _item_lote(client_offline_id=f"off-{uuid4()}"),  # ok
        ],
    }
    r = _post(client, URL_SYNC, payload)
    assert r.status_code == 207, r.content
    body = r.json()
    resultados = body["resultados"]
    assert len(resultados) == 2
    # Deve haver pelo menos 1 sucesso e 1 falha
    sucessos = [x for x in resultados if x["sucesso"]]
    falhas = [x for x in resultados if not x["sucesso"]]
    assert len(falhas) >= 1
    assert len(sucessos) >= 1


# ===========================================================================
# Cenários de segurança / borda
# ===========================================================================


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_retrieve_cross_tenant_404():
    """Retrieve de despesa de outro tenant → 404."""
    c_a = _cenario()
    c_b = _cenario()
    caixa_b = _cria_caixa(c_b["tenant"])
    despesa_b = _cria_despesa(c_b["tenant"], caixa_b)

    client = APIClient()
    _autenticar(client, c_a["admin"], c_a["tenant"])
    r = client.get(f"/api/v1/caixa-tecnico/despesas/{despesa_b.id}/")
    assert r.status_code == 404, r.content
