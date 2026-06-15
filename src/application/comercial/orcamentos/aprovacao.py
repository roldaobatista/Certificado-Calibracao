"""Use case `aprovar_orcamento` — análise crítica cl. 7.1 + transição (T-ORC-033).

Onda 2c-2. Orquestra a função pura de decisão (``decidir_analise_critica``), a
persistência WORM da ``AnaliseCriticaOrcamento`` e a transição
``enviado→aprovado→aprovado_pendente_os`` (D-ORC-3), devolvendo o envelope
``orcamento.aprovado`` pronto para a view publicar (D-ORC-6).

Arquitetura (matriz §"Implementação"):
  - As PORTAS (escopos_cmc/procedimentos) e o PERFIL/suspensão são resolvidos na
    VIEW/infra (server-side) e chegam já materializados em ``resultados_itens`` +
    ``perfil`` + ``acreditacao_suspensa`` — este use case NÃO importa infra.
  - A publicação dos eventos de bus (``orcamento.aprovado`` /
    ``orcamento.analise_critica_reprovada`` / ``_com_ressalva``) é da VIEW, dentro
    do mesmo ``transaction.atomic`` (transactional outbox — molde Onda 2b).

Reprovada (perfil A fail-closed / A suspenso): grava a ``AnaliseCriticaOrcamento``
WORM, NÃO transiciona e devolve ``aprovado=False`` — a view publica
``orcamento.analise_critica_reprovada`` e retorna 422 (a transação COMMITA: o WORM
e o evento ficam gravados, o estado permanece ``enviado``).

A ``Aprovacao`` WORM (aceite rico LGPD + IP) é do canal PÚBLICO (T-ORC-038, Onda 2e);
o canal interno registra a autoria via ``avaliada_por`` (user_id) na análise (C5).

Caller (view) abre ``transaction.atomic``. Refs: spec §4/§6; D-ORC-5/6/14/15;
INV-ORC-CL71-001 / APROVADO-ENVELOPE / ANALISE-WORM; AC-ORC-007/009.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from src.application.comercial.orcamentos.ciclo_vida import OrcamentoNaoEncontrado
from src.domain.comercial.orcamentos.analise_critica import (
    NORMA_REFERENCIA_CL71,
    ResultadoItemMensurando,
    calcular_snapshot_hash_analise,
    decidir_analise_critica,
)
from src.domain.comercial.orcamentos.entities import AnaliseCriticaOrcamento, Orcamento
from src.domain.comercial.orcamentos.enums import (
    EstadoOrcamento,
    SeveridadeRessalva,
    VeredictoAnaliseCritica,
)
from src.domain.comercial.orcamentos.erros import EstadoInvalido, OrcamentoConvertido
from src.domain.comercial.orcamentos.repository import OrcamentoRepository
from src.domain.comercial.orcamentos.transicoes import (
    montar_envelope_orcamento_aprovado,
    validar_transicao,
)


@dataclass(frozen=True, slots=True)
class AprovarOrcamentoInput:
    """Entrada do use case — tudo já resolvido server-side pela view.

    ``avaliada_por``: interno = ``str(user_id)``; público = ``"SISTEMA/AUTO:<id>"`` (C5).
    ``criada_por_user_id``: aprovador interno (vai no envelope); None no público.
    """

    tenant_id: UUID
    orcamento_id: UUID
    perfil: str  # "A"|"B"|"C"|"D" (obter_perfil_tenant_corrente — server-side)
    acreditacao_suspensa: bool
    resultados_itens: Sequence[ResultadoItemMensurando]
    avaliada_por: str
    agora: datetime
    regra_decisao_acordada: str = ""
    criada_por_user_id: UUID | None = None


@dataclass(frozen=True, slots=True)
class AprovarOrcamentoOutput:
    """Resultado do use case.

    ``aprovado``: False quando ``veredito == reprovada`` (a view retorna 422). O
    ``envelope`` é None nesse caso (não publica ``orcamento.aprovado``).
    """

    orcamento: Orcamento
    analise: AnaliseCriticaOrcamento
    veredito: VeredictoAnaliseCritica
    severidade: SeveridadeRessalva | None
    aprovado: bool
    exige_confirmacao_ressalvas: bool
    envelope: dict[str, Any] | None


def aprovar_orcamento(
    inp: AprovarOrcamentoInput, *, repo: OrcamentoRepository
) -> AprovarOrcamentoOutput:
    """Avalia a análise crítica cl. 7.1, grava WORM e (se viável) aprova (D-ORC-5/6).

    Sempre grava ``AnaliseCriticaOrcamento`` (AJUSTE-1 — envelope sempre tem
    ``analise_critica_id``). Reprovada não transiciona (fail-closed perfil A).
    """
    orcamento = repo.get_by_id(inp.orcamento_id, tenant_id=inp.tenant_id)
    if orcamento is None:
        raise OrcamentoNaoEncontrado(
            f"orcamento {inp.orcamento_id} inexistente neste tenant.",
            orcamento_id=str(inp.orcamento_id),
        )
    if orcamento.estado == EstadoOrcamento.CONVERTIDO:
        raise OrcamentoConvertido(
            f"orcamento {inp.orcamento_id} ja convertido (INV-ORC-CONVERTIDO-TERMINAL).",
            orcamento_id=str(inp.orcamento_id),
        )
    # enviado -> aprovado (409 se o orçamento não está em 'enviado').
    validar_transicao(orcamento.estado, EstadoOrcamento.APROVADO)

    versao = repo.get_versao_ativa(inp.orcamento_id, tenant_id=inp.tenant_id)
    if versao is None:
        raise EstadoInvalido(
            f"orcamento {inp.orcamento_id} sem versao corrente — estado inconsistente.",
            orcamento_id=str(inp.orcamento_id),
        )
    itens = repo.listar_itens_versao(versao.id, tenant_id=inp.tenant_id)

    # 1) Decisão pura da matriz perfil-aware (levanta PerfilIndeterminado se "").
    decisao = decidir_analise_critica(
        perfil=inp.perfil,
        acreditacao_suspensa=inp.acreditacao_suspensa,
        resultados=inp.resultados_itens,
    )

    # 2) Snapshot hash ADR-0029 do registro probatório (carimbado no envelope).
    snapshot_hash = calcular_snapshot_hash_analise(
        orcamento_id=inp.orcamento_id,
        versao_id=versao.id,
        perfil=decisao.perfil_normalizado,
        veredito=decisao.veredito,
        norma_referencia=NORMA_REFERENCIA_CL71,
        itens_avaliados=decisao.itens_avaliados,
        avaliada_em=inp.agora,
        avaliada_por=inp.avaliada_por,
    )

    # 3) Grava AnaliseCriticaOrcamento WORM SEMPRE (AJUSTE-1 / INV-ORC-ANALISE-WORM).
    analise = repo.salvar_analise_critica(
        AnaliseCriticaOrcamento(
            id=uuid4(),
            orcamento_id=inp.orcamento_id,
            versao_id=versao.id,
            tenant_id=inp.tenant_id,
            perfil_no_evento=decisao.perfil_normalizado,
            veredito=decisao.veredito,
            norma_referencia=NORMA_REFERENCIA_CL71,
            itens_avaliados=decisao.itens_avaliados,
            snapshot_hash=snapshot_hash,
            avaliada_em=inp.agora,
            avaliada_por=inp.avaliada_por,
        )
    )

    # 4) Reprovada (fail-closed): não transiciona; a view publica reprovada + 422.
    if decisao.bloqueia:
        return AprovarOrcamentoOutput(
            orcamento=orcamento,
            analise=analise,
            veredito=decisao.veredito,
            severidade=decisao.severidade,
            aprovado=False,
            exige_confirmacao_ressalvas=decisao.exige_confirmacao_ressalvas,
            envelope=None,
        )

    # 5) Viável: enviado -> aprovado -> aprovado_pendente_os (D-ORC-3 / D-ORC-14).
    repo.atualizar_estado(
        inp.orcamento_id, tenant_id=inp.tenant_id, novo_estado=EstadoOrcamento.APROVADO
    )
    orcamento = repo.atualizar_estado(
        inp.orcamento_id,
        tenant_id=inp.tenant_id,
        novo_estado=EstadoOrcamento.APROVADO_PENDENTE_OS,
    )

    # 6) Envelope orcamento.aprovado (equipamento POR ITEM — D-ORC-6).
    envelope = montar_envelope_orcamento_aprovado(
        orcamento=orcamento,
        itens=itens,
        analise_critica=analise,
        regra_decisao_acordada=inp.regra_decisao_acordada,
        abertura_at=inp.agora,
        criada_por_user_id=inp.criada_por_user_id,
    )

    return AprovarOrcamentoOutput(
        orcamento=orcamento,
        analise=analise,
        veredito=decisao.veredito,
        severidade=decisao.severidade,
        aprovado=True,
        exige_confirmacao_ressalvas=decisao.exige_confirmacao_ressalvas,
        envelope=envelope,
    )
