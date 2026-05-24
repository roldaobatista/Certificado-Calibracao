"""HttpxWebhookOut — adapter canonico OutboundWebhookProvider (F-C1 P4).

Implementa o Protocol `OutboundWebhookProvider` integrando:
- ssrf_guard: validacao de IP/hostname/porta antes do connect (INV-WEBHOOK-OUT-002)
- hmac_sign: canonical string + HMAC + headers (INV-WEBHOOK-OUT-003)
- models.WebhookDestino: cadastro DPA + chave HMAC (INV-WEBHOOK-OUT-005)
- httpx Transport custom: connect pelo IP fixado (INV-WEBHOOK-OUT-004 anti-rebinding)

Retry com backoff exponencial + jitter (PERF-002).
Timeouts obrigatorios (conn=5s default, read=15s default).
"""

from __future__ import annotations

import json
import logging
import random
import socket
import time
from dataclasses import dataclass
from datetime import date
from typing import Any
from uuid import UUID, uuid4

import httpx
from django.utils import timezone

from src.domain.shared.webhook_out_provider import (
    MotivoRejeicao,
    OutboundWebhookProvider,
    RequisicaoWebhook,
    RespostaWebhook,
)
from src.infrastructure.webhook_out import hmac_sign, ssrf_guard
from src.infrastructure.webhook_out.models import WebhookDestino

logger = logging.getLogger(__name__)


class _IpFixadoTransport(httpx.HTTPTransport):
    """Transport httpx que fixa o IP de destino (anti-DNS-rebinding).

    Substitui o hostname pelo IP resolvido antes de delegar pro transport
    padrao. O HTTPS continua validando o certificado pelo HOSTNAME original
    (SNI + cert hostname) via header `Host` preservado.
    """

    def __init__(self, ip_fixado: str, hostname_original: str, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._ip_fixado = ip_fixado
        self._hostname_original = hostname_original

    def handle_request(self, request: httpx.Request) -> httpx.Response:
        # Reescreve URL: hostname -> IP fixado, mas mantem Host header
        original_url = request.url
        novo_host = self._ip_fixado
        # IPv6 precisa de [bracketing] na URL
        if ":" in self._ip_fixado:
            novo_host = f"[{self._ip_fixado}]"
        nova_url = original_url.copy_with(host=novo_host)
        request.url = nova_url
        request.headers["Host"] = self._hostname_original
        return super().handle_request(request)


@dataclass(frozen=True)
class _ContextoChamada:
    """Dados resolvidos uma vez no inicio da chamada (evita re-resolver)."""

    destino: WebhookDestino
    chave_hmac_bytes: bytes
    url_completa: str
    resultado_ssrf: ssrf_guard.ResultadoSsrfGuard


class HttpxWebhookOut(OutboundWebhookProvider):
    """Implementacao canonica do Protocol.

    Construido com:
        carregar_chave: callable(chave_hmac_id) -> bytes. Em F-C1 dogfooding,
            lookup em env var. Em F-C3 produtivo, lookup em KMS.
    """

    def __init__(self, carregar_chave) -> None:
        self._carregar_chave = carregar_chave

    # =========================================================
    # Protocol — chamar
    # =========================================================
    def chamar(
        self,
        requisicao: RequisicaoWebhook,
        *,
        timeout_conexao_s: float = 5.0,
        timeout_leitura_s: float = 15.0,
        max_tentativas: int = 3,
    ) -> RespostaWebhook:
        inicio = time.monotonic()

        # 1. Carrega destino (RLS aplicado via middleware multi-tenant)
        try:
            destino = WebhookDestino.objects.get(
                id=requisicao.destino_id,
                tenant_id=requisicao.tenant_id,
            )
        except WebhookDestino.DoesNotExist:
            return self._rejeitar(
                MotivoRejeicao.DESTINO_DESATIVADO,
                requisicao,
                inicio,
                tentativa=1,
            )

        # 2. Destino desativado?
        if not destino.esta_ativo:
            return self._rejeitar(
                MotivoRejeicao.DESTINO_DESATIVADO, requisicao, inicio, tentativa=1
            )

        # 3. DPA vigente?
        hoje = date.today()
        if destino.dpa_assinado_em is None:
            return self._rejeitar(MotivoRejeicao.DPA_AUSENTE, requisicao, inicio, tentativa=1)
        if destino.dpa_vence_em < hoje:
            return self._rejeitar(MotivoRejeicao.DPA_VENCIDO, requisicao, inicio, tentativa=1)
        if destino.chave_expires_at < hoje:
            return self._rejeitar(
                MotivoRejeicao.HMAC_KEY_VENCIDA, requisicao, inicio, tentativa=1
            )

        # 4. SSRF guard (resolve DNS UMA vez)
        url_completa = self._montar_url(destino.url_base, requisicao.caminho)
        resultado_ssrf = ssrf_guard.validar_url(
            url_completa, permite_http=destino.permite_http
        )
        if not resultado_ssrf.permitido:
            return self._rejeitar(
                resultado_ssrf.motivo or MotivoRejeicao.SSRF_DNS_INTERNO,
                requisicao,
                inicio,
                tentativa=1,
            )

        # 5. Carrega chave HMAC + assina
        chave_bytes = self._carregar_chave(destino.chave_hmac_id)
        ctx = _ContextoChamada(
            destino=destino,
            chave_hmac_bytes=chave_bytes,
            url_completa=url_completa,
            resultado_ssrf=resultado_ssrf,
        )

        # 6. Retry com backoff exponencial + jitter
        ultima_resposta: RespostaWebhook | None = None
        for tentativa in range(1, max_tentativas + 1):
            ultima_resposta = self._executar_uma_vez(
                requisicao,
                ctx,
                tentativa=tentativa,
                timeout_conexao_s=timeout_conexao_s,
                timeout_leitura_s=timeout_leitura_s,
                inicio_total=inicio,
            )
            if ultima_resposta.sucesso:
                return ultima_resposta
            # Nao retentar rejeicoes "permanentes" (SSRF/DPA — nao saem da
            # logica acima de qualquer forma; aqui so erra rede/timeout)
            if ultima_resposta.motivo_rejeicao in (
                MotivoRejeicao.DPA_AUSENTE,
                MotivoRejeicao.DPA_VENCIDO,
                MotivoRejeicao.HMAC_KEY_VENCIDA,
                MotivoRejeicao.DESTINO_DESATIVADO,
            ):
                return ultima_resposta
            if tentativa < max_tentativas:
                # Backoff exponencial + jitter (0.5*2^n + random[0,0.5])
                espera = (0.5 * (2 ** (tentativa - 1))) + (random.random() * 0.5)
                time.sleep(espera)

        assert ultima_resposta is not None
        return ultima_resposta

    # =========================================================
    # Protocol — registrar_destino
    # =========================================================
    def registrar_destino(
        self,
        *,
        tenant_id: UUID,
        nome: str,
        url_base: str,
        papel_lgpd: str,
        dpa_url: str,
        dpa_assinado_em,
        dpa_vence_em,
        finalidade: str,
        categorias_dados: tuple[str, ...],
        chave_hmac_id: str,
        chave_expires_at,
        criado_por: UUID,
    ) -> UUID:
        destino = WebhookDestino.objects.create(
            tenant_id=tenant_id,
            nome=nome,
            url_base=url_base,
            papel_lgpd=papel_lgpd,
            dpa_url=dpa_url,
            dpa_assinado_em=dpa_assinado_em,
            dpa_vence_em=dpa_vence_em,
            finalidade=finalidade,
            categorias_dados=list(categorias_dados),
            chave_hmac_id=chave_hmac_id,
            chave_expires_at=chave_expires_at,
            criado_por=criado_por,
        )
        return destino.id

    # =========================================================
    # Protocol — desativar_destino
    # =========================================================
    def desativar_destino(
        self, destino_id: UUID, *, motivo: str, desativado_por: UUID
    ) -> None:
        WebhookDestino.objects.filter(id=destino_id, desativado_em__isnull=True).update(
            desativado_em=timezone.now(),
            desativado_por=desativado_por,
            desativado_motivo=motivo,
        )

    # =========================================================
    # Internos
    # =========================================================
    def _executar_uma_vez(
        self,
        requisicao: RequisicaoWebhook,
        ctx: _ContextoChamada,
        *,
        tentativa: int,
        timeout_conexao_s: float,
        timeout_leitura_s: float,
        inicio_total: float,
    ) -> RespostaWebhook:
        # Serializa body
        body_bytes = b""
        if requisicao.corpo is not None:
            body_bytes = json.dumps(requisicao.corpo).encode("utf-8")

        # Assina
        cabecalhos = hmac_sign.assinar(
            metodo=requisicao.metodo,
            caminho=requisicao.caminho,
            body_bytes=body_bytes,
            chave_hmac=ctx.chave_hmac_bytes,
            event_id=requisicao.event_id,
        ).como_dict()
        cabecalhos["Content-Type"] = "application/json"
        if requisicao.correlation_id is not None:
            cabecalhos["X-Afere-Correlation-Id"] = str(requisicao.correlation_id)

        # Connect pelo IP FIXADO (anti-rebinding)
        primeiro_ip = ctx.resultado_ssrf.ips_resolvidos[0]
        transport = _IpFixadoTransport(
            ip_fixado=primeiro_ip,
            hostname_original=ctx.resultado_ssrf.hostname,
        )
        timeout = httpx.Timeout(
            connect=timeout_conexao_s,
            read=timeout_leitura_s,
            write=timeout_leitura_s,
            pool=timeout_conexao_s,
        )

        try:
            with httpx.Client(transport=transport, timeout=timeout, verify=True) as client:
                response = client.request(
                    method=requisicao.metodo,
                    url=ctx.url_completa,
                    content=body_bytes if body_bytes else None,
                    headers=cabecalhos,
                )
        except httpx.ConnectTimeout:
            return RespostaWebhook(
                sucesso=False,
                status_code=None,
                motivo_rejeicao=MotivoRejeicao.TIMEOUT_CONEXAO,
                corpo=None,
                latencia_ms=int((time.monotonic() - inicio_total) * 1000),
                tentativa=tentativa,
            )
        except (httpx.ReadTimeout, httpx.WriteTimeout):
            return RespostaWebhook(
                sucesso=False,
                status_code=None,
                motivo_rejeicao=MotivoRejeicao.TIMEOUT_LEITURA,
                corpo=None,
                latencia_ms=int((time.monotonic() - inicio_total) * 1000),
                tentativa=tentativa,
            )

        # Decodifica response body se for JSON
        corpo_decodificado: dict[str, Any] | str | None = response.text
        ct = response.headers.get("content-type", "")
        if ct.startswith("application/json"):
            try:
                corpo_decodificado = response.json()
            except json.JSONDecodeError:
                pass

        sucesso = 200 <= response.status_code < 300
        return RespostaWebhook(
            sucesso=sucesso,
            status_code=response.status_code,
            motivo_rejeicao=None,
            corpo=corpo_decodificado,
            latencia_ms=int((time.monotonic() - inicio_total) * 1000),
            tentativa=tentativa,
        )

    def _rejeitar(
        self,
        motivo: MotivoRejeicao,
        requisicao: RequisicaoWebhook,
        inicio_monotonic: float,
        *,
        tentativa: int,
    ) -> RespostaWebhook:
        logger.warning(
            "webhook_out rejeitado: motivo=%s destino_id=%s event_id=%s tenant_id=%s",
            motivo,
            requisicao.destino_id,
            requisicao.event_id,
            requisicao.tenant_id,
        )
        return RespostaWebhook(
            sucesso=False,
            status_code=None,
            motivo_rejeicao=motivo,
            corpo=None,
            latencia_ms=int((time.monotonic() - inicio_monotonic) * 1000),
            tentativa=tentativa,
        )

    @staticmethod
    def _montar_url(url_base: str, caminho: str) -> str:
        base = url_base.rstrip("/")
        path = caminho if caminho.startswith("/") else f"/{caminho}"
        return f"{base}{path}"
