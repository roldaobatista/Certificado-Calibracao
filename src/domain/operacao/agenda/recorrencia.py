"""Materialização de janelas de recorrência — puro, determinístico, idempotente (Fatia 1a — T-AGE-015).

D-AGE-8 / INV-AG-RECORRENCIA-001 / ADR-0033.

``materializar_janela`` recebe uma ``RegraRecorrencia`` (RRULE RFC 5545 simplificada)
e retorna a lista de datetimes de início das ocorrências em um horizonte de
``dias`` dias a partir de ``inicio``.

Decisão de implementação (não usa dateutil):
    ``dateutil`` NÃO está no pyproject.toml. Implementação própria suporta
    os padrões reais usados no Wave A:
      - ``FREQ=DAILY``
      - ``FREQ=WEEKLY`` + ``BYDAY=MO,TU,WE,TH,FR,SA,SU`` (subconjunto)
      - ``FREQ=MONTHLY`` + ``BYMONTHDAY=N`` (dia fixo do mês)

    Frequências não suportadas levantam ``ValueError`` descritivo.
    A função é PURA, DETERMINÍSTICA e IDEMPOTENTE (ADR-0033 / R10):
    chamadas repetidas com os mesmos argumentos produzem o mesmo resultado.

Funções PURAS — sem I/O, sem Django.
"""

from __future__ import annotations

import re
from datetime import date, datetime, timedelta
from typing import Final

from .value_objects import RegraRecorrencia

# Mapeamento de dia da semana RRULE → índice Python (0=segunda .. 6=domingo)
_DIA_SEMANA: Final[dict[str, int]] = {
    "MO": 0,
    "TU": 1,
    "WE": 2,
    "TH": 3,
    "FR": 4,
    "SA": 5,
    "SU": 6,
}

# Padrões RRULE suportados
_RE_FREQ = re.compile(r"FREQ=(\w+)", re.IGNORECASE)
_RE_BYDAY = re.compile(r"BYDAY=([\w,]+)", re.IGNORECASE)
_RE_BYMONTHDAY = re.compile(r"BYMONTHDAY=(-?\d+)", re.IGNORECASE)
_RE_COUNT = re.compile(r"COUNT=(\d+)", re.IGNORECASE)
_RE_INTERVAL = re.compile(r"INTERVAL=(\d+)", re.IGNORECASE)


def _parse_rrule(rrule_str: str) -> dict[str, object]:
    """Extrai os parâmetros relevantes de uma string RRULE.

    Retorna um dicionário com as chaves presentes.
    Levanta ``ValueError`` para FREQ não suportada ou string malformada.
    """
    freq_m = _RE_FREQ.search(rrule_str)
    if not freq_m:
        raise ValueError(f"RRULE inválida: FREQ ausente. String recebida: {rrule_str!r}")
    freq = freq_m.group(1).upper()
    suportadas = {"DAILY", "WEEKLY", "MONTHLY"}
    if freq not in suportadas:
        raise ValueError(
            f"FREQ={freq!r} não suportada nesta implementação. "
            f"Suportadas: {sorted(suportadas)}. RRULE: {rrule_str!r}"
        )

    params: dict[str, object] = {"freq": freq}

    # INTERVAL (default 1)
    interval_m = _RE_INTERVAL.search(rrule_str)
    params["interval"] = int(interval_m.group(1)) if interval_m else 1

    # COUNT (limitador explícito de ocorrências)
    count_m = _RE_COUNT.search(rrule_str)
    params["count"] = int(count_m.group(1)) if count_m else None

    # BYDAY (para WEEKLY)
    byday_m = _RE_BYDAY.search(rrule_str)
    if byday_m:
        raw_dias = [d.strip().upper() for d in byday_m.group(1).split(",")]
        dias_invalidos = [d for d in raw_dias if d not in _DIA_SEMANA]
        if dias_invalidos:
            raise ValueError(
                f"BYDAY contém dias inválidos: {dias_invalidos!r}. "
                f"Válidos: {sorted(_DIA_SEMANA)}. RRULE: {rrule_str!r}"
            )
        params["byday"] = [_DIA_SEMANA[d] for d in raw_dias]
    else:
        params["byday"] = None

    # BYMONTHDAY (para MONTHLY)
    bymonthday_m = _RE_BYMONTHDAY.search(rrule_str)
    if bymonthday_m:
        params["bymonthday"] = int(bymonthday_m.group(1))
    else:
        params["bymonthday"] = None

    return params


def materializar_janela(
    regra: RegraRecorrencia,
    inicio: datetime,
    dias: int = 90,
) -> list[datetime]:
    """Materializa as ocorrências de uma regra RRULE em um horizonte de ``dias`` dias.

    Puro, determinístico e idempotente (ADR-0033 / INV-AG-RECORRENCIA-001 / R10):
    chamadas repetidas com os mesmos argumentos produzem sempre o mesmo resultado.

    A unicidade de ocorrências no banco é garantida pelo UNIQUE
    ``(recorrencia_id, ocorrencia_dt)`` na Fatia 1b — esta função apenas
    calcula os datetimes sem tocar o banco.

    Args:
        regra:  regra de recorrência com ``rrule_str`` (RRULE RFC 5545 simplificada).
        inicio: data/hora de início da primeira ocorrência (âncora da série).
        dias:   horizonte em dias a partir de ``inicio`` (default 90).

    Returns:
        Lista de datetimes de início de ocorrência, em ordem crescente,
        dentro do horizonte ``[inicio, inicio + dias)``.

    Raises:
        ValueError: se a RRULE for inválida ou a frequência não for suportada.

    Exemplos suportados:
        ``FREQ=DAILY``                         — diário.
        ``FREQ=DAILY;INTERVAL=2``              — a cada 2 dias.
        ``FREQ=WEEKLY;BYDAY=MO,WE,FR``         — semanal às 2ª/4ª/6ª.
        ``FREQ=MONTHLY;BYMONTHDAY=1``          — primeiro dia do mês.
        ``FREQ=WEEKLY;BYDAY=TU;COUNT=4``       — 4 terças-feiras.
    """
    params = _parse_rrule(regra.rrule_str)
    freq: str = params["freq"]  # type: ignore[assignment]
    interval: int = params["interval"]  # type: ignore[assignment]
    count: int | None = params["count"]  # type: ignore[assignment]
    byday: list[int] | None = params["byday"]  # type: ignore[assignment]
    bymonthday: int | None = params["bymonthday"]  # type: ignore[assignment]

    limite = inicio + timedelta(days=dias)
    ocorrencias: list[datetime] = []

    if freq == "DAILY":
        candidato = inicio
        while candidato < limite:
            if count is not None and len(ocorrencias) >= count:
                break
            ocorrencias.append(candidato)
            candidato += timedelta(days=interval)

    elif freq == "WEEKLY":
        dias_alvo: list[int] = byday if byday is not None else [inicio.weekday()]
        # Começa pelo início da semana que contém ``inicio``
        # Para determinismo, iteramos dia a dia e filtramos pelos dias-alvo
        candidato = inicio
        # Alinha candidato ao primeiro dia-alvo na semana de início
        while candidato < limite:
            if count is not None and len(ocorrencias) >= count:
                break
            if candidato.weekday() in dias_alvo:
                if candidato >= inicio:
                    ocorrencias.append(candidato)
            candidato += timedelta(days=1)
            # Se interval > 1, pular semanas: após completar uma semana, avançar (interval-1) semanas
            # Implementação simplificada: agrupamos por semana
            # Para exatidão com interval > 1, usamos o número de semana
        # Para INTERVAL > 1: filtrar apenas as semanas corretas. Alinha ao início
        # da semana (segunda — WKST default RFC 5545) e conta semanas decorridas:
        # determinístico e robusto à virada de ano (o cálculo por nº de semana ISO
        # ano*53+semana quebrava a paridade quando o ano tinha 52 semanas).
        if interval > 1 and ocorrencias:
            seg_inicio = _segunda_da_semana(inicio.date())
            ocorrencias = [
                dt
                for dt in ocorrencias
                if ((_segunda_da_semana(dt.date()) - seg_inicio).days // 7) % interval == 0
            ]

    elif freq == "MONTHLY":
        dia_mes = bymonthday if bymonthday is not None else inicio.day
        candidato = _mesmo_mes_dia(inicio, dia_mes)
        if candidato < inicio:
            candidato = _proximo_mes(candidato, dia_mes)
        while candidato < limite:
            if count is not None and len(ocorrencias) >= count:
                break
            ocorrencias.append(candidato)
            for _ in range(interval):
                candidato = _proximo_mes(candidato, dia_mes)

    return sorted(ocorrencias)


# ---------------------------------------------------------------------------
# Helpers de data
# ---------------------------------------------------------------------------


def _segunda_da_semana(d: date) -> date:
    """Retorna a segunda-feira da semana de ``d`` (WKST=segunda, default RFC 5545).

    Base para contar semanas decorridas no cálculo de ``INTERVAL`` semanal de
    forma determinística e robusta à virada de ano.
    """
    return d - timedelta(days=d.weekday())


def _mesmo_mes_dia(dt: datetime, dia: int) -> datetime:
    """Retorna datetime no mesmo mês/ano de ``dt`` com o dia ``dia``.

    Clamp: se ``dia`` excede o número de dias do mês, usa o último dia.
    """
    import calendar

    ultimo_dia = calendar.monthrange(dt.year, dt.month)[1]
    dia_real = min(dia, ultimo_dia)
    return dt.replace(day=dia_real, hour=dt.hour, minute=dt.minute, second=dt.second)


def _proximo_mes(dt: datetime, dia: int) -> datetime:
    """Avança ``dt`` para o mesmo dia no mês seguinte.

    Clamp: se ``dia`` excede o número de dias do próximo mês, usa o último dia.
    """
    import calendar

    mes = dt.month + 1
    ano = dt.year
    if mes > 12:
        mes = 1
        ano += 1
    ultimo_dia = calendar.monthrange(ano, mes)[1]
    dia_real = min(dia, ultimo_dia)
    return dt.replace(year=ano, month=mes, day=dia_real)
