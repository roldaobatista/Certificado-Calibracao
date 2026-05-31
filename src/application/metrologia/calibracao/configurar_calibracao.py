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

import logging
from dataclasses import dataclass, replace
from datetime import datetime
from decimal import Decimal
from typing import Protocol, runtime_checkable
from uuid import UUID

from src.domain.metrologia.calibracao.entities import CalibracaoSnapshot
from src.domain.metrologia.calibracao.enums import (
    EstadoCalibracao,
    OrigemRecepcao,
    RegraDecisao,
    TipoAcreditacao,
)
from src.domain.metrologia.calibracao.repository import CalibracaoRepository
from src.domain.metrologia.value_objects import FaixaMedicao, Grandeza

log = logging.getLogger(__name__)


@runtime_checkable
class CoberturaEscopoPort(Protocol):
    """Porta de cobertura de escopo CMC (ADR-0073/0074 cond. 1 — contenção total).

    Implementada como FUNCAO DE MODULO sem estado (TL-C-04 / ADR-0073 ponto 4):
    `src.infrastructure.metrologia.escopos_cmc.query_service.cobre`. A view injeta
    o adapter REAL; o use case NUNCA importa infra (ADR-0007). Retorna (True, '')
    se algum escopo CONFIRMADO vigente em `data` CONTEM a faixa solicitada; senao
    (False, reason). Fail-CLOSED na implementacao real.
    """

    def __call__(
        self,
        *,
        tenant_id: UUID,
        grandeza: str,
        faixa_min: Decimal | str,
        faixa_max: Decimal | str,
        unidade: str,
        data: datetime,
    ) -> tuple[bool, str]: ...


def _cobertura_fail_open_lazy(
    *,
    tenant_id: UUID,
    grandeza: str,
    faixa_min: Decimal | str,
    faixa_max: Decimal | str,
    unidade: str,
    data: datetime,
) -> tuple[bool, str]:
    """STUB default da porta — fail-open lazy (ADR-0066, transicao etapa 1 T-ECMC-046).

    Usado quando NENHUM adapter real e injetado (ex.: testes de use case puro que
    nao exercem cobertura). Em producao a view injeta o adapter REAL
    (`escopos_cmc.query_service.cobre`). Distinto do fail-open por AUSENCIA de
    grandeza/faixa (decidido no corpo do use case — GATE-CAL-CMC-PREDICATE).
    """
    return True, ""


@runtime_checkable
class CoberturaProcedimentoPort(Protocol):
    """Porta de procedimento tecnico vigente (M7 — ADR-0073 / cl. 7.2.1).

    Funcao de modulo `procedimentos_calibracao.query_service.cobre_procedimento`.
    A view injeta o adapter REAL; o use case NUNCA importa infra (ADR-0007).
    Retorna `(True, resolvido)` quando ha procedimento PUBLICADO vigente em `data`
    que CONTEM a faixa (resolvido = dict {procedimento_id, codigo, versao,
    numero_revisao, hash_anexo} para preencher o snapshot real, ou None no STUB
    lazy); `(False, None)` quando nenhum cobre (RBC -> 412). So consultada se RBC.
    """

    def __call__(
        self,
        *,
        tenant_id: UUID,
        grandeza: str,
        faixa_min: Decimal | str,
        faixa_max: Decimal | str,
        unidade: str,
        data: datetime,
    ) -> tuple[bool, dict[str, str] | None]: ...


def _procedimento_fail_open_lazy(
    *,
    tenant_id: UUID,
    grandeza: str,
    faixa_min: Decimal | str,
    faixa_max: Decimal | str,
    unidade: str,
    data: datetime,
) -> tuple[bool, dict[str, str] | None]:
    """STUB default da 2a porta — fail-open lazy (paralelo ADR-0066 / T-PROC-040).

    `(True, None)`: nao bloqueia E mantem o procedimento do input (legado M4). Em
    producao a view injeta o adapter REAL (`procedimentos_calibracao.query_service.
    cobre_procedimento`), que resolve o procedimento vigente server-side ou bloqueia
    (GATE-CAL-PROC-VIGENTE-PREDICATE).
    """
    return True, None


class CalibracaoNaoEncontrada(Exception):
    """ID nao existe no tenant ativo (RLS ja filtrou) — caller retorna 404."""


class EstadoInvalidoParaConfigurar(Exception):
    """Calibracao nao esta em RECEPCIONADA — caller retorna 409 Conflict."""


class EscopoNaoCobreFaixa(Exception):
    """RBC: nenhum escopo CMC CONFIRMADO vigente cobre a grandeza+faixa solicitada.

    ADR-0073/0074 cond. 1 (contencao total). Caller (view) retorna 412. Carrega
    grandeza/faixa/motivo para a mensagem com contexto metrologico.
    """

    def __init__(
        self,
        grandeza: str,
        faixa_min: str,
        faixa_max: str,
        unidade: str,
        motivo: str,
    ) -> None:
        self.grandeza = grandeza
        self.faixa_min = faixa_min
        self.faixa_max = faixa_max
        self.unidade = unidade
        self.motivo = motivo
        super().__init__(
            f"EscopoNaoCobreFaixa grandeza={grandeza} "
            f"faixa=[{faixa_min},{faixa_max}]{unidade} motivo={motivo}"
        )


class ProcedimentoVigenteAusente(Exception):
    """RBC: nenhum ProcedimentoCalibracao PUBLICADO vigente cobre a grandeza+faixa.

    cl. 7.2.1 (procedimento documentado controlado) — erro de dominio DISTINTO de
    EscopoNaoCobreFaixa (escopo = fraude de acreditacao; procedimento = lacuna de
    metodo). Caller (view) retorna 412. M7 GATE-CAL-PROC-VIGENTE-PREDICATE.
    """

    def __init__(
        self,
        grandeza: str,
        faixa_min: str,
        faixa_max: str,
        unidade: str,
        motivo: str,
    ) -> None:
        self.grandeza = grandeza
        self.faixa_min = faixa_min
        self.faixa_max = faixa_max
        self.unidade = unidade
        self.motivo = motivo
        super().__init__(
            f"ProcedimentoVigenteAusente grandeza={grandeza} "
            f"faixa=[{faixa_min},{faixa_max}]{unidade} motivo={motivo}"
        )


def _declarar_faixa(
    inp: ConfigurarCalibracaoInput,
) -> tuple[Grandeza | None, FaixaMedicao | None]:
    """Constroi os VOs `(Grandeza, FaixaMedicao)` da faixa calibrada DECLARADA pelo
    RT na configuracao (ADR-0076). Fonte UNICA (NC-05 — sem ler snapshot_equipamento_json).

    - Nada declarado -> (None, None).
    - Declaracao PARCIAL (ex.: grandeza sem faixa) -> ValueError (atomico: tudo ou nada).
    - Declaracao completa -> VOs validados (Grandeza.from_string + FaixaMedicao
      validam vocabulario/unidade/inferior<superior server-side).
    """
    tem_algo = (
        bool(inp.grandeza_calibrada)
        or inp.faixa_calibrada_min is not None
        or inp.faixa_calibrada_max is not None
        or bool(inp.unidade_calibrada)
    )
    if not tem_algo:
        return None, None
    completo = (
        bool(inp.grandeza_calibrada)
        and inp.faixa_calibrada_min is not None
        and inp.faixa_calibrada_max is not None
        and bool(inp.unidade_calibrada)
    )
    if not completo:
        raise ValueError(
            "configurar_calibracao: faixa calibrada declarada exige grandeza + "
            "faixa_min + faixa_max + unidade JUNTOS (ADR-0076)"
        )
    # `completo` ja garante non-None — estreita pro type checker.
    assert inp.faixa_calibrada_min is not None
    assert inp.faixa_calibrada_max is not None
    return (
        Grandeza.from_string(inp.grandeza_calibrada),
        FaixaMedicao(
            inp.faixa_calibrada_min,
            inp.faixa_calibrada_max,
            inp.unidade_calibrada,
        ),
    )


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
    # Faixa calibrada declarada (ADR-0076) — RT declara; obrigatoria em RBC.
    # Primitivos (serializer fornece); use case constroi os VOs em _declarar_faixa.
    # Default vazio/None: NAO_RBC pode omitir; tudo-ou-nada (declaracao parcial = erro).
    grandeza_calibrada: str = ""
    faixa_calibrada_min: Decimal | None = None
    faixa_calibrada_max: Decimal | None = None
    unidade_calibrada: str = ""

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
    cobertura: CoberturaEscopoPort = _cobertura_fail_open_lazy,
    procedimento: CoberturaProcedimentoPort = _procedimento_fail_open_lazy,
) -> ConfigurarCalibracaoOutput:
    """Configura calibracao: RECEPCIONADA -> CONFIGURADA via CAS.

    `cobertura` (ADR-0073): porta de cobertura de escopo CMC injetada pela view
    (`escopos_cmc.query_service.cobre`). Default fail-open lazy para testes de
    use case puro. So consultada quando tipo_acreditacao=RBC.

    Levanta:
      CalibracaoNaoEncontrada — id nao existe.
      EstadoInvalidoParaConfigurar — status != RECEPCIONADA.
      ValueError — analise critica inconsistente com origem (ADR-0023)
        OU RBC sem escopo_id OU regra_decisao_acordada_documento_id ausente.
      EscopoNaoCobreFaixa — RBC + faixa fora de qualquer escopo CMC vigente (412).
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

    # ADR-0076: faixa calibrada declarada pelo RT (fonte UNICA — server-side
    # validada pelos VOs). RBC = portao obrigatorio fail-CLOSED: declarada DEVE
    # existir E estar contida em escopo CMC acreditado vigente (cobre()).
    # NAO_RBC: declaracao opcional, nunca bloqueia (ADR-0075 — aviso suave fica
    # na borda de apresentacao, nao aqui).
    grandeza_decl, faixa_decl = _declarar_faixa(inp)
    if atual.tipo_acreditacao == TipoAcreditacao.RBC:
        if grandeza_decl is None or faixa_decl is None:
            raise ValueError(
                "configurar_calibracao: tipo_acreditacao=RBC exige faixa calibrada "
                "declarada (grandeza + faixa + unidade) — ADR-0076 + "
                "GATE-CAL-CMC-PREDICATE"
            )
        # ADR-0073/0074 cond. 1: cobertura validada DENTRO do use case (porta
        # injetada), contra o ESCOPO acreditado (teto regulatorio — ADR-0076),
        # nao a capacidade do instrumento.
        ok, motivo = cobertura(
            tenant_id=atual.tenant_id,
            grandeza=grandeza_decl.value,
            faixa_min=faixa_decl.inferior,
            faixa_max=faixa_decl.superior,
            unidade=faixa_decl.unidade,
            data=inp.regra_decisao_acordada_em,
        )
        if not ok:
            raise EscopoNaoCobreFaixa(
                grandeza_decl.value,
                str(faixa_decl.inferior),
                str(faixa_decl.superior),
                faixa_decl.unidade,
                motivo,
            )

    # M7 (ADR-0073 / cl. 7.2.1): 2o portao na MESMA transicao, DEPOIS do escopo
    # (ordem escopo->procedimento, 1a falha interrompe). So RBC. Resolve o
    # procedimento PUBLICADO vigente server-side (porta injetada) e preenche o
    # snapshot real; None -> 412 ProcedimentoVigenteAusente (GATE-CAL-PROC-VIGENTE).
    proc_id_final = inp.procedimento_id
    proc_snap_final = inp.procedimento_versao_snapshot
    if atual.tipo_acreditacao == TipoAcreditacao.RBC:
        assert grandeza_decl is not None and faixa_decl is not None  # garantido acima
        proc_ok, proc_resolvido = procedimento(
            tenant_id=atual.tenant_id,
            grandeza=grandeza_decl.value,
            faixa_min=faixa_decl.inferior,
            faixa_max=faixa_decl.superior,
            unidade=faixa_decl.unidade,
            data=inp.regra_decisao_acordada_em,
        )
        if not proc_ok:
            raise ProcedimentoVigenteAusente(
                grandeza_decl.value,
                str(faixa_decl.inferior),
                str(faixa_decl.superior),
                faixa_decl.unidade,
                "procedimento_inexistente",
            )
        # Adapter real resolveu o procedimento vigente -> preenche o snapshot real
        # (server-side, nao do payload — C-1). STUB lazy retorna None -> mantem input.
        if proc_resolvido is not None:
            proc_id_final = UUID(proc_resolvido["procedimento_id"])
            proc_snap_final = {
                "codigo": proc_resolvido["codigo"],
                "versao": proc_resolvido["versao"],
                "numero_revisao": proc_resolvido["numero_revisao"],
                "hash_anexo": proc_resolvido["hash_anexo"],
            }

    # Snapshot novo (frozen — usa replace pra trocar campos)
    novo = replace(
        atual,
        status=EstadoCalibracao.CONFIGURADA,
        revision=atual.revision + 1,
        regra_decisao=inp.regra_decisao,
        regra_decisao_acordada_em=inp.regra_decisao_acordada_em,
        regra_decisao_acordada_documento_id=inp.regra_decisao_acordada_documento_id,
        procedimento_id=proc_id_final,
        procedimento_versao_snapshot=proc_snap_final,
        escopo_id=inp.escopo_id,
        analise_critica_pedido_id=inp.analise_critica_pedido_id,
        analise_critica_pedido_inline_hash=inp.analise_critica_pedido_inline_hash,
        capacidade_tecnica_confirmada_por_user_id=inp.capacidade_tecnica_confirmada_por_user_id,
        grandeza_calibrada=grandeza_decl,
        faixa_calibrada_declarada=faixa_decl,
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
