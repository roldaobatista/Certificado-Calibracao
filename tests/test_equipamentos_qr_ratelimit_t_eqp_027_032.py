"""T-EQP-027 + T-EQP-032 — rate-limit IP + global por tenant em
GET `/api/v1/qr/{hash}/` (US-EQP-003).

Cobre:
- T-EQP-027 (AC-EQP-003-4): 60 req/min por IP -> 429 com `Retry-After`.
- T-EQP-027: 100 4xx em 1h por IP -> lockout 24h + publica
  `sistema.qr_lockout_disparado`.
- T-EQP-032 (AC-EQP-003-9 / P-EQP-S2): rate-limit GLOBAL por tenant
  (100 × n_equipamentos_ativos) — anonimo cross-tenant.
- T-EQP-032: excedente publica `sistema.qr_scraping_suspeito` (1 por
  dia por tenant).

Padroes:
- LocMemCache em settings/test garante isolamento por-processo +
  rotatividade do estado entre testes via `clear_cache` fixture.
- Eventos sistema publicados via `run_as_system` — buscar com
  `Auditoria.objects.filter(action=..., tenant_id__isnull=True)`.
"""

from __future__ import annotations

from uuid import uuid4

import pytest
from django.core.cache import caches
from rest_framework.test import APIClient
from src.infrastructure.audit.models import Auditoria
from src.infrastructure.clientes.models import Cliente, TipoPessoa
from src.infrastructure.equipamentos.models import Equipamento, QRCode
from src.infrastructure.equipamentos.services_qr import (
    gerar_qr_hash_versionado,
)
from src.infrastructure.equipamentos.services_ratelimit import (
    JANELA_HORA_SEG,
    MAX_4XX_HORA,
    MAX_REQS_MIN,
)
from src.infrastructure.multitenant.connection import (
    run_as_system,
    run_in_tenant_context,
)

from tests.factories import TenantFactory


@pytest.fixture(autouse=True)
def _limpa_cache_ratelimit():
    """Garante isolamento entre testes (LocMem persiste por-processo)."""
    caches["ratelimit"].clear()
    yield
    caches["ratelimit"].clear()


@pytest.fixture
def cenario(db):
    sfx = uuid4().hex[:6]
    tenant_a = TenantFactory(slug=f"rl-a-{sfx}", nome_fantasia="Lab A")
    with run_in_tenant_context(tenant_a.id):
        cliente_a = Cliente.objects.create(
            tenant=tenant_a,
            tipo_pessoa=TipoPessoa.PJ,
            documento="11222333000181",
            nome="Cliente Rl A",
            aceite_lgpd_dispensa_motivo="pj_sem_pf_associada",
        )
        eq_a = Equipamento.objects.create(
            tenant=tenant_a,
            tag=f"RL-A-{sfx}",
            numero_serie=f"NS-RL-A-{sfx}",
            fabricante="Toledo",
            modelo="Prix 4",
            cliente_atual=cliente_a,
            perfil_tenant_snapshot={"perfil": "D"},
        )
        hash_a = gerar_qr_hash_versionado(eq_a.id, tenant_a.id, eq_a.criado_em)
        QRCode.objects.create(
            tenant=tenant_a,
            equipamento=eq_a,
            hash=hash_a,
            emitido_em=eq_a.criado_em,
        )
    return {
        "tenant_a": tenant_a,
        "eq_a": eq_a,
        "hash_a": hash_a,
    }


# ====================================================================
# T-EQP-027 — rate-limit por IP
# ====================================================================


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_rate_limit_ip_60req_min_retorna_429(cenario):
    """61a chamada no minuto do mesmo IP -> 429 com Retry-After."""
    client = APIClient(REMOTE_ADDR="10.0.0.42")
    # MAX_REQS_MIN = 60 chamadas validas.
    for _ in range(MAX_REQS_MIN):
        resp = client.get(f"/api/v1/qr/{cenario['hash_a']}/")
        assert resp.status_code == 200
    resp = client.get(f"/api/v1/qr/{cenario['hash_a']}/")
    assert resp.status_code == 429
    assert resp.json()["motivo"] == "rate_limit_min"
    assert int(resp["Retry-After"]) >= 1


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_rate_limit_ip_ips_diferentes_nao_se_afetam(cenario):
    """Outro IP nao sofre rate-limit do primeiro IP."""
    client1 = APIClient(REMOTE_ADDR="10.0.0.10")
    # Esgota limite do IP1.
    for _ in range(MAX_REQS_MIN + 1):
        client1.get(f"/api/v1/qr/{cenario['hash_a']}/")
    client2 = APIClient(REMOTE_ADDR="10.0.0.11")
    resp = client2.get(f"/api/v1/qr/{cenario['hash_a']}/")
    assert resp.status_code == 200


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_lockout_disparado_apos_100_4xx_em_1h(cenario):
    """100 4xx em 1h por IP -> lockout + evento sistema."""
    # IP unico por teste (Auditoria nao truncada entre runs — filtra
    # por ip_hash garante isolamento contra residuo de runs anteriores).
    ip_unico = f"10.0.0.{(hash(uuid4()) % 250) + 1}"
    client = APIClient(REMOTE_ADDR=ip_unico)
    # Hash invalido (404). Mas o rate-limit-min permite so 60/min;
    # injetamos 4xx contagem diretamente via cache pra atingir limiar.
    cache = caches["ratelimit"]
    ip_hash_existente = _ip_hash_via_helper(ip_unico)
    cache.set(f"qr:ip:4xx:{ip_hash_existente}", MAX_4XX_HORA - 1, JANELA_HORA_SEG)
    # 1 chamada com hash invalido -> 404 -> incrementa pra MAX -> lockout.
    resp = client.get("/api/v1/qr/qr1:invalid_hash_with_colon/")
    assert resp.status_code == 404
    # 1 chamada extra ja deve cair em lockout.
    resp2 = client.get(f"/api/v1/qr/{cenario['hash_a']}/")
    assert resp2.status_code == 429
    assert resp2.json()["motivo"] == "lockout"
    # Verifica evento publicado em modo sistema (tenant_id NULL).
    # Filtra por ip_hash deste teste — Auditoria nao truncada entre testes.
    with run_as_system():
        eventos = [
            e
            for e in Auditoria.objects.filter(
                action="sistema.qr_lockout_disparado"
            )
            if e.payload_jsonb.get("ip_hash") == ip_hash_existente
        ]
    assert len(eventos) == 1
    assert eventos[0].payload_jsonb.get("contagem_4xx") == MAX_4XX_HORA
    assert eventos[0].payload_jsonb.get("ip_hash")  # hash, nao IP cru


def _ip_hash_via_helper(ip: str) -> str:
    """Reusa o mesmo helper do view (mesmo salt)."""
    from src.infrastructure.equipamentos.views_qr_publico import (
        _hash_ip_simples,
    )

    return _hash_ip_simples(ip)


# ====================================================================
# T-EQP-032 — rate-limit global por tenant
# ====================================================================


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_rate_limit_tenant_excedido_anonimo_retorna_429(cenario):
    """Anonimo excede `100 * n_equipamentos_ativos`/dia -> 429 + evento."""
    from datetime import UTC, datetime

    # Saturar a contagem por tenant ate o limite + 1.
    cache = caches["ratelimit"]
    n_equip = 1  # tem 1 equipamento ativo no cenario
    limite = 100 * n_equip
    dia = datetime.now(UTC).strftime("%Y%m%d")
    cache.set(f"qr:tnt:{cenario['tenant_a'].id}:{dia}", limite, 24 * 3600)
    # Cache do n_equipamentos pra evitar query lateral:
    cache.set(f"qr:tnt:eqp_ativos:{cenario['tenant_a'].id}", n_equip, 300)

    client = APIClient(REMOTE_ADDR="10.0.0.50")
    resp = client.get(f"/api/v1/qr/{cenario['hash_a']}/")
    # Ja era == limite; esta chamada incrementa pra limite+1 -> 429.
    assert resp.status_code == 429
    assert resp.json()["motivo"] == "rate_limit_tenant"
    # Verifica evento sistema publicado.
    # Auditoria nao truncada entre testes (trigger anti-DELETE) — filtra
    # por tenant_alvo deste teste para isolar do residuo de outros testes.
    with run_as_system():
        eventos = [
            e
            for e in Auditoria.objects.filter(
                action="sistema.qr_scraping_suspeito"
            )
            if e.payload_jsonb.get("tenant_id_alvo") == str(cenario["tenant_a"].id)
        ]
    assert len(eventos) == 1
    assert eventos[0].payload_jsonb["limite_calculado"] == limite


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_rate_limit_tenant_evento_disparado_uma_vez_por_dia(cenario):
    """2 requests acima do limite no mesmo dia -> 1 evento sistema."""
    from datetime import UTC, datetime

    cache = caches["ratelimit"]
    dia = datetime.now(UTC).strftime("%Y%m%d")
    n_equip = 1
    limite = 100 * n_equip
    cache.set(f"qr:tnt:{cenario['tenant_a'].id}:{dia}", limite, 24 * 3600)
    cache.set(f"qr:tnt:eqp_ativos:{cenario['tenant_a'].id}", n_equip, 300)
    client = APIClient(REMOTE_ADDR="10.0.0.51")
    client.get(f"/api/v1/qr/{cenario['hash_a']}/")
    # Segunda chamada acima do limite — NAO deve duplicar evento
    # para o MESMO tenant_alvo.
    client.get(f"/api/v1/qr/{cenario['hash_a']}/")
    with run_as_system():
        eventos = [
            e
            for e in Auditoria.objects.filter(
                action="sistema.qr_scraping_suspeito"
            )
            if e.payload_jsonb.get("tenant_id_alvo") == str(cenario["tenant_a"].id)
        ]
    assert len(eventos) == 1


# ====================================================================
# T-EQP-029 — filtro historico cessionario sem consentimento
# ====================================================================


@pytest.fixture
def cenario_transferencia(db):
    """Cenario com transferencia efetivada + consentimento `nada`."""
    from src.infrastructure.audit.services import hashear_pii_com_salt_tenant
    from src.infrastructure.equipamentos.models import EquipamentoVersao
    from src.infrastructure.equipamentos.services_transferencia import (
        Aceite,
        DadosSolicitacaoTransferencia,
        solicitar_transferencia,
    )

    from tests.factories import UsuarioFactory

    sfx = uuid4().hex[:6]
    tenant = TenantFactory(slug=f"f29-{sfx}", nome_fantasia="Lab F29")
    user = UsuarioFactory(email=f"adm-{sfx}@e.local")
    with run_in_tenant_context(tenant.id):
        cedente = Cliente.objects.create(
            tenant=tenant,
            tipo_pessoa=TipoPessoa.PJ,
            documento="11222333000181",
            nome="Cedente F29",
            aceite_lgpd_dispensa_motivo="pj_sem_pf_associada",
        )
        cessionario = Cliente.objects.create(
            tenant=tenant,
            tipo_pessoa=TipoPessoa.PJ,
            documento="22333444000172",
            nome="Cessionario F29",
            aceite_lgpd_dispensa_motivo="pj_sem_pf_associada",
        )
        eq = Equipamento.objects.create(
            tenant=tenant,
            tag=f"F29-{sfx}",
            numero_serie=f"NS-F29-{sfx}",
            fabricante="Toledo",
            modelo="Prix 4",
            cliente_atual=cedente,
            perfil_tenant_snapshot={"perfil": "D"},
        )
        # Versao ANTES da transferencia (deve ser ocultada quando nivel=nada).
        EquipamentoVersao.objects.create(
            tenant=tenant,
            equipamento=eq,
            campo="modelo",
            valor_anterior_hash=hashear_pii_com_salt_tenant("Prix 3", tenant.id),
            valor_novo_hash=hashear_pii_com_salt_tenant("Prix 4", tenant.id),
            motivo_mudanca="correcao_cadastral",
            criado_por=user,
        )
        # Faz transferencia com nivel=NADA (cessionario sem acesso ao hist).
        solicitar_transferencia(
            tenant_id=tenant.id,
            equipamento=eq,
            solicitado_por_id=user.id,
            dados=DadosSolicitacaoTransferencia(
                cessionario_cliente_id=cessionario.id,
                motivo_categoria="venda",
                aceite_cedente=Aceite(
                    tipo="presencial_atendente",
                    usuario_id_atendente=user.id,
                    observacao="aceite cedente",
                    nivel_consentimento_historico="nada",
                ),
                aceite_cessionario=Aceite(
                    tipo="contrato_fisico_digitalizado",
                    usuario_id_atendente=user.id,
                    observacao="aceite cessionario",
                ),
            ),
        )
        eq.refresh_from_db()
    return {
        "tenant": tenant,
        "user": user,
        "cedente": cedente,
        "cessionario": cessionario,
        "eq": eq,
    }


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_filtro_historico_nivel_nada_oculta_versoes_pre_transferencia(
    cenario_transferencia,
):
    """Cessionario sem consentimento NAO ve versoes anteriores a
    transferencia + banner aparece."""
    from src.infrastructure.equipamentos.services_ficha360 import (
        construir_ficha_360,
    )

    with run_in_tenant_context(cenario_transferencia["tenant"].id):
        ficha = construir_ficha_360(cenario_transferencia["eq"])
    aviso = ficha["aviso_historico_filtrado"]
    assert aviso["ativo"] is True
    assert aviso["nivel_consentimento_historico"] == "nada"
    assert "Historico preservado" in aviso["banner"]
    # Versao pre-transferencia foi ocultada (>= corte filtra).
    # A unica versao foi criada ANTES da transferencia, entao
    # versoes deve estar vazio (filtro por criado_em >= corte).
    versoes_pre = [
        v for v in ficha["versoes"]
        if v["motivo_mudanca"] == "correcao_cadastral"
    ]
    assert versoes_pre == []


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_filtro_historico_nivel_completo_mostra_tudo(cenario_transferencia):
    """Cessionario com consentimento `completo` ve historico
    integral + sem banner ativo."""
    from src.infrastructure.equipamentos.models import (
        ConsentimentoHistoricoEquipamento,
    )
    from src.infrastructure.equipamentos.services_ficha360 import (
        construir_ficha_360,
    )

    # Promove o consentimento existente a `completo` via UPDATE
    # direto — trigger PG so bloqueia `nivel` se for um campo CORE,
    # mas nivel E CORE imutavel. Nao podemos UPDATE. Vou simular
    # criando outro cenario diretamente: usar `concede_again` apos
    # revogar? Mais simples: criar nova transferencia com nivel
    # completo (mas seria nova transferencia, fica complexo).
    #
    # Solucao pragmatica: deletar e recriar o consentimento com
    # nivel=completo via run_as_system (bypass trigger so via
    # CRIACAO direta, sem UPDATE).
    tenant = cenario_transferencia["tenant"]
    eq = cenario_transferencia["eq"]
    with run_in_tenant_context(tenant.id):
        consent = ConsentimentoHistoricoEquipamento.objects.get(
            equipamento_id=eq.id
        )
        transferencia = consent.transferencia_origem
        # Nao podemos UPDATE nivel (trigger bloqueia). Vamos SIMULAR
        # criando novo registro com nivel completo apos REVOGAR o
        # existente (revogar libera UNIQUE parcial).
        from src.infrastructure.equipamentos.services_consentimento_historico import (
            conceder_consentimento_historico,
            revogar_consentimento_historico,
        )

        revogar_consentimento_historico(
            tenant_id=tenant.id,
            consentimento=consent,
            revogado_por_id=cenario_transferencia["user"].id,
            justificativa="reset para teste de nivel completo no cenario.",
            via_revogacao="presencial_atendente",
        )
        conceder_consentimento_historico(
            tenant_id=tenant.id,
            equipamento=eq,
            transferencia=transferencia,
            cedente_cliente_id=cenario_transferencia["cedente"].id,
            nivel="completo",
            concedido_por_id=cenario_transferencia["user"].id,
            via_concessao="presencial_atendente",
        )
        ficha = construir_ficha_360(eq)
    aviso = ficha["aviso_historico_filtrado"]
    assert aviso["ativo"] is False
    assert aviso["nivel_consentimento_historico"] == "completo"
    # Versao pre-transferencia esta visivel.
    versoes_pre = [
        v for v in ficha["versoes"]
        if v["motivo_mudanca"] == "correcao_cadastral"
    ]
    assert len(versoes_pre) == 1


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_filtro_historico_sem_transferencia_sem_filtro(db):
    """Equipamento que nunca foi transferido -> sem filtro, sem banner."""
    from src.infrastructure.equipamentos.services_ficha360 import (
        construir_ficha_360,
    )

    sfx = uuid4().hex[:6]
    tenant = TenantFactory(slug=f"f29b-{sfx}", nome_fantasia="Lab F29B")
    with run_in_tenant_context(tenant.id):
        cliente = Cliente.objects.create(
            tenant=tenant,
            tipo_pessoa=TipoPessoa.PJ,
            documento="11222333000181",
            nome="Cliente B",
            aceite_lgpd_dispensa_motivo="pj_sem_pf_associada",
        )
        eq = Equipamento.objects.create(
            tenant=tenant,
            tag=f"F29B-{sfx}",
            numero_serie=f"NS-F29B-{sfx}",
            fabricante="Toledo",
            modelo="Prix 4",
            cliente_atual=cliente,
            perfil_tenant_snapshot={"perfil": "D"},
        )
        ficha = construir_ficha_360(eq)
    aviso = ficha["aviso_historico_filtrado"]
    assert aviso["ativo"] is False
    assert aviso["nivel_consentimento_historico"] == "sem_filtro"
