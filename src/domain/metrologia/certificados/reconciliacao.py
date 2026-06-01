"""Reconciliação de cobertura ponto-a-ponto do certificado (M8 Fatia 0,
T-CER-001/002).

PURO (Decimal, sem Django). COMPÕE as peças já validadas cl. 7.11 — NÃO
reimplementa geometria nem a decisão `U ≥ CMC`:
  - `value_objects.FaixaMedicao.contem`        → ponto ∈ faixa declarada
  - `escopos_cmc.cobertura.avaliar_u_cmc`      → `U(ponto) ≥ CMC(ponto)` (ILAC-P14 §5.5)
  - `escopos_cmc.cobertura.u_igual_cmc_suspeita` → flag anti-cópia (NC-06)
  - read-model `OrcamentoPorPontoSnapshot` (ADR-0077) → `U(ponto)`+k+nível+nu_eff
    por lookup ÚNICO. A `U(ponto)` já agrega as N repetições do ponto via Tipo A
    (`s/√n`); NUNCA se soma U por repetição (dupla contagem — INV-CER-RECONCILIA-005).

ADR-0076: a cobertura DEFINITIVA mede-se contra os pontos EFETIVAMENTE medidos
(CGCRE não extrapola) — `pontos ⊆ declarada` + `U ≥ CMC` + faixa do certificado =
`[min,max]` dos pontos VÁLIDOS (metadado; os pontos discretos são a verdade).

Faz os passos 1-4 + 6 do plan §2. O passo 5 (decisão WORM do RT sobre pontos
problemáticos) e o congelamento `reconciliacao_hash` são da Fatia 2/1a.
`cmc_para=None` ⇒ emissão NÃO-RBC (perfis B/C/D, ou perfil A com acreditação
vencida/suspensa já rebaixada pelo use case — INV-CER-CGCRE-VIG-001).
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from uuid import UUID

from src.domain.metrologia.calibracao.entities import OrcamentoPorPontoSnapshot
from src.domain.metrologia.escopos_cmc import cobertura
from src.domain.metrologia.value_objects import FaixaMedicao, Grandeza

from .enums import ClassificacaoPonto
from .erros import OrcamentoPontoAmbiguoError, SemOrcamentoPontoError
from .portas import CmcParaPort


@dataclass(frozen=True, slots=True)
class PontoMedido:
    """Entrada: um ponto distinto medido. O use case agrupa `LeituraSnapshot` por
    `ponto_calibracao` e deriva o `valor_reportado` (média das repetições); a
    reconciliação é pura — recebe já agrupado."""

    ponto_calibracao: Decimal
    valor_reportado: Decimal
    unidade: str


@dataclass(frozen=True, slots=True)
class PontoReconciliado:
    """Resultado puro da reconciliação de UM ponto. A Fatia 1a persiste este
    mesmo conteúdo (`PontoReconciliadoSnapshot`) acrescido de `ressalva_nao_rbc`
    (texto da decisão RT — cl. 8.1.3 / C-03)."""

    ponto_calibracao: Decimal
    valor_reportado: Decimal
    U_no_ponto: Decimal  # U é notação metrológica canônica (NIT-DICLA-030)
    k_no_ponto: Decimal
    nivel_confianca_no_ponto: Decimal
    grau_liberdade_efetivo_no_ponto: Decimal  # nu_eff (999999 = infinito prático)
    cmc_no_ponto: Decimal | None  # None ⇒ não-RBC no ponto
    classificacao: ClassificacaoPonto
    u_igual_cmc_suspeita: bool
    incluido_no_certificado: bool  # default pré-decisão-RT (Fatia 2 ajusta)


@dataclass(frozen=True, slots=True)
class ReconciliacaoCertificado:
    """VO puro: reconciliação de TODOS os pontos (plan §2). Pontos ordenados
    canonicamente por `ponto_calibracao` ASC (INV-CER-RECONCILIA-004)."""

    pontos: tuple[PontoReconciliado, ...]
    pontos_rbc: tuple[PontoReconciliado, ...]
    pontos_nao_rbc: tuple[PontoReconciliado, ...]
    faixa_certificado_min: Decimal | None
    faixa_certificado_max: Decimal | None
    pode_emitir_rbc: bool


def _indexar_orcamentos(
    orcamentos: Sequence[OrcamentoPorPontoSnapshot],
) -> dict[Decimal, OrcamentoPorPontoSnapshot]:
    """Lookup 1:1 de `U(ponto)` por `ponto_calibracao`. Duplicidade → fail-closed
    (C-01 / INV-CER-RECONCILIA-005)."""
    idx: dict[Decimal, OrcamentoPorPontoSnapshot] = {}
    for orc in orcamentos:
        if orc.ponto_calibracao in idx:
            raise OrcamentoPontoAmbiguoError(
                f"2+ OrcamentoPorPonto para ponto {orc.ponto_calibracao} — lookup "
                f"de U(ponto) deve ser 1:1 (INV-CER-RECONCILIA-005)"
            )
        idx[orc.ponto_calibracao] = orc
    return idx


def _classificar(
    *, dentro_declarada: bool, cmc: Decimal | None, contexto_rbc: bool, u: Decimal
) -> tuple[ClassificacaoPonto, bool]:
    """Precedência fixa `FORA_DECLARADA > SEM_CMC > U_MENOR_CMC > RBC_OK`.

    Retorna `(classificacao, incluido_no_certificado)` — inclusão é o default
    pré-decisão-RT: pontos problemáticos em contexto RBC ficam fora até o RT
    decidir (Fatia 2); em contexto não-RBC (B/C/D) o ponto dentro da declarada é
    válido (caminho normal sem acreditação).
    """
    if not dentro_declarada:
        return ClassificacaoPonto.FORA_DECLARADA, False
    if cmc is None:
        # Sem CMC: B/C/D = válido não-RBC; perfil A = fora do escopo (pendente RT).
        return ClassificacaoPonto.SEM_CMC, (not contexto_rbc)
    atende, _ = cobertura.avaliar_u_cmc(u_reportada=u, cmc_no_ponto=cmc)
    if atende:
        return ClassificacaoPonto.RBC_OK, True
    return ClassificacaoPonto.U_MENOR_CMC, False


def reconciliar_pontos(
    *,
    pontos_medidos: Sequence[PontoMedido],
    orcamentos_por_ponto: Sequence[OrcamentoPorPontoSnapshot],
    faixa_declarada: FaixaMedicao,
    grandeza: Grandeza,
    cmc_para: CmcParaPort | None,
    data_emissao: date,
    tenant_id: UUID,
) -> ReconciliacaoCertificado:
    """Reconcilia a cobertura ponto-a-ponto (plan §2 passos 1-4 + 6).

    Pré-condições fail-closed: nenhum ponto medido → `SemOrcamentoPontoError`;
    ponto sem orçamento → `SemOrcamentoPontoError`; orçamento duplicado por ponto
    → `OrcamentoPontoAmbiguoError`. `cmc_para=None` ⇒ não-RBC.
    """
    if not pontos_medidos:
        raise SemOrcamentoPontoError("reconciliação chamada sem pontos medidos")

    idx = _indexar_orcamentos(orcamentos_por_ponto)
    contexto_rbc = cmc_para is not None
    reconciliados: list[PontoReconciliado] = []

    for ponto in pontos_medidos:
        orc = idx.get(ponto.ponto_calibracao)
        if orc is None:
            raise SemOrcamentoPontoError(
                f"ponto {ponto.ponto_calibracao} sem OrcamentoPorPonto "
                f"(pré-condição da emissão — SEM_ORCAMENTO)"
            )
        u = orc.U_expandida_no_ponto
        # Contenção declarada com unidade fail-closed (espelha faixa_contida).
        dentro = (
            ponto.unidade == faixa_declarada.unidade
            and faixa_declarada.contem(ponto.ponto_calibracao)
        )
        # CMC só é consultada quando há contexto RBC E o ponto está dentro.
        cmc: Decimal | None = None
        if cmc_para is not None and dentro:
            cmc = cmc_para(
                tenant_id=tenant_id,
                grandeza=grandeza,
                ponto=ponto.ponto_calibracao,
                data=data_emissao,
            )
        classificacao, incluido = _classificar(
            dentro_declarada=dentro, cmc=cmc, contexto_rbc=contexto_rbc, u=u
        )
        suspeita = cmc is not None and cobertura.u_igual_cmc_suspeita(
            u_reportada=u, cmc_no_ponto=cmc
        )
        reconciliados.append(
            PontoReconciliado(
                ponto_calibracao=ponto.ponto_calibracao,
                valor_reportado=ponto.valor_reportado,
                U_no_ponto=u,
                k_no_ponto=orc.k_no_ponto,
                nivel_confianca_no_ponto=orc.nivel_confianca_no_ponto,
                grau_liberdade_efetivo_no_ponto=orc.grau_liberdade_efetivo_no_ponto,
                cmc_no_ponto=cmc,
                classificacao=classificacao,
                u_igual_cmc_suspeita=suspeita,
                incluido_no_certificado=incluido,
            )
        )

    # Ordenação canônica ASC antes de calcular a faixa (INV-CER-RECONCILIA-004).
    reconciliados.sort(key=lambda p: p.ponto_calibracao)
    pontos = tuple(reconciliados)
    pontos_rbc = tuple(p for p in pontos if p.classificacao is ClassificacaoPonto.RBC_OK)
    pontos_nao_rbc = tuple(
        p for p in pontos if p.classificacao is not ClassificacaoPonto.RBC_OK
    )

    validos = [p.ponto_calibracao for p in pontos if p.incluido_no_certificado]
    faixa_min = min(validos, default=None)
    faixa_max = max(validos, default=None)

    # RBC só é emissível quando há pontos RBC E nenhum ponto problemático pendente.
    pode_emitir_rbc = contexto_rbc and bool(pontos_rbc) and not pontos_nao_rbc

    return ReconciliacaoCertificado(
        pontos=pontos,
        pontos_rbc=pontos_rbc,
        pontos_nao_rbc=pontos_nao_rbc,
        faixa_certificado_min=faixa_min,
        faixa_certificado_max=faixa_max,
        pode_emitir_rbc=pode_emitir_rbc,
    )
