"""Enums fechados do domínio certificados (M8 Wave A).

`ClassificacaoPonto` nasce AQUI (Fatia 0, T-CER-010 parcial) porque o avaliador
puro `reconciliacao.reconciliar_pontos` classifica cada ponto — é dependência da
Fatia 0. A Fatia 1a ACRESCENTA neste mesmo arquivo os enums de ciclo de vida
(`EstadoCertificado`), decisão do RT (`DecisaoReconciliacaoRT`) e categoria de
exclusão (`CategoriaMotivoExclusao`). str-mixin → serialização JSON nativa (mesmo
padrão de escopos_cmc/enums.py). Domain NÃO importa Django (ADR-0007).
"""

from __future__ import annotations

from enum import Enum


class ClassificacaoPonto(str, Enum):
    """Classe metrológica de cada ponto reconciliado na emissão (plan §2).

    Resolvida por PRECEDÊNCIA FIXA `FORA_DECLARADA > SEM_CMC > U_MENOR_CMC >
    RBC_OK` (C-04 — replay determinístico cl. 7.11): um ponto pode falhar em
    mais de um critério; a classe é a de MAIOR precedência. Sem isso, dois
    certificados da mesma calibração classificariam o mesmo ponto diferente (NC
    de replay).

    - `RBC_OK`: dentro da faixa declarada E coberto por CMC E `U(ponto) ≥
      CMC(ponto)` (ILAC-P14 §5.5).
    - `FORA_DECLARADA`: ponto fora da `faixa_calibrada_declarada` — CGCRE não
      extrapola (ADR-0076). Furo de processo → decisão do RT (Fatia 2).
    - `SEM_CMC`: sem CMC no ponto. Perfil A = ponto fora do escopo RBC vigente
      (pendente decisão RT); B/C/D = caminho NORMAL (sem acreditação, todo ponto
      é não-RBC).
    - `U_MENOR_CMC`: `U(ponto) < CMC(ponto)` — incerteza reportada melhor que a
      capacidade acreditada. Bug de orçamento OU exclusão legítima → RT decide.
      (Na exclusão, mapeia para `CategoriaMotivoExclusao.U_MAIOR_QUE_CMC_BUG` —
      nomes de direção aparente oposta descrevem o MESMO fenômeno: CMC declarada
      otimista demais perante a U real.)
    - `EXCLUIDO`: removido do certificado por decisão WORM do RT (Fatia 2).
    """

    RBC_OK = "RBC_OK"
    FORA_DECLARADA = "FORA_DECLARADA"
    SEM_CMC = "SEM_CMC"
    U_MENOR_CMC = "U_MENOR_CMC"
    EXCLUIDO = "EXCLUIDO"

    @property
    def e_rbc(self) -> bool:
        """Único ponto que sai com selo RBC sem decisão do RT."""
        return self is ClassificacaoPonto.RBC_OK

    @property
    def problematico(self) -> bool:
        """Exige decisão do RT antes de emitir RBC (perfil A) — partição
        `pontos_nao_rbc`. `EXCLUIDO` já é resultado de decisão, não fica
        pendente."""
        return self in (
            ClassificacaoPonto.FORA_DECLARADA,
            ClassificacaoPonto.SEM_CMC,
            ClassificacaoPonto.U_MENOR_CMC,
        )


class EstadoCertificado(str, Enum):
    """Ciclo de vida do certificado (plan §3). Os VALORES batem 1:1 com
    `StatusCertificado` do stub (`infrastructure/certificados/models.py`) —
    lowercase — porque o trigger cross-app INV-025 lê `status='emitido'` literal
    (ADR-0078). `SUBSTITUIDA` é a choice ESTENDIDA pela migration aditiva
    (T-CER-020) para a reemissão versionada (US-CER-004); aditiva, não toca o
    contrato do trigger (que só filtra `'emitido'`).

    `RASCUNHO` permanece declarado (compat stub) mas NÃO é materializado nesta
    frente: a reconciliação calculada + as `AnaliseReconciliacaoCertificado`
    penduram em `calibracao_id`, SEM linha em `certificados` até `emitir`. Assim
    a tabela contém APENAS snapshots imutáveis `'emitido'` (WORM puro).
    """

    RASCUNHO = "rascunho"
    EMITIDO = "emitido"
    SUBSTITUIDA = "substituida"
    REVOGADO = "revogado"

    @property
    def terminal(self) -> bool:
        """Estados sem transição de saída (reemissão cria NOVA linha, não muta)."""
        return self in (EstadoCertificado.SUBSTITUIDA, EstadoCertificado.REVOGADO)

    @property
    def emitido(self) -> bool:
        """Emissão metrológica concluída (números definitivos + snapshot
        congelado). NÃO significa 'entregue ao cliente' — a entrega normativa
        cl. 7.8 depende da assinatura A3 (Wave A)."""
        return self is EstadoCertificado.EMITIDO

    @property
    def consultavel(self) -> bool:
        """Já materializado em `certificados` (read-path). RASCUNHO não
        materializa nesta frente."""
        return self in (
            EstadoCertificado.EMITIDO,
            EstadoCertificado.SUBSTITUIDA,
            EstadoCertificado.REVOGADO,
        )


class TipoAcreditacao(str, Enum):
    """Selo do certificado (cl. 8.1.3 / ADR-0075). `RBC` só perfil A com
    acreditação vigente E pontos todos cobertos (`pode_emitir_rbc`); senão
    `NAO_RBC` (capacidade interna B/C/D, ou perfil A fora do escopo/vencido)."""

    RBC = "RBC"
    NAO_RBC = "NAO_RBC"


class DecisaoReconciliacaoRT(str, Enum):
    """Decisão WORM do RT sobre um ponto problemático (NC-03 / padrão ADR-0070).

    - `EXCLUIR_PONTO`: ponto sai do certificado (não reportado).
    - `EMITIR_NAO_RBC_NO_PONTO`: ponto reportado SEM selo RBC (exige
      `ressalva_nao_rbc` — C-03 / cl. 8.1.3, anti uso indevido de acreditação).
    - `ABORTAR`: cancela a emissão (bug grave — ex.: orçamento errado).
    """

    EXCLUIR_PONTO = "EXCLUIR_PONTO"
    EMITIR_NAO_RBC_NO_PONTO = "EMITIR_NAO_RBC_NO_PONTO"
    ABORTAR = "ABORTAR"


class CategoriaMotivoExclusao(str, Enum):
    """Categoria objetiva do motivo de exclusão/rebaixamento de um ponto
    (C-02 / cl. 7.10.1) — campo estruturado para auditoria CGCRE.

    `U_MAIOR_QUE_CMC_BUG` casa com a classificação `ClassificacaoPonto.U_MENOR_CMC`
    (a U declarada é menor que a CMC = a CMC estava otimista demais perante a U
    real; nomes de direção aparente oposta, mesmo fenômeno)."""

    PADRAO_FORA_VALIDADE = "PADRAO_FORA_VALIDADE"
    FALHA_REPETIBILIDADE = "FALHA_REPETIBILIDADE"
    U_MAIOR_QUE_CMC_BUG = "U_MAIOR_QUE_CMC_BUG"
    PONTO_FORA_FAIXA_DECLARADA = "PONTO_FORA_FAIXA_DECLARADA"
    CONDICAO_AMBIENTAL_NC = "CONDICAO_AMBIENTAL_NC"
    OUTRO = "OUTRO"
