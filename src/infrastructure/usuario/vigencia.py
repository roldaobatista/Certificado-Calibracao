"""Janela de vigência de `UsuarioPerfilTenant` — FONTE ÚNICA (T-FB-02).

Antes havia 3 cópias da regra (`multitenant/middleware`, `authz/
django_provider` duplicada "evita import circular", `authz/middleware.
_tem_perfil_sensivel` que ignorava `valido_ate` por completo — FB-A4).
Aqui mora a definição ÚNICA da janela COMPLETA.

Sem ciclo de import: só `django.db.models.Q` (nenhum model/app) — pode
ser importado no topo de qualquer módulo.
"""

from __future__ import annotations

from datetime import datetime

from django.db.models import Q


def janela_vigente(agora: datetime) -> Q:
    """`valido_de <= agora` E (`valido_ate` nulo OU `>= agora`).

    Janela COMPLETA — não só o teto `valido_ate` (era o defeito FB-A4:
    o middleware MFA filtrava só `valido_de` e barrava por perfil já
    expirado).
    """
    return Q(valido_de__lte=agora) & (Q(valido_ate__isnull=True) | Q(valido_ate__gte=agora))
