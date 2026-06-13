"""Funcoes puras de calculo e validacao do modulo `precificacao` (T-PRC-014).

Sem I/O, sem Django. Determinismo bit-a-bit garantido por:
  - `Decimal` em todo calculo (sem float)
  - `ROUND_HALF_EVEN` escala 2
  - Conversao pra fracao via `Percentual.fracao()` (nunca float division - TL-PRC-18)
  - `canonicalizar` ADR-0029 no fingerprint (reusar helper, nao reimplementar - D-PRC-14)

Formulas canonicas do glossario:
  preco_minimo   = (custo + custo_km) / (1 - pct_imp - pct_com - pct_piso)
  preco_sugerido = (custo + custo_km) / (1 - pct_imp - pct_com - pct_alvo)
  margem_liquida = (preco_final - custo - custo_km - impostos - comissao) / preco_final

Denominador <= 0 -> `ParametrosInviaveis` (422) - NUNCA divisao por zero crua.
"""

from __future__ import annotations

import hashlib
from collections.abc import Sequence
from datetime import datetime
from decimal import ROUND_HALF_EVEN, Decimal
from uuid import UUID

from src.domain.metrologia.calibracao.hash_versionado import (
    canonicalizar_payload_para_hmac,
)
from src.domain.produtos_pecas_servicos.entities import PrecoResolvido

from .entities import (
    FaixaAprovacaoDesconto,
    ParametrosPrecificacaoTenant,
    PerfilComposicaoPreco,
    RegraFormacaoPreco,
)
from .enums import Alcada, ModoFormacaoPreco, ModoMontagem, OrigemCusto, Semaforo
from .erros import (
    DecisorNaoIndependente,
    FaixasDescontoInvalidas,
    ParametrosInviaveis,
    PrecoMinimoViolado,
)
from .value_objects import CalculoPrecoResultado, ItemCalculado, Percentual

_ESCALA = Decimal("0.01")
_ZERO = Decimal("0")
_CEM = Decimal("100")

# Versão do motor — incrementada quando fórmulas canônicas mudam.
# Testes de determinismo bit-a-bit comparam o hash do resultado com esta versão.
MOTOR_VERSAO: str = "v1"


# ---------------------------------------------------------------------------
# Funções auxiliares internas
# ---------------------------------------------------------------------------


def _quantizar(v: Decimal) -> Decimal:
    """Arredonda para escala 2 com ROUND_HALF_EVEN (determinismo fiscal)."""
    return v.quantize(_ESCALA, rounding=ROUND_HALF_EVEN)


def _denominador_seguro(valor: Decimal, descricao: str) -> Decimal:
    """Valida denominador > 0; levanta ParametrosInviaveis se ≤ 0."""
    if valor <= _ZERO:
        raise ParametrosInviaveis(
            f"Denominador inválido em {descricao}: {valor} ≤ 0 — "
            "verificar margem_alvo_pct, margem_piso_pct, imposto e comissão "
            "(TL-PRC-18 / D-PRC-8)."
        )
    return valor


# ---------------------------------------------------------------------------
# Cálculo de preço para UM item (função auxiliar interna)
# ---------------------------------------------------------------------------


def _calcular_item(
    *,
    preco_base: PrecoResolvido,
    regra: RegraFormacaoPreco | None,
    custo: Decimal | None,
    origem_custo: OrigemCusto,
    desconto_pct: Percentual,
    params: ParametrosPrecificacaoTenant,
    km: Decimal,
    parcelas: int,
    aliquota_imposto_fracao: Decimal,
) -> ItemCalculado:
    """Calcula preço para um item a partir da regra e custo disponíveis.

    Retorna ItemCalculado com preco_final, semáforo, margem estimada,
    custo estimado, preço mínimo e origem do custo.

    Denominador ≤ 0 → ParametrosInviaveis (fórmulas do glossário.md).
    """
    preco_venda = preco_base.preco.valor  # Decimal
    custo_km = _quantizar(params.custo_km * km)
    comissao_fracao = params.pct_comissao_prevista.fracao()
    taxa_parcela_fracao = params.taxa_parcelamento_mensal.fracao()

    # Juros de parcelamento (simples): preco × taxa × n parcelas
    juros = _ZERO
    if parcelas > 1:
        juros = _quantizar(preco_venda * taxa_parcela_fracao * Decimal(parcelas))

    # Preço base efetivo = preço de venda + juros de parcelamento
    preco_efetivo = _quantizar(preco_venda + juros)

    # --- Sem regra de formação ---
    if regra is None:
        preco_com_desconto = _quantizar(
            preco_efetivo * (Decimal("1") - desconto_pct.fracao())
        )
        preco_final = max(_ZERO, preco_com_desconto)
        return ItemCalculado(
            preco_base=preco_base,
            preco_final=preco_final,
            desconto_pct=desconto_pct,
            semaforo=Semaforo.INDISPONIVEL,
            origem_custo=OrigemCusto.INDISPONIVEL,
            sem_regra_formacao=True,
            cortesia=(desconto_pct.valor == _CEM),
        )

    # --- PRECO_FIXO ---
    if regra.modo == ModoFormacaoPreco.PRECO_FIXO:
        preco_fixo = regra.preco_fixo or _ZERO
        preco_com_desconto = _quantizar(preco_fixo * (Decimal("1") - desconto_pct.fracao()))
        preco_final = max(_ZERO, preco_com_desconto)
        return ItemCalculado(
            preco_base=preco_base,
            preco_final=preco_final,
            desconto_pct=desconto_pct,
            semaforo=Semaforo.INDISPONIVEL,  # sem custo → semáforo indisponível
            origem_custo=OrigemCusto.INDISPONIVEL,
            sem_regra_formacao=False,
            cortesia=(desconto_pct.valor == _CEM),
        )

    # --- MARGEM_ALVO ou COST_PLUS (requer custo) ---
    if custo is None or origem_custo == OrigemCusto.INDISPONIVEL:
        # Custo indisponível → sem semáforo calculável
        preco_com_desconto = _quantizar(
            preco_efetivo * (Decimal("1") - desconto_pct.fracao())
        )
        preco_final = max(_ZERO, preco_com_desconto)
        return ItemCalculado(
            preco_base=preco_base,
            preco_final=preco_final,
            desconto_pct=desconto_pct,
            semaforo=Semaforo.INDISPONIVEL,
            origem_custo=OrigemCusto.INDISPONIVEL,
            sem_regra_formacao=False,
            cortesia=(desconto_pct.valor == _CEM),
        )

    # Custo disponível → fórmulas canônicas do glossário
    custo_total = _quantizar(custo + custo_km)

    margem_alvo_pct = regra.margem_alvo_pct or params.margem_alvo_default
    margem_piso_pct = regra.margem_piso_pct or params.margem_piso_default

    # preço_sugerido = custo_total / (1 - %imp - %com - %alvo)
    denom_sugerido = _denominador_seguro(
        Decimal("1") - aliquota_imposto_fracao - comissao_fracao - margem_alvo_pct.fracao(),
        "preço_sugerido (margem_alvo)",
    )
    preco_sugerido = _quantizar(custo_total / denom_sugerido)

    # preço_mínimo = custo_total / (1 - %imp - %com - %piso)
    denom_minimo = _denominador_seguro(
        Decimal("1") - aliquota_imposto_fracao - comissao_fracao - margem_piso_pct.fracao(),
        "preço_mínimo (margem_piso)",
    )
    preco_minimo = _quantizar(custo_total / denom_minimo)

    # Preço final com desconto
    preco_com_desconto = _quantizar(
        preco_sugerido * (Decimal("1") - desconto_pct.fracao())
    )
    preco_final = max(_ZERO, preco_com_desconto)

    # Verificar bloqueio de mínimo (D-PRC-8 — INV-PRC-MINIMO-BLOQUEIO)
    if preco_final < preco_minimo and desconto_pct.valor < _CEM:
        raise PrecoMinimoViolado(
            f"Preço final {preco_final} < preço mínimo {preco_minimo} "
            f"(custo={custo_total}, desconto={desconto_pct}%) — "
            "bloqueio DURO, não aprovável (INV-PRC-MINIMO-BLOQUEIO / D-PRC-8)."
        )

    # Margem líquida estimada = (preco_final - custo_total - impostos - comissao) / preco_final
    # custo_total = custo + custo_km (linha 161 — deslocamento incluso)
    imposto_estimado = _quantizar(preco_final * aliquota_imposto_fracao)
    comissao_estimada = _quantizar(preco_final * comissao_fracao)
    margem_estimada_valor = _ZERO
    if preco_final > _ZERO:
        margem_estimada_valor = _quantizar(
            (preco_final - custo_total - imposto_estimado - comissao_estimada)
            / preco_final
            * _CEM
        )

    # Semáforo de margem (D-PRC-4)
    if margem_estimada_valor >= margem_alvo_pct.valor:
        semaforo = Semaforo.VERDE
    elif margem_estimada_valor >= margem_piso_pct.valor:
        semaforo = Semaforo.AMARELO
    else:
        semaforo = Semaforo.VERMELHO

    return ItemCalculado(
        preco_base=preco_base,
        preco_final=preco_final,
        desconto_pct=desconto_pct,
        semaforo=semaforo,
        margem_estimada=margem_estimada_valor,
        custo_estimado=_quantizar(custo_total),
        preco_minimo=preco_minimo,
        origem_custo=origem_custo,
        custo_declarado_em=regra.custo_referencia_em,
        sem_regra_formacao=False,
        cortesia=(desconto_pct.valor == _CEM),
    )


# ---------------------------------------------------------------------------
# calcular_precos — função pública principal (D-PRC-11)
# ---------------------------------------------------------------------------


def calcular_precos(
    *,
    itens: Sequence[PrecoResolvido],
    regras: dict[UUID, RegraFormacaoPreco],  # item_id → regra vigente (pode ser vazio)
    custos: dict[UUID, Decimal | None],  # item_id → custo (None = indisponível)
    origens: dict[UUID, OrigemCusto],  # item_id → origem do custo
    perfis: dict[UUID, PerfilComposicaoPreco],  # item_id_servico → perfil (opcional)
    faixas: list[FaixaAprovacaoDesconto],
    params: ParametrosPrecificacaoTenant,
    desconto_pct: Percentual,
    modo_montagem: ModoMontagem,
    km: Decimal,
    parcelas: int,
    aliquota_imposto_fracao: Decimal,
    imposto_ref: tuple[UUID, int] | None,
    motor_versao: str = MOTOR_VERSAO,
) -> CalculoPrecoResultado:
    """Calcula preços para uma CESTA de itens (D-PRC-11 — entrada canônica é a cesta).

    Stateless e determinístico: mesmas entradas → mesmo resultado (AC-PRC-002-3 / TL-PRC-18).
    NÃO persiste nada — consumidor (orçamento/OS) carimba o snapshot (D-PRC-9 / INV-026).

    Args:
      itens: cesta de PrecoResolvido (cada um com item_id, preco, refs probatórias).
      regras: mapa item_id → RegraFormacaoPreco vigente (ausente → sem_regra_formacao).
      custos: mapa item_id → custo Decimal ou None (None = indisponível, origem INDISPONIVEL).
      origens: mapa item_id → OrigemCusto (CUSTO_MANUAL / PROVIDER_REAL / INDISPONIVEL).
      perfis: mapa item_id_servico → PerfilComposicaoPreco (COMPONENTES_CHECKLIST).
      faixas: faixas de aprovação vigentes do tenant.
      params: parâmetros de precificação do tenant (custo_km, taxas, margens default).
      desconto_pct: percentual de desconto solicitado (0..100).
      modo_montagem: COMPONENTES_CHECKLIST ou FECHADO_COM_AVISO.
      km: distância de deslocamento em km (pode ser 0).
      parcelas: número de parcelas (1 = à vista).
      aliquota_imposto_fracao: alíquota de imposto vigente (Decimal, ex: 0.10 para 10%).
      imposto_ref: (id, versao_n) do Imposto usado — carimba referência para replay.
      motor_versao: versão do motor (rastreabilidade AC-PRC-002-3).

    Returns:
      CalculoPrecoResultado frozen com todos os campos preenchidos.

    Raises:
      PrecoMinimoViolado: se preco_final < preco_minimo calculável (bloqueio DURO).
      ParametrosInviaveis: se denominador ≤ 0 nas fórmulas.
    """
    itens_calculados: list[ItemCalculado] = []
    ids_cesta: set[UUID] = {item.item_id for item in itens}

    for preco_base in itens:
        item_id = preco_base.item_id
        regra = regras.get(item_id)
        custo = custos.get(item_id)
        origem = origens.get(item_id, OrigemCusto.INDISPONIVEL)

        item_calc = _calcular_item(
            preco_base=preco_base,
            regra=regra,
            custo=custo,
            origem_custo=origem,
            desconto_pct=desconto_pct,
            params=params,
            km=km,
            parcelas=parcelas,
            aliquota_imposto_fracao=aliquota_imposto_fracao,
        )
        itens_calculados.append(item_calc)

    # Componentes faltantes (D-PRC-2 — COMPONENTES_CHECKLIST)
    componentes_faltantes: list[UUID] = []
    avisos: list[str] = []
    if modo_montagem == ModoMontagem.COMPONENTES_CHECKLIST:
        for item_id_servico, perfil in perfis.items():
            if item_id_servico in ids_cesta:
                for comp_id in perfil.componentes_esperados:
                    if comp_id not in ids_cesta:
                        componentes_faltantes.append(comp_id)
    elif modo_montagem == ModoMontagem.FECHADO_COM_AVISO:
        for perfil in perfis.values():
            if perfil.aviso_texto:
                avisos.append(perfil.aviso_texto)

    # Alçada máxima necessária (D-PRC-3)
    alcada_exigida = alcada_para_pct(desconto_pct, faixas)

    # Versão de hash do conjunto de faixas
    faixas_versao = (
        faixas[0].hash_conjunto if faixas else ""
    )

    # Eco das entradas para replay bit-a-bit
    eco_entradas: dict[str, str] = {
        "km": str(km),
        "desconto_pct": str(desconto_pct.valor),
        "modo_montagem": modo_montagem.value,
        "parcelas": str(parcelas),
        "aliquota_imposto_fracao": str(aliquota_imposto_fracao),
    }

    return CalculoPrecoResultado(
        itens=tuple(itens_calculados),
        componentes_faltantes=tuple(componentes_faltantes),
        avisos=tuple(avisos),
        alcada_exigida=alcada_exigida,
        motor_versao=motor_versao,
        faixas_versao=faixas_versao,
        imposto_ref=imposto_ref,
        parametros_versao=params.versao_n,
        eco_entradas=eco_entradas,
    )


# ---------------------------------------------------------------------------
# validar_vigencia_nao_retroativa
# ---------------------------------------------------------------------------


def validar_vigencia_nao_retroativa(
    *,
    inicio_nova: datetime,
    vigente_atual: RegraFormacaoPreco | None,
    agora: datetime,
) -> None:
    """INV-PPS-PRECO-NAO-RETROATIVO adaptado pra RegraFormacaoPreco (spec §5 / D-PRC-7).

    Nova regra exige `inicio_nova >= max(agora, inicio_da_vigente)` —
    encerrar a anterior NÃO pode truncar vigência já decorrida.

    Args:
      inicio_nova: início da vigência da nova regra (UTC-aware).
      vigente_atual: regra atualmente vigente para o item (None se nenhuma).
      agora: instante atual (UTC-aware).

    Raises:
      ValueError: se inicio_nova < piso.
    """
    piso = agora
    if vigente_atual is not None and vigente_atual.vigencia.inicio > piso:
        piso = vigente_atual.vigencia.inicio
    if inicio_nova < piso:
        raise ValueError(
            f"vigencia_inicio {inicio_nova.isoformat()} anterior ao piso "
            f"{piso.isoformat()} — nova regra não trunca história da vigente (D-PRC-7)."
        )


# ---------------------------------------------------------------------------
# validar_faixas_contiguas
# ---------------------------------------------------------------------------


def validar_faixas_contiguas(faixas: Sequence[FaixaAprovacaoDesconto]) -> None:
    """INV-PRC-FAIXAS-CONTIGUAS — conjunto cobre [0..100] exatamente sem buraco nem sobreposição.

    Replace-all atômico (D-PRC-3 / TL-PRC-16): valida o CONJUNTO COMPLETO antes de persistir.

    Regras:
      1. Conjunto não pode ser vazio.
      2. Primeira faixa começa em 0.
      3. Última faixa termina em 100.
      4. Faixas ordenadas por pct_de, contíguas (pct_ate[i] == pct_de[i+1]).
      5. Nenhuma faixa com pct_de >= pct_ate (largura > 0).

    Args:
      faixas: conjunto completo de faixas candidatas.

    Raises:
      FaixasDescontoInvalidas: se qualquer regra for violada.
    """
    if not faixas:
        raise FaixasDescontoInvalidas(
            "Conjunto de faixas não pode ser vazio (INV-PRC-FAIXAS-CONTIGUAS)."
        )

    ordenadas = sorted(faixas, key=lambda f: f.pct_de.valor)

    if ordenadas[0].pct_de.valor != _ZERO:
        raise FaixasDescontoInvalidas(
            f"Primeira faixa deve começar em 0 (achou {ordenadas[0].pct_de.valor}) "
            "— INV-PRC-FAIXAS-CONTIGUAS."
        )

    if ordenadas[-1].pct_ate.valor != _CEM:
        raise FaixasDescontoInvalidas(
            f"Última faixa deve terminar em 100 (achou {ordenadas[-1].pct_ate.valor}) "
            "— INV-PRC-FAIXAS-CONTIGUAS."
        )

    for i, faixa in enumerate(ordenadas):
        if faixa.pct_de.valor >= faixa.pct_ate.valor:
            raise FaixasDescontoInvalidas(
                f"Faixa {i}: pct_de={faixa.pct_de.valor} >= pct_ate={faixa.pct_ate.valor} "
                "— faixa sem largura (INV-PRC-FAIXAS-CONTIGUAS)."
            )
        if i < len(ordenadas) - 1:
            prox = ordenadas[i + 1]
            if faixa.pct_ate.valor != prox.pct_de.valor:
                raise FaixasDescontoInvalidas(
                    f"Buraco/sobreposição entre faixa {i} (ate={faixa.pct_ate.valor}) "
                    f"e faixa {i+1} (de={prox.pct_de.valor}) "
                    "— INV-PRC-FAIXAS-CONTIGUAS."
                )


# ---------------------------------------------------------------------------
# fingerprint_calculo — ADR-0029 (reusar canonicalizar, não reimplementar)
# ---------------------------------------------------------------------------


def fingerprint_calculo(
    *,
    entradas: dict[str, str],
    refs: dict[str, str],
    desconto_pct: Decimal,
) -> str:
    """Hash canônico ADR-0029 das entradas + refs + pct (D-PRC-14 / TL-PRC-08).

    Binding aprovação↔cálculo: consumidor só usa aprovação se o fingerprint
    do cálculo vigente bater com o gerado na solicitação.

    Usa `canonicalizar_payload_para_hmac` de
    `src.domain.metrologia.calibracao.hash_versionado` (ADR-0029, helper de
    DOMÍNIO — não reimplementado; camada de domínio não importa infrastructure).

    Args:
      entradas: eco das entradas do cálculo (km, modo_montagem, parcelas, etc.).
      refs: referências de versão (motor_versao, faixas_versao, parametros_versao, etc.).
      desconto_pct: percentual de desconto solicitado (Decimal).

    Returns:
      SHA-256 hex do payload canonicalizado (64 chars hex).
    """
    payload = {
        "entradas": entradas,
        "refs": refs,
        "desconto_pct": str(desconto_pct),
    }
    return hashlib.sha256(canonicalizar_payload_para_hmac(payload)).hexdigest()  # audit-pii-salt: skip -- fingerprint de binding aprovacao<->calculo (D-PRC-14): entradas de calculo + refs de versao + pct, ZERO PII; nao e pseudonimizacao de pessoa


# ---------------------------------------------------------------------------
# validar_decisor_independente
# ---------------------------------------------------------------------------


def validar_decisor_independente(
    *,
    decisor_id: UUID,
    solicitante_id: UUID,
) -> None:
    """INV-PRC-APROVACAO-INDEPENDENTE — decisor != solicitante (molde ADR-0026).

    Quem solicitou o desconto não pode aprovar o próprio pedido.

    Args:
      decisor_id: UUID do usuário que decide.
      solicitante_id: UUID do usuário que solicitou.

    Raises:
      DecisorNaoIndependente: se decisor_id == solicitante_id.
    """
    if decisor_id == solicitante_id:
        raise DecisorNaoIndependente(
            f"Decisor {decisor_id} == solicitante {solicitante_id} — "
            "aprovação de desconto exige independência (INV-PRC-APROVACAO-INDEPENDENTE / ADR-0026)."
        )


# ---------------------------------------------------------------------------
# alcada_para_pct
# ---------------------------------------------------------------------------


def alcada_para_pct(
    desconto_pct: Percentual,
    faixas: Sequence[FaixaAprovacaoDesconto],
) -> Alcada:
    """Determina a alçada exigida para um percentual de desconto (D-PRC-3).

    Busca a faixa cujo intervalo [pct_de, pct_ate) cobre o desconto.
    Semântica half-open: [pct_de, pct_ate) → pct_de <= desconto < pct_ate.
    Caso especial: desconto == 100 (cortesia) → DONO sempre (D-PRC-13).

    Se não houver faixa aplicável (conjunto incompleto ou vazio), retorna DONO
    como default conservador (fail-closed — nunca concede mais do que o necessário).

    Args:
      desconto_pct: percentual de desconto a avaliar (0..100).
      faixas: conjunto de faixas do tenant.

    Returns:
      Alcada exigida para o desconto.
    """
    # Cortesia 100%: DONO sempre (D-PRC-13)
    if desconto_pct.valor == _CEM:
        return Alcada.DONO

    for faixa in faixas:
        if faixa.pct_de.valor <= desconto_pct.valor < faixa.pct_ate.valor:
            return faixa.alcada

    # Sem faixa aplicável → fail-closed (DONO)
    return Alcada.DONO
