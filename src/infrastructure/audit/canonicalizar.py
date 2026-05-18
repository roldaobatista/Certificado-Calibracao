"""Canonicalizacao de JSON pra entrar no hash chain.

Regra deterministica (forcada por teste, nao por convencao):
- sort_keys=True               -> ordem de chaves alfabetica
- separators=(",", ":")        -> sem espaco
- ensure_ascii=False           -> acentos preservados (codepoint UTF-8 estavel)
- datetime -> isoformat()      -> ISO-8601 com timezone, milissegundos opcionais
- date -> isoformat()          -> YYYY-MM-DD
- Decimal -> str(d)            -> "12.34" (sem virar float, sem perda de precisao)
- UUID -> str(u)               -> "xxx-xxx-..."

Por que importa: 2 maquinas calculando hash do mesmo payload TEM que chegar no
mesmo hash. Sem canonicalizacao, ordem de chaves do dict Python (3.7+ preserva
insercao) vaza pra dentro do hash.
"""

from __future__ import annotations

import json
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Any
from uuid import UUID


def _serializar(obj: Any) -> Any:
    """Converte tipos nao-serializaveis nativos do JSON pra string canonica."""
    if isinstance(obj, datetime):
        # Forca UTC + isoformat. Datetime naive (sem tz) e bug — fail loud.
        if obj.tzinfo is None:
            raise ValueError(
                f"datetime naive proibido em audit payload (campo sem timezone): {obj!r}. "
                "Use timezone.now() do Django ou datetime.now(timezone.utc)."
            )
        return obj.astimezone(timezone.utc).isoformat()
    if isinstance(obj, date):
        return obj.isoformat()
    if isinstance(obj, Decimal):
        return str(obj)
    if isinstance(obj, UUID):
        return str(obj)
    raise TypeError(f"Tipo nao-serializavel em audit payload: {type(obj).__name__}")


def canonicalizar(payload: dict[str, Any]) -> str:
    """Serializa dict pra JSON canonico (string UTF-8 sem espaco, chaves ordenadas)."""
    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        default=_serializar,
    )
