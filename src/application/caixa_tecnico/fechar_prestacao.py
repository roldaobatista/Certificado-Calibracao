"""Use case: fechamento da prestação de contas do técnico (US-CT-009 / Fatia 2).

Calcula saldo do período (adiantamentos entregues vs despesas validadas),
determina a direção e persiste a prestação de contas como registro WORM conceitual.

O advisory lock ``pg_advisory_xact_lock`` deve ser feito na VIEW antes de
chamar este use case — não é responsabilidade do use case.

Não publica eventos — a view faz isso dentro do ``transaction.atomic``.

Refs: D-CT-8; US-CT-009; INV-CT-PRESTACAO-001; INV-CT-SALDO-001.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime
from uuid import UUID, uuid4

from src.domain.caixa_tecnico.entities import PrestacaoContas
from src.domain.caixa_tecnico.enums import EstadoAdiantamento, EstadoDespesa
from src.domain.caixa_tecnico.erros import PeriodoPrestacaoFechado
from src.domain.caixa_tecnico.regras.calcular_saldo import calcular_saldo
from src.domain.caixa_tecnico.value_objects import Periodo
from src.infrastructure.caixa_tecnico.repositories import (
    AdiantamentoRepository,
    CaixaTecnicoRepository,
    DespesaRepository,
    PrestacaoRepository,
)


@dataclass
class FecharPrestacaoInput:
    """Parâmetros de entrada para fechamento de prestação de contas (US-CT-009)."""

    tenant_id: UUID
    caixa_id: UUID
    periodo_de: date
    periodo_ate: date
    observacoes: str | None = None


class FecharPrestacaoUseCase:
    """Fecha a prestação de contas de um período do técnico.

    Dependências injetadas via construtor (hexagonal — ADR-0007).
    """

    def __init__(
        self,
        caixa_repo: CaixaTecnicoRepository,
        adiantamento_repo: AdiantamentoRepository,
        despesa_repo: DespesaRepository,
        prestacao_repo: PrestacaoRepository,
    ) -> None:
        self._caixa_repo = caixa_repo
        self._adiantamento_repo = adiantamento_repo
        self._despesa_repo = despesa_repo
        self._prestacao_repo = prestacao_repo

    def executar(self, inp: FecharPrestacaoInput) -> PrestacaoContas:
        """Executa o fechamento da prestação de contas.

        Fluxo:
        1. Carrega e valida caixa.
        2. Valida o intervalo do período (Periodo levanta ValueError se inválido).
        3. Verifica duplicata — prestação já existente no período bloqueia.
        4. Carrega adiantamentos ENTREGUES no período.
        5. Carrega despesas VALIDADAS no período.
        6. Calcula saldo e direção com ``calcular_saldo``.
        7. Persiste e retorna.

        Returns:
            PrestacaoContas fechada com saldo calculado.

        Raises:
            ValueError: caixa não encontrado ou período inválido.
            PeriodoPrestacaoFechado: já existe prestação para o período (422).
        """
        # 1. Carrega caixa
        caixa = self._caixa_repo.obter_por_id(inp.tenant_id, inp.caixa_id)
        if caixa is None:
            raise ValueError("caixa não encontrado")

        # 2. Valida período — Periodo.__post_init__ lança ValueError se de >= ate
        periodo = Periodo(de=inp.periodo_de, ate=inp.periodo_ate)

        # 3. Verifica duplicata de prestação no período
        if self._prestacao_repo.existe_prestacao_no_periodo(
            inp.tenant_id, inp.caixa_id, inp.periodo_de, inp.periodo_ate
        ):
            raise PeriodoPrestacaoFechado("já existe prestação para este período")

        # 4. Adiantamentos ENTREGUES no período
        todos_adiantamentos = self._adiantamento_repo.listar_por_caixa(
            inp.tenant_id, inp.caixa_id, estado=EstadoAdiantamento.ENTREGUE.value
        )
        adiantamentos_entregues = [
            a
            for a in todos_adiantamentos
            if a.entregue_em is not None and periodo.contem(a.entregue_em.date())
        ]

        # 5. Despesas VALIDADAS no período
        todas_despesas = self._despesa_repo.listar_por_caixa(
            inp.tenant_id, inp.caixa_id, estado=EstadoDespesa.VALIDADA.value
        )
        despesas_validadas_periodo = [d for d in todas_despesas if periodo.contem(d.data)]

        # 6. Calcula saldo
        resultado = calcular_saldo(adiantamentos_entregues, despesas_validadas_periodo)

        # 7. Persiste prestação
        fechada_em = datetime.now(UTC)
        prestacao = PrestacaoContas(
            prestacao_id=uuid4(),
            tenant_id=inp.tenant_id,
            caixa_id=inp.caixa_id,
            tecnico_referencia=caixa.tecnico_referencia,
            periodo=periodo,
            total_adiantado=resultado.total_adiantado,
            total_despesas_validadas=resultado.total_despesas,
            saldo_final=resultado.saldo_final,
            direcao=resultado.direcao,
            fechada_em=fechada_em,
            criado_em=fechada_em,
            observacoes=inp.observacoes,
        )

        self._prestacao_repo.salvar_nova(prestacao)

        return prestacao
