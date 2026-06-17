"""Testes de regressão de invariante — módulo `agenda` (TST-004 / Fatia 3d).

Uma função ou classe por INV crítica, com o ID literal no nome. Cada teste EXERCE
A BARREIRA REAL e falha se a barreira for removida.

INVs cobertas (família INV-AG-* — cravadas em REGRAS-INEGOCIAVEIS.md, T-AGE-046):
  INV-AG-JORNADA-UMC-001  — validar_jornada_umc perfil-AGNÓSTICA (hook + domínio)
  INV-AG-REGIME-001       — regime NUNCA do payload; IA NUNCA grava override
  INV-AG-OVERLAP-001      — ExclusionConstraint deve incluir tenant_id (hook estático)
  INV-AG-ATIVIDADE-001    — tipo=os exige atividade_id NOT NULL (DB constraint)
  INV-AG-PERFIL-001       — regime_jornada_colaborador INSERT-only (trigger WORM)
  INV-AG-RECORRENCIA-001  — RegraRecorrencia exige rrule_str (RRULE RFC 5545)
  INV-AG-CNH-001          — motorista_umc com pendencia_cnh bloqueado via adapter
  INV-AG-AUDIT-WORM-001   — wiring adapter registrado no boot (AgendaConfig.ready)
                             + esta_referenciado (happy + sem-agenda + cancelado)
  INV-AG-NOSHOW-AR001     — no-show cobrável chama AReceberPort no use case de forma
                             atômica: 1 chamada; falha propaga (A1); sem cliente_id → erro (A3)

Referências: plan §5 Fatia 3d, T-AGE-046, T-AGE-047, T-AGE-048.
"""

from __future__ import annotations

import json
import os
import subprocess
import uuid
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

import pytest

from tests.factories import TenantFactory, UsuarioFactory

# ---------------------------------------------------------------------------
# Constantes e helpers compartilhados
# ---------------------------------------------------------------------------

_HOOKS_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", ".claude", "hooks")
)


def _hook(nome: str) -> str:
    return os.path.join(_HOOKS_DIR, nome)


def _run_hook(nome: str, stdin: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["bash", _hook(nome)],
        input=stdin,
        capture_output=True,
        text=True,
    )


def _json_tool(file_path: str, content: str) -> str:
    return json.dumps({"tool_input": {"file_path": file_path, "content": content}})


def _slot_futuro(dias: int = 7, hora_inicio: int = 9, hora_fim: int = 11):
    base = datetime.now(UTC).replace(hour=hora_inicio, minute=0, second=0, microsecond=0)
    base += timedelta(days=dias)
    fim = base.replace(hour=hora_fim)
    return base, fim


def _criar_evento_agenda(
    tenant,
    *,
    tecnico_id: uuid.UUID | None = None,
    tipo: str = "bloqueio",
    estado: str = "agendado",
    dias_futuro: int = 7,
    atividade_id: uuid.UUID | None = None,
    os_id: uuid.UUID | None = None,
):
    from src.infrastructure.agenda.models import EventoAgenda
    from src.infrastructure.multitenant.connection import run_in_tenant_context

    inicia_at, termina_at = _slot_futuro(dias=dias_futuro)
    if tecnico_id is None:
        tecnico_id = uuid.uuid4()
    ator_id = UsuarioFactory().id
    with run_in_tenant_context(tenant.id):
        ev = EventoAgenda.objects.create(
            tenant_id=tenant.id,
            tecnico_id=tecnico_id,
            tipo=tipo,
            estado=estado,
            inicia_at=inicia_at,
            termina_at=termina_at,
            aloca_em_umc=False,
            atividade_id=atividade_id,
            os_id=os_id,
            confirmar_feriado=False,
            descricao_publica="",
            revision=1,
            criado_por_usuario_id=ator_id,
        )
    return ev


# ===========================================================================
# INV-AG-JORNADA-UMC-001 — validar_jornada_umc perfil-AGNÓSTICA
# ===========================================================================


def test_inv_ag_jornada_umc_001_hook_bloqueia_gate_por_perfil():
    """INV-AG-JORNADA-UMC-001: hook bloqueia chamada de validar_jornada_umc gateada por perfil.

    Barreira: `.claude/hooks/agenda-jornada-perfil-agnostica-check.sh`.
    Valida que a verificação de jornada UMC NÃO depende do perfil metrológico A/B/C/D —
    é ordem pública trabalhista (Lei 13.103/2015 + CLT 235-C + STF ADI 5322).
    """
    conteudo_violacao = (
        "def criar_evento(slot, perfil):\n"
        "    if perfil == 'A':\n"
        "        validar_jornada_umc(slot, tecnico)\n"
        "    return slot\n"
    )
    resultado = _run_hook(
        "agenda-jornada-perfil-agnostica-check.sh",
        _json_tool("src/application/operacao/agenda/criar_evento.py", conteudo_violacao),
    )
    assert resultado.returncode == 2, (
        f"INV-AG-JORNADA-UMC-001: hook deveria bloquear (exit 2) gate por perfil, "
        f"got exit={resultado.returncode}\nstderr={resultado.stderr}"
    )


def test_inv_ag_jornada_umc_001_hook_passa_sem_gate():
    """INV-AG-JORNADA-UMC-001 (happy): chamada sem gate por perfil → hook permite."""
    conteudo_ok = (
        "def criar_evento(slot, tecnico):\n"
        "    validar_jornada_umc(slot, tecnico)\n"
        "    return slot\n"
    )
    resultado = _run_hook(
        "agenda-jornada-perfil-agnostica-check.sh",
        _json_tool("src/application/operacao/agenda/criar_evento.py", conteudo_ok),
    )
    assert resultado.returncode == 0, (
        f"INV-AG-JORNADA-UMC-001: hook NÃO deveria bloquear código sem gate por perfil, "
        f"got exit={resultado.returncode}\nstderr={resultado.stderr}"
    )


def test_inv_ag_jornada_umc_001_dominio_sem_parametro_perfil():
    """INV-AG-JORNADA-UMC-001 (domínio puro): validar_jornada_umc NÃO aceita parâmetro `perfil`.

    Barreira: a função não aceita `perfil` como parâmetro decisório — se aceitar,
    o teste sinaliza GATE VERMELHO (a invariante foi violada).
    """
    import inspect

    from src.domain.operacao.agenda.jornada import validar_jornada_umc

    sig = inspect.signature(validar_jornada_umc)
    params = list(sig.parameters.keys())

    # A função NÃO deve ter parâmetro `perfil` ou `perfil_regulatorio` (seria gate)
    parametros_proibidos = {"perfil", "perfil_regulatorio", "perfil_tenant"}
    violacoes = set(params) & parametros_proibidos
    assert not violacoes, (
        f"INV-AG-JORNADA-UMC-001 violado: validar_jornada_umc aceita parâmetro(s) de perfil "
        f"{violacoes!r}. Jornada UMC é perfil-AGNÓSTICA (Lei 13.103/2015 + ADV-AGE-04)."
    )


def test_inv_ag_jornada_umc_001_dominio_puro_clt_geral_sem_r2():
    """INV-AG-JORNADA-UMC-001 (domínio puro): clt_geral NÃO aplica R2 (direção contínua).

    Barreira: `validar_jornada_umc` só aplica R2 para motorista_profissional.
    clt_geral com bloco contínuo de 5h30+ não deve violar R2 (CLT art. 58, não 235-C).
    Válido para qualquer perfil A/B/C/D — é ordem pública trabalhista.
    """

    from src.domain.operacao.agenda.enums import RegimeJornada, TipoEvento
    from src.domain.operacao.agenda.jornada import EventoSimples, validar_jornada_umc
    from src.domain.operacao.agenda.value_objects import Janela, TecnicoJornada

    tecnico = TecnicoJornada(
        tenant_id=uuid.uuid4(),
        colaborador_id=uuid.uuid4(),
        is_tecnico_campo=True,
        aloca_em_umc=True,
    )
    agora = datetime.now(UTC).replace(hour=7, minute=0, second=0, microsecond=0)
    agora += timedelta(days=10)

    # 4h de evento existente hoje
    eventos_existentes = [
        EventoSimples(
            tipo=TipoEvento.OS,
            janela=Janela(
                inicia_at=agora,
                termina_at=agora + timedelta(hours=4),
            ),
        )
    ]
    # Novo evento: mais 1h30 logo após (total contínuo = 5h30 = exatamente o limite R2)
    nova_janela = Janela(
        inicia_at=agora + timedelta(hours=4),
        termina_at=agora + timedelta(hours=5, minutes=30),
    )

    resultado = validar_jornada_umc(
        tecnico,
        RegimeJornada.CLT_GERAL,
        nova_janela,
        eventos_existentes,
    )

    # clt_geral: R2 não se aplica (só motorista_profissional) → não pode violar R2
    assert resultado.violacao != "R2_DIRECAO_CONTINUA", (
        "INV-AG-JORNADA-UMC-001: R2 (direção contínua) aplicada para clt_geral — "
        "viola a invariante de perfil-AGNÓSTICO (R2 é exclusiva de motorista_profissional)"
    )


@pytest.mark.django_db(transaction=True)
def test_inv_ag_jornada_umc_001_tentativa_bloqueada_grava_audit_worm():
    """INV-AG-JORNADA-UMC-001: tentativa bloqueada deixa trilha WORM (audit ≥5a).

    Barreira: `AgendaViewSet._auditar_jornada_bloqueada` grava um EventoAuditoriaAgenda
    com acao=BLOQUEADO. Antes do conserto, a tentativa violada não deixava rastro
    (o use case levantava antes do salvar_auditoria e o rollback do savepoint apagava).
    """
    from src.infrastructure.agenda.models import EventoAuditoriaAgenda
    from src.infrastructure.agenda.views import AgendaViewSet
    from src.infrastructure.multitenant.connection import run_in_tenant_context

    tenant = TenantFactory()
    tecnico_id = uuid.uuid4()
    usuario_id = UsuarioFactory().id
    inicia, termina = _slot_futuro()
    with run_in_tenant_context(tenant.id):
        AgendaViewSet._auditar_jornada_bloqueada(
            tenant_id=tenant.id,
            evento_id=uuid.uuid4(),
            tecnico_id=tecnico_id,
            janela_inicia=inicia,
            janela_termina=termina,
            usuario_id=usuario_id,
            perfil_tenant="A",
            detalhe="Jornada UMC violada: R3_TETO_DIARIO.",
        )
        registros = list(
            EventoAuditoriaAgenda.objects.filter(tenant_id=tenant.id, acao="bloqueado")
        )
    assert len(registros) == 1, (
        "INV-AG-JORNADA-UMC-001: tentativa bloqueada não gerou trilha WORM (acao=bloqueado)"
    )
    assert "jornada_umc_violada" in registros[0].payload_resumo


# ===========================================================================
# INV-AG-REGIME-001 — regime NUNCA do payload; IA NUNCA grava override
# ===========================================================================


def test_inv_ag_regime_001_hook_bloqueia_regime_do_payload():
    """INV-AG-REGIME-001 §1: hook bloqueia 'regime' vindo de request.data.

    Barreira: `.claude/hooks/agenda-regime-server-side-check.sh`.
    O regime de jornada NUNCA pode vir do cliente — deriva server-side
    via ColaboradorAgendaAdapter.regime_jornada() (D-AGE-15 / ADR-0067).
    """
    conteudo_violacao = (
        "def criar_slot(request):\n" "    regime = request.data.get('regime')\n" "    return slot\n"
    )
    resultado = _run_hook(
        "agenda-regime-server-side-check.sh",
        _json_tool("src/infrastructure/agenda/serializers.py", conteudo_violacao),
    )
    assert resultado.returncode == 2, (
        f"INV-AG-REGIME-001 §1: hook deveria bloquear (exit 2) regime do payload, "
        f"got exit={resultado.returncode}\nstderr={resultado.stderr}"
    )


def test_inv_ag_regime_001_hook_bloqueia_create_regime_fora_enquadrar():
    """INV-AG-REGIME-001 §2: hook bloqueia RegimeJornadaColaborador.objects.create fora de enquadrar_regime.

    Barreira: `.claude/hooks/agenda-regime-server-side-check.sh`.
    Só humano (RH/gerente) pode gravar override via endpoint dedicado `enquadrar_regime.py`.
    IA NUNCA deve gravar override automaticamente (R6 / D-AGE-15).
    """
    conteudo_violacao = (
        "def processo_colaborador(dados):\n"
        "    RegimeJornadaColaborador.objects.create(regime='motorista_profissional')\n"
    )
    resultado = _run_hook(
        "agenda-regime-server-side-check.sh",
        _json_tool("src/infrastructure/agenda/consumers/colaborador_eventos.py", conteudo_violacao),
    )
    assert resultado.returncode == 2, (
        f"INV-AG-REGIME-001 §2: hook deveria bloquear (exit 2) create de regime fora de "
        f"enquadrar_regime.py, got exit={resultado.returncode}\nstderr={resultado.stderr}"
    )


def test_inv_ag_regime_001_hook_passa_regime_server_side():
    """INV-AG-REGIME-001 (happy): regime derivado server-side → hook permite."""
    conteudo_ok = (
        "def criar_slot(tenant_id, colaborador_id):\n"
        "    regime_info = adapter.regime_jornada(tenant_id=tenant_id, colaborador_id=colaborador_id, na_data=hoje)\n"
        "    return regime_info.regime\n"
    )
    resultado = _run_hook(
        "agenda-regime-server-side-check.sh",
        _json_tool("src/infrastructure/agenda/views.py", conteudo_ok),
    )
    assert resultado.returncode == 0, (
        f"INV-AG-REGIME-001: hook NÃO deveria bloquear regime server-side, "
        f"got exit={resultado.returncode}\nstderr={resultado.stderr}"
    )


@pytest.mark.django_db(transaction=True)
def test_inv_ag_regime_001_papel_atribuido_nao_cria_override():
    """INV-AG-REGIME-001 (runtime): papel_atribuido NÃO grava RegimeJornadaColaborador.

    Barreira: `handle_papel_atribuido` em consumers/colaborador_eventos.py — deve ser
    log-only, nunca grava override (IA NÃO escreve override automático — R6/D-AGE-15).
    """
    from src.infrastructure.agenda.consumers.colaborador_eventos import handle_papel_atribuido
    from src.infrastructure.agenda.models import RegimeJornadaColaborador
    from src.infrastructure.multitenant.connection import run_in_tenant_context

    tenant = TenantFactory()
    colab_id = uuid.uuid4()

    envelope = {
        "event_id": str(uuid.uuid4()),
        "acao": "colaborador.papel_atribuido",
        "tenant_id": str(tenant.id),
        "perfil_no_evento": "D",
        "payload": {"colaborador_id": str(colab_id), "papel": "motorista_umc"},
    }
    antes = RegimeJornadaColaborador.objects.filter(
        tenant_id=tenant.id, colaborador_id=colab_id
    ).count()

    with run_in_tenant_context(tenant.id):
        handle_papel_atribuido(envelope)

    depois = RegimeJornadaColaborador.objects.filter(
        tenant_id=tenant.id, colaborador_id=colab_id
    ).count()

    assert depois == antes, (
        f"INV-AG-REGIME-001 violado: handle_papel_atribuido criou {depois - antes} "
        f"override(s) de regime (esperava 0 — IA NUNCA escreve override automático)"
    )


@pytest.mark.django_db(transaction=True)
def test_inv_ag_regime_001_worm_regime_update_raise():
    """INV-AG-REGIME-001 (WORM): UPDATE em regime_jornada_colaborador → DatabaseError.

    Barreira: trigger `regime_jornada_colaborador_block_update` (migration 0004).
    Regime é INSERT-only — para alterar, insere nova linha com nova vigencia_inicio.
    """
    from django.db import DatabaseError
    from src.infrastructure.agenda.models import RegimeJornadaColaborador
    from src.infrastructure.multitenant.connection import run_in_tenant_context

    tenant = TenantFactory()
    colab_id = uuid.uuid4()
    hoje = date.today()
    ator_id = UsuarioFactory().id

    with run_in_tenant_context(tenant.id):
        regime = RegimeJornadaColaborador.objects.create(
            tenant_id=tenant.id,
            colaborador_id=colab_id,
            regime="clt_geral",
            fonte="override_humano",
            vigencia_inicio=hoje,
            vigencia_fim=None,
            definido_por_usuario_id=ator_id,
            justificativa="motivo de teste para invariante INV-AG-REGIME-001 (>=30 chars ok)",
        )

    with run_in_tenant_context(tenant.id), pytest.raises(DatabaseError):
        RegimeJornadaColaborador.objects.filter(id=regime.id).update(
            regime="motorista_profissional"
        )


# ===========================================================================
# INV-AG-OVERLAP-001 — ExclusionConstraint inclui tenant_id (hook estático)
# ===========================================================================


def test_inv_ag_overlap_001_hook_bloqueia_exclusion_sem_tenant_id():
    """INV-AG-OVERLAP-001: hook bloqueia ExclusionConstraint sem tenant_id.

    Barreira: `.claude/hooks/agenda-overlap-tenant-check.sh`.
    EXCLUDE GIST de overlap DEVE incluir tenant_id como 1ª coluna (ADR-0002 / R1).
    Sem tenant_id, técnico de tenant B pode colidir com slot de tenant A silenciosamente.
    """
    conteudo_violacao = (
        "ExclusionConstraint(\n"
        "    fields=[('tecnico_id', '='), ('slot', '&&')],\n"
        "    condition=Q(estado__ne='cancelado'),\n"
        ")\n"
    )
    resultado = _run_hook(
        "agenda-overlap-tenant-check.sh",
        _json_tool(
            "src/infrastructure/agenda/migrations/0003_exclusion_overlap.py",
            conteudo_violacao,
        ),
    )
    assert resultado.returncode == 2, (
        f"INV-AG-OVERLAP-001: hook deveria bloquear (exit 2) ExclusionConstraint sem tenant_id, "
        f"got exit={resultado.returncode}\nstderr={resultado.stderr}"
    )


def test_inv_ag_overlap_001_hook_passa_com_tenant_id():
    """INV-AG-OVERLAP-001 (happy): ExclusionConstraint com tenant_id → hook permite."""
    conteudo_ok = (
        "ExclusionConstraint(\n"
        "    fields=[('tenant_id', '='), ('tecnico_id', '='), ('slot', '&&')],\n"
        "    condition=Q(estado__ne='cancelado'),\n"
        ")\n"
    )
    resultado = _run_hook(
        "agenda-overlap-tenant-check.sh",
        _json_tool(
            "src/infrastructure/agenda/migrations/0004_fix_overlap.py",
            conteudo_ok,
        ),
    )
    assert resultado.returncode == 0, (
        f"INV-AG-OVERLAP-001: hook NÃO deveria bloquear ExclusionConstraint com tenant_id, "
        f"got exit={resultado.returncode}\nstderr={resultado.stderr}"
    )


# ===========================================================================
# INV-AG-ATIVIDADE-001 — tipo=os exige atividade_id NOT NULL (DB constraint)
# ===========================================================================


@pytest.mark.django_db(transaction=True)
def test_inv_ag_atividade_001_tipo_os_sem_atividade_id_raise():
    """INV-AG-ATIVIDADE-001: EventoAgenda tipo=os com atividade_id=None → IntegrityError.

    Barreira: CHECK constraint `chk_agenda_tipo_os_atividade_id` (migration 0003).
    Todo evento de agendamento de OS deve ter atividade_id (rastreabilidade D-AGE-2/ADR-0023).
    """
    from django.db import IntegrityError
    from src.infrastructure.agenda.models import EventoAgenda
    from src.infrastructure.multitenant.connection import run_in_tenant_context

    tenant = TenantFactory()
    inicia_at, termina_at = _slot_futuro()
    ator_id = UsuarioFactory().id

    with run_in_tenant_context(tenant.id), pytest.raises(IntegrityError):
        EventoAgenda.objects.create(
            tenant_id=tenant.id,
            tecnico_id=uuid.uuid4(),
            tipo="os",
            estado="agendado",
            inicia_at=inicia_at,
            termina_at=termina_at,
            aloca_em_umc=False,
            atividade_id=None,  # violação: tipo=os exige atividade_id NOT NULL
            confirmar_feriado=False,
            descricao_publica="",
            revision=1,
            criado_por_usuario_id=ator_id,
        )


@pytest.mark.django_db(transaction=True)
def test_inv_ag_atividade_001_tipo_os_com_atividade_id_ok():
    """INV-AG-ATIVIDADE-001 (happy): tipo=os com atividade_id → sem erro."""
    tenant = TenantFactory()
    ev = _criar_evento_agenda(tenant, tipo="os", atividade_id=uuid.uuid4(), os_id=uuid.uuid4())
    assert ev.id is not None
    assert ev.atividade_id is not None


@pytest.mark.django_db(transaction=True)
def test_inv_ag_atividade_001_tipo_bloqueio_sem_atividade_id_ok():
    """INV-AG-ATIVIDADE-001: tipo=bloqueio com atividade_id=None → permitido (CHECK só 'os')."""
    tenant = TenantFactory()
    ev = _criar_evento_agenda(tenant, tipo="bloqueio", atividade_id=None)
    assert ev.id is not None


# ===========================================================================
# INV-AG-PERFIL-001 — regime_jornada_colaborador INSERT-only (trigger WORM)
# ===========================================================================
# NOTA: EventoAgenda não tem campo `perfil_no_evento` próprio. INV-AG-PERFIL-001
# garante que o snapshot regulatório (regime) é imutável via INSERT-only em
# regime_jornada_colaborador e evento_auditoria_agenda (triggers migration 0004).


@pytest.mark.django_db(transaction=True)
def test_inv_ag_perfil_001_regime_worm_delete_raise():
    """INV-AG-PERFIL-001 (WORM): DELETE em regime_jornada_colaborador → DatabaseError.

    Barreira: trigger `regime_jornada_colaborador_block_delete` (migration 0004).
    Para encerrar vigência, insere nova linha com vigencia_fim preenchido — nunca DELETE.
    """
    from django.db import DatabaseError
    from src.infrastructure.agenda.models import RegimeJornadaColaborador
    from src.infrastructure.multitenant.connection import run_in_tenant_context

    tenant = TenantFactory()
    colab_id = uuid.uuid4()
    hoje = date.today()
    ator_id = UsuarioFactory().id

    with run_in_tenant_context(tenant.id):
        regime = RegimeJornadaColaborador.objects.create(
            tenant_id=tenant.id,
            colaborador_id=colab_id,
            regime="clt_geral",
            fonte="override_humano",
            vigencia_inicio=hoje,
            vigencia_fim=None,
            definido_por_usuario_id=ator_id,
            justificativa="justificativa de teste INV-AG-PERFIL-001 (>=30 chars ok aqui)",
        )

    with run_in_tenant_context(tenant.id), pytest.raises(DatabaseError):
        RegimeJornadaColaborador.objects.filter(id=regime.id).delete()


@pytest.mark.django_db(transaction=True)
def test_inv_ag_perfil_001_auditoria_agenda_worm_update_raise():
    """INV-AG-PERFIL-001 (WORM): UPDATE em evento_auditoria_agenda → DatabaseError.

    Barreira: trigger `evento_auditoria_agenda_block_update` (migration 0004 — INV-AG-AUDIT-WORM-001).
    Auditoria da agenda é trilha imutável (retenção ≥5 anos — D-AGE-3).
    """
    from django.db import DatabaseError
    from src.infrastructure.agenda.models import EventoAuditoriaAgenda
    from src.infrastructure.multitenant.connection import run_in_tenant_context

    tenant = TenantFactory()
    ev = _criar_evento_agenda(tenant)
    ator_id = UsuarioFactory().id

    with run_in_tenant_context(tenant.id):
        audit = EventoAuditoriaAgenda.objects.create(
            tenant=tenant,
            evento_id=ev.id,
            acao="criado",
            actor_usuario_id=ator_id,
            occurred_at=datetime.now(UTC),
            payload_resumo="teste de invariante INV-AG-PERFIL-001",
        )

    with run_in_tenant_context(tenant.id), pytest.raises(DatabaseError):
        EventoAuditoriaAgenda.objects.filter(id=audit.id).update(payload_resumo="alterado")


# ===========================================================================
# INV-AG-RECORRENCIA-001 — RegraRecorrencia exige rrule_str (RRULE RFC 5545)
# ===========================================================================


def test_inv_ag_recorrencia_001_janela_invalida_inicia_igual_termina_raise():
    """INV-AG-RECORRENCIA-001: Janela com inicia_at == termina_at → ValueError.

    Barreira: `Janela.__post_init__` em value_objects.py. Semântica half-open
    exige inicia_at < termina_at (ADR-0023 / R12 / INV-AG-OVERLAP-001).
    """
    from src.domain.operacao.agenda.value_objects import Janela

    agora = datetime.now(UTC)
    with pytest.raises(ValueError):
        Janela(inicia_at=agora, termina_at=agora)  # igual → inválido


def test_inv_ag_recorrencia_001_janela_invalida_invertida_raise():
    """INV-AG-RECORRENCIA-001: Janela com inicia_at > termina_at → ValueError."""
    from src.domain.operacao.agenda.value_objects import Janela

    agora = datetime.now(UTC)
    with pytest.raises(ValueError):
        Janela(inicia_at=agora, termina_at=agora - timedelta(minutes=1))  # invertido


def test_inv_ag_recorrencia_001_rrule_valido_ok():
    """INV-AG-RECORRENCIA-001 (happy): RegraRecorrencia com RRULE RFC 5545 válida → sem erro."""
    from src.domain.operacao.agenda.value_objects import RegraRecorrencia

    # RRULE RFC 5545 mínima válida: semanal às segundas
    regra = RegraRecorrencia(rrule_str="FREQ=WEEKLY;BYDAY=MO")
    assert regra.rrule_str == "FREQ=WEEKLY;BYDAY=MO"


def test_inv_ag_recorrencia_001_materializar_rrule_invalida_raise():
    """INV-AG-RECORRENCIA-001: materializar_janela com RRULE inválida → ValueError.

    Barreira: `materializar_janela` em recorrencia.py. Frequência não suportada
    levanta ValueError descritivo (puro, determinístico — ADR-0033 / R10).
    """
    from src.domain.operacao.agenda.recorrencia import materializar_janela
    from src.domain.operacao.agenda.value_objects import RegraRecorrencia

    regra_invalida = RegraRecorrencia(rrule_str="FREQ=MINUTELY;INTERVAL=1")
    with pytest.raises(ValueError):
        materializar_janela(regra_invalida, datetime.now(UTC), dias=7)


def test_inv_ag_recorrencia_001_dominio_puro_duracao_janela():
    """INV-AG-RECORRENCIA-001 (domínio puro): Janela.duracao_minutos calculada corretamente."""
    from src.domain.operacao.agenda.value_objects import Janela

    agora = datetime.now(UTC)
    janela = Janela(
        inicia_at=agora,
        termina_at=agora + timedelta(hours=2),
    )
    assert (
        janela.duracao_minutos == 120.0
    ), f"Janela de 2h deve ter 120 minutos, got {janela.duracao_minutos}"


def test_inv_ag_recorrencia_001_sobrepoe_half_open():
    """INV-AG-RECORRENCIA-001: Janela.sobrepoe usa semântica half-open — adjacentes NÃO colidem."""
    from src.domain.operacao.agenda.value_objects import Janela

    agora = datetime.now(UTC)
    j1 = Janela(inicia_at=agora, termina_at=agora + timedelta(hours=1))
    j2 = Janela(inicia_at=agora + timedelta(hours=1), termina_at=agora + timedelta(hours=2))
    # half-open: adjacentes não colidem (espelha EXCLUDE GIST '[)')
    assert not j1.sobrepoe(j2), "Janelas adjacentes NÃO devem se sobrepor (half-open)"

    j3 = Janela(inicia_at=agora + timedelta(minutes=30), termina_at=agora + timedelta(hours=2))
    assert j1.sobrepoe(j3), "Janelas sobrepostas DEVEM se sobrepor"


# ===========================================================================
# INV-AG-CNH-001 — motorista_umc com pendencia_cnh bloqueado via adapter
# ===========================================================================


@pytest.mark.django_db(transaction=True)
def test_inv_ag_cnh_001_pendencia_cnh_retorna_true():
    """INV-AG-CNH-001 (happy): adapter retorna True para motorista com pendência de CNH.

    Barreira: `ColaboradorAgendaAdapter.pendencia_cnh` em adapters.py.
    O motor de criação de evento deve consultar este adapter e bloquear o slot
    se pendencia_cnh=True (D-AGE-11 / INV-AG-CNH-001).
    """
    from src.infrastructure.agenda.adapters import ColaboradorAgendaAdapter
    from src.infrastructure.colaboradores.models import Colaborador, ColaboradorPapel
    from src.infrastructure.multitenant.connection import run_in_tenant_context

    tenant = TenantFactory()
    adapter = ColaboradorAgendaAdapter()
    colab_id = uuid.uuid4()

    with run_in_tenant_context(tenant.id):
        Colaborador.objects.create(
            id=colab_id,
            tenant_id=tenant.id,
            nome="Motorista CNH Pendente",
            cpf="66666666666",
            email="",
            telefone="",
            vinculo="clt",
            data_admissao=date.today(),
            comissao_default_pct=Decimal("0"),
        )
        ColaboradorPapel.objects.create(
            tenant_id=tenant.id,
            colaborador_id=colab_id,
            papel="motorista_umc",
            data_inicio=date.today(),
            pendencia_cnh=True,
        )

    with run_in_tenant_context(tenant.id):
        resultado = adapter.pendencia_cnh(tenant_id=tenant.id, colaborador_id=colab_id)

    assert resultado is True, (
        "INV-AG-CNH-001 violado: adapter deveria retornar True para motorista_umc com "
        "pendencia_cnh=True (D-AGE-11)"
    )


@pytest.mark.django_db(transaction=True)
def test_inv_ag_cnh_001_sem_pendencia_retorna_false():
    """INV-AG-CNH-001 (happy path 2): motorista sem pendência → False."""
    from src.infrastructure.agenda.adapters import ColaboradorAgendaAdapter
    from src.infrastructure.colaboradores.models import Colaborador, ColaboradorPapel
    from src.infrastructure.multitenant.connection import run_in_tenant_context

    tenant = TenantFactory()
    adapter = ColaboradorAgendaAdapter()
    colab_id = uuid.uuid4()

    with run_in_tenant_context(tenant.id):
        Colaborador.objects.create(
            id=colab_id,
            tenant_id=tenant.id,
            nome="Motorista CNH OK",
            cpf="77777777777",
            email="",
            telefone="",
            vinculo="clt",
            data_admissao=date.today(),
            comissao_default_pct=Decimal("0"),
        )
        ColaboradorPapel.objects.create(
            tenant_id=tenant.id,
            colaborador_id=colab_id,
            papel="motorista_umc",
            data_inicio=date.today(),
            pendencia_cnh=False,
        )

    with run_in_tenant_context(tenant.id):
        resultado = adapter.pendencia_cnh(tenant_id=tenant.id, colaborador_id=colab_id)

    assert resultado is False


# ===========================================================================
# INV-AG-AUDIT-WORM-001 — wiring adapter registrado no boot (AgendaConfig.ready)
# ===========================================================================


def test_inv_ag_audit_worm_001_adapter_registrado_no_boot():
    """INV-AG-AUDIT-WORM-001: AgendaConfig.ready() registra AgendaColaboradorReferenciadoAdapter.

    Barreira: `AgendaConfig.ready()` em apps.py injeta o adapter em
    `ColaboradorViewSet._referenciado_agenda_port`. Verifica que o atributo
    existe e implementa `esta_referenciado` (duck-typing — ADR-0066 / T-AGE-045).
    """
    from django.apps import apps

    apps.get_app_config("agenda")  # garante ready() executado

    from src.infrastructure.agenda.referenciado import AgendaColaboradorReferenciadoAdapter
    from src.infrastructure.colaboradores.views import ColaboradorViewSet

    adapter = getattr(ColaboradorViewSet, "_referenciado_agenda_port", None)

    assert adapter is not None, (
        "INV-AG-AUDIT-WORM-001 violado: ColaboradorViewSet._referenciado_agenda_port não foi "
        "injetado pelo AgendaConfig.ready() (T-AGE-045 / D-AGE-12)"
    )
    assert isinstance(adapter, AgendaColaboradorReferenciadoAdapter), (
        f"INV-AG-AUDIT-WORM-001: adapter deve ser AgendaColaboradorReferenciadoAdapter, "
        f"got {type(adapter)!r}"
    )
    assert callable(getattr(adapter, "esta_referenciado", None)), (
        "INV-AG-AUDIT-WORM-001: adapter não implementa esta_referenciado "
        "(contrato ColaboradorReferenciadoPort)"
    )


@pytest.mark.django_db(transaction=True)
def test_inv_ag_audit_worm_001_esta_referenciado_com_agenda_futura():
    """INV-AG-AUDIT-WORM-001 (T-AGE-048 happy): técnico com agenda futura → esta_referenciado=True.

    Barreira: `AgendaColaboradorReferenciadoAdapter.esta_referenciado` delega a
    `DjangoEventoAgendaRepository.tem_agenda_futura` — técnico com evento futuro
    não-cancelado deve retornar True (bloqueia hard-delete — D-AGE-12 / T-AGE-045).
    """
    from src.infrastructure.agenda.referenciado import AgendaColaboradorReferenciadoAdapter
    from src.infrastructure.multitenant.connection import run_in_tenant_context

    tenant = TenantFactory()
    tecnico_id = uuid.uuid4()

    # Cria evento FUTURO não-cancelado
    _criar_evento_agenda(tenant, tecnico_id=tecnico_id, estado="agendado", dias_futuro=5)

    adapter = AgendaColaboradorReferenciadoAdapter()
    with run_in_tenant_context(tenant.id):
        resultado = adapter.esta_referenciado(colaborador_id=tecnico_id, tenant_id=tenant.id)

    assert resultado is True, (
        "INV-AG-AUDIT-WORM-001 violado: esta_referenciado deve retornar True quando "
        "o técnico tem agenda futura não-cancelada (D-AGE-12 / T-AGE-045)"
    )


@pytest.mark.django_db(transaction=True)
def test_inv_ag_audit_worm_001_esta_referenciado_sem_agenda_permite_delete():
    """INV-AG-AUDIT-WORM-001 (T-AGE-048 sem-agenda): técnico sem agenda futura → False.

    Sem agenda futura não-cancelada, hard-delete pode prosseguir (se não há outra
    referência em outros módulos). Garante que o adapter não bloqueia sem causa.
    """
    from src.infrastructure.agenda.referenciado import AgendaColaboradorReferenciadoAdapter
    from src.infrastructure.multitenant.connection import run_in_tenant_context

    tenant = TenantFactory()
    tecnico_id = uuid.uuid4()  # sem nenhum evento criado

    adapter = AgendaColaboradorReferenciadoAdapter()
    with run_in_tenant_context(tenant.id):
        resultado = adapter.esta_referenciado(colaborador_id=tecnico_id, tenant_id=tenant.id)

    assert resultado is False, (
        "INV-AG-AUDIT-WORM-001: esta_referenciado deve retornar False quando técnico "
        "não tem agenda futura (hard-delete permitido — D-AGE-12)"
    )


@pytest.mark.django_db(transaction=True)
def test_inv_ag_audit_worm_001_esta_referenciado_evento_cancelado_nao_bloqueia():
    """INV-AG-AUDIT-WORM-001 (T-AGE-048 cancelado): evento futuro CANCELADO não bloqueia."""
    from src.infrastructure.agenda.referenciado import AgendaColaboradorReferenciadoAdapter
    from src.infrastructure.multitenant.connection import run_in_tenant_context

    tenant = TenantFactory()
    tecnico_id = uuid.uuid4()

    # Evento futuro mas CANCELADO → não deve bloquear
    _criar_evento_agenda(tenant, tecnico_id=tecnico_id, estado="cancelado", dias_futuro=3)

    adapter = AgendaColaboradorReferenciadoAdapter()
    with run_in_tenant_context(tenant.id):
        resultado = adapter.esta_referenciado(colaborador_id=tecnico_id, tenant_id=tenant.id)

    assert resultado is False, (
        "INV-AG-AUDIT-WORM-001: evento CANCELADO não deve bloquear hard-delete "
        "(esta_referenciado deve retornar False)"
    )


# ===========================================================================
# INV-AG-NOSHOW-AR001 — no-show cobrável chama AReceberPort DENTRO do use case,
# de forma atômica (falha propaga). Barreira REAL = registrar_no_show.executar.
# ===========================================================================


def _evento_agendado_no_fake(repo, *, tenant_id, tecnico_id):
    """Cria e salva um EventoAgenda AGENDADO no fake repo (alvo do no-show)."""
    from src.domain.operacao.agenda.entities import EventoAgenda
    from src.domain.operacao.agenda.enums import EstadoEvento, TipoEvento

    agora = datetime.now(UTC)
    evento = EventoAgenda(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        tecnico_id=tecnico_id,
        tipo=TipoEvento.OS,
        estado=EstadoEvento.AGENDADO,
        inicia_at=agora + timedelta(days=1),
        termina_at=agora + timedelta(days=1, hours=2),
        aloca_em_umc=False,
        criado_por_usuario_id=uuid.uuid4(),
        criado_em=agora,
        atualizado_em=agora,
        revision=0,
        atividade_id=uuid.uuid4(),
    )
    repo.salvar_novo(evento)
    return evento


class TestINVAGNoShowAR001:
    """INV-AG-NOSHOW-AR-001: no-show cobrável exige cliente_id+custo>0 e chama AReceber
    DENTRO da transação; a falha PROPAGA (atomicidade — nunca no-show cobrável sem título)."""

    def _portas(self):
        from tests.fakes.agenda_fakes import FakeAReceberPort, FakeEventoAgendaRepository

        return FakeEventoAgendaRepository(), FakeAReceberPort()

    def test_inv_ag_noshow_ar001_cobravel_chama_areceber_uma_vez(self):
        """Barreira real: cobrável (cliente+custo) → AReceberPort chamado exatamente 1x."""
        from src.application.operacao.agenda import registrar_no_show

        repo, areceber = self._portas()
        tenant_id, tecnico_id = uuid.uuid4(), uuid.uuid4()
        evento = _evento_agendado_no_fake(repo, tenant_id=tenant_id, tecnico_id=tecnico_id)
        inp = registrar_no_show.RegistrarNoShowInput(
            tenant_id=tenant_id,
            evento_id=evento.id,
            registrado_por_usuario_id=uuid.uuid4(),
            perfil_tenant="A",
            cobrar_cliente=True,
            custo_estimado_centavos=5000,
            cliente_id=uuid.uuid4(),
        )
        out = registrar_no_show.executar(inp, repo=repo, areceber_port=areceber)
        assert out.titulo_criado is True
        assert len(areceber.chamadas) == 1

    def test_inv_ag_noshow_ar001_falha_cobranca_propaga_nao_engole(self):
        """A1: se criar_titulo_manual falha, a exceção PROPAGA (não é engolida)."""
        from src.application.operacao.agenda import registrar_no_show

        from tests.fakes.agenda_fakes import FakeAReceberPort, FakeEventoAgendaRepository

        repo = FakeEventoAgendaRepository()
        areceber = FakeAReceberPort(deve_falhar=True)
        tenant_id, tecnico_id = uuid.uuid4(), uuid.uuid4()
        evento = _evento_agendado_no_fake(repo, tenant_id=tenant_id, tecnico_id=tecnico_id)
        inp = registrar_no_show.RegistrarNoShowInput(
            tenant_id=tenant_id,
            evento_id=evento.id,
            registrado_por_usuario_id=uuid.uuid4(),
            perfil_tenant="A",
            cobrar_cliente=True,
            custo_estimado_centavos=5000,
            cliente_id=uuid.uuid4(),
        )
        with pytest.raises(RuntimeError):
            registrar_no_show.executar(inp, repo=repo, areceber_port=areceber)

    def test_inv_ag_noshow_ar001_cobravel_sem_cliente_id_raise(self):
        """A3: cobrar_cliente=True sem cliente_id → ValueError (nunca cliente-fantasma)."""
        from src.application.operacao.agenda import registrar_no_show

        repo, areceber = self._portas()
        tenant_id, tecnico_id = uuid.uuid4(), uuid.uuid4()
        evento = _evento_agendado_no_fake(repo, tenant_id=tenant_id, tecnico_id=tecnico_id)
        inp = registrar_no_show.RegistrarNoShowInput(
            tenant_id=tenant_id,
            evento_id=evento.id,
            registrado_por_usuario_id=uuid.uuid4(),
            perfil_tenant="A",
            cobrar_cliente=True,
            custo_estimado_centavos=5000,
            cliente_id=None,
        )
        with pytest.raises(ValueError, match="cliente_id"):
            registrar_no_show.executar(inp, repo=repo, areceber_port=areceber)
        assert len(areceber.chamadas) == 0
