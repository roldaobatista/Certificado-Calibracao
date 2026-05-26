"""Use case `criar_calibracao` — US-CAL-001 (P4 Fase 5 Batch A — T-CAL-077).

Cobre 2 cenarios de origem (ADR-0023):
  - ATIVIDADE_OS: chamado pelo consumer de evento `Atividade.Criada` quando
    tipo=calibracao. atividade_os_id NOT NULL; cliente_id herdado da OS.
  - AVULSA: recepcao direta de item pra calibracao sem OS por tras
    (US-CAL-001 happy path). Atendente/metrologista cria via portal interno.

Use case PURO:
- Recebe Input frozen + Repository Protocol + correlation_id.
- Reserva proximo numero_interno via repo.proximo_numero_interno().
- Monta CalibracaoSnapshot inicial em estado RECEPCIONADA com defaults PG.
- Salva via repo.salvar_nova().
- Retorna Output frozen com snapshot novo.

NAO chama AuthorizationProvider aqui — checagem authz ocorre no caller
(view ou consumer) ANTES de invocar este use case. Motivo: use case puro
nao deve depender de provider; mantemos separacao caller=guard,
use_case=transacao.

Invariantes:
- INV-CAL-WORM-001: snapshot inicia em RECEPCIONADA + revision=0.
- INV-CAL-CONF-001: estado inicial NAO eh CONFIGURADA — configuracao
  acontece em use case separado (configurar_calibracao US-CAL-002).
- ADR-0023: origem_recepcao + atividade_os_id mutuamente consistentes.
- ADR-0032: cliente_referencia_hash sempre presente; cliente_id pode ser
  NULL apos anonimizacao.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID, uuid4

from src.domain.metrologia.calibracao.entities import CalibracaoSnapshot
from src.domain.metrologia.calibracao.enums import (
    EstadoCalibracao,
    OrigemRecepcao,
    RegraDecisao,
    TipoAcreditacao,
)
from src.domain.metrologia.calibracao.repository import CalibracaoRepository


@dataclass(frozen=True, slots=True)
class CriarCalibracaoInput:
    """Payload de criacao (recepcao avulsa OU plugada em OS)."""

    tenant_id: UUID
    origem_recepcao: OrigemRecepcao
    atividade_os_id: UUID | None
    instrumento_id: UUID
    snapshot_equipamento_json: dict[str, object]
    cliente_id: UUID | None
    cliente_referencia_hash: str
    cliente_key_id: str
    tipo_acreditacao: TipoAcreditacao
    recepcionada_em: datetime
    correlation_id: UUID
    criada_por_user_id: UUID | None = None
    causation_id: UUID | None = None

    def __post_init__(self) -> None:
        # ADR-0023: origem_recepcao e atividade_os_id coerentes
        if self.origem_recepcao == OrigemRecepcao.ATIVIDADE_OS:
            if self.atividade_os_id is None:
                raise ValueError(
                    "criar_calibracao: origem=ATIVIDADE_OS exige "
                    "atividade_os_id NOT NULL (ADR-0023)"
                )
        elif self.atividade_os_id is not None:
            raise ValueError(
                "criar_calibracao: origem=AVULSA proibe atividade_os_id "
                "(ADR-0023 — recepcao avulsa nao vincula a OS)"
            )
        # ADR-0032: hash sempre presente
        if not self.cliente_referencia_hash:
            raise ValueError(
                "criar_calibracao: cliente_referencia_hash obrigatorio "
                "(ADR-0032 — preserva audit pos-anonimizacao)"
            )
        if not self.cliente_key_id:
            raise ValueError(
                "criar_calibracao: cliente_key_id obrigatorio "
                "(ADR-0064 — referencia chave KMS)"
            )
        # INV-VIG-004
        if self.recepcionada_em.tzinfo is None:
            raise ValueError(
                "criar_calibracao: recepcionada_em exige datetime tz-aware "
                "(INV-VIG-004 — UTC obrigatorio)"
            )


@dataclass(frozen=True, slots=True)
class CriarCalibracaoOutput:
    """Resultado: snapshot persistido + numero alocado."""

    snapshot: CalibracaoSnapshot


def executar(
    inp: CriarCalibracaoInput,
    repo: CalibracaoRepository,
) -> CriarCalibracaoOutput:
    """Executa criacao da Calibracao em estado RECEPCIONADA."""
    numero_interno = repo.proximo_numero_interno()
    calibracao_id = uuid4()

    snapshot = CalibracaoSnapshot(
        id=calibracao_id,
        tenant_id=inp.tenant_id,
        numero_interno=numero_interno,
        numero_exibido="",  # GENERATED por trigger PG (migration 0003)
        origem_recepcao=inp.origem_recepcao,
        atividade_os_id=inp.atividade_os_id,
        instrumento_id=inp.instrumento_id,
        snapshot_equipamento_json=inp.snapshot_equipamento_json,
        cliente_id=inp.cliente_id,
        cliente_referencia_hash=inp.cliente_referencia_hash,
        cliente_key_id=inp.cliente_key_id,
        tipo_acreditacao=inp.tipo_acreditacao,
        status=EstadoCalibracao.RECEPCIONADA,
        revision=0,
        # Defaults PG na criacao — refletidos no snapshot pos-INSERT
        regra_decisao=RegraDecisao.ACEITACAO_SIMPLES,
        regra_decisao_acordada_em=None,
        regra_decisao_acordada_documento_id=None,
        versao_motor_calculo="",
        # Campos de configuracao — vazios em RECEPCIONADA; configurar_calibracao
        # US-CAL-002 preenche na transicao RECEPCIONADA -> CONFIGURADA.
        procedimento_id=None,
        procedimento_versao_snapshot={},
        escopo_id=None,
        analise_critica_pedido_id=None,
        analise_critica_pedido_inline_hash="",
        capacidade_tecnica_confirmada_por_user_id=None,
        # Atores cl. 6.2 — preenchidos em use cases posteriores
        executor_id=None,
        revisor_id=None,
        conferente_id=None,
        snapshot_competencia_revisor_json=None,
        snapshot_competencia_conferente_json=None,
        excecao_2a_conf_id=None,
        correlation_id=inp.correlation_id,
        causation_id=inp.causation_id,
        criada_em=inp.recepcionada_em,
        criada_por_user_id=inp.criada_por_user_id,
    )

    repo.salvar_nova(snapshot)
    return CriarCalibracaoOutput(snapshot=snapshot)
