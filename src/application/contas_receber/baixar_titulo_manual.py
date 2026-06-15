"""Use case `baixar_titulo_manual` — US-CR-003 baixa manual (T-CR-032).

Fluxo (D-CR-3/4):
  1. Carrega título + pagamentos já confirmados do repo.
  2. Valida que não está pago nem cancelado (estado terminal).
  3. Calcula `valor_atualizado` via `calcular_valor_atualizado(titulo, pagamentos,
     data_pagamento, regra)` sobre o SALDO (R12 / INV-026).
  4. Cria `Pagamento` (origem=manual, INSERT-only WORM) com snapshot M-FIN-002.
  5. Recalcula saldo pós-pagamento para decidir novo estado:
     - saldo zero → PAGO + data_baixa = data_pagamento.
     - saldo positivo → PARCIALMENTE_PAGO.
  6. Valida transição via `validar_transicao` (D-CR-3).
  7. Persiste pagamento + atualiza título.

NÃO publica evento — view publica `contas_receber.pago` no mesmo `atomic`.
`RegraJurosMulta` padrão (1% a.m. + 2% multa) se não informada (spec D-CR-4).
"""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from uuid import UUID, uuid4

from src.domain.contas_receber.entities import Pagamento, Titulo
from src.domain.contas_receber.enums import EstadoTitulo, OrigemPagamento
from src.domain.contas_receber.erros import TituloNaoEncontrado, TransicaoProibida
from src.domain.contas_receber.juros import calcular_valor_atualizado
from src.domain.contas_receber.portas import TituloRepository
from src.domain.contas_receber.transicoes import validar_transicao
from src.domain.contas_receber.value_objects import RegraJurosMulta
from src.domain.shared.value_objects import Dinheiro


@dataclass(frozen=True, slots=True)
class BaixarTituloManualInput:
    """Payload de baixa manual.

    `valor_centavos` — valor efetivamente recebido (pode ser parcial).
    `data_pagamento` — data da baixa (geralmente hoje).
    `regra` — regra de juros/multa para snapshot; usa padrão se None.
    """

    tenant_id: UUID
    titulo_id: UUID
    valor_centavos: int
    data_pagamento: date
    regra: RegraJurosMulta = field(default_factory=RegraJurosMulta)
    comprovante_url: str | None = None

    def __post_init__(self) -> None:
        if self.valor_centavos <= 0:
            raise ValueError("baixar_titulo_manual: valor_centavos deve ser > 0.")


@dataclass(frozen=True, slots=True)
class BaixarTituloManualOutput:
    titulo: Titulo
    pagamento: Pagamento
    novo_estado: EstadoTitulo


def executar(
    inp: BaixarTituloManualInput,
    *,
    repo: TituloRepository,
) -> BaixarTituloManualOutput:
    """Registra baixa manual. NÃO publica evento (responsabilidade da view)."""
    # 1. Carrega título e pagamentos existentes
    titulo = repo.obter_por_id(tenant_id=inp.tenant_id, titulo_id=inp.titulo_id)
    if titulo is None:
        raise TituloNaoEncontrado(f"Título {inp.titulo_id} não encontrado.")

    pagamentos = repo.listar_pagamentos(tenant_id=inp.tenant_id, titulo_id=inp.titulo_id)

    # 2. Estado terminal não aceita baixa
    if titulo.estado in (EstadoTitulo.PAGO, EstadoTitulo.CANCELADO):
        raise TransicaoProibida(
            f"Título {inp.titulo_id} está em estado terminal: {titulo.estado.value!r}."
        )

    # 3. Calcula valor atualizado (snapshot M-FIN-002 — juros/multa sobre saldo)
    valor_atualizado = calcular_valor_atualizado(titulo, pagamentos, inp.data_pagamento, inp.regra)

    # 4. Cria Pagamento INSERT-only (WORM — D-CR-8)
    agora = datetime.now(UTC)
    pagamento = Pagamento(
        pagamento_id=uuid4(),
        titulo_id=inp.titulo_id,
        valor=Dinheiro(centavos=inp.valor_centavos, moeda="BRL"),
        data=inp.data_pagamento,
        origem=OrigemPagamento.MANUAL,
        valor_atualizado_snapshot_em_pagamento=valor_atualizado,
        criado_em=agora,
        comprovante_url=inp.comprovante_url,
    )
    repo.salvar_pagamento(tenant_id=inp.tenant_id, pagamento=pagamento)

    # 5. Recalcula saldo pós-pagamento
    total_pago = sum(p.valor.centavos for p in pagamentos) + inp.valor_centavos
    saldo_restante = titulo.valor_original.centavos - total_pago

    if saldo_restante <= 0:
        novo_estado = EstadoTitulo.PAGO
        data_baixa = inp.data_pagamento
    else:
        novo_estado = EstadoTitulo.PARCIALMENTE_PAGO
        data_baixa = None

    # 6. Valida transição (D-CR-3)
    validar_transicao(titulo.estado, novo_estado)

    # 7. Atualiza título com novo estado e data_baixa
    titulo_atualizado = dataclasses.replace(titulo, estado=novo_estado, data_baixa=data_baixa)
    repo.atualizar_titulo(tenant_id=inp.tenant_id, titulo=titulo_atualizado)

    return BaixarTituloManualOutput(
        titulo=titulo_atualizado,
        pagamento=pagamento,
        novo_estado=novo_estado,
    )
