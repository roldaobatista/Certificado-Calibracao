"""Funções puras de regra do domínio `configuracoes-sistema` (Fatia 1a — T-CFG-013).

Sem I/O, sem Django. Concorrência/atomicidade da reserva de número vive na infra
(reserva-TTL para gap-less; UPDATE atômico para buracos-aceitos — ADR-0080).
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from datetime import datetime

from .entities import Filial, Imposto, SerieDocumento
from .enums import RegimeNumeracao, TipoDocumento
from .erros import MatrizInvalidaError, NumeroNuncaDiminuiError

# Tipos cuja numeração é gap-less obrigatória (exigência fiscal/ISO — ADR-0080).
_TIPOS_GAP_LESS: frozenset[TipoDocumento] = frozenset(
    {TipoDocumento.FATURA, TipoDocumento.CERTIFICADO}
)


def regime_numeracao_do_tipo(tipo: TipoDocumento) -> RegimeNumeracao:
    """Deriva o regime de numeração do TIPO do documento (ADR-0080).

    fatura/certificado → GAP_LESS (sem buraco); demais → BURACOS_ACEITOS.
    """
    if tipo in _TIPOS_GAP_LESS:
        return RegimeNumeracao.GAP_LESS
    return RegimeNumeracao.BURACOS_ACEITOS


def proximo_formatado(
    serie: SerieDocumento, numero: int, ano: int | None = None
) -> str:
    """Renderiza o número no `formato` da série (prefixo/padding/ano).

    Placeholders suportados: `{prefixo}`, `{seq}` (com padding), `{ano}`.
    Ex.: formato `OS-{ano}-{seq}` + prefixo `OS` + padding 6 → `OS-2026-000123`.
    """
    seq = str(numero).zfill(serie.padding)
    ano_str = str(ano) if ano is not None else ""
    return (
        serie.formato.replace("{prefixo}", serie.prefixo)
        .replace("{seq}", seq)
        .replace("{ano}", ano_str)
    )


def validar_proximo_numero_nao_diminui(antigo: int, novo: int) -> None:
    """INV-028 — `proximo_numero` nunca pode ser ajustado para menor."""
    if novo < antigo:
        raise NumeroNuncaDiminuiError(
            f"proximo_numero não pode diminuir: {antigo} → {novo} (INV-028)."
        )


def validar_uma_matriz(filiais: Sequence[Filial]) -> None:
    """INV-037 — exatamente 1 matriz quando há ≥1 filial.

    Conjunto vazio é válido (empresa sem filiais cadastradas ainda). Com filiais,
    exatamente uma deve ter `eh_matriz=True`.
    """
    if not filiais:
        return
    matrizes = [f for f in filiais if f.eh_matriz]
    if len(matrizes) != 1:
        raise MatrizInvalidaError(
            f"esperava exatamente 1 matriz, encontrou {len(matrizes)} (INV-037)."
        )


def _vigencias_sobrepoem(a: Imposto, b: Imposto) -> bool:
    """True se as janelas de vigência de dois impostos se sobrepõem (half-open `[)`)."""
    a_ini, a_fim = a.vigencia.inicio, a.vigencia.fim
    b_ini, b_fim = b.vigencia.inicio, b.vigencia.fim
    # fim None = vigência aberta (+inf).
    a_fim_eff = a_fim if a_fim is not None else datetime.max.replace(tzinfo=a_ini.tzinfo)
    b_fim_eff = b_fim if b_fim is not None else datetime.max.replace(tzinfo=b_ini.tzinfo)
    return a_ini < b_fim_eff and b_ini < a_fim_eff


def ha_sobreposicao_vigencia(
    existentes: Iterable[Imposto], novo: Imposto
) -> bool:
    """INV-CFG-IMPOSTO-SEM-SOBREPOSICAO (defesa no domínio; constraint no banco).

    True se `novo` colide com alguma linha existente do MESMO (tenant, tipo, filial).
    """
    for e in existentes:
        if (
            e.tenant_id == novo.tenant_id
            and e.tipo == novo.tipo
            and e.filial_id == novo.filial_id
            and e.id != novo.id
            and _vigencias_sobrepoem(e, novo)
        ):
            return True
    return False


def imposto_vigente_em(
    impostos: Iterable[Imposto],
    tipo: object,
    filial_id: object,
    momento: datetime,
) -> Imposto | None:
    """Retorna o `Imposto` do (tipo, filial) vigente em `momento`, ou None.

    Determinístico: a não-sobreposição (constraint INV-CFG-IMPOSTO-SEM-SOBREPOSICAO)
    garante no máximo 1 resultado.
    """
    for imp in impostos:
        if (
            imp.tipo == tipo
            and imp.filial_id == filial_id
            and imp.vigencia.vigente_em(momento)
        ):
            return imp
    return None
