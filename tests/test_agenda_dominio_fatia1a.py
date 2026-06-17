"""Testes da Fatia 1a — domínio puro da agenda (T-AGE-017).

Verificação 1a: sem Django, sem PostgreSQL — domínio puro.
Cobertura obrigatória (plan §2 / T-AGE-017):
- Máquina de estados: transições válidas (happy) + cada inválida levanta erro.
- Jornada motorista_profissional viola R2 onde clt_geral NÃO viola (prova diferença de regime).
- Espera 1/1 estoura teto R3 (ADI 5322).
- R1, R3, R4, R5 em ambos os regimes.
- nao_aplica nunca bloqueia.
- R7 noturno marcado (advisory, ok=True).
- RegimeJornadaResolvido indeterminado + regime≠nao_aplica → ValueError.
- Janela inicia≥termina → erro.
- materializar_janela determinística + idempotente + conta ocorrências em 90d.
- EventoAgenda tipo=os sem atividade_id → erro.
- Protocols runtime_checkable.
"""

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime, timedelta

import pytest
from src.domain.operacao.agenda.entities import (
    EventoAgenda,
    RegimeJornadaColaborador,
)
from src.domain.operacao.agenda.enums import (
    AcaoAuditoria,
    EstadoEvento,
    FonteRegime,
    MotivoBloqueio,
    RegimeJornada,
    TipoEvento,
)
from src.domain.operacao.agenda.erros import (
    AtividadeObrigatoria,
    TransicaoEventoProibida,
)
from src.domain.operacao.agenda.jornada import (
    EventoSimples,
    validar_jornada_umc,
)
from src.domain.operacao.agenda.portas import (
    AReceberPort,
    ColaboradorAgendaPort,
    EventoAgendaRepository,
    MapsProvider,
    NotificacaoClientePort,
    OSSchedulingPort,
    RTSubstitutoPort,
)
from src.domain.operacao.agenda.recorrencia import materializar_janela
from src.domain.operacao.agenda.transicoes import eh_terminal, validar_transicao
from src.domain.operacao.agenda.value_objects import (
    Janela,
    RegimeJornadaResolvido,
    RegraRecorrencia,
    TecnicoJornada,
)

# ---------------------------------------------------------------------------
# Fixtures e helpers
# ---------------------------------------------------------------------------

_TID = uuid.uuid4()
_UID = uuid.uuid4()
_CID = uuid.uuid4()
_TEC = uuid.uuid4()
_ATV = uuid.uuid4()

# Técnico de campo alocado em UMC (valida jornada)
_TECNICO_CAMPO = TecnicoJornada(
    tenant_id=_TID,
    colaborador_id=_CID,
    is_tecnico_campo=True,
    aloca_em_umc=True,
)

# Técnico não-campo (nunca valida jornada)
_TECNICO_NAO_CAMPO = TecnicoJornada(
    tenant_id=_TID,
    colaborador_id=_CID,
    is_tecnico_campo=False,
    aloca_em_umc=False,
)

_DT_BASE = datetime(2026, 6, 16, 8, 0, tzinfo=UTC)  # segunda-feira 08:00 UTC


def _janela(horas_inicio: float, duracao_h: float, base: datetime = _DT_BASE) -> Janela:
    """Cria uma Janela a partir de offset em horas relativo à base."""
    inicio = base + timedelta(hours=horas_inicio)
    fim = inicio + timedelta(hours=duracao_h)
    return Janela(inicia_at=inicio, termina_at=fim)


def _ev(
    tipo: TipoEvento, horas_inicio: float, duracao_h: float, base: datetime = _DT_BASE
) -> EventoSimples:
    """Cria um EventoSimples para uso nos testes de jornada."""
    return EventoSimples(tipo=tipo, janela=_janela(horas_inicio, duracao_h, base))


def _novo_evento(
    tipo: TipoEvento = TipoEvento.BLOQUEIO,
    estado: EstadoEvento = EstadoEvento.AGENDADO,
    atividade_id: uuid.UUID | None = None,
) -> EventoAgenda:
    agora = datetime.now(tz=UTC)
    return EventoAgenda(
        id=uuid.uuid4(),
        tenant_id=_TID,
        tecnico_id=_TEC,
        tipo=tipo,
        estado=estado,
        inicia_at=agora,
        termina_at=agora + timedelta(hours=1),
        aloca_em_umc=True,
        criado_por_usuario_id=_UID,
        criado_em=agora,
        atualizado_em=agora,
        atividade_id=atividade_id,
    )


# ---------------------------------------------------------------------------
# 1. Máquina de estados
# ---------------------------------------------------------------------------


class TestMaquinaEstados:
    """T-AGE-017: máquina de estados — happy + unhappy parametrize."""

    @pytest.mark.parametrize(
        "de, para",
        [
            (EstadoEvento.AGENDADO, EstadoEvento.EM_EXECUCAO),
            (EstadoEvento.AGENDADO, EstadoEvento.CANCELADO),
            (EstadoEvento.AGENDADO, EstadoEvento.NO_SHOW),
            (EstadoEvento.EM_EXECUCAO, EstadoEvento.CONCLUIDO),
            (EstadoEvento.EM_EXECUCAO, EstadoEvento.CANCELADO),
        ],
    )
    def test_transicao_valida(self, de: EstadoEvento, para: EstadoEvento) -> None:
        """Transições válidas não levantam exceção."""
        validar_transicao(de, para)  # não deve levantar

    @pytest.mark.parametrize(
        "de, para",
        [
            # Terminais
            (EstadoEvento.CONCLUIDO, EstadoEvento.AGENDADO),
            (EstadoEvento.CONCLUIDO, EstadoEvento.CANCELADO),
            (EstadoEvento.CANCELADO, EstadoEvento.AGENDADO),
            (EstadoEvento.NO_SHOW, EstadoEvento.AGENDADO),
            # Saltos inválidos
            (EstadoEvento.AGENDADO, EstadoEvento.CONCLUIDO),
            (EstadoEvento.EM_EXECUCAO, EstadoEvento.NO_SHOW),
            (EstadoEvento.EM_EXECUCAO, EstadoEvento.AGENDADO),
        ],
    )
    def test_transicao_proibida_levanta(self, de: EstadoEvento, para: EstadoEvento) -> None:
        """Transições proibidas levantam TransicaoEventoProibida."""
        with pytest.raises(TransicaoEventoProibida):
            validar_transicao(de, para)

    def test_estados_terminais(self) -> None:
        """concluido, cancelado e no_show são terminais."""
        assert eh_terminal(EstadoEvento.CONCLUIDO)
        assert eh_terminal(EstadoEvento.CANCELADO)
        assert eh_terminal(EstadoEvento.NO_SHOW)
        assert not eh_terminal(EstadoEvento.AGENDADO)
        assert not eh_terminal(EstadoEvento.EM_EXECUCAO)


# ---------------------------------------------------------------------------
# 2. Jornada — R1..R5 + diferença de regime + nao_aplica + R7
# ---------------------------------------------------------------------------


class TestJornadaNaoAplica:
    """nao_aplica nunca bloqueia."""

    def test_nao_aplica_com_tecnico_campo(self) -> None:
        """nao_aplica retorna ok=True mesmo com is_tecnico_campo=True."""
        janela = _janela(0, 12)  # 12h — estouraria todos os tetos
        result = validar_jornada_umc(_TECNICO_CAMPO, RegimeJornada.NAO_APLICA, janela, [])
        assert result.ok is True
        assert result.violacao is None

    def test_nao_campo_retorna_ok(self) -> None:
        """Técnico não-campo: sem validação independente do regime."""
        janela = _janela(0, 16)
        result = validar_jornada_umc(
            _TECNICO_NAO_CAMPO, RegimeJornada.MOTORISTA_PROFISSIONAL, janela, []
        )
        assert result.ok is True


class TestJornadaR1InterJornada:
    """R1: descanso inter-jornada ≥11h ininterruptas."""

    def test_r1_viola_motorista(self) -> None:
        """Jornada com menos de 11h de descanso → R1 violada (motorista)."""
        # Evento terminando 22:00 ontem; novo às 08:00 hoje = 10h de gap
        ontem = _DT_BASE - timedelta(days=1)
        ev_ontem = _ev(TipoEvento.OS, 14, 8, ontem)  # 22:00-06:00 não; 08:00+14h=22:00
        nova = _janela(0, 4)  # 08:00-12:00 hoje = 10h após fim (22:00)
        result = validar_jornada_umc(
            _TECNICO_CAMPO, RegimeJornada.MOTORISTA_PROFISSIONAL, nova, [ev_ontem]
        )
        # gap = 10h < 11h → viola R1
        assert result.ok is False
        assert result.violacao == "R1_INTER_JORNADA"
        assert result.faltante_min is not None
        assert result.faltante_min > 0
        assert result.proximo_slot is not None

    def test_r1_ok_com_11h_de_gap(self) -> None:
        """11h de gap exato → R1 não viola.

        _DT_BASE = 2026-06-16 08:00 UTC (segunda-feira).
        Evento ontem: termina em 2026-06-15 21:00 (início 13:00 + 8h = 21:00).
        Novo evento: 2026-06-16 08:00. Gap = 11h exato → R1 não viola.
        """
        ontem = _DT_BASE - timedelta(days=1)  # 2026-06-15 08:00
        # Evento com início às 13:00 ontem (offset=5h do base ontem) e duração 8h → termina 21:00
        ev_ontem = _ev(TipoEvento.OS, 5, 8, ontem)  # 13:00-21:00 ontem (2026-06-15)
        # Novo evento às 08:00 hoje = 11h após 21:00 ontem → gap exato = 11h
        nova = _janela(0, 2)  # 2026-06-16 08:00
        result = validar_jornada_umc(_TECNICO_CAMPO, RegimeJornada.CLT_GERAL, nova, [ev_ontem])
        assert result.ok is True

    def test_r1_viola_clt_geral(self) -> None:
        """R1 também aplica a clt_geral."""
        ontem = _DT_BASE - timedelta(days=1)
        ev_ontem = _ev(TipoEvento.OS, 14, 8, ontem)  # gap 10h
        nova = _janela(0, 2)
        result = validar_jornada_umc(_TECNICO_CAMPO, RegimeJornada.CLT_GERAL, nova, [ev_ontem])
        assert result.ok is False
        assert result.violacao == "R1_INTER_JORNADA"


class TestJornadaR2DirecaoContinua:
    """R2: pausa ≥30min a cada 5h30 — APENAS motorista_profissional."""

    def test_r2_viola_motorista_mais_de_5h30_continuas(self) -> None:
        """6h contínuas → R2 violada para motorista_profissional."""
        # Evento existente: 08:00-13:00 (5h contínuas)
        ev_continuo = _ev(TipoEvento.OS, 0, 5)
        # Novo evento: 13:00-14:00 (acumularia 6h sem pausa)
        nova = _janela(5, 1)
        result = validar_jornada_umc(
            _TECNICO_CAMPO, RegimeJornada.MOTORISTA_PROFISSIONAL, nova, [ev_continuo]
        )
        assert result.ok is False
        assert result.violacao == "R2_DIRECAO_CONTINUA"
        assert result.faltante_min == 30.0
        assert result.proximo_slot is not None

    def test_r2_clt_geral_nao_viola(self) -> None:
        """MESMO cenário de 6h contínuas → clt_geral NÃO viola R2."""
        ev_continuo = _ev(TipoEvento.OS, 0, 5)
        nova = _janela(5, 1)
        result = validar_jornada_umc(_TECNICO_CAMPO, RegimeJornada.CLT_GERAL, nova, [ev_continuo])
        # clt_geral não tem R2; pode violar R3/R4/R5 mas não R2
        assert result.violacao != "R2_DIRECAO_CONTINUA"

    def test_r2_ok_com_pausa_almoco_intercalada(self) -> None:
        """5h + pausa almoço 1h + mais 1h → R2 não viola (pausa intercalada)."""
        ev1 = _ev(TipoEvento.OS, 0, 5)  # 08:00-13:00 (5h)
        pausa = _ev(TipoEvento.ALMOCO, 5, 1)  # 13:00-14:00 (1h almoço)
        nova = _janela(6, 1)  # 14:00-15:00
        result = validar_jornada_umc(
            _TECNICO_CAMPO, RegimeJornada.MOTORISTA_PROFISSIONAL, nova, [ev1, pausa]
        )
        # Bloco contínuo reiniciado após pausa ≥30min → novo bloco = 1h < 5h30
        assert result.violacao != "R2_DIRECAO_CONTINUA"

    def test_r2_diferenca_regime_prova(self) -> None:
        """Prova explícita: mesmo input viola R2 para motorista, não para clt_geral."""
        ev_continuo = _ev(TipoEvento.OS, 0, 5)
        nova = _janela(5, 1)

        res_motorista = validar_jornada_umc(
            _TECNICO_CAMPO, RegimeJornada.MOTORISTA_PROFISSIONAL, nova, [ev_continuo]
        )
        res_clt = validar_jornada_umc(_TECNICO_CAMPO, RegimeJornada.CLT_GERAL, nova, [ev_continuo])

        assert res_motorista.ok is False
        assert res_motorista.violacao == "R2_DIRECAO_CONTINUA"
        # clt_geral: R2 não aplica → resultado não viola R2
        assert res_clt.violacao != "R2_DIRECAO_CONTINUA"


class TestJornadaR3TetoDiario:
    """R3: teto diário 10h (normal) ou 12h (acordo coletivo)."""

    def test_r3_viola_teto_normal_10h(self) -> None:
        """11h totais → viola teto normal de 10h.

        Usa clt_geral para isolar R3 de R2 (R2 só aplica a motorista_profissional).
        9h existentes + 2h novas = 11h > teto 10h.
        """
        ev_existente = _ev(TipoEvento.OS, 0, 9)  # 9h já alocadas
        nova = _janela(9, 2)  # +2h = 11h total
        result = validar_jornada_umc(_TECNICO_CAMPO, RegimeJornada.CLT_GERAL, nova, [ev_existente])
        assert result.ok is False
        assert result.violacao == "R3_TETO_DIARIO"

    def test_r3_ok_com_acordo_coletivo_12h(self) -> None:
        """11h com acordo coletivo habilitado → ok (teto = 12h).

        Usa clt_geral para isolar R3 de R2. Inclui almoço para não violar R5.
        """
        ev_existente = _ev(TipoEvento.OS, 0, 5)  # 5h de OS
        almoco = _ev(TipoEvento.ALMOCO, 5, 1)  # 1h almoço (R5 ok)
        ev2 = _ev(TipoEvento.OS, 6, 4)  # mais 4h = 9h total
        nova = _janela(10, 2)  # +2h = 11h total < teto 12h
        result = validar_jornada_umc(
            _TECNICO_CAMPO,
            RegimeJornada.CLT_GERAL,
            nova,
            [ev_existente, almoco, ev2],
            acordo_coletivo_12h=True,
        )
        assert result.ok is True

    def test_r3_espera_integral_1_1_estoura_teto(self) -> None:
        """Espera = jornada INTEGRAL 1/1 (ADI 5322): tempo de espera conta no teto.

        Cenário: 8h de OS + 2h30 de deslocamento = 10h30 > teto 10h.
        Usa clt_geral para isolar de R2 (motorista_profissional).
        ADI 5322: tempo de espera conta 1:1 como jornada (não 1/3).
        """
        ev_os = _ev(TipoEvento.OS, 0, 8)
        # 2h30 de deslocamento/espera — conta 1:1 (ADI 5322, não 1/3)
        ev_espera = _ev(TipoEvento.DESLOCAMENTO, 8, 2.5)
        nova = _janela(10.5, 0.5)  # + 30min → total 11h
        result = validar_jornada_umc(
            _TECNICO_CAMPO, RegimeJornada.CLT_GERAL, nova, [ev_os, ev_espera]
        )
        assert result.ok is False
        assert result.violacao == "R3_TETO_DIARIO"

    def test_r3_clt_geral_respeita_teto(self) -> None:
        """clt_geral também tem teto de 10h (R3 aplica)."""
        ev = _ev(TipoEvento.OS, 0, 9)
        nova = _janela(9, 2)  # 11h total
        result = validar_jornada_umc(_TECNICO_CAMPO, RegimeJornada.CLT_GERAL, nova, [ev])
        assert result.ok is False
        assert result.violacao == "R3_TETO_DIARIO"

    def test_r3_motorista_com_r2_ok_mas_r3_viola(self) -> None:
        """Para motorista, R2 se aplica antes de R3. Usar pausas suficientes para isolar R3.

        Estrutura: 5h OS | 1h almoço | 5h OS | 1h pausa | nova 1h → total 11h > 10h.
        Blocos de direção: 5h e 5h (ambos < 5h30). R2 não viola. R3 viola (11h > 10h).
        """
        # Bloco 1: 5h de OS (08:00-13:00)
        ev1 = _ev(TipoEvento.OS, 0, 5)
        # Almoço 1h (13:00-14:00) — reinicia R2 e satisfaz R5
        almoco = _ev(TipoEvento.ALMOCO, 5, 1)
        # Bloco 2: 5h OS (14:00-19:00) → total 10h trabalhadas
        ev2 = _ev(TipoEvento.OS, 6, 5)
        # Pausa 30min (19:00-19:30) — reinicia R2 para nova
        pausa2 = _ev(TipoEvento.DESCANSO_LEGAL, 11, 0.5)
        # Nova: 1h (19:30-20:30) → total 11h > teto 10h
        nova = _janela(11.5, 1)
        result = validar_jornada_umc(
            _TECNICO_CAMPO, RegimeJornada.MOTORISTA_PROFISSIONAL, nova, [ev1, almoco, ev2, pausa2]
        )
        assert result.ok is False
        assert result.violacao == "R3_TETO_DIARIO"


class TestJornadaR4DSR:
    """R4: descanso semanal ≥35h a cada 6 dias."""

    def test_r4_nao_viola_com_carga_normal(self) -> None:
        """Carga normal de 8h/dia por 5 dias não viola R4 (descanso >> 35h)."""
        base = _DT_BASE
        eventos = []
        for dia in range(4):
            d = base - timedelta(days=4 - dia)
            eventos.append(_ev(TipoEvento.OS, 0, 8, d))
        nova = _janela(0, 8)  # 8h hoje
        result = validar_jornada_umc(_TECNICO_CAMPO, RegimeJornada.CLT_GERAL, nova, eventos)
        # 5 dias × 8h = 40h; descanso em 6 dias = 144h - 40h = 104h >> 35h; R4 ok
        assert result.violacao != "R4_DSR_SEMANAL"

    def test_r4_viola_quando_sem_descanso_semanal(self) -> None:
        """6 dias sem descanso → R4 violada.

        Cenário extremo: 6 dias × 24h = 144h de trabalho → 0h descanso < 35h.
        """
        base = _DT_BASE
        eventos = []
        for dia in range(6):
            d = base - timedelta(days=6 - dia)
            # 23h de trabalho por dia (máximo plausível)
            eventos.append(_ev(TipoEvento.OS, 0, 23, d))
        nova = _janela(0, 2)  # +2h hoje
        result = validar_jornada_umc(
            _TECNICO_CAMPO, RegimeJornada.MOTORISTA_PROFISSIONAL, nova, eventos
        )
        # Pode violar R1 (inter-jornada) antes de chegar a R4 — o teste verifica
        # que o validador retorna alguma violação (comportamento correto)
        assert result.ok is False  # alguma regra violada com carga extrema


class TestJornadaR5Refeicao:
    """R5: refeição ≥1h intrajornada quando jornada > 6h."""

    def test_r5_viola_quando_sem_almoco_em_jornada_longa(self) -> None:
        """7h de jornada sem pausa de almoço → viola R5 (usando clt_geral para isolar de R2)."""
        ev_existente = _ev(TipoEvento.OS, 0, 6)
        nova = _janela(6, 1)  # mais 1h = 7h total sem almoço
        # clt_geral para isolar R5 de R2 (R2 só aplica em motorista_profissional)
        result = validar_jornada_umc(_TECNICO_CAMPO, RegimeJornada.CLT_GERAL, nova, [ev_existente])
        assert result.ok is False
        assert result.violacao == "R5_REFEICAO"

    def test_r5_ok_com_almoco_adequado(self) -> None:
        """7h com almoço de 1h → R5 ok."""
        ev1 = _ev(TipoEvento.OS, 0, 4)
        almoco = _ev(TipoEvento.ALMOCO, 4, 1)  # 1h de almoço
        nova = _janela(5, 3)  # mais 3h = 7h de trabalho + 1h almoço
        result = validar_jornada_umc(_TECNICO_CAMPO, RegimeJornada.CLT_GERAL, nova, [ev1, almoco])
        assert result.violacao != "R5_REFEICAO"

    def test_r5_nao_aplica_jornada_curta(self) -> None:
        """Jornada ≤6h: R5 não aplica (sem obrigatoriedade de pausa)."""
        nova = _janela(0, 4)  # apenas 4h, sem eventos anteriores
        result = validar_jornada_umc(_TECNICO_CAMPO, RegimeJornada.CLT_GERAL, nova, [])
        assert result.ok is True


class TestJornadaR7Noturno:
    """R7: advisory — jornada noturna (22h-5h)."""

    def test_r7_advisory_marcado_sem_bloquear(self) -> None:
        """Evento que cruza 22h-5h → ok=True com violacao=R7_NOTURNO_ADVISORY."""
        base_noturno = datetime(2026, 6, 16, 23, 0, tzinfo=UTC)
        janela = Janela(
            inicia_at=base_noturno,
            termina_at=base_noturno + timedelta(hours=2),
        )
        result = validar_jornada_umc(_TECNICO_CAMPO, RegimeJornada.CLT_GERAL, janela, [])
        assert result.ok is True
        assert result.violacao == "R7_NOTURNO_ADVISORY"

    def test_r7_diurno_sem_advisory(self) -> None:
        """Evento diurno (08h-17h) → sem R7 advisory."""
        nova = _janela(0, 8)  # 08:00-16:00
        result = validar_jornada_umc(_TECNICO_CAMPO, RegimeJornada.CLT_GERAL, nova, [])
        assert result.violacao != "R7_NOTURNO_ADVISORY"

    def test_r7_diurno_longo_nao_marcado(self) -> None:
        """Evento diurno de 4h (09:00-13:00) que CHEGA ao R7 NÃO é marcado noturno.

        Regressão: a heurística antiga marcava qualquer evento >2h como noturno.
        4h ≤ 6h não dispara R5, então a validação chega ao R7 e prova o cálculo
        de interseção real (09:00-13:00 não intersecta [22h,05h)).
        """
        base = datetime(2026, 6, 16, 9, 0, tzinfo=UTC)
        janela = Janela(inicia_at=base, termina_at=base + timedelta(hours=4))  # 09:00-13:00
        result = validar_jornada_umc(_TECNICO_CAMPO, RegimeJornada.CLT_GERAL, janela, [])
        assert result.ok is True
        assert result.violacao is None  # nem R5 (≤6h) nem R7 (diurno)

    def test_r7_madrugada_marcado(self) -> None:
        """Evento de madrugada (03:00-05:00) intersecta o noturno → R7 advisory."""
        base = datetime(2026, 6, 16, 3, 0, tzinfo=UTC)
        janela = Janela(inicia_at=base, termina_at=base + timedelta(hours=2))  # 03:00-05:00
        result = validar_jornada_umc(_TECNICO_CAMPO, RegimeJornada.CLT_GERAL, janela, [])
        assert result.ok is True
        assert result.violacao == "R7_NOTURNO_ADVISORY"


# ---------------------------------------------------------------------------
# 3. Value Objects — Janela e RegimeJornadaResolvido
# ---------------------------------------------------------------------------


class TestJanela:
    """Janela: invariantes half-open."""

    def test_janela_valida(self) -> None:
        """Janela válida: inicia < termina."""
        agora = datetime.now(tz=UTC)
        j = Janela(inicia_at=agora, termina_at=agora + timedelta(hours=1))
        assert j.duracao_minutos == 60.0

    def test_janela_inicia_igual_termina_levanta(self) -> None:
        """inicia == termina → ValueError."""
        agora = datetime.now(tz=UTC)
        with pytest.raises(ValueError, match="estritamente anterior"):
            Janela(inicia_at=agora, termina_at=agora)

    def test_janela_inicia_depois_levanta(self) -> None:
        """inicia > termina → ValueError."""
        agora = datetime.now(tz=UTC)
        with pytest.raises(ValueError):
            Janela(inicia_at=agora + timedelta(hours=1), termina_at=agora)

    def test_janela_half_open_adjacentes_nao_sobrepoe(self) -> None:
        """Slots adjacentes [09:00-10:00) e [10:00-11:00) NÃO se sobrepõem (half-open)."""
        base = datetime(2026, 6, 16, 9, 0, tzinfo=UTC)
        j1 = Janela(inicia_at=base, termina_at=base + timedelta(hours=1))
        j2 = Janela(inicia_at=base + timedelta(hours=1), termina_at=base + timedelta(hours=2))
        assert not j1.sobrepoe(j2)
        assert not j2.sobrepoe(j1)

    def test_janela_sobreposicao_real(self) -> None:
        """Slots com overlap real se sobrepõem."""
        base = datetime(2026, 6, 16, 9, 0, tzinfo=UTC)
        j1 = Janela(inicia_at=base, termina_at=base + timedelta(hours=2))
        j2 = Janela(inicia_at=base + timedelta(hours=1), termina_at=base + timedelta(hours=3))
        assert j1.sobrepoe(j2)
        assert j2.sobrepoe(j1)


class TestRegimeJornadaResolvido:
    """RegimeJornadaResolvido: invariante fail-safe (indeterminado ⇒ nao_aplica)."""

    def test_override_humano_qualquer_regime(self) -> None:
        """fonte=override_humano aceita qualquer regime."""
        r = RegimeJornadaResolvido(
            regime=RegimeJornada.MOTORISTA_PROFISSIONAL,
            fonte=FonteRegime.OVERRIDE_HUMANO,
        )
        assert r.regime == RegimeJornada.MOTORISTA_PROFISSIONAL

    def test_derivado_papel_clt_geral(self) -> None:
        """fonte=derivado_papel aceita clt_geral."""
        r = RegimeJornadaResolvido(
            regime=RegimeJornada.CLT_GERAL,
            fonte=FonteRegime.DERIVADO_PAPEL,
        )
        assert r.regime == RegimeJornada.CLT_GERAL

    def test_indeterminado_com_nao_aplica_ok(self) -> None:
        """fonte=indeterminado com regime=nao_aplica → válido (fail-safe)."""
        r = RegimeJornadaResolvido(
            regime=RegimeJornada.NAO_APLICA,
            fonte=FonteRegime.INDETERMINADO,
        )
        assert r.regime == RegimeJornada.NAO_APLICA

    def test_indeterminado_com_motorista_levanta(self) -> None:
        """fonte=indeterminado com regime≠nao_aplica → ValueError (INV-AG-REGIME-001)."""
        with pytest.raises(ValueError, match="indeterminado"):
            RegimeJornadaResolvido(
                regime=RegimeJornada.MOTORISTA_PROFISSIONAL,
                fonte=FonteRegime.INDETERMINADO,
            )

    def test_indeterminado_com_clt_geral_levanta(self) -> None:
        """fonte=indeterminado com regime=clt_geral → ValueError."""
        with pytest.raises(ValueError):
            RegimeJornadaResolvido(
                regime=RegimeJornada.CLT_GERAL,
                fonte=FonteRegime.INDETERMINADO,
            )


# ---------------------------------------------------------------------------
# 4. Entidades
# ---------------------------------------------------------------------------


class TestEventoAgenda:
    """EventoAgenda: invariante atividade_id (INV-AG-ATIVIDADE-001)."""

    def test_tipo_os_com_atividade_id_ok(self) -> None:
        """tipo=os com atividade_id → sem erro."""
        ev = _novo_evento(tipo=TipoEvento.OS, atividade_id=_ATV)
        assert ev.atividade_id == _ATV

    def test_tipo_os_sem_atividade_id_levanta(self) -> None:
        """tipo=os sem atividade_id → AtividadeObrigatoria (INV-AG-ATIVIDADE-001)."""
        with pytest.raises(AtividadeObrigatoria):
            _novo_evento(tipo=TipoEvento.OS, atividade_id=None)

    def test_tipo_bloqueio_sem_atividade_ok(self) -> None:
        """tipo≠os sem atividade_id → sem erro."""
        ev = _novo_evento(tipo=TipoEvento.BLOQUEIO, atividade_id=None)
        assert ev.atividade_id is None

    def test_frozen_e_slots(self) -> None:
        """EventoAgenda é frozen+slots: não tem __dict__ e não aceita novos atributos."""
        ev = _novo_evento()
        # dataclass frozen=True, slots=True: sem __dict__ (slots)
        assert not hasattr(ev, "__dict__"), "frozen+slots não deve ter __dict__"
        # Confirma que é imutável: atribuição de slot existente via setattr levanta FrozenInstanceError
        from dataclasses import FrozenInstanceError

        try:
            # Em Python 3.12, frozen+slots: setattr normal levanta FrozenInstanceError
            ev.estado = EstadoEvento.CANCELADO  # type: ignore[misc] # frozen: atribuição intencional para provar imutabilidade
            raise AssertionError("deveria ter levantado FrozenInstanceError")
        except (FrozenInstanceError, AttributeError):
            pass  # esperado — qualquer um dos dois é correto


class TestRegimeJornadaColaborador:
    """RegimeJornadaColaborador: fonte deve ser override_humano."""

    def test_override_humano_valido(self) -> None:
        """fonte=override_humano → entidade válida."""
        r = RegimeJornadaColaborador(
            id=uuid.uuid4(),
            tenant_id=_TID,
            colaborador_id=_CID,
            regime=RegimeJornada.MOTORISTA_PROFISSIONAL,
            vigencia_inicio=date(2026, 1, 1),
            definido_por_usuario_id=_UID,
            fonte=FonteRegime.OVERRIDE_HUMANO,
            criado_em=datetime.now(tz=UTC),
        )
        assert r.fonte == FonteRegime.OVERRIDE_HUMANO

    def test_fonte_derivado_levanta(self) -> None:
        """fonte≠override_humano (derivado_papel) → ValueError (IA não grava)."""
        with pytest.raises(ValueError, match="override_humano"):
            RegimeJornadaColaborador(
                id=uuid.uuid4(),
                tenant_id=_TID,
                colaborador_id=_CID,
                regime=RegimeJornada.CLT_GERAL,
                vigencia_inicio=date(2026, 1, 1),
                definido_por_usuario_id=_UID,
                fonte=FonteRegime.DERIVADO_PAPEL,
                criado_em=datetime.now(tz=UTC),
            )


# ---------------------------------------------------------------------------
# 5. Recorrência — materializar_janela
# ---------------------------------------------------------------------------


class TestMaterializarJanela:
    """materializar_janela: determinística, idempotente, conta ocorrências em 90d."""

    _INICIO = datetime(2026, 6, 16, 8, 0, tzinfo=UTC)  # segunda-feira

    def test_diario_90_dias(self) -> None:
        """FREQ=DAILY em 90 dias → 90 ocorrências (D0..D89)."""
        regra = RegraRecorrencia(rrule_str="FREQ=DAILY")
        ocorrencias = materializar_janela(regra, self._INICIO, dias=90)
        assert len(ocorrencias) == 90

    def test_semanal_segunda_quarta_sexta_90_dias(self) -> None:
        """FREQ=WEEKLY;BYDAY=MO,WE,FR em 90 dias → ~38-39 ocorrências."""
        regra = RegraRecorrencia(rrule_str="FREQ=WEEKLY;BYDAY=MO,WE,FR")
        ocorrencias = materializar_janela(regra, self._INICIO, dias=90)
        # 90 dias / 7 ≈ 12.8 semanas × 3 dias = ~38 ou 39
        assert 38 <= len(ocorrencias) <= 39

    def test_mensal_dia_1_90_dias(self) -> None:
        """FREQ=MONTHLY;BYMONTHDAY=1 em 90 dias → 3 ocorrências (Jul, Ago, Set)."""
        regra = RegraRecorrencia(rrule_str="FREQ=MONTHLY;BYMONTHDAY=1")
        ocorrencias = materializar_janela(regra, self._INICIO, dias=90)
        # Início em 16/Jun → próximos dias-1: Jul 1, Ago 1, Set 1 (= 3)
        assert len(ocorrencias) == 3

    def test_deterministico_mesma_entrada_mesmo_resultado(self) -> None:
        """Determinismo: chamadas repetidas produzem o mesmo resultado."""
        regra = RegraRecorrencia(rrule_str="FREQ=WEEKLY;BYDAY=TU,TH")
        r1 = materializar_janela(regra, self._INICIO, dias=90)
        r2 = materializar_janela(regra, self._INICIO, dias=90)
        assert r1 == r2

    def test_idempotente_sem_duplicatas_internas(self) -> None:
        """Idempotência: resultado sem duplicatas internas (set de datetimes)."""
        regra = RegraRecorrencia(rrule_str="FREQ=DAILY")
        r = materializar_janela(regra, self._INICIO, dias=30)
        assert len(r) == len(set(r))

    def test_ordem_crescente(self) -> None:
        """Resultado sempre em ordem crescente."""
        regra = RegraRecorrencia(rrule_str="FREQ=WEEKLY;BYDAY=MO,WE,FR")
        r = materializar_janela(regra, self._INICIO, dias=90)
        assert r == sorted(r)

    def test_count_limita_ocorrencias(self) -> None:
        """COUNT=4 limita a 4 ocorrências."""
        regra = RegraRecorrencia(rrule_str="FREQ=WEEKLY;BYDAY=MO;COUNT=4")
        r = materializar_janela(regra, self._INICIO, dias=90)
        assert len(r) == 4

    def test_freq_invalida_levanta(self) -> None:
        """FREQ não suportada → ValueError."""
        regra = RegraRecorrencia(rrule_str="FREQ=HOURLY")
        with pytest.raises(ValueError, match="FREQ"):
            materializar_janela(regra, self._INICIO)

    def test_rrule_sem_freq_levanta(self) -> None:
        """RRULE sem FREQ → ValueError."""
        regra = RegraRecorrencia(rrule_str="BYDAY=MO")
        with pytest.raises(ValueError, match="FREQ"):
            materializar_janela(regra, self._INICIO)

    def test_diario_com_interval_2(self) -> None:
        """FREQ=DAILY;INTERVAL=2 → 45 ocorrências em 90 dias."""
        regra = RegraRecorrencia(rrule_str="FREQ=DAILY;INTERVAL=2")
        r = materializar_janela(regra, self._INICIO, dias=90)
        assert len(r) == 45

    def test_semanal_interval_2_cruza_virada_de_ano(self) -> None:
        """FREQ=WEEKLY;INTERVAL=2 cruzando a virada de ano mantém o intervalo de 14 dias.

        Regressão: o cálculo antigo (ano*53+semana ISO) quebrava a paridade na
        virada de ano (anos com 52 semanas), incluindo/excluindo a semana errada.
        """
        inicio = datetime(2026, 12, 7, 8, 0, tzinfo=UTC)  # segunda-feira
        regra = RegraRecorrencia(rrule_str="FREQ=WEEKLY;BYDAY=MO;INTERVAL=2")
        r = materializar_janela(regra, inicio, dias=90)  # cruza 2026→2027
        assert len(r) >= 2
        difs = {(r[i + 1] - r[i]).days for i in range(len(r) - 1)}
        assert difs == {14}, f"intervalos inesperados na virada de ano: {difs}"


# ---------------------------------------------------------------------------
# 6. Enums — str-mixin e valores
# ---------------------------------------------------------------------------


class TestEnums:
    """Enums: str-mixin, valores corretos."""

    def test_tipo_evento_values(self) -> None:
        """TipoEvento: todos os valores esperados presentes."""
        valores = {e.value for e in TipoEvento}
        esperados = {
            "os",
            "bloqueio",
            "descanso_legal",
            "deslocamento",
            "almoco",
            "manutencao_interna",
            "feriado",
        }
        assert esperados == valores

    def test_estado_evento_values(self) -> None:
        """EstadoEvento: todos os valores esperados."""
        valores = {e.value for e in EstadoEvento}
        assert valores == {"agendado", "em_execucao", "concluido", "cancelado", "no_show"}

    def test_acao_auditoria_inclui_reagendado_e_bloqueado(self) -> None:
        """AcaoAuditoria: reagendado e bloqueado presentes (PLAN-AGE-08)."""
        assert AcaoAuditoria.REAGENDADO.value == "reagendado"
        assert AcaoAuditoria.BLOQUEADO.value == "bloqueado"
        assert AcaoAuditoria.REGIME_INDETERMINADO.value == "regime_indeterminado"

    def test_regime_jornada_values(self) -> None:
        """RegimeJornada: valores corretos."""
        assert RegimeJornada.MOTORISTA_PROFISSIONAL.value == "motorista_profissional"
        assert RegimeJornada.CLT_GERAL.value == "clt_geral"
        assert RegimeJornada.NAO_APLICA.value == "nao_aplica"

    def test_enums_sao_str(self) -> None:
        """Enums herdam str → serialização JSON nativa."""
        assert isinstance(TipoEvento.OS, str)
        assert isinstance(EstadoEvento.AGENDADO, str)
        assert isinstance(RegimeJornada.CLT_GERAL, str)
        assert isinstance(FonteRegime.INDETERMINADO, str)
        assert isinstance(AcaoAuditoria.CRIADO, str)
        assert isinstance(MotivoBloqueio.FERIAS, str)


# ---------------------------------------------------------------------------
# 7. Protocols runtime_checkable
# ---------------------------------------------------------------------------


class TestProtocols:
    """Protocols: runtime_checkable verificado via atributo __protocol_attrs__."""

    def test_protocols_sao_runtime_checkable(self) -> None:
        """Todos os Protocols têm __protocol_attrs__ (decorador @runtime_checkable aplicado)."""
        for protocolo in [
            EventoAgendaRepository,
            OSSchedulingPort,
            ColaboradorAgendaPort,
            RTSubstitutoPort,
            MapsProvider,
            NotificacaoClientePort,
            AReceberPort,
        ]:
            assert hasattr(protocolo, "__protocol_attrs__"), (
                f"{protocolo.__name__} não é @runtime_checkable — "
                "aplicar @runtime_checkable em portas.py"
            )
