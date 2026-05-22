"""Rate-limit do QR publico (T-EQP-027 + T-EQP-032 / US-EQP-003).

Duas camadas — APIs separadas para o caller compor:

1. **Por IP** (T-EQP-027 / AC-EQP-003-4 — defesa em profundidade
   corretora):
   - **60 req/min** em `/v1/qr/*`.
   - **>=100 respostas 4xx em 1h** por IP -> **lockout 24h** + publica
     `sistema.qr_lockout_disparado`.

2. **Global por tenant** (T-EQP-032 / AC-EQP-003-9 / P-EQP-S2):
   - **`100 * n_equipamentos_ativos`** req/dia em `/v1/qr/*` cross-tenant
     ou anonimo.
   - Excedente publica `sistema.qr_scraping_suspeito` (1 vez por dia).

Backing store: `django.core.cache.caches['ratelimit']` (Redis DB 2 em
dev/prod, LocMem em test — settings/base.py).

API exposta:
- `avaliar_limite_ip(ip_hash) -> ResultadoIp`
- `avaliar_limite_tenant_qr(tenant_id, n_equip) -> ResultadoTenant`
- `registrar_4xx_ip(ip_hash) -> None`
- `IP_LOCKOUT_TTL_SEG`, `MAX_4XX_HORA`, `MAX_REQS_MIN` (constantes)

NAO usa django-ratelimit — implementacao manual via `cache.add()` +
`cache.incr()` (atomico no Redis; LocMem tambem aceita via lock GIL em
test). Sem dep nova.

Defesa contra cache key collision entre tenants: prefixo embutido na
chave (`qr:ip:{hash}` / `qr:tnt:{uuid}:{dia}`); `KEY_PREFIX='afere-rl'`
do settings aplica-se globalmente.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Final
from uuid import UUID, uuid4

from django.core.cache import caches

# T-EQP-027 — limites por IP.
MAX_REQS_MIN: Final[int] = 60
MAX_4XX_HORA: Final[int] = 100
IP_LOCKOUT_TTL_SEG: Final[int] = 24 * 3600  # 24h
JANELA_MIN_SEG: Final[int] = 60
JANELA_HORA_SEG: Final[int] = 3600

# T-EQP-032 — limite global por tenant (calculado dinamicamente).
LIMITE_REQS_POR_EQUIPAMENTO_DIA: Final[int] = 100
JANELA_DIA_SEG: Final[int] = 24 * 3600


@dataclass(frozen=True)
class ResultadoIp:
    """Decisao do rate-limit por IP."""

    permitido: bool
    motivo: str  # "ok" | "rate_limit_min" | "lockout"
    retry_after_seg: int  # 0 quando permitido
    contagem_min: int
    contagem_4xx_hora: int
    em_lockout: bool


@dataclass(frozen=True)
class ResultadoTenant:
    """Decisao do rate-limit global por tenant."""

    permitido: bool
    motivo: str  # "ok" | "rate_limit_tenant"
    contagem_dia: int
    limite_calculado: int


def _cache():
    return caches["ratelimit"]


# ============================================================
# T-EQP-027 — por IP
# ============================================================


def avaliar_limite_ip(ip_hash: str) -> ResultadoIp:
    """Avalia rate-limit por IP em `/v1/qr/*` (60 req/min) + lockout.

    Incrementa contador da janela atual (1 min) ATOMICAMENTE. Se
    estourar limite OU se IP esta em lockout, retorna `permitido=False`
    com `Retry-After`.

    Caller separadamente chama `registrar_4xx_ip` quando a resposta foi
    4xx; quando atingir `MAX_4XX_HORA` em 1h, esta funcao detecta no
    proximo `avaliar_limite_ip` e ativa lockout.
    """
    if not ip_hash:
        # Sem IP (test/local), nao aplica rate-limit. Defesa: anonimo
        # via curl sem REMOTE_ADDR cai aqui — Wave A vira fail-loud.
        return ResultadoIp(
            permitido=True,
            motivo="ok",
            retry_after_seg=0,
            contagem_min=0,
            contagem_4xx_hora=0,
            em_lockout=False,
        )

    cache = _cache()
    chave_lockout = f"qr:ip:lockout:{ip_hash}"
    em_lockout = cache.get(chave_lockout) is not None

    chave_min = f"qr:ip:min:{ip_hash}"
    chave_4xx = f"qr:ip:4xx:{ip_hash}"
    # cache.add() so seta se nao existir -> TTL preservado entre incrementos.
    cache.add(chave_min, 0, JANELA_MIN_SEG)
    try:
        contagem_min = cache.incr(chave_min)
    except ValueError:
        # Chave expirou entre add e incr (raro) — recoloca.
        cache.set(chave_min, 1, JANELA_MIN_SEG)
        contagem_min = 1
    contagem_4xx = cache.get(chave_4xx, 0) or 0

    if em_lockout:
        ttl_restante = cache.ttl(chave_lockout) if hasattr(cache, "ttl") else IP_LOCKOUT_TTL_SEG
        return ResultadoIp(
            permitido=False,
            motivo="lockout",
            retry_after_seg=int(ttl_restante) if ttl_restante else IP_LOCKOUT_TTL_SEG,
            contagem_min=contagem_min,
            contagem_4xx_hora=contagem_4xx,
            em_lockout=True,
        )

    if contagem_min > MAX_REQS_MIN:
        return ResultadoIp(
            permitido=False,
            motivo="rate_limit_min",
            retry_after_seg=JANELA_MIN_SEG,
            contagem_min=contagem_min,
            contagem_4xx_hora=contagem_4xx,
            em_lockout=False,
        )

    return ResultadoIp(
        permitido=True,
        motivo="ok",
        retry_after_seg=0,
        contagem_min=contagem_min,
        contagem_4xx_hora=contagem_4xx,
        em_lockout=False,
    )


def registrar_4xx_ip(ip_hash: str) -> None:
    """Incrementa contador de 4xx por IP na janela horaria. Quando
    atinge `MAX_4XX_HORA`, ativa lockout 24h e publica
    `sistema.qr_lockout_disparado`.

    Chamado pelo caller APOS responder 4xx (nao bloqueia o request).
    """
    if not ip_hash:
        return

    cache = _cache()
    chave_4xx = f"qr:ip:4xx:{ip_hash}"
    cache.add(chave_4xx, 0, JANELA_HORA_SEG)
    try:
        contagem_4xx = cache.incr(chave_4xx)
    except ValueError:
        cache.set(chave_4xx, 1, JANELA_HORA_SEG)
        contagem_4xx = 1

    if contagem_4xx == MAX_4XX_HORA:
        # Ativacao do lockout — `cache.add` garante idempotencia se
        # chamadas concorrentes atingirem o limiar no mesmo instante.
        chave_lockout = f"qr:ip:lockout:{ip_hash}"
        added = cache.add(chave_lockout, "1", IP_LOCKOUT_TTL_SEG)
        if added:
            _publicar_lockout_disparado(
                ip_hash=ip_hash,
                contagem_4xx=contagem_4xx,
            )


def _publicar_lockout_disparado(
    *, ip_hash: str, contagem_4xx: int
) -> None:
    """Publica `sistema.qr_lockout_disparado` em modo sistema.

    Isolado pra facilitar mock em test (Wave A: alerta P2 vai pra
    PagerDuty stub aqui).
    """
    from src.infrastructure.audit.event_helpers import publicar_evento
    from src.infrastructure.multitenant.connection import run_as_system

    agora = datetime.now(UTC)
    lockout_ate = agora.timestamp() + IP_LOCKOUT_TTL_SEG
    with run_as_system():
        publicar_evento(
            acao="sistema.qr_lockout_disparado",
            tenant_id=None,
            causation_id=uuid4(),
            payload={
                "ip_hash": ip_hash,
                "janela_temporal": "1h",
                "contagem_4xx": contagem_4xx,
                "limite": MAX_4XX_HORA,
                "lockout_ate_unix": int(lockout_ate),
                "disparado_em": agora.isoformat(),
            },
            resource_summary=f"qr_lockout:{ip_hash}",
        )


# ============================================================
# T-EQP-032 — global por tenant
# ============================================================


def avaliar_limite_tenant_qr(
    *, tenant_id: UUID, n_equipamentos_ativos: int
) -> ResultadoTenant:
    """Avalia rate-limit global por tenant em `/v1/qr/*` (cross-tenant
    ou anonimo).

    Limite = `100 * n_equipamentos_ativos` req/dia.

    Sem equipamentos ativos: limite 0 (zero — bloqueia tudo, defesa
    contra scraping em tenant vazio).
    """
    limite = LIMITE_REQS_POR_EQUIPAMENTO_DIA * max(int(n_equipamentos_ativos), 0)

    cache = _cache()
    dia = datetime.now(UTC).strftime("%Y%m%d")
    chave = f"qr:tnt:{tenant_id}:{dia}"
    cache.add(chave, 0, JANELA_DIA_SEG)
    try:
        contagem = cache.incr(chave)
    except ValueError:
        cache.set(chave, 1, JANELA_DIA_SEG)
        contagem = 1

    if contagem > limite:
        # Publica scraping_suspeito uma vez por dia (chave dedicada
        # com mesmo TTL).
        chave_alerta = f"qr:tnt:scraping:{tenant_id}:{dia}"
        if cache.add(chave_alerta, "1", JANELA_DIA_SEG):
            _publicar_qr_scraping_suspeito(
                tenant_id=tenant_id,
                contagem=contagem,
                limite=limite,
                n_equipamentos_ativos=n_equipamentos_ativos,
                dia=dia,
            )
        return ResultadoTenant(
            permitido=False,
            motivo="rate_limit_tenant",
            contagem_dia=contagem,
            limite_calculado=limite,
        )

    return ResultadoTenant(
        permitido=True,
        motivo="ok",
        contagem_dia=contagem,
        limite_calculado=limite,
    )


def _publicar_qr_scraping_suspeito(
    *,
    tenant_id: UUID,
    contagem: int,
    limite: int,
    n_equipamentos_ativos: int,
    dia: str,
) -> None:
    """Publica `sistema.qr_scraping_suspeito` em modo sistema.

    1 evento por dia por tenant (idempotencia via cache.add no caller).
    """
    from src.infrastructure.audit.event_helpers import publicar_evento
    from src.infrastructure.multitenant.connection import run_as_system

    with run_as_system():
        publicar_evento(
            acao="sistema.qr_scraping_suspeito",
            tenant_id=None,
            causation_id=uuid4(),
            payload={
                "tenant_id_alvo": str(tenant_id),
                "janela_dia": dia,
                "contagem_requests": contagem,
                "limite_calculado": limite,
                "n_equipamentos_ativos": n_equipamentos_ativos,
                "disparado_em": datetime.now(UTC).isoformat(),
            },
            resource_summary=f"qr_scraping:{tenant_id}:{dia}",
        )
