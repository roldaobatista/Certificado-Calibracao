"""SSRF guard — validacao de IP/hostname/porta antes do connect.

Implementa INV-WEBHOOK-OUT-002 (F-C1 P3 retrofit). 8 faixas de IP
proibidas + sufixos DNS de descoberta interna + allowlist de portas.

Modulo puro — sem dependencia de httpx/requests/Django. Testavel
isoladamente.
"""

from __future__ import annotations

import ipaddress
import socket
from dataclasses import dataclass
from urllib.parse import urlparse

from src.domain.shared.webhook_out_provider import MotivoRejeicao

# 6 faixas IPv4 + 2 faixas IPv6 (proibidas pra outbound)
_FAIXAS_IPV4_PROIBIDAS: tuple[tuple[ipaddress.IPv4Network, MotivoRejeicao], ...] = (
    (ipaddress.IPv4Network("10.0.0.0/8"), MotivoRejeicao.SSRF_IP_RFC1918),
    (ipaddress.IPv4Network("172.16.0.0/12"), MotivoRejeicao.SSRF_IP_RFC1918),
    (ipaddress.IPv4Network("192.168.0.0/16"), MotivoRejeicao.SSRF_IP_RFC1918),
    (ipaddress.IPv4Network("127.0.0.0/8"), MotivoRejeicao.SSRF_IP_LOOPBACK),
    (ipaddress.IPv4Network("169.254.0.0/16"), MotivoRejeicao.SSRF_IP_LINK_LOCAL),
    (ipaddress.IPv4Network("224.0.0.0/4"), MotivoRejeicao.SSRF_IP_MULTICAST),
    # P3 retrofit (R-3 / CONV-FC1-A):
    (ipaddress.IPv4Network("100.64.0.0/10"), MotivoRejeicao.SSRF_IP_CGN),
    (ipaddress.IPv4Network("0.0.0.0/8"), MotivoRejeicao.SSRF_IP_ZERO),
)

_FAIXAS_IPV6_PROIBIDAS: tuple[tuple[ipaddress.IPv6Network, MotivoRejeicao], ...] = (
    (ipaddress.IPv6Network("::1/128"), MotivoRejeicao.SSRF_IP_LOOPBACK),
    (ipaddress.IPv6Network("fe80::/10"), MotivoRejeicao.SSRF_IP_LINK_LOCAL),
    (ipaddress.IPv6Network("ff00::/8"), MotivoRejeicao.SSRF_IP_MULTICAST),
    # P3 retrofit (R-3 / CONV-FC1-A):
    (ipaddress.IPv6Network("fc00::/7"), MotivoRejeicao.SSRF_IPV6_ULA),
)

# Sufixos DNS de descoberta interna (P3 retrofit R-3 / TL-03)
_SUFIXOS_DNS_INTERNOS: tuple[str, ...] = (
    ".svc.cluster.local",
    ".cluster.local",
    ".consul",
    ".local",  # mDNS
    ".internal",
)

# Allowlist de portas: 443 default; 80 opt-in por destino
_PORTAS_PADRAO_PERMITIDAS: frozenset[int] = frozenset({443})
_PORTAS_OPCIONAIS: frozenset[int] = frozenset({80})


@dataclass(frozen=True)
class ValidacaoIp:
    """Resultado da validacao de UM endereco IP contra as faixas proibidas.

    `ip_resolvido`: o IP que sera usado pra conectar (fixado pra anti-rebinding).
    `permitido`: True quando o IP nao bate em nenhuma faixa proibida.
    `motivo`: razao especifica quando `permitido=False`.
    """

    ip_resolvido: str
    permitido: bool
    motivo: MotivoRejeicao | None


def validar_hostname_dns(hostname: str) -> MotivoRejeicao | None:
    """Verifica se o hostname termina em sufixo DNS de descoberta interna.

    Retorna o motivo (DNS_INTERNO) se bater; None se OK pra proceder.
    """
    hostname_lower = hostname.lower()
    for sufixo in _SUFIXOS_DNS_INTERNOS:
        if hostname_lower.endswith(sufixo):
            return MotivoRejeicao.SSRF_DNS_INTERNO
    return None


def validar_ip(ip: str) -> ValidacaoIp:
    """Valida UM IP (v4 ou v6) contra as 8 faixas proibidas.

    Aceita string. Retorna ValidacaoIp com permitido + motivo.
    """
    try:
        addr = ipaddress.ip_address(ip)
    except ValueError:
        # IP malformado — trata como rejeitado (defesa em profundidade)
        return ValidacaoIp(ip_resolvido=ip, permitido=False, motivo=MotivoRejeicao.SSRF_IP_ZERO)

    if isinstance(addr, ipaddress.IPv4Address):
        for rede, motivo in _FAIXAS_IPV4_PROIBIDAS:
            if addr in rede:
                return ValidacaoIp(ip_resolvido=ip, permitido=False, motivo=motivo)
    else:  # IPv6
        for rede_v6, motivo in _FAIXAS_IPV6_PROIBIDAS:
            if addr in rede_v6:
                return ValidacaoIp(ip_resolvido=ip, permitido=False, motivo=motivo)

    return ValidacaoIp(ip_resolvido=ip, permitido=True, motivo=None)


def validar_porta(porta: int, *, permite_http: bool = False) -> MotivoRejeicao | None:
    """Valida porta contra allowlist.

    443 sempre permitido. 80 so quando `permite_http=True` (opt-in por destino).
    Qualquer outra porta -> SSRF_PORTA_PROIBIDA.
    """
    if porta in _PORTAS_PADRAO_PERMITIDAS:
        return None
    if permite_http and porta in _PORTAS_OPCIONAIS:
        return None
    return MotivoRejeicao.SSRF_PORTA_PROIBIDA


def resolver_hostname(hostname: str) -> list[str]:
    """Resolve hostname pra lista de IPs (A + AAAA) via getaddrinfo.

    Modulo separado pra permitir mock em teste sem patch global.
    Retorna lista deduplicada de strings de IP.
    """
    try:
        results = socket.getaddrinfo(hostname, None, type=socket.SOCK_STREAM)
    except socket.gaierror:
        return []
    ips: list[str] = []
    for family, _, _, _, sockaddr in results:
        ip = sockaddr[0]
        if ip not in ips:
            ips.append(ip)
    return ips


@dataclass(frozen=True)
class ResultadoSsrfGuard:
    """Resultado completo do SSRF guard (porta + hostname + todos os IPs)."""

    permitido: bool
    motivo: MotivoRejeicao | None
    ips_resolvidos: tuple[str, ...]
    porta: int
    hostname: str


def validar_url(
    url: str,
    *,
    permite_http: bool = False,
    resolver=resolver_hostname,
) -> ResultadoSsrfGuard:
    """Pipeline completo do SSRF guard pra uma URL.

    1. Parse URL -> hostname + porta.
    2. Valida sufixo DNS interno.
    3. Valida porta no allowlist.
    4. Resolve DNS via `resolver` (default getaddrinfo; injetavel pra teste).
    5. Valida TODOS os IPs resolvidos contra 8 faixas. Se QUALQUER um bate,
       rejeita (defesa pessimista pro caso de getaddrinfo retornar mix
       seguro+inseguro).

    Retorna ResultadoSsrfGuard com motivo especifico quando rejeitado.
    """
    parsed = urlparse(url)
    hostname = (parsed.hostname or "").lower()
    scheme = (parsed.scheme or "").lower()

    if not hostname:
        return ResultadoSsrfGuard(
            permitido=False,
            motivo=MotivoRejeicao.SSRF_PORTA_PROIBIDA,
            ips_resolvidos=(),
            porta=0,
            hostname="",
        )

    # Porta default por scheme se nao explicita
    porta = parsed.port if parsed.port else (443 if scheme == "https" else 80 if scheme == "http" else 0)

    # 2. Sufixo DNS interno
    motivo_dns = validar_hostname_dns(hostname)
    if motivo_dns:
        return ResultadoSsrfGuard(
            permitido=False,
            motivo=motivo_dns,
            ips_resolvidos=(),
            porta=porta,
            hostname=hostname,
        )

    # 3. Porta
    motivo_porta = validar_porta(porta, permite_http=permite_http)
    if motivo_porta:
        return ResultadoSsrfGuard(
            permitido=False,
            motivo=motivo_porta,
            ips_resolvidos=(),
            porta=porta,
            hostname=hostname,
        )

    # 4. DNS resolve
    ips = resolver(hostname)
    if not ips:
        # Falha de resolucao trata como rejeicao
        return ResultadoSsrfGuard(
            permitido=False,
            motivo=MotivoRejeicao.SSRF_DNS_INTERNO,
            ips_resolvidos=(),
            porta=porta,
            hostname=hostname,
        )

    # 5. Valida TODOS os IPs (pessimista)
    for ip in ips:
        validacao = validar_ip(ip)
        if not validacao.permitido:
            return ResultadoSsrfGuard(
                permitido=False,
                motivo=validacao.motivo,
                ips_resolvidos=tuple(ips),
                porta=porta,
                hostname=hostname,
            )

    return ResultadoSsrfGuard(
        permitido=True,
        motivo=None,
        ips_resolvidos=tuple(ips),
        porta=porta,
        hostname=hostname,
    )
