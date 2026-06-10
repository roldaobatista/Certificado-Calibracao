"""Use cases `criar_serie` + `reservar_numero` — US-CFG-002 (T-CFG-032). PUROS.

ADR-0080: o `regime_numeracao` é DERIVADO do tipo (`regime_numeracao_do_tipo`),
NUNCA vem do caller — fatura/certificado = GAP_LESS; demais = BURACOS_ACEITOS.
`reset_anual` também é derivado (TL-07): contador por (série, ano) quando o
`formato` usa o placeholder `{ano}`. A atomicidade da reserva vive na infra
(advisory lock + triggers — INV-CFG-NUM-ATOMICA); aqui ficam as regras.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID, uuid4

from src.domain.configuracoes_sistema.entities import SerieDocumento
from src.domain.configuracoes_sistema.enums import RegimeNumeracao, TipoDocumento
from src.domain.configuracoes_sistema.repository import SerieDocumentoRepository
from src.domain.configuracoes_sistema.transicoes import (
    proximo_formatado,
    regime_numeracao_do_tipo,
)


class SerieJaExisteError(Exception):
    """Chave (tenant, filial, tipo, prefixo) já cadastrada — 409 (TL-06)."""

    reason = "SERIE_JA_EXISTE"


class SerieNaoEncontradaError(Exception):
    """Série inexistente para (tenant, serie_id) — 404."""

    reason = "SERIE_NAO_ENCONTRADA"


@dataclass(frozen=True, slots=True)
class CriarSerieInput:
    tenant_id: UUID
    tipo: TipoDocumento
    prefixo: str
    formato: str = "{prefixo}-{seq}"
    padding: int = 6
    filial_id: UUID | None = None  # None = série global do tenant


def criar_serie(inp: CriarSerieInput, *, repo: SerieDocumentoRepository) -> SerieDocumento:
    """Cria série com regime + reset anual DERIVADOS (AC-CFG-002-1; ADR-0080/TL-07)."""
    prefixo = inp.prefixo.strip().upper()
    if not prefixo:
        raise ValueError("prefixo obrigatório.")
    if "{seq}" not in inp.formato:
        raise ValueError("formato deve conter o placeholder {seq}.")
    if not 1 <= inp.padding <= 12:
        raise ValueError(f"padding fora de 1..12: {inp.padding}.")
    if (
        repo.obter(
            tenant_id=inp.tenant_id,
            tipo=inp.tipo,
            prefixo=prefixo,
            filial_id=inp.filial_id,
        )
        is not None
    ):
        raise SerieJaExisteError(
            f"série ({inp.tipo.value}, {prefixo}) já existe para esta filial/tenant."
        )
    serie = SerieDocumento(
        id=uuid4(),
        tenant_id=inp.tenant_id,
        tipo=inp.tipo,
        prefixo=prefixo,
        proximo_numero=1,
        regime_numeracao=regime_numeracao_do_tipo(inp.tipo),  # NUNCA do caller
        formato=inp.formato,
        padding=inp.padding,
        filial_id=inp.filial_id,
        reset_anual="{ano}" in inp.formato,  # TL-07 — derivado do formato
        ano_corrente=None,
    )
    repo.salvar(serie)
    return serie


@dataclass(frozen=True, slots=True)
class ReservarNumeroInput:
    tenant_id: UUID
    serie_id: UUID
    agora: datetime  # tz-aware — fonte do ano quando reset_anual

    def __post_init__(self) -> None:
        if self.agora.tzinfo is None:
            raise ValueError("reservar_numero: agora exige datetime tz-aware.")


@dataclass(frozen=True, slots=True)
class ReservarNumeroOutput:
    serie_id: UUID
    sequencial: int
    numero_formatado: str
    regime_numeracao: RegimeNumeracao
    ano: int | None  # dimensão usada (None quando série sem reset anual)
    reserva_id: UUID | None  # GAP_LESS: alvo do confirmar_numero (CFG-IDEMP-01)


def reservar_numero(
    inp: ReservarNumeroInput, *, repo: SerieDocumentoRepository
) -> ReservarNumeroOutput:
    """Reserva o próximo número da série (AC-CFG-002-2 / INV-028).

    GAP_LESS: reserva-TTL — o EMISSOR confirma na própria transação via
    `confirmar_numero(reserva_id=...)` (fluxo reservar→confirmar do motor M8);
    não confirmada expira e o número volta.
    BURACOS_ACEITOS: número já consumido (buraco por rollback aceito — D-CFG-10).
    """
    serie = repo.obter_por_id(tenant_id=inp.tenant_id, serie_id=inp.serie_id)
    if serie is None:
        raise SerieNaoEncontradaError(str(inp.serie_id))
    ano = inp.agora.year if serie.reset_anual else None
    reserva = repo.reservar_numero(tenant_id=inp.tenant_id, serie_id=inp.serie_id, ano=ano)
    return ReservarNumeroOutput(
        serie_id=inp.serie_id,
        sequencial=reserva.sequencial,
        numero_formatado=proximo_formatado(serie, reserva.sequencial, ano),
        regime_numeracao=serie.regime_numeracao,
        ano=ano,
        reserva_id=reserva.reserva_id,
    )
