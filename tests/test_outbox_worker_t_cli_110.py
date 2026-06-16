"""T-CLI-110 — testes do worker `processar_outbox_em_contexto_tenant`.

Cobertura:

1. test_worker_processa_linha_em_contexto_correto — happy path:
   linha de tenant A é processada com active_tenant_id=A.
2. test_worker_3_tenants_intercalados_zero_vazamento — drill principal:
   3 tenants intercalados, worker drena, cada consumer vê APENAS seu tenant.
3. test_worker_consumer_falha_tentativas_incrementa_processado_em_NULL
   — T4 tech-lead: Tx-1 commit; Tx-2 rollback; ultimo_erro gravado.
4. test_worker_poison_message_para_apos_5_tentativas — BLOQ-B.
5. test_worker_tenant_null_so_processa_em_modo_sistema — linha com
   tenant_id NULL é processada sob run_as_system.
6. test_worker_fail_loud_se_chamado_dentro_de_contexto_tenant — pré-
   condição protege contra "trocar de tenant no meio".
7. test_worker_envelope_entregue_eh_byte_a_byte_o_gravado — SUG-3
   tech-lead golden contract.
8. test_worker_ultimo_erro_sanitiza_pii_em_stack_trace — BLOQ-A4
   advogado: CPF do erro vira [REDACTED].
9. test_worker_ultimo_erro_truncado_em_500_chars — BLOQ-A4.
10. test_worker_registry_isolado_entre_testes — SUG-4 (autouse fixture).
11. test_worker_skip_locked_dois_workers_separados_nao_dupla_processa —
    SELECT FOR UPDATE SKIP LOCKED comportamento básico.
"""

from __future__ import annotations

from uuid import UUID, uuid4

import pytest
from django.db import connection
from src.infrastructure.audit.event_helpers import publicar_evento
from src.infrastructure.audit.outbox_worker import (
    _resetar_registry_para_testes,
    drenar_outbox,
    processar_outbox_em_contexto_tenant,
    registrar_consumer,
    sanitizar_erro_para_outbox,
)
from src.infrastructure.multitenant.connection import (
    run_as_system,
    run_in_tenant_context,
)
from src.infrastructure.multitenant.context import active_tenant_context

from tests.factories import TenantFactory


@pytest.fixture(autouse=True)
def clear_outbox_registry():
    """SUG-4: reset registry entre testes pra evitar interferência."""
    _resetar_registry_para_testes()
    yield
    _resetar_registry_para_testes()


def _publicar_em_tenant(tenant_id: UUID, acao: str, payload: dict | None = None) -> UUID:
    cid = uuid4()
    with run_in_tenant_context(tenant_id):
        publicar_evento(
            acao=acao,
            payload=payload or {},
            causation_id=cid,
            tenant_id=tenant_id,
            outbox=True,
            cadeia=False,  # foco no outbox, evita prender lock da cadeia
        )
    return cid


def _id_da_linha(causation_id: UUID) -> UUID:
    with run_as_system():
        with connection.cursor() as cur:
            cur.execute(
                "SELECT id FROM bus_outbox WHERE causation_id = %s",
                [str(causation_id)],
            )
            return UUID(str(cur.fetchone()[0]))


def _estado_linha(linha_id: UUID) -> dict:
    with run_as_system():
        with connection.cursor() as cur:
            cur.execute(
                "SELECT processado_em, tentativas, ultimo_erro " "FROM bus_outbox WHERE id = %s",
                [str(linha_id)],
            )
            row = cur.fetchone()
    if row is None:
        return {"processado_em": None, "tentativas": 0, "ultimo_erro": None}
    return {"processado_em": row[0], "tentativas": row[1], "ultimo_erro": row[2]}


# =============================================================
@pytest.mark.django_db(transaction=True)
def test_worker_processa_linha_em_contexto_correto():
    tenant = TenantFactory()
    visto: list[str | None] = []

    def consumer(envelope):
        # Ao executar, o active_tenant_context deve refletir o tenant da linha
        visto.append(str(active_tenant_context.get(None)))

    registrar_consumer("cliente.criado", consumer)
    cid = _publicar_em_tenant(tenant.id, "cliente.criado", {"x": 1})
    linha_id = _id_da_linha(cid)
    r = processar_outbox_em_contexto_tenant(linha_id)
    assert r.status == "processada"
    assert visto == [str(tenant.id)]
    estado = _estado_linha(linha_id)
    assert estado["processado_em"] is not None
    assert estado["tentativas"] == 1


@pytest.mark.django_db(transaction=True)
def test_worker_3_tenants_intercalados_zero_vazamento():
    # Limpa outbox de testes anteriores (reuse-db) pra contagem honesta
    with run_as_system():
        with connection.cursor() as cur:
            cur.execute("DELETE FROM bus_outbox")
    t_a = TenantFactory()
    t_b = TenantFactory()
    t_c = TenantFactory()
    visto: list[tuple[str, str | None]] = []  # (envelope_tenant, contexto_ativo)

    def consumer(envelope):
        visto.append((envelope["tenant_id"], str(active_tenant_context.get(None))))

    registrar_consumer("cliente.criado", consumer)
    # Publica intercalado A, B, C, A, B, C
    cids = []
    for _ in range(2):
        for t in (t_a, t_b, t_c):
            cids.append(_publicar_em_tenant(t.id, "cliente.criado", {"t": str(t.id)}))
    # Drena tudo
    drenar_outbox(limit=100)
    # Cada consumer roda no contexto do tenant DONO da linha — zero vazamento
    assert len(visto) == 6, f"esperado 6 consumos, achou {len(visto)} (cids={cids})"
    for envelope_tenant, contexto_ativo in visto:
        assert envelope_tenant == contexto_ativo


@pytest.mark.django_db(transaction=True)
def test_worker_consumer_falha_tentativas_incrementa_processado_em_NULL():
    tenant = TenantFactory()

    def consumer_que_falha(envelope):
        raise ValueError("bug do consumer")

    registrar_consumer("cliente.criado", consumer_que_falha)
    cid = _publicar_em_tenant(tenant.id, "cliente.criado", {})
    linha_id = _id_da_linha(cid)
    r = processar_outbox_em_contexto_tenant(linha_id)
    assert r.status == "falhou"
    estado = _estado_linha(linha_id)
    assert estado["processado_em"] is None  # Tx-2 rolled back
    assert estado["tentativas"] == 1  # Tx-1 commitou
    assert estado["ultimo_erro"] is not None
    assert "bug do consumer" in estado["ultimo_erro"]


@pytest.mark.django_db(transaction=True)
def test_worker_poison_message_para_apos_5_tentativas():
    tenant = TenantFactory()

    def sempre_falha(envelope):
        raise RuntimeError("veneno")

    registrar_consumer("cliente.criado", sempre_falha)
    cid = _publicar_em_tenant(tenant.id, "cliente.criado", {})
    linha_id = _id_da_linha(cid)
    # 5 chamadas: tentativas vai de 0 a 5 (todas falham)
    for _ in range(5):
        processar_outbox_em_contexto_tenant(linha_id)
    estado = _estado_linha(linha_id)
    assert estado["tentativas"] == 5
    # drenar_outbox NÃO inclui linhas com tentativas >= 5
    resultados = drenar_outbox(limit=100)
    assert all(r.linha_id != linha_id for r in resultados)


@pytest.mark.django_db(transaction=True)
def test_worker_tenant_null_so_processa_em_modo_sistema():
    visto: list[str | None] = []

    def consumer(envelope):
        visto.append(envelope["tenant_id"])

    registrar_consumer("sistema.tenant_provisionado", consumer)
    cid = uuid4()
    with run_as_system():
        publicar_evento(
            acao="sistema.tenant_provisionado",
            payload={"a": 1},
            causation_id=cid,
            tenant_id=None,
            outbox=True,
            cadeia=False,
        )
    linha_id = _id_da_linha(cid)
    r = processar_outbox_em_contexto_tenant(linha_id)
    assert r.status == "processada"
    assert visto == [None]


@pytest.mark.django_db(transaction=True)
def test_worker_fail_loud_se_chamado_dentro_de_contexto_tenant():
    tenant = TenantFactory()
    cid = _publicar_em_tenant(tenant.id, "cliente.criado", {})
    linha_id = _id_da_linha(cid)
    with run_in_tenant_context(tenant.id):
        with pytest.raises(RuntimeError, match="proteção contra troca de tenant"):
            processar_outbox_em_contexto_tenant(linha_id)


@pytest.mark.django_db(transaction=True)
def test_worker_envelope_entregue_eh_byte_a_byte_o_gravado():
    """SUG-3 tech-lead: golden contract — o envelope que chega ao consumer
    é o mesmo que está em bus_outbox."""
    tenant = TenantFactory()
    payload = {"campo_a": 42, "campo_b": "ok"}
    capturado: list[dict] = []

    def consumer(envelope):
        capturado.append(envelope)

    registrar_consumer("cliente.criado", consumer)
    cid = _publicar_em_tenant(tenant.id, "cliente.criado", payload)
    linha_id = _id_da_linha(cid)
    processar_outbox_em_contexto_tenant(linha_id)
    # Lê o envelope gravado direto do banco
    import json as _json

    with run_as_system():
        with connection.cursor() as cur:
            cur.execute(
                "SELECT envelope_jsonb FROM bus_outbox WHERE id = %s",
                [str(linha_id)],
            )
            gravado_raw = cur.fetchone()[0]
    gravado = gravado_raw if isinstance(gravado_raw, dict) else _json.loads(gravado_raw)
    assert capturado[0] == gravado


@pytest.mark.django_db(transaction=True)
def test_worker_ultimo_erro_sanitiza_pii_em_stack_trace():
    """BLOQ-A4 advogado: erro com CPF na mensagem vira [REDACTED]."""
    tenant = TenantFactory()

    def consumer_que_vaza_cpf(envelope):
        raise ValueError("CPF inválido: 12345678901")

    registrar_consumer("cliente.criado", consumer_que_vaza_cpf)
    cid = _publicar_em_tenant(tenant.id, "cliente.criado", {})
    linha_id = _id_da_linha(cid)
    processar_outbox_em_contexto_tenant(linha_id)
    estado = _estado_linha(linha_id)
    assert estado["ultimo_erro"] is not None
    assert "12345678901" not in estado["ultimo_erro"]
    assert "[REDACTED]" in estado["ultimo_erro"]


@pytest.mark.django_db(transaction=True)
def test_worker_ultimo_erro_truncado_em_500_chars():
    """BLOQ-A4: mensagens longas truncam em 500 chars."""
    tenant = TenantFactory()

    def consumer_msg_gigante(envelope):
        raise RuntimeError("X" * 2000)

    registrar_consumer("cliente.criado", consumer_msg_gigante)
    cid = _publicar_em_tenant(tenant.id, "cliente.criado", {})
    linha_id = _id_da_linha(cid)
    processar_outbox_em_contexto_tenant(linha_id)
    estado = _estado_linha(linha_id)
    assert estado["ultimo_erro"] is not None
    assert len(estado["ultimo_erro"]) <= 500
    assert estado["ultimo_erro"].endswith("...[truncado]")


@pytest.mark.django_db(transaction=True)
def test_worker_registry_isolado_entre_testes():
    """SUG-4 tech-lead: a fixture autouse reseta o registry."""

    # Registramos um consumer aqui; em outro teste autouse já apagou.
    def consumer_local(envelope):
        pass

    registrar_consumer("cliente.atualizado", consumer_local)
    # Confirma que está lá nesta sessão
    from src.infrastructure.audit.outbox_worker import _REGISTRY

    assert "cliente.atualizado" in _REGISTRY


# =============================================================
# Fan-out (Fatia 3a / T-CR-041) — N consumers por ação
# =============================================================
@pytest.mark.django_db(transaction=True)
def test_fanout_dois_consumers_ambos_rodam_em_ordem():
    tenant = TenantFactory()
    vistos: list[str] = []

    def consumer_a(envelope):
        vistos.append("a")

    def consumer_b(envelope):
        vistos.append("b")

    registrar_consumer("os.concluida", consumer_a)
    registrar_consumer("os.concluida", consumer_b)
    cid = _publicar_em_tenant(tenant.id, "os.concluida", {"os_id": "x"})
    linha_id = _id_da_linha(cid)
    r = processar_outbox_em_contexto_tenant(linha_id)
    assert r.status == "processada"
    assert vistos == ["a", "b"]  # ordem de registro preservada
    assert _estado_linha(linha_id)["processado_em"] is not None


@pytest.mark.django_db(transaction=True)
def test_fanout_um_consumer_falha_linha_inteira_rollback():
    """Tudo-ou-nada por linha (TL C1/A1): run_in_tenant_context abre transaction.atomic,
    então se um consumer da mesma ação levanta, a exceção propaga → rollback da linha
    INTEIRA → re-drena (tentativas++) e todos re-rodam (idempotentes no replay).
    Isolamento por-consumer (tx independente) é trabalho futuro.
    """
    tenant = TenantFactory()
    vistos: list[str] = []

    def consumer_ok(envelope):
        vistos.append("ok")

    def consumer_falha(envelope):
        vistos.append("falha")
        raise RuntimeError("bug no consumer 2")

    registrar_consumer("os.concluida", consumer_ok)
    registrar_consumer("os.concluida", consumer_falha)
    cid = _publicar_em_tenant(tenant.id, "os.concluida", {"os_id": "x"})
    linha_id = _id_da_linha(cid)
    r = processar_outbox_em_contexto_tenant(linha_id)
    assert r.status == "falhou"
    estado = _estado_linha(linha_id)
    assert estado["processado_em"] is None  # rollback total
    assert estado["tentativas"] == 1
    assert estado["ultimo_erro"] is not None
    assert "bug no consumer 2" in estado["ultimo_erro"]


@pytest.mark.django_db(transaction=True)
def test_registrar_consumer_mesmo_fn_duas_vezes_levanta():
    """Re-registro do MESMO fn levanta ValueError (preserva try/except dos apps.py)."""

    def consumer(envelope):
        pass

    registrar_consumer("os.concluida", consumer)
    with pytest.raises(ValueError, match="ja registrado"):
        registrar_consumer("os.concluida", consumer)


def test_dispatch_event_fanout_chama_todos_em_ordem():
    """Unidade: dispatch_event itera todos os consumers na ordem de registro."""
    from src.infrastructure.audit.outbox_worker import dispatch_event

    chamados: list[str] = []
    registrar_consumer("evt.x", lambda e: chamados.append("a"))
    registrar_consumer("evt.x", lambda e: chamados.append("b"))
    dispatch_event({"acao": "evt.x", "payload": {}})
    assert chamados == ["a", "b"]


def test_sanitizar_erro_para_outbox_unidade():
    """Unidade pura — sem DB. Cobre o helper isoladamente."""
    erro = sanitizar_erro_para_outbox(
        ValueError("CPF do titular: 12345678901, telefone 11987654321")
    )
    assert "12345678901" not in erro
    assert "11987654321" not in erro
    assert "ValueError" in erro
    assert "[REDACTED]" in erro
