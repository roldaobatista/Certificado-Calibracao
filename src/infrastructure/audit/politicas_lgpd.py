"""Políticas LGPD declarativas — parte de `INV-CLI-002` (SANEA-07).

Por enquanto traz apenas `POLITICA_BUS_OUTBOX` (BLOQ-A6 + SUG-3 do
review advogado). Wave A consolida com `lgpd_policy.py` do domínio
(`src/domain/comercial/clientes/lgpd_policy.py`) na entrega do
agregado `Cliente` (US-CLI-001).

Por que aqui (e não no domain): `bus_outbox` é infraestrutura — manter
a política co-localizada com a fila evita dependência reversa
infrastructure -> domain enquanto o domain ainda não tem `lgpd_policy`.
"""

from __future__ import annotations

from typing import Final, TypedDict


class PoliticaBusOutboxDict(TypedDict):
    """Forma da declaração — TypedDict pra mypy validar evolução."""

    natureza: str
    base_legal_herdada: str
    prazo_retencao_pos_processado_dias: int
    cascata_offboarding_tenant: bool
    afetado_por_art18_eliminacao_titular_individual: bool
    afetado_por_art18_acesso_portabilidade: bool
    fonte_da_verdade_para_art18: str
    vetor_pii_acoes_mitigadas: list[str]


# Decisão consolidada (review advogado 2026-05-20):
# - `bus_outbox` é fila intermediária ≤ 7 dias pós-processado.
# - NÃO é evidência regulatória — fonte da verdade é a cadeia F-A.
# - Cascata via `tenant_id` aplica APENAS em offboarding (cenário C da
#   `retencao-matriz.md`). Pedido de titular individual (cenário B) NÃO
#   toca `bus_outbox` — minimização cumprida pelo cleanup natural 7d.
# - FORA do escopo art. 18 II (acesso) e art. 18 V (portabilidade) —
#   tratamento intermediário, não-durável; F-A responde aos direitos.
POLITICA_BUS_OUTBOX: Final[PoliticaBusOutboxDict] = {
    "natureza": "fila intermediaria nao-evidencia regulatoria",
    "base_legal_herdada": "art. 7 V (execucao contrato) | art. 7 II (obrigacao legal)",
    "prazo_retencao_pos_processado_dias": 7,
    "cascata_offboarding_tenant": True,
    "afetado_por_art18_eliminacao_titular_individual": False,
    "afetado_por_art18_acesso_portabilidade": False,
    "fonte_da_verdade_para_art18": "cadeia_hash_f_a",
    "vetor_pii_acoes_mitigadas": [
        "envelope_jsonb (sanitizado em escrita)",
        "acao (CHECK constraint enum semantico)",
        "ultimo_erro (sanitizar_erro_para_outbox)",
        "causation_id (acesso restrito a dpo+sre Wave A)",
    ],
}
