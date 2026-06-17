"""Validação de jornada UMC — predicate puro e perfil-AGNÓSTICO (Fatia 1a — T-AGE-014).

D-AGE-4 / INV-AG-JORNADA-UMC-001 / ADV-AGE-01.

Este módulo NÃO recebe nem consulta o perfil regulatório A/B/C/D do tenant.
A jornada UMC é ordem pública trabalhista (CLT 235-C + arts. 58/66/71), não
parâmetro de configuração de perfil metrológico (RBC-AGE-01 / ADV-AGE-04).

Discriminação por ``regime: RegimeJornada``:
- ``nao_aplica``            → ``ResultadoJornada(ok=True)`` sem validar.
- ``motorista_profissional`` (CLT 235-C): R1-R5 + espera 1/1 (ADI 5322 ex nunc 12/07/2023).
- ``clt_geral`` (arts. 58/66/71):         R1/R3/R4/R5 — SEM R2.

Regras implementadas:
- R1  descanso inter-jornada ≥11h ininterruptas (CLT 235-C §3º + art. 66).
- R2  pausa ≥30min a cada 5h30 de direção contínua (CLT 235-C §5º + CTB 67-C)
      — APENAS ``motorista_profissional``.
- R3  teto diário: 8h + até 2h extras = 10h; até 4h extras com acordo coletivo = 12h.
      Flag ``acordo_coletivo_12h`` habilita o teto estendido (CLT 235-C caput / art. 58).
- R4  descanso semanal ≥35h a cada 6 dias (§3º + ADI 5322).
- R5  refeição ≥1h intrajornada (CLT art. 71 §5º).
- R7  advisory: janela cruzando 22h-5h → marca jornada noturna (não bloqueia).
      Retorna ``ResultadoJornada(ok=True)`` com ``violacao='R7_NOTURNO_ADVISORY'``.

R6 (non-goal): agenda é planejamento, não substitui controle de ponto.
Tempo de espera = jornada INTEGRAL 1/1 (ADI 5322 derrubou §8º/§9º).

Modelagem de "direção contínua" (R2):
    A pausa de direção contínua aplica-se ao bloco de condução consecutiva.
    Neste domínio puro, "direção contínua" é aproximada como a janela do evento
    em si (sem pausa registrada). O validador recebe a janela do novo evento e
    a lista de eventos já alocados no dia para o técnico. Calcula o bloco
    contínuo acumulado imediatamente antes do novo evento (eventos adjacentes
    ou sobrepostos). Se o bloco + janela nova excede 5h30 sem pausa ≥30min
    intercalada (``ALMOCO`` ou ``DESCANSO_LEGAL``), R2 é violada.

Funções PURAS — sem I/O, sem Django.
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime, time, timedelta

from .enums import RegimeJornada, TipoEvento
from .value_objects import Janela, ResultadoJornada, TecnicoJornada

# ---------------------------------------------------------------------------
# Constantes (Lei 13.103 + CLT)
# ---------------------------------------------------------------------------

# R1 — inter-jornada mínima ininterrupta (CLT 235-C §3º / art. 66)
_INTER_JORNADA_MIN_HORAS: float = 11.0

# R2 — direção contínua máxima sem pausa (CLT 235-C §5º + CTB 67-C)
_DIRECAO_CONTINUA_MAX_MIN: float = 5.5 * 60  # 5h30 em minutos
_PAUSA_DIRECAO_MIN: float = 30.0  # pausa mínima de direção

# R3 — teto diário
_TETO_DIARIO_NORMAL_MIN: float = 10.0 * 60  # 8h + 2h extras = 10h
_TETO_DIARIO_ACORDO_MIN: float = 12.0 * 60  # 12h com acordo coletivo

# R4 — descanso semanal (ADI 5322)
_DSR_MIN_HORAS: float = 35.0  # 35h a cada 6 dias
_DSR_JANELA_DIAS: int = 6

# R5 — refeição mínima (CLT art. 71 §5º)
_REFEICAO_MIN_MIN: float = 60.0  # 1h

# R7 — jornada noturna advisory (22h-5h)
_HORA_NOTURNA_INICIO: int = 22
_HORA_NOTURNA_FIM: int = 5


# ---------------------------------------------------------------------------
# Evento simplificado para validação (sem importar entities — evita circular)
# ---------------------------------------------------------------------------


class EventoSimples:
    """Representação mínima de um evento alocado para validação de jornada.

    Evita importar ``EventoAgenda`` (evita importação circular entre
    ``entities`` e ``jornada``). O use case e os testes instanciam direto.

    ``tipo``      — tipo do evento (usado para identificar pausas em R2).
    ``janela``    — janela temporal do evento.
    """

    __slots__ = ("tipo", "janela")

    def __init__(self, tipo: TipoEvento, janela: Janela) -> None:
        self.tipo = tipo
        self.janela = janela


# ---------------------------------------------------------------------------
# Helpers internos
# ---------------------------------------------------------------------------


def _minutos_no_dia(janela: Janela) -> float:
    """Duração da janela em minutos (sem considerar múltiplos dias)."""
    return janela.duracao_minutos


def _cruza_noturno(janela: Janela) -> bool:
    """Verifica se a janela INTERSECTA o período noturno 22h-5h (R7 advisory).

    Período noturno diário = ``[22:00, 05:00)`` do dia seguinte. O evento cruza
    o noturno se ``[inicia_at, termina_at)`` intersecta alguma janela noturna.

    Robusto: NÃO marca eventos diurnos longos (ex.: 09:00-13:00) como noturnos
    — o cálculo é interseção real de intervalos, não heurística de duração; e
    cobre eventos que atravessam a meia-noite ou múltiplos dias (<48h típico).
    """
    inicio = janela.inicia_at
    fim = janela.termina_at
    tz = inicio.tzinfo

    # Evento de 24h+ cobre qualquer período noturno.
    if (fim - inicio) >= timedelta(hours=24):
        return True

    # Itera as janelas noturnas dos dias tocados. Inclui o dia ANTERIOR ao
    # início, cujo bloco 00h-05h pode alcançar a madrugada do dia do evento.
    dia = inicio.date() - timedelta(days=1)
    ultimo = fim.date()
    while dia <= ultimo:
        noturno_inicio = datetime.combine(dia, time(_HORA_NOTURNA_INICIO, 0), tzinfo=tz)
        noturno_fim = datetime.combine(
            dia + timedelta(days=1), time(_HORA_NOTURNA_FIM, 0), tzinfo=tz
        )
        # interseção half-open: [inicio, fim) ∩ [noturno_inicio, noturno_fim) ≠ ∅
        if inicio < noturno_fim and fim > noturno_inicio:
            return True
        dia += timedelta(days=1)
    return False


def _eventos_do_dia(eventos: Sequence[EventoSimples], data: datetime) -> list[EventoSimples]:
    """Filtra eventos que ocorrem no mesmo dia calendário de ``data``."""
    dia = data.date()
    resultado = []
    for ev in eventos:
        # Evento pertence ao dia se inicia ou termina nesse dia
        if ev.janela.inicia_at.date() == dia or ev.janela.termina_at.date() == dia:
            resultado.append(ev)
    return resultado


def _total_alocado_no_dia_min(
    eventos: Sequence[EventoSimples],
    nova_janela: Janela,
    data: datetime,
) -> float:
    """Soma total de minutos alocados no dia (incluindo o novo evento).

    Eventos do tipo ``DESCANSO_LEGAL``, ``ALMOCO`` e ``FERIADO`` não contam
    como jornada trabalhada (são pausas).
    """
    tipos_pausa = {TipoEvento.DESCANSO_LEGAL, TipoEvento.ALMOCO, TipoEvento.FERIADO}
    total = nova_janela.duracao_minutos
    for ev in _eventos_do_dia(eventos, data):
        if ev.tipo not in tipos_pausa:
            total += ev.janela.duracao_minutos
    return total


def _bloco_continuo_antes_de(
    eventos: Sequence[EventoSimples],
    nova_janela: Janela,
) -> float:
    """Calcula o bloco de direção contínua acumulado IMEDIATAMENTE antes do novo evento.

    Retorna a duração do bloco contínuo (em minutos) de eventos de trabalho
    que terminam adjacentes ou sobrepostos ao início do novo evento, sem uma
    pausa ≥30min de ``ALMOCO`` ou ``DESCANSO_LEGAL`` intercalada.

    Lógica:
    1. Ordena os eventos existentes por ``termina_at`` decrescente.
    2. Percorre para trás a partir de ``nova_janela.inicia_at``.
    3. Acumula blocos contíguos (gap ≤ 0 entre fim do anterior e início do próximo).
    4. Para quando encontra um gap > 0 OU uma pausa qualificada (≥30min de ALMOCO/DESCANSO).
    """
    tipos_pausa = {TipoEvento.DESCANSO_LEGAL, TipoEvento.ALMOCO}
    limite = nova_janela.inicia_at
    # Filtra eventos anteriores ao novo, ordena por término decrescente
    anteriores = sorted(
        [ev for ev in eventos if ev.janela.termina_at <= limite],
        key=lambda e: e.janela.termina_at,
        reverse=True,
    )
    bloco_min: float = 0.0
    cursor = limite
    for ev in anteriores:
        gap_seg = (cursor - ev.janela.termina_at).total_seconds()
        # Evento de pausa qualificada (ALMOCO/DESCANSO_LEGAL) com duração ≥30min:
        # encerra o bloco independentemente de gap
        if ev.tipo in tipos_pausa and ev.janela.duracao_minutos >= _PAUSA_DIRECAO_MIN:
            break
        if gap_seg > 0:
            # Lacuna entre eventos ≥30min: encerra o bloco (pausa informal suficiente)
            if gap_seg >= _PAUSA_DIRECAO_MIN * 60:
                break
            # Lacuna pequena (<30min): não encerra o bloco contínuo
        if ev.tipo not in tipos_pausa:
            bloco_min += ev.janela.duracao_minutos
        cursor = ev.janela.inicia_at
    return bloco_min


def _ultima_jornada_fim(
    eventos: Sequence[EventoSimples],
    nova_janela: Janela,
) -> datetime | None:
    """Retorna o fim do último evento trabalhado em um DIA DIFERENTE do novo evento.

    R1 (inter-jornada) mede o descanso entre **jornadas** (dias de trabalho
    distintos). Eventos do mesmo dia calendário pertencem ao mesmo turno e
    não disparam R1 entre si — apenas teto (R3) e R2 (direção contínua).

    Retorna ``None`` se não há evento trabalhado em dia anterior ao novo evento.
    """
    tipos_pausa = {TipoEvento.DESCANSO_LEGAL, TipoEvento.ALMOCO, TipoEvento.FERIADO}
    dia_novo = nova_janela.inicia_at.date()
    trabalhados_dia_anterior = [
        ev for ev in eventos if ev.tipo not in tipos_pausa and ev.janela.inicia_at.date() < dia_novo
    ]
    if not trabalhados_dia_anterior:
        return None
    return max(ev.janela.termina_at for ev in trabalhados_dia_anterior)


def _proximo_slot_apos(base: datetime, delta_min: float) -> datetime:
    """Calcula o próximo slot válido após ``base`` + ``delta_min`` minutos."""
    return base + timedelta(minutes=delta_min)


# ---------------------------------------------------------------------------
# Função pública principal
# ---------------------------------------------------------------------------


def validar_jornada_umc(
    tecnico: TecnicoJornada,
    regime: RegimeJornada,
    janela: Janela,
    eventos_existentes: Sequence[EventoSimples],
    *,
    acordo_coletivo_12h: bool = False,
) -> ResultadoJornada:
    """Valida se a janela candidata respeita a jornada UMC do técnico.

    Perfil-AGNÓSTICO: NÃO recebe nem consulta perfil A/B/C/D do tenant.
    A jornada trabalhista é ordem pública (D-AGE-4 / ADV-AGE-04).

    Args:
        tecnico:              dados do técnico (``is_tecnico_campo`` + ``aloca_em_umc``).
        regime:               regime de jornada resolvido via porta.
        janela:               janela candidata do novo evento.
        eventos_existentes:   eventos já alocados para o técnico (sem o novo).
        acordo_coletivo_12h:  se ``True``, teto diário é 12h em vez de 10h (R3).

    Returns:
        ``ResultadoJornada(ok=True)`` se nenhuma regra é violada.
        ``ResultadoJornada(ok=False, violacao, faltante_min, proximo_slot)`` na primeira violação.
        ``ResultadoJornada(ok=True, violacao='R7_NOTURNO_ADVISORY')`` — aviso noturno (não bloqueia).

    Regras por regime:
        ``nao_aplica``             → sem validação.
        ``motorista_profissional`` → R1, R2, R3, R4, R5.
        ``clt_geral``              → R1, R3, R4, R5 (sem R2).
    """
    # Condição de entrada: só valida técnicos de campo alocados em UMC
    if not (tecnico.is_tecnico_campo and tecnico.aloca_em_umc):
        return ResultadoJornada(ok=True)

    if regime == RegimeJornada.NAO_APLICA:
        return ResultadoJornada(ok=True)

    # --- R1: inter-jornada mínima ≥11h ininterruptas ---
    ultimo_fim = _ultima_jornada_fim(eventos_existentes, janela)
    if ultimo_fim is not None:
        gap_horas = (janela.inicia_at - ultimo_fim).total_seconds() / 3600
        if gap_horas < _INTER_JORNADA_MIN_HORAS:
            faltante = (_INTER_JORNADA_MIN_HORAS - gap_horas) * 60
            proximo = _proximo_slot_apos(ultimo_fim, _INTER_JORNADA_MIN_HORAS * 60)
            return ResultadoJornada(
                ok=False,
                violacao="R1_INTER_JORNADA",
                faltante_min=round(faltante, 1),
                proximo_slot=proximo,
            )

    # --- R2: pausa a cada 5h30 de direção contínua (APENAS motorista_profissional) ---
    if regime == RegimeJornada.MOTORISTA_PROFISSIONAL:
        bloco_continuo = _bloco_continuo_antes_de(eventos_existentes, janela)
        total_continuo = bloco_continuo + janela.duracao_minutos
        if total_continuo > _DIRECAO_CONTINUA_MAX_MIN:
            # Quantos minutos de direção ainda cabem antes de precisar de pausa
            restante = _DIRECAO_CONTINUA_MAX_MIN - bloco_continuo
            if restante <= 0:
                # Já estourou antes mesmo de começar — requer pausa imediata
                proximo = _proximo_slot_apos(janela.inicia_at, _PAUSA_DIRECAO_MIN)
            else:
                # Pode dirigir ``restante`` minutos, depois pausa de 30min
                proximo = _proximo_slot_apos(janela.inicia_at, restante + _PAUSA_DIRECAO_MIN)
            return ResultadoJornada(
                ok=False,
                violacao="R2_DIRECAO_CONTINUA",
                faltante_min=round(_PAUSA_DIRECAO_MIN, 1),
                proximo_slot=proximo,
            )

    # --- R3: teto diário ---
    teto_min = _TETO_DIARIO_ACORDO_MIN if acordo_coletivo_12h else _TETO_DIARIO_NORMAL_MIN
    total_dia = _total_alocado_no_dia_min(eventos_existentes, janela, janela.inicia_at)
    if total_dia > teto_min:
        excesso = total_dia - teto_min
        return ResultadoJornada(
            ok=False,
            violacao="R3_TETO_DIARIO",
            faltante_min=round(excesso, 1),
            proximo_slot=None,
        )

    # --- R4: descanso semanal ≥35h a cada 6 dias ---
    janela_inicio = janela.inicia_at
    seis_dias_atras = janela_inicio - timedelta(days=_DSR_JANELA_DIAS)
    eventos_semana = [ev for ev in eventos_existentes if ev.janela.inicia_at >= seis_dias_atras]
    tipos_pausa_r4 = {TipoEvento.DESCANSO_LEGAL, TipoEvento.ALMOCO, TipoEvento.FERIADO}
    total_semana_horas = (
        sum(
            ev.janela.duracao_minutos / 60 for ev in eventos_semana if ev.tipo not in tipos_pausa_r4
        )
        + janela.duracao_minutos / 60
    )
    # Horas trabalhadas em 6 dias + novo evento: verifica se restariam ≥35h de descanso
    horas_em_6_dias = _DSR_JANELA_DIAS * 24
    descanso_disponivel = horas_em_6_dias - total_semana_horas
    if descanso_disponivel < _DSR_MIN_HORAS:
        faltante = (_DSR_MIN_HORAS - descanso_disponivel) * 60
        return ResultadoJornada(
            ok=False,
            violacao="R4_DSR_SEMANAL",
            faltante_min=round(faltante, 1),
            proximo_slot=None,
        )

    # --- R5: refeição ≥1h intrajornada ---
    # Verifica se há evento de ALMOCO ou DESCANSO_LEGAL no dia com duração ≥1h
    # Aplica apenas se a jornada do dia (com novo evento) ultrapassa 6h
    tipos_refeicao = {TipoEvento.ALMOCO, TipoEvento.DESCANSO_LEGAL}
    eventos_dia_r5 = _eventos_do_dia(eventos_existentes, janela.inicia_at)
    total_dia_sem_pausa = _total_alocado_no_dia_min(
        [ev for ev in eventos_existentes if ev.tipo not in tipos_refeicao],
        janela if janela.duracao_minutos > 0 else janela,
        janela.inicia_at,
    )
    if total_dia_sem_pausa > 6 * 60:
        pausa_refeicao = sum(
            ev.janela.duracao_minutos for ev in eventos_dia_r5 if ev.tipo in tipos_refeicao
        )
        if pausa_refeicao < _REFEICAO_MIN_MIN:
            faltante = _REFEICAO_MIN_MIN - pausa_refeicao
            return ResultadoJornada(
                ok=False,
                violacao="R5_REFEICAO",
                faltante_min=round(faltante, 1),
                proximo_slot=None,
            )

    # --- R7: advisory — jornada noturna (22h-5h) — não bloqueia ---
    if _cruza_noturno(janela):
        return ResultadoJornada(
            ok=True,
            violacao="R7_NOTURNO_ADVISORY",
            faltante_min=None,
            proximo_slot=None,
        )

    return ResultadoJornada(ok=True)


# ---------------------------------------------------------------------------
# proximo_slot_valido
# ---------------------------------------------------------------------------


def proximo_slot_valido(
    tecnico: TecnicoJornada,
    regime: RegimeJornada,
    duracao_minutos: float,
    eventos_existentes: Sequence[EventoSimples],
    *,
    a_partir_de: datetime | None = None,
    acordo_coletivo_12h: bool = False,
    max_tentativas: int = 48,
) -> datetime | None:
    """Encontra o próximo horário de início válido para um evento com a duração dada.

    Usa abordagem iterativa: testa candidatos em incrementos de 30min a partir
    de ``a_partir_de`` (default = ``datetime.now(tz=timezone.utc)``).
    Retorna ``None`` se não encontrar slot válido em ``max_tentativas``.

    Args:
        tecnico:            dados do técnico.
        regime:             regime de jornada.
        duracao_minutos:    duração do evento candidato.
        eventos_existentes: eventos já alocados.
        a_partir_de:        início da busca (default = agora UTC).
        acordo_coletivo_12h: habilita teto diário de 12h.
        max_tentativas:     limite de iterações (default 48 = 24h em slots de 30min).

    Returns:
        ``datetime`` do início do próximo slot válido, ou ``None`` se não encontrado.
    """
    candidato = a_partir_de or datetime.now(tz=UTC)
    incremento = timedelta(minutes=30)

    for _ in range(max_tentativas):
        janela_candidata = Janela(
            inicia_at=candidato,
            termina_at=candidato + timedelta(minutes=duracao_minutos),
        )
        resultado = validar_jornada_umc(
            tecnico,
            regime,
            janela_candidata,
            eventos_existentes,
            acordo_coletivo_12h=acordo_coletivo_12h,
        )
        # ok=True sem violação, ou apenas advisory R7 (não bloqueia)
        if resultado.ok:
            return candidato
        # Se há proximo_slot sugerido pela regra, pular direto
        if resultado.proximo_slot is not None:
            candidato = resultado.proximo_slot
        else:
            candidato += incremento

    return None
