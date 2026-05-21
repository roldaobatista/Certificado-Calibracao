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


# =============================================================
# Mapa finalidade × bases legais aceitas (BLOQ-A2 advogado).
#
# Quando o titular revoga consentimento (T-CLI-115 / LGPD art. 8º §5º),
# operacoes baseadas SOMENTE em CONSENTIMENTO param. Operacoes com
# outras bases legais subsistem se a base estiver disponivel.
#
# A spec INV-CLI-002 (politica LGPD canonica) cita as 5 bases em
# `lgpd.py::BASES_LEGAIS`:
#   - CONSENTIMENTO       (art. 7 I)
#   - EXECUCAO_CONTRATO   (art. 7 V)
#   - OBRIG_LEGAL         (art. 7 II)
#   - LEGITIMO_INTERESSE  (art. 7 IX)
#   - PROTECAO_CREDITO    (art. 7 X)
# =============================================================
MAPA_FINALIDADE_BASE_LEGAL_ACEITA: Final[dict[str, frozenset[str]]] = {
    # Cadastro basico do cliente: contratual ou consentimento
    "cadastro_basico": frozenset({"EXECUCAO_CONTRATO", "CONSENTIMENTO"}),
    # NF/fiscal: obrigacao legal (CTN 173 + Receita)
    "emissao_nf": frozenset({"OBRIG_LEGAL", "EXECUCAO_CONTRATO"}),
    # Certificado ISO 17025: obrigacao regulatoria (Lei 9.933/99 INMETRO)
    "emissao_certificado_iso": frozenset({"OBRIG_LEGAL"}),
    # Comunicacao marketing/promocional: SO consentimento explicito
    "comunicacao_marketing": frozenset({"CONSENTIMENTO"}),
    # Audit trail: obrigacao legal de prestacao de contas + leg. interesse
    "audit_trail": frozenset({"OBRIG_LEGAL", "LEGITIMO_INTERESSE"}),
    # Cobranca de inadimplencia: contrato + protecao de credito
    "cobranca_inadimplencia": frozenset({"EXECUCAO_CONTRATO", "PROTECAO_CREDITO"}),
    # Operacao interna (cadastro/edicao/export por staff)
    "operacao_interna": frozenset({"EXECUCAO_CONTRATO", "LEGITIMO_INTERESSE"}),
}


def base_legal_aplicavel_pos_revogacao(finalidade: str, bases_disponiveis: set[str]) -> bool:
    """T-CLI-115 (BLOQ-A2 / A4 advogado) — base legal aplicavel pos revogacao.

    True se ha ao menos uma base legal aceita pra `finalidade` quando o
    titular revogou consentimento (CONSENTIMENTO removido das disponiveis).

    Exemplo:
    - `emissao_nf` com `bases_disponiveis={OBRIG_LEGAL}` → True (NF continua
      por obrigacao legal mesmo apos revogacao).
    - `comunicacao_marketing` com `bases_disponiveis={CONSENTIMENTO}` →
      False apos revogacao (so consentimento aceita).
    """
    aceitas = MAPA_FINALIDADE_BASE_LEGAL_ACEITA.get(finalidade, frozenset())
    return bool(aceitas & (bases_disponiveis - {"CONSENTIMENTO"}))
