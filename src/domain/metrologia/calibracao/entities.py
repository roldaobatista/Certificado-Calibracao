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
from uuid import UUID

from .enums import EstadoCalibracao, OrigemRecepcao, RegraDecisao, TipoAcreditacao


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

    # Auditoria forense (correlation + causation cross-marco)
    correlation_id: UUID
    causation_id: UUID | None  # nova calibracao apos rejeicao/recall (US-CAL-007)
    criada_em: datetime  # auto_now_add no PG
    criada_por_user_id: UUID | None
