"""Maquina de estados do PadraoMetrologico (M5 T-PAD-007).

Transicoes validas + guarda pura (sem Django). O estado
`RECAL_RETORNADO_PENDENTE_APROVACAO` (C-4 FURO-1) intermedeia retorno do lab e
liberacao por aprovacao do RT — o padrao NAO volta direto a EM_USO.
"""

from __future__ import annotations

from .enums import EstadoPadrao

# Transicoes validas: de -> {para...}. Espelha plan v2 §14 estados.
TRANSICOES_VALIDAS: dict[EstadoPadrao, frozenset[EstadoPadrao]] = {
    EstadoPadrao.EM_USO: frozenset({
        EstadoPadrao.EM_RECAL_EXTERNO,  # envio recal OU VI reprovada (AC-PAD-003-2)
        EstadoPadrao.INTERCOMPARACAO_PT_EM_CURSO,  # PT inicio
        EstadoPadrao.BAIXADO,
        EstadoPadrao.SUCATEADO,
    }),
    EstadoPadrao.EM_RECAL_EXTERNO: frozenset({
        EstadoPadrao.RECAL_RETORNADO_PENDENTE_APROVACAO,  # retorno normal (C-4)
        EstadoPadrao.BAIXADO,  # extraviado/recusado no transporte
    }),
    EstadoPadrao.RECAL_RETORNADO_PENDENTE_APROVACAO: frozenset({
        EstadoPadrao.EM_USO,  # RT aprova analise critica (C-4)
        EstadoPadrao.EM_RECAL_EXTERNO,  # RT reprova -> re-envia
    }),
    EstadoPadrao.INTERCOMPARACAO_PT_EM_CURSO: frozenset({
        EstadoPadrao.EM_USO,  # PT concluida
    }),
    EstadoPadrao.BAIXADO: frozenset({
        EstadoPadrao.EM_USO,  # reversao com avaliacao tecnica
        EstadoPadrao.SUCATEADO,
    }),
    EstadoPadrao.SUCATEADO: frozenset(),  # terminal duro
}


class TransicaoInvalidaError(Exception):
    """Transicao de estado nao permitida pela maquina de estados."""

    def __init__(self, de: EstadoPadrao, para: EstadoPadrao) -> None:
        self.de = de
        self.para = para
        super().__init__(
            f"Transicao invalida {de.value} -> {para.value}. "
            f"Validas a partir de {de.value}: "
            f"{sorted(e.value for e in TRANSICOES_VALIDAS.get(de, frozenset()))}"
        )


def pode_transicionar(de: EstadoPadrao, para: EstadoPadrao) -> bool:
    return para in TRANSICOES_VALIDAS.get(de, frozenset())


def validar_transicao(de: EstadoPadrao, para: EstadoPadrao) -> None:
    """Levanta TransicaoInvalidaError se a transicao nao for permitida."""
    if not pode_transicionar(de, para):
        raise TransicaoInvalidaError(de, para)
