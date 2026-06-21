"""Use case: validação de despesa pelo financeiro (US-CT-003 / Fatia 2).

Transição ``pendente → validada``. Despesa validada torna-se WORM —
trigger PG bloqueia UPDATE/DELETE após a transição (INV-CT-IMUT-001).

Não publica eventos — a view faz isso dentro do ``transaction.atomic``.

Refs: D-CT-3; US-CT-003; INV-CT-IMUT-001.
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
class ValidarDespesaInput:
    """Parâmetros de entrada para validação de despesa (US-CT-003)."""

    tenant_id: UUID
    despesa_id: UUID
    usuario_id: UUID


class ValidarDespesaUseCase:
    """Valida uma despesa pendente, promovendo-a para o estado ``validada``.

    Dependências injetadas via construtor (hexagonal — ADR-0007).
    """

    def __init__(self, despesa_repo: DespesaRepository) -> None:
        self._despesa_repo = despesa_repo

    def executar(self, inp: ValidarDespesaInput) -> Despesa:
        """Executa a validação da despesa.

        Fluxo:
        1. Carrega a despesa existente.
        2. Valida transição de estado: deve estar em ``pendente``.
        3. Atualiza para ``validada`` com timestamp de validação.

        Returns:
            Despesa atualizada no estado ``validada``.

        Raises:
            ValueError: despesa não encontrada.
            TransicaoInvalida: despesa não está no estado ``pendente`` (422).
        """
        # 1. Carrega despesa
        despesa = self._despesa_repo.obter_por_id(inp.tenant_id, inp.despesa_id)
        if despesa is None:
            raise ValueError("despesa não encontrada")

        # 2. Valida transição (pendente → validada)
        validar_transicao_despesa(de=despesa.estado, para=EstadoDespesa.VALIDADA)

        # 3. Atualiza estado (frozen → dataclasses.replace)
        despesa_atualizada = dataclasses.replace(
            despesa,
            estado=EstadoDespesa.VALIDADA,
            validado_em=datetime.now(UTC),
        )

        # 4. Persiste
        self._despesa_repo.atualizar(inp.tenant_id, despesa_atualizada)

        return despesa_atualizada
