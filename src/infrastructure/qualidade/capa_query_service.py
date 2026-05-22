"""Porta `CAPAQueryService` — link de nao-conformidade (ISO 17025 cl. 8.7).

Stub Marco 2: consumidores que querem saber se um recebimento ou
equipamento tem CAPA aberta NAO importam tabela CAPA direto — usam esta
porta. Wave A constroi o modulo `qualidade` completo (RegistroCAPA +
fluxo de tratamento + auditoria interna) sem quebrar consumidores
(ADR-0007).

API minima Marco 2:
- `capa_aberta_para_recebimento(recebimento_id) -> bool`
- `capa_aberta_para_equipamento(equipamento_id) -> bool`

Marco 2 retorna sempre `False` (modulo CAPA nao existe ainda). Wave A
substitui implementacao consultando `qualidade.RegistroCAPA`.

Consumidor primario: T-EQP-050 (transicoes status_fluxo_lab para
`nao_conformidade_*` poderao no futuro exigir CAPA aberta) e Marco 2
P-EQP-R3 (AC-EQP-006-7b — link recebimento -> RegistroCAPA quando
condicoes ambientais fora da faixa).
"""

from __future__ import annotations

from uuid import UUID


def capa_aberta_para_recebimento(recebimento_id: UUID) -> bool:
    """True se existe pelo menos 1 CAPA aberta vinculada ao recebimento.

    Marco 2 (stub): sempre retorna `False`. Wave A consulta
    `qualidade.RegistroCAPA.objects.filter(
        recebimento_id=recebimento_id, status='aberta'
    ).exists()`.
    """
    del recebimento_id  # nao usado no stub
    return False


def capa_aberta_para_equipamento(equipamento_id: UUID) -> bool:
    """True se existe pelo menos 1 CAPA aberta vinculada ao equipamento.

    Marco 2 (stub): sempre retorna `False`. Wave A consulta
    `qualidade.RegistroCAPA.objects.filter(
        equipamento_id=equipamento_id, status='aberta'
    ).exists()`.
    """
    del equipamento_id  # nao usado no stub
    return False
