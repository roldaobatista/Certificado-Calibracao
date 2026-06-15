"""Grace period por perfil regulatório (Fatia 1a — T-CR-014).

Função pura `grace_period_por_perfil(perfil) -> int` — número de dias de carência
antes do título entrar na lista de inadimplência dura (D-CR-9 / INV-FIN-GRACE-PERFIL-001).

Valores (spec §3 D-CR-9 / plan §2):
    A = 45 dias  (acreditado RBC — prazo maior por compliance CDC / ISO 17025)
    B = 20 dias  (rastreável)
    C = 30 dias  (em preparação D→A)
    D =  7 dias  (comercial puro)

Sem I/O, sem Django.
"""

from __future__ import annotations

from .erros import PerfilIndeterminado

_GRACE_POR_PERFIL: dict[str, int] = {
    "A": 45,
    "B": 20,
    "C": 30,
    "D": 7,
}


def grace_period_por_perfil(perfil: str) -> int:
    """Dias de carência de inadimplência para o perfil informado.

    Parâmetro:
        perfil — char único 'A'|'B'|'C'|'D' (snapshot `perfil_no_evento` — D-CR-6).

    Levanta `PerfilIndeterminado` para perfil desconhecido (fail-closed — D-CR-6).
    """
    try:
        return _GRACE_POR_PERFIL[perfil.upper()]
    except (KeyError, AttributeError) as exc:
        raise PerfilIndeterminado(
            f"perfil_no_evento desconhecido: {perfil!r} — "
            f"valores aceitos: {sorted(_GRACE_POR_PERFIL)}"
        ) from exc
