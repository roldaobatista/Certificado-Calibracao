"""Erros de domínio do módulo `precificacao` (T-PRC-015).

9 erros de regra de negócio. Mapeados a HTTP na camada REST.
Refs: spec §4 Erros; TL-PRC-05.
"""

from __future__ import annotations


class PrecificacaoError(Exception):
    """Base dos erros de domínio de precificação."""


class CustoRealIndisponivel(PrecificacaoError):
    """INV-PRC-COSTPLUS-STUB — tentativa de publicar regra COST_PLUS sem provider
    real disponível (stub ativo). Fail-closed: gate em tempo de CONFIGURAÇÃO.
    → 422 (D-PRC-6).
    """

    reason = "CUSTO_REAL_INDISPONIVEL"


class PrecoMinimoViolado(PrecificacaoError):
    """INV-PRC-MINIMO-BLOQUEIO — preço final resultante < preço mínimo calculável.

    Bloqueio DURO quando custo está disponível (NUNCA aprovável — AC-PRC-003-3).
    O bloqueio é sempre reversível pelo tenant em autosserviço (revogar a regra
    remove o mínimo — fato probatório de alocação de responsabilidade, ADV-PRC-08).
    → 422.
    """

    reason = "PRECO_MINIMO_VIOLADO"


class ParametrosInviaveis(PrecificacaoError):
    """Denominador ≤ 0 em fórmula de cálculo (TL-PRC-18 — never divide by zero raw).

    Situações: margem_alvo_pct = 100% → denominador (1 - 1) = 0 em MARGEM_ALVO;
    custo_manual_declarado = 0 → custo inválido para cálculo de margem.
    → 422.
    """

    reason = "PARAMETROS_INVIAVEIS"


class FaixasDescontoInvalidas(PrecificacaoError):
    """INV-PRC-FAIXAS-CONTIGUAS — conjunto de faixas não cobre [0..100] exatamente.

    Causas: buraco entre faixas, sobreposição, não começa em 0, não termina em 100.
    → 422.
    """

    reason = "FAIXAS_DESCONTO_INVALIDAS"


class RegraVigenteAusente(PrecificacaoError):
    """Sem regra de formação vigente para o item (TL-PRC-05).

    LEVANTADO SÓ no endpoint `vigente?item_id=` (→ 404).
    O MOTOR NUNCA levanta este erro — caminho sem regra é válido e marca
    `sem_regra_formacao: True` + semáforo INDISPONIVEL no resultado.
    """

    reason = "REGRA_VIGENTE_AUSENTE"


class CustoIndisponivel(PrecificacaoError):
    """INV-PRC-CUSTO-EXPLICITO — stub nunca retorna 0; ausência = esta exceção.

    O `StubCustoProvider` levanta esta exceção sempre (nunca retorna 0 silencioso).
    O motor usa a exceção para marcar `origem_custo = INDISPONIVEL` e semáforo
    INDISPONIVEL — nunca mascara a ausência.
    → contexto: informativo no motor (capturado); 422 se uso require custo real.
    """

    reason = "CUSTO_INDISPONIVEL"


class FingerprintDivergente(PrecificacaoError):
    """D-PRC-14 — fingerprint do cálculo vigente não bate com o do pedido de aprovação.

    Consumidor NÃO pode usar aprovação se o cálculo foi refeito com entradas
    diferentes desde a solicitação (preço mudou, faixas mudaram, etc.).
    → 422.
    """

    reason = "FINGERPRINT_DIVERGENTE"


class AlcadaInsuficiente(PrecificacaoError):
    """INV-PRC-APROVACAO-INDEPENDENTE / predicate `alcada_cobre` — papel do decisor
    não cobre a alçada exigida pelo desconto solicitado (ex: gerente decidindo
    faixa que exige DONO).
    → 403.
    """

    reason = "ALCADA_INSUFICIENTE"


class DecisorNaoIndependente(PrecificacaoError):
    """INV-PRC-APROVACAO-INDEPENDENTE — decisor_id == solicitante_id (ADR-0026 molde).

    A decisão de aprovação de desconto exige independência: quem solicitou não
    pode aprovar o próprio desconto.
    → 422.
    """

    reason = "DECISOR_NAO_INDEPENDENTE"
