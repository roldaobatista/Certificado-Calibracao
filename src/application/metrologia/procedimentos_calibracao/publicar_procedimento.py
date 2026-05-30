"""Use case `publicar_procedimento` — US-PROC-002 (M7 T-PROC-031).

Transição RASCUNHO→PUBLICADO de um documento controlado (cl. 7.2.1). Exige
controle documental completo (numero_revisao + aprovado_em + aprovado_por —
INV-PROC-009 cl. 8.3.1). Superseção automática: encerra a `vigencia_fim` da versão
PUBLICADA vigente anterior da mesma chave natural (INV-PROC-008) no instante em
que a nova passa a valer — a anterior NÃO é apagada (WORM Padrão B, auditoria
retroativa cl. 8.4). Use case PURO (ADR-0007).

**Atomicidade + advisory lock** (D-PROC-3): o caller (view) envolve `executar` em
`transaction.atomic()` + `pg_advisory_xact_lock(hash(tenant,codigo,grandeza,faixa))`
para serializar publicações concorrentes do mesmo procedimento. O UNIQUE parcial
`uq_proc_uma_vigente` é o cinto-e-suspensório no banco.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime
from uuid import UUID

from src.domain.metrologia.procedimentos_calibracao.entities import (
    ProcedimentoSnapshot,
)
from src.domain.metrologia.procedimentos_calibracao.enums import EstadoProcedimento
from src.domain.metrologia.procedimentos_calibracao.repository import (
    ProcedimentoRepository,
)
from src.domain.metrologia.procedimentos_calibracao.transicoes import (
    metodo_exige_validacao_pendente,
    pode_transicionar,
    validar_controle_documental,
)


class ProcedimentoNaoEncontradoError(Exception):
    def __init__(self, procedimento_id: UUID) -> None:
        super().__init__(f"Procedimento {procedimento_id} não encontrado neste tenant.")


class ProcedimentoNaoPublicavelError(Exception):
    """Só RASCUNHO pode ser publicado (PUBLICADO/REVOGADO não)."""

    def __init__(self, estado: str) -> None:
        super().__init__(f"Procedimento em estado {estado} não pode ser publicado.")


class ConflitoVersaoError(Exception):
    """CAS — o procedimento ou a versão anterior mudou concorrentemente (409)."""


@dataclass(frozen=True, slots=True)
class PublicarProcedimentoInput:
    tenant_id: UUID
    procedimento_id: UUID  # o RASCUNHO a publicar
    numero_revisao: str
    aprovado_em: datetime
    aprovado_por_id: UUID
    perfil: str  # server-side
    aprovado_por_nome_snapshot: str = ""
    vigente_a_partir: datetime | None = None  # default = vigencia_inicio do rascunho

    def __post_init__(self) -> None:
        if self.aprovado_em.tzinfo is None:
            raise ValueError("publicar_procedimento: aprovado_em exige tz-aware.")
        if self.vigente_a_partir is not None and self.vigente_a_partir.tzinfo is None:
            raise ValueError("publicar_procedimento: vigente_a_partir exige tz-aware.")
        # INV-PROC-009 — controle documental completo (cl. 8.3.1)
        validar_controle_documental(
            numero_revisao=self.numero_revisao,
            aprovado_em=self.aprovado_em,
            aprovado_por_id=self.aprovado_por_id,
        )


@dataclass(frozen=True, slots=True)
class PublicarProcedimentoOutput:
    publicado: ProcedimentoSnapshot
    anterior_encerrada_id: UUID | None  # versão superada (None se 1ª publicação)
    aviso_validacao_metodo: bool


def executar(
    inp: PublicarProcedimentoInput, repo: ProcedimentoRepository
) -> PublicarProcedimentoOutput:
    """Publica o RASCUNHO: supersede a vigente anterior + transiciona. Caller
    serializa com advisory lock (D-PROC-3)."""
    atual = repo.obter_por_id(inp.procedimento_id)
    if atual is None or atual.tenant_id != inp.tenant_id:
        raise ProcedimentoNaoEncontradoError(inp.procedimento_id)
    if not pode_transicionar(atual.estado, EstadoProcedimento.PUBLICADO):
        raise ProcedimentoNaoPublicavelError(atual.estado.value)

    vigente_a_partir = inp.vigente_a_partir or atual.vigencia_inicio

    # Superseção: encerra a vigência da versão PUBLICADA vigente anterior (mesma
    # chave natural) no instante em que a nova passa a valer (INV-PROC-008).
    anterior = repo.vigente_anterior(
        tenant_id=inp.tenant_id,
        codigo=atual.codigo,
        grandeza=atual.grandeza,
        faixa=atual.faixa,
    )
    anterior_id: UUID | None = None
    if anterior is not None:
        if not repo.encerrar_vigencia(
            procedimento_id=anterior.id,
            vigencia_fim=vigente_a_partir,
            revision_anterior=anterior.revision,
        ):
            raise ConflitoVersaoError
        anterior_id = anterior.id

    publicado = replace(
        atual,
        estado=EstadoProcedimento.PUBLICADO,
        numero_revisao=inp.numero_revisao,
        aprovado_em=inp.aprovado_em,
        aprovado_por_id=inp.aprovado_por_id,
        aprovado_por_nome_snapshot=inp.aprovado_por_nome_snapshot,
        vigente_a_partir=vigente_a_partir,
        vigencia_inicio=vigente_a_partir,
    )
    if not repo.atualizar_com_lock(publicado, atual.revision):
        raise ConflitoVersaoError

    aviso = metodo_exige_validacao_pendente(
        tipo_metodo=atual.tipo_metodo,
        perfil=inp.perfil,
        registro_validacao_id=atual.registro_validacao_id,
    )
    return PublicarProcedimentoOutput(
        publicado=publicado, anterior_encerrada_id=anterior_id, aviso_validacao_metodo=aviso
    )
