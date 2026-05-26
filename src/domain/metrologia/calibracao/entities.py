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

from .enums import EstadoCalibracao, OrigemRecepcao, RegraDecisao, TipoAcreditacao
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

    # Auditoria forense (correlation + causation cross-marco)
    correlation_id: UUID
    causation_id: UUID | None  # nova calibracao apos rejeicao/recall (US-CAL-007)
    criada_em: datetime  # auto_now_add no PG
    criada_por_user_id: UUID | None


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
