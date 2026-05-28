# ruff: noqa: RUF001, RUF002, RUF003 — simbolo grego canonico (σ = sigma) na notacao estatistica
"""Enums fechados do dominio padroes (M5 Wave A — T-PAD-001).

Estados + tipos canonicos do PadraoMetrologico. Frozen + str-mixin para
serializar em JSON sem conversao manual (mesmo padrao de
src/domain/metrologia/calibracao/enums.py).

Bate 1:1 com choices em src/infrastructure/metrologia/padroes/models.py
(Wave A — a criar). Domain NAO importa Django (ADR-0007 spec-as-source).
"""

from __future__ import annotations

from enum import Enum


class EstadoPadrao(str, Enum):
    """Ciclo de vida do padrao metrologico (modelo-de-dominio + plan v2 §14).

    `RECAL_RETORNADO_PENDENTE_APROVACAO` (C-4 FURO-1 corretora): o padrao voltou
    do lab externo com novos valores gravados, mas o RT ainda NAO fez a analise
    critica do cert de recal — nao pode voltar a uso utilizavel ate aprovado.
    """

    EM_USO = "EM_USO"
    EM_RECAL_EXTERNO = "EM_RECAL_EXTERNO"
    RECAL_RETORNADO_PENDENTE_APROVACAO = "RECAL_RETORNADO_PENDENTE_APROVACAO"
    INTERCOMPARACAO_PT_EM_CURSO = "INTERCOMPARACAO_PT_EM_CURSO"
    BAIXADO = "BAIXADO"
    SUCATEADO = "SUCATEADO"

    @property
    def terminal(self) -> bool:
        """SUCATEADO eh terminal duro; BAIXADO eh reversivel (avaliacao tecnica)."""
        return self == EstadoPadrao.SUCATEADO

    @property
    def permite_uso_em_calibracao(self) -> bool:
        """Apenas EM_USO libera selecao do padrao numa calibracao.

        Demais estados bloqueiam (fail-closed — ADR-0070/plan D-PAD-5). A
        flag transversal `rastreabilidade_origem_revogada` (C-5) bloqueia uso
        mesmo em EM_USO — verificada separadamente em `padrao_bloqueado_para_uso`.
        """
        return self == EstadoPadrao.EM_USO

    @property
    def aceita_recal_envio(self) -> bool:
        """Apenas EM_USO pode ser enviado ao lab externo."""
        return self == EstadoPadrao.EM_USO

    @property
    def aceita_intercomparacao(self) -> bool:
        """Apenas EM_USO pode iniciar PT."""
        return self == EstadoPadrao.EM_USO


class VinculacaoCadeia(str, Enum):
    """Cadeia de rastreabilidade ao SI (cl. 6.5)."""

    BIPM = "BIPM"
    INMETRO = "INMETRO"
    RBC = "RBC"
    INTERNACIONAL = "INTERNACIONAL"

    @property
    def exige_perfil_a(self) -> bool:
        """RBC exige tenant perfil A acreditado CGCRE (INV-PAD-005 + ADR-0067)."""
        return self == VinculacaoCadeia.RBC


class ClassePadrao(str, Enum):
    """Classe de exatidao OIML R111 (massa) + analogos por grandeza.

    R111 define classe/MPE/incerteza — NAO define periodicidade de VI/recal
    (ADR/plan C-9: intervalo eh configuravel por tenant com criterio justificado,
    cl. 6.4.7 + ILAC-G24; NUNCA cravar 'intervalo R111').
    """

    E1 = "E1"
    E2 = "E2"
    F1 = "F1"
    F2 = "F2"
    M1 = "M1"
    M2 = "M2"
    M3 = "M3"
    OUTRA = "OUTRA"


class SubtipoPadrao(str, Enum):
    """Padrao principal vs equipamento auxiliar cl. 6.4.5 (US-PAD-007 / C-8)."""

    PRINCIPAL = "PRINCIPAL"
    AUXILIAR_AMBIENTAL = "AUXILIAR_AMBIENTAL"  # termo-higrometro de sala
    AUXILIAR_ELETRICO = "AUXILIAR_ELETRICO"  # fonte de tensao estavel
    AUXILIAR_TERMOMETRICO = "AUXILIAR_TERMOMETRICO"  # banho termostatico

    @property
    def eh_auxiliar(self) -> bool:
        return self != SubtipoPadrao.PRINCIPAL


class StatusRecal(str, Enum):
    """Status do recal externo (modelo-de-dominio §RecalExternoPadrao)."""

    ENVIADO = "ENVIADO"
    RETORNADO = "RETORNADO"
    EXTRAVIADO_NO_TRANSPORTE = "EXTRAVIADO_NO_TRANSPORTE"
    RECUSADO_PELO_LAB = "RECUSADO_PELO_LAB"


class ResultadoVI(str, Enum):
    """Resultado da verificacao intermediaria (cl. 6.4.10 — INV-022)."""

    APROVADO = "APROVADO"
    REPROVADO = "REPROVADO"
    INCONCLUSIVO = "INCONCLUSIVO"

    @property
    def bloqueia_uso(self) -> bool:
        """REPROVADO bloqueia uso ate nova VI aprovada (INV-CAL-VI-001)."""
        return self == ResultadoVI.REPROVADO


class ResultadoPT(str, Enum):
    """Resultado da intercomparacao / proficiency testing (cl. 6.6 — INV-023)."""

    APROVADO = "APROVADO"
    REJEITADO = "REJEITADO"
    SOB_REVISAO = "SOB_REVISAO"

    @property
    def bloqueia_uso(self) -> bool:
        """REJEITADO bloqueia uso ate NC tratada (INV-012)."""
        return self == ResultadoPT.REJEITADO


class RegraWesternElectric(str, Enum):
    """Regras de controle estatistico Shewhart (ADR-0070 + C-3 RBC).

    Regras 2 e 3 sao 'do mesmo lado' (correcao RBC — sem isso, falso-positivo).
    Regra 5 (tendencia) eh o cerne da deteccao de deriva (Dor #04) — sem ela o
    modulo nao detecta o cenario-alvo. Conjunto + parametros versionados
    (`versao_motor_shewhart` — cl. 7.11).
    """

    REGRA_1_FORA_3SIGMA = "REGRA_1_FORA_3SIGMA"  # 1 ponto alem de ±3σ
    REGRA_2_2DE3_2SIGMA = "REGRA_2_2DE3_2SIGMA"  # 2 de 3 alem de ±2σ, mesmo lado
    REGRA_3_4DE5_1SIGMA = "REGRA_3_4DE5_1SIGMA"  # 4 de 5 alem de ±1σ, mesmo lado
    REGRA_4_RUN_8 = "REGRA_4_RUN_8"  # 8 consecutivos do mesmo lado da media
    REGRA_5_TENDENCIA_7 = "REGRA_5_TENDENCIA_7"  # 7 consecutivos monotonicos

    @property
    def severidade_p1(self) -> bool:
        """Regra 1 (fora 3σ) eh violacao dura P1; demais sao alerta/trend (C-16).

        Mesmo as de alerta exigem AnaliseCartaControle registrada antes de
        liberar uso continuado (INV-PAD-010).
        """
        return self == RegraWesternElectric.REGRA_1_FORA_3SIGMA


class DecisaoRTCarta(str, Enum):
    """Decisao do RT ao analisar disparo de regra Western Electric (ADR-0070)."""

    ACEITO_COM_JUSTIFICATIVA = "ACEITO_COM_JUSTIFICATIVA"
    RECALIBRAR = "RECALIBRAR"
    SUSPENDER_USO = "SUSPENDER_USO"

    @property
    def libera_uso(self) -> bool:
        """Apenas ACEITO_COM_JUSTIFICATIVA mantem o padrao em uso."""
        return self == DecisaoRTCarta.ACEITO_COM_JUSTIFICATIVA
