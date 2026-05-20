"""T-CLI-110 — Worker de `bus_outbox` em contexto multi-tenant.

Drena linhas pendentes garantindo INV-TENANT-001..004:
- Entra em `run_in_tenant_context(tenant_id)` ou `run_as_system()`
  (quando `tenant_id IS NULL`) ele mesmo — chamador NAO deve estar em
  contexto.
- Consumer registrado em `_REGISTRY[acao]` recebe o `envelope_jsonb`
  byte-a-byte como foi gravado (golden contract, SUG-3 tech-lead).

Estratégia de transação (T4 tech-lead — 2 transações distintas):
- Tx-1 (curta): SELECT FOR UPDATE SKIP LOCKED + UPDATE
  `tentativas = tentativas + 1, ultimo_erro = NULL` + COMMIT imediato.
  Garante que poison message conta tentativa mesmo se o processo cair
  no meio do dispatch.
- Tx-2: `dispatch_event(envelope)` + UPDATE `processado_em = now()`.
  Se consumer levanta, rollback de `processado_em` mas tentativas ja
  foi contabilizado na Tx-1.
- Tx-3 (curta, condicional): se Tx-2 falhou, grava `ultimo_erro`
  sanitizado fora do rollback.

Contrato de entrega (BLOQ-C tech-lead): **at-least-once**. Consumers
DEVEM ser idempotentes em `envelope['causation_id']` — side-effects
externos (HTTP, fiscal, e-mail) registram tabela
`consumer_idempotencia(consumer_name, causation_id)` UNIQUE com
ON CONFLICT DO NOTHING antes do side-effect.

Ordering NAO é preservado (BLOQ-D tech-lead — non-goal Wave A). `SKIP
LOCKED` quebra ordem causal; saga pattern é responsabilidade do
consumer Wave A.

# tests-coverage: tests/test_outbox_worker_t_cli_110.py
"""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any
from uuid import UUID

from django.db import connection

from src.infrastructure.audit.services import (
    _RE_CNPJ_AUDIT,
    _RE_CPF_AUDIT,
    _RE_EMAIL_AUDIT,
    _RE_TELEFONE_AUDIT,
)
from src.infrastructure.multitenant.connection import (
    run_as_system,
    run_in_tenant_context,
)
from src.infrastructure.multitenant.context import active_tenant_context

# =============================================================
# Sanitização de erro (BLOQ-A4 advogado)
# =============================================================
_LIMITE_ULTIMO_ERRO = 500


def sanitizar_erro_para_outbox(exc: BaseException) -> str:
    """Converte exceção em texto seguro pra coluna `bus_outbox.ultimo_erro`.

    Garantias (BLOQ-A4 advogado):
    1. Tipo + 1ª linha da mensagem (não stack trace completo).
    2. Substitui CPF/CNPJ/email/telefone INLINE por `[REDACTED]`
       (preserva o tipo do erro pra diagnóstico). Importante:
       `sanitizar_payload_audit` redata a STRING INTEIRA quando acha
       PII — pra `ultimo_erro` precisamos substituição inline pra
       não perder a info do tipo da exceção.
    3. Trunca em `_LIMITE_ULTIMO_ERRO` caracteres com sufixo
       `...[truncado]`.
    """
    tipo = type(exc).__name__
    msg_completa = str(exc)
    msg = msg_completa.splitlines()[0] if msg_completa else ""
    bruto = f"{tipo}: {msg}" if msg else tipo
    # Substituição INLINE preservando estrutura da mensagem
    sanitizado = bruto
    for regex in (_RE_CPF_AUDIT, _RE_CNPJ_AUDIT, _RE_EMAIL_AUDIT, _RE_TELEFONE_AUDIT):
        sanitizado = regex.sub("[REDACTED]", sanitizado)
    if len(sanitizado) > _LIMITE_ULTIMO_ERRO:
        sanitizado = sanitizado[: _LIMITE_ULTIMO_ERRO - 14] + "...[truncado]"
    return sanitizado


# =============================================================
# Registry de consumers (ponto de extensão)
# =============================================================
_REGISTRY: dict[str, Callable[[dict[str, Any]], None]] = {}


def registrar_consumer(acao: str, fn: Callable[[dict[str, Any]], None]) -> None:
    """Registra consumer para `acao`. Lança ValueError se já houver."""
    if acao in _REGISTRY:
        raise ValueError(
            f"consumer ja registrado para acao={acao} — desregistre primeiro "
            "via `_REGISTRY.pop` (uso interno) ou use fixture de teste "
            "`clear_outbox_registry`."
        )
    _REGISTRY[acao] = fn


def _noop(envelope: dict[str, Any]) -> None:
    """Default quando nenhum consumer está registrado para a acao."""


def dispatch_event(envelope: dict[str, Any]) -> None:
    """Invoca consumer registrado pra `envelope['acao']`. Default = noop."""
    acao = envelope.get("acao", "")
    fn = _REGISTRY.get(acao, _noop)
    fn(envelope)


# =============================================================
# Resultado do worker
# =============================================================
@dataclass(frozen=True)
class ResultadoOutbox:
    """Resultado de `processar_outbox_em_contexto_tenant`.

    `status`:
    - `processada`: dispatch OK + `processado_em` setado.
    - `falhou`: dispatch levantou; `tentativas` incrementado, `ultimo_erro`
       gravado, `processado_em` continua NULL.
    - `ja_processada_ou_lockada`: SELECT FOR UPDATE SKIP LOCKED retornou
       0 linhas (outro worker pegou ou já foi processado).
    """

    linha_id: UUID
    status: str
    erro: str | None = None


class _ErroConsumer(Exception):
    """Wrapper interno pra carregar `linha_id` e mensagem sanitizada pra Tx-3."""

    def __init__(self, linha_id: Any, erro: str) -> None:
        self.linha_id = linha_id
        self.erro = erro
        super().__init__(erro)


# =============================================================
# Driver principal — processar_outbox_em_contexto_tenant
# =============================================================
def processar_outbox_em_contexto_tenant(linha_id: UUID) -> ResultadoOutbox:
    """Processa UMA linha do outbox em contexto multi-tenant correto.

    Pré-condição: chamado FORA de qualquer `run_in_tenant_context`. Se
    já estiver em contexto, fail-loud — evita "trocar de tenant no meio".
    """
    if active_tenant_context.get(None) is not None:
        raise RuntimeError(
            "processar_outbox_em_contexto_tenant chamado dentro de "
            "run_in_tenant_context — worker deve entrar no contexto certo "
            "ele mesmo (proteção contra troca de tenant no meio)."
        )

    # =============================================================
    # Tx-1: lockeia + incrementa tentativas + commit imediato.
    # =============================================================
    with run_as_system():
        with connection.cursor() as cur:
            cur.execute(
                "SELECT id, tenant_id, acao, envelope_jsonb, tentativas "
                "FROM bus_outbox "
                "WHERE id = %s AND processado_em IS NULL "
                "FOR UPDATE SKIP LOCKED",
                [str(linha_id)],
            )
            row = cur.fetchone()
            if row is None:
                return ResultadoOutbox(linha_id=linha_id, status="ja_processada_ou_lockada")
            id_, tenant_id, acao, envelope_raw, _tentativas = row
            # Cursor cru retorna jsonb como str (sem adapter do ORM).
            envelope: dict[str, Any] = (
                envelope_raw if isinstance(envelope_raw, dict) else json.loads(envelope_raw)
            )
            cur.execute(
                "UPDATE bus_outbox SET tentativas = tentativas + 1, "
                "ultimo_erro = NULL WHERE id = %s",
                [id_],
            )
        # commit da Tx-1 ao sair do `run_as_system` (e do `transaction.atomic`)

    # =============================================================
    # Tx-2: dispatch + marca processado.
    # =============================================================
    try:
        if tenant_id is None:
            _executar_dispatch_em_modo_sistema(id_, envelope)
        else:
            _executar_dispatch_em_tenant(UUID(str(tenant_id)), id_, envelope)
        return ResultadoOutbox(linha_id=linha_id, status="processada")
    except _ErroConsumer as wrapped:
        # =============================================================
        # Tx-3 (curta): grava ultimo_erro fora do rollback da Tx-2.
        # =============================================================
        with run_as_system():
            with connection.cursor() as cur:
                cur.execute(
                    "UPDATE bus_outbox SET ultimo_erro = %s WHERE id = %s",
                    [wrapped.erro, wrapped.linha_id],
                )
        return ResultadoOutbox(linha_id=linha_id, status="falhou", erro=wrapped.erro)


def _executar_dispatch_em_modo_sistema(linha_id: Any, envelope: dict[str, Any]) -> None:
    with run_as_system():
        _dispatch_e_marca(linha_id, envelope)


def _executar_dispatch_em_tenant(tenant_id: UUID, linha_id: Any, envelope: dict[str, Any]) -> None:
    with run_in_tenant_context(tenant_id):
        _dispatch_e_marca(linha_id, envelope)


def _dispatch_e_marca(linha_id: Any, envelope: dict[str, Any]) -> None:
    """Dentro do contexto (sistema OU tenant): dispatch + marca processado.

    Se consumer levanta, levanta `_ErroConsumer` pra Tx-3 gravar
    `ultimo_erro` fora do rollback. `processado_em` fica NULL.
    """
    try:
        dispatch_event(envelope)
        with connection.cursor() as cur:
            cur.execute(
                "UPDATE bus_outbox SET processado_em = now() WHERE id = %s",
                [linha_id],
            )
    except Exception as exc:
        # Re-empacota com mensagem sanitizada antes de subir (rollback Tx-2)
        raise _ErroConsumer(linha_id=linha_id, erro=sanitizar_erro_para_outbox(exc)) from exc


# =============================================================
# Driver `drenar_outbox` — BLOQ-B + MED-3 tech-lead
# =============================================================
def drenar_outbox(limit: int = 100) -> list[ResultadoOutbox]:
    """Drena até `limit` linhas pendentes do outbox.

    BLOQ-B: filtra `tentativas < 5` — linhas envenenadas viram visíveis
    no management command `listar_outbox_envenenado` e param de drenar.

    MED-3: pega IDs sem lock; helper individual lockeia cada linha no
    SELECT FOR UPDATE SKIP LOCKED interno (Tx-1).

    Wave A pluga este `drenar_outbox` num cron Procrastinate. Marco 1
    invoca via management command `drenar_outbox_uma_vez` (manual).
    """
    with run_as_system():
        with connection.cursor() as cur:
            cur.execute(
                "SELECT id FROM bus_outbox "
                "WHERE processado_em IS NULL AND tentativas < 5 "
                "ORDER BY criado_em LIMIT %s",
                [limit],
            )
            ids = [row[0] for row in cur.fetchall()]
    resultados: list[ResultadoOutbox] = []
    for id_ in ids:
        # Cada chamada abre seu próprio run_as_system/tenant — não pode
        # estar dentro de outro contexto, daí saímos do run_as_system
        # acima antes de iterar.
        resultados.append(processar_outbox_em_contexto_tenant(UUID(str(id_))))
    return resultados


# =============================================================
# Helper de teste — reset do registry entre testes (SUG-4 tech-lead)
# =============================================================
def _resetar_registry_para_testes() -> None:
    """Uso EXCLUSIVO de fixtures pytest (`clear_outbox_registry` autouse).

    Não invocar em runtime — registry é cravado no startup
    (`AppConfig.ready()`) em Wave A.
    """
    _REGISTRY.clear()
