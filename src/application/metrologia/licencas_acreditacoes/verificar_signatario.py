"""US-LIC-005 / D-LIC-5b — aptidão do signatário (ART/RRT/e-CNPJ). M9 T-LIC-060.

Função PURA (ADR-0007): dado o conjunto de documentos do signatário do tenant,
decide se há algum vencido que inviabilize a assinatura de QUALQUER certificado —
fronteira HARD-409 (cl. 6.2 / NIT-DICLA-021), DISTINTA da acreditação CGCRE (que
REBAIXA via M8 — D-LIC-5a). A integração com a emissão M8 (consumo do veredito) é
GATE-LIC-EMISSAO-HARDBLOCK (Wave B); aqui o M9 expõe o read-model `signatario_apto`.

`bloqueia_assinatura_hard` cobre ART/RRT/CERT_DIGITAL_A1/A3 (enum). Documento
revogado é ignorado; vencimento é avaliado na `data` informada (não `today`) para
preservar o replay determinístico quando a emissão consultar por data de assinatura.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from uuid import UUID

from src.domain.metrologia.licencas_acreditacoes.enums import TipoDocumentoRegulatorio


@dataclass(frozen=True, slots=True)
class DocumentoSignatarioSnapshot:
    """Snapshot leve de um documento do signatário (sem Django)."""

    documento_id: UUID
    tipo: TipoDocumentoRegulatorio
    numero: str
    vigencia_fim: date
    revogado: bool = False


def documentos_signatario_vencidos(
    snapshots: list[DocumentoSignatarioSnapshot], *, data: date
) -> list[DocumentoSignatarioSnapshot]:
    """Documentos do signatário (ART/RRT/cert digital) NÃO-revogados e vencidos na
    `data` — cada um inviabiliza a assinatura (HARD-409). Demais tipos são ignorados."""
    return [
        d
        for d in snapshots
        if d.tipo.bloqueia_assinatura_hard
        and not d.revogado
        and d.vigencia_fim < data
    ]


def signatario_apto(
    snapshots: list[DocumentoSignatarioSnapshot], *, data: date
) -> bool:
    """`True` se NENHUM documento do signatário está vencido na `data` (apto a
    assinar). `True` também quando não há documento do signatário cadastrado — o
    bloqueio hard exige EVIDÊNCIA de vencimento (não presunção de ausência)."""
    return not documentos_signatario_vencidos(snapshots, data=data)
