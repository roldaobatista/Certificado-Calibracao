"""Use case: aprovação de adiantamento pelo gestor (US-CT-005 / Fatia 2).

Transição ``solicitado → aprovado``. Verifica alçada de aprovação
configurada na política do tenant (D-CT-9 / D-CT-7).

Não publica eventos — a view faz isso dentro do ``transaction.atomic``.

Refs: D-CT-7/9; US-CT-005.
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
from src.infrastructure.caixa_tecnico.repositories import (
    AdiantamentoRepository,
    PoliticaRepository,
)


@dataclass
class AprovarAdiantamentoInput:
    """Parâmetros de entrada para aprovação de adiantamento (US-CT-005).

    ``perfil`` é usado para verificação de alçada por papel (Wave B).
    Em Wave A, a alçada usa a chave ``"default"`` da política.
    """

    tenant_id: UUID
    adiantamento_id: UUID
    aprovado_por_id: UUID
    perfil: str | None = None


class AprovarAdiantamentoUseCase:
    """Aprova um adiantamento solicitado, verificando alçada configurada.

    Dependências injetadas via construtor (hexagonal — ADR-0007).
    """

    def __init__(
        self,
        adiantamento_repo: AdiantamentoRepository,
        politica_repo: PoliticaRepository,
    ) -> None:
        self._adiantamento_repo = adiantamento_repo
        self._politica_repo = politica_repo

    def executar(self, inp: AprovarAdiantamentoInput) -> Adiantamento:
        """Executa a aprovação do adiantamento.

        Fluxo:
        1. Carrega o adiantamento existente.
        2. Valida transição de estado: deve estar em ``solicitado``.
        3. Verifica alçada de aprovação contra política do tenant.
        4. Atualiza para ``aprovado`` com aprovador e timestamp.

        Returns:
            Adiantamento atualizado no estado ``aprovado``.

        Raises:
            ValueError: adiantamento não encontrado ou valor acima da alçada.
            TransicaoInvalida: adiantamento não está em ``solicitado`` (422).
        """
        # 1. Carrega adiantamento
        adiantamento = self._adiantamento_repo.obter_por_id(inp.tenant_id, inp.adiantamento_id)
        if adiantamento is None:
            raise ValueError("adiantamento não encontrado")

        # 2. Valida transição (solicitado → aprovado)
        validar_transicao_adiantamento(de=adiantamento.estado, para=EstadoAdiantamento.APROVADO)

        # 3. Verifica alçada server-side (D-CT-7 / D-CT-9)
        politica = self._politica_repo.obter_por_tenant(inp.tenant_id)
        if politica is not None and politica.alcada_aprovacao is not None:
            alcada = politica.alcada_aprovacao.get("default")
            if alcada is not None and adiantamento.valor.centavos > alcada:
                valor_reais = adiantamento.valor.centavos / 100
                raise ValueError(f"valor R${valor_reais:.2f} excede alçada configurada")

        # 4. Atualiza estado (frozen → dataclasses.replace)
        adiantamento_atualizado = dataclasses.replace(
            adiantamento,
            estado=EstadoAdiantamento.APROVADO,
            aprovado_em=datetime.now(UTC),
            aprovado_por_id=inp.aprovado_por_id,
        )

        # 5. Persiste
        self._adiantamento_repo.atualizar(inp.tenant_id, adiantamento_atualizado)

        return adiantamento_atualizado
