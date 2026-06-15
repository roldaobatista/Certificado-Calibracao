"""Endpoint PÚBLICO de aprovação de orçamento — E2E (Onda 2e / T-ORC-038).

Cobre o que só o PG-real prova: resolução de token SEM RLS (SECURITY DEFINER),
allowlist anti-vazamento (ADV-ORC-09), aprovação 1-clique com Aprovacao WORM,
fail-closed perfil A, confirmação de ressalvas (cl. 7.1.1-d), token inválido/
expirado/revogado → 404 indistinguível (D-ORC-7/19).

Reusa os helpers de `test_orcamentos_fatia2` (cenário + catálogo + envio).
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID

import pytest
from rest_framework.test import APIClient
from src.infrastructure.multitenant.connection import run_in_tenant_context

from tests.test_orcamentos_fatia2 import (
    _DBS,
    _adicionar_item_calib,
    _cenario_perfil,
    _client,
    _criar_cliente,
    _criar_orcamento,
    _post,
    _setup_catalogo,
)

_ACEITE = {
    "nome_aprovador": "Joao Cliente",
    "email_aprovador": "joao@cliente.example",
    "aceite_versao_termo": "v2026-01",
    "aceite_texto": "Li e aceito os termos e o valor deste orcamento de calibracao.",
}


def _enviar_e_pegar_token(perfil: str) -> tuple[dict, dict, str]:
    """Cria→item calibração→envia. Retorna (cenario, orc, token_do_link)."""
    c = _cenario_perfil(perfil)
    client = _client(c)
    cliente = _criar_cliente(c["tenant"], c["admin"])
    item = _setup_catalogo(client, preco="150.00")
    orc = _criar_orcamento(client, cliente.id).json()
    assert _adicionar_item_calib(client, orc["id"], item["id"]).status_code == 201
    env = _post(client, f"/api/v1/orcamentos/{orc['id']}/enviar/", {})
    assert env.status_code == 200, env.content
    return c, orc, env.json()["link"]["token"]


def _publico() -> APIClient:
    """Cliente anônimo (sem auth, sem header de tenant)."""
    return APIClient()


# ---------------------------------------------------------------------------
# GET preview
# ---------------------------------------------------------------------------


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_get_publico_allowlist_sem_vazamento() -> None:
    """GET {token} resolve via SECURITY DEFINER e devolve só a allowlist."""
    _c, orc, token = _enviar_e_pegar_token("D")
    r = _publico().get(f"/api/v1/public/orcamentos/{token}/")
    assert r.status_code == 200, r.content
    body = r.json()
    assert body["numero"] == orc["numero"]
    assert body["itens"][0]["descricao"]
    assert body["itens"][0]["preco_unitario"]["centavos"] == 15000
    # Anti-vazamento (ADV-ORC-09 / INV-ORC-MARGEM-OFF): NUNCA campos internos.
    bruto = str(body)
    for proibido in ("margem", "custo", "comissao", "observac", "semaforo", "preco_resolvido"):
        assert proibido not in bruto, f"vazou campo interno: {proibido}"


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_get_publico_token_invalido_404() -> None:
    r = _publico().get("/api/v1/public/orcamentos/token-inexistente-mas-longo-o-bastante/")
    assert r.status_code == 404, r.content
    assert r.json()["codigo"] == "token_invalido_ou_expirado"


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_get_publico_token_expirado_404() -> None:
    c, _orc, token = _enviar_e_pegar_token("D")
    from src.infrastructure.orcamentos.models import LinkPublico as LinkModel

    with run_in_tenant_context(c["tenant"].id):
        LinkModel.objects.filter(token=token).update(
            expira_em=datetime.now(UTC) - timedelta(days=1)
        )
    r = _publico().get(f"/api/v1/public/orcamentos/{token}/")
    assert r.status_code == 404, r.content


# ---------------------------------------------------------------------------
# POST aprovação 1-clique
# ---------------------------------------------------------------------------


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_post_publico_aprova_perfil_d() -> None:
    """Aprovação 1-clique: Aprovacao WORM + estado + evento + link revogado (one-shot)."""
    c, orc, token = _enviar_e_pegar_token("D")
    r = _publico().post(
        f"/api/v1/public/orcamentos/{token}/aprovar/", _ACEITE, format="json"
    )
    assert r.status_code == 200, r.content
    assert r.json()["estado"] == "aprovado_pendente_os"

    from src.infrastructure.audit.models import BusOutbox
    from src.infrastructure.orcamentos.models import Aprovacao as AprovModel
    from src.infrastructure.orcamentos.models import LinkPublico as LinkModel
    from src.infrastructure.orcamentos.models import Orcamento as OModel

    with run_in_tenant_context(c["tenant"].id):
        assert OModel.objects.get(id=orc["id"]).estado == "aprovado_pendente_os"
        aprov = AprovModel.objects.get(orcamento_id=orc["id"])
        assert aprov.canal == "link_publico"
        assert aprov.aprovado_por is None
        assert aprov.nome_aprovador_hash and aprov.nome_aprovador_hash != _ACEITE["nome_aprovador"]
        assert aprov.lgpd_aceite_versao_termo == "v2026-01"
        # Link revogado (one-shot — não reaprovável).
        assert LinkModel.objects.get(token=token).revogado_em is not None
        assert BusOutbox.objects.filter(
            acao="orcamento.aprovado", causation_id=UUID(orc["id"])
        ).count() == 1


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_post_publico_link_revogado_nao_reaprova_404() -> None:
    """Após aprovar (link revogado), 2ª tentativa → 404."""
    _c, _orc, token = _enviar_e_pegar_token("D")
    pub = _publico()
    assert pub.post(f"/api/v1/public/orcamentos/{token}/aprovar/", _ACEITE, format="json").status_code == 200
    r2 = pub.post(f"/api/v1/public/orcamentos/{token}/aprovar/", _ACEITE, format="json")
    assert r2.status_code == 404, r2.content


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_post_publico_reprova_perfil_a_sem_cmc() -> None:
    """Perfil A fail-closed: análise WORM gravada + 422 + SEM Aprovacao (não aprovou)."""
    c, orc, token = _enviar_e_pegar_token("A")
    r = _publico().post(
        f"/api/v1/public/orcamentos/{token}/aprovar/", _ACEITE, format="json"
    )
    assert r.status_code == 422, r.content
    assert r.json()["codigo"] == "analise_critica_reprovada"

    from src.infrastructure.orcamentos.models import AnaliseCriticaOrcamento as AModel
    from src.infrastructure.orcamentos.models import Aprovacao as AprovModel
    from src.infrastructure.orcamentos.models import Orcamento as OModel

    with run_in_tenant_context(c["tenant"].id):
        assert OModel.objects.get(id=orc["id"]).estado == "enviado"  # não transicionou
        assert AModel.objects.filter(orcamento_id=orc["id"]).count() == 1  # WORM gravada
        assert AprovModel.objects.filter(orcamento_id=orc["id"]).count() == 0  # sem Aprovacao


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_post_publico_com_ressalva_exige_confirmacao() -> None:
    """Perfil B + item sem CMC = com_ressalva média: POST sem confirmação → 422; com → 200."""
    c, orc, token = _enviar_e_pegar_token("B")

    # GET preview deve sinalizar requer_confirmacao + ressalvas.
    g = _publico().get(f"/api/v1/public/orcamentos/{token}/")
    assert g.status_code == 200, g.content
    assert g.json()["requer_confirmacao_ressalvas"] is True
    assert g.json()["ressalvas"]

    # POST sem ressalvas_confirmadas → 422.
    r1 = _publico().post(
        f"/api/v1/public/orcamentos/{token}/aprovar/", _ACEITE, format="json"
    )
    assert r1.status_code == 422, r1.content
    assert r1.json()["codigo"] == "ressalvas_nao_confirmadas"

    # POST com ressalvas_confirmadas → 200 + Aprovacao.ressalvas_aceitas=True.
    r2 = _publico().post(
        f"/api/v1/public/orcamentos/{token}/aprovar/",
        {**_ACEITE, "ressalvas_confirmadas": True},
        format="json",
    )
    assert r2.status_code == 200, r2.content

    from src.infrastructure.orcamentos.models import Aprovacao as AprovModel

    with run_in_tenant_context(c["tenant"].id):
        aprov = AprovModel.objects.get(orcamento_id=orc["id"])
        assert aprov.ressalvas_aceitas is True
