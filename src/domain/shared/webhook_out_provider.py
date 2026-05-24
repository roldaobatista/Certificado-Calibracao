"""Porta `OutboundWebhookProvider` — webhooks de saida (ADR-0054, F-C1).

Domain layer puro: sem dependencia de Django, sem dependencia de requests/httpx.
Quem implementa esta porta:
- `src.infrastructure.webhook_out.adapter.RequestsWebhookOut` (F-C1 P4).
- futuros adapters trocam SEM tocar no dominio.

Quem CHAMA esta porta (regra cravada em INV-WEBHOOK-OUT-001):
- Qualquer modulo que precise chamar URL HTTP externa: Lacuna (A3), AWS KMS,
  Asaas (gateway pagamento), INMETRO, SendGrid (email), webhooks de tenant.
- Uso direto de `requests`/`httpx`/`urllib.request`/`urllib3` em
  `src/infrastructure/**` fica PROIBIDO fora do adapter
  (hook `outbound-webhook-ssrf-check.sh`).

Defesas implementadas (F-C1 P3 retrofit):
- INV-WEBHOOK-OUT-002: SSRF guard 8 faixas (RFC1918, loopback, link-local,
  multicast, IPv6 ULA fc00::/7, CGN 100.64/10, 0.0.0.0/8, sufixos DNS
  internos).
- INV-WEBHOOK-OUT-003: HMAC-SHA256 sobre canonical string
  `{timestamp}.{method}.{path}.{sha256(body)}` + janela <=5min + event_id.
- INV-WEBHOOK-OUT-004: DNS resolve uma vez + connect pelo IP fixado
  (anti-rebinding).
- INV-WEBHOOK-OUT-005: REJEITA chamada se `webhook_destino.dpa_assinado_em IS
  NULL` ou `dpa_vence_em < hoje` ou `chave_expires_at < hoje` (LGPD art. 39 +
  rotacao <=90d).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Any, Protocol, runtime_checkable
from uuid import UUID


class MotivoRejeicao(StrEnum):
    """Razao estavel pra rejeicao de chamada outbound (usada em log/metric)."""

    SSRF_IP_RFC1918 = "ssrf_ip_rfc1918"
    SSRF_IP_LOOPBACK = "ssrf_ip_loopback"
    SSRF_IP_LINK_LOCAL = "ssrf_ip_link_local"
    SSRF_IP_MULTICAST = "ssrf_ip_multicast"
    SSRF_IPV6_ULA = "ssrf_ipv6_ula"
    SSRF_IP_CGN = "ssrf_ip_cgn"
    SSRF_IP_ZERO = "ssrf_ip_0_0_0_0_slash_8"
    SSRF_DNS_INTERNO = "ssrf_dns_descoberta_interna"
    SSRF_PORTA_PROIBIDA = "ssrf_porta_proibida"
    DNS_REBINDING_DETECTADO = "dns_rebinding_detectado"
    DPA_AUSENTE = "dpa_ausente"
    DPA_VENCIDO = "dpa_vencido"
    HMAC_KEY_VENCIDA = "hmac_key_vencida"
    DESTINO_DESATIVADO = "destino_desativado"
    TIMEOUT_CONEXAO = "timeout_conexao"
    TIMEOUT_LEITURA = "timeout_leitura"


@dataclass(frozen=True)
class RequisicaoWebhook:
    """Dados de entrada pra uma chamada outbound.

    `destino_id`: aponta pra `webhook_destino` (tabela com cadastro DPA + chave
        HMAC). NUNCA passar URL crua — sempre via `destino_id`. Quem cadastra o
        destino e quem registra o DPA + chave HMAC.

    `metodo`: HTTP method (GET, POST, PUT, PATCH, DELETE).

    `caminho`: path relativo ao `url_base` do destino (ex: "/v2/payments").

    `corpo`: body JSON-serializavel; vazio em GET. NAO pode conter PII
        nao-declarada nas `categorias_dados` do destino (validacao no adapter).

    `event_id`: UUID v4 gerado pelo chamador; propagado no header
        `X-Afere-Event-Id`; persistido em `consumer_idempotencia` (ADR-0033)
        pra dedupe quando webhook ENTRANTE volta como confirmacao.

    `tenant_id`: tenant que origina a chamada (RLS + audit).

    `correlation_id`: opcional, propagado se vier de contexto HTTP/bus.
    """

    destino_id: UUID
    metodo: str
    caminho: str
    corpo: dict[str, Any] | None
    event_id: UUID
    tenant_id: UUID
    correlation_id: UUID | None = None


@dataclass(frozen=True)
class RespostaWebhook:
    """Resultado de uma chamada outbound.

    `sucesso`: 2xx do destino + assinatura validada (se destino assina volta).

    `status_code`: HTTP status do destino, ou None se nao chegou a chamar
        (ex: rejeicao por SSRF guard / DPA).

    `motivo_rejeicao`: preenchido quando `sucesso=False` por defesa propria
        (SSRF, DPA, rebinding, timeout). None quando a chamada saiu e o
        destino respondeu non-2xx (nesse caso, ver `status_code` + `corpo`).

    `corpo`: response body decodificado JSON quando aplicavel; texto cru caso
        contrario; vazio em rejeicao pre-chamada.

    `latencia_ms`: tempo decorrido entre inicio e fim (ou rejeicao).

    `tentativa`: contador 1..N (retry com backoff PERF-002).

    `audit_id`: UUID do registro em audit log (preenchido pelo adapter apos
        commit do log).
    """

    sucesso: bool
    status_code: int | None
    motivo_rejeicao: MotivoRejeicao | None
    corpo: dict[str, Any] | str | None
    latencia_ms: int
    tentativa: int
    audit_id: UUID | None = None


@runtime_checkable
class OutboundWebhookProvider(Protocol):
    """Interface unica de webhooks de saida.

    Cada chamada outbound do sistema DEVE passar por aqui. Hook
    `outbound-webhook-ssrf-check.sh` valida ausencia de uso direto de
    `requests`/`httpx`/`urllib*` em `src/infrastructure/**` fora do adapter.

    Implementacoes:
    - `RequestsWebhookOut` (F-C1 P4): adapter com `requests` + SSRF guard
      manual + HTTPAdapter custom pra DNS rebinding lock.
    - Trocas futuras (httpx async, aiohttp) trocam adapter sem alterar esta
      Protocol.
    """

    def chamar(
        self,
        requisicao: RequisicaoWebhook,
        *,
        timeout_conexao_s: float = 5.0,
        timeout_leitura_s: float = 15.0,
        max_tentativas: int = 3,
    ) -> RespostaWebhook:
        """Executa a chamada outbound com todas as defesas.

        Fluxo:
        1. Carrega `webhook_destino` por `destino_id`. Se desativado, retorna
           `DESTINO_DESATIVADO`.
        2. Valida DPA: `dpa_assinado_em IS NOT NULL`, `dpa_vence_em >= hoje`,
           `chave_expires_at >= hoje`. Caso contrario retorna `DPA_AUSENTE` ou
           `DPA_VENCIDO` ou `HMAC_KEY_VENCIDA`.
        3. Resolve DNS uma vez via `getaddrinfo` (com hostname extraido do
           `url_base + caminho`).
        4. Valida TODOS os IPs A/AAAA contra as 8 faixas proibidas
           (INV-WEBHOOK-OUT-002). Se QUALQUER um cai, retorna o motivo
           especifico (SSRF_IP_*).
        5. Valida porta no allowlist (443 default, 80 opt-in).
        6. Constroi canonical string + HMAC + headers (INV-WEBHOOK-OUT-003).
        7. Connect pelo IP fixado (nao pelo hostname) via HTTPAdapter
           customizado (INV-WEBHOOK-OUT-004 — anti-rebinding).
        8. Aplica timeouts (PERF-002).
        9. Retry com backoff exponencial + jitter ate `max_tentativas`.
        10. Registra audit log (sucesso ou rejeicao).
        """
        ...

    def registrar_destino(
        self,
        *,
        tenant_id: UUID,
        nome: str,
        url_base: str,
        papel_lgpd: str,
        dpa_url: str,
        dpa_assinado_em: datetime,
        dpa_vence_em: datetime,
        finalidade: str,
        categorias_dados: tuple[str, ...],
        chave_hmac_id: str,
        chave_expires_at: datetime,
        criado_por: UUID,
    ) -> UUID:
        """Cadastra novo `webhook_destino`. Retorna `destino_id`."""
        ...

    def desativar_destino(
        self,
        destino_id: UUID,
        *,
        motivo: str,
        desativado_por: UUID,
    ) -> None:
        """Marca destino como desativado (soft-delete). Chamada futura
        retorna `DESTINO_DESATIVADO` sem tentar conectar."""
        ...
