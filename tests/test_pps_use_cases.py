"""Frente `produtos-pecas-servicos` — Fatia 2 (T-PPS-035): use cases PUROS com Fakes.

Cobre o que não depende de PG: anti-retroatividade (TL-PPS-08), ordem
revoga→recria do corrigir (D-PPS-8), kit (ciclo/inativo/soma das partes),
tabela padrão única, default sugerido (ADR-0081) e o CONTRATO da porta
`preco_para_os` (T-PPS-032 — repos injetáveis; fail-closed em todas as
ausências; refs probatórias completas). Reconciliação de centavos TL-PPS-15.
"""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID, uuid4

import pytest
from src.application.produtos_pecas_servicos import item as uc_item
from src.application.produtos_pecas_servicos import tabela as uc_tabela
from src.domain.produtos_pecas_servicos.entities import (
    ItemCatalogo,
    ItemCatalogoVersao,
    KitComposicao,
    LinhaTabelaPreco,
    TabelaPreco,
)
from src.domain.produtos_pecas_servicos.enums import (
    OrigemPreco,
    StatusItem,
    TipoItem,
)
from src.domain.produtos_pecas_servicos.erros import (
    CodigoDuplicadoError,
    ItemInativoError,
    KitComCicloError,
    PrecoTabelaAusenteError,
    TabelaPadraoDuplicadaError,
    VersaoRetroativaError,
)
from src.infrastructure.produtos_pecas_servicos.query_service import preco_para_os

TENANT = uuid4()
USUARIO = uuid4()
_T0 = datetime(2026, 1, 1, tzinfo=UTC)
_AGORA = datetime(2026, 6, 11, 12, 0, tzinfo=UTC)


class FakeItemRepo:
    """Fake em memória do ItemCatalogoRepository (lock = no-op; registra ordem)."""

    def __init__(self) -> None:
        self.itens: dict[UUID, ItemCatalogo] = {}
        self.versoes: dict[UUID, ItemCatalogoVersao] = {}
        self.composicoes: dict[UUID, list[KitComposicao]] = {}
        self.chamadas: list[str] = []

    def obter(self, *, tenant_id: UUID, item_id: UUID) -> ItemCatalogo | None:
        i = self.itens.get(item_id)
        return i if i is not None and i.tenant_id == tenant_id else None

    def obter_por_codigo(self, *, tenant_id: UUID, codigo_interno: str) -> ItemCatalogo | None:
        for i in self.itens.values():
            if i.tenant_id == tenant_id and i.codigo_interno == codigo_interno:
                return i
        return None

    def salvar(self, item: ItemCatalogo) -> None:
        self.chamadas.append("salvar")
        self.itens[item.id] = item

    def travar_item(self, *, tenant_id: UUID, item_id: UUID) -> None:
        self.chamadas.append("travar_item")

    def listar_versoes(self, *, tenant_id: UUID, item_id: UUID) -> list[ItemCatalogoVersao]:
        return [
            v
            for v in self.versoes.values()
            if v.tenant_id == tenant_id and v.item_id == item_id
        ]

    def salvar_versao(self, versao: ItemCatalogoVersao) -> None:
        self.chamadas.append("salvar_versao")
        self.versoes[versao.id] = versao

    def encerrar_vigencia_versao(self, *, tenant_id: UUID, versao_id: UUID, fim: datetime) -> None:
        self.chamadas.append("encerrar_vigencia_versao")
        v = self.versoes.get(versao_id)
        if v is None or v.vigencia.fim is not None:
            raise RuntimeError("versão sem vigência aberta pra encerrar.")
        self.versoes[versao_id] = replace(v, vigencia=replace(v.vigencia, fim=fim))

    def revogar_versao(self, *, tenant_id: UUID, versao_id: UUID, motivo: str) -> None:
        self.chamadas.append("revogar_versao")
        v = self.versoes.get(versao_id)
        if v is None or v.vigencia.revogado_em is not None:
            raise RuntimeError("versão já revogada ou inexistente.")
        self.versoes[versao_id] = replace(
            v,
            vigencia=replace(v.vigencia, revogado_em=_AGORA, motivo_revogacao=motivo),
        )

    def listar_composicao(self, *, tenant_id: UUID, kit_item_id: UUID) -> list[KitComposicao]:
        return list(self.composicoes.get(kit_item_id, []))

    def substituir_composicao(
        self, *, tenant_id: UUID, kit_item_id: UUID, composicao: list[KitComposicao]
    ) -> None:
        self.chamadas.append("substituir_composicao")
        self.composicoes[kit_item_id] = list(composicao)


class FakeTabelaRepo:
    """Fake em memória do TabelaPrecoRepository."""

    def __init__(self) -> None:
        self.tabelas: dict[UUID, TabelaPreco] = {}
        self.linhas: dict[UUID, LinhaTabelaPreco] = {}
        self.chamadas: list[str] = []

    def obter_padrao(self, *, tenant_id: UUID) -> TabelaPreco | None:
        for t in self.tabelas.values():
            if t.tenant_id == tenant_id and t.eh_padrao:
                return t
        return None

    def obter(self, *, tenant_id: UUID, tabela_id: UUID) -> TabelaPreco | None:
        t = self.tabelas.get(tabela_id)
        return t if t is not None and t.tenant_id == tenant_id else None

    def salvar(self, tabela: TabelaPreco) -> None:
        self.tabelas[tabela.id] = tabela

    def travar_linha(self, *, tenant_id: UUID, tabela_id: UUID, item_id: UUID) -> None:
        self.chamadas.append("travar_linha")

    def obter_linha(
        self, *, tenant_id: UUID, tabela_id: UUID, linha_id: UUID
    ) -> LinhaTabelaPreco | None:
        linha = self.linhas.get(linha_id)
        if linha is None or linha.tenant_id != tenant_id or linha.tabela_id != tabela_id:
            return None
        return linha

    def listar_linhas(
        self, *, tenant_id: UUID, tabela_id: UUID, item_id: UUID | None = None
    ) -> list[LinhaTabelaPreco]:
        linhas = [
            linha
            for linha in self.linhas.values()
            if linha.tenant_id == tenant_id and linha.tabela_id == tabela_id
        ]
        if item_id is not None:
            linhas = [linha for linha in linhas if linha.item_id == item_id]
        return linhas

    def salvar_linha(self, linha: LinhaTabelaPreco) -> None:
        self.chamadas.append("salvar_linha")
        self.linhas[linha.id] = linha

    def encerrar_vigencia_linha(self, *, tenant_id: UUID, linha_id: UUID, fim: datetime) -> None:
        linha = self.linhas.get(linha_id)
        if linha is None or linha.vigencia.fim is not None:
            raise RuntimeError("linha sem vigência aberta pra encerrar.")
        self.linhas[linha_id] = replace(linha, vigencia=replace(linha.vigencia, fim=fim))

    def revogar_linha(self, *, tenant_id: UUID, linha_id: UUID, motivo: str) -> None:
        self.chamadas.append("revogar_linha")
        linha = self.linhas.get(linha_id)
        if linha is None or linha.vigencia.revogado_em is not None:
            raise RuntimeError("linha já revogada ou inexistente.")
        self.linhas[linha_id] = replace(
            linha,
            vigencia=replace(linha.vigencia, revogado_em=_AGORA, motivo_revogacao=motivo),
        )


def _cadastrar(repo: FakeItemRepo, *, codigo="P-001", tipo=TipoItem.PECA, preco="50.00", **kw):
    return uc_item.cadastrar_item(
        uc_item.CadastrarItemInput(
            tenant_id=TENANT,
            codigo_interno=codigo,
            tipo=tipo,
            nome=f"Item {codigo}",
            unidade_medida="un",
            preco_padrao=Decimal(preco),
            criado_por=USUARIO,
            agora=_AGORA,
            **kw,
        ),
        repo=repo,
    )


# === cadastrar_item (US-CAT-001) ===


def test_cadastrar_cria_item_ativo_e_v1():
    repo = FakeItemRepo()
    out = _cadastrar(repo)
    assert out.item.status == StatusItem.ATIVO
    assert out.item.controla_estoque is True  # peca → True (derivado)
    assert out.versao.versao_n == 1
    assert out.versao.vigencia.inicio == _AGORA
    assert out.versao.preco_padrao.valor == Decimal("50.00")


def test_cadastrar_servico_e_kit_nao_controlam_estoque_por_default():
    repo = FakeItemRepo()
    servico = _cadastrar(repo, codigo="S-001", tipo=TipoItem.SERVICO)
    kit = _cadastrar(repo, codigo="K-001", tipo=TipoItem.KIT)
    assert servico.item.controla_estoque is False
    assert kit.item.controla_estoque is False


def test_cadastrar_codigo_duplicado_raise():
    repo = FakeItemRepo()
    _cadastrar(repo)
    with pytest.raises(CodigoDuplicadoError):
        _cadastrar(repo)


def test_cadastrar_vigencia_passada_so_com_importacao():
    repo = FakeItemRepo()
    with pytest.raises(VersaoRetroativaError):
        _cadastrar(repo, vigencia_inicio=_T0)
    out = _cadastrar(repo, codigo="P-IMP", vigencia_inicio=_T0, importacao=True)
    assert out.versao.vigencia.inicio == _T0


# === nova_versao_preco (US-CAT-002 / TL-PPS-08) ===


def test_nova_versao_encerra_anterior_e_e_densa():
    repo = FakeItemRepo()
    out1 = _cadastrar(repo, vigencia_inicio=_T0, importacao=True)
    depois = datetime(2026, 7, 1, tzinfo=UTC)
    out2 = uc_item.nova_versao_preco(
        uc_item.NovaVersaoPrecoInput(
            tenant_id=TENANT,
            item_id=out1.item.id,
            preco_padrao=Decimal("60.00"),
            criado_por=USUARIO,
            agora=_AGORA,
            vigencia_inicio=depois,
        ),
        repo=repo,
    )
    assert out2.versao.versao_n == 2
    assert out2.versao.nome == out1.versao.nome  # herda da base
    assert out2.versao_encerrada_id == out1.versao.id
    v1 = repo.versoes[out1.versao.id]
    # INV-026: v1 NÃO muda — só ganha fim exatamente no início da nova.
    assert v1.vigencia.fim == depois
    assert v1.preco_padrao.valor == Decimal("50.00")


def test_nova_versao_retroativa_raise():
    repo = FakeItemRepo()
    out1 = _cadastrar(repo, vigencia_inicio=_T0, importacao=True)
    with pytest.raises(VersaoRetroativaError):
        uc_item.nova_versao_preco(
            uc_item.NovaVersaoPrecoInput(
                tenant_id=TENANT,
                item_id=out1.item.id,
                preco_padrao=Decimal("60.00"),
                criado_por=USUARIO,
                agora=_AGORA,
                vigencia_inicio=datetime(2026, 3, 1, tzinfo=UTC),  # < agora
            ),
            repo=repo,
        )


def test_nova_versao_item_inativo_raise():
    repo = FakeItemRepo()
    out = _cadastrar(repo)
    uc_item.inativar_item(
        uc_item.InativarItemInput(tenant_id=TENANT, item_id=out.item.id), repo=repo
    )
    with pytest.raises(ItemInativoError):
        uc_item.nova_versao_preco(
            uc_item.NovaVersaoPrecoInput(
                tenant_id=TENANT,
                item_id=out.item.id,
                preco_padrao=Decimal("60.00"),
                criado_por=USUARIO,
                agora=_AGORA,
            ),
            repo=repo,
        )


def test_nova_versao_item_inexistente_raise_404():
    with pytest.raises(uc_item.ItemAusenteError):
        uc_item.nova_versao_preco(
            uc_item.NovaVersaoPrecoInput(
                tenant_id=TENANT,
                item_id=uuid4(),
                preco_padrao=Decimal("60.00"),
                criado_por=USUARIO,
                agora=_AGORA,
            ),
            repo=FakeItemRepo(),
        )


# === corrigir_versao (D-PPS-8) ===


def test_corrigir_versao_revoga_antes_de_recriar_na_mesma_janela():
    repo = FakeItemRepo()
    out = _cadastrar(repo, vigencia_inicio=_T0, importacao=True)
    repo.chamadas.clear()
    corrigida = uc_item.corrigir_versao(
        uc_item.CorrigirVersaoInput(
            tenant_id=TENANT,
            item_id=out.item.id,
            versao_id=out.versao.id,
            motivo="preço digitado errado na importação",
            criado_por=USUARIO,
            preco_padrao=Decimal("55.00"),
        ),
        repo=repo,
    )
    # ORDEM importa (exclusion WHERE revogado_em IS NULL): revoga → recria.
    assert repo.chamadas.index("revogar_versao") < repo.chamadas.index("salvar_versao")
    revogada = repo.versoes[out.versao.id]
    assert revogada.vigencia.revogado_em is not None
    assert corrigida.versao.versao_n == 2
    assert corrigida.versao.vigencia.inicio == revogada.vigencia.inicio  # MESMA janela
    assert corrigida.versao.preco_padrao.valor == Decimal("55.00")
    assert corrigida.versao.nome == revogada.nome  # preserva o que não mudou


def test_corrigir_versao_motivo_curto_raise():
    repo = FakeItemRepo()
    out = _cadastrar(repo)
    with pytest.raises(ValueError, match="motivo"):
        uc_item.corrigir_versao(
            uc_item.CorrigirVersaoInput(
                tenant_id=TENANT,
                item_id=out.item.id,
                versao_id=out.versao.id,
                motivo="curto",
                criado_por=USUARIO,
            ),
            repo=repo,
        )


def test_corrigir_versao_ja_revogada_raise_409():
    repo = FakeItemRepo()
    out = _cadastrar(repo)
    inp = uc_item.CorrigirVersaoInput(
        tenant_id=TENANT,
        item_id=out.item.id,
        versao_id=out.versao.id,
        motivo="preço digitado errado de novo",
        criado_por=USUARIO,
        preco_padrao=Decimal("51.00"),
    )
    uc_item.corrigir_versao(inp, repo=repo)
    with pytest.raises(RuntimeError):
        uc_item.corrigir_versao(inp, repo=repo)


# === inativar (US-CAT-005) + kit (US-CAT-003) ===


def test_inativar_e_inativar_de_novo_raise():
    repo = FakeItemRepo()
    out = _cadastrar(repo)
    item = uc_item.inativar_item(
        uc_item.InativarItemInput(tenant_id=TENANT, item_id=out.item.id), repo=repo
    )
    assert item.status == StatusItem.INATIVO
    with pytest.raises(ItemInativoError):
        uc_item.inativar_item(
            uc_item.InativarItemInput(tenant_id=TENANT, item_id=out.item.id), repo=repo
        )


def test_montar_kit_substitui_composicao():
    repo = FakeItemRepo()
    kit = _cadastrar(repo, codigo="K-001", tipo=TipoItem.KIT)
    p1 = _cadastrar(repo, codigo="P-001")
    p2 = _cadastrar(repo, codigo="P-002")
    composicao = uc_item.montar_kit(
        uc_item.MontarKitInput(
            tenant_id=TENANT,
            kit_item_id=kit.item.id,
            componentes=((p1.item.id, Decimal("2")), (p2.item.id, Decimal("0.5"))),
        ),
        repo=repo,
    )
    assert len(composicao) == 2
    assert repo.composicoes[kit.item.id] == composicao


def test_montar_kit_com_filho_kit_raise():
    repo = FakeItemRepo()
    kit = _cadastrar(repo, codigo="K-001", tipo=TipoItem.KIT)
    outro_kit = _cadastrar(repo, codigo="K-002", tipo=TipoItem.KIT)
    with pytest.raises(KitComCicloError):
        uc_item.montar_kit(
            uc_item.MontarKitInput(
                tenant_id=TENANT,
                kit_item_id=kit.item.id,
                componentes=((outro_kit.item.id, Decimal("1")),),
            ),
            repo=repo,
        )


def test_montar_kit_com_filho_inativo_raise():
    repo = FakeItemRepo()
    kit = _cadastrar(repo, codigo="K-001", tipo=TipoItem.KIT)
    p1 = _cadastrar(repo, codigo="P-001")
    uc_item.inativar_item(
        uc_item.InativarItemInput(tenant_id=TENANT, item_id=p1.item.id), repo=repo
    )
    with pytest.raises(ItemInativoError):
        uc_item.montar_kit(
            uc_item.MontarKitInput(
                tenant_id=TENANT,
                kit_item_id=kit.item.id,
                componentes=((p1.item.id, Decimal("1")),),
            ),
            repo=repo,
        )


# === tabela + linha (ADR-0081) ===


def _tabela_padrao(repo: FakeTabelaRepo) -> TabelaPreco:
    return uc_tabela.criar_tabela(
        uc_tabela.CriarTabelaInput(tenant_id=TENANT, nome="Padrão"), repo=repo
    )


def test_segunda_tabela_padrao_raise():
    repo = FakeTabelaRepo()
    _tabela_padrao(repo)
    with pytest.raises(TabelaPadraoDuplicadaError):
        _tabela_padrao(repo)


def test_criar_linha_default_sugerido_da_lista_origem_manual():
    item_repo, tabela_repo = FakeItemRepo(), FakeTabelaRepo()
    out = _cadastrar(item_repo, preco="123.45")
    tabela = _tabela_padrao(tabela_repo)
    criada = uc_tabela.criar_linha(
        uc_tabela.CriarLinhaInput(
            tenant_id=TENANT,
            tabela_id=tabela.id,
            item_id=out.item.id,
            criado_por=USUARIO,
            agora=_AGORA,
        ),
        tabela_repo=tabela_repo,
        item_repo=item_repo,
    )
    assert criada.linha.preco.valor == Decimal("123.45")
    assert criada.linha.origem_sugestao == OrigemPreco.MANUAL


def test_criar_linha_kit_soma_das_partes_reconcilia_centavos():
    """TL-PPS-15: qtd fracionária × preço escala 2 — soma exata, sem deriva."""
    item_repo, tabela_repo = FakeItemRepo(), FakeTabelaRepo()
    kit = _cadastrar(item_repo, codigo="K-001", tipo=TipoItem.KIT, preco="1.00")
    p1 = _cadastrar(item_repo, codigo="P-001", preco="33.33")
    p2 = _cadastrar(item_repo, codigo="P-002", preco="0.10")
    uc_item.montar_kit(
        uc_item.MontarKitInput(
            tenant_id=TENANT,
            kit_item_id=kit.item.id,
            componentes=((p1.item.id, Decimal("3")), (p2.item.id, Decimal("0.5"))),
        ),
        repo=item_repo,
    )
    tabela = _tabela_padrao(tabela_repo)
    criada = uc_tabela.criar_linha(
        uc_tabela.CriarLinhaInput(
            tenant_id=TENANT,
            tabela_id=tabela.id,
            item_id=kit.item.id,
            criado_por=USUARIO,
            agora=_AGORA,
        ),
        tabela_repo=tabela_repo,
        item_repo=item_repo,
    )
    # 3×33.33 + 0.5×0.10 = 99.99 + 0.05 = 100.04 (exato; em_centavos inteiro)
    assert criada.linha.preco.valor == Decimal("100.04")
    assert criada.linha.preco.em_centavos() == 10004
    assert criada.linha.origem_sugestao == OrigemPreco.SOMA_PARTES


def test_criar_linha_kit_sem_composicao_raise():
    item_repo, tabela_repo = FakeItemRepo(), FakeTabelaRepo()
    kit = _cadastrar(item_repo, codigo="K-001", tipo=TipoItem.KIT)
    tabela = _tabela_padrao(tabela_repo)
    with pytest.raises(uc_tabela.SugestaoPrecoIndisponivelError):
        uc_tabela.criar_linha(
            uc_tabela.CriarLinhaInput(
                tenant_id=TENANT,
                tabela_id=tabela.id,
                item_id=kit.item.id,
                criado_por=USUARIO,
                agora=_AGORA,
            ),
            tabela_repo=tabela_repo,
            item_repo=item_repo,
        )


def test_criar_linha_sobreposta_raise():
    item_repo, tabela_repo = FakeItemRepo(), FakeTabelaRepo()
    out = _cadastrar(item_repo)
    tabela = _tabela_padrao(tabela_repo)
    inp = uc_tabela.CriarLinhaInput(
        tenant_id=TENANT,
        tabela_id=tabela.id,
        item_id=out.item.id,
        criado_por=USUARIO,
        agora=_AGORA,
        preco=Decimal("10.00"),
    )
    uc_tabela.criar_linha(inp, tabela_repo=tabela_repo, item_repo=item_repo)
    with pytest.raises(uc_tabela.LinhaSobrepostaError):
        uc_tabela.criar_linha(inp, tabela_repo=tabela_repo, item_repo=item_repo)


def test_criar_linha_item_inativo_raise():
    item_repo, tabela_repo = FakeItemRepo(), FakeTabelaRepo()
    out = _cadastrar(item_repo)
    uc_item.inativar_item(
        uc_item.InativarItemInput(tenant_id=TENANT, item_id=out.item.id), repo=item_repo
    )
    tabela = _tabela_padrao(tabela_repo)
    with pytest.raises(ItemInativoError):
        uc_tabela.criar_linha(
            uc_tabela.CriarLinhaInput(
                tenant_id=TENANT,
                tabela_id=tabela.id,
                item_id=out.item.id,
                criado_por=USUARIO,
                agora=_AGORA,
                preco=Decimal("10.00"),
            ),
            tabela_repo=tabela_repo,
            item_repo=item_repo,
        )


def test_corrigir_linha_revoga_antes_de_recriar():
    item_repo, tabela_repo = FakeItemRepo(), FakeTabelaRepo()
    out = _cadastrar(item_repo)
    tabela = _tabela_padrao(tabela_repo)
    criada = uc_tabela.criar_linha(
        uc_tabela.CriarLinhaInput(
            tenant_id=TENANT,
            tabela_id=tabela.id,
            item_id=out.item.id,
            criado_por=USUARIO,
            agora=_AGORA,
            preco=Decimal("100.00"),
        ),
        tabela_repo=tabela_repo,
        item_repo=item_repo,
    )
    tabela_repo.chamadas.clear()
    corrigida = uc_tabela.corrigir_linha(
        uc_tabela.CorrigirLinhaInput(
            tenant_id=TENANT,
            tabela_id=tabela.id,
            linha_id=criada.linha.id,
            preco=Decimal("90.00"),
            motivo="preço digitado errado pelo operador",
            criado_por=USUARIO,
        ),
        tabela_repo=tabela_repo,
    )
    assert tabela_repo.chamadas.index("revogar_linha") < tabela_repo.chamadas.index(
        "salvar_linha"
    )
    assert corrigida.linha.vigencia.inicio == criada.linha.vigencia.inicio  # MESMA janela
    assert corrigida.linha.preco.valor == Decimal("90.00")
    assert tabela_repo.linhas[criada.linha.id].vigencia.revogado_em is not None


def test_encerrar_linha_one_shot():
    item_repo, tabela_repo = FakeItemRepo(), FakeTabelaRepo()
    out = _cadastrar(item_repo)
    tabela = _tabela_padrao(tabela_repo)
    criada = uc_tabela.criar_linha(
        uc_tabela.CriarLinhaInput(
            tenant_id=TENANT,
            tabela_id=tabela.id,
            item_id=out.item.id,
            criado_por=USUARIO,
            agora=_AGORA,
            preco=Decimal("100.00"),
        ),
        tabela_repo=tabela_repo,
        item_repo=item_repo,
    )
    fim = datetime(2026, 12, 31, tzinfo=UTC)
    inp = uc_tabela.EncerrarLinhaInput(
        tenant_id=TENANT, tabela_id=tabela.id, linha_id=criada.linha.id, fim=fim
    )
    uc_tabela.encerrar_linha(inp, tabela_repo=tabela_repo)
    with pytest.raises(RuntimeError):
        uc_tabela.encerrar_linha(inp, tabela_repo=tabela_repo)


# === contrato da porta preco_para_os (T-PPS-032 — ADR-0081 §4) ===


def _cenario_porta() -> tuple[FakeItemRepo, FakeTabelaRepo, UUID, UUID]:
    item_repo, tabela_repo = FakeItemRepo(), FakeTabelaRepo()
    out = _cadastrar(item_repo, preco="123.45")
    tabela = _tabela_padrao(tabela_repo)
    criada = uc_tabela.criar_linha(
        uc_tabela.CriarLinhaInput(
            tenant_id=TENANT,
            tabela_id=tabela.id,
            item_id=out.item.id,
            criado_por=USUARIO,
            agora=_AGORA,
            preco=Decimal("150.00"),
        ),
        tabela_repo=tabela_repo,
        item_repo=item_repo,
    )
    assert criada is not None
    return item_repo, tabela_repo, out.item.id, tabela.id


def test_porta_vigente_resolve_com_refs_probatorias_completas():
    item_repo, tabela_repo, item_id, tabela_id = _cenario_porta()
    r = preco_para_os(
        tenant_id=TENANT,
        item_id=item_id,
        data_referencia=_AGORA,
        item_repo=item_repo,
        tabela_repo=tabela_repo,
    )
    # VENDA (linha), NÃO o preco_padrao da lista (D-PPS-2 — sem fallback).
    assert r.preco.valor == Decimal("150.00")
    assert r.item_versao_n == 1
    assert r.tabela_id == tabela_id
    assert r.origem_preco == OrigemPreco.MANUAL
    # data_referencia = data da CONTRATAÇÃO ecoada no contrato (ADV-PPS-05).
    assert r.data_referencia == _AGORA


def test_porta_sem_linha_fail_closed_sem_fallback_a_lista():
    item_repo = FakeItemRepo()
    tabela_repo = FakeTabelaRepo()
    out = _cadastrar(item_repo, preco="123.45")
    _tabela_padrao(tabela_repo)  # tabela existe, linha NÃO
    with pytest.raises(PrecoTabelaAusenteError):
        preco_para_os(
            tenant_id=TENANT,
            item_id=out.item.id,
            data_referencia=_AGORA,
            item_repo=item_repo,
            tabela_repo=tabela_repo,
        )


def test_porta_sem_tabela_padrao_fail_closed():
    item_repo = FakeItemRepo()
    out = _cadastrar(item_repo)
    with pytest.raises(PrecoTabelaAusenteError):
        preco_para_os(
            tenant_id=TENANT,
            item_id=out.item.id,
            data_referencia=_AGORA,
            item_repo=item_repo,
            tabela_repo=FakeTabelaRepo(),
        )


def test_porta_linha_revogada_nunca_resolve():
    """Lição M2: revogação é retroativa à janela INTEIRA — mesmo D anterior
    à revogação não resolve a linha revogada."""
    item_repo, tabela_repo, item_id, _ = _cenario_porta()
    (linha_id,) = list(tabela_repo.linhas)
    tabela_repo.revogar_linha(
        tenant_id=TENANT, linha_id=linha_id, motivo="linha digitada errada"
    )
    with pytest.raises(PrecoTabelaAusenteError):
        preco_para_os(
            tenant_id=TENANT,
            item_id=item_id,
            data_referencia=_AGORA,
            item_repo=item_repo,
            tabela_repo=tabela_repo,
        )


def test_porta_item_inativo_erro_distinto():
    item_repo, tabela_repo, item_id, _ = _cenario_porta()
    uc_item.inativar_item(
        uc_item.InativarItemInput(tenant_id=TENANT, item_id=item_id), repo=item_repo
    )
    with pytest.raises(ItemInativoError):
        preco_para_os(
            tenant_id=TENANT,
            item_id=item_id,
            data_referencia=_AGORA,
            item_repo=item_repo,
            tabela_repo=tabela_repo,
        )


def test_porta_kit_sem_linha_propria_fail_closed():
    """TL-PPS-09: soma das partes NUNCA é resolução runtime."""
    item_repo, tabela_repo = FakeItemRepo(), FakeTabelaRepo()
    kit = _cadastrar(item_repo, codigo="K-001", tipo=TipoItem.KIT)
    p1 = _cadastrar(item_repo, codigo="P-001", preco="10.00")
    uc_item.montar_kit(
        uc_item.MontarKitInput(
            tenant_id=TENANT,
            kit_item_id=kit.item.id,
            componentes=((p1.item.id, Decimal("2")),),
        ),
        repo=item_repo,
    )
    _tabela_padrao(tabela_repo)
    with pytest.raises(PrecoTabelaAusenteError):
        preco_para_os(
            tenant_id=TENANT,
            item_id=kit.item.id,
            data_referencia=_AGORA,
            item_repo=item_repo,
            tabela_repo=tabela_repo,
        )


def test_porta_kit_com_linha_propria_resolve_com_composicao():
    item_repo, tabela_repo = FakeItemRepo(), FakeTabelaRepo()
    kit = _cadastrar(item_repo, codigo="K-001", tipo=TipoItem.KIT)
    p1 = _cadastrar(item_repo, codigo="P-001", preco="10.00")
    uc_item.montar_kit(
        uc_item.MontarKitInput(
            tenant_id=TENANT,
            kit_item_id=kit.item.id,
            componentes=((p1.item.id, Decimal("2")),),
        ),
        repo=item_repo,
    )
    tabela = _tabela_padrao(tabela_repo)
    uc_tabela.criar_linha(
        uc_tabela.CriarLinhaInput(
            tenant_id=TENANT,
            tabela_id=tabela.id,
            item_id=kit.item.id,
            criado_por=USUARIO,
            agora=_AGORA,
            preco=Decimal("18.00"),  # preço comercial do kit ≠ soma (20.00)
        ),
        tabela_repo=tabela_repo,
        item_repo=item_repo,
    )
    r = preco_para_os(
        tenant_id=TENANT,
        item_id=kit.item.id,
        data_referencia=_AGORA,
        item_repo=item_repo,
        tabela_repo=tabela_repo,
    )
    assert r.preco.valor == Decimal("18.00")
    assert len(r.composicao_resolvida) == 1
    parte = r.composicao_resolvida[0]
    assert parte.item_filho_id == p1.item.id
    assert parte.quantidade == Decimal("2")
    assert parte.preco_unitario.valor == Decimal("10.00")


def test_porta_kit_decomposicao_all_or_nothing_vazia_quando_parte_sem_versao():
    """P9 QUAL-B3: parte sem versão de lista vigente → composicao_resolvida=()
    (decomposição parcial enganaria a reconciliação de soma — ADV-PPS-08);
    o PREÇO segue resolvendo pela linha própria (TL-PPS-09, sem 422 cascata)."""
    item_repo, tabela_repo = FakeItemRepo(), FakeTabelaRepo()
    kit = _cadastrar(item_repo, codigo="K-001", tipo=TipoItem.KIT)
    # filho com vigência passada (importação) pra poder ENCERRAR antes de _AGORA
    p1 = _cadastrar(
        item_repo, codigo="P-001", preco="10.00", vigencia_inicio=_T0, importacao=True
    )
    uc_item.montar_kit(
        uc_item.MontarKitInput(
            tenant_id=TENANT,
            kit_item_id=kit.item.id,
            componentes=((p1.item.id, Decimal("2")),),
        ),
        repo=item_repo,
    )
    # encerra a única versão de lista do filho ANTES da data de referência
    item_repo.encerrar_vigencia_versao(
        tenant_id=TENANT,
        versao_id=p1.versao.id,
        fim=datetime(2026, 6, 1, tzinfo=UTC),
    )
    tabela = _tabela_padrao(tabela_repo)
    uc_tabela.criar_linha(
        uc_tabela.CriarLinhaInput(
            tenant_id=TENANT,
            tabela_id=tabela.id,
            item_id=kit.item.id,
            criado_por=USUARIO,
            agora=_AGORA,
            preco=Decimal("18.00"),
        ),
        tabela_repo=tabela_repo,
        item_repo=item_repo,
    )
    r = preco_para_os(
        tenant_id=TENANT,
        item_id=kit.item.id,
        data_referencia=_AGORA,
        item_repo=item_repo,
        tabela_repo=tabela_repo,
    )
    assert r.preco.valor == Decimal("18.00")  # linha própria resolve normal
    assert r.composicao_resolvida == ()  # decomposição indisponível, NUNCA parcial
