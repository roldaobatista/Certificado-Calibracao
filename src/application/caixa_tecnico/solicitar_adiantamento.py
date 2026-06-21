"""Use case: solicitação de adiantamento pelo técnico (US-CT-001 / Fatia 2).

Cria um adiantamento no estado ``solicitado`` vinculado ao caixa do técnico.
A liberação (PIX/transferência) é manual em Wave A (automática em Wave B — ADR-0050).

Não publica eventos — a view faz isso dentro do ``transaction.atomic``.

Refs: D-CT-7; US-CT-001.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID, uuid4

from src.domain.caixa_tecnico.entities import Adiantamento
from src.domain.caixa_tecnico.enums import EstadoAdiantamento, MeioEntrega
from src.domain.caixa_tecnico.erros import CaixaTecnicoDesligado
from src.domain.shared.value_objects import Dinheiro
from src.infrastructure.caixa_tecnico.repositories import (
    AdiantamentoRepository,
    CaixaTecnicoRepository,
)


@dataclass
class SolicitarAdiantamentoInput:
    """Parâmetros de entrada para solicitação de adiantamento (US-CT-001)."""

    tenant_id: UUID
    caixa_id: UUID
    valor_centavos: int
    meio: MeioEntrega
    justificativa: str | None = None


class SolicitarAdiantamentoUseCase:
    """Registra a solicitação de adiantamento para um técnico.

    Dependências injetadas via construtor (hexagonal — ADR-0007).
    """

    def __init__(
        self,
        caixa_repo: CaixaTecnicoRepository,
        adiantamento_repo: AdiantamentoRepository,
    ) -> None:
        self._caixa_repo = caixa_repo
        self._adiantamento_repo = adiantamento_repo

    def executar(self, inp: SolicitarAdiantamentoInput) -> Adiantamento:
        """Executa a solicitação de adiantamento.

        Fluxo:
        1. Carrega e valida caixa (ativo e não desligado).
        2. Cria adiantamento no estado ``solicitado``.
        3. Persiste e retorna.

        Returns:
            Adiantamento criado no estado ``solicitado``.

        Raises:
            ValueError: caixa não encontrado.
            CaixaTecnicoDesligado: caixa desligado (409).
        """
        # 1. Carrega caixa
        caixa = self._caixa_repo.obter_por_id(inp.tenant_id, inp.caixa_id)
        if caixa is None:
            raise ValueError("caixa não encontrado")
        if caixa.esta_desligado:
            raise CaixaTecnicoDesligado(
                f"CaixaTecnico {inp.caixa_id} está desligado — solicitação de adiantamento bloqueada"
            )

        # 2. Cria adiantamento
        agora = datetime.now(UTC)
        adiantamento = Adiantamento(
            adiantamento_id=uuid4(),
            tenant_id=inp.tenant_id,
            caixa_id=inp.caixa_id,
            tecnico_referencia=caixa.tecnico_referencia,
            valor=Dinheiro(inp.valor_centavos),
            estado=EstadoAdiantamento.SOLICITADO,
            meio=inp.meio,
            solicitado_em=agora,
            criado_em=agora,
            revision=1,
            justificativa=inp.justificativa,
        )

        # 3. Persiste
        self._adiantamento_repo.salvar_novo(adiantamento)

        return adiantamento
