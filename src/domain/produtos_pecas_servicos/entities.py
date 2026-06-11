"""Entidades do catálogo (T-PPS-012 — frozen dataclasses, espelham colunas tipadas).

ADR-0081: `ItemCatalogoVersao.preco_padrao` = LISTA histórica imutável;
`LinhaTabelaPreco` = VENDA vigente que a OS consulta fail-closed.
`controla_estoque` vive no ITEM (estrutural — TL-PPS-12), não na versão.
`KitComposicao` NÃO carrega UM própria (TL-PPS-11 — deriva da versão vigente
do filho).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from src.domain.produtos_pecas_servicos.enums import (
    OrigemPreco,
    StatusItem,
    StatusLinhaImportacao,
    TipoItem,
)
from src.domain.produtos_pecas_servicos.value_objects import Preco
from src.domain.shared.value_objects import JanelaVigencia


@dataclass(frozen=True)
class ItemCatalogo:
    """Agregado raiz (US-CAT-001). `codigo_interno`/`tipo` imutáveis;
    `controla_estoque`/`status` estruturais mutáveis com auditoria."""

    id: UUID
    tenant_id: UUID
    codigo_interno: str  # INV-PPS-CODIGO-UNICO por tenant
    tipo: TipoItem
    controla_estoque: bool
    status: StatusItem
    codigo_fabricante: str = ""  # identifica produto, não pessoa (não-PII — ADV-PPS-09)


@dataclass(frozen=True)
class ItemCatalogoVersao:
    """Versão imutável de apresentação+preço de lista (INV-026 / INV-PPS-VERSAO-IMUTAVEL).

    `versao_n` denso por item (max+1 sob advisory lock — TL-PPS-04).
    Linha errada → revogar+recriar (use case composto — D-PPS-8), nunca UPDATE.
    """

    id: UUID
    tenant_id: UUID
    item_id: UUID
    versao_n: int
    nome: str
    unidade_medida: str  # texto curto validado contra seed de UMs (TL-PPS-11)
    preco_padrao: Preco
    vigencia: JanelaVigencia
    criado_por: UUID  # pseudônimo art. 12 LGPD — eventos WORM levam só o hash (ADV-PPS-01)
    descricao: str = ""  # em evento WORM vai HASHIFICADA ADR-0029 (ADV-PPS-02)
    categoria: str = ""
    motivo: str = ""  # idem descricao


@dataclass(frozen=True)
class KitComposicao:
    """Parte de um kit (US-CAT-003). Filho NUNCA é kit (INV-PPS-KIT-SEM-CICLO).

    Sem UM própria (TL-PPS-11 — deriva da versão vigente do filho). Quantidade
    Decimal > 0 (fracionária é legítima: 0.5 kg de solda, 2.5 m de cabo).
    """

    kit_item_id: UUID
    item_filho_id: UUID
    quantidade: Decimal

    def __post_init__(self) -> None:
        if not isinstance(self.quantidade, Decimal):
            raise TypeError(
                f"KitComposicao.quantidade deve ser Decimal, veio {type(self.quantidade)!r}"
            )
        if self.quantidade <= 0:
            raise ValueError(f"KitComposicao.quantidade deve ser > 0 (veio {self.quantidade}).")


@dataclass(frozen=True)
class TabelaPreco:
    """Tabela de venda (D-PPS-3 — schema N-tabelas; MVP trava 1 via `eh_padrao`)."""

    id: UUID
    tenant_id: UUID
    nome: str
    eh_padrao: bool
    descricao: str = ""


@dataclass(frozen=True)
class LinhaTabelaPreco:
    """Preço de VENDA vigente por (tabela, item) — imutável molde Imposto
    (INV-PPS-LINHA-IMUTAVEL + INV-PPS-LINHA-SEM-SOBREPOSICAO)."""

    id: UUID
    tenant_id: UUID
    tabela_id: UUID
    item_id: UUID
    preco: Preco
    vigencia: JanelaVigencia
    criado_por: UUID
    origem_sugestao: OrigemPreco = OrigemPreco.MANUAL


@dataclass(frozen=True)
class ImportacaoCatalogo:
    """Lote de importação CSV em STAGING (US-CAT-004 — molde INV-ECMC-007).

    Mutável no banco (staging, NÃO WORM); TTL 90d (ADV-PPS-06). A prova
    permanente de integridade é o `arquivo_sha256` no evento WORM
    `Catalogo.ImportacaoConcluida` — o arquivo em si não é retido aqui.
    """

    id: UUID
    tenant_id: UUID
    arquivo_sha256: str
    arquivo_nome_hash: str  # nome de arquivo pode carregar PII — só o hash
    total_linhas: int
    criado_por: UUID
    criado_em: datetime


@dataclass(frozen=True)
class LinhaImportacaoCatalogo:
    """Linha do staging — validada|rejeitada|aceita (aceite é one-shot e
    reusa `cadastrar_item`, o caminho canônico; INV-PPS-IMPORTACAO-STAGING)."""

    id: UUID
    tenant_id: UUID
    importacao_id: UUID
    linha_numero: int
    status: StatusLinhaImportacao
    codigo_interno: str = ""
    tipo: str = ""  # produto|peca|servico (kit não importa via CSV)
    nome: str = ""
    unidade_medida: str = ""
    preco_padrao: Decimal | None = None  # parseado (dialeto BR); None se rejeitada
    categoria: str = ""
    descricao: str = ""
    codigo_fabricante: str = ""
    motivo_rejeicao: str = ""
    item_criado_id: UUID | None = None  # preenchido no aceite


@dataclass(frozen=True)
class ComponenteResolvido:
    """Parte de kit resolvida na MESMA data_referencia (TL-PPS-10/ADV-PPS-08)."""

    item_filho_id: UUID
    quantidade: Decimal
    versao_n: int
    preco_unitario: Preco


@dataclass(frozen=True)
class PrecoResolvido:
    """Contrato da porta `preco_para_os` (ADR-0081 §4 — refs probatórias completas).

    Caller (OS/orçamentos) persiste as refs junto do valor (INV-026 ponto 3).
    `data_referencia` = data do fato gerador COMERCIAL (contratação/lançamento),
    não do faturamento (CDC art. 39 X — ADV-PPS-05).
    """

    item_id: UUID
    item_versao_n: int
    linha_tabela_id: UUID
    tabela_id: UUID
    preco: Preco
    data_referencia: datetime
    origem_preco: OrigemPreco
    composicao_resolvida: tuple[ComponenteResolvido, ...] = field(default_factory=tuple)
