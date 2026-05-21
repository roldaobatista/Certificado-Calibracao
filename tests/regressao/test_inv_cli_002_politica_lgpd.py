"""INV-CLI-002 — política LGPD num único lar.

Spec Marco 1 §3 item 9 + §1: suíte anti-regressão `tests/regressao/inv_cli_*.py`
com happy + unhappy.

INV-CLI-002 (REGRAS-INEGOCIAVEIS): decisão sobre base legal aplicável
pós-revogação/incidente vem de `politicas_lgpd.base_legal_aplicavel_pos_revogacao`,
não duplicada em view/serializer/use case. Hook `lgpd-policy-unica.sh`
bloqueia hardcode em pre-commit.
"""

from __future__ import annotations

from src.infrastructure.audit.politicas_lgpd import (
    base_legal_aplicavel_pos_revogacao,
)


def test_inv_cli_002_happy_emissao_nf_subsiste_pos_revogacao():
    """Happy — após revogação, finalidade NF subsiste via base `OBRIG_LEGAL`."""
    # Após revogar consentimento, OBRIG_LEGAL continua disponível.
    aplicavel = base_legal_aplicavel_pos_revogacao(
        finalidade="emissao_nf",
        bases_disponiveis={"OBRIG_LEGAL"},
    )
    assert aplicavel is True


def test_inv_cli_002_unhappy_marketing_so_com_consentimento_recusado_pos_revogacao():
    """Unhappy — marketing só aceita CONSENTIMENTO; pós-revogação, NÃO aplica."""
    aplicavel = base_legal_aplicavel_pos_revogacao(
        finalidade="comunicacao_marketing",
        bases_disponiveis={"CONSENTIMENTO"},  # única base; revogação remove
    )
    assert aplicavel is False


def test_inv_cli_002_unhappy_finalidade_fora_do_mapa_retorna_false():
    """Unhappy — finalidade fora do mapa: política não autoriza tratamento."""
    aplicavel = base_legal_aplicavel_pos_revogacao(
        finalidade="finalidade_inexistente_no_mapa",
        bases_disponiveis={"EXECUCAO_CONTRATO", "OBRIG_LEGAL"},
    )
    assert aplicavel is False
