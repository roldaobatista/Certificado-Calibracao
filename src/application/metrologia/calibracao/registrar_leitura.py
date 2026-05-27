"""Use case `registrar_leitura` (P4 Fase 5 Batch C — T-CAL-085).

INSERT em Leitura (1:N de Calibracao). Calibracao precisa estar em
EM_EXECUCAO (INV-CAL-WORM-001). UNIQUE composto
(tenant, calibracao, ponto, repeticao) garante idempotencia forte —
violacao = ConflitoLeituraExistente (caller retorna 409).

Idempotencia sync mobile (ADR-0027):
- Se Input.client_event_id NOT NULL e ja existe leitura com mesmo
  client_event_id na calibracao: retorna leitura existente (HTTP 200
  idempotente, nao 201).
- Se nao existe: INSERT normal; UNIQUE parcial garante atomicidade.

INV-CAL-FRAUDE-EXEC-001: executor_id_hash (HashVersionado) substitui
UUID cru — anti-stalking pos retencao 25a. Caller calcula hash a partir
do request.user.id via helpers/crypto KMS antes de chamar.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4

from src.application.metrologia.calibracao.configurar_calibracao import (
    CalibracaoNaoEncontrada,
)
from src.domain.metrologia.calibracao.entities import LeituraSnapshot, OrigemLeitura
from src.domain.metrologia.calibracao.enums import EstadoCalibracao
from src.domain.metrologia.calibracao.repository import (
    CalibracaoRepository,
    LeituraRepository,
)


class EstadoInvalidoParaRegistrarLeitura(Exception):
    """Calibracao nao esta em EM_EXECUCAO — caller retorna 409 Conflict."""


class ConflitoLeituraExistente(Exception):
    """UNIQUE (tenant, calibracao, ponto, repeticao) violado — caller 409.

    Carrega a leitura existente pra caller poder retornar 409 com link.
    """

    def __init__(self, leitura_existente: LeituraSnapshot) -> None:
        self.leitura_existente = leitura_existente
        super().__init__(
            f"ConflitoLeituraExistente calibracao_id={leitura_existente.calibracao_id} "
            f"ponto={leitura_existente.ponto_calibracao} "
            f"repeticao={leitura_existente.numero_repeticao}"
        )


class IdempotencyPayloadMismatch(Exception):
    """INV-CAL-IDEMP-001 (IDEMP-CAL-03 1a passada Familia 5 2026-05-27):
    `client_event_id` reusado com payload divergente. Caller retorna 422.

    Carrega a leitura existente (snapshot armazenado) + um descritor do
    diff pra debug do cliente — sem expor PII.
    """

    def __init__(
        self,
        leitura_existente: LeituraSnapshot,
        campos_divergentes: tuple[str, ...],
    ) -> None:
        self.leitura_existente = leitura_existente
        self.campos_divergentes = campos_divergentes
        super().__init__(
            f"IdempotencyPayloadMismatch leitura_id={leitura_existente.id} "
            f"client_event_id={leitura_existente.client_event_id} "
            f"campos_divergentes={list(campos_divergentes)} — INV-CAL-IDEMP-001"
        )


@dataclass(frozen=True, slots=True)
class RegistrarLeituraInput:
    """Payload de registro de leitura individual."""

    calibracao_id: UUID
    ponto_calibracao: Decimal
    numero_repeticao: int  # 1..N
    valor_lido: Decimal
    unidade: str
    origem: OrigemLeitura
    timestamp: datetime  # UTC-aware
    executor_id_hash: str  # HashVersionado v<NN>$<base64>
    correlation_id: UUID
    client_event_id: UUID | None = None  # ADR-0027 sync mobile

    def __post_init__(self) -> None:
        if not isinstance(self.ponto_calibracao, Decimal):
            raise TypeError(
                f"ponto_calibracao deve ser Decimal "
                f"(achou {type(self.ponto_calibracao).__name__}) — INV-CAL-INC-003"
            )
        if not isinstance(self.valor_lido, Decimal):
            raise TypeError(
                f"valor_lido deve ser Decimal "
                f"(achou {type(self.valor_lido).__name__}) — INV-CAL-INC-003"
            )
        if self.numero_repeticao < 1:
            raise ValueError(
                f"numero_repeticao >= 1 ({self.numero_repeticao}); "
                f"primeira leitura comeca em 1"
            )
        if self.timestamp.tzinfo is None:
            raise ValueError(
                "registrar_leitura: timestamp exige datetime tz-aware (INV-VIG-004)"
            )
        if not self.executor_id_hash:
            raise ValueError(
                "registrar_leitura: executor_id_hash obrigatorio "
                "(INV-CAL-FRAUDE-EXEC-001 + ADR-0064)"
            )
        if not self.unidade:
            raise ValueError("registrar_leitura: unidade nao pode ser vazia")


@dataclass(frozen=True, slots=True)
class RegistrarLeituraOutput:
    snapshot: LeituraSnapshot
    idempotente: bool  # True quando reuso de client_event_id existente


def executar(
    inp: RegistrarLeituraInput,
    calibracao_repo: CalibracaoRepository,
    leitura_repo: LeituraRepository,
) -> RegistrarLeituraOutput:
    """Registra leitura em Calibracao EM_EXECUCAO com idempotencia client_event.

    Caller precisa garantir que calibracao_id pertence ao tenant ativo
    (RLS ja filtra; obter_por_id retorna None se cross-tenant).

    Fluxo:
      1. Carrega Calibracao para validar estado EM_EXECUCAO.
      2. Se client_event_id != None: chama obter_por_client_event;
         se ja existir, retorna idempotente=True.
      3. Insere via salvar_nova.
      4. Retorna snapshot novo (idempotente=False).
    """
    calibracao = calibracao_repo.obter_por_id(inp.calibracao_id)
    if calibracao is None:
        raise CalibracaoNaoEncontrada(str(inp.calibracao_id))

    if calibracao.status != EstadoCalibracao.EM_EXECUCAO:
        raise EstadoInvalidoParaRegistrarLeitura(
            f"status atual={calibracao.status.value}; registrar_leitura exige "
            f"EM_EXECUCAO (INV-CAL-WORM-001)"
        )

    # Idempotencia sync mobile (ADR-0027 + INV-CAL-IDEMP-001).
    # IDEMP-CAL-03 (2026-05-27): mismatch payload no replay com mesmo
    # client_event_id => 422 IdempotencyPayloadMismatch (em vez de silent
    # stale read antes do conserto).
    if inp.client_event_id is not None:
        existente = leitura_repo.obter_por_client_event(
            tenant_id=calibracao.tenant_id,
            calibracao_id=inp.calibracao_id,
            client_event_id=inp.client_event_id,
        )
        if existente is not None:
            divergentes: list[str] = []
            if existente.ponto_calibracao != inp.ponto_calibracao:
                divergentes.append("ponto_calibracao")
            if existente.numero_repeticao != inp.numero_repeticao:
                divergentes.append("numero_repeticao")
            if existente.valor_lido != inp.valor_lido:
                divergentes.append("valor_lido")
            if existente.unidade != inp.unidade:
                divergentes.append("unidade")
            if existente.origem != inp.origem:
                divergentes.append("origem")
            if existente.executor_id_hash != inp.executor_id_hash:
                divergentes.append("executor_id_hash")
            if divergentes:
                raise IdempotencyPayloadMismatch(existente, tuple(divergentes))
            return RegistrarLeituraOutput(snapshot=existente, idempotente=True)

    snapshot = LeituraSnapshot(
        id=uuid4(),
        tenant_id=calibracao.tenant_id,
        calibracao_id=inp.calibracao_id,
        ponto_calibracao=inp.ponto_calibracao,
        numero_repeticao=inp.numero_repeticao,
        valor_lido=inp.valor_lido,
        unidade=inp.unidade,
        origem=inp.origem,
        timestamp=inp.timestamp,
        executor_id_hash=inp.executor_id_hash,
        client_event_id=inp.client_event_id,
        correlation_id=inp.correlation_id,
    )

    leitura_repo.salvar_nova(snapshot)
    return RegistrarLeituraOutput(snapshot=snapshot, idempotente=False)
