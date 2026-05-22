"""Service de resolucao publica de QR (T-EQP-025+026+033 / US-EQP-003).

Tres caminhos:

1. `resolver_escopo_a_se_mesmo_tenant(hash)` — pre-condicao: middleware
   ja setou `app.active_tenant_id`. Tenta via `verificar_qr_hash_em_tabela`
   (que respeita RLS); se retornar nao-None, devolve `QRCode` (escopo A).
   Se None: pode ser hash invalido OU equipamento de outro tenant
   (RLS bloqueia) — caller decide 404 indistinguivel.

2. `resolver_escopo_c_anonimo(hash)` — chama funcao PG SECURITY DEFINER
   `resolver_qr_publico` (T-EQP-025) que ignora RLS controladamente e
   retorna APENAS allowlist publica (fabricante, modelo, status). NAO
   retorna tenant/cliente/tag/NS/localizacao.

3. `aplicar_timing_constant_se_necessario(inicio_perf, alvo_ms=200)` —
   normaliza tempo de resposta total para evitar timing oracle
   (P-EQP-T3 / AC-EQP-003-3). Diferenca entre 404 (hash invalido) e
   200 (hash valido) precisa ser <5ms p99.

Retorno do resolvedor:
- `EscopoAResolvido(qrcode)` quando autenticado mesmo tenant.
- `EscopoCResolvido(payload)` quando anonimo + hash valido.
- `None` quando hash invalido ou Escopo B (autenticado outro tenant).
  Caller monta 404 indistinguivel.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any

from django.db import connection

from src.infrastructure.equipamentos.models import QRCode
from src.infrastructure.equipamentos.services_qr import (
    verificar_qr_hash_em_tabela,
)

# AC-EQP-003-3 (P-EQP-T3): alvo p99 200ms; teto operacional 200ms;
# fuzzing valida ±5ms entre 404 e 200.
TIMING_ALVO_MS = 200
TIMING_TOLERANCIA_MS = 5


@dataclass(frozen=True)
class EscopoAResolvido:
    """Resolvido como Escopo A — autenticado, mesmo tenant. Caller
    monta ficha completa (reusa `construir_ficha_360`)."""

    qrcode: QRCode


@dataclass(frozen=True)
class EscopoCResolvido:
    """Resolvido como Escopo C — anonimo + hash valido. Payload
    minimo allowlist."""

    payload: dict[str, Any]


def resolver_escopo_a_se_mesmo_tenant(hash_apresentado: str) -> QRCode | None:
    """Tenta resolver como Escopo A. Retorna `QRCode` se autenticado +
    mesmo tenant; `None` se hash invalido OU outro tenant (RLS bloqueia).
    """
    return verificar_qr_hash_em_tabela(hash_apresentado)


def resolver_escopo_c_anonimo(hash_apresentado: str) -> EscopoCResolvido | None:
    """Resolve via funcao PG SECURITY DEFINER `resolver_qr_publico`.

    Retorna `EscopoCResolvido` com payload minimo allowlist OU `None` se
    hash invalido. Caller (Escopo C) sempre vai chamar isto — se `None`,
    retorna 404. Se objeto, retorna 200 com payload anonimo.
    """
    if not hash_apresentado or ":" not in hash_apresentado:
        return None
    with connection.cursor() as cur:
        cur.execute(
            "SELECT equipamento_id, fabricante, modelo, status "
            "FROM resolver_qr_publico(%s::text)",
            [hash_apresentado],
        )
        row = cur.fetchone()
    if row is None:
        return None
    _equipamento_id, fabricante, modelo, status = row
    # Allowlist Escopo C — espelha `qr-publico-allowlist.md` §2.
    payload: dict[str, Any] = {
        "tipo": "ativo_afere",
        "fabricante": fabricante or None,
        "modelo": modelo or None,
        "status": status,
        "mensagem": (
            "Este ativo esta cadastrado no Afere. Para acessar detalhes "
            "tecnicos, entre em contato com o laboratorio responsavel."
        ),
        "afere_url_institucional": "https://afere.com.br",
    }
    return EscopoCResolvido(payload=payload)


def aplicar_timing_constant_se_necessario(
    inicio_perf: float,
    alvo_ms: int = TIMING_ALVO_MS,
) -> None:
    """Normaliza tempo de resposta total para `alvo_ms`.

    Mede tempo decorrido desde `inicio_perf` (capturado pelo caller com
    `time.perf_counter()`). Se decorrido < alvo, dorme a diferenca.
    Se decorrido >= alvo, nao faz nada (alerta P2 deve ser disparado
    quando >alvo+50ms em Wave A — observabilidade).
    """
    decorrido_ms = (time.perf_counter() - inicio_perf) * 1000
    falta_ms = alvo_ms - decorrido_ms
    if falta_ms > 0:
        time.sleep(falta_ms / 1000)
