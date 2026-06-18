"""Regra de negócio pura: cálculo de valor por deslocamento (T-CT-013).

D-CT-9:
    valor_deslocamento = km_percorridos × tarifa_km

AC T-CT-013:
    valor_deslocamento(10, Dinheiro(150)) → Dinheiro(1500)

Função PURA — determinística, sem I/O, sem Django.
"""

from __future__ import annotations

from src.domain.shared.value_objects import Dinheiro


def valor_deslocamento(km_percorridos: int, tarifa_km: Dinheiro) -> Dinheiro:
    """Calcula o valor da despesa de deslocamento (categoria=deslocamento).

    Multiplicação inteira: ``km_percorridos × tarifa_km.centavos``.
    Zero km ou zero tarifa retorna ``Dinheiro(0)`` (sem erro — borda legítima
    em teste de configuração ainda não preenchida).

    Args:
        km_percorridos: quilômetros percorridos (int ≥ 0).
        tarifa_km:      valor por km em centavos (``Dinheiro``).

    Returns:
        ``Dinheiro`` com centavos = ``km_percorridos × tarifa_km.centavos``.

    Raises:
        ValueError: se ``km_percorridos`` for negativo.
    """
    if km_percorridos < 0:
        raise ValueError(f"km_percorridos deve ser ≥ 0, recebido: {km_percorridos}")
    return tarifa_km * km_percorridos
