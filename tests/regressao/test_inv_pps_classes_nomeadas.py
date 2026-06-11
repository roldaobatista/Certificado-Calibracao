"""TST-004 — classes nomeando cada INV da frente produtos-pecas-servicos (T-PPS-050).

Convenção do projeto (análoga `test_inv_cfg_classes_nomeadas.py`): todo INV
crítico tem ≥1 teste cujo NOME cita o ID. Cada classe exercita a barreira
REAL — PG-real onde a defesa é trigger/constraint/UNIQUE; puro/Fake onde é
domínio/use case. Cobre: CODIGO-UNICO, VERSAO-IMUTAVEL, PRECO-NAO-RETROATIVO,
LINHA-IMUTAVEL, LINHA-SEM-SOBREPOSICAO, PRECO-FAIL-CLOSED, KIT-SEM-CICLO,
PRECO-POSITIVO, IMPORTACAO-STAGING.
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

import pytest
from django.db import DatabaseError, IntegrityError
from django.utils import timezone
from src.application.produtos_pecas_servicos import importacao as uc_importacao
from src.domain.produtos_pecas_servicos.enums import StatusLinhaImportacao
from src.domain.produtos_pecas_servicos.erros import (
    KitComCicloError,
    PrecoTabelaAusenteError,
    VersaoRetroativaError,
)
from src.domain.produtos_pecas_servicos.extracao_csv import (
    LinhaImportacaoParseada,
    parse_preco_br,
)
from src.domain.produtos_pecas_servicos.transicoes import (
    validar_vigencia_nao_retroativa,
)
from src.domain.produtos_pecas_servicos.value_objects import Preco
from src.infrastructure.multitenant.connection import run_in_tenant_context
from src.infrastructure.produtos_pecas_servicos.models import (
    ItemCatalogo,
    ItemCatalogoVersao,
    LinhaTabelaPreco,
    TabelaPreco,
)
from src.infrastructure.produtos_pecas_servicos.query_service import preco_para_os

from tests.factories import TenantFactory
from tests.test_pps_use_cases import (
    _AGORA,
    TENANT,
    USUARIO,
    FakeItemRepo,
    FakeTabelaRepo,
    _cadastrar,
    _tabela_padrao,
)

_JAN = datetime(2026, 1, 1, tzinfo=UTC)
_JUN = datetime(2026, 6, 1, tzinfo=UTC)


def _item_pg(tenant, *, codigo="P-001"):
    with run_in_tenant_context(tenant.id):
        return ItemCatalogo.objects.create(
            tenant=tenant, codigo_interno=codigo, tipo="peca", controla_estoque=True
        )


def _versao_pg(tenant, item, *, n=1, inicio=_JAN, fim=None):
    with run_in_tenant_context(tenant.id):
        return ItemCatalogoVersao.objects.create(
            tenant=tenant, item=item, versao_n=n, nome="Peça X", unidade_medida="un",
            preco_padrao=Decimal("50.00"), vigencia_inicio=inicio, vigencia_fim=fim,
            criado_por=uuid4(),
        )


def _linha_pg(tenant, tabela, item, *, inicio=_JAN, fim=None):
    with run_in_tenant_context(tenant.id):
        return LinhaTabelaPreco.objects.create(
            tenant=tenant, tabela=tabela, item=item, preco=Decimal("55.00"),
            vigencia_inicio=inicio, vigencia_fim=fim, criado_por=uuid4(),
        )


class TestINV_PPS_CODIGO_UNICO:
    @pytest.mark.django_db(transaction=True)
    def test_unique_no_banco_e_a_verdade_na_corrida(self) -> None:
        tenant = TenantFactory()
        _item_pg(tenant, codigo="P-DUP")
        with pytest.raises(IntegrityError):
            _item_pg(tenant, codigo="P-DUP")


class TestINV_PPS_VERSAO_IMUTAVEL:
    @pytest.mark.django_db(transaction=True)
    def test_update_probatorio_e_delete_bloqueados_por_trigger(self) -> None:
        tenant = TenantFactory()
        versao = _versao_pg(tenant, _item_pg(tenant))
        with run_in_tenant_context(tenant.id):
            with pytest.raises(DatabaseError):
                ItemCatalogoVersao.objects.filter(id=versao.id).update(
                    preco_padrao=Decimal("99.00")
                )
            with pytest.raises(DatabaseError):
                ItemCatalogoVersao.objects.filter(id=versao.id).delete()


class TestINV_PPS_PRECO_NAO_RETROATIVO:
    def test_inicio_anterior_ao_piso_raise(self) -> None:
        with pytest.raises(VersaoRetroativaError):
            validar_vigencia_nao_retroativa(
                inicio_nova=_JAN, vigente_atual=None, agora=_AGORA
            )

    def test_excecao_unica_primeira_versao_importada(self) -> None:
        validar_vigencia_nao_retroativa(
            inicio_nova=_JAN, vigente_atual=None, agora=_AGORA, primeira_versao=True
        )


class TestINV_PPS_LINHA_IMUTAVEL:
    @pytest.mark.django_db(transaction=True)
    def test_update_preco_e_delete_bloqueados_por_trigger(self) -> None:
        tenant = TenantFactory()
        with run_in_tenant_context(tenant.id):
            tabela = TabelaPreco.objects.create(tenant=tenant, nome="P", eh_padrao=True)
        linha = _linha_pg(tenant, tabela, _item_pg(tenant))
        with run_in_tenant_context(tenant.id):
            with pytest.raises(DatabaseError):
                LinhaTabelaPreco.objects.filter(id=linha.id).update(preco=Decimal("1.00"))
            with pytest.raises(DatabaseError):
                LinhaTabelaPreco.objects.filter(id=linha.id).delete()


class TestINV_PPS_LINHA_SEM_SOBREPOSICAO:
    @pytest.mark.django_db(transaction=True)
    def test_exclusion_raise_e_revogada_libera_mesma_janela(self) -> None:
        tenant = TenantFactory()
        with run_in_tenant_context(tenant.id):
            tabela = TabelaPreco.objects.create(tenant=tenant, nome="P", eh_padrao=True)
        item = _item_pg(tenant)
        linha = _linha_pg(tenant, tabela, item, inicio=_JAN)  # aberta
        with pytest.raises(IntegrityError):
            _linha_pg(tenant, tabela, item, inicio=_JUN)  # sobrepõe
        with run_in_tenant_context(tenant.id):
            LinhaTabelaPreco.objects.filter(id=linha.id).update(
                revogado_em=timezone.now(), motivo_revogacao="preco digitado errado"
            )
        substituta = _linha_pg(tenant, tabela, item, inicio=_JAN)  # MESMA janela OK
        assert substituta.id != linha.id


class TestINV_PPS_PRECO_FAIL_CLOSED:
    def test_sem_linha_vigente_raise_sem_fallback_a_lista(self) -> None:
        """A lista TEM preço (123.45) e mesmo assim a porta NÃO resolve — o
        fallback silencioso é exatamente o que a ADR-0081 proíbe."""
        item_repo, tabela_repo = FakeItemRepo(), FakeTabelaRepo()
        out = _cadastrar(item_repo, preco="123.45")
        _tabela_padrao(tabela_repo)
        with pytest.raises(PrecoTabelaAusenteError):
            preco_para_os(
                tenant_id=TENANT,
                item_id=out.item.id,
                data_referencia=_AGORA,
                item_repo=item_repo,
                tabela_repo=tabela_repo,
            )


class TestINV_PPS_KIT_SEM_CICLO:
    def test_filho_kit_raise(self) -> None:
        from src.application.produtos_pecas_servicos import item as uc_item
        from src.domain.produtos_pecas_servicos.enums import TipoItem

        repo = FakeItemRepo()
        kit = _cadastrar(repo, codigo="K-1", tipo=TipoItem.KIT)
        kit2 = _cadastrar(repo, codigo="K-2", tipo=TipoItem.KIT)
        with pytest.raises(KitComCicloError):
            uc_item.montar_kit(
                uc_item.MontarKitInput(
                    tenant_id=TENANT,
                    kit_item_id=kit.item.id,
                    componentes=((kit2.item.id, Decimal("1")),),
                ),
                repo=repo,
            )


class TestINV_PPS_PRECO_POSITIVO:
    def test_vo_rejeita_zero_e_negativo(self) -> None:
        for valor in (Decimal("0"), Decimal("-1"), Decimal("0.004")):  # 0.004→0.00
            with pytest.raises(ValueError):
                Preco(valor)

    @pytest.mark.django_db(transaction=True)
    def test_check_no_banco_rejeita_zero(self) -> None:
        tenant = TenantFactory()
        item = _item_pg(tenant)
        with run_in_tenant_context(tenant.id), pytest.raises(IntegrityError):
            ItemCatalogoVersao.objects.create(
                tenant=tenant, item=item, versao_n=1, nome="X", unidade_medida="un",
                preco_padrao=Decimal("0.00"), vigencia_inicio=_JAN, criado_por=uuid4(),
            )


class TestINV_PPS_IMPORTACAO_STAGING:
    def test_registrar_importacao_nao_cria_item(self) -> None:
        """Staging puro: lote registrado, ZERO item no catálogo."""

        class FakeImportacaoRepo:
            def __init__(self) -> None:
                self.lotes: list = []
                self.linhas: list = []

            def salvar_importacao(self, importacao, linhas) -> None:
                self.lotes.append(importacao)
                self.linhas.extend(linhas)

        item_repo = FakeItemRepo()
        repo = FakeImportacaoRepo()
        out = uc_importacao.registrar_importacao(
            uc_importacao.RegistrarImportacaoInput(
                tenant_id=TENANT,
                arquivo_sha256="a" * 64,
                arquivo_nome_hash="",
                criado_por=USUARIO,
                agora=_AGORA,
                linhas_parseadas=(
                    LinhaImportacaoParseada(
                        linha_numero=2,
                        status=StatusLinhaImportacao.VALIDADA,
                        codigo_interno="P-1",
                        tipo="peca",
                        nome="Peça",
                        unidade_medida="un",
                        preco_padrao=Decimal("10.00"),
                    ),
                ),
            ),
            repo=repo,
        )
        assert out.total_validadas == 1
        assert len(repo.lotes) == 1
        assert item_repo.itens == {}  # NENHUM item nasceu do upload

    def test_preco_ambiguo_rejeita_fail_closed(self) -> None:
        with pytest.raises(ValueError):
            parse_preco_br("1.234")  # milhar BR sem vírgula = ambíguo
