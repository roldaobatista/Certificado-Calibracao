"""Adapters M3↔M4 para a competência do executor por grandeza (ADR-0063 Opção A).

Funções de módulo (molde ADR-0073 — sem estado) que a view de `configurar_calibracao`
(M4) injeta nas portas `CompetenciaExecutorPort` / `PropagarGrandezaAtividadePort`. Vivem
em `ordens_servico` porque é o dono de `AtividadeDaOS` (o adapter de M4 chama a FUNÇÃO, não
importa o model cross-módulo — port-binding). Defesa em profundidade: `tenant_id` explícito.

- `competencia_executor_cobre`: resolve o técnico atribuído à atividade
  (`AtividadeDaOS.tecnico_executor_id`) ou usa o `executor_fallback_id` (origem AVULSA) e
  delega ao predicate `rt_competencia_cobre` (lógica real RTCompetencia). Sem técnico
  atribuído → fail-open (a emissão M8 ainda barra o signatário — INV-CER-COMP-001).
- `propagar_grandeza_atividade`: `UPDATE atividade_da_os SET grandeza` (fecha o predicate
  M3 retroativamente p/ transferências posteriores — ADR-0063 ponto 3).
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from src.infrastructure.ordens_servico.models import AtividadeDaOS
from src.infrastructure.ordens_servico.predicates_os import rt_competencia_cobre


def competencia_executor_cobre(
    *,
    tenant_id: UUID,
    atividade_os_id: UUID | None,
    executor_fallback_id: UUID | None,
    grandeza: str,
    data: datetime,
) -> tuple[bool, str]:
    """`(True, '')` se o técnico responsável cobre a `grandeza` na `data`; senão
    `(False, reason)`. Sem técnico resolvido → fail-open (`True, ''`) — ninguém executou
    ainda; a competência do signatário é barrada na emissão (M8)."""
    tecnico_id: UUID | None = None
    if atividade_os_id is not None:
        tecnico_id = (
            AtividadeDaOS.objects.filter(id=atividade_os_id, tenant_id=tenant_id)
            .values_list("tecnico_executor_id", flat=True)
            .first()
        )
    tecnico_id = tecnico_id or executor_fallback_id
    if tecnico_id is None:
        return True, ""  # sem executor atribuído — fail-open (emissão M8 barra signatário)

    return rt_competencia_cobre(
        {
            "tenant_id": str(tenant_id),
            "executor_user_id": str(tecnico_id),
            "grandeza": grandeza,
            "data": data.date().isoformat(),
        }
    )


def propagar_grandeza_atividade(
    *, tenant_id: UUID, atividade_os_id: UUID, grandeza: str
) -> None:
    """Grava a grandeza calibrada em `AtividadeDaOS.grandeza` (campo mutável, sem trigger
    WORM). Fecha o predicate M3 `rt_competencia_cobre` p/ transferências posteriores."""
    AtividadeDaOS.objects.filter(id=atividade_os_id, tenant_id=tenant_id).update(
        grandeza=grandeza
    )
