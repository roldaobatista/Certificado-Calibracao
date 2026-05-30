"""Máquina de estados + regras puras do procedimento (M7 — T-PROC-014).

Transições válidas de `EstadoProcedimento` + invariantes puras (sem Django) que
os use cases (Fatia 2) consomem. Molde `escopos_cmc/transicoes.py`.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from .enums import EstadoProcedimento, TipoMetodo

# Transições permitidas. Rascunho publica (vira vigente) OU é descartado
# (revogado antes de publicar). PUBLICADO só revoga. REVOGADO é terminal.
# Revisão NÃO é transição: é INSERT de nova `versao`.
_TRANSICOES_VALIDAS: dict[EstadoProcedimento, frozenset[EstadoProcedimento]] = {
    EstadoProcedimento.RASCUNHO: frozenset(
        {EstadoProcedimento.PUBLICADO, EstadoProcedimento.REVOGADO}
    ),
    EstadoProcedimento.PUBLICADO: frozenset({EstadoProcedimento.REVOGADO}),
    EstadoProcedimento.REVOGADO: frozenset(),
}

_MOTIVO_REVOGACAO_MIN = 10  # chars (ADR-0030)
_PERFIL_ACREDITADO = "A"


class ControleDocumentalIncompletoError(Exception):
    """INV-PROC-009 — publicar exige numero_revisao + aprovado_em + aprovado_por."""


def pode_transicionar(de: EstadoProcedimento, para: EstadoProcedimento) -> bool:
    """True se a transição `de -> para` é permitida pela máquina de estados."""
    return para in _TRANSICOES_VALIDAS.get(de, frozenset())


def validar_motivo_revogacao(motivo: str) -> None:
    """Revogação exige motivo >=10 chars (ADR-0030 / INV-PROC-003). Raise se não."""
    if len(motivo.strip()) < _MOTIVO_REVOGACAO_MIN:
        raise ValueError(
            f"motivo_revogacao exige >= {_MOTIVO_REVOGACAO_MIN} chars "
            f"(ADR-0030); recebeu {len(motivo.strip())}"
        )


def validar_controle_documental(
    *,
    numero_revisao: str,
    aprovado_em: datetime | None,
    aprovado_por_id: UUID | None,
) -> None:
    """INV-PROC-009 (cl. 8.3.1) — procedimento PUBLICADO tem os 3 metadados de
    controle documental preenchidos. Levanta se faltar algum (publicação bloqueia).
    """
    faltando = []
    if not numero_revisao.strip():
        faltando.append("numero_revisao")
    if aprovado_em is None:
        faltando.append("aprovado_em")
    if aprovado_por_id is None:
        faltando.append("aprovado_por_id")
    if faltando:
        raise ControleDocumentalIncompletoError(
            "INV-PROC-009 (cl. 8.3.1): publicar exige controle documental "
            f"completo; faltando: {', '.join(faltando)}"
        )


def metodo_exige_validacao_pendente(
    *,
    tipo_metodo: TipoMetodo,
    perfil: str,
    registro_validacao_id: UUID | None,
) -> bool:
    """INV-PROC-010 (cl. 7.2.2) — True quando o método deveria ter evidência de
    validação e NÃO tem: perfil A + (NAO_NORMALIZADO | MODIFICADO) sem
    `registro_validacao_id`.

    **Fail-open lazy no MVP** (paralelo ADR-0066): o use case usa este helper só
    para EMITIR AVISO; o bloqueio duro entra com `licencas-acreditacoes`
    (GATE-PROC-METODO-VALIDADO). Em B/C/D nunca pende (não-acreditado).
    """
    if perfil.strip().upper() != _PERFIL_ACREDITADO:
        return False
    return tipo_metodo.exige_validacao and registro_validacao_id is None
