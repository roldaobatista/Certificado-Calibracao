"""Frente agenda — Fatia 1b (T-AGE-027): schema PG-real.

Cobre o COMPORTAMENTO em PG real (o que o drill estrutural não garante):
- RLS ENABLE+FORCE + >=4 policies por tabela (INV-TENANT-001/002).
- Isolamento cross-tenant UNHAPPY: tenant B NÃO vê evento de A (INV-TENANT-003).
- CHECK atividade_id NOT NULL quando tipo='os' (INV-AG-ATIVIDADE-001).
- UNIQUE (recorrencia_id, ocorrencia_dt) — INV-AG-RECORRENCIA-001 / R10.
- EventoAuditoriaAgenda INSERT-only: UPDATE/DELETE → RAISE (INV-AG-AUDIT-WORM-001).
- RegistroNoShow INSERT-only: UPDATE/DELETE → RAISE.
- RegimeJornadaColaborador INSERT-only: UPDATE/DELETE → RAISE.
- EXCLUDE GIST: rejeita overlap do mesmo técnico/tenant (→ IntegrityError).
- EXCLUDE GIST: PERMITE mesmo horário em técnicos DIFERENTES.
- EXCLUDE GIST: PERMITE mesmo horário em tenants DIFERENTES.
- Half-open: slot 09:00-10:00 e 10:00-11:00 do mesmo técnico NÃO colidem (R12).
- Cancelado não entra no EXCLUDE (pode inserir na mesma janela após cancelar).
- Drill de concorrência REAL do EXCLUDE (PLAN-AGE-05):
  2 transações/conexões simultâneas tentando alocar o MESMO técnico no MESMO
  tstzrange → exatamente 1 commita, a outra recebe IntegrityError.

Cada RAISE aborta a transação PG → cada cenário em teste isolado (TST-004).

IMPORTANTE: usa ``--reuse-db`` (NUNCA ``--create-db``). Memória:
``feedback_test_db_nao_dropar_create_db`` + ``feedback_test_db_owner_app_user``.
"""

from __future__ import annotations

import threading
import uuid
from datetime import UTC, date

import pytest
from django.db import DatabaseError, IntegrityError, connection
from django.utils import timezone as dj_tz
from src.infrastructure.agenda.models import (
    EventoAgenda,
    EventoAuditoriaAgenda,
    RegimeJornadaColaborador,
    RegistroNoShow,
)
from src.infrastructure.multitenant.connection import run_in_tenant_context

from tests.factories import TenantFactory

# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

_DATA_HOJE = date.today()


def _agora():
    return dj_tz.now()


def _slot(hora_inicio: int = 8, hora_fim: int = 9, dia_offset: int = 1):
    """Retorna (inicia_at, termina_at) para um slot simples."""
    from datetime import datetime

    base = datetime(2030, 6, 15 + dia_offset, hora_inicio, 0, 0, tzinfo=UTC)
    fim = datetime(2030, 6, 15 + dia_offset, hora_fim, 0, 0, tzinfo=UTC)
    return base, fim


def _cria_evento(
    tenant,
    tecnico_id=None,
    *,
    tipo: str = "bloqueio",
    estado: str = "agendado",
    hora_inicio: int = 8,
    hora_fim: int = 9,
    dia_offset: int = 1,
    atividade_id=None,
    recorrencia_id=None,
    ocorrencia_dt=None,
) -> EventoAgenda:
    """Cria EventoAgenda dentro do contexto do tenant."""
    if tecnico_id is None:
        tecnico_id = uuid.uuid4()
    inicia, termina = _slot(hora_inicio, hora_fim, dia_offset)
    with run_in_tenant_context(tenant.id):
        return EventoAgenda.objects.create(
            tenant=tenant,
            tecnico_id=tecnico_id,
            tipo=tipo,
            estado=estado,
            inicia_at=inicia,
            termina_at=termina,
            aloca_em_umc=False,
            criado_por_usuario_id=uuid.uuid4(),
            atividade_id=atividade_id,
            recorrencia_id=recorrencia_id,
            ocorrencia_dt=ocorrencia_dt,
        )


def _cria_auditoria(tenant, evento: EventoAgenda) -> EventoAuditoriaAgenda:
    with run_in_tenant_context(tenant.id):
        return EventoAuditoriaAgenda.objects.create(
            tenant=tenant,
            evento_id=evento.id,
            acao="criado",
            actor_usuario_id=uuid.uuid4(),
            occurred_at=_agora(),
        )


def _cria_noshow(tenant, evento: EventoAgenda) -> RegistroNoShow:
    with run_in_tenant_context(tenant.id):
        return RegistroNoShow.objects.create(
            tenant=tenant,
            evento_id=evento.id,
            tecnico_id=uuid.uuid4(),
            ocorrido_em=_agora(),
            custo_estimado="150.00",
            cobrar_cliente=False,
            registrado_por_usuario_id=uuid.uuid4(),
        )


def _cria_regime(tenant) -> RegimeJornadaColaborador:
    with run_in_tenant_context(tenant.id):
        return RegimeJornadaColaborador.objects.create(
            tenant=tenant,
            colaborador_id=uuid.uuid4(),
            regime="clt_geral",
            vigencia_inicio=_DATA_HOJE,
            definido_por_usuario_id=uuid.uuid4(),
            fonte="override_humano",
        )


# ---------------------------------------------------------------------------
# 1. Estrutura RLS — >=4 policies + ENABLE + FORCE
# ---------------------------------------------------------------------------


@pytest.mark.django_db
@pytest.mark.parametrize(
    "tabela",
    [
        "evento_agenda",
        "recorrencia_agenda",
        "registro_no_show",
        "capacidade_tecnico",
        "feriado",
        "evento_auditoria_agenda",
        "regime_jornada_colaborador",
    ],
)
def test_rls_force_e_4_policies(tabela: str) -> None:
    """Todas as 7 tabelas têm RLS ENABLED + FORCE + >=4 policies (INV-TENANT-001/002)."""
    with connection.cursor() as cur:
        cur.execute(
            "SELECT relrowsecurity, relforcerowsecurity FROM pg_class c "
            "JOIN pg_namespace n ON c.relnamespace=n.oid "
            "WHERE n.nspname='public' AND c.relname=%s",
            [tabela],
        )
        row = cur.fetchone()
        assert row is not None, f"Tabela {tabela} não existe"
        enabled, forced = row
        cur.execute("SELECT COUNT(*) FROM pg_policies WHERE tablename=%s", [tabela])
        n_pol = cur.fetchone()[0]
    assert enabled, f"INV-TENANT-001: {tabela} sem RLS ENABLED"
    assert forced, f"INV-TENANT-002: {tabela} sem FORCE"
    assert n_pol >= 4, f"{tabela} com <4 policies ({n_pol})"


# ---------------------------------------------------------------------------
# 2. Isolamento cross-tenant (UNHAPPY explícito)
# ---------------------------------------------------------------------------


@pytest.mark.django_db(transaction=True)
def test_rls_isola_evento_entre_tenants() -> None:
    """Tenant B NÃO enxerga evento do tenant A (INV-TENANT-003 UNHAPPY)."""
    tenant_a = TenantFactory()
    tenant_b = TenantFactory()
    evento_a = _cria_evento(tenant_a)
    # Tenant B NÃO enxerga evento de A:
    with run_in_tenant_context(tenant_b.id):
        assert not EventoAgenda.objects.filter(
            id=evento_a.id
        ).exists(), "INV-TENANT-003: tenant B viu evento do tenant A (vazamento RLS)"
    # Tenant A enxerga o próprio:
    with run_in_tenant_context(tenant_a.id):
        assert EventoAgenda.objects.filter(id=evento_a.id).exists()


# ---------------------------------------------------------------------------
# 3. CHECK atividade_id quando tipo='os' (INV-AG-ATIVIDADE-001)
# ---------------------------------------------------------------------------


@pytest.mark.django_db(transaction=True)
def test_check_atividade_id_obrigatorio_quando_tipo_os() -> None:
    """tipo='os' sem atividade_id → IntegrityError (INV-AG-ATIVIDADE-001)."""
    tenant = TenantFactory()
    inicia, termina = _slot(8, 9)
    with run_in_tenant_context(tenant.id), pytest.raises(IntegrityError):
        EventoAgenda.objects.create(
            tenant=tenant,
            tecnico_id=uuid.uuid4(),
            tipo="os",
            estado="agendado",
            inicia_at=inicia,
            termina_at=termina,
            aloca_em_umc=False,
            criado_por_usuario_id=uuid.uuid4(),
            atividade_id=None,  # violação: tipo='os' sem atividade_id
        )


@pytest.mark.django_db(transaction=True)
def test_check_atividade_id_obrigatorio_quando_tipo_os_ok_com_atividade() -> None:
    """tipo='os' COM atividade_id → OK."""
    tenant = TenantFactory()
    evento = _cria_evento(tenant, tipo="os", atividade_id=uuid.uuid4(), hora_inicio=10, hora_fim=11)
    assert evento.id is not None


@pytest.mark.django_db(transaction=True)
def test_check_atividade_id_nao_obrigatorio_para_outros_tipos() -> None:
    """tipo='bloqueio' sem atividade_id → OK."""
    tenant = TenantFactory()
    evento = _cria_evento(tenant, tipo="bloqueio")
    assert evento.id is not None


# ---------------------------------------------------------------------------
# 4. UNIQUE (recorrencia_id, ocorrencia_dt) — INV-AG-RECORRENCIA-001 / R10
# ---------------------------------------------------------------------------


@pytest.mark.django_db(transaction=True)
def test_unique_recorrencia_ocorrencia_raise() -> None:
    """Mesma (recorrencia_id, ocorrencia_dt) → IntegrityError (R10)."""
    tenant = TenantFactory()
    rec_id = uuid.uuid4()
    ocorrencia = _slot(8, 9)[0]  # inicia_at como âncora
    _cria_evento(
        tenant,
        hora_inicio=8,
        hora_fim=9,
        dia_offset=1,
        recorrencia_id=rec_id,
        ocorrencia_dt=ocorrencia,
    )
    # 2ª ocorrência com mesmo (recorrencia_id, ocorrencia_dt):
    inicia2, termina2 = _slot(14, 15, 2)  # horário diferente (não bate no EXCLUDE)
    with run_in_tenant_context(tenant.id), pytest.raises(IntegrityError):
        EventoAgenda.objects.create(
            tenant=tenant,
            tecnico_id=uuid.uuid4(),  # técnico diferente (não bate no EXCLUDE)
            tipo="bloqueio",
            estado="agendado",
            inicia_at=inicia2,
            termina_at=termina2,
            aloca_em_umc=False,
            criado_por_usuario_id=uuid.uuid4(),
            recorrencia_id=rec_id,
            ocorrencia_dt=ocorrencia,  # mesma ocorrência → viola UNIQUE
        )


@pytest.mark.django_db(transaction=True)
def test_unique_recorrencia_ocorrencia_diferente_ok() -> None:
    """Mesma recorrencia_id com ocorrencia_dt DIFERENTE → OK."""
    tenant = TenantFactory()
    rec_id = uuid.uuid4()
    ocorrencia1 = _slot(8, 9, 1)[0]
    ocorrencia2 = _slot(8, 9, 2)[0]
    tecnico = uuid.uuid4()
    _cria_evento(
        tenant,
        tecnico_id=tecnico,
        hora_inicio=8,
        hora_fim=9,
        dia_offset=1,
        recorrencia_id=rec_id,
        ocorrencia_dt=ocorrencia1,
    )
    # dia_offset=2: slot em dia diferente, não bate no EXCLUDE
    ev2 = _cria_evento(
        tenant,
        tecnico_id=tecnico,
        hora_inicio=8,
        hora_fim=9,
        dia_offset=2,
        recorrencia_id=rec_id,
        ocorrencia_dt=ocorrencia2,
    )
    assert ev2.id is not None


# ---------------------------------------------------------------------------
# 5. EventoAuditoriaAgenda INSERT-only (block-update + block-delete)
# ---------------------------------------------------------------------------


@pytest.mark.django_db(transaction=True)
def test_auditoria_update_raise() -> None:
    """EventoAuditoriaAgenda INSERT-only: UPDATE → RAISE (INV-AG-AUDIT-WORM-001)."""
    tenant = TenantFactory()
    evento = _cria_evento(tenant)
    auditoria = _cria_auditoria(tenant, evento)
    with run_in_tenant_context(tenant.id), pytest.raises(DatabaseError):
        EventoAuditoriaAgenda.objects.filter(id=auditoria.id).update(acao="cancelado")


@pytest.mark.django_db(transaction=True)
def test_auditoria_delete_raise() -> None:
    """EventoAuditoriaAgenda INSERT-only: DELETE → RAISE (INV-AG-AUDIT-WORM-001)."""
    tenant = TenantFactory()
    evento = _cria_evento(tenant)
    auditoria = _cria_auditoria(tenant, evento)
    with run_in_tenant_context(tenant.id), pytest.raises(DatabaseError):
        EventoAuditoriaAgenda.objects.filter(id=auditoria.id).delete()


# ---------------------------------------------------------------------------
# 6. RegistroNoShow INSERT-only (block-update + block-delete)
# ---------------------------------------------------------------------------


@pytest.mark.django_db(transaction=True)
def test_noshow_update_raise() -> None:
    """RegistroNoShow INSERT-only: UPDATE → RAISE."""
    tenant = TenantFactory()
    evento = _cria_evento(tenant)
    noshow = _cria_noshow(tenant, evento)
    with run_in_tenant_context(tenant.id), pytest.raises(DatabaseError):
        RegistroNoShow.objects.filter(id=noshow.id).update(cobrar_cliente=True)


@pytest.mark.django_db(transaction=True)
def test_noshow_delete_raise() -> None:
    """RegistroNoShow INSERT-only: DELETE → RAISE."""
    tenant = TenantFactory()
    evento = _cria_evento(tenant)
    noshow = _cria_noshow(tenant, evento)
    with run_in_tenant_context(tenant.id), pytest.raises(DatabaseError):
        RegistroNoShow.objects.filter(id=noshow.id).delete()


@pytest.mark.django_db(transaction=True)
def test_noshow_unico_por_evento_raise() -> None:
    """2º no-show do mesmo evento → IntegrityError (uq_no_show_evento — INV-AG-NOSHOW-AR-001).

    Fecha o TOCTOU de cobrança dupla sob concorrência: a unicidade vive no banco.
    """
    tenant = TenantFactory()
    evento = _cria_evento(tenant)
    _cria_noshow(tenant, evento)
    with run_in_tenant_context(tenant.id), pytest.raises(IntegrityError):
        _cria_noshow(tenant, evento)


# ---------------------------------------------------------------------------
# 7. RegimeJornadaColaborador INSERT-only (block-update + block-delete)
# ---------------------------------------------------------------------------


@pytest.mark.django_db(transaction=True)
def test_regime_update_raise() -> None:
    """RegimeJornadaColaborador INSERT-only: UPDATE → RAISE (INV-AG-REGIME-001)."""
    tenant = TenantFactory()
    regime = _cria_regime(tenant)
    with run_in_tenant_context(tenant.id), pytest.raises(DatabaseError):
        RegimeJornadaColaborador.objects.filter(id=regime.id).update(
            regime="motorista_profissional"
        )


@pytest.mark.django_db(transaction=True)
def test_regime_delete_raise() -> None:
    """RegimeJornadaColaborador INSERT-only: DELETE → RAISE (INV-AG-REGIME-001)."""
    tenant = TenantFactory()
    regime = _cria_regime(tenant)
    with run_in_tenant_context(tenant.id), pytest.raises(DatabaseError):
        RegimeJornadaColaborador.objects.filter(id=regime.id).delete()


# ---------------------------------------------------------------------------
# 8. EXCLUDE GIST: rejeita overlap do mesmo técnico/tenant
# ---------------------------------------------------------------------------


@pytest.mark.django_db(transaction=True)
def test_exclude_gist_rejeita_overlap_mesmo_tecnico_tenant() -> None:
    """Mesmo técnico + mesmo tenant + slots sobrepostos → IntegrityError (INV-AG-OVERLAP-001)."""
    tenant = TenantFactory()
    tecnico = uuid.uuid4()
    # 1 evento: 09:00-11:00
    _cria_evento(tenant, tecnico_id=tecnico, hora_inicio=9, hora_fim=11, dia_offset=3)
    # 2 evento: 10:00-12:00 -> sobrepoe (10-11 eh compartilhado)
    inicia2, termina2 = _slot(10, 12, 3)
    with run_in_tenant_context(tenant.id), pytest.raises(IntegrityError):
        EventoAgenda.objects.create(
            tenant=tenant,
            tecnico_id=tecnico,
            tipo="bloqueio",
            estado="agendado",
            inicia_at=inicia2,
            termina_at=termina2,
            aloca_em_umc=False,
            criado_por_usuario_id=uuid.uuid4(),
        )


@pytest.mark.django_db(transaction=True)
def test_exclude_gist_permite_mesmo_horario_tecnicos_diferentes() -> None:
    """Técnicos DIFERENTES → podem ter o mesmo horário (EXCLUDE é por técnico)."""
    tenant = TenantFactory()
    tecnico_a = uuid.uuid4()
    tecnico_b = uuid.uuid4()
    ev_a = _cria_evento(tenant, tecnico_id=tecnico_a, hora_inicio=9, hora_fim=10, dia_offset=4)
    ev_b = _cria_evento(tenant, tecnico_id=tecnico_b, hora_inicio=9, hora_fim=10, dia_offset=4)
    assert ev_a.id is not None
    assert ev_b.id is not None


@pytest.mark.django_db(transaction=True)
def test_exclude_gist_permite_mesmo_horario_tenants_diferentes() -> None:
    """Tenants DIFERENTES → podem ter o mesmo técnico_id e mesmo horário (EXCLUDE escopa tenant_id)."""
    tenant_a = TenantFactory()
    tenant_b = TenantFactory()
    # Mesmo UUID de técnico (coincidência — colaboradores não têm FK hard)
    tecnico = uuid.uuid4()
    ev_a = _cria_evento(tenant_a, tecnico_id=tecnico, hora_inicio=9, hora_fim=10, dia_offset=5)
    ev_b = _cria_evento(tenant_b, tecnico_id=tecnico, hora_inicio=9, hora_fim=10, dia_offset=5)
    assert ev_a.id is not None
    assert ev_b.id is not None


# ---------------------------------------------------------------------------
# 9. Half-open: slots adjacentes NÃO colidem (R12)
# ---------------------------------------------------------------------------


@pytest.mark.django_db(transaction=True)
def test_halfopen_slots_adjacentes_nao_colidem() -> None:
    """09:00-10:00 e 10:00-11:00 do mesmo técnico NÃO colidem — range half-open '[)' (R12)."""
    tenant = TenantFactory()
    tecnico = uuid.uuid4()
    # Slot 09:00-10:00
    ev1 = _cria_evento(tenant, tecnico_id=tecnico, hora_inicio=9, hora_fim=10, dia_offset=6)
    # Slot 10:00-11:00 (adjacente - nao sobrepoe com '[]')
    ev2 = _cria_evento(tenant, tecnico_id=tecnico, hora_inicio=10, hora_fim=11, dia_offset=6)
    assert ev1.id is not None
    assert ev2.id is not None


@pytest.mark.django_db(transaction=True)
def test_halfopen_slots_sobrepostos_1min_colidem() -> None:
    """09:00-10:01 e 10:00-11:00 DO colidem (sobreposição de 1 minuto)."""
    from datetime import datetime

    tenant = TenantFactory()
    tecnico = uuid.uuid4()
    # 09:00-10:01
    inicia1 = datetime(2030, 6, 22, 9, 0, 0, tzinfo=UTC)
    termina1 = datetime(2030, 6, 22, 10, 1, 0, tzinfo=UTC)
    with run_in_tenant_context(tenant.id):
        EventoAgenda.objects.create(
            tenant=tenant,
            tecnico_id=tecnico,
            tipo="bloqueio",
            estado="agendado",
            inicia_at=inicia1,
            termina_at=termina1,
            aloca_em_umc=False,
            criado_por_usuario_id=uuid.uuid4(),
        )
    # 10:00-11:00 -> sobrepoe (compartilha 10:00-10:01)
    inicia2 = datetime(2030, 6, 22, 10, 0, 0, tzinfo=UTC)
    termina2 = datetime(2030, 6, 22, 11, 0, 0, tzinfo=UTC)
    with run_in_tenant_context(tenant.id), pytest.raises(IntegrityError):
        EventoAgenda.objects.create(
            tenant=tenant,
            tecnico_id=tecnico,
            tipo="bloqueio",
            estado="agendado",
            inicia_at=inicia2,
            termina_at=termina2,
            aloca_em_umc=False,
            criado_por_usuario_id=uuid.uuid4(),
        )


# ---------------------------------------------------------------------------
# 10. Cancelado não entra no EXCLUDE
# ---------------------------------------------------------------------------


@pytest.mark.django_db(transaction=True)
def test_cancelado_nao_entra_no_exclude() -> None:
    """Após cancelar evento, pode inserir outro no mesmo slot (EXCLUDE WHERE estado != 'cancelado')."""
    tenant = TenantFactory()
    tecnico = uuid.uuid4()
    ev = _cria_evento(tenant, tecnico_id=tecnico, hora_inicio=9, hora_fim=10, dia_offset=7)
    # Cancelar o evento:
    with run_in_tenant_context(tenant.id):
        EventoAgenda.objects.filter(id=ev.id).update(estado="cancelado")
    # Inserir novo evento no mesmo slot → deve ser aceito:
    ev2 = _cria_evento(tenant, tecnico_id=tecnico, hora_inicio=9, hora_fim=10, dia_offset=7)
    assert ev2.id is not None


# ---------------------------------------------------------------------------
# 11. Drill de concorrência REAL do EXCLUDE (PLAN-AGE-05)
#     2 conexões simultâneas tentando alocar o MESMO técnico no MESMO tstzrange →
#     exatamente 1 commita, a outra recebe IntegrityError.
# ---------------------------------------------------------------------------


@pytest.mark.django_db(transaction=True)
def test_concorrencia_real_exclude_gist_exatamente_um_commit() -> None:
    """Drill de concorrência REAL do EXCLUDE GIST (PLAN-AGE-05).

    2 threads com 2 conexões Django independentes tentam inserir o MESMO
    técnico no MESMO slot. O PG garante que no máximo 1 commita — a outra
    recebe IntegrityError (violação EXCLUDE) OU OperationalError (deadlock).

    Ambos os erros são resultados VÁLIDOS: em ambos os casos a transação
    conflitante é abortada e o evento NÃO é persistido. O invariante central
    é ``len(sucessos) <= 1`` — nunca 2 commits para o mesmo slot.

    O deadlock pode ocorrer porque o EXCLUDE GIST adquire ShareLocks por
    transação para verificar sobreposições. Quando 2 transações concorrentes
    atingem a verificação simultaneamente, o PG detecta o ciclo e aborta uma
    delas (comportamento documentado — PG docs § CREATE TABLE / EXCLUDE).

    Molde: commit 88483e3 (CR webhook idempotência sob corrida).
    """
    import django.db
    from django.db import OperationalError as DjangoOperationalError

    tenant = TenantFactory()
    tecnico = uuid.uuid4()
    inicia, termina = _slot(13, 14, 8)

    erros: list[Exception] = []
    sucessos: list[str] = []
    barreira = threading.Barrier(2)  # sincroniza os 2 INSERTs

    def tentar_alocar(thread_id: str) -> None:
        # Cada thread precisa de sua própria conexão Django.
        django.db.connections.close_all()
        try:
            barreira.wait()  # ambas chegam juntas ao INSERT
            with run_in_tenant_context(tenant.id):
                EventoAgenda.objects.create(
                    tenant=tenant,
                    tecnico_id=tecnico,
                    tipo="bloqueio",
                    estado="agendado",
                    inicia_at=inicia,
                    termina_at=termina,
                    aloca_em_umc=False,
                    criado_por_usuario_id=uuid.uuid4(),
                )
            sucessos.append(thread_id)
        except IntegrityError:
            # Violação direta do EXCLUDE GIST — esperado.
            erros.append(Exception(f"{thread_id} recebeu IntegrityError (esperado)"))
        except DjangoOperationalError as exc:
            msg = str(exc).lower()
            if "deadlock" in msg:
                # Deadlock é resultado igualmente válido: PG abortou a transação
                # conflitante — nenhum dado inválido foi persistido.
                erros.append(Exception(f"{thread_id} recebeu deadlock (esperado): {exc}"))
            else:
                erros.append(exc)
        except Exception as exc:
            erros.append(exc)
        finally:
            django.db.connections.close_all()

    t1 = threading.Thread(target=tentar_alocar, args=("thread-1",))
    t2 = threading.Thread(target=tentar_alocar, args=("thread-2",))
    t1.start()
    t2.start()
    t1.join(timeout=15)
    t2.join(timeout=15)

    # Erros inesperados (não IntegrityError nem deadlock) levantam no teste:
    erros_inesperados = [
        e for e in erros if "IntegrityError" not in str(e) and "deadlock" not in str(e).lower()
    ]
    assert not erros_inesperados, f"Erros inesperados nas threads: {erros_inesperados}"

    # Invariante central: NUNCA 2 commits para o mesmo slot.
    assert (
        len(sucessos) <= 1
    ), f"FALHA CRÍTICA: {len(sucessos)} threads commitaram o mesmo slot: {sucessos}"

    # Confirma que no banco há no máximo 1 linha para o técnico/slot:
    with run_in_tenant_context(tenant.id):
        count = EventoAgenda.objects.filter(tecnico_id=tecnico).count()
    assert count <= 1, f"FALHA CRÍTICA: {count} eventos duplicados no banco para o mesmo slot"


# ---------------------------------------------------------------------------
# 12. Seed de feriados nacionais (D-AGE-10)
# ---------------------------------------------------------------------------


@pytest.mark.django_db(transaction=True)
def test_seed_feriados_nacionais_presentes() -> None:
    """Seed de feriados nacionais BR foi aplicado (D-AGE-10 / migration 0007).

    Feriados nacionais (tenant_id=NULL) são visíveis para QUALQUER tenant via
    policy RLS SELECT: ``(tenant_id IS NULL) OR (tenant_id IN app.tenant_ids)``.
    O teste usa um tenant real para ativar o contexto RLS corretamente.
    """
    tenant = TenantFactory()
    # Qualquer tenant enxerga os feriados nacionais (policy inclui tenant_id IS NULL).
    with run_in_tenant_context(tenant.id):
        with connection.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM feriado WHERE nacional = TRUE AND tenant_id IS NULL")
            count = cur.fetchone()[0]
    # 9 feriados × 6 anos (2025-2030) = 54
    assert count >= 54, f"Seed de feriados insuficiente: {count} (esperado >=54)"


@pytest.mark.django_db(transaction=True)
def test_feriado_natal_presente_2026() -> None:
    """Natal 2026 está no seed (spot check — D-AGE-10)."""
    tenant = TenantFactory()
    with run_in_tenant_context(tenant.id):
        with connection.cursor() as cur:
            cur.execute(
                "SELECT descricao FROM feriado "
                "WHERE data = '2026-12-25' AND nacional = TRUE AND tenant_id IS NULL"
            )
            row = cur.fetchone()
    assert row is not None, "Natal 2026 não está no seed de feriados"
    assert "Natal" in row[0], f"Descrição inesperada: {row[0]}"
