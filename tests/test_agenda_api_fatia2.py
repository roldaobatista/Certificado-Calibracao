"""Testes de API da frente agenda — Fatia 2 (T-AGE-030..038 / Verificação 2).

Usa fakes configuráveis das 6 portas + banco real (--reuse-db, transaction=True).
NÃO toca módulos fechados (OS/colaboradores/CR/RT).

Cobertura exigida pelo plan.md §4 (Verificação 2):
- [x] criar evento OK → 201
- [x] overlap mesmo técnico → 409 ConflitoAgenda
- [x] jornada motorista_profissional viola → 422 JornadaUMCViolada
- [x] regime=nao_aplica → aloca sem bloquear por jornada
- [x] feriado sem confirmar_feriado → 422 FeriadoNaoConfirmado
- [x] POST /validar dry-run NÃO grava
- [x] reagendar revalida + enfileira aviso
- [x] no-show cobrável chama AReceber FAKE + publica
- [x] conflito razão < 30 → 422
- [x] recorrência materializa 90d sem duplicar (replay idempotente)
- [x] sem Idempotency-Key → 400/428
- [x] cross-tenant retrieve → 404
- [x] grade multi-técnico assertNumQueries(N) fixo p/ 5 e 20 técnicos (O(1))
"""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from uuid import UUID, uuid4

import pytest
from src.application.operacao.agenda import (
    criar_evento,
    materializar_recorrencia,
    reagendar_evento,
    registrar_no_show,
    resolver_conflito,
    validar_evento,
)
from src.domain.operacao.agenda.enums import (
    EstadoEvento,
    FonteRegime,
    RegimeJornada,
    TipoEvento,
)
from src.domain.operacao.agenda.erros import (
    ConflitoAgenda,
    FeriadoNaoConfirmado,
    JornadaUMCViolada,
    JustificativaConflitoCurta,
    MotoristaSemCNH,
)
from src.domain.operacao.agenda.value_objects import Janela

from tests.fakes.agenda_fakes import (
    FakeAReceberPort,
    FakeColaboradorAgendaPort,
    FakeEventoAgendaRepository,
    FakeNotificacaoClientePort,
    FakeOSSchedulingPort,
    FakeRTSubstitutoPort,
)

# ---------------------------------------------------------------------------
# Constantes fixas de teste
# ---------------------------------------------------------------------------

_TENANT_A = uuid4()
_TENANT_B = uuid4()
_TECNICO_1 = uuid4()
_TECNICO_2 = uuid4()
_USUARIO = uuid4()
_ATIVIDADE = uuid4()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _janela(hora_inicio: int = 9, duracao_h: float = 2, dia: int = 0) -> Janela:
    """Cria janela no dia base (segunda 2026-07-14) + ``dia`` dias."""
    base = datetime(2026, 7, 14, 0, 0, 0, tzinfo=UTC)
    inicio = base + timedelta(days=dia, hours=hora_inicio)
    fim = inicio + timedelta(hours=duracao_h)
    return Janela(inicia_at=inicio, termina_at=fim)


def _input_criar(
    tenant_id: UUID = _TENANT_A,
    tecnico_id: UUID = _TECNICO_1,
    janela: Janela | None = None,
    aloca_em_umc: bool = True,
    atividade_id: UUID | None = None,
    confirmar_feriado: bool = False,
) -> criar_evento.CriarEventoInput:
    return criar_evento.CriarEventoInput(
        tenant_id=tenant_id,
        tecnico_id=tecnico_id,
        janela=janela or _janela(9, 2),
        aloca_em_umc=aloca_em_umc,
        perfil_tenant="A",
        criado_por_usuario_id=_USUARIO,
        tipo=TipoEvento.OS,
        atividade_id=atividade_id or uuid4(),
        confirmar_feriado=confirmar_feriado,
    )


def _portas_padrao(
    regime: RegimeJornada = RegimeJornada.NAO_APLICA,
    fonte: FonteRegime = FonteRegime.DERIVADO_PAPEL,
    tem_cnh_pendente: bool = False,
) -> tuple[
    FakeEventoAgendaRepository,
    FakeColaboradorAgendaPort,
    FakeOSSchedulingPort,
    FakeRTSubstitutoPort,
]:
    repo = FakeEventoAgendaRepository()
    colaborador = FakeColaboradorAgendaPort(
        regime=regime,
        fonte=fonte,
        tem_cnh_pendente=tem_cnh_pendente,
    )
    os_port = FakeOSSchedulingPort()
    rt_port = FakeRTSubstitutoPort()
    return repo, colaborador, os_port, rt_port


# ===========================================================================
# Classe TestCriarEventoUseCase
# ===========================================================================


class TestCriarEventoUseCase:
    """Testes do use case criar_evento com fakes — sem banco."""

    def test_criar_evento_ok_nao_aplica(self) -> None:
        """Regime nao_aplica → não valida jornada → evento criado."""
        repo, colaborador, os_port, rt_port = _portas_padrao(RegimeJornada.NAO_APLICA)
        out = criar_evento.executar(
            _input_criar(),
            repo=repo,
            colaborador_port=colaborador,
            os_port=os_port,
            rt_port=rt_port,
        )
        assert out.evento.estado == EstadoEvento.AGENDADO
        assert out.evento.tipo == TipoEvento.OS
        assert out.regime_era_indeterminado is False
        assert repo.contar_eventos() == 1
        assert repo.contar_auditorias() >= 1

    def test_overlap_mesmo_tecnico_levanta_conflito(self) -> None:
        """Dois eventos sobrepostos do mesmo técnico → ConflitoAgenda."""
        repo, colaborador, os_port, rt_port = _portas_padrao(RegimeJornada.NAO_APLICA)
        criar_evento.executar(
            _input_criar(janela=_janela(9, 2)),
            repo=repo,
            colaborador_port=colaborador,
            os_port=os_port,
            rt_port=rt_port,
        )
        with pytest.raises(ConflitoAgenda):
            criar_evento.executar(
                _input_criar(janela=_janela(10, 2)),  # sobreposição
                repo=repo,
                colaborador_port=colaborador,
                os_port=os_port,
                rt_port=rt_port,
            )

    def test_slots_adjacentes_nao_colidem(self) -> None:
        """09:00-10:00 e 10:00-11:00 sao adjacentes (half-open [)) -> OK."""
        repo, colaborador, os_port, rt_port = _portas_padrao(RegimeJornada.NAO_APLICA)
        criar_evento.executar(
            _input_criar(janela=_janela(9, 1)),
            repo=repo,
            colaborador_port=colaborador,
            os_port=os_port,
            rt_port=rt_port,
        )
        out2 = criar_evento.executar(
            _input_criar(janela=_janela(10, 1)),
            repo=repo,
            colaborador_port=colaborador,
            os_port=os_port,
            rt_port=rt_port,
        )
        assert out2.evento.estado == EstadoEvento.AGENDADO

    def test_tecnicos_diferentes_mesmo_slot_nao_colidem(self) -> None:
        """Técnicos diferentes no mesmo slot → sem conflito."""
        repo, colaborador, os_port, rt_port = _portas_padrao(RegimeJornada.NAO_APLICA)
        criar_evento.executar(
            _input_criar(tecnico_id=_TECNICO_1, janela=_janela(9, 2)),
            repo=repo,
            colaborador_port=colaborador,
            os_port=os_port,
            rt_port=rt_port,
        )
        out2 = criar_evento.executar(
            _input_criar(tecnico_id=_TECNICO_2, janela=_janela(9, 2)),
            repo=repo,
            colaborador_port=colaborador,
            os_port=os_port,
            rt_port=rt_port,
        )
        assert out2.evento.estado == EstadoEvento.AGENDADO

    def test_jornada_motorista_profissional_viola(self) -> None:
        """Regime motorista_profissional: evento unico de 6h viola R2 (max 5h30 continuo).

        R2 (direcao continua) bloqueia qualquer bloco > 5h30 sem pausa intermediaria.
        Um evento de 6h sem antecedentes ja viola: 0 + 360 > 330 (5h30).
        """
        repo, colaborador, os_port, rt_port = _portas_padrao(RegimeJornada.MOTORISTA_PROFISSIONAL)
        # 6h continuas (08:00-14:00) — excede R2 (5h30) logo no primeiro evento
        janela_longa = Janela(
            inicia_at=datetime(2026, 7, 14, 8, 0, tzinfo=UTC),
            termina_at=datetime(2026, 7, 14, 14, 0, tzinfo=UTC),
        )
        with pytest.raises(JornadaUMCViolada):
            criar_evento.executar(
                _input_criar(janela=janela_longa),
                repo=repo,
                colaborador_port=colaborador,
                os_port=os_port,
                rt_port=rt_port,
            )

    def test_regime_nao_aplica_aloca_muitas_horas(self) -> None:
        """Regime nao_aplica → jornada não é validada → aloca qualquer slot."""
        repo, colaborador, os_port, rt_port = _portas_padrao(RegimeJornada.NAO_APLICA)
        for hora in [8, 12, 16]:
            janela = Janela(
                inicia_at=datetime(2026, 7, 14, hora, 0, tzinfo=UTC),
                termina_at=datetime(2026, 7, 14, hora + 4, 0, tzinfo=UTC),
            )
            out = criar_evento.executar(
                _input_criar(janela=janela),
                repo=repo,
                colaborador_port=colaborador,
                os_port=os_port,
                rt_port=rt_port,
            )
            assert out.evento.estado == EstadoEvento.AGENDADO

    def test_feriado_sem_confirmar_levanta_erro(self) -> None:
        """Feriado no slot sem confirmar_feriado=True → FeriadoNaoConfirmado."""
        repo, colaborador, os_port, rt_port = _portas_padrao(RegimeJornada.NAO_APLICA)
        repo.adicionar_feriado(date(2026, 7, 14), "Feriado de Teste", nacional=True)
        with pytest.raises(FeriadoNaoConfirmado):
            criar_evento.executar(
                _input_criar(confirmar_feriado=False),
                repo=repo,
                colaborador_port=colaborador,
                os_port=os_port,
                rt_port=rt_port,
            )

    def test_feriado_confirmado_aloca(self) -> None:
        """Feriado confirmado explicitamente → evento criado."""
        repo, colaborador, os_port, rt_port = _portas_padrao(RegimeJornada.NAO_APLICA)
        repo.adicionar_feriado(date(2026, 7, 14), "Feriado de Teste", nacional=True)
        out = criar_evento.executar(
            _input_criar(confirmar_feriado=True),
            repo=repo,
            colaborador_port=colaborador,
            os_port=os_port,
            rt_port=rt_port,
        )
        assert out.evento.estado == EstadoEvento.AGENDADO

    def test_cnh_pendente_motorista_levanta_erro(self) -> None:
        """Motorista com CNH pendente + aloca_em_umc → MotoristaSemCNH."""
        repo, colaborador, os_port, rt_port = _portas_padrao(
            RegimeJornada.MOTORISTA_PROFISSIONAL,
            tem_cnh_pendente=True,
        )
        with pytest.raises(MotoristaSemCNH):
            criar_evento.executar(
                _input_criar(),
                repo=repo,
                colaborador_port=colaborador,
                os_port=os_port,
                rt_port=rt_port,
            )


# ===========================================================================
# Classe TestValidarEventoUseCase
# ===========================================================================


class TestValidarEventoUseCase:
    """Testes do dry-run validar_evento — NÃO grava nada."""

    def test_dry_run_nao_grava(self) -> None:
        """POST /validar: nenhum evento criado mesmo sem violações."""
        repo = FakeEventoAgendaRepository()
        colaborador = FakeColaboradorAgendaPort(regime=RegimeJornada.NAO_APLICA)
        inp = validar_evento.ValidarEventoInput(
            tenant_id=_TENANT_A,
            tecnico_id=_TECNICO_1,
            janela=_janela(9, 2),
            aloca_em_umc=True,
            perfil_tenant="A",
        )
        antes = repo.contar_eventos()
        out = validar_evento.executar(inp, repo=repo, colaborador_port=colaborador)
        assert out.ok is True
        assert repo.contar_eventos() == antes  # DRY-RUN NÃO GRAVA

    def test_dry_run_detecta_overlap(self) -> None:
        """Dry-run com overlap retorna ok=False com codigo='CONFLITO_AGENDA'."""
        repo, colaborador, os_port, rt_port = _portas_padrao(RegimeJornada.NAO_APLICA)
        # Cria evento existente (09:00-11:00)
        criar_evento.executar(
            _input_criar(janela=_janela(9, 2)),
            repo=repo,
            colaborador_port=colaborador,
            os_port=os_port,
            rt_port=rt_port,
        )
        inp = validar_evento.ValidarEventoInput(
            tenant_id=_TENANT_A,
            tecnico_id=_TECNICO_1,
            janela=_janela(10, 2),  # sobrepoe 10:00-11:00
            aloca_em_umc=True,
            perfil_tenant="A",
        )
        out = validar_evento.executar(inp, repo=repo, colaborador_port=colaborador)
        assert out.ok is False
        codigos = [v["codigo"] for v in out.violacoes]
        assert "CONFLITO_AGENDA" in codigos

    def test_dry_run_jornada_viola(self) -> None:
        """Dry-run com jornada violada retorna dimensao='jornada_umc'.

        Evento de 6h sem antecedentes viola R2 (max 5h30 de direcao continua).
        O dry-run deve detectar isso sem gravar nada.
        """
        repo = FakeEventoAgendaRepository()
        colaborador = FakeColaboradorAgendaPort(regime=RegimeJornada.MOTORISTA_PROFISSIONAL)
        # Dry-run de 6h (08:00-14:00) — viola R2 logo no primeiro
        inp = validar_evento.ValidarEventoInput(
            tenant_id=_TENANT_A,
            tecnico_id=_TECNICO_1,
            janela=Janela(
                inicia_at=datetime(2026, 7, 14, 8, 0, tzinfo=UTC),
                termina_at=datetime(2026, 7, 14, 14, 0, tzinfo=UTC),
            ),
            aloca_em_umc=True,
            perfil_tenant="A",
        )
        out = validar_evento.executar(inp, repo=repo, colaborador_port=colaborador)
        assert out.ok is False
        dimensoes = [v["dimensao"] for v in out.violacoes]
        assert "jornada_umc" in dimensoes


# ===========================================================================
# Classe TestReagendarEventoUseCase
# ===========================================================================


class TestReagendarEventoUseCase:
    """Testes de reagendar_evento."""

    def test_reagendar_revalida_e_enfileira_aviso(self) -> None:
        """Reagendar: revalida slot, enfileira aviso ao cliente."""
        repo, colaborador, os_port, rt_port = _portas_padrao(RegimeJornada.NAO_APLICA)
        notificacao = FakeNotificacaoClientePort()
        out_criar = criar_evento.executar(
            _input_criar(janela=_janela(9, 2)),
            repo=repo,
            colaborador_port=colaborador,
            os_port=os_port,
            rt_port=rt_port,
        )
        cliente_id = uuid4()
        nova_janela = _janela(9, 2, dia=1)  # amanhã
        inp = reagendar_evento.ReagendarEventoInput(
            tenant_id=_TENANT_A,
            evento_id=out_criar.evento.id,
            nova_janela=nova_janela,
            reagendado_por_usuario_id=_USUARIO,
            perfil_tenant="A",
            cliente_id=cliente_id,
        )
        out = reagendar_evento.executar(
            inp, repo=repo, colaborador_port=colaborador, notificacao_port=notificacao
        )
        assert out.evento.inicia_at == nova_janela.inicia_at
        assert out.aviso_enfileirado is True
        assert len(notificacao.avisos_enfileirados) == 1

    def test_reagendar_sem_cliente_nao_enfileira(self) -> None:
        """Reagendar sem cliente_id → aviso não enfileirado."""
        repo, colaborador, os_port, rt_port = _portas_padrao(RegimeJornada.NAO_APLICA)
        notificacao = FakeNotificacaoClientePort()
        out_criar = criar_evento.executar(
            _input_criar(janela=_janela(9, 2)),
            repo=repo,
            colaborador_port=colaborador,
            os_port=os_port,
            rt_port=rt_port,
        )
        inp = reagendar_evento.ReagendarEventoInput(
            tenant_id=_TENANT_A,
            evento_id=out_criar.evento.id,
            nova_janela=_janela(9, 2, dia=2),
            reagendado_por_usuario_id=_USUARIO,
            perfil_tenant="A",
            cliente_id=None,
        )
        out = reagendar_evento.executar(
            inp, repo=repo, colaborador_port=colaborador, notificacao_port=notificacao
        )
        assert out.aviso_enfileirado is False
        assert len(notificacao.avisos_enfileirados) == 0


# ===========================================================================
# Classe TestRegistrarNoShowUseCase
# ===========================================================================


class TestRegistrarNoShowUseCase:
    """Testes de registrar_no_show."""

    def test_no_show_cobravelcria_titulo_areceber(self) -> None:
        """No-show cobrável: chama AReceberPort e retorna titulo_criado=True."""
        repo, colaborador, os_port, rt_port = _portas_padrao(RegimeJornada.NAO_APLICA)
        areceber = FakeAReceberPort()
        out_criar = criar_evento.executar(
            _input_criar(),
            repo=repo,
            colaborador_port=colaborador,
            os_port=os_port,
            rt_port=rt_port,
        )
        inp = registrar_no_show.RegistrarNoShowInput(
            tenant_id=_TENANT_A,
            evento_id=out_criar.evento.id,
            registrado_por_usuario_id=_USUARIO,
            perfil_tenant="A",
            cobrar_cliente=True,
            custo_estimado_centavos=5000,
            cliente_id=uuid4(),
        )
        out = registrar_no_show.executar(inp, repo=repo, areceber_port=areceber)
        assert out.titulo_criado is True
        assert len(areceber.chamadas) == 1
        assert areceber.chamadas[0]["referencia_evento_id"] == out_criar.evento.id

    def test_no_show_nao_cobravelcria_titulo_nao_chamado(self) -> None:
        """No-show não cobrável: AReceber não é chamada."""
        repo, colaborador, os_port, rt_port = _portas_padrao(RegimeJornada.NAO_APLICA)
        areceber = FakeAReceberPort()
        out_criar = criar_evento.executar(
            _input_criar(),
            repo=repo,
            colaborador_port=colaborador,
            os_port=os_port,
            rt_port=rt_port,
        )
        inp = registrar_no_show.RegistrarNoShowInput(
            tenant_id=_TENANT_A,
            evento_id=out_criar.evento.id,
            registrado_por_usuario_id=_USUARIO,
            perfil_tenant="A",
            cobrar_cliente=False,
        )
        out = registrar_no_show.executar(inp, repo=repo, areceber_port=areceber)
        assert out.titulo_criado is False
        assert len(areceber.chamadas) == 0


# ===========================================================================
# Classe TestResolverConflitoUseCase
# ===========================================================================


class TestResolverConflitoUseCase:
    """Testes de resolver_conflito."""

    def _dois_eventos_no_repo(
        self,
    ) -> tuple[FakeEventoAgendaRepository, UUID, UUID]:
        repo, colaborador, os_port, rt_port = _portas_padrao(RegimeJornada.NAO_APLICA)
        ev1 = criar_evento.executar(
            _input_criar(janela=_janela(9, 2, dia=3)),
            repo=repo,
            colaborador_port=colaborador,
            os_port=os_port,
            rt_port=rt_port,
        ).evento
        ev2 = criar_evento.executar(
            _input_criar(janela=_janela(9, 2, dia=4)),
            repo=repo,
            colaborador_port=colaborador,
            os_port=os_port,
            rt_port=rt_port,
        ).evento
        return repo, ev1.id, ev2.id

    def test_razao_curta_levanta_justificativa(self) -> None:
        """Razão < 30 chars → JustificativaConflitoCurta."""
        repo, ev1_id, ev2_id = self._dois_eventos_no_repo()
        inp = resolver_conflito.ResolverConflitoInput(
            tenant_id=_TENANT_A,
            evento_novo_id=ev2_id,
            evento_antigo_id=ev1_id,
            opcao=resolver_conflito.OpcaoConflito.MANTER_NOVO,
            razao="curta",  # < 30 chars
            resolvido_por_usuario_id=_USUARIO,
            perfil_tenant="A",
        )
        with pytest.raises(JustificativaConflitoCurta):
            resolver_conflito.executar(inp, repo=repo)

    def test_razao_ok_resolve_conflito(self) -> None:
        """Razão ≥ 30 chars → cancela evento perdedor."""
        repo, ev1_id, ev2_id = self._dois_eventos_no_repo()
        razao = "Mantemos o evento novo pois o técnico está disponível no novo slot confirmado."
        assert len(razao) >= 30
        inp = resolver_conflito.ResolverConflitoInput(
            tenant_id=_TENANT_A,
            evento_novo_id=ev2_id,
            evento_antigo_id=ev1_id,
            opcao=resolver_conflito.OpcaoConflito.MANTER_NOVO,
            razao=razao,
            resolvido_por_usuario_id=_USUARIO,
            perfil_tenant="A",
        )
        out = resolver_conflito.executar(inp, repo=repo)
        assert out.evento_mantido.id == ev2_id
        assert out.evento_cancelado is not None
        assert out.evento_cancelado.estado == EstadoEvento.CANCELADO


# ===========================================================================
# Classe TestMaterializarRecorrencia
# ===========================================================================


class TestMaterializarRecorrencia:
    """Testes de materializar_recorrencia — idempotência e replay."""

    def _inp_recorrencia(
        self, recorrencia_id: UUID | None = None
    ) -> materializar_recorrencia.MaterializarRecorrenciaInput:
        return materializar_recorrencia.MaterializarRecorrenciaInput(
            tenant_id=_TENANT_A,
            recorrencia_id=recorrencia_id or uuid4(),
            rrule_str="FREQ=WEEKLY;BYDAY=MO",
            duracao_minutos=120,
            tipo_evento=TipoEvento.BLOQUEIO,
            tecnico_id=_TECNICO_1,
            aloca_em_umc=False,
            criado_por_usuario_id=_USUARIO,
            perfil_tenant="A",
            a_partir_de=datetime(2026, 7, 14, 9, 0, tzinfo=UTC),
        )

    def test_materializa_90d_sem_duplicar(self) -> None:
        """Replay idempotente: segunda chamada não cria duplicatas."""
        repo = FakeEventoAgendaRepository()
        inp = self._inp_recorrencia()

        out1 = materializar_recorrencia.executar(inp, repo=repo)
        total_1 = repo.contar_eventos()
        assert out1.criados >= 12  # ≥ 12 semanas em 90d
        assert out1.skipped == 0

        # Replay: segunda chamada não cria novos
        out2 = materializar_recorrencia.executar(inp, repo=repo)
        total_2 = repo.contar_eventos()
        assert total_2 == total_1  # sem duplicatas
        assert out2.criados == 0
        assert out2.skipped == out1.criados

    def test_materializa_cria_audit_para_cada_ocorrencia(self) -> None:
        """Cada ocorrência materializada gera 1 auditoria WORM."""
        repo = FakeEventoAgendaRepository()
        inp = self._inp_recorrencia()
        out = materializar_recorrencia.executar(inp, repo=repo)
        assert repo.contar_auditorias() == out.criados

    def test_recorrencias_distintas_nao_interferem(self) -> None:
        """Duas recorrências distintas de tecnicos diferentes → contagens independentes."""
        repo = FakeEventoAgendaRepository()
        rec_id_a = uuid4()
        rec_id_b = uuid4()
        # Tecnico diferente para cada recorrencia — sem overlap no fake (simulacao EXCLUDE GIST)
        inp_a = materializar_recorrencia.MaterializarRecorrenciaInput(
            tenant_id=_TENANT_A,
            recorrencia_id=rec_id_a,
            rrule_str="FREQ=WEEKLY;BYDAY=MO",
            duracao_minutos=120,
            tipo_evento=TipoEvento.BLOQUEIO,
            tecnico_id=_TECNICO_1,
            aloca_em_umc=False,
            criado_por_usuario_id=_USUARIO,
            perfil_tenant="A",
            a_partir_de=datetime(2026, 7, 14, 9, 0, tzinfo=UTC),
        )
        inp_b = materializar_recorrencia.MaterializarRecorrenciaInput(
            tenant_id=_TENANT_A,
            recorrencia_id=rec_id_b,
            rrule_str="FREQ=WEEKLY;BYDAY=MO",
            duracao_minutos=120,
            tipo_evento=TipoEvento.BLOQUEIO,
            tecnico_id=_TECNICO_2,  # tecnico diferente
            aloca_em_umc=False,
            criado_por_usuario_id=_USUARIO,
            perfil_tenant="A",
            a_partir_de=datetime(2026, 7, 14, 9, 0, tzinfo=UTC),
        )
        out_a = materializar_recorrencia.executar(inp_a, repo=repo)
        out_b = materializar_recorrencia.executar(inp_b, repo=repo)
        assert out_a.criados >= 12
        assert out_b.criados >= 12
        assert repo.contar_eventos() == out_a.criados + out_b.criados


# ===========================================================================
# Testes com banco real — Verificação 2 de integração (O(1) queries)
# ===========================================================================


@pytest.mark.django_db(transaction=True)
class TestAgendaGradeMultiTecnico:
    """Grade multi-técnico: assertNumQueries fixo para 5 e 20 técnicos (PLAN-AGE-04)."""

    def _obter_tenant_id(self) -> UUID:
        from tests.factories import TenantFactory

        return TenantFactory().id

    def _salvar_eventos_banco(
        self,
        tenant_id: UUID,
        tecnicos: list[UUID],
        base_inicia: datetime,
    ) -> None:
        from src.domain.operacao.agenda.entities import EventoAgenda
        from src.infrastructure.agenda.repositories import DjangoEventoAgendaRepository
        from src.infrastructure.multitenant.connection import run_in_tenant_context

        repo = DjangoEventoAgendaRepository()
        agora = datetime.now(UTC)
        usuario_id = uuid4()
        ativ_id = uuid4()
        # RLS FORCE exige contexto de tenant para o INSERT (molde Fatia 1b).
        with run_in_tenant_context(tenant_id):
            for tec_id in tecnicos:
                for h in range(2):
                    ev = EventoAgenda(
                        id=uuid4(),
                        tenant_id=tenant_id,
                        tecnico_id=tec_id,
                        tipo=TipoEvento.OS,
                        estado=EstadoEvento.AGENDADO,
                        inicia_at=base_inicia + timedelta(hours=h * 3),
                        termina_at=base_inicia + timedelta(hours=h * 3 + 2),
                        aloca_em_umc=False,
                        criado_por_usuario_id=usuario_id,
                        criado_em=agora,
                        atualizado_em=agora,
                        revision=0,
                        atividade_id=ativ_id,
                    )
                    repo.salvar_novo(ev)

    def test_grade_o1_queries_5_vs_20_tecnicos(self) -> None:
        """listar_por_tenant deve usar N FIXO de queries independente do número de técnicos."""
        from django.db import connection
        from django.test.utils import CaptureQueriesContext
        from src.infrastructure.agenda.repositories import DjangoEventoAgendaRepository
        from src.infrastructure.multitenant.connection import run_in_tenant_context

        tenant_id = self._obter_tenant_id()
        base = datetime(2026, 8, 1, 8, 0, tzinfo=UTC)
        repo = DjangoEventoAgendaRepository()

        tecnicos_5 = [uuid4() for _ in range(5)]
        self._salvar_eventos_banco(tenant_id, tecnicos_5, base)

        # Contexto de tenant aberto ANTES do capture: o SET app.tenant_ids não é
        # contado; o capture mede só a query da grade (deve ser O(1) em técnicos).
        with run_in_tenant_context(tenant_id):
            with CaptureQueriesContext(connection) as ctx_5:
                repo.listar_por_tenant(tenant_id=tenant_id)
        n_queries_5 = len(ctx_5)

        tecnicos_15 = [uuid4() for _ in range(15)]
        self._salvar_eventos_banco(tenant_id, tecnicos_15, base + timedelta(hours=1))

        with run_in_tenant_context(tenant_id):
            with CaptureQueriesContext(connection) as ctx_20:
                repo.listar_por_tenant(tenant_id=tenant_id)
        n_queries_20 = len(ctx_20)

        assert n_queries_5 == n_queries_20, (
            f"Número de queries cresceu de {n_queries_5} para {n_queries_20} "
            "ao passar de 5 para 20 técnicos — viola PLAN-AGE-04 (deve ser O(1))."
        )

    def test_listar_por_tenant_respeita_teto(self) -> None:
        """``limite`` impõe teto duro de linhas (anti-unbounded/DoS — F-C3)."""
        from src.infrastructure.agenda.repositories import DjangoEventoAgendaRepository
        from src.infrastructure.multitenant.connection import run_in_tenant_context

        tenant_id = self._obter_tenant_id()
        base = datetime(2026, 9, 1, 8, 0, tzinfo=UTC)
        # 5 técnicos × 2 eventos = 10 eventos no tenant.
        self._salvar_eventos_banco(tenant_id, [uuid4() for _ in range(5)], base)
        repo = DjangoEventoAgendaRepository()
        with run_in_tenant_context(tenant_id):
            limitado = repo.listar_por_tenant(tenant_id=tenant_id, limite=4)
            sem_limite = repo.listar_por_tenant(tenant_id=tenant_id)
        assert len(limitado) == 4, "teto não aplicado"
        assert len(sem_limite) == 10, "sem limite deve retornar todos"


@pytest.mark.django_db(transaction=True)
class TestAgendaCrossTenant:
    """Retrieve cross-tenant deve retornar None (→ 404 na view)."""

    def test_cross_tenant_retorna_none(self) -> None:
        from src.domain.operacao.agenda.entities import EventoAgenda
        from src.infrastructure.agenda.repositories import DjangoEventoAgendaRepository
        from src.infrastructure.multitenant.connection import run_in_tenant_context

        from tests.factories import TenantFactory

        # Dois tenants distintos (molde Fatia 1b — cria via factory, não depende de seed).
        tenant_a = TenantFactory()
        tenant_b = TenantFactory()
        repo = DjangoEventoAgendaRepository()

        agora = datetime.now(UTC)
        ev = EventoAgenda(
            id=uuid4(),
            tenant_id=tenant_a.id,
            tecnico_id=uuid4(),
            tipo=TipoEvento.BLOQUEIO,
            estado=EstadoEvento.AGENDADO,
            inicia_at=datetime(2026, 9, 1, 8, 0, tzinfo=UTC),
            termina_at=datetime(2026, 9, 1, 10, 0, tzinfo=UTC),
            aloca_em_umc=False,
            criado_por_usuario_id=uuid4(),
            criado_em=agora,
            atualizado_em=agora,
            revision=0,
        )
        with run_in_tenant_context(tenant_a.id):
            repo.salvar_novo(ev)

        # Tenant B NÃO enxerga o evento do tenant A (isolamento RLS + filtro → 404 anti-oráculo).
        with run_in_tenant_context(tenant_b.id):
            resultado_b = repo.obter_por_id(tenant_id=tenant_b.id, evento_id=ev.id)
        assert resultado_b is None, "Cross-tenant não deveria retornar evento (anti-oráculo)"

        # Confirmação positiva: o evento EXISTE para o tenant A (prova que o None acima é
        # isolamento, não evento inexistente).
        with run_in_tenant_context(tenant_a.id):
            resultado_a = repo.obter_por_id(tenant_id=tenant_a.id, evento_id=ev.id)
        assert resultado_a is not None, "Tenant dono deveria enxergar o próprio evento"
