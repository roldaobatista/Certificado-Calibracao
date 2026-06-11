"""Frente `produtos-pecas-servicos` — Fatia 1a (T-PPS-015): domínio puro, sem banco.

Cobre: VO Preco (escala/arredondamento/positivo TL-PPS-15/16), anti-retroatividade
TL-PPS-08 (INV-PPS-PRECO-NAO-RETROATIVO), kit sem ciclo (INV-PPS-KIT-SEM-CICLO +
filho inativo AC-CAT-005-1), versão densa max+1 (TL-PPS-04), resolução vigente
(linha/versão revogada NUNCA resolve — lição M2 da frente #1).
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

import pytest
from src.domain.produtos_pecas_servicos.entities import (
    ItemCatalogo,
    ItemCatalogoVersao,
    KitComposicao,
    LinhaTabelaPreco,
)
from src.domain.produtos_pecas_servicos.enums import StatusItem, TipoItem
from src.domain.produtos_pecas_servicos.erros import (
    ItemInativoError,
    KitComCicloError,
    VersaoRetroativaError,
)
from src.domain.produtos_pecas_servicos.transicoes import (
    linha_vigente_em,
    proxima_versao_n,
    validar_kit_sem_ciclo,
    validar_vigencia_nao_retroativa,
    versao_vigente_em,
)
from src.domain.produtos_pecas_servicos.value_objects import Preco
from src.domain.shared.value_objects import JanelaVigencia

_JAN = datetime(2026, 1, 1, tzinfo=UTC)
_JUN = datetime(2026, 6, 1, tzinfo=UTC)
_AGO = datetime(2026, 8, 1, tzinfo=UTC)


def _item(tipo: TipoItem = TipoItem.PECA, status: StatusItem = StatusItem.ATIVO) -> ItemCatalogo:
    return ItemCatalogo(
        id=uuid4(), tenant_id=uuid4(), codigo_interno="P-001", tipo=tipo,
        controla_estoque=tipo is not TipoItem.SERVICO, status=status,
    )


def _versao(
    item_id, n: int, preco: str, inicio=_JAN, fim=None, revogado=False
) -> ItemCatalogoVersao:
    return ItemCatalogoVersao(
        id=uuid4(), tenant_id=uuid4(), item_id=item_id, versao_n=n,
        nome="Peça X", unidade_medida="un", preco_padrao=Preco(Decimal(preco)),
        vigencia=JanelaVigencia(
            inicio=inicio, fim=fim,
            revogado_em=_JUN if revogado else None,
            motivo_revogacao="preco digitado errado" if revogado else None,
        ),
        criado_por=uuid4(),
    )


def _linha(tabela_id, item_id, preco: str, inicio=_JAN, fim=None, revogado=False):
    return LinhaTabelaPreco(
        id=uuid4(), tenant_id=uuid4(), tabela_id=tabela_id, item_id=item_id,
        preco=Preco(Decimal(preco)),
        vigencia=JanelaVigencia(
            inicio=inicio, fim=fim,
            revogado_em=_JUN if revogado else None,
            motivo_revogacao="linha errada corrigida" if revogado else None,
        ),
        criado_por=uuid4(),
    )


# === VO Preco (TL-PPS-15/16) ===


def test_preco_normaliza_escala_2_half_even():
    assert Preco(Decimal("10.005")).valor == Decimal("10.00")  # half-even: 0.5 → par
    assert Preco(Decimal("10.015")).valor == Decimal("10.02")
    assert Preco(Decimal("50")).valor == Decimal("50.00")


def test_preco_zero_ou_negativo_raise():
    with pytest.raises(ValueError):
        Preco(Decimal("0"))
    with pytest.raises(ValueError):
        Preco(Decimal("-1"))
    # 0.004 quantiza pra 0.00 → sentinela da OS preservada (TL-PPS-16)
    with pytest.raises(ValueError):
        Preco(Decimal("0.004"))


def test_preco_em_centavos_reconcilia():
    assert Preco(Decimal("55.50")).em_centavos() == 5550


def test_preco_exige_decimal():
    with pytest.raises(TypeError):
        Preco(55.5)  # type: ignore[arg-type] -- contrato: float proibido (deriva binária)


# === INV-PPS-PRECO-NAO-RETROATIVO (TL-PPS-08) ===


def test_versao_nova_retroativa_raise():
    item_id = uuid4()
    vigente = _versao(item_id, 1, "50.00", inicio=_JAN)
    with pytest.raises(VersaoRetroativaError):
        validar_vigencia_nao_retroativa(
            inicio_nova=_JAN, vigente_atual=vigente, agora=_JUN
        )  # início == passado já decorrido → trunca história


def test_versao_nova_futura_ok():
    item_id = uuid4()
    vigente = _versao(item_id, 1, "50.00", inicio=_JAN)
    validar_vigencia_nao_retroativa(inicio_nova=_AGO, vigente_atual=vigente, agora=_JUN)


def test_primeira_versao_importacao_pode_vigencia_passada():
    validar_vigencia_nao_retroativa(
        inicio_nova=_JAN, vigente_atual=None, agora=_JUN, primeira_versao=True
    )


def test_consulta_historica_nao_muda_apos_nova_versao():
    """Regressão INV-026 DURA: preço vigente em D não muda quando nova versão entra."""
    item_id = uuid4()
    v1 = _versao(item_id, 1, "50.00", inicio=_JAN, fim=_AGO)
    resposta_antes = versao_vigente_em([v1], _JUN)
    v2 = _versao(item_id, 2, "55.00", inicio=_AGO)
    resposta_depois = versao_vigente_em([v1, v2], _JUN)
    assert resposta_antes is not None and resposta_depois is not None
    assert resposta_antes.id == resposta_depois.id  # mesma v1 — história intacta
    assert versao_vigente_em([v1, v2], datetime(2026, 9, 1, tzinfo=UTC)).versao_n == 2


# === kit (INV-PPS-KIT-SEM-CICLO + AC-CAT-005-1) ===


def test_kit_com_filho_kit_raise():
    kit, sub_kit = _item(TipoItem.KIT), _item(TipoItem.KIT)
    comp = [KitComposicao(kit_item_id=kit.id, item_filho_id=sub_kit.id, quantidade=Decimal(1))]
    with pytest.raises(KitComCicloError):
        validar_kit_sem_ciclo(kit=kit, filhos=[sub_kit], composicao=comp)


def test_kit_com_filho_inativo_raise():
    kit, filho = _item(TipoItem.KIT), _item(TipoItem.PECA, StatusItem.INATIVO)
    comp = [KitComposicao(kit_item_id=kit.id, item_filho_id=filho.id, quantidade=Decimal(2))]
    with pytest.raises(ItemInativoError):
        validar_kit_sem_ciclo(kit=kit, filhos=[filho], composicao=comp)


def test_kit_valido_ok_e_vazio_raise():
    kit, p1, s1 = _item(TipoItem.KIT), _item(TipoItem.PECA), _item(TipoItem.SERVICO)
    comp = [
        KitComposicao(kit_item_id=kit.id, item_filho_id=p1.id, quantidade=Decimal("0.5")),
        KitComposicao(kit_item_id=kit.id, item_filho_id=s1.id, quantidade=Decimal(1)),
    ]
    validar_kit_sem_ciclo(kit=kit, filhos=[p1, s1], composicao=comp)
    with pytest.raises(KitComCicloError):
        validar_kit_sem_ciclo(kit=kit, filhos=[], composicao=[])


def test_kit_quantidade_invalida_raise():
    with pytest.raises(ValueError):
        KitComposicao(kit_item_id=uuid4(), item_filho_id=uuid4(), quantidade=Decimal(0))


# === versão densa (TL-PPS-04) ===


def test_proxima_versao_densa():
    item_id = uuid4()
    assert proxima_versao_n([]) == 1
    assert proxima_versao_n([_versao(item_id, 1, "50.00"), _versao(item_id, 2, "55.00")]) == 3


# === resolução vigente (lição M2: revogada NUNCA resolve) ===


def test_linha_revogada_nunca_resolve_mesmo_em_momento_anterior():
    tabela_id, item_id = uuid4(), uuid4()
    revogada = _linha(tabela_id, item_id, "50.00", revogado=True)  # revogada em _JUN
    substituta = _linha(tabela_id, item_id, "45.00")
    # Momento ANTERIOR à revogação: vigente_em(_JAN) da revogada seria True —
    # mas revogação invalida a janela INTEIRA (cadastro errado).
    resolvida = linha_vigente_em(
        [revogada, substituta], tabela_id=tabela_id, item_id=item_id, momento=_JAN
    )
    assert resolvida is not None and resolvida.id == substituta.id


def test_linha_ausente_retorna_none():
    assert (
        linha_vigente_em([], tabela_id=uuid4(), item_id=uuid4(), momento=_JUN) is None
    )


def test_linha_de_outra_tabela_ou_item_nao_resolve():
    tabela_id, item_id = uuid4(), uuid4()
    linha = _linha(tabela_id, item_id, "50.00")
    assert linha_vigente_em([linha], tabela_id=uuid4(), item_id=item_id, momento=_JUN) is None
    assert linha_vigente_em([linha], tabela_id=tabela_id, item_id=uuid4(), momento=_JUN) is None
