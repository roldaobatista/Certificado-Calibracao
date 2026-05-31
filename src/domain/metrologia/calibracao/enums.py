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


class EstadoNaoConformidade(str, Enum):
    """6 estados da NaoConformidade — cl. 7.10 + cl. 8.7 CAPA (INV-CAL-NC-002/003).

    Maquina de estados §4.2 spec — REABERTA volta sempre a CONTIDA (cl. 8.7.2).
    """

    CONTIDA = "CONTIDA"
    ACAO_CORRETIVA_DEFINIDA = "ACAO_CORRETIVA_DEFINIDA"
    ACAO_EXECUTADA = "ACAO_EXECUTADA"
    EFICACIA_VERIFICADA = "EFICACIA_VERIFICADA"
    FECHADA = "FECHADA"
    REABERTA = "REABERTA"

    @property
    def terminal(self) -> bool:
        """FECHADA eh o unico terminal de fato — REABERTA volta a CONTIDA."""
        return self == EstadoNaoConformidade.FECHADA


class AcaoCorretivaTipo(str, Enum):
    """Tipo de acao corretiva (NOVO-2 RBC R2)."""

    RE_EXECUTAR = "RE_EXECUTAR"
    AJUSTE_ADMINISTRATIVO = "AJUSTE_ADMINISTRATIVO"


class DecisaoContinuarOuParar(str, Enum):
    """Decisao cl. 7.10.1/2 — INV-CAL-NC-002 (default A_DEFINIR pre-acao)."""

    PARAR_TRABALHO = "PARAR_TRABALHO"
    CONTINUAR_COM_CONTROLE = "CONTINUAR_COM_CONTROLE"
    A_DEFINIR = "A_DEFINIR"


class ClienteNotificadoVia(str, Enum):
    """Canal de notificacao ao cliente quando PARAR_TRABALHO (INV-CAL-NC-003).

    Valor NAO_APLICA representa explicitamente "nao notificar" — usado em
    NaoConformidade quando decisao != PARAR_TRABALHO (ex: CONTINUAR_COM_CONTROLE
    ou A_DEFINIR; nesses casos a notificacao formal nao e obrigatoria).
    Quando decisao == PARAR_TRABALHO, o use case `executar_acao` valida que
    canal != NAO_APLICA (regra INV-CAL-NC-003 — cliente precisa ser notificado
    via meio rastreavel).
    """

    NAO_APLICA = "NAO_APLICA"
    EMAIL_PORTAL = "EMAIL_PORTAL"
    A3_ASSINATURA = "A3_ASSINATURA"
    TERMO_PRESENCIAL = "TERMO_PRESENCIAL"


class EstadoReclamacao(str, Enum):
    """4 estados da ReclamacaoCalibracao — US-CAL-018 + cl. 7.9 + CDC art. 26."""

    RECEBIDA = "RECEBIDA"
    EM_ANALISE = "EM_ANALISE"
    RESPONDIDA = "RESPONDIDA"
    ARQUIVADA = "ARQUIVADA"

    @property
    def terminal(self) -> bool:
        """RESPONDIDA + ARQUIVADA sao terminais."""
        return self in {EstadoReclamacao.RESPONDIDA, EstadoReclamacao.ARQUIVADA}


class DecisaoAvaliacaoSubcontratado(str, Enum):
    """3 decisoes da avaliacao periodica de subcontratado (cl. 6.6.2 + P-CAL-R5)."""

    MANTER = "MANTER"
    ACOMPANHAMENTO = "ACOMPANHAMENTO"
    DESCREDENCIAR = "DESCREDENCIAR"

    @property
    def aprovado(self) -> bool:
        """MANTER + ACOMPANHAMENTO continuam operando (com vigilancia)."""
        return self in {
            DecisaoAvaliacaoSubcontratado.MANTER,
            DecisaoAvaliacaoSubcontratado.ACOMPANHAMENTO,
        }


class DecisaoReclamacao(str, Enum):
    """3 decisoes finais da reclamacao (US-CAL-018 + ADR-0045 saga recall)."""

    PROCEDENTE_RECALL = "PROCEDENTE_RECALL"
    PROCEDENTE_ERRATA = "PROCEDENTE_ERRATA"
    IMPROCEDENTE = "IMPROCEDENTE"

    @property
    def dispara_recall_m5(self) -> bool:
        """PROCEDENTE_RECALL aciona saga recall Marco 5 (ADR-0045)."""
        return self == DecisaoReclamacao.PROCEDENTE_RECALL

    @property
    def procedente(self) -> bool:
        return self in {
            DecisaoReclamacao.PROCEDENTE_RECALL,
            DecisaoReclamacao.PROCEDENTE_ERRATA,
        }


class TipoOrigemComponente(str, Enum):
    """8 origens fisicas de um componente de incerteza (NIT-DICLA-030 §16.6).

    Bate 1:1 com TIPO_ORIGEM_COMPONENTE_CHOICES em models.py. INV-CAL-INC-002
    valida as obrigatorias por grandeza+padrao (matriz
    componentes-obrigatorios-por-grandeza).
    """

    REPETIBILIDADE = "REPETIBILIDADE"
    RESOLUCAO_INSTRUMENTO = "RESOLUCAO_INSTRUMENTO"
    INCERTEZA_PADRAO_REF = "INCERTEZA_PADRAO_REF"
    DERIVA_PADRAO = "DERIVA_PADRAO"
    CONDICOES_AMBIENTAIS = "CONDICOES_AMBIENTAIS"
    EXCENTRICIDADE = "EXCENTRICIDADE"
    POLARIZACAO_BIAS = "POLARIZACAO_BIAS"
    OUTRO = "OUTRO"


class DistribuicaoIncerteza(str, Enum):
    """Distribuicao de probabilidade do componente (GUM cl. 4.3 + §16.6).

    Bate 1:1 com DISTRIBUICAO_CHOICES em models.py. O divisor associado
    converte a meia-largura `a` em incerteza-padrao u_i (ex: RETANGULAR ->
    a/sqrt(3); TRIANGULAR -> a/sqrt(6); U -> a/sqrt(2)).
    """

    NORMAL = "NORMAL"
    RETANGULAR = "RETANGULAR"
    TRIANGULAR = "TRIANGULAR"
    U = "U"
    OUTRA = "OUTRA"


class FormulaCalculoComponente(str, Enum):
    """Formula declarada de derivacao do componente (NIT-DICLA-030 §16.6).

    Bate 1:1 com FORMULA_CALCULO_CHOICES em models.py (matriz
    formula-calculo-por-grandeza). Provenance auditavel CGCRE 25a (cl. 8.4).
    """

    REPETIBILIDADE_STD_MEDIA = "REPETIBILIDADE_STD_MEDIA"
    RESOLUCAO_RETANGULAR = "RESOLUCAO_RETANGULAR"
    PADRAO_CERTIFICADO = "PADRAO_CERTIFICADO"
    DERIVA_LINEAR = "DERIVA_LINEAR"
    TEMPERATURA_QUADRATICA = "TEMPERATURA_QUADRATICA"
    BIAS_CONHECIDO = "BIAS_CONHECIDO"
    OUTRO = "OUTRO"


class MetodoTipoAPonto(str, Enum):
    """Como o componente Tipo A (repetibilidade) foi obtido NUM ponto — ADR-0077
    (SAN-INCERTEZA-PONTO / consultor-rbc Q-RBC-2).

    Registro probatório cl. 7.5/7.11: nunca substituir s_x silenciosamente.
    - SX_PROPRIO: s_x calculado das repetições do próprio ponto (n >= 6).
    - S_POOLED: desvio-padrão combinado (pooled) de histórico/validação do método,
      usado quando 2 <= n < 6 (GUM §4.2.4 + EA-4/02 §3.2 — continua Tipo A).
    - AUSENTE: n < 2 — sem componente Tipo A no ponto (só Tipo B), registrado.
    """

    SX_PROPRIO = "SX_PROPRIO"
    S_POOLED = "S_POOLED"
    AUSENTE = "AUSENTE"


class LeiEscalonamento(str, Enum):
    """Como um componente Tipo B varia ao longo da faixa — ADR-0077 (consultor-rbc
    Q-RBC-1, base GUM §5.1.3 / NIT-DICLA-030 §5.5 / ILAC-P14 §5.5).

    - CONSTANTE: valor absoluto fixo em todos os pontos (ex.: resolução = a/√3).
    - PROPORCIONAL: escala com o valor do ponto (b·X) — ex.: deriva % do valor.
    - LINEAR_AFIM: a + b·X — forma do certificado do padrão (piso + ganho).

    Default por origem (RT confirma): RESOLUCAO_* -> CONSTANTE; INCERTEZA_PADRAO_REF
    / DERIVA_PADRAO -> LINEAR_AFIM; ambientais/excentricidade -> declarado pelo RT.
    1ª fatia SAN-INCERTEZA-PONTO trata todo Tipo B como CONSTANTE + portão
    fail-closed na emissão RBC quando algum padrão tem b != 0 (não subestimar U).
    """

    CONSTANTE = "CONSTANTE"
    PROPORCIONAL = "PROPORCIONAL"
    LINEAR_AFIM = "LINEAR_AFIM"
