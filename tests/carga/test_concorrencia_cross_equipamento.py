"""Teste de carga — concorrencia cross-equipamento (AC-OSME-005).

Valida 2 propriedades do indice unique partial `idx_atividade_em_execucao_por_equip`
criado pelo retrofit os-multi-equipamento (ADR-0082):

    CREATE UNIQUE INDEX idx_atividade_em_execucao_por_equip
      ON atividade_da_os (tenant_id, equipamento_id)
      WHERE estado='em_execucao' AND tipo_bloqueia_concorrencia=true;

AC-OSME-005-1 (sem falso-412): numa MESMA OS, 2 atividades bloqueantes de
  equipamentos DISTINTOS -> ambas chegam a EM_EXECUCAO simultaneamente, sem
  IntegrityError. O indice nao conflita porque a chave (tenant_id, equipamento_id)
  eh diferente para cada atividade.

AC-OSME-005-2 (serializa mesmo equipamento): 2 atividades bloqueantes do MESMO
  equipamento tentando EM_EXECUCAO simultaneamente -> exatamente 1 sucede; a
  outra recebe IntegrityError do banco. Garante que o indice serializa acesso
  por equipamento mesmo sob carga.

Molde de concorrencia: cada thread abre conexao propria (close() no finally),
usa transaction.atomic() isolado, e deposita resultado/excecao numa lista
thread-safe. Assertivas rodam na thread principal apos join().

GATE VERMELHO: se AC-OSME-005-1 falhar (IntegrityError para equipamentos
distintos), ha bug real no indice (falta coluna equipamento_id ou index
errado). Nao mascarar.
"""

from __future__ import annotations

import threading
from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

import pytest
from django.db import IntegrityError, connection, transaction
from src.application.operacao.os.abrir_os_via_orcamento import (
    AbrirOSInput,
    ItemOrcamento,
    abrir_os_via_orcamento,
)
from src.application.operacao.os.atribuir_tecnico import (
    AtribuicaoAtividade,
    AtribuirTecnicoInput,
    atribuir_tecnico,
)
from src.application.operacao.os.iniciar_atividade import (
    IniciarAtividadeInput,
    iniciar_atividade,
)
from src.domain.operacao.os.value_objects import TipoAtividade
from src.infrastructure.clientes.models import Cliente, TipoPessoa
from src.infrastructure.equipamentos.models import Equipamento
from src.infrastructure.multitenant.connection import run_in_tenant_context
from src.infrastructure.ordens_servico.repositories import DjangoOSRepository

from tests.factories import TenantFactory

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _setup_tenant_cliente(slug: str):
    """Cria tenant + cliente PJ; retorna (tenant, cliente)."""
    tenant = TenantFactory(slug=slug)
    sfx = slug[-6:]
    with run_in_tenant_context(tenant.id):
        cliente, _ = Cliente.objects.get_or_create(
            tenant=tenant,
            documento="11222333000181",
            defaults={
                "tipo_pessoa": TipoPessoa.PJ,
                "nome": f"Cli {sfx}",
                "aceite_lgpd_dispensa_motivo": "pj_sem_pf_associada",
            },
        )
    return tenant, cliente


def _criar_equipamento(tenant, cliente, tag_sfx: str):
    """Cria e retorna um Equipamento ativo."""
    with run_in_tenant_context(tenant.id):
        return Equipamento.objects.create(
            tenant=tenant,
            tag=f"CONC-CE-{tag_sfx}",
            numero_serie=f"NS-CE-{tag_sfx}",
            fabricante="Toledo",
            modelo="Z",
            cliente_atual=cliente,
            perfil_tenant_snapshot={"perfil": "D"},
        )


def _abrir_os_com_atividade(tenant, cliente, equipamento, executor_id):
    """Abre OS com 1 atividade bloqueante (calibracao) no equipamento dado.

    Retorna atividade_id.
    """
    repo = DjangoOSRepository()
    payload = AbrirOSInput(
        orcamento_id=uuid4(),
        tenant_id=tenant.id,
        cliente_id=cliente.id,
        cliente_referencia_hash="a" * 64,
        cliente_key_id="kms",
        # Retrofit ADR-0082: equipamento_id por item (nao no header).
        equipamento_id=None,
        equipamento_recebimento_id=None,
        analise_critica_id=uuid4(),
        analise_critica_snapshot_hash="b" * 64,
        regra_decisao_acordada="default",
        valor_total=Decimal("100.00"),
        itens=(
            ItemOrcamento(
                tipo=TipoAtividade.CALIBRACAO,
                sequencia=1,
                valor_unitario=Decimal("100.00"),
                requer_recebimento=False,
                equipamento_id=equipamento.id,
            ),
        ),
        correlation_id=uuid4(),
        abertura_at=datetime.now(UTC),
        criada_por_user_id=None,
    )
    with run_in_tenant_context(tenant.id), transaction.atomic():
        res = abrir_os_via_orcamento(payload=payload, repository=repo)
        atividades = repo.listar_atividades_por_os(res.os_id)
        atribuir_tecnico(
            payload=AtribuirTecnicoInput(
                os_id=res.os_id,
                atribuicoes=(
                    AtribuicaoAtividade(
                        atividade_id=atividades[0].id,
                        tecnico_executor_id=executor_id,
                    ),
                ),
                correlation_id=uuid4(),
                solicitada_em=datetime.now(UTC),
                solicitada_por_user_id=None,
            ),
            repository=repo,
        )
    return atividades[0].id


def _iniciar_em_thread(tenant_id, atividade_id, executor_id, resultados, idx, barrier):
    """Funcao executada em thread: iniciar_atividade e depositar resultado."""
    try:
        repo = DjangoOSRepository()
        barrier.wait()  # sincroniza todas as threads antes de executar
        with run_in_tenant_context(tenant_id), transaction.atomic():
            iniciar_atividade(
                payload=IniciarAtividadeInput(
                    atividade_id=atividade_id,
                    usuario_id=executor_id,
                    correlation_id=uuid4(),
                    client_event_id=uuid4(),
                    iniciada_em=datetime.now(UTC),
                ),
                repository=repo,
            )
        resultados[idx] = "ok"
    except IntegrityError:
        resultados[idx] = "integrity_error"
    except Exception as exc:
        resultados[idx] = f"outro:{type(exc).__name__}:{exc}"
    finally:
        # Cada thread deve fechar a conexao Django ao terminar (pool nao-thread-safe).
        connection.close()


# ---------------------------------------------------------------------------
# AC-OSME-005-1: equipamentos DISTINTOS na mesma OS — sem falso-412
# ---------------------------------------------------------------------------


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_ac_osme_005_1_sem_falso_412_equip_distintos(db):
    """AC-OSME-005-1: 2 atividades bloqueantes de equipamentos DISTINTOS
    na mesma OS -> ambas chegam a EM_EXECUCAO sem conflito de indice.

    O idx_atividade_em_execucao_por_equip chaveaia por (tenant_id, equipamento_id).
    Equipamentos distintos => chaves distintas => sem IntegrityError.
    """
    tenant, cliente = _setup_tenant_cliente(f"osme-005-1-{uuid4().hex[:6]}")
    executor_1 = uuid4()
    executor_2 = uuid4()
    sfx_a = uuid4().hex[:6]
    sfx_b = uuid4().hex[:6]
    equip_a = _criar_equipamento(tenant, cliente, sfx_a)
    equip_b = _criar_equipamento(tenant, cliente, sfx_b)

    ativ_a = _abrir_os_com_atividade(tenant, cliente, equip_a, executor_1)
    ativ_b = _abrir_os_com_atividade(tenant, cliente, equip_b, executor_2)

    resultados = [None, None]
    barrier = threading.Barrier(2)

    t1 = threading.Thread(
        target=_iniciar_em_thread,
        args=(tenant.id, ativ_a, executor_1, resultados, 0, barrier),
    )
    t2 = threading.Thread(
        target=_iniciar_em_thread,
        args=(tenant.id, ativ_b, executor_2, resultados, 1, barrier),
    )
    t1.start()
    t2.start()
    t1.join(timeout=30)
    t2.join(timeout=30)

    assert not t1.is_alive(), "Thread 1 travou (timeout 30s)"
    assert not t2.is_alive(), "Thread 2 travou (timeout 30s)"

    # AC-OSME-005-1: AMBAS devem ter sucesso — equipamentos distintos nao conflitam.
    falhas = [r for r in resultados if r != "ok"]
    assert not falhas, (
        f"AC-OSME-005-1 FALHOU: equipamentos distintos geraram conflito de indice. "
        f"resultados={resultados}. "
        f"GATE VERMELHO: verificar se idx_atividade_em_execucao_por_equip "
        f"inclui equipamento_id na chave (retrofit ADR-0082)."
    )


# ---------------------------------------------------------------------------
# AC-OSME-005-2: MESMO equipamento — serializa com IntegrityError
# ---------------------------------------------------------------------------


@pytest.mark.django_db(transaction=True, databases=["default", "breaker_writer"])
def test_ac_osme_005_2_serializa_mesmo_equipamento(db):
    """AC-OSME-005-2: 2 atividades bloqueantes do MESMO equipamento tentando
    EM_EXECUCAO simultaneamente -> exatamente 1 sucede; a outra recebe
    IntegrityError (unique partial index serializa acesso por equipamento).

    Usa 50 threads para garantir pressao real no banco (mesmo numero de threads
    que o molde INV-OS-CONC-001 exigiria — parametro conservador para CI local).
    """
    N_THREADS = 50
    tenant, cliente = _setup_tenant_cliente(f"osme-005-2-{uuid4().hex[:6]}")
    executor_id = uuid4()
    sfx = uuid4().hex[:6]
    equip = _criar_equipamento(tenant, cliente, sfx)

    # Cria N_THREADS atividades bloqueantes no MESMO equipamento (OSs diferentes).
    ativ_ids = []
    for _ in range(N_THREADS):
        ativ_id = _abrir_os_com_atividade(tenant, cliente, equip, executor_id)
        ativ_ids.append(ativ_id)

    resultados = [None] * N_THREADS
    barrier = threading.Barrier(N_THREADS)
    threads = []
    for i, ativ_id in enumerate(ativ_ids):
        t = threading.Thread(
            target=_iniciar_em_thread,
            args=(tenant.id, ativ_id, executor_id, resultados, i, barrier),
        )
        threads.append(t)

    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=60)

    for i, t in enumerate(threads):
        assert not t.is_alive(), f"Thread {i} travou (timeout 60s)"

    sucessos = [r for r in resultados if r == "ok"]
    integrity_errors = [r for r in resultados if r == "integrity_error"]
    outros = [r for r in resultados if r not in ("ok", "integrity_error")]

    assert not outros, (
        f"AC-OSME-005-2: erros inesperados (nem ok nem IntegrityError): {outros}"
    )
    assert len(sucessos) == 1, (
        f"AC-OSME-005-2: esperava exatamente 1 sucesso, obteve {len(sucessos)}. "
        f"GATE VERMELHO: se sucesso > 1, o indice unique partial nao esta "
        f"serializando corretamente. resultados={resultados}"
    )
    assert len(integrity_errors) == N_THREADS - 1, (
        f"AC-OSME-005-2: esperava {N_THREADS - 1} IntegrityErrors, "
        f"obteve {len(integrity_errors)}."
    )
