"""Use case `configurar_calibracao` — US-CAL-002 (P4 Fase 5 Batch B — T-CAL-082).

Transicao RECEPCIONADA -> CONFIGURADA. Crava:
  - procedimento_id + procedimento_versao_snapshot (cl. 7.2).
  - regra_decisao + acordo cliente (ADR-0024 + cl. 7.1.3 + INV-CAL-DEC-006).
  - escopo_id (RBC) ou NULL (NAO_RBC).
  - analise_critica_pedido_id (origem=ATIVIDADE_OS) OU
    analise_critica_pedido_inline_hash + capacidade_tecnica_confirmada_por_user_id
    (origem=AVULSA + cl. 7.1.1 INV-CAL-ANAL-001).

Concorrencia (ADR-0065 + INV-CAL-CONC-003): UPDATE atomico via
repo.atualizar_com_lock(snapshot, revision_anterior). Se race perdida
(rowcount=0), levanta ConflitoVersao — caller decide retry vs 409.

Predicates ABAC ja registrados na Fase 4 (apps.py ready()):
  - cmc_cobre (escopo: calibracao.configurar + iniciar_leituras)
  - procedimento_vigente_para (escopo: calibracao.configurar)
Caller chama AuthorizationProvider.can('calibracao.configurar', resource={
    tenant_id, tipo_acreditacao, grandeza, data, ...
}) ANTES de invocar este use case. Use case nao re-chama provider.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime
from uuid import UUID

from src.domain.metrologia.calibracao.entities import CalibracaoSnapshot
from src.domain.metrologia.calibracao.enums import (
    EstadoCalibracao,
    OrigemRecepcao,
    RegraDecisao,
    TipoAcreditacao,
)
from src.domain.metrologia.calibracao.repository import CalibracaoRepository


class CalibracaoNaoEncontrada(Exception):
    """ID nao existe no tenant ativo (RLS ja filtrou) — caller retorna 404."""


class EstadoInvalidoParaConfigurar(Exception):
    """Calibracao nao esta em RECEPCIONADA — caller retorna 409 Conflict."""


class ConflitoVersaoCalibracao(Exception):
    """CAS perdeu race — outro update concorrente. Caller decide retry/409.

    INV-CAL-CONC-003 + ADR-0065. Carrega snapshot ATUAL (depois do race)
    para caller eventualmente recomputar e re-tentar.
    """

    def __init__(self, snapshot_atual: CalibracaoSnapshot) -> None:
        self.snapshot_atual = snapshot_atual
        super().__init__(
            f"ConflitoVersao calibracao_id={snapshot_atual.id} "
            f"revision_atual={snapshot_atual.revision}"
        )


@dataclass(frozen=True, slots=True)
class ConfigurarCalibracaoInput:
    """Payload de configuracao (transicao RECEPCIONADA -> CONFIGURADA)."""

    calibracao_id: UUID
    revision_esperada: int  # CAS: deve bater com snapshot.revision atual
    # Procedimento (cl. 7.2)
    procedimento_id: UUID
    procedimento_versao_snapshot: dict[str, object]  # {codigo, versao, hash_anexo}
    # Regra de decisao (ADR-0024 + cl. 7.1.3)
    regra_decisao: RegraDecisao
    regra_decisao_acordada_em: datetime
    regra_decisao_acordada_documento_id: UUID  # FK AceiteRegraDecisao
    # Escopo CMC (NULL se NAO_RBC)
    escopo_id: UUID | None
    # Analise critica (cl. 7.1.1 — uma das duas formas eh obrigatoria)
    analise_critica_pedido_id: UUID | None  # quando origem=ATIVIDADE_OS
    analise_critica_pedido_inline_hash: str  # quando origem=AVULSA (>=10 chars)
    capacidade_tecnica_confirmada_por_user_id: UUID | None  # avulsa: obrigatorio

    def __post_init__(self) -> None:
        if self.regra_decisao_acordada_em.tzinfo is None:
            raise ValueError(
                "configurar_calibracao: regra_decisao_acordada_em exige "
                "datetime tz-aware (INV-VIG-004)"
            )
        # procedimento_versao_snapshot precisa ter os 3 campos canonicos
        chaves_obrigatorias = {"codigo", "versao", "hash_anexo"}
        if not chaves_obrigatorias.issubset(self.procedimento_versao_snapshot.keys()):
            raise ValueError(
                f"configurar_calibracao: procedimento_versao_snapshot deve ter "
                f"{sorted(chaves_obrigatorias)} (achou "
                f"{sorted(self.procedimento_versao_snapshot.keys())})"
            )


@dataclass(frozen=True, slots=True)
class ConfigurarCalibracaoOutput:
    snapshot: CalibracaoSnapshot


def executar(
    inp: ConfigurarCalibracaoInput,
    repo: CalibracaoRepository,
) -> ConfigurarCalibracaoOutput:
    """Configura calibracao: RECEPCIONADA -> CONFIGURADA via CAS.

    Levanta:
      CalibracaoNaoEncontrada — id nao existe.
      EstadoInvalidoParaConfigurar — status != RECEPCIONADA.
      ValueError — analise critica inconsistente com origem (ADR-0023)
        OU RBC sem escopo_id OU regra_decisao_acordada_documento_id ausente.
      ConflitoVersaoCalibracao — CAS perdeu race.
    """
    atual = repo.obter_por_id(inp.calibracao_id)
    if atual is None:
        raise CalibracaoNaoEncontrada(str(inp.calibracao_id))

    if atual.status != EstadoCalibracao.RECEPCIONADA:
        raise EstadoInvalidoParaConfigurar(
            f"status atual={atual.status.value}; configurar exige RECEPCIONADA "
            f"(INV-CAL-WORM-001)"
        )

    # ADR-0023: analise critica consistente com origem
    if atual.origem_recepcao == OrigemRecepcao.ATIVIDADE_OS:
        if inp.analise_critica_pedido_id is None:
            raise ValueError(
                "configurar_calibracao: origem=ATIVIDADE_OS exige "
                "analise_critica_pedido_id (cl. 7.1.1 + ADR-0023)"
            )
        if inp.analise_critica_pedido_inline_hash:
            raise ValueError(
                "configurar_calibracao: origem=ATIVIDADE_OS proibe inline_hash "
                "(analise critica fica no orcamento)"
            )
    else:  # OrigemRecepcao.AVULSA
        if not inp.analise_critica_pedido_inline_hash:
            raise ValueError(
                "configurar_calibracao: origem=AVULSA exige "
                "analise_critica_pedido_inline_hash (cl. 7.1.1 + INV-CAL-ANAL-001)"
            )
        if inp.capacidade_tecnica_confirmada_por_user_id is None:
            raise ValueError(
                "configurar_calibracao: origem=AVULSA exige "
                "capacidade_tecnica_confirmada_por_user_id (cl. 7.1.1)"
            )
        if inp.analise_critica_pedido_id is not None:
            raise ValueError(
                "configurar_calibracao: origem=AVULSA proibe "
                "analise_critica_pedido_id (FK orcamento — ADR-0023)"
            )

    # RBC: escopo_id obrigatorio (INV-CAL-CMC-001 — CMC vinculado a escopo)
    if atual.tipo_acreditacao == TipoAcreditacao.RBC and inp.escopo_id is None:
        raise ValueError(
            "configurar_calibracao: tipo_acreditacao=RBC exige escopo_id NOT NULL "
            "(INV-CAL-CMC-001 + cl. 6.4.10)"
        )

    # Snapshot novo (frozen — usa replace pra trocar campos)
    novo = replace(
        atual,
        status=EstadoCalibracao.CONFIGURADA,
        revision=atual.revision + 1,
        regra_decisao=inp.regra_decisao,
        regra_decisao_acordada_em=inp.regra_decisao_acordada_em,
        regra_decisao_acordada_documento_id=inp.regra_decisao_acordada_documento_id,
        procedimento_id=inp.procedimento_id,
        procedimento_versao_snapshot=inp.procedimento_versao_snapshot,
        escopo_id=inp.escopo_id,
        analise_critica_pedido_id=inp.analise_critica_pedido_id,
        analise_critica_pedido_inline_hash=inp.analise_critica_pedido_inline_hash,
        capacidade_tecnica_confirmada_por_user_id=inp.capacidade_tecnica_confirmada_por_user_id,
    )

    # CAS atomico (ADR-0065)
    ok = repo.atualizar_com_lock(novo, inp.revision_esperada)
    if not ok:
        # Reload pra entregar snapshot atualizado pra caller decidir retry
        atualizado = repo.obter_por_id(inp.calibracao_id)
        # Se snapshot sumiu (concorrente deletou? cenario impossivel mas defensivo):
        snapshot_para_excecao = atualizado if atualizado is not None else atual
        raise ConflitoVersaoCalibracao(snapshot_para_excecao)

    return ConfigurarCalibracaoOutput(snapshot=novo)
