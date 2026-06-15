"""Lógica de categoria de receita perfil-aware (Fatia 1a — T-CR-014).

D-CR-5 / INV-FIN-PERFIL-001 / spec §3.1:
  - `CALIBRACAO_RBC` exige `perfil='A'` (acreditado RBC).
  - Derivação automática pelo `perfil_no_evento`:
      A  → CALIBRACAO_RBC
      B/C → CALIBRACAO_NAO_RBC
      D  → CALIBRACAO_BASICA

Validação no use case (ADR-0073), nunca no DRF.
Sem I/O, sem Django.
"""

from __future__ import annotations

from .enums import CategoriaReceita
from .erros import CategoriaReceitaExigePerfilA, PerfilIndeterminado

_CATEGORIA_POR_PERFIL: dict[str, CategoriaReceita] = {
    "A": CategoriaReceita.CALIBRACAO_RBC,
    "B": CategoriaReceita.CALIBRACAO_NAO_RBC,
    "C": CategoriaReceita.CALIBRACAO_NAO_RBC,
    "D": CategoriaReceita.CALIBRACAO_BASICA,
}


def categoria_por_perfil_evento(perfil: str) -> CategoriaReceita:
    """Deriva a `CategoriaReceita` padrão a partir do perfil regulatório.

    Parâmetro:
        perfil — char único 'A'|'B'|'C'|'D' (snapshot `perfil_no_evento` — D-CR-6).

    Levanta `PerfilIndeterminado` para perfil desconhecido (fail-closed).

    Uso típico: consumer de `os.concluida` deriva a categoria automaticamente
    pelo `perfil_no_evento` do envelope (D-CR-12).
    """
    try:
        return _CATEGORIA_POR_PERFIL[perfil.upper()]
    except (KeyError, AttributeError) as exc:
        raise PerfilIndeterminado(
            f"perfil_no_evento desconhecido: {perfil!r} — "
            f"valores aceitos: {sorted(_CATEGORIA_POR_PERFIL)}"
        ) from exc


def categoria_permitida(categoria: CategoriaReceita, perfil: str) -> bool:
    """Verifica se a `categoria` é permitida para o `perfil` informado.

    Regra (INV-FIN-PERFIL-001 / D-CR-5):
      - `CALIBRACAO_RBC` só é permitida para perfil 'A'.
      - Demais categorias são permitidas para qualquer perfil.

    Levanta `CategoriaReceitaExigePerfilA` se há mismatch (fail-closed → 403).
    Levanta `PerfilIndeterminado` para perfil desconhecido.
    Retorna `True` se a combinação é permitida.
    """
    perfil_upper = perfil.upper() if isinstance(perfil, str) else None
    if perfil_upper not in _CATEGORIA_POR_PERFIL:
        raise PerfilIndeterminado(
            f"perfil_no_evento desconhecido: {perfil!r} — "
            f"valores aceitos: {sorted(_CATEGORIA_POR_PERFIL)}"
        )
    if categoria is CategoriaReceita.CALIBRACAO_RBC and perfil_upper != "A":
        raise CategoriaReceitaExigePerfilA(
            f"categoria {categoria.value!r} exige perfil 'A'; " f"tenant tem perfil {perfil!r}"
        )
    return True
