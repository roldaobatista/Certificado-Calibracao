"""Máquina de estados + regras puras de emissão do certificado (M8 Fatia 1a,
T-CER-015).

Transições válidas de `EstadoCertificado` + validações que os use cases (Fatia 2)
consomem. `RASCUNHO` permanece declarado (compat stub) mas NÃO é materializado
nesta frente — a reconciliação pendurada em `calibracao_id` é a "pré-emissão";
`emitir_certificado` cria a linha já em `EMITIDO` numa transação atômica. Sem
Django (ADR-0007).
"""

from __future__ import annotations

from collections.abc import Collection, Mapping, Sequence
from dataclasses import replace
from datetime import date
from decimal import Decimal
from typing import Protocol

from .enums import (
    CategoriaMotivoExclusao,
    ClassificacaoPonto,
    DecisaoReconciliacaoRT,
    EstadoCertificado,
)
from .erros import (
    EmissaoAbortadaPeloRTError,
    MotivoReemissaoInsuficienteError,
    PadraoCalibracaoVencidaError,
    ReconciliacaoPendenteDecisaoRTError,
    RessalvaNaoRbcObrigatoriaError,
    TransicaoCertificadoInvalidaError,
)
from .reconciliacao import PontoReconciliado

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


# NC-07 / cl. 6.5: chave da vigência da calibração de cada padrão usado no snapshot.
_CHAVE_VIGENCIA_PADRAO = "calibracao_padrao_vigencia_fim"


def _coerce_date(raw: object) -> date | None:
    """Coerção tolerante de uma vigência vinda do snapshot JSON (`date` ou ISO
    `YYYY-MM-DD`). Qualquer outro formato → None (tratado como vigência ausente —
    fail-open lazy, nunca derruba a emissão por dado malformado de origem)."""
    if isinstance(raw, date):
        return raw
    if isinstance(raw, str):
        try:
            return date.fromisoformat(raw[:10])
        except ValueError:
            return None
    return None


def _suspensa_na_data_de_emissao(
    *, suspensa_em: date | None, suspensa_ate: date | None, data_emissao: date
) -> bool:
    """True se a janela de suspensão CGCRE `[suspensa_em, suspensa_ate]` cobre a
    data de emissão. Avaliada contra `data_emissao` (NÃO `today`) — todas as
    condições de conformidade do certificado WORM usam a mesma data de referência,
    eliminando a assimetria temporal (parecer consultor-rbc 2026-06-01). Suspensão
    sem `ate` registrado → não suspensa (cancelamento definitivo é outra direção)."""
    if suspensa_ate is None:
        return False
    if suspensa_em is not None and data_emissao < suspensa_em:
        return False  # suspensão começa depois da emissão → não cobre
    return data_emissao <= suspensa_ate


def acreditacao_vigente_para_rbc(
    *,
    perfil: str,
    acreditacao_vigencia_fim: date | None,
    acreditacao_suspensa_em: date | None,
    acreditacao_suspensa_ate: date | None,
    data_emissao: date,
) -> bool:
    """INV-CER-CGCRE-VIG-001 — só há classificação `RBC_OK` quando o perfil é A,
    a acreditação NÃO está suspensa e está vigente NA data de emissão.

    `acreditacao_vigencia_fim is None` é **fail-open lazy** (assume vigente),
    espelhando ADR-0063/0066/0073: o campo `Tenant.acreditacao_vigencia_fim` é
    novo e pode não estar populado nos tenants A existentes (dogfooding). O
    bloqueio real por VENCIMENTO entra em vigor quando o campo é preenchido —
    GATE-CER-CGCRE-VIG-DATA-POPULAR (Wave A).

    A SUSPENSÃO usa dado já existente (`Tenant.acreditacao_suspensa_em/ate`) e é
    fail-closed imediato, avaliada por janela NA `data_de_emissao` (não `today`).
    Vigência é **inclusiva do último dia** (`>= data_emissao`) — leitura física de
    "válido até DD/MM" e alinhamento de borda com `validar_vigencia_padroes`
    (parecer consultor-rbc 2026-06-01). Comparar com `data_de_emissao` (não `today`)
    preserva o replay determinístico cl. 7.11 do snapshot WORM."""
    if not perfil_e_acreditado(perfil):
        return False
    if _suspensa_na_data_de_emissao(
        suspensa_em=acreditacao_suspensa_em,
        suspensa_ate=acreditacao_suspensa_ate,
        data_emissao=data_emissao,
    ):
        return False
    if acreditacao_vigencia_fim is None:
        return True  # fail-open lazy — GATE-CER-CGCRE-VIG-DATA-POPULAR
    return acreditacao_vigencia_fim >= data_emissao


def validar_vigencia_padroes(
    *,
    snapshot_padroes_usados: Sequence[Mapping[str, object]],
    data_emissao: date,
    perfil: str,
) -> None:
    """INV-CER-PADRAO-VIG-001 (cl. 6.5 / NC-07): perfil A bloqueia a emissão se
    algum padrão usado tinha a calibração vencida na data de emissão
    (`PadraoCalibracaoVencidaError`). Vigência ausente/malformada no snapshot é
    fail-open lazy (campo opcional até o wiring com M5 `padroes` —
    GATE-CER-PADRAO-VIG-SNAPSHOT). Perfis B/C/D não bloqueiam."""
    if not perfil_e_acreditado(perfil):
        return
    for item in snapshot_padroes_usados:
        vig = _coerce_date(item.get(_CHAVE_VIGENCIA_PADRAO))
        if vig is not None and vig < data_emissao:
            raise PadraoCalibracaoVencidaError(
                f"padrão {item.get('padrao_id', '?')} com calibração vencida em "
                f"{vig.isoformat()} < emissão {data_emissao.isoformat()} (cl. 6.5)"
            )


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


class _DecisaoRT(Protocol):
    """Forma estrutural mínima de uma decisão do RT (basta `decisao_rt`).
    `@property` read-only → aceita dataclass frozen (AnaliseReconciliacaoCertificado)."""

    @property
    def decisao_rt(self) -> DecisaoReconciliacaoRT: ...


def aplicar_decisoes_rt(
    pontos: Sequence[PontoReconciliado],
    decisoes_por_ponto: Mapping[Decimal, _DecisaoRT],
) -> list[PontoReconciliado]:
    """Aplica as decisões WORM do RT aos pontos problemáticos (NC-03):

    - `EXCLUIR_PONTO` → `EXCLUIDO`, fora do certificado (`incluido=False`).
    - `EMITIR_NAO_RBC_NO_PONTO` → reportado sem selo RBC (`incluido=True`; a
      `ressalva_nao_rbc` é gravada no snapshot pelo use case).
    - `ABORTAR` → `EmissaoAbortadaPeloRTError` (não emite).

    Pontos `RBC_OK` e não-RBC-válidos (B/C/D `SEM_CMC` sem decisão) ficam intactos.
    A completude das decisões (perfil A) é validada em separado
    (`validar_completude_decisoes_rt`) antes de chamar esta função.
    """
    resultado: list[PontoReconciliado] = []
    for p in pontos:
        dec = decisoes_por_ponto.get(p.ponto_calibracao)
        if not p.classificacao.problematico or dec is None:
            resultado.append(p)
            continue
        if dec.decisao_rt is DecisaoReconciliacaoRT.ABORTAR:
            raise EmissaoAbortadaPeloRTError(
                f"RT abortou a emissão no ponto {p.ponto_calibracao}"
            )
        if dec.decisao_rt is DecisaoReconciliacaoRT.EXCLUIR_PONTO:
            resultado.append(
                replace(
                    p,
                    classificacao=ClassificacaoPonto.EXCLUIDO,
                    incluido_no_certificado=False,
                )
            )
        else:  # EMITIR_NAO_RBC_NO_PONTO
            resultado.append(replace(p, incluido_no_certificado=True))
    return resultado
