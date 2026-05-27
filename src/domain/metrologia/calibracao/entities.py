"""Snapshot DTOs imutaveis do dominio calibracao (P4 Fase 5 Batch A).

Snapshots atravessam fronteira de camada (use case <-> repository).
Adapter Django converte Model PG <-> Snapshot. Use case nunca conhece
Django.

ADR-0007 (spec-as-source) + ADR-0023 (Atividade com tipo=calibracao
acopla a esta entidade).

Esta release (Batch A — Fase 5 inicial):
- CalibracaoSnapshot — raiz agregado (alinhado com PG 0001_initial.py
  field-by-field; somente os campos que use cases iniciais USAM).

Pendente (proximos batches Fase 5):
- LeituraSnapshot, OrcamentoIncertezaSnapshot, ComponenteIncertezaSnapshot,
  PadraoUsadoSnapshot, EventoDeCalibracaoSnapshot,
  NaoConformidadeSnapshot, AceiteRegraDecisaoSnapshot, etc.

Estrategia "snapshot enxuto": cada snapshot carrega APENAS campos
relevantes pra use cases atuais. Adicionar campo novo eh PR mínimo
quando use case novo precisar.

Convencao com defaults PG: snapshot reflete o estado DEPOIS do INSERT.
Campos com DEFAULT no PG aparecem com seus valores default na criacao
(ex: regra_decisao=ACEITACAO_SIMPLES default; nao representamos como
None). Snapshot eh "verdade pos-INSERT".
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import Enum
from uuid import UUID

from .enums import (
    AcaoCorretivaTipo,
    ClienteNotificadoVia,
    DecisaoAvaliacaoSubcontratado,
    DecisaoContinuarOuParar,
    DecisaoReclamacao,
    EstadoCalibracao,
    EstadoNaoConformidade,
    EstadoReclamacao,
    OrigemRecepcao,
    RegraDecisao,
    TipoAcreditacao,
)
from .value_objects import ZonaILACG8


class OrigemLeitura(str, Enum):
    """Origem da leitura (cl. 7.5 ISO 17025 + INV-CAL-FRAUDE-EXEC-001)."""

    MANUAL = "MANUAL"
    INTEGRACAO_SERIAL = "INTEGRACAO_SERIAL"
    INTEGRACAO_USB = "INTEGRACAO_USB"


@dataclass(frozen=True, slots=True)
class CalibracaoSnapshot:
    """Snapshot da entidade Calibracao (raiz agregado §3.2 spec).

    Campos minimos para use cases Fase 5 iniciais. Demais entidades
    relacionadas (Leitura, OrcamentoIncerteza, PadraoUsado, etc) tem
    seus proprios snapshots quando os use cases delas chegarem.
    """

    # Identidade + multi-tenancy
    id: UUID
    tenant_id: UUID
    numero_interno: int  # sequence global calibracao_numero_seq_global
    numero_exibido: str  # GENERATED 'CAL-YYYY-NNNNNN' (trigger PG)

    # Vinculacao operacional (ADR-0023)
    origem_recepcao: OrigemRecepcao  # derivado de atividade_os_id (NULL=AVULSA)
    atividade_os_id: UUID | None
    instrumento_id: UUID  # FK Equipamento (M2) — obrigatorio
    snapshot_equipamento_json: dict[str, object]  # JSONB no PG; capturado em recepcionar

    # Cliente (ADR-0032 — preservacao pos-anonimizacao)
    cliente_id: UUID | None  # NULL pos-anonimizacao
    cliente_referencia_hash: str  # HashVersionado v<NN>$<base64> (ADR-0064)
    cliente_key_id: str

    # Acreditacao (cl. 6.4.10 + INV-CAL-CMC-001)
    tipo_acreditacao: TipoAcreditacao  # default NAO_RBC no PG

    # Estado + concorrencia (ADR-0065)
    status: EstadoCalibracao  # default 'recepcionada' no PG
    revision: int  # default 0 no PG; CAS para UPDATE

    # Regra de decisao (ADR-0024 rev. — default ACEITACAO_SIMPLES no PG;
    # cravado em configurar_calibracao US-CAL-002)
    regra_decisao: RegraDecisao  # default ACEITACAO_SIMPLES; nao-NULL no PG
    regra_decisao_acordada_em: datetime | None  # NULL ate cliente acordar
    regra_decisao_acordada_documento_id: UUID | None  # FK AceiteRegraDecisao

    # Validacao software (ADR-0025 cl. 7.11 + INV-CAL-VERSAO-001)
    versao_motor_calculo: str  # vazio em RECEPCIONADA; semver+commit em calcular

    # Configuracao (preenchida em configurar_calibracao US-CAL-002 — RECEPCIONADA -> CONFIGURADA)
    # Cl. 7.2 (procedimento) + cl. 7.1.1 (analise critica) + cl. 7.1.3 (capacidade).
    procedimento_id: UUID | None  # FK ProcedimentoCalibracao; NOT NULL pos-CONFIGURADA
    procedimento_versao_snapshot: dict[str, object]  # codigo + versao + hash anexo
    escopo_id: UUID | None  # FK Escopo CMC (NULL se NAO_RBC)
    analise_critica_pedido_id: UUID | None  # FK orcamento.AnaliseCritica (origem=OS)
    analise_critica_pedido_inline_hash: str  # nao-vazio em recepcao avulsa
    capacidade_tecnica_confirmada_por_user_id: UUID | None  # cl. 7.1.1 avulsa

    # Atores cl. 6.2 (preenchidos progressivamente) — INV-CAL-FRAUDE-EXEC/REV/CONF-001
    executor_id: UUID | None  # metrologista que iniciou as leituras (US-CAL-004)
    revisor_id: UUID | None  # RT que aprovou a 1a conferencia (US-CAL-007)
    conferente_id: UUID | None  # RT que aprovou a 2a conferencia (US-CAL-008)

    # Snapshots de competencia (cl. 6.2 + AC-CAL-007-5/008-4 + INV-CAL-RT-002)
    # Imutaveis pos-aprovacao. JSONB no PG. None ate aprovacao acontecer.
    snapshot_competencia_revisor_json: dict[str, object] | None
    snapshot_competencia_conferente_json: dict[str, object] | None

    # Excecao 2a conferencia (ADR-0026 4 condicoes objetivas + 5%/mes)
    # FK para Excecao2aConferencia quando conferente_id == revisor_id (excecao registrada).
    excecao_2a_conf_id: UUID | None

    # Avaliacao de conformidade (US-CAL-006 + ADR-0024 revisado + ILAC G8:2019 §4)
    # Preenchidos por avaliar_conformidade; default NA na criacao (PG: default 'NA').
    zona_ilac_g8: ZonaILACG8  # default ZonaILACG8.NA
    decisao: str  # default "NA"; CONFORME / NAO_CONFORME / NA (derivada da zona)
    pfa_calculada: Decimal | None  # NOT NULL quando regra=BANDA_GUARDA_30 (INV-CAL-DEC-004)
    pra_calculada: Decimal | None  # NOT NULL quando regra=RISCO_COMPARTILHADO (INV-CAL-DEC-004)

    # Subcontratacao US-CAL-017 (cl. 6.6 + INV-CAL-SUBC-001..006)
    # Preenchidos quando fluxo subcontratacao ativo. None na criacao.
    subcontratado_id: UUID | None  # FK LaboratorioSubcontratado
    aceite_subcontratacao_id: UUID | None  # FK AceiteSubcontratacao (INV-CAL-SUBC-001)
    certificado_subcontratado_snapshot_json: dict[str, object] | None  # cert recebido
    recebedor_user_id: UUID | None  # INV-CAL-FRAUDE-RECEB-001 (quem registrou recebimento)

    # Auditoria forense (correlation + causation cross-marco)
    correlation_id: UUID
    causation_id: UUID | None  # nova calibracao apos rejeicao/recall (US-CAL-007)
    criada_em: datetime  # auto_now_add no PG
    criada_por_user_id: UUID | None

    # Cancelamento (T-CAL-095 PROD-CAL-03 conserto P5 — ADR-0064)
    # HashVersionado v<NN>$<base64> derivado do motivo canonicalizado.
    # Vazio quando status != CANCELADA.
    motivo_cancelamento_hash: str = ""


@dataclass(frozen=True, slots=True)
class ComponenteIncertezaSnapshot:
    """Componente individual do orcamento (1:N de OrcamentoIncerteza).

    Imutavel pos-INSERT (INV-CAL-WORM-001). Tipo A exige n_amostras >=6
    + s_x NOT NULL (INV-CAL-INC-003 + NIT-DICLA-030 §7.4).
    """

    id: UUID
    tenant_id: UUID
    orcamento_incerteza_id: UUID
    nome_componente: str
    tipo_componente: str  # 'A' ou 'B'
    valor_estimativa: Decimal
    contribuicao: Decimal  # u_i^2 ponderado (depois aplicado coeficiente sensibilidade)
    grau_liberdade: Decimal | None  # NULL pra Tipo B com dof=infinito
    n_amostras: int | None  # NOT NULL quando Tipo A (>=6)
    s_x: Decimal | None  # desvio-padrao amostral (NOT NULL quando Tipo A)
    correlacao_com_componente_id: UUID | None
    coeficiente_correlacao: Decimal | None  # -1 a 1
    # INV-CAL-INC-004: 2+ componentes com mesma fonte_default_padrao_id
    # sem correlacao_com_componente_id geram alerta P2 (job T-CAL-119).
    fonte_default_padrao_id: UUID | None = None


@dataclass(frozen=True, slots=True)
class OrcamentoIncertezaSnapshot:
    """Orcamento de incerteza (NIT-DICLA-030 rev. 15 + GUM JCGM 100:2008).

    Imutavel pos-EM_REVISAO_1 (INV-CAL-WORM-001 — trigger PG).
    Algoritmo 1 (GUM Decimal) obrigatorio; algoritmo 2 (Monte Carlo)
    opcional dependendo da grandeza.
    """

    id: UUID
    tenant_id: UUID
    calibracao_id: UUID
    u_combinada: Decimal  # u_c (cl. 5.1.2 GUM)
    grau_liberdade_efetivo: Decimal  # Welch-Satterthwaite (G.4)
    k: Decimal  # fator de cobertura (default 2.0)
    U_expandida: Decimal  # - U eh notacao metrologica canonica
    nivel_confianca: Decimal  # default 0.9545
    documentacao_agregacao: str  # >=50 chars (INV-CAL-INC-001)
    versao_motor_calculo: str  # semver + commit (ADR-0025 + INV-CAL-VERSAO-001)
    algoritmo_1_resultado: dict[str, object]  # GUM Decimal completo
    algoritmo_2_resultado: dict[str, object] | None  # Monte Carlo NumPy
    divergencia_pct: Decimal | None  # NULL se algoritmo_2 nao rodou
    replay_determinismo_hash: str  # HashVersionado v<NN>$<base64>
    bias_orcado: Decimal | None
    bias_origem: str  # vazio se sem bias
    arredondamento_aplicado_regra: str  # default 'NIT_DICLA_030_2_DIGITOS_SIG'
    calculado_em: datetime  # auto_now_add no PG
    correlation_id: UUID


@dataclass(frozen=True, slots=True)
class LeituraCorrecaoSnapshot:
    """Snapshot de rasura digital sobre uma Leitura (cl. 7.5 ISO 17025).

    Append-only WORM (INV-CAL-WORM-001). NAO muta a Leitura original;
    grava (valor_original, valor_corrigido, razao_correcao) preservando
    historico. Auditoria CGCRE retracta a sequencia inteira de correcoes
    em 25 anos (cl. 8.4).

    AC-CAL-004-7: so permitida quando calibracao.status IN
    (CONFIGURADA, EM_EXECUCAO). Apos EM_REVISAO_1 a correcao exige
    reabertura formal via CAPA (gera NaoConformidade — fluxo separado).

    INV-CAL-FRAUDE-COR-001: corretor_id_hash deve ser
    HashVersionado(request.user.id) — caller calcula e valida que o
    usuario logado eh quem esta corrigindo.
    """

    id: UUID
    tenant_id: UUID
    leitura_id: UUID  # FK Leitura
    valor_original: Decimal  # snapshot do valor_lido ANTES da correcao
    valor_corrigido: Decimal
    razao_correcao_canonicalizada: str  # >=30 chars + NFC + anti-PII
    razao_correcao_hash: str  # HashVersionado v<NN>$<base64>
    corretor_id_hash: str  # HashVersionado(user.id)
    corrigido_em: datetime  # auto_now_add no PG
    correlation_id: UUID


@dataclass(frozen=True, slots=True)
class LeituraSnapshot:
    """Snapshot de uma leitura individual em ponto+repeticao (cl. 7.5).

    1:N de Calibracao. Imutavel pos-INSERT (INV-CAL-WORM-001). Correcoes
    via LeituraCorrecao (rasura digital — entidade separada).

    UNIQUE composto (tenant, calibracao, ponto_calibracao, numero_repeticao)
    impede leituras duplicadas concorrentes (ADR-0065 + INV-CAL-CONC-001).

    `executor_id_hash` substitui UUID cru — INV-CAL-FRAUDE-EXEC-001 +
    anti-stalking pos retencao 25a.
    """

    id: UUID
    tenant_id: UUID
    calibracao_id: UUID
    ponto_calibracao: Decimal
    numero_repeticao: int  # 1, 2, 3, ...
    valor_lido: Decimal
    unidade: str
    origem: OrigemLeitura
    timestamp: datetime  # momento da leitura no instrumento (UTC-aware)
    executor_id_hash: str  # HashVersionado v<NN>$<base64>
    client_event_id: UUID | None  # ADR-0027 — idempotencia sync mobile
    correlation_id: UUID


@dataclass(frozen=True, slots=True)
class NaoConformidadeSnapshot:
    """Snapshot de Nao-Conformidade (cl. 7.10 + cl. 8.7 CAPA).

    Origem mutuamente exclusiva (XOR via CHECK PG):
      - calibracao_id NOT NULL + origem_proficiencia_id NULL, OU
      - origem_proficiencia_id NOT NULL + calibracao_id NULL.

    Estado-maquina §4.2: CONTIDA -> ACAO_CORRETIVA_DEFINIDA -> ACAO_EXECUTADA
      -> EFICACIA_VERIFICADA -> FECHADA. REABERTA volta a CONTIDA
      (cl. 8.7.2 — NOVO-1 RBC R2).

    Anti-PII P-CAL-A2: responsavel_acao_user_id eh "zona quente" (UUID cru
    ≤90d); responsavel_acao_user_id_hash eh sempre presente (HashVersionado).
    Job nc-responsavel-pseudonimizacao zera UUID cru pos prazo.
    """

    id: UUID
    tenant_id: UUID

    # Origem XOR
    calibracao_id: UUID | None
    origem_proficiencia_id: UUID | None

    # Descricao + hash imutaveis pos-INSERT (INV-CAL-WORM-001)
    descricao_canonicalizada: str  # >=30 chars + anti-PII + INV-DOC-CANON-001
    descricao_hash: str  # HashVersionado v<NN>$<base64> ADR-0064

    # Estado
    estado: EstadoNaoConformidade

    # Acao corretiva (preenchida em CONTIDA -> ACAO_CORRETIVA_DEFINIDA)
    causa_raiz_canonicalizada: str  # default "" antes de definir
    causa_raiz_hash: str  # default ""
    acao_corretiva_descricao_hash: str  # default ""
    acao_corretiva_tipo: AcaoCorretivaTipo | None  # None ate definir

    # Execucao da acao (preenchida em ACAO_CORRETIVA_DEFINIDA -> ACAO_EXECUTADA)
    acao_executada_em: datetime | None

    # Verificacao de eficacia (preenchida em ACAO_EXECUTADA -> EFICACIA_VERIFICADA)
    eficacia_verificada_em: datetime | None
    eficacia_verificada_por_user_id: UUID | None

    # Responsavel (P-CAL-A2 — UUID ≤90d + hash sempre)
    responsavel_acao_user_id: UUID | None
    responsavel_acao_user_id_hash: str  # NOT NULL (default "" so apos pseudonimizacao)

    # Decisao continuar/parar (cl. 7.10.1/2 + INV-CAL-NC-002)
    decisao_continuar_ou_parar: DecisaoContinuarOuParar

    # Notificacao cliente (INV-CAL-NC-003 quando PARAR_TRABALHO)
    cliente_notificado_em: datetime | None
    cliente_notificado_via: ClienteNotificadoVia | None
    cliente_notificado_documento_id: UUID | None

    # Autorizacao de retomada (apos PARAR_TRABALHO -> CONTINUAR_COM_CONTROLE)
    autorizacao_retomada_user_id: UUID | None
    autorizacao_retomada_em: datetime | None

    # Auditoria
    correlation_id: UUID


@dataclass(frozen=True, slots=True)
class ReclamacaoCalibracaoSnapshot:
    """Snapshot de ReclamacaoCalibracao (US-CAL-018 + cl. 7.9 + CDC art. 26).

    Estado-maquina: RECEBIDA -> EM_ANALISE -> RESPONDIDA / ARQUIVADA.

    Imutaveis pos-INSERT: calibracao_id, certificado_id, cliente_referencia_hash,
    relato_canonicalizado, relato_hash, aberta_em.

    Resposta (resposta_canonicalizada + resposta_hash + decisao + respondida_em)
    preenchida em RESPONDIDA.

    CDC art. 26 (90d janela) eh checado pelo CALLER antes de invocar abrir.
    """

    id: UUID
    tenant_id: UUID
    calibracao_id: UUID  # FK Calibracao (a reclamacao sempre tem cal origem)
    certificado_id: UUID  # FK Certificado M5 (db_constraint=False)
    cliente_referencia_hash: str  # HashVersionado ADR-0064 + ADR-0032

    relato_canonicalizado: str  # >=100 chars + anti-PII
    relato_hash: str

    estado: EstadoReclamacao  # default RECEBIDA

    # Preenchidos em EM_ANALISE (atribuir_rt)
    rt_atribuido_user_id_hash: str  # default "" em RECEBIDA

    # Preenchidos em RESPONDIDA (responder)
    resposta_canonicalizada: str  # default "" em RECEBIDA / EM_ANALISE
    resposta_hash: str
    decisao: DecisaoReclamacao | None  # None ate RESPONDIDA

    aberta_em: datetime  # tz-aware
    prazo_resposta_dia_util: int  # default 15 (AC-CAL-018-3)
    respondida_em: datetime | None

    correlation_id: UUID


@dataclass(frozen=True, slots=True)
class AvaliacaoPeriodicaSubcontratadoSnapshot:
    """Avaliacao periodica anual de LaboratorioSubcontratado (cl. 6.6.2 + P-CAL-R5).

    1:N de LaboratorioSubcontratado — uma avaliacao por ciclo anual.
    Imutavel pos-INSERT (WORM trigger PG). Snapshot enxuto: campos que
    use cases + jobs atualmente consomem.

    Job `verificar_avaliacoes_subcontratados_vencendo` (T-CAL-115) consome
    `proxima_avaliacao_em` para alerta P2 30d antes de vencer.
    """

    id: UUID
    tenant_id: UUID
    laboratorio_id: UUID  # FK LaboratorioSubcontratado
    avaliado_em: datetime  # tz-aware
    score: Decimal  # 0-10 (cl. 6.6.2)
    decisao: DecisaoAvaliacaoSubcontratado
    proxima_avaliacao_em: datetime  # default avaliado_em + 12 meses
    correlation_id: UUID


@dataclass(frozen=True, slots=True)
class MedicaoControleSnapshot:
    """Medicao de controle de padrao metrologico (cl. 7.7.1 + P-CAL-R8 RBC).

    1:N de PadraoMetrologico — uma medicao por ponto+timestamp. Imutavel
    pos-INSERT (INV-CAL-WORM-001). Job `analisar_padrao_medicoes_controle`
    consome as ultimas 30 e roda Western Electric (4 regras) para detectar
    desvio sistematico.

    `regra_western_electric_violada` eh string ('' = nenhuma; valores em
    REGRAS_WESTERN_ELECTRIC_ACEITAS).
    """

    id: UUID
    tenant_id: UUID
    padrao_id: UUID
    grandeza: str
    valor_medido: Decimal
    valor_esperado: Decimal
    desvio: Decimal  # valor_medido - valor_esperado
    dentro_2sigma: bool
    dentro_3sigma: bool
    escore_z: Decimal | None  # NULL quando padrao sem incerteza_referencia
    regra_western_electric_violada: str  # '' = nenhuma
    executor_id_hash: str  # HashVersionado v<NN>$<base64>
    executado_em: datetime  # tz-aware
    correlation_id: UUID


@dataclass(frozen=True, slots=True)
class EventoDeCalibracaoSnapshot:
    """Snapshot WORM da trilha hash-chain por calibracao (OBS-CAL-01 conserto P5).

    Cobre os 23 tipos `TIPO_EVENTO_CALIBRACAO_CHOICES` declarados na migration
    0009. Persistencia atomica via use case `append_evento_calibracao` (ADR-0065
    advisory lock + ADR-0064 HMAC versionado). Cada elo encadeia no anterior
    via `evento_anterior_hash`; `evento_hash` cobre payload + anterior +
    tenant + occurred_at.

    sequencia_local + evento_hash sao OUTPUT do append (trigger PG popula
    sequencia_local; helper crypto calcula evento_hash dentro do lock).
    Caller passa snapshot SEM esses campos; recebe snapshot completo.
    """

    id: UUID
    tenant_id: UUID
    calibracao_id: UUID
    tipo: str  # uma das constantes TIPO_EVENTO_CALIBRACAO_CHOICES
    payload_sanitizado: dict[str, object]
    actor_user_id: UUID
    actor_user_id_hash: str  # HashVersionado v<NN>$<base64>
    occurred_at: datetime  # tz-aware
    correlation_id: UUID
    causation_id: UUID | None
    # Campos abaixo populados pelo append (None na entrada):
    sequencia_local: int | None = None  # trigger PG seta MAX+1
    evento_anterior_hash: str = ""  # vazio = primeiro elo
    evento_hash: str = ""  # HashVersionado calculado dentro do advisory lock
