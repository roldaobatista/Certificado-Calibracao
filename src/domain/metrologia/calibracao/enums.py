"""Enums fechados do dominio calibracao (P4 Fase 5 Batch A).

Estados + tipos canonicos. Frozen + str-mixin para serializar facil
em JSON sem conversao manual.

Bate 1:1 com choices em src/infrastructure/calibracao/models.py:
- ESTADO_CALIBRACAO_CHOICES -> EstadoCalibracao
- TIPO_ACREDITACAO_CHOICES  -> TipoAcreditacao
- REGRA_DECISAO_CHOICES     -> RegraDecisao

Por que duplicar (vs reusar choices):
- Domain layer NAO importa Django (ADR-0007 spec-as-source).
- Choices em models.py sao listas (str, str); enums em domain sao
  tipos com semantica (.terminal, .imutavel, etc).
"""

from __future__ import annotations

from enum import Enum


class EstadoCalibracao(str, Enum):
    """12 estados da calibracao (§4.1 spec — INV-CAL-WORM-001)."""

    RECEPCIONADA = "recepcionada"
    CONFIGURADA = "configurada"
    EM_EXECUCAO = "em_execucao"
    EM_REVISAO_1 = "em_revisao_1"
    AGUARDANDO_2A_CONFERENCIA = "aguardando_2a_conferencia"
    APROVADA = "aprovada"
    REJEITADA = "rejeitada"
    CANCELADA = "cancelada"
    NAO_CONFORME = "nao_conforme"
    PENDENTE_RESOLUCAO_NC = "pendente_resolucao_nc"
    AGUARDANDO_SUBCONTRATADO = "aguardando_subcontratado"
    RECEBIDA_DO_SUBCONTRATADO = "recebida_do_subcontratado"

    @property
    def terminal(self) -> bool:
        """Estado nao reabrivel (APROVADA imutavel + REJEITADA/CANCELADA)."""
        return self in {
            EstadoCalibracao.APROVADA,
            EstadoCalibracao.REJEITADA,
            EstadoCalibracao.CANCELADA,
        }

    @property
    def aceita_leituras(self) -> bool:
        """Apenas EM_EXECUCAO aceita registro de leitura nova."""
        return self == EstadoCalibracao.EM_EXECUCAO

    @property
    def aceita_subcontratacao(self) -> bool:
        """Apenas CONFIGURADA pode transitar pra AGUARDANDO_SUBCONTRATADO."""
        return self == EstadoCalibracao.CONFIGURADA


class TipoAcreditacao(str, Enum):
    """Acreditacao do tenant (CGCRE) — cl. 6.4.10 + INV-CAL-CMC-001."""

    RBC = "RBC"
    NAO_RBC = "NAO_RBC"

    @property
    def exige_cmc(self) -> bool:
        """RBC obrigatoriamente declara CMC; NAO_RBC nao tem CMC formal."""
        return self == TipoAcreditacao.RBC


class RegraDecisao(str, Enum):
    """3 modos de regra de decisao ISO 17025 cl. 7.8.6 (ADR-0024 rev.)."""

    ACEITACAO_SIMPLES = "ACEITACAO_SIMPLES"
    BANDA_GUARDA_30 = "BANDA_GUARDA_30"
    RISCO_COMPARTILHADO = "RISCO_COMPARTILHADO"

    @property
    def exige_pfa(self) -> bool:
        """BANDA_GUARDA_30 -> calcula PFA (Probability of False Accept)."""
        return self == RegraDecisao.BANDA_GUARDA_30

    @property
    def exige_pra(self) -> bool:
        """RISCO_COMPARTILHADO -> calcula PRA (Probability of False Reject)."""
        return self == RegraDecisao.RISCO_COMPARTILHADO


class OrigemRecepcao(str, Enum):
    """Origem da calibracao (ADR-0023 — ou plugada em OS ou recepcao avulsa)."""

    ATIVIDADE_OS = "ATIVIDADE_OS"  # acoplada em AtividadeDaOS (campo atividade_os_id NOT NULL)
    AVULSA = "AVULSA"  # recepcao direta (US-CAL-001 — sem OS por tras)
