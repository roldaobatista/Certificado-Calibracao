"""Use case: recusa de adiantamento pelo gestor (US-CT-006 / Fatia 2).

Transição ``solicitado → recusado``. O motivo de recusa deve ter no mínimo
30 caracteres para garantir clareza ao técnico.

Não publica eventos — a view faz isso dentro do ``transaction.atomic``.

Refs: D-CT-7; US-CT-006.
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
class RecusarAdiantamentoInput:
    """Parâmetros de entrada para recusa de adiantamento (US-CT-006).

    ``motivo`` deve ter no mínimo 30 caracteres.
    """

    tenant_id: UUID
    adiantamento_id: UUID
    motivo: str
    recusado_por_id: UUID


class RecusarAdiantamentoUseCase:
    """Recusa um adiantamento solicitado com motivo obrigatório.

    Dependências injetadas via construtor (hexagonal — ADR-0007).
    """

    def __init__(self, adiantamento_repo: AdiantamentoRepository) -> None:
        self._adiantamento_repo = adiantamento_repo

    def executar(self, inp: RecusarAdiantamentoInput) -> Adiantamento:
        """Executa a recusa do adiantamento.

        Fluxo:
        1. Carrega o adiantamento existente.
        2. Valida comprimento mínimo do motivo (≥30 chars).
        3. Valida transição de estado: deve estar em ``solicitado``.
        4. Atualiza para ``recusado`` com motivo e timestamp.

        Returns:
            Adiantamento atualizado no estado ``recusado``.

        Raises:
            ValueError: adiantamento não encontrado ou motivo muito curto.
            TransicaoInvalida: adiantamento não está em ``solicitado`` (422).
        """
        # 1. Carrega adiantamento
        adiantamento = self._adiantamento_repo.obter_por_id(inp.tenant_id, inp.adiantamento_id)
        if adiantamento is None:
            raise ValueError("adiantamento não encontrado")

        # 2. Valida motivo
        if len(inp.motivo) < 30:
            raise ValueError("motivo deve ter no mínimo 30 caracteres")

        # 3. Valida transição (solicitado → recusado)
        validar_transicao_adiantamento(de=adiantamento.estado, para=EstadoAdiantamento.RECUSADO)

        # 4. Atualiza estado (frozen → dataclasses.replace)
        adiantamento_atualizado = dataclasses.replace(
            adiantamento,
            estado=EstadoAdiantamento.RECUSADO,
            recusado_em=datetime.now(UTC),
            motivo_recusa=inp.motivo,
        )

        # 5. Persiste
        self._adiantamento_repo.atualizar(inp.tenant_id, adiantamento_atualizado)

        return adiantamento_atualizado
