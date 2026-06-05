"""F-C2 Fatia A — logs estruturados + correlation_id automatico.

Prova que:
- o processor injeta correlation_id/tenant_id/usuario_id do contexto (OBS-002);
- nao sobrescreve campo ja presente no `extra=`;
- sem contexto, nao polui o log;
- o ProcessorFormatter renderiza JSON com o contexto + o `extra=` (ExtraAdder);
- o CorrelationIdMiddleware gera/propaga o id + devolve no header + reseta.

Sem DB — processor puro + formatter + middleware com RequestFactory.
"""

from __future__ import annotations

import json
import logging
from uuid import uuid4

import structlog
from django.http import HttpResponse
from django.test import RequestFactory
from src.infrastructure.multitenant.context import (
    active_tenant_context,
    correlation_id_context,
    usuario_id_context,
)
from src.infrastructure.observabilidade.contexto_log import (
    injetar_contexto_observabilidade,
)
from src.infrastructure.observabilidade.logging_config import configurar_logging
from src.infrastructure.observabilidade.middleware import (
    HEADER_CORRELATION_ID,
    CorrelationIdMiddleware,
)


def test_processor_injeta_correlation_e_tenant_e_usuario():
    tid = uuid4()
    uid = uuid4()
    tok_c = correlation_id_context.set("corr-123")
    tok_t = active_tenant_context.set(tid)
    tok_u = usuario_id_context.set(uid)
    try:
        ev = injetar_contexto_observabilidade(None, "info", {"event": "x"})
    finally:
        correlation_id_context.reset(tok_c)
        active_tenant_context.reset(tok_t)
        usuario_id_context.reset(tok_u)
    assert ev["correlation_id"] == "corr-123"
    assert ev["tenant_id"] == str(tid)
    assert ev["usuario_id"] == str(uid)


def test_processor_nao_sobrescreve_campo_explicito():
    tok = correlation_id_context.set("do-contexto")
    try:
        ev = injetar_contexto_observabilidade(
            None, "info", {"event": "x", "correlation_id": "explicito"}
        )
    finally:
        correlation_id_context.reset(tok)
    assert ev["correlation_id"] == "explicito"


def test_processor_sem_contexto_nao_adiciona():
    # Defaults: correlation_id="" / tenant=None / usuario=None -> nada injetado.
    ev = injetar_contexto_observabilidade(None, "info", {"event": "x"})
    assert "correlation_id" not in ev
    assert "tenant_id" not in ev
    assert "usuario_id" not in ev


def _formatter_json() -> logging.Formatter:
    cfg = configurar_logging(json_logs=True)
    f = cfg["formatters"]["estruturado"]
    return structlog.stdlib.ProcessorFormatter(
        processors=f["processors"],
        foreign_pre_chain=f["foreign_pre_chain"],
    )


def test_log_stdlib_renderiza_json_com_contexto_e_extra():
    formatter = _formatter_json()
    record = logging.LogRecord(
        name="teste.fc2", level=logging.INFO, pathname="f.py", lineno=1,
        msg="evento_teste", args=None, exc_info=None,
    )
    record.endpoint = "calibracao.recepcionar"  # simula extra={"endpoint": ...}
    tok = correlation_id_context.set("corr-json")
    try:
        saida = formatter.format(record)
    finally:
        correlation_id_context.reset(tok)
    dados = json.loads(saida)  # 1 linha JSON valida
    assert dados["event"] == "evento_teste"
    assert dados["correlation_id"] == "corr-json"
    assert dados["endpoint"] == "calibracao.recepcionar"  # ExtraAdder pegou
    assert dados["level"] == "info"


def test_middleware_gera_propaga_e_reseta():
    capturado: dict[str, str] = {}

    def get_response(_request):
        capturado["cid"] = correlation_id_context.get()
        return HttpResponse("ok")

    mw = CorrelationIdMiddleware(get_response)
    resp = mw(RequestFactory().get("/qualquer/"))
    assert capturado["cid"]  # setado durante o request
    assert resp[HEADER_CORRELATION_ID] == capturado["cid"]
    # resetado apos o request (nao vaza pro proximo)
    assert correlation_id_context.get() == ""


def test_middleware_reusa_header_seguro():
    capturado: dict[str, str] = {}

    def get_response(_request):
        capturado["cid"] = correlation_id_context.get()
        return HttpResponse("ok")

    mw = CorrelationIdMiddleware(get_response)
    req = RequestFactory().get("/x/", HTTP_X_CORRELATION_ID="abc12345-req-001")
    mw(req)
    assert capturado["cid"] == "abc12345-req-001"


def test_middleware_rejeita_header_inseguro_gera_novo():
    capturado: dict[str, str] = {}

    def get_response(_request):
        capturado["cid"] = correlation_id_context.get()
        return HttpResponse("ok")

    mw = CorrelationIdMiddleware(get_response)
    # header com caractere proibido (espaco/newline) -> nao reusa, gera hex novo
    req = RequestFactory().get("/x/", HTTP_X_CORRELATION_ID="injeta\nmaldoso")
    mw(req)
    assert capturado["cid"] != "injeta\nmaldoso"
    assert len(capturado["cid"]) == 32  # uuid4().hex
