"""Numeração visível inviolável do certificado (M8 Fatia 1b-numeração, T-CER-033).

NIT-DICLA-021: o número VISÍVEL (`numero_certificado` `<SLUG>-<YYYY>-<NNNNNN>`) não
pode ter buracos por (tenant, tipo, ano) — distinto do `numero_interno` (sequence PG
global, buracos OK — INV-CER-NUM-002). A densidade é garantida por RESERVA com TTL
(T-CER-031): o número é reservado (preview), confirmado na MESMA transação atômica da
emissão; reservas não-confirmadas EXPIRAM e são liberadas, devolvendo o número à
sequência (reuso) — assim o conjunto de números CONFIRMADOS é `{1..N}` denso.

Lógica PURA aqui (ADR-0007); o acesso PG (advisory lock + INSERT/UPDATE + triggers de
consecutividade) vive no adapter `infrastructure/metrologia/certificados/
repositories.py`. Concorrência cronometrada real (gap-detection sob carga) =
T-CER-034 / GATE-CER-DRILL-LOCAL Wave A.
"""

from __future__ import annotations

import re
from collections.abc import Collection
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Protocol, runtime_checkable
from uuid import UUID

from src.domain.metrologia.value_objects import NumeroCertificado

TTL_RESERVA = timedelta(minutes=5)  # T-CER-031 — janela da reserva não-confirmada.
# 1 sequência por (tenant, ano). RBC/NÃO-RBC NÃO separam numeração — senão o número
# visível teria buracos (NIT-DICLA-021). `tipo` fica para futuros TIPOS de documento.
TIPO_CERTIFICADO = "CERTIFICADO"

_SLUG_INVALIDO_RE = re.compile(r"[^A-Z0-9]")


def slug_certificado(tenant_slug: str) -> str:
    """Slug alfanumérico `{2,16}` para o número visível (regex `NumeroCertificado`).

    O slug do tenant pode ter hífen/minúsculas (separador do formato é hífen) —
    sanitiza para `[A-Z0-9]{2,16}`. É COSMÉTICO: a densidade/unicidade da numeração
    é por `tenant_id` na tabela, não pelo slug. Fallback determinístico se < 2 chars.
    """
    limpo = _SLUG_INVALIDO_RE.sub("", tenant_slug.upper())[:16]
    if len(limpo) < 2:
        limpo = (limpo + "CERT")[:16]
    return limpo


@dataclass(frozen=True, slots=True)
class ReservaNumero:
    """Reserva de um número VISÍVEL (T-CER-031). `confirmado=False` até a emissão
    cravar (one-shot). `numero_certificado` é o valor do VO já validado."""

    id: UUID
    tenant_id: UUID
    tipo: str
    ano: int
    sequencial: int
    numero_certificado: str
    reservado_em: datetime
    ttl_expira_em: datetime
    confirmado: bool
    correlation_id: UUID


def proximo_sequencial(sequenciais_em_uso: Collection[int]) -> int:
    """Menor inteiro `>= 1` ausente de `sequenciais_em_uso` (confirmados + reservas
    vivas). Reusa números liberados por reservas expiradas → densidade sem buracos
    (NIT-DICLA-021). Determinístico (replay cl. 7.11)."""
    usados = set(sequenciais_em_uso)
    n = 1
    while n in usados:
        n += 1
    return n


def montar_numero_certificado(
    *, tenant_slug: str, ano: int, sequencial: int
) -> NumeroCertificado:
    """Formata `<SLUG>-<YYYY>-<NNNNNN>` (o VO valida a regex NIT-DICLA-021)."""
    return NumeroCertificado(
        value=f"{slug_certificado(tenant_slug)}-{ano:04d}-{sequencial:06d}"
    )


@runtime_checkable
class NumeracaoCertificadoRepository(Protocol):
    """Reserva → confirma → libera (T-CER-033). Serializa por (tenant, tipo, ano)
    com advisory lock transacional; o INSERT é validado pelo trigger de
    consecutividade (T-CER-032)."""

    def reservar_numero(
        self,
        *,
        tenant_id: UUID,
        tenant_slug: str,
        ano: int,
        correlation_id: UUID,
        tipo: str = TIPO_CERTIFICADO,
    ) -> ReservaNumero:
        """Reserva o próximo número denso (preview, `confirmado=False`, TTL 5min)."""
        ...

    def confirmar_numero(self, *, reserva_id: UUID, tenant_id: UUID) -> bool:
        """One-shot dentro da `transaction.atomic` da emissão. False se expirada/já
        confirmada (caller re-reserva)."""
        ...

    def liberar_expirados(
        self, *, tenant_id: UUID, ano: int, tipo: str = TIPO_CERTIFICADO
    ) -> int:
        """Remove reservas não-confirmadas vencidas (devolve número à sequência).
        Retorna a quantidade liberada."""
        ...
