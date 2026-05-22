"""T-EQP-054 (US-EQP-006 AC-EQP-006-7 / P-EQP-T9) — sweep de
equipamentos orfaos.

Trigger PG `equipamento_anti_orfao_imediato` (migration 0002) ja marca
o equipamento como `orfao_pendente_decisao` na hora em que o cliente
referenciado e deletado. Este service e a DEFESA EM PROFUNDIDADE:
- Casos de race condition (insert tardio durante delete do cliente).
- Manutencao manual via app_migrator (bypass do trigger porque ele
  vive no app_user role).
- Migracoes que envolvem reorganizar relacao Cliente<->Equipamento.

Service `marcar_equipamentos_orfaos_pendentes` localiza inconsistencias
e corrige + publica `equipamento.orfao_marcado_pelo_job` (alerta P3
operacao Wave A — consumer real notifica admin_tenant).

ISO/IEC 17025 cl. 7.4.4 — integridade do item de ensaio na cadeia
de custodia exige que orfaos sejam tratados explicitamente, nao
deixados em status `ativo` sem cliente.
"""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID, uuid4

from django.db import transaction

from src.infrastructure.audit.event_helpers import publicar_evento
from src.infrastructure.equipamentos.models import (
    Equipamento,
    EquipamentoStatus,
)

# Status que NAO devem ser marcados orfaos automaticamente (ja terminais).
STATUS_TERMINAIS_PARA_ORFAO: frozenset[str] = frozenset(
    {
        EquipamentoStatus.SUCATA.value,
        EquipamentoStatus.EXTRAVIADO.value,
        EquipamentoStatus.ORFAO_PENDENTE_DECISAO.value,
    }
)


@dataclass(frozen=True)
class OrfaoMarcado:
    equipamento_id: UUID
    status_anterior: str


def marcar_equipamentos_orfaos_pendentes(
    *,
    tenant_id: UUID,
    detectado_pelo_usuario_id: UUID | None = None,
) -> list[OrfaoMarcado]:
    """Localiza equipamentos com `cliente_atual_id IS NULL` que NAO
    estao em status terminal e os marca como `orfao_pendente_decisao`.

    Pre-condicao: caller deve setar `app.active_tenant_id` via
    `run_in_tenant_context` (RLS valida).

    Publica 1 evento `equipamento.orfao_marcado_pelo_job` por
    equipamento marcado (payload sanitizado: equipamento_id,
    status_anterior, detectado_em).

    Retorna lista de `OrfaoMarcado` para o caller logar.
    """
    candidatos = list(
        Equipamento.objects.filter(
            tenant_id=tenant_id,
            cliente_atual_id__isnull=True,
        ).exclude(status__in=STATUS_TERMINAIS_PARA_ORFAO)
    )

    marcados: list[OrfaoMarcado] = []
    for eq in candidatos:
        status_anterior = eq.status
        with transaction.atomic():
            # UPDATE direto evita validacao do clean() (que pode reler
            # o cliente_atual e duplicar trabalho).
            Equipamento.objects.filter(id=eq.id).update(
                status=EquipamentoStatus.ORFAO_PENDENTE_DECISAO.value
            )
            publicar_evento(
                acao="equipamento.orfao_marcado_pelo_job",
                tenant_id=tenant_id,
                usuario_id=detectado_pelo_usuario_id,
                causation_id=uuid4(),
                payload={
                    "tenant_id": str(tenant_id),
                    "equipamento_id": str(eq.id),
                    "status_anterior": status_anterior,
                    "motivo": "cliente_atual_id_nulo_sem_status_terminal",
                },
                resource_summary=f"equipamento:{eq.id}:orfao_job",
            )
        marcados.append(
            OrfaoMarcado(equipamento_id=eq.id, status_anterior=status_anterior)
        )
    return marcados
