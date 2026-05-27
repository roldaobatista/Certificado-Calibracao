"""Job `analisar_correlacao_componentes` (T-CAL-119) — INV-CAL-INC-004.

Detecta orcamentos de incerteza onde 2+ componentes compartilham a mesma
`fonte_default_padrao_id` SEM correlacao declarada entre si. Sinaliza
risco metrologico: componentes correlacionados omitidos do calculo
levam a underestimar a incerteza combinada (NIT-DICLA-030 §7.4 +
JCGM 100:2008 §5.2).

Trigger por evento: `OrcamentoIncerteza.ComponenteInserido` (consumer
procrastinate).

Funcao PURA — recebe lista de componentes de UM orcamento + retorna
acao se INV-CAL-INC-004 violada.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from uuid import UUID

from src.domain.metrologia.calibracao.entities import (
    ComponenteIncertezaSnapshot,
)


@dataclass(frozen=True, slots=True)
class AlertaCorrelacaoOmitida:
    """Alerta P2 (auditor metrologico): correlacao implicita nao declarada."""

    orcamento_incerteza_id: UUID
    tenant_id: UUID
    fonte_default_padrao_id: UUID  # padrao compartilhado pelos componentes
    componentes_envolvidos_ids: tuple[UUID, ...]  # 2+
    correlation_id: UUID  # placeholder — caller injeta da OrcamentoIncerteza


def executar(
    *,
    orcamento_incerteza_id: UUID,
    tenant_id: UUID,
    correlation_id: UUID,
    componentes: list[ComponenteIncertezaSnapshot],
) -> list[AlertaCorrelacaoOmitida]:
    """Detecta grupos de componentes com mesma fonte_default_padrao_id
    sem correlacao_com_componente_id declarada entre eles.

    Args:
      orcamento_incerteza_id: id do orcamento em analise.
      tenant_id: tenant.
      correlation_id: id pra propagar no evento de alerta.
      componentes: lista de snapshots do mesmo orcamento.

    Returns:
      Lista de AlertaCorrelacaoOmitida (1 por fonte_default_padrao_id
      violadora). Vazia se nenhuma violacao.
    """
    # Agrupa por fonte_default_padrao_id (ignora None)
    por_fonte: dict[UUID, list[ComponenteIncertezaSnapshot]] = defaultdict(list)
    for c in componentes:
        if c.orcamento_incerteza_id != orcamento_incerteza_id:
            continue
        if c.tenant_id != tenant_id:
            continue
        if c.fonte_default_padrao_id is None:
            continue
        por_fonte[c.fonte_default_padrao_id].append(c)

    alertas: list[AlertaCorrelacaoOmitida] = []
    for fonte_id, grupo in por_fonte.items():
        if len(grupo) < 2:
            continue
        # Verifica se algum componente do grupo tem correlacao declarada
        # com OUTRO do mesmo grupo (basta 1 par; mas pra grupos >=3 a regra
        # exige que TODOS os pares tenham correlacao declarada. Aproximacao
        # conservadora Wave A: alerta se ALGUM componente do grupo NAO tem
        # correlacao declarada).
        ids_grupo = {c.id for c in grupo}
        alguma_omissao = False
        for c in grupo:
            if c.correlacao_com_componente_id is None:
                alguma_omissao = True
                break
            if c.correlacao_com_componente_id not in ids_grupo:
                # Declara correlacao mas com outro grupo — omitiu intra-grupo
                alguma_omissao = True
                break
        if alguma_omissao:
            alertas.append(
                AlertaCorrelacaoOmitida(
                    orcamento_incerteza_id=orcamento_incerteza_id,
                    tenant_id=tenant_id,
                    fonte_default_padrao_id=fonte_id,
                    componentes_envolvidos_ids=tuple(c.id for c in grupo),
                    correlation_id=correlation_id,
                )
            )
    return alertas
