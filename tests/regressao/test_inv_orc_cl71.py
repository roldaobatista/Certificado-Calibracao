"""INV-ORC-CL71-001 — análise crítica cl. 7.1 perfil-aware, UNHAPPY por perfil (T-ORC-053).

A matriz PURA já é coberta por `tests/test_orcamentos_analise_critica.py` (15 casos).
Este arquivo de regressão pina o comportamento de INTEGRAÇÃO (endpoint `aprovar` +
WORM + transição) que a matriz pura não prova (R1):

  - Perfil A, item fora do CMC → 422 `analise_critica_reprovada` + AnaliseCritica WORM
    gravada + estado permanece `enviado` (fail-closed; a transação COMMITA o WORM).
  - Perfil B, item fora do CMC → 200 `aprovado_pendente_os` + análise WORM
    `com_ressalva` (média) — fail-open lazy com ressalva (capacidade interna declarada).
  - Perfil D → 200 + análise `desabilitada` (não avalia itens).
  - Perfil indeterminado (server-side vazio) → 422 `perfil_indeterminado`, SEM análise,
    SEM transição (fail-closed — D-ORC-5/19; NUNCA aprovar sem perfil resolvido).

Reusa os helpers de `tests/test_orcamentos_fatia2.py` (cenário + catálogo + envio).
Cuidados: PG-real (--reuse-db), TenantFactory + run_in_tenant_context.
"""

from __future__ import annotations

from uuid import UUID

import pytest
from src.infrastructure.multitenant.connection import run_in_tenant_context

from tests.test_orcamentos_fatia2 import (
    _DBS,
    _criar_enviar_com_calib,
    _post,
)


# ---------------------------------------------------------------------------
# Perfil A — fail-closed (item fora do CMC → reprova 422 + WORM)
# ---------------------------------------------------------------------------


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_inv_orc_cl71_perfil_a_reprova_422_grava_worm() -> None:
    """INV-ORC-CL71-001: perfil A com item sem CMC → 422 + WORM + sem transição."""
    c, client, orc = _criar_enviar_com_calib("A")

    r = _post(client, f"/api/v1/orcamentos/{orc['id']}/aprovar/", {})
    assert r.status_code == 422, r.content
    body = r.json()
    assert body["codigo"] == "analise_critica_reprovada"
    assert body["analise_critica"]["veredito"] == "reprovada"
    assert body["orcamento"]["estado"] == "enviado"  # fail-closed: não transiciona

    from src.infrastructure.audit.models import BusOutbox
    from src.infrastructure.orcamentos.models import AnaliseCriticaOrcamento as AModel
    from src.infrastructure.orcamentos.models import Orcamento as OModel

    with run_in_tenant_context(c["tenant"].id):
        # WORM gravada mesmo reprovando (AJUSTE-1) — a transação COMMITOU.
        assert AModel.objects.filter(orcamento_id=orc["id"]).count() == 1
        assert OModel.objects.get(id=orc["id"]).estado == "enviado"
        # Reprovada NUNCA publica orcamento.aprovado.
        assert not BusOutbox.objects.filter(
            acao="orcamento.aprovado", causation_id=UUID(orc["id"])
        ).exists()
        assert (
            BusOutbox.objects.filter(
                acao="orcamento.analise_critica_reprovada", causation_id=UUID(orc["id"])
            ).count()
            == 1
        )


# ---------------------------------------------------------------------------
# Perfil B — fail-open lazy com ressalva (item fora do CMC → aprova com_ressalva)
# ---------------------------------------------------------------------------


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_inv_orc_cl71_perfil_b_item_sem_cmc_aprova_com_ressalva() -> None:
    """INV-ORC-CL71-001: perfil B com item sem CMC → 200 + análise com_ressalva (média)."""
    c, client, orc = _criar_enviar_com_calib("B")

    r = _post(client, f"/api/v1/orcamentos/{orc['id']}/aprovar/", {})
    assert r.status_code == 200, r.content
    body = r.json()
    assert body["orcamento"]["estado"] == "aprovado_pendente_os"
    assert body["analise_critica"]["veredito"] == "com_ressalva"

    from src.infrastructure.audit.models import BusOutbox
    from src.infrastructure.orcamentos.models import AnaliseCriticaOrcamento as AModel

    with run_in_tenant_context(c["tenant"].id):
        analise = AModel.objects.get(orcamento_id=orc["id"])
        assert analise.veredito == "com_ressalva"
        assert analise.itens_avaliados, "ressalva deve carregar registro probatório por item"
        # Aprovada publica orcamento.aprovado (D-ORC-6).
        assert (
            BusOutbox.objects.filter(
                acao="orcamento.aprovado", causation_id=UUID(orc["id"])
            ).count()
            == 1
        )


# ---------------------------------------------------------------------------
# Perfil D — análise desabilitada (não avalia itens; aprova)
# ---------------------------------------------------------------------------


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_inv_orc_cl71_perfil_d_desabilitada_aprova() -> None:
    """INV-ORC-CL71-001: perfil D → análise desabilitada → 200 (sem avaliar itens)."""
    c, client, orc = _criar_enviar_com_calib("D")

    r = _post(client, f"/api/v1/orcamentos/{orc['id']}/aprovar/", {})
    assert r.status_code == 200, r.content
    body = r.json()
    assert body["orcamento"]["estado"] == "aprovado_pendente_os"
    assert body["analise_critica"]["veredito"] == "desabilitada"
    assert body["analise_critica"]["itens_avaliados"] == []

    from src.infrastructure.orcamentos.models import AnaliseCriticaOrcamento as AModel

    with run_in_tenant_context(c["tenant"].id):
        assert AModel.objects.filter(orcamento_id=orc["id"]).count() == 1


# ---------------------------------------------------------------------------
# Perfil indeterminado — fail-closed (server-side vazio → 422, sem WORM, sem transição)
# ---------------------------------------------------------------------------


@pytest.mark.django_db(transaction=True, databases=_DBS)
def test_inv_orc_cl71_perfil_indeterminado_fail_closed(monkeypatch) -> None:
    """INV-ORC-CL71-001: perfil resolvido vazio → 422 perfil_indeterminado, fail-closed.

    Simula a borda de resolução server-side devolvendo perfil indeterminado
    (ADR-0067 não persistido / tenant sem perfil). A view DEVE barrar ANTES de
    avaliar/transicionar — nunca aprovar sem perfil (D-ORC-5/19).
    """
    c, client, orc = _criar_enviar_com_calib("A")

    # Força a resolução server-side a devolver perfil indeterminado.
    import src.infrastructure.orcamentos.views as views_mod

    monkeypatch.setattr(
        views_mod, "resolver_perfil_e_suspensao", lambda: ("", False)
    )

    r = _post(client, f"/api/v1/orcamentos/{orc['id']}/aprovar/", {})
    assert r.status_code == 422, r.content
    assert r.json()["codigo"] == "perfil_indeterminado"

    from src.infrastructure.orcamentos.models import AnaliseCriticaOrcamento as AModel
    from src.infrastructure.orcamentos.models import Orcamento as OModel

    with run_in_tenant_context(c["tenant"].id):
        # Fail-closed: nem análise WORM, nem transição.
        assert AModel.objects.filter(orcamento_id=orc["id"]).count() == 0
        assert OModel.objects.get(id=orc["id"]).estado == "enviado"
