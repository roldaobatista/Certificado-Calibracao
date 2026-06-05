"""F-C2 Fatia B — endpoints de health (liveness vs readiness).

- /livez e /healthz (alias legado): 200 sem checar dependencia;
- /readyz: 200 + checks db/cache OK quando tudo de pe;
- /readyz: 503 + status degraded quando uma dependencia falha (DB mockado).
Todos publicos (sem auth, bypass do TenantMiddleware).
"""

from __future__ import annotations

import pytest
from django.test import Client

_DBS = ["default", "breaker_writer"]


def test_livez_200_sem_dependencia():
    r = Client().get("/livez/")
    assert r.status_code == 200, r.content
    assert r.json()["status"] == "ok"


def test_healthz_legado_alias_de_liveness():
    r = Client().get("/healthz/")
    assert r.status_code == 200, r.content
    assert r.json()["status"] == "ok"


@pytest.mark.django_db(databases=_DBS)
def test_readyz_200_quando_db_e_cache_ok():
    r = Client().get("/readyz/")
    assert r.status_code == 200, r.content
    body = r.json()
    assert body["status"] == "ready"
    assert body["checks"]["db"] == "ok"
    assert body["checks"]["cache"] == "ok"


@pytest.mark.django_db(databases=_DBS)
def test_readyz_503_quando_db_degradado(monkeypatch):
    monkeypatch.setattr(
        "src.infrastructure.observabilidade.health._checar_db",
        lambda: (False, "erro: OperationalError"),
    )
    r = Client().get("/readyz/")
    assert r.status_code == 503, r.content
    body = r.json()
    assert body["status"] == "degraded"
    assert body["checks"]["db"].startswith("erro")
