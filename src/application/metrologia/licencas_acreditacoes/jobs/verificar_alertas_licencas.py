"""Job `verificar_alertas_licencas` — US-LIC-002 (M9 T-LIC-051).

Função PURA (ADR-0007): recebe os snapshots dos documentos regulatórios vigentes do
tenant + `agora` + janelas (D-90/60/30/15/7) e retorna os `AlertaVencimento` que
DEVEM existir (estado desejado). O caller (command Django) lê o DB, chama esta função
e agenda via `AlertaRepository.agendar` — idempotente pela UNIQUE
`(tenant, documento, janela_dias)` (reexecução diária não duplica).

Semântica: para um documento a `dias = (vigencia_fim - agora)` do vencimento, devem
existir alertas para TODAS as janelas `j` com `dias <= j` (entrou na janela). Quando o
documento vence (`dias < 0`) os alertas já criados nos dias anteriores permanecem; a
função não cria nada novo além das janelas aplicáveis. Documento revogado é ignorado.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from uuid import UUID, uuid4

from src.domain.metrologia.licencas_acreditacoes.entities import AlertaVencimento
from src.domain.metrologia.licencas_acreditacoes.enums import (
    JANELAS_ALERTA_DIAS,
    CanalAlerta,
)

# Destinatário-padrão (dashboard do tenant) quando o documento não tem responsável.
_DESTINATARIO_DASHBOARD = UUID(int=0)


@dataclass(frozen=True, slots=True)
class DocumentoAlertaSnapshot:
    """Snapshot leve de um documento para a verificação de alertas (sem Django)."""

    documento_id: UUID
    tenant_id: UUID
    vigencia_fim: date
    revogado: bool = False
    responsavel_id: UUID | None = None


def verificar_alertas_licencas(
    snapshots: list[DocumentoAlertaSnapshot],
    *,
    agora: date,
    janelas: tuple[int, ...] = JANELAS_ALERTA_DIAS,
    canal: CanalAlerta = CanalAlerta.DASHBOARD,
) -> list[AlertaVencimento]:
    """Retorna os `AlertaVencimento` a agendar (idempotência via UNIQUE no caller).

    Args:
        snapshots: documentos regulatórios do tenant (já no contexto RLS).
        agora: data corrente (injetada — testes determinísticos).
        janelas: janelas em dias antes do vencimento (default 90/60/30/15/7).
        canal: canal do alerta (default DASHBOARD — e-mail é diferido ADR-0060).

    Returns:
        Lista de alertas (vazia se nada na janela). Caller agenda via repo.
    """
    alertas: list[AlertaVencimento] = []
    for snap in snapshots:
        if snap.revogado:
            continue
        dias = (snap.vigencia_fim - agora).days
        destinatario = snap.responsavel_id or _DESTINATARIO_DASHBOARD
        for janela in janelas:
            if dias <= janela:
                alertas.append(
                    AlertaVencimento(
                        id=uuid4(),
                        tenant_id=snap.tenant_id,
                        documento_id=snap.documento_id,
                        data_disparo=agora,
                        janela_dias=janela,
                        canal=canal,
                        destinatario_id=destinatario,
                    )
                )
    return alertas
