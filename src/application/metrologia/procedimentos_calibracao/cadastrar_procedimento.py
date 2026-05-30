"""Use case `cadastrar_procedimento` — US-PROC-001 (M7 T-PROC-030).

Cria um ProcedimentoCalibracao novo (versão 1) em estado RASCUNHO (editável). Use
case PURO (ADR-0007): Input frozen + Repository Protocol. O método não-normalizado
sem evidência de validação NÃO bloqueia o cadastro (fail-open lazy INV-PROC-010);
o aviso é devolvido para a UI. NÃO chama AuthorizationProvider (caller=guard).
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
from src.domain.metrologia.procedimentos_calibracao.transicoes import (
    metodo_exige_validacao_pendente,
)
from src.domain.metrologia.value_objects import FaixaMedicao, Grandeza


class CodigoVersaoDuplicadoError(Exception):
    """INV-PROC-002 — já existe (codigo, versao) neste tenant."""

    def __init__(self, codigo: str, versao: int) -> None:
        super().__init__(
            f"INV-PROC-002: já existe procedimento {codigo} v{versao} "
            "(use revisar para criar nova versão)."
        )


@dataclass(frozen=True, slots=True)
class CadastrarProcedimentoInput:
    tenant_id: UUID
    codigo: str
    titulo: str
    grandeza: Grandeza
    faixa: FaixaMedicao
    metodo_norma: str
    tipo_metodo: TipoMetodo
    perfil: str  # perfil regulatório do tenant (A/B/C/D) — server-side
    vigencia_inicio: datetime
    correlation_id: UUID
    registro_validacao_id: UUID | None = None
    anexo_pdf_storage_key: str = ""
    anexo_pdf_sha256: str = ""

    def __post_init__(self) -> None:
        if self.vigencia_inicio.tzinfo is None:
            raise ValueError(
                "cadastrar_procedimento: vigencia_inicio exige tz-aware (INV-VIG-004)."
            )
        if not self.codigo.strip():
            raise ValueError("cadastrar_procedimento: codigo obrigatório.")
        if not self.metodo_norma.strip():
            raise ValueError("cadastrar_procedimento: metodo_norma obrigatório.")


@dataclass(frozen=True, slots=True)
class CadastrarProcedimentoOutput:
    snapshot: ProcedimentoSnapshot
    aviso_validacao_metodo: bool  # INV-PROC-010 fail-open lazy (UI mostra aviso)


def executar(
    inp: CadastrarProcedimentoInput, repo: ProcedimentoRepository
) -> CadastrarProcedimentoOutput:
    """Cadastra o procedimento v1 RASCUNHO. INV-PROC-002 (chave única)."""
    if repo.existe_chave(tenant_id=inp.tenant_id, codigo=inp.codigo, versao=1):
        raise CodigoVersaoDuplicadoError(inp.codigo, 1)

    snapshot = ProcedimentoSnapshot(
        id=uuid4(),
        tenant_id=inp.tenant_id,
        codigo=inp.codigo,
        titulo=inp.titulo,
        grandeza=inp.grandeza,
        faixa=inp.faixa,
        metodo_norma=inp.metodo_norma,
        tipo_metodo=inp.tipo_metodo,
        registro_validacao_id=inp.registro_validacao_id,
        numero_revisao="",
        anexo_pdf_storage_key=inp.anexo_pdf_storage_key,
        anexo_pdf_sha256=inp.anexo_pdf_sha256,
        versao=1,
        vigente_a_partir=inp.vigencia_inicio,
        estado=EstadoProcedimento.RASCUNHO,
        revision=0,
        vigencia_inicio=inp.vigencia_inicio,
        correlation_id=inp.correlation_id,
    )
    repo.salvar_novo(snapshot)
    aviso = metodo_exige_validacao_pendente(
        tipo_metodo=inp.tipo_metodo,
        perfil=inp.perfil,
        registro_validacao_id=inp.registro_validacao_id,
    )
    return CadastrarProcedimentoOutput(snapshot=snapshot, aviso_validacao_metodo=aviso)
