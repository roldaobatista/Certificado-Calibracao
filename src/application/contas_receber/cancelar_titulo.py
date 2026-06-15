"""Use case `cancelar_titulo` — parte cancelar de T-CR-034.

Fluxo (D-CR-3):
  1. Carrega título + pagamentos do repo.
  2. `pode_cancelar(titulo, pagamentos)` — levanta `TituloComPagamentoParcial` (409)
     se houver qualquer pagamento registrado (mesmo parcial).
  3. `validar_transicao(estado, CANCELADO)` — levanta `TransicaoProibida` (409) se
     já está em estado terminal.
  4. Persiste cancelamento: estado=cancelado + cancelado_em (via atualizar_titulo
     + cancelado_em direto no banco via SQL no repository).

NÃO publica evento — view publica `contas_receber.titulo_cancelado` no mesmo `atomic`.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import UTC, datetime
from uuid import UUID

from src.domain.contas_receber.entities import Titulo
from src.domain.contas_receber.enums import EstadoTitulo
from src.domain.contas_receber.erros import TituloNaoEncontrado
from src.domain.contas_receber.portas import TituloRepository
from src.domain.contas_receber.transicoes import pode_cancelar, validar_transicao


@dataclass(frozen=True, slots=True)
class CancelarTituloInput:
    """Payload de cancelamento.

    `razao` — motivo livre do cancelamento (vai no payload do evento).
    """

    tenant_id: UUID
    titulo_id: UUID
    razao: str = ""


@dataclass(frozen=True, slots=True)
class CancelarTituloOutput:
    titulo: Titulo
    cancelado_em: datetime


def executar(
    inp: CancelarTituloInput,
    *,
    repo: TituloRepository,
) -> CancelarTituloOutput:
    """Cancela título. NÃO publica evento (responsabilidade da view)."""
    # 1. Carrega título e pagamentos
    titulo = repo.obter_por_id(tenant_id=inp.tenant_id, titulo_id=inp.titulo_id)
    if titulo is None:
        raise TituloNaoEncontrado(f"Título {inp.titulo_id} não encontrado.")

    pagamentos = repo.listar_pagamentos(tenant_id=inp.tenant_id, titulo_id=inp.titulo_id)

    # 2. Regra de negócio: só cancela sem pagamento (D-CR-3 / INV-CR-PAGAMENTO-WORM)
    # Levanta TituloComPagamentoParcial se há qualquer pagamento.
    pode_cancelar(titulo, pagamentos)

    # 3. Valida transição de estado
    validar_transicao(titulo.estado, EstadoTitulo.CANCELADO)

    # 4. Persiste cancelamento
    agora = datetime.now(UTC)
    titulo_cancelado = replace(titulo, estado=EstadoTitulo.CANCELADO)
    repo.atualizar_titulo_cancelado(
        tenant_id=inp.tenant_id,
        titulo=titulo_cancelado,
        cancelado_em=agora,
    )

    return CancelarTituloOutput(titulo=titulo_cancelado, cancelado_em=agora)
