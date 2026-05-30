"""Use case `importar_escopo_pdf` — M6 Fatia 4 (T-ECMC-051).

Recebe linhas JÁ extraídas do PDF CGCRE (pelo `LeitorTabelaPdf` em infra) + o
mapa de colunas, roda o motor DETERMINÍSTICO `parsear_tabela` e cria um
`EscopoExtraido` em STAGING (mutável, NÃO WORM). NUNCA persiste escopo vigente
(INV-ECMC-007) — só a conferência humana (T-ECMC-052) promove a CONFIRMADO.

Puro (ADR-0007): Input frozen + EscopoExtraidoRepository Protocol. NÃO IA
(parser determinístico — não ativa ADR-0059).
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID, uuid4

from src.domain.metrologia.escopos_cmc.entities import EscopoExtraido
from src.domain.metrologia.escopos_cmc.extracao import MapaColunas, parsear_tabela
from src.domain.metrologia.escopos_cmc.repository import EscopoExtraidoRepository


@dataclass(frozen=True, slots=True)
class ImportarEscopoPdfInput:
    tenant_id: UUID
    origem_pdf_storage_key: str  # chave opaca do PDF (documento público CGCRE)
    numero_escopo_cgcre: str
    linhas_cruas: Sequence[Sequence[str]]  # células extraídas pelo leitor (infra)
    mapa_colunas: MapaColunas
    extraido_em: datetime
    correlation_id: UUID

    def __post_init__(self) -> None:
        if self.extraido_em.tzinfo is None:
            raise ValueError(
                "importar_escopo_pdf: extraido_em exige datetime tz-aware (INV-VIG-004)."
            )
        if not self.origem_pdf_storage_key.strip():
            raise ValueError("importar_escopo_pdf: origem_pdf_storage_key obrigatória.")


@dataclass(frozen=True, slots=True)
class ImportarEscopoPdfOutput:
    extraido: EscopoExtraido


def executar(
    inp: ImportarEscopoPdfInput, repo: EscopoExtraidoRepository
) -> ImportarEscopoPdfOutput:
    """Parseia (determinístico) e grava o staging RASCUNHO_EXTRAIDO (INV-ECMC-007)."""
    linhas = parsear_tabela(inp.linhas_cruas, inp.mapa_colunas)
    extraido = EscopoExtraido(
        id=uuid4(),
        tenant_id=inp.tenant_id,
        origem_pdf_storage_key=inp.origem_pdf_storage_key,
        numero_escopo_cgcre=inp.numero_escopo_cgcre,
        extraido_em=inp.extraido_em,
        linhas=linhas,
        confirmado_em=None,
        confirmado_por_id_hash="",
    )
    repo.salvar_novo(extraido)
    return ImportarEscopoPdfOutput(extraido=extraido)
