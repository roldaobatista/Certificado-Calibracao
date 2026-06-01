"""Erros fail-closed da reconciliação de cobertura do certificado (M8).

Distintos das CLASSIFICAÇÕES de ponto (`ClassificacaoPonto`): estes ABORTAM a
reconciliação (bug de dados ou pré-condição não satisfeita) — nunca classificam.
O atributo `reason` é o código estável que a aplicação mapeia para 4xx e que o
hook `cert-reconcilia-fail-closed` (Fatia 3) protege.
"""

from __future__ import annotations


class ReconciliacaoCertificadoError(Exception):
    """Base fail-closed da reconciliação (mapeada a 4xx pela aplicação)."""

    reason = "reconciliacao_erro"


class OrcamentoPontoAmbiguoError(ReconciliacaoCertificadoError):
    """2+ `OrcamentoPorPonto` para o MESMO `ponto_calibracao` (C-01 /
    INV-CER-RECONCILIA-005). O lookup de `U(ponto)` é 1:1; duplicidade poderia
    mascarar dupla contagem da incerteza — fail-closed."""

    reason = "ORCAMENTO_PONTO_AMBIGUO"


class SemOrcamentoPontoError(ReconciliacaoCertificadoError):
    """Ponto medido sem `OrcamentoPorPonto` correspondente (pré-condição da
    emissão — plan §2 passo 2). Sem `U(ponto)` não há o que reconciliar →
    fail-closed (não se emite ponto sem incerteza)."""

    reason = "SEM_ORCAMENTO"
