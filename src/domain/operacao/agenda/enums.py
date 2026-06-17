"""Enums fechados do domínio agenda (Fatia 1a — T-AGE-010).

str-mixin → serialização JSON nativa (mesmo padrão de ``contas_receber/enums.py``).
Domínio NÃO importa Django (ADR-0007).
"""

from __future__ import annotations

from enum import Enum


class TipoEvento(str, Enum):
    """Tipo do evento na agenda.

    ``os``                 — atividade de OS (exige ``atividade_id`` — INV-AG-ATIVIDADE-001).
    ``bloqueio``           — bloqueio com motivo (férias, atestado etc. — US-AG-004).
    ``descanso_legal``     — descanso obrigatório (gerado pela validação de jornada UMC).
    ``deslocamento``       — deslocamento entre pontos (Wave A: preenchido manualmente).
    ``almoco``             — pausa de almoço (R5 intrajornada).
    ``manutencao_interna`` — manutenção interna/reunião sem atendimento externo.
    ``feriado``            — feriado (seed nacional ou custom por tenant — D-AGE-10).
    """

    OS = "os"
    BLOQUEIO = "bloqueio"
    DESCANSO_LEGAL = "descanso_legal"
    DESLOCAMENTO = "deslocamento"
    ALMOCO = "almoco"
    MANUTENCAO_INTERNA = "manutencao_interna"
    FERIADO = "feriado"


class EstadoEvento(str, Enum):
    """Estado do evento — máquina de estados (D-AGE-3, Padrão A).

    Transições válidas (ver ``transicoes.py``):
        agendado      → em_execucao | cancelado | no_show
        em_execucao   → concluido | cancelado
        concluido     → (terminal)
        cancelado     → (terminal)
        no_show       → (terminal)

    Eventos passados imutáveis: move = update timestamps + EventoAuditoriaAgenda
    append-only (D-AGE-3).
    """

    AGENDADO = "agendado"
    EM_EXECUCAO = "em_execucao"
    CONCLUIDO = "concluido"
    CANCELADO = "cancelado"
    NO_SHOW = "no_show"


class MotivoBloqueio(str, Enum):
    """Motivo de um evento do tipo ``bloqueio`` (US-AG-004).

    ``ferias``      — férias anuais.
    ``treinamento`` — treinamento / capacitação.
    ``atestado``    — afastamento médico.
    ``outro``       — qualquer outro motivo com descrição livre.
    """

    FERIAS = "ferias"
    TREINAMENTO = "treinamento"
    ATESTADO = "atestado"
    OUTRO = "outro"


class AcaoAuditoria(str, Enum):
    """Ação registrada no ``EventoAuditoriaAgenda`` (PLAN-AGE-08 / D-AGE-5).

    ``criado``             — evento criado pela primeira vez.
    ``movido``             — data/hora alterada sem mudar técnico.
    ``reagendado``         — reagendamento com novo técnico ou nova janela (PLAN-AGE-08).
    ``bloqueado``          — bloqueio de jornada aplicado (PLAN-AGE-08).
    ``cancelado``          — evento cancelado.
    ``aprovado``           — aprovação manual (gestor confirma slot).
    ``no_show``            — técnico não compareceu.
    ``regime_indeterminado``— papéis de campo conflitantes sem override (D-AGE-15 / INV-AG-REGIME-001).
    """

    CRIADO = "criado"
    MOVIDO = "movido"
    REAGENDADO = "reagendado"
    BLOQUEADO = "bloqueado"
    CANCELADO = "cancelado"
    APROVADO = "aprovado"
    NO_SHOW = "no_show"
    REGIME_INDETERMINADO = "regime_indeterminado"


class RegimeJornada(str, Enum):
    """Regime de jornada do colaborador (D-AGE-15 / ADV-AGE-02).

    O enquadramento depende da CTPS real — análise trabalhista individual
    (RH/advogado humano). A IA NUNCA decide o valor (INV-AG-REGIME-001).

    ``motorista_profissional`` — CLT 235-C: R1-R5 + espera 1/1 (ADI 5322).
    ``clt_geral``              — CLT arts. 58/66/71: R1/R3/R4/R5 sem R2.
    ``nao_aplica``             — papel não-campo ou indeterminado (fail-safe).
    """

    MOTORISTA_PROFISSIONAL = "motorista_profissional"
    CLT_GERAL = "clt_geral"
    NAO_APLICA = "nao_aplica"


class FonteRegime(str, Enum):
    """Fonte do regime de jornada resolvido (D-AGE-15 / INV-AG-REGIME-001).

    ``override_humano`` — valor gravado explicitamente por RH/advogado humano.
    ``derivado_papel``  — derivado automaticamente do papel do colaborador.
    ``indeterminado``   — papéis de campo conflitantes sem override; regime
                          deve ser ``nao_aplica`` (fail-safe — ver ``RegimeJornadaResolvido``).
    """

    OVERRIDE_HUMANO = "override_humano"
    DERIVADO_PAPEL = "derivado_papel"
    INDETERMINADO = "indeterminado"
