"""Máquina de estados + regras puras de emissão do certificado (M8 Fatia 1a,
T-CER-015).

Transições válidas de `EstadoCertificado` + validações que os use cases (Fatia 2)
consomem. `RASCUNHO` permanece declarado (compat stub) mas NÃO é materializado
nesta frente — a reconciliação pendurada em `calibracao_id` é a "pré-emissão";
`emitir_certificado` cria a linha já em `EMITIDO` numa transação atômica. Sem
Django (ADR-0007).
"""

from __future__ import annotations

from collections.abc import Collection
from decimal import Decimal

from .enums import (
    CategoriaMotivoExclusao,
    ClassificacaoPonto,
    DecisaoReconciliacaoRT,
    EstadoCertificado,
)
from .erros import (
    MotivoReemissaoInsuficienteError,
    ReconciliacaoPendenteDecisaoRTError,
    RessalvaNaoRbcObrigatoriaError,
    TransicaoCertificadoInvalidaError,
)

# Reemissão NÃO é transição: cria NOVA linha v(N+1) e marca v(N)→SUBSTITUIDA.
_TRANSICOES_VALIDAS: dict[EstadoCertificado, frozenset[EstadoCertificado]] = {
    EstadoCertificado.RASCUNHO: frozenset({EstadoCertificado.EMITIDO}),
    EstadoCertificado.EMITIDO: frozenset(
        {EstadoCertificado.SUBSTITUIDA, EstadoCertificado.REVOGADO}
    ),
    EstadoCertificado.SUBSTITUIDA: frozenset(),
    EstadoCertificado.REVOGADO: frozenset(),
}

_PERFIL_ACREDITADO = "A"
_MOTIVO_REEMISSAO_MIN = 50  # chars (US-CER-004)


def pode_transicionar(de: EstadoCertificado, para: EstadoCertificado) -> bool:
    """True se `de -> para` é permitida pela máquina de estados."""
    return para in _TRANSICOES_VALIDAS.get(de, frozenset())


def exigir_transicao(de: EstadoCertificado, para: EstadoCertificado) -> None:
    """Raise `TransicaoCertificadoInvalidaError` se a transição for inválida."""
    if not pode_transicionar(de, para):
        raise TransicaoCertificadoInvalidaError(
            f"transição {de.value} -> {para.value} não permitida"
        )


def validar_motivo_reemissao(motivo: str) -> None:
    """Reemissão exige motivo ≥ 50 chars (US-CER-004). Raise se não."""
    if len(motivo.strip()) < _MOTIVO_REEMISSAO_MIN:
        raise MotivoReemissaoInsuficienteError(
            f"motivo de reemissão exige >= {_MOTIVO_REEMISSAO_MIN} chars "
            f"(US-CER-004); recebeu {len(motivo.strip())}"
        )


def perfil_e_acreditado(perfil: str) -> bool:
    """Só perfil A (acreditado CGCRE) emite RBC (ADR-0067)."""
    return perfil.strip().upper() == _PERFIL_ACREDITADO


def validar_completude_decisoes_rt(
    *,
    pontos_nao_rbc: Collection[Decimal],
    pontos_com_decisao: Collection[Decimal],
    perfil: str,
) -> None:
    """Perfil A: TODO ponto não-RBC precisa de decisão do RT antes de emitir;
    faltando → `ReconciliacaoPendenteDecisaoRTError` (422, sem persistir — NC-03).
    Perfis B/C/D NÃO bloqueiam (ressalva registrada)."""
    if not perfil_e_acreditado(perfil):
        return
    com_decisao = set(pontos_com_decisao)
    faltantes = [p for p in pontos_nao_rbc if p not in com_decisao]
    if faltantes:
        raise ReconciliacaoPendenteDecisaoRTError(
            f"perfil A: {len(faltantes)} ponto(s) não-RBC sem decisão do RT "
            f"(ex.: {faltantes[0]}) — emissão bloqueada"
        )


def exigir_ressalva_nao_rbc(decisao_rt: DecisaoReconciliacaoRT, ressalva: str) -> None:
    """`EMITIR_NAO_RBC_NO_PONTO` exige `ressalva_nao_rbc` não-vazia (C-03 /
    cl. 8.1.3 / ADR-0075). Raise `RessalvaNaoRbcObrigatoriaError` se vazia."""
    if decisao_rt is DecisaoReconciliacaoRT.EMITIR_NAO_RBC_NO_PONTO and not ressalva.strip():
        raise RessalvaNaoRbcObrigatoriaError(
            "EMITIR_NAO_RBC_NO_PONTO exige ressalva não-RBC (cl. 8.1.3)"
        )


# Categorias que SÓ fazem sentido para uma classificação específica (T-CER-014,
# C-02 / cl. 7.10.1). As demais (PADRAO_FORA_VALIDADE/FALHA_REPETIBILIDADE/
# CONDICAO_AMBIENTAL_NC/OUTRO) são razões físicas legítimas para excluir qualquer
# ponto problemático — o RT tem autonomia clínica.
_CATEGORIA_EXIGE_CLASSIFICACAO: dict[CategoriaMotivoExclusao, ClassificacaoPonto] = {
    CategoriaMotivoExclusao.PONTO_FORA_FAIXA_DECLARADA: ClassificacaoPonto.FORA_DECLARADA,
    CategoriaMotivoExclusao.U_MAIOR_QUE_CMC_BUG: ClassificacaoPonto.U_MENOR_CMC,
}


def categoria_coerente(
    classificacao: ClassificacaoPonto, categoria: CategoriaMotivoExclusao
) -> bool:
    """True se a `categoria_motivo` é coerente com a `classificacao` do ponto.

    Ex.: `PONTO_FORA_FAIXA_DECLARADA` só vale para `FORA_DECLARADA`;
    `U_MAIOR_QUE_CMC_BUG` só para `U_MENOR_CMC` (CMC otimista perante a U real).
    Categorias físicas/`OUTRO` valem para qualquer classificação."""
    exigida = _CATEGORIA_EXIGE_CLASSIFICACAO.get(categoria)
    return exigida is None or exigida is classificacao
