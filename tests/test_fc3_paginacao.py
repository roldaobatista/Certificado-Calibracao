"""F-C3 — paginação global DRF (PaginacaoPadrao).

Prova que a paginação padrão está configurada e ativa: envelope canônico
`{count, next, previous, results}`, page_size padrão 50, e TETO anti-unbounded
(`?page_size=999999` é capado em max_page_size). Testa a classe diretamente
(puro, sem DB); a fiação global vive em config/settings/base.py REST_FRAMEWORK.

Antes do F-C3 o projeto não tinha DEFAULT_PAGINATION_CLASS — list endpoints
retornavam o queryset inteiro (risco DoS acidental conforme o tenant cresce).
"""

from __future__ import annotations

from rest_framework.request import Request
from rest_framework.test import APIRequestFactory
from src.infrastructure.comum.pagination import PaginacaoPadrao

_FACTORY = APIRequestFactory()


def _req(url: str) -> Request:
    return Request(_FACTORY.get(url))


class TestConfigClasse:
    def test_page_size_padrao_50(self) -> None:
        assert PaginacaoPadrao.page_size == 50

    def test_max_page_size_200(self) -> None:
        assert PaginacaoPadrao.max_page_size == 200

    def test_page_size_query_param(self) -> None:
        assert PaginacaoPadrao.page_size_query_param == "page_size"


class TestComportamento:
    def test_envelope_canonico_e_page_size_padrao(self) -> None:
        paginator = PaginacaoPadrao()
        page = paginator.paginate_queryset(list(range(60)), _req("/x"))
        assert page is not None
        assert len(page) == 50  # page_size padrão
        resp = paginator.get_paginated_response(page)
        assert resp.data["count"] == 60
        assert resp.data["next"] is not None  # tem proxima pagina
        assert resp.data["previous"] is None
        assert "results" in resp.data

    def test_page_size_query_param_respeitado(self) -> None:
        paginator = PaginacaoPadrao()
        page = paginator.paginate_queryset(list(range(60)), _req("/x?page_size=10"))
        assert page is not None
        assert len(page) == 10

    def test_teto_anti_unbounded(self) -> None:
        """?page_size=999999 é capado em max_page_size (anti-DoS acidental)."""
        paginator = PaginacaoPadrao()
        page = paginator.paginate_queryset(
            list(range(300)), _req("/x?page_size=999999")
        )
        assert page is not None
        assert len(page) == 200  # capado, NAO 300

    def test_segunda_pagina_tem_previous(self) -> None:
        paginator = PaginacaoPadrao()
        page = paginator.paginate_queryset(list(range(60)), _req("/x?page=2"))
        assert page is not None
        assert len(page) == 10  # 60 - 50 = 10 na 2a pagina
        resp = paginator.get_paginated_response(page)
        assert resp.data["previous"] is not None
        assert resp.data["next"] is None
