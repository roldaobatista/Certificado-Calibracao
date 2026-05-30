"""Máquina de estados + regras puras do escopo (M6 T-ECMC-006).

Transições válidas de `EstadoEscopo` + invariantes puras (sem Django) que os
use cases (Fatia 2) consomem. Anti-fraude INV-ECMC-002 (rbc só perfil A) é
forçado AQUI, no domínio, não no payload (ADR-0067 / FAIL L6 SAN-PERFIL).
"""

from __future__ import annotations

from .enums import EstadoEscopo

# Transições permitidas. Rascunho extraído pode ser confirmado (vira vigente) OU
# descartado (revogado, antes de confirmar). CONFIRMADO só revoga. REVOGADO é
# terminal. Revisão NÃO é transição: é INSERT de nova `versao` (TL-C-07).
_TRANSICOES_VALIDAS: dict[EstadoEscopo, frozenset[EstadoEscopo]] = {
    EstadoEscopo.RASCUNHO_EXTRAIDO: frozenset(
        {EstadoEscopo.CONFIRMADO, EstadoEscopo.REVOGADO}
    ),
    EstadoEscopo.CONFIRMADO: frozenset({EstadoEscopo.REVOGADO}),
    EstadoEscopo.REVOGADO: frozenset(),
}

_PERFIL_ACREDITADO = "A"
_MOTIVO_REVOGACAO_MIN = 10  # chars (ADR-0030)


def pode_transicionar(de: EstadoEscopo, para: EstadoEscopo) -> bool:
    """True se a transição `de -> para` é permitida pela máquina de estados."""
    return para in _TRANSICOES_VALIDAS.get(de, frozenset())


def perfil_permite_rbc(perfil: str) -> bool:
    """Só perfil A (acreditado CGCRE) pode declarar escopo RBC (INV-ECMC-002 /
    ADR-0067). B/C/D declaram capacidade interna (ADR-0075)."""
    return perfil.strip().upper() == _PERFIL_ACREDITADO


def rbc_efetivo(*, rbc_solicitado: bool, perfil: str) -> bool:
    """RBC EFETIVO server-side — anti-fraude (INV-ECMC-002 / INV-015 / FAIL L6).

    Tenant não-A que tente `rbc_acreditado=True` tem o valor FORÇADO para False.
    Nunca confiar no payload — o perfil vem do Tenant (ADR-0067).
    """
    return bool(rbc_solicitado) and perfil_permite_rbc(perfil)


def validar_motivo_revogacao(motivo: str) -> None:
    """Revogação exige motivo >=10 chars (ADR-0030 / INV-ECMC-003). Raise se não."""
    if len(motivo.strip()) < _MOTIVO_REVOGACAO_MIN:
        raise ValueError(
            f"motivo_revogacao exige >= {_MOTIVO_REVOGACAO_MIN} chars "
            f"(ADR-0030); recebeu {len(motivo.strip())}"
        )
