"""Use case: rejeição de despesa pelo financeiro (US-CT-004 / Fatia 2).

Transição ``pendente → rejeitada``. O motivo de rejeição deve ter no mínimo
30 caracteres para garantir clareza ao técnico.

Não publica eventos — a view faz isso dentro do ``transaction.atomic``.

Refs: D-CT-3; US-CT-004.
"""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID

from src.domain.caixa_tecnico.entities import Despesa
from src.domain.caixa_tecnico.enums import EstadoDespesa
from src.domain.caixa_tecnico.transicoes_despesa import (
    validar_transicao as validar_transicao_despesa,
)
from src.infrastructure.caixa_tecnico.repositories import DespesaRepository


@dataclass
class RejeitarDespesaInput:
    """Parâmetros de entrada para rejeição de despesa (US-CT-004).

    ``motivo`` deve ter no mínimo 30 caracteres.
    """

    tenant_id: UUID
    despesa_id: UUID
    motivo: str
    usuario_id: UUID


class RejeitarDespesaUseCase:
    """Rejeita uma despesa pendente com motivo obrigatório.

    Dependências injetadas via construtor (hexagonal — ADR-0007).
    """

    def __init__(self, despesa_repo: DespesaRepository) -> None:
        self._despesa_repo = despesa_repo

    def executar(self, inp: RejeitarDespesaInput) -> Despesa:
        """Executa a rejeição da despesa.

        Fluxo:
        1. Carrega a despesa existente.
        2. Valida comprimento mínimo do motivo (≥30 chars).
        3. Valida transição de estado: deve estar em ``pendente``.
        4. Atualiza para ``rejeitada`` com motivo e timestamp.

        Returns:
            Despesa atualizada no estado ``rejeitada``.

        Raises:
            ValueError: despesa não encontrada ou motivo muito curto.
            TransicaoInvalida: despesa não está no estado ``pendente`` (422).
        """
        # 1. Carrega despesa
        despesa = self._despesa_repo.obter_por_id(inp.tenant_id, inp.despesa_id)
        if despesa is None:
            raise ValueError("despesa não encontrada")

        # 2. Valida motivo
        if len(inp.motivo) < 30:
            raise ValueError("motivo deve ter no mínimo 30 caracteres")

        # 3. Valida transição (pendente → rejeitada)
        validar_transicao_despesa(de=despesa.estado, para=EstadoDespesa.REJEITADA)

        # 4. Atualiza estado (frozen → dataclasses.replace)
        despesa_atualizada = dataclasses.replace(
            despesa,
            estado=EstadoDespesa.REJEITADA,
            motivo_rejeicao=inp.motivo,
            rejeitado_em=datetime.now(UTC),
        )

        # 5. Persiste
        self._despesa_repo.atualizar(inp.tenant_id, despesa_atualizada)

        return despesa_atualizada
