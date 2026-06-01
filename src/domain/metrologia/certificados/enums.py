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
