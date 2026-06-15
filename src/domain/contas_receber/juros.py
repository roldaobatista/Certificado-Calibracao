"""Cálculo de juros/multa/desconto do domínio contas-receber (Fatia 1a — T-CR-013).

D-CR-4 — cálculo NA LEITURA (INV-026, não persiste valor inflado):
  - Função pura `calcular_valor_atualizado(titulo, pagamentos, data, regra) -> Dinheiro`.
  - Incide sobre o SALDO (`valor_original - sum(pagamentos)`) — NÃO sobre `valor_original`
    (R12 / TL-CR-10).
  - Juros: 1% a.m. proporcional (dias em atraso / 30).
  - Multa: 2% one-shot a partir do D+1 de vencimento.
  - Remove desconto pontualidade após vencimento.

Sem I/O, sem Django, sem banco.
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import date
from decimal import ROUND_HALF_UP, Decimal

from src.domain.shared.value_objects import Dinheiro

from .entities import Pagamento, Titulo
from .value_objects import RegraJurosMulta


def calcular_valor_atualizado(
    titulo: Titulo,
    pagamentos: Sequence[Pagamento],
    data: date,
    regra: RegraJurosMulta,
) -> Dinheiro:
    """Valor atualizado com juros/multa sobre o SALDO em aberto (D-CR-4 / R12).

    Parâmetros:
        titulo    — título com `valor_original` e `data_vencimento`.
        pagamentos — lista de pagamentos já confirmados (INSERT-only, imutáveis).
        data      — data de referência para o cálculo (hoje ou data do pagamento).
        regra     — `RegraJurosMulta` com `juros_ao_mes_pct` e `multa_pct`.

    Retorna `Dinheiro` em centavos (BRL) com o saldo corrigido.

    Regras (spec D-CR-4):
      1. Saldo = `valor_original.centavos - sum(p.valor.centavos for p in pagamentos)`.
      2. Se `data <= data_vencimento`: devolve o saldo (sem correção).
         Se `titulo.desconto_pontualidade_pct` estava ativo, era sobre `valor_original`
         — mas após vencimento ele é removido (aqui já não se aplica).
      3. Dias em atraso = (data - data_vencimento).days  [≥1].
      4. Multa one-shot = saldo × multa_pct / 100  (D+1 em diante).
      5. Juros proporcional = saldo × (juros_ao_mes_pct / 100) × (dias / 30).
      6. Valor atualizado = saldo + multa + juros  (arredondado HALF_UP para centavos).
    """
    # 1. Saldo em aberto
    total_pago = sum(p.valor.centavos for p in pagamentos)
    saldo_centavos = titulo.valor_original.centavos - total_pago

    if saldo_centavos <= 0:
        # Quitado: retorna zero
        return Dinheiro(0, titulo.valor_original.moeda)

    # 2. Sem atraso: devolve saldo puro
    if data <= titulo.data_vencimento:
        return Dinheiro(saldo_centavos, titulo.valor_original.moeda)

    # 3. Dias em atraso
    dias_atraso = (data - titulo.data_vencimento).days  # ≥1

    saldo_d = Decimal(saldo_centavos)

    # 4. Multa one-shot (a partir do D+1)
    multa_d = (saldo_d * Decimal(str(regra.multa_pct)) / Decimal("100")).quantize(
        Decimal("1"), rounding=ROUND_HALF_UP
    )

    # 5. Juros proporcional ao mês (1% a.m. = por default)
    juros_d = (
        saldo_d
        * (Decimal(str(regra.juros_ao_mes_pct)) / Decimal("100"))
        * (Decimal(dias_atraso) / Decimal("30"))
    ).quantize(Decimal("1"), rounding=ROUND_HALF_UP)

    # 6. Total atualizado
    total_centavos = int(saldo_d + multa_d + juros_d)
    return Dinheiro(total_centavos, titulo.valor_original.moeda)
