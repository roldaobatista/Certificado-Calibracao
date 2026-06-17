"""Use case `feriados` — CRUD custom por tenant + leitura seed nacional (T-AGE-036 / US-AG-005).

Feriados nacionais vêm do seed (migration 0007). Feriados custom (estadual/municipal/empresa)
são criados por tenant. O repositório une ambos na listagem.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime
from uuid import UUID, uuid4

from src.domain.operacao.agenda.entities import Feriado
from src.domain.operacao.agenda.portas import EventoAgendaRepository


@dataclass(frozen=True, slots=True)
class CriarFeriadoCustomInput:
    tenant_id: UUID
    descricao: str
    data: date
    criado_por_usuario_id: UUID


@dataclass(frozen=True, slots=True)
class CriarFeriadoCustomOutput:
    feriado: Feriado


def criar_feriado_custom(
    inp: CriarFeriadoCustomInput,
    *,
    repo: EventoAgendaRepository,
) -> CriarFeriadoCustomOutput:
    """Cria feriado custom (estadual/municipal/empresa) para o tenant."""
    if not inp.descricao.strip():
        raise ValueError("Descrição do feriado é obrigatória.")

    agora = datetime.now(UTC)
    feriado = Feriado(
        id=uuid4(),
        tenant_id=inp.tenant_id,
        data=inp.data,
        descricao=inp.descricao.strip(),
        nacional=False,
        criado_em=agora,
        ativo=True,
    )
    repo.salvar_feriado(feriado)
    return CriarFeriadoCustomOutput(feriado=feriado)


@dataclass(frozen=True, slots=True)
class ListarFeriadosInput:
    tenant_id: UUID
    data_inicio: date
    data_fim: date


@dataclass(frozen=True, slots=True)
class ListarFeriadosOutput:
    feriados: list[Feriado]


def listar_feriados(
    inp: ListarFeriadosInput,
    *,
    repo: EventoAgendaRepository,
) -> ListarFeriadosOutput:
    """Lista feriados nacionais + custom do tenant no intervalo."""
    feriados = repo.listar_feriados(
        tenant_id=inp.tenant_id,
        data_inicio=inp.data_inicio,
        data_fim=inp.data_fim,
    )
    return ListarFeriadosOutput(feriados=feriados)
