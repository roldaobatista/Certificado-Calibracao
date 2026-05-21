"""Direitos do titular LGPD (US-CLI-006 — T-CLI-115/119).

Marco 1 entrega T-CLI-115 (revogacao consentimento) + T-CLI-119
(evento incidente). T-CLI-114 (8 endpoints completos) +
T-CLI-116 (matriz eliminacao×anonimizacao) ficam como GATE
rastreado pra Wave A.

Anti-corrosion (BLOQ-TL-3 tech-lead): use cases em
`src/application/comercial/clientes/direitos_titular/` quando
formalizado em Wave A; Marco 1 mantem coesao em `infrastructure/`.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from src.infrastructure.audit.acoes_canonicas import ACOES_CLIENTES
from src.infrastructure.audit.event_helpers import publicar_evento
from src.infrastructure.clientes.models import Cliente


class ClienteJaRevogou(Exception):
    """T-CLI-115 — tentativa de revogar consentimento ja revogado."""


def revogar_consentimento(
    *,
    cliente: Cliente,
    tenant_id: UUID,
    usuario_id: UUID | None,
    causation_id: UUID | None = None,
) -> Cliente:
    """T-CLI-115 (AC-CLI-006-2 — LGPD art. 8º §5º) — revoga consentimento.

    Efeito >= 1 min (cravado na spec): seta `consentimento_revogado_em`
    + publica evento `cliente.consentimento_revogado` (cadeia F-A +
    outbox transacional).

    Outras bases legais continuam aplicaveis conforme
    `politicas_lgpd.base_legal_aplicavel_pos_revogacao`.

    Idempotencia: chamar 2x para cliente ja revogado levanta
    `ClienteJaRevogou` (caller decide retornar 200 com flag ou 409).
    """
    if cliente.consentimento_revogado_em is not None:
        raise ClienteJaRevogou(
            f"cliente {cliente.id} já revogou em "
            f"{cliente.consentimento_revogado_em.isoformat()}"
        )

    cliente.consentimento_revogado_em = datetime.now(UTC)
    cliente.save(update_fields=["consentimento_revogado_em", "atualizado_em"])

    publicar_evento(
        acao="cliente.consentimento_revogado",
        payload={
            "cliente_id": str(cliente.id),
            "revogado_em": cliente.consentimento_revogado_em.isoformat(),
        },
        causation_id=causation_id or uuid4(),
        tenant_id=tenant_id,
        usuario_id=usuario_id,
        resource_summary=f"cliente {cliente.id} revogou consentimento",
    )
    return cliente


# =============================================================
# T-CLI-119 (AC-CLI-006-6) — evento de incidente PII (Res. ANPD 15/2024)
# =============================================================

_ESCOPOS_VALIDOS = frozenset({"registro_unico", "subconjunto_filtrado", "base_inteira"})


def emitir_incidente_pii(
    *,
    tenant_id: UUID,
    descricao_curta: str,
    categoria_pii_afetada: str,
    cliente_ids: list[UUID] | None = None,
    escopo: str | None = None,
    qt_titulares_declarada: int | None = None,
    usuario_id: UUID | None = None,
    causation_id: UUID | None = None,
) -> dict[str, Any]:
    """T-CLI-119 (AC-CLI-006-6) — emite evento de incidente PII.

    BLOQ-A5 advogado: `qt_titulares_estimada` NAO eh inferida de
    `Cliente.count()` (superestima). Helper recebe:
    - `cliente_ids: list[UUID]` (afetados conhecidos) — caso preciso.
    - OU `escopo: Literal["registro_unico"|"subconjunto_filtrado"|
      "base_inteira"]` + `qt_titulares_declarada` opcional.

    Default conservador se nada informado: `escopo="registro_unico"`,
    `qt=1`. Operador declara o escopo no momento do incidente — NAO
    inferimos.

    Publica via outbox transacional. Wave A: consumer `governanca`
    recebe e dispara fluxo ANPD (SLA 3 dias uteis Res. ANPD 15/2024).
    """
    if cliente_ids is not None:
        qt = len(cliente_ids)
        escopo_efetivo = "registro_unico" if qt == 1 else "subconjunto_filtrado"
    elif escopo is not None:
        if escopo not in _ESCOPOS_VALIDOS:
            raise ValueError(f"escopo invalido '{escopo}'. Use {sorted(_ESCOPOS_VALIDOS)}")
        escopo_efetivo = escopo
        qt = qt_titulares_declarada or 0
    else:
        # Default conservador (BLOQ-A5)
        escopo_efetivo = "registro_unico"
        qt = 1

    cid = causation_id or uuid4()
    publicar_evento(
        acao="cliente.pii.incidente_detectado",
        payload={
            "descricao_curta": descricao_curta,
            "categoria_pii_afetada": categoria_pii_afetada,
            "escopo": escopo_efetivo,
            "qt_titulares_estimada": qt,
            "cliente_ids": [str(c) for c in (cliente_ids or [])],
        },
        causation_id=cid,
        tenant_id=tenant_id,
        usuario_id=usuario_id,
        resource_summary=f"incidente {escopo_efetivo} qt={qt}",
    )
    return {
        "causation_id": str(cid),
        "escopo": escopo_efetivo,
        "qt_titulares_estimada": qt,
    }


# Adicionar acoes canonicas pre-povoadas (T-CLI-115/T-CLI-119 ja estao em
# `acoes_canonicas.ACOES_CLIENTES`). Garante visibilidade do conjunto.
assert "cliente.consentimento_revogado" in ACOES_CLIENTES
