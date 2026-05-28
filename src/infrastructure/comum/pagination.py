"""Paginação padrão DRF (F-C3 — Foundation instrumentação).

Antes desta classe o projeto NAO tinha `DEFAULT_PAGINATION_CLASS` — todo
endpoint de lista (`ListModelMixin`) retornava o queryset INTEIRO sem limite.
Risco: lista cresce com cada tenant/marco; sem teto vira DoS acidental +
payload gigante + p95 degradado (L8 auditoria pré-Wave A: "retrofit cresce
com cada Marco — 621 hoje, pode ser 1500 daqui 2 meses").

Envelope canônico DRF: `{count, next, previous, results: [...]}`.

Cliente pode pedir `?page_size=` até `max_page_size` (anti-`?page_size=999999`
unbounded). `?page=N` navega.
"""

from __future__ import annotations

from rest_framework.pagination import PageNumberPagination

_PAGE_SIZE_PADRAO = 50
_PAGE_SIZE_MAX = 200


class PaginacaoPadrao(PageNumberPagination):
    """Paginação por número de página com teto de tamanho (anti-unbounded)."""

    page_size = _PAGE_SIZE_PADRAO
    page_size_query_param = "page_size"
    max_page_size = _PAGE_SIZE_MAX
