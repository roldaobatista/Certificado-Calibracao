"""Use case `revisar_procedimento` — US-PROC-003 / AC-CAL-016-3 (M7 T-PROC-032).

Revisão = INSERT de nova `versao` (RASCUNHO) preservando a chave natural (codigo+
grandeza+faixa) e as versões anteriores. A nova versão nasce editável; só vira
vigente (e supersede a anterior) quando PUBLICADA (publicar_procedimento). Use
case PURO (ADR-0007).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID, uuid4

from src.domain.metrologia.procedimentos_calibracao.entities import (
    ProcedimentoSnapshot,
)
from src.domain.metrologia.procedimentos_calibracao.enums import (
    EstadoProcedimento,
    TipoMetodo,
)
from src.domain.metrologia.procedimentos_calibracao.repository import (
    ProcedimentoRepository,
)
from src.domain.metrologia.value_objects import FaixaMedicao, Grandeza


class ProcedimentoNaoEncontradoError(Exception):
    def __init__(self, procedimento_id: UUID) -> None:
        super().__init__(f"Procedimento {procedimento_id} não encontrado neste tenant.")


@dataclass(frozen=True, slots=True)
class RevisarProcedimentoInput:
    tenant_id: UUID
    procedimento_id_atual: UUID  # qualquer versão do código a revisar
    titulo: str
    metodo_norma: str
    tipo_metodo: TipoMetodo
    vigencia_inicio: datetime
    correlation_id: UUID
    registro_validacao_id: UUID | None = None
    anexo_pdf_storage_key: str = ""
    anexo_pdf_sha256: str = ""

    def __post_init__(self) -> None:
        if self.vigencia_inicio.tzinfo is None:
            raise ValueError("revisar_procedimento: vigencia_inicio exige tz-aware.")
        if not self.metodo_norma.strip():
            raise ValueError("revisar_procedimento: metodo_norma obrigatório.")


@dataclass(frozen=True, slots=True)
class RevisarProcedimentoOutput:
    nova_versao: ProcedimentoSnapshot
    anterior_id: UUID


def executar(
    inp: RevisarProcedimentoInput, repo: ProcedimentoRepository
) -> RevisarProcedimentoOutput:
    atual = repo.obter_por_id(inp.procedimento_id_atual)
    if atual is None or atual.tenant_id != inp.tenant_id:
        raise ProcedimentoNaoEncontradoError(inp.procedimento_id_atual)

    nova_versao = repo.proxima_versao(tenant_id=inp.tenant_id, codigo=atual.codigo)
    # Reconstrói a chave natural (preservada) e os campos revisáveis.
    grandeza: Grandeza = atual.grandeza
    faixa: FaixaMedicao = atual.faixa
    nova = ProcedimentoSnapshot(
        id=uuid4(),
        tenant_id=atual.tenant_id,
        codigo=atual.codigo,
        titulo=inp.titulo,
        grandeza=grandeza,
        faixa=faixa,
        metodo_norma=inp.metodo_norma,
        tipo_metodo=inp.tipo_metodo,
        registro_validacao_id=inp.registro_validacao_id,
        numero_revisao="",
        anexo_pdf_storage_key=inp.anexo_pdf_storage_key,
        anexo_pdf_sha256=inp.anexo_pdf_sha256,
        versao=nova_versao,
        vigente_a_partir=inp.vigencia_inicio,
        estado=EstadoProcedimento.RASCUNHO,
        revision=0,
        vigencia_inicio=inp.vigencia_inicio,
        correlation_id=inp.correlation_id,
    )
    repo.salvar_novo(nova)
    return RevisarProcedimentoOutput(nova_versao=nova, anterior_id=atual.id)
