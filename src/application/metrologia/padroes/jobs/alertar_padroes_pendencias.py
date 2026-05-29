"""Job `alertar_padroes_pendencias` (T-PAD-050 — P6 M5 padroes).

ISO 17025 cl. 6.4.7/6.4.10/6.5 — o padrao metrologico tem ciclo de vida
com vencimentos que, se ignorados, invalidam calibracoes derivadas (cl. 8.4
rastreabilidade). Este job varre 4 tipos de pendencia e emite alertas P1/P2
ao gerente de qualidade / RT:

  1. RECAL_VENCENDO          — `proximo_recal` <= hoje + 30d (ou ja vencido).
  2. VI_PENDENTE             — ultima VI + `intervalo_vi_meses` <= hoje + 30d.
  3. RECAL_RETORNO_ATRASADO  — recal ENVIADO ha > 90 dias sem retorno
                               (padrao preso em EM_RECAL_EXTERNO).
  4. RECAL_APROVACAO_RT_PENDENTE — recal RETORNADO ha > N dias sem analise
                               critica do RT (estado
                               RECAL_RETORNADO_PENDENTE_APROVACAO — C-4).

Funcao PURA — recebe snapshots ja filtrados pelo caller + `agora` tz-aware.
Retorna lista de AlertaPadrao (pode ser vazia). NAO muta estado: o caller
(adapter Django) publica os alertas via bus e/ou loga.

Idempotente: chamadas multiplas no mesmo dia retornam alertas identicos;
caller deduplica via `correlation_id` do padrao/recal.

Frequencia recomendada (Wave A): diaria (e.g. 04:00 BRT).

INV-VIG-004: `agora` exige datetime tz-aware.
"""

from __future__ import annotations

import calendar
from dataclasses import dataclass
from datetime import date, datetime
from enum import Enum
from uuid import UUID

from src.domain.metrologia.padroes.entities import (
    PadraoMetrologicoSnapshot,
    RecalExternoPadraoSnapshot,
)

# Janela de antecedencia (dias corridos) para alertar vencimento futuro.
_DIAS_ALERTA_RECAL = 30
_DIAS_ALERTA_VI = 30
# Recal enviado ao lab externo sem retorno por mais que isso = P1.
_DIAS_RECAL_RETORNO_LIMITE = 90
# Recal retornado sem analise critica do RT por mais que isso = P2 (C-4).
_DIAS_APROVACAO_RT_LIMITE_DEFAULT = 7


class TipoAlertaPadrao(str, Enum):
    """Discrimina o tipo de pendencia detectada (str-mixin p/ JSON)."""

    RECAL_VENCENDO = "RECAL_VENCENDO"
    VI_PENDENTE = "VI_PENDENTE"
    RECAL_RETORNO_ATRASADO = "RECAL_RETORNO_ATRASADO"
    RECAL_APROVACAO_RT_PENDENTE = "RECAL_APROVACAO_RT_PENDENTE"


@dataclass(frozen=True, slots=True)
class PadraoComUltimaVI:
    """Entrada para o tipo VI_PENDENTE.

    `ultima_vi_em` = None quando o padrao NUNCA teve VI; nesse caso a base de
    calculo da proxima VI eh `vigencia_inicio` do padrao.
    """

    padrao: PadraoMetrologicoSnapshot
    ultima_vi_em: datetime | None


@dataclass(frozen=True, slots=True)
class AlertaPadrao:
    """Alerta que o adapter Django publica via bus / loga.

    `dias`: dias restantes (>=0) quando ainda dentro da janela de
    antecedencia, ou dias de atraso (negativo) quando ja vencido/estourado.
    `referencia_id`: id do recal quando o alerta deriva de um recal.
    """

    tipo: TipoAlertaPadrao
    padrao_id: UUID
    tenant_id: UUID
    numero_serie: str
    severidade: str  # "P1_*" | "P2_ALERTA"
    dias: int
    correlation_id: UUID
    referencia_id: UUID | None = None


def _somar_meses(base: datetime, meses: int) -> datetime:
    """Soma `meses` a `base` com clamp do dia ao ultimo dia do mes alvo.

    Ex.: 31/01 + 1 mes -> 28/02 (ou 29 em bissexto). Puro — usa calendar
    (stdlib). Nao depende de dateutil (nao eh dependencia do projeto).
    """
    mes_total = base.month - 1 + meses
    ano = base.year + mes_total // 12
    mes = mes_total % 12 + 1
    dia = min(base.day, calendar.monthrange(ano, mes)[1])
    return base.replace(year=ano, month=mes, day=dia)


def _classificar_vencimento(
    dias_restantes: int, janela: int, severidade_vencido: str
) -> str | None:
    """Severidade por antecedencia. Retorna None se ainda fora da janela."""
    if dias_restantes < 0:
        return severidade_vencido
    if dias_restantes <= janela:
        return "P2_ALERTA"
    return None


def _alertas_recal_vencendo(
    padroes_em_uso: list[PadraoMetrologicoSnapshot], hoje: date
) -> list[AlertaPadrao]:
    alertas: list[AlertaPadrao] = []
    for p in padroes_em_uso:
        # Defensivo: origem revogada ja esta bloqueada — nao realertar.
        if p.rastreabilidade_origem_revogada:
            continue
        dias = (p.proximo_recal - hoje).days
        sev = _classificar_vencimento(dias, _DIAS_ALERTA_RECAL, "P1_VENCIDO")
        if sev is None:
            continue
        alertas.append(
            AlertaPadrao(
                tipo=TipoAlertaPadrao.RECAL_VENCENDO,
                padrao_id=p.id,
                tenant_id=p.tenant_id,
                numero_serie=p.numero_serie,
                severidade=sev,
                dias=dias,
                correlation_id=p.correlation_id,
            )
        )
    return alertas


def _alertas_vi_pendente(
    padroes_vi: list[PadraoComUltimaVI], hoje: date
) -> list[AlertaPadrao]:
    alertas: list[AlertaPadrao] = []
    for item in padroes_vi:
        p = item.padrao
        if p.rastreabilidade_origem_revogada:
            continue
        base = item.ultima_vi_em if item.ultima_vi_em is not None else p.vigencia_inicio
        proxima_vi = _somar_meses(base, p.intervalo_vi_meses)
        dias = (proxima_vi.date() - hoje).days
        sev = _classificar_vencimento(dias, _DIAS_ALERTA_VI, "P1_VI_VENCIDA")
        if sev is None:
            continue
        alertas.append(
            AlertaPadrao(
                tipo=TipoAlertaPadrao.VI_PENDENTE,
                padrao_id=p.id,
                tenant_id=p.tenant_id,
                numero_serie=p.numero_serie,
                severidade=sev,
                dias=dias,
                correlation_id=p.correlation_id,
            )
        )
    return alertas


def _alertas_recal_retorno_atrasado(
    recals_enviados: list[RecalExternoPadraoSnapshot],
    padroes_por_id: dict[UUID, PadraoMetrologicoSnapshot],
    agora: datetime,
) -> list[AlertaPadrao]:
    alertas: list[AlertaPadrao] = []
    for r in recals_enviados:
        dias_no_lab = (agora - r.enviado_em).days
        if dias_no_lab <= _DIAS_RECAL_RETORNO_LIMITE:
            continue
        p = padroes_por_id.get(r.padrao_id)
        numero_serie = p.numero_serie if p is not None else ""
        correlation_id = p.correlation_id if p is not None else r.id
        alertas.append(
            AlertaPadrao(
                tipo=TipoAlertaPadrao.RECAL_RETORNO_ATRASADO,
                padrao_id=r.padrao_id,
                tenant_id=r.tenant_id,
                numero_serie=numero_serie,
                severidade="P1_RECAL_PRESO",
                dias=_DIAS_RECAL_RETORNO_LIMITE - dias_no_lab,  # negativo
                correlation_id=correlation_id,
                referencia_id=r.id,
            )
        )
    return alertas


def _alertas_aprovacao_rt_pendente(
    recals_retornados: list[RecalExternoPadraoSnapshot],
    padroes_por_id: dict[UUID, PadraoMetrologicoSnapshot],
    agora: datetime,
    limite_dias: int,
) -> list[AlertaPadrao]:
    alertas: list[AlertaPadrao] = []
    for r in recals_retornados:
        # Ja aprovado nao gera alerta (caller deveria filtrar; defensivo).
        if r.aprovado_rt_em is not None or r.retornado_em is None:
            continue
        dias_aguardando = (agora - r.retornado_em).days
        if dias_aguardando <= limite_dias:
            continue
        p = padroes_por_id.get(r.padrao_id)
        numero_serie = p.numero_serie if p is not None else ""
        correlation_id = p.correlation_id if p is not None else r.id
        alertas.append(
            AlertaPadrao(
                tipo=TipoAlertaPadrao.RECAL_APROVACAO_RT_PENDENTE,
                padrao_id=r.padrao_id,
                tenant_id=r.tenant_id,
                numero_serie=numero_serie,
                severidade="P2_ALERTA",
                dias=limite_dias - dias_aguardando,  # negativo
                correlation_id=correlation_id,
                referencia_id=r.id,
            )
        )
    return alertas


def executar(
    *,
    padroes_em_uso: list[PadraoMetrologicoSnapshot],
    padroes_vi: list[PadraoComUltimaVI],
    recals_enviados: list[RecalExternoPadraoSnapshot],
    recals_retornados: list[RecalExternoPadraoSnapshot],
    agora: datetime,
    limite_aprovacao_rt_dias: int = _DIAS_APROVACAO_RT_LIMITE_DEFAULT,
) -> list[AlertaPadrao]:
    """Varre as 4 pendencias e retorna a lista consolidada de alertas.

    Args:
      padroes_em_uso: padroes EM_USO (para RECAL_VENCENDO).
      padroes_vi: padroes EM_USO + sua ultima VI (para VI_PENDENTE).
      recals_enviados: recals com status ENVIADO (para RECAL_RETORNO_ATRASADO).
      recals_retornados: recals RETORNADO sem aprovacao RT
        (para RECAL_APROVACAO_RT_PENDENTE).
      agora: timestamp atual tz-aware.
      limite_aprovacao_rt_dias: prazo da analise critica do RT pos-retorno.

    Returns:
      Lista de AlertaPadrao (pode ser vazia).

    Levanta:
      ValueError se `agora` nao for tz-aware (INV-VIG-004).
    """
    if agora.tzinfo is None:
        raise ValueError(
            "alertar_padroes_pendencias: agora exige datetime tz-aware "
            "(INV-VIG-004)"
        )
    hoje = agora.date()

    # Indice padrao_id -> snapshot para enriquecer alertas de recal.
    padroes_por_id: dict[UUID, PadraoMetrologicoSnapshot] = {
        p.id: p for p in padroes_em_uso
    }

    return [
        *_alertas_recal_vencendo(padroes_em_uso, hoje),
        *_alertas_vi_pendente(padroes_vi, hoje),
        *_alertas_recal_retorno_atrasado(recals_enviados, padroes_por_id, agora),
        *_alertas_aprovacao_rt_pendente(
            recals_retornados, padroes_por_id, agora, limite_aprovacao_rt_dias
        ),
    ]
