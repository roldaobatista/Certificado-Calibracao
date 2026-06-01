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


class FaixaDeclaradaAusenteError(ReconciliacaoCertificadoError):
    """Calibração APROVADA sem `faixa_calibrada_declarada`/`grandeza_calibrada`
    (ADR-0076). Sem a faixa declarada não se pode aferir `pontos ⊆ declarada`
    → fail-closed (fecha GATE-CAL-EMISSAO-RECONCILIA-FAIXA com dado de origem)."""

    reason = "FAIXA_DECLARADA_AUSENTE"


class CertificadoError(Exception):
    """Base dos erros de ciclo de vida/emissão do certificado (≠ reconciliação)."""

    reason = "certificado_erro"


class TransicaoCertificadoInvalidaError(CertificadoError):
    """Transição de `EstadoCertificado` não permitida pela máquina de estados."""

    reason = "TRANSICAO_CERTIFICADO_INVALIDA"


class MotivoReemissaoInsuficienteError(CertificadoError):
    """Reemissão (US-CER-004) exige motivo com ≥ 50 chars."""

    reason = "MOTIVO_REEMISSAO_INSUFICIENTE"


class ReconciliacaoPendenteDecisaoRTError(CertificadoError):
    """Perfil A com ponto não-RBC SEM decisão do RT → bloqueia emissão (422), sem
    persistir nada (NC-03 / máquina de estados plan §3)."""

    reason = "RECONCILIACAO_PENDENTE_DECISAO_RT"


class RessalvaNaoRbcObrigatoriaError(CertificadoError):
    """Decisão `EMITIR_NAO_RBC_NO_PONTO` sem `ressalva_nao_rbc` (C-03 / cl. 8.1.3
    / ADR-0075) — anti uso indevido de acreditação (L6 invertido)."""

    reason = "RESSALVA_NAO_RBC_OBRIGATORIA"


class CalibracaoNaoAprovadaError(CertificadoError):
    """Só calibração `APROVADA` (2ª conferência ADR-0026) pode emitir certificado
    (INV-CER-EMISSAO-001). Estado anterior → 422."""

    reason = "CALIBRACAO_NAO_APROVADA"


class CategoriaIncoerenteError(CertificadoError):
    """`categoria_motivo` incoerente com a `classificacao` do ponto (C-02 /
    cl. 7.10.1) — ex.: PONTO_FORA_FAIXA_DECLARADA para ponto que está dentro."""

    reason = "CATEGORIA_MOTIVO_INCOERENTE"


class JustificativaInsuficienteError(CertificadoError):
    """Decisão do RT exige justificativa objetiva (cl. 7.10.1) — mín. 20 chars."""

    reason = "JUSTIFICATIVA_INSUFICIENTE"


class EmissaoAbortadaPeloRTError(CertificadoError):
    """Decisão `ABORTAR` do RT em algum ponto → emissão não prossegue (bug grave,
    ex.: orçamento de incerteza errado)."""

    reason = "EMISSAO_ABORTADA_PELO_RT"


class CertificadoJaEmitidoError(CertificadoError):
    """Idempotência: já existe certificado para (tenant, calibração, versão)
    (INV-CER-EMISSAO-001) — evita dupla emissão da mesma calibração."""

    reason = "CERTIFICADO_JA_EMITIDO"


class PadraoCalibracaoVencidaError(CertificadoError):
    """Perfil A: algum padrão usado tinha a calibração VENCIDA na data de emissão
    (cl. 6.5 / NC-07 / INV-CER-PADRAO-VIG-001) — não se emite RBC apoiado em padrão
    sem rastreabilidade vigente. Vigência ausente no snapshot é fail-open lazy
    (campo opcional até o wiring com M5 `padroes` — GATE-CER-PADRAO-VIG-SNAPSHOT)."""

    reason = "PADRAO_CALIBRACAO_VENCIDA"


class ReemissaoConflitanteError(CertificadoError):
    """Reemissão (US-CER-004): o CAS `marcar_substituida(revision_anterior)` falhou
    — corrida ou o certificado anterior já foi substituído/revogado. Caller → 409
    (a transação atômica reverte o INSERT da nova versão)."""

    reason = "REEMISSAO_CONFLITANTE"
