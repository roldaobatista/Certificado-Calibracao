"""Use case: registro de entrega de adiantamento (US-CT-008 / Fatia 2).

Transição ``aprovado → entregue``. Uma vez entregue, o adiantamento
torna-se terminal — não pode mais ser cancelado (``AdiantamentoNaoCancelavel``).

Não publica eventos — a view faz isso dentro do ``transaction.atomic``.

Refs: D-CT-7; US-CT-008; INV-CT-ADIAN-001.
"""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID

from src.domain.caixa_tecnico.entities import Adiantamento
from src.domain.caixa_tecnico.enums import EstadoAdiantamento
from src.domain.caixa_tecnico.transicoes_adiantamento import (
    validar_transicao as validar_transicao_adiantamento,
)
from src.infrastructure.caixa_tecnico.repositories import AdiantamentoRepository


@dataclass
class EntregarAdiantamentoInput:
    """Parâmetros de entrada para registro de entrega de adiantamento (US-CT-008)."""

    tenant_id: UUID
    adiantamento_id: UUID
    entregue_por_id: UUID


class EntregarAdiantamentoUseCase:
    """Registra a entrega do adiantamento ao técnico.

    Dependências injetadas via construtor (hexagonal — ADR-0007).
    """

    def __init__(self, adiantamento_repo: AdiantamentoRepository) -> None:
        self._adiantamento_repo = adiantamento_repo

    def executar(self, inp: EntregarAdiantamentoInput) -> Adiantamento:
        """Executa o registro de entrega do adiantamento.

        Fluxo:
        1. Carrega o adiantamento existente.
        2. Valida transição de estado: deve estar em ``aprovado``.
        3. Atualiza para ``entregue`` com entregador e timestamp.

        Returns:
            Adiantamento atualizado no estado ``entregue`` (terminal).

        Raises:
            ValueError: adiantamento não encontrado.
            TransicaoInvalida: adiantamento não está em ``aprovado`` (422).
        """
        # 1. Carrega adiantamento
        adiantamento = self._adiantamento_repo.obter_por_id(inp.tenant_id, inp.adiantamento_id)
        if adiantamento is None:
            raise ValueError("adiantamento não encontrado")

        # 2. Valida transição (aprovado → entregue)
        validar_transicao_adiantamento(de=adiantamento.estado, para=EstadoAdiantamento.ENTREGUE)

        # 3. Atualiza estado (frozen → dataclasses.replace)
        adiantamento_atualizado = dataclasses.replace(
            adiantamento,
            estado=EstadoAdiantamento.ENTREGUE,
            entregue_em=datetime.now(UTC),
            entregue_por_id=inp.entregue_por_id,
        )

        # 4. Persiste
        self._adiantamento_repo.atualizar(inp.tenant_id, adiantamento_atualizado)

        return adiantamento_atualizado
