"""Use cases da importação CSV em staging — US-CAT-004 (T-PPS-041). PUROS.

INV-PPS-IMPORTACAO-STAGING (molde INV-ECMC-007 do M6): a importação NUNCA
auto-persiste item de catálogo — só cria o lote em STAGING. O aceite é POR
LINHA, one-shot, e REUSA `cadastrar_item` (o caminho canônico — mesmo código
de validação, mesma exceção de vigência passada `importacao=True`).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID, uuid4

from src.application.produtos_pecas_servicos.item import (
    CadastrarItemInput,
    CadastrarItemOutput,
    cadastrar_item,
)
from src.domain.produtos_pecas_servicos.entities import (
    ImportacaoCatalogo,
    LinhaImportacaoCatalogo,
)
from src.domain.produtos_pecas_servicos.enums import StatusLinhaImportacao, TipoItem
from src.domain.produtos_pecas_servicos.extracao_csv import LinhaImportacaoParseada
from src.domain.produtos_pecas_servicos.repository import (
    ImportacaoCatalogoRepository,
    ItemCatalogoRepository,
)


class LinhaImportacaoAusenteError(Exception):
    """Linha inexistente no lote/tenant — view mapeia 404."""


class ImportacaoAusenteError(Exception):
    """Lote inexistente no tenant — view mapeia 404."""


# === registrar_importacao (staging — NÃO cria item) ===


@dataclass(frozen=True, slots=True)
class RegistrarImportacaoInput:
    tenant_id: UUID
    arquivo_sha256: str
    arquivo_nome_hash: str
    criado_por: UUID
    agora: datetime
    linhas_parseadas: tuple[LinhaImportacaoParseada, ...]

    def __post_init__(self) -> None:
        if not self.arquivo_sha256.strip():
            raise ValueError("registrar_importacao: arquivo_sha256 obrigatório.")
        if not self.linhas_parseadas:
            raise ValueError("registrar_importacao: arquivo sem linhas de dados.")


@dataclass(frozen=True, slots=True)
class RegistrarImportacaoOutput:
    importacao: ImportacaoCatalogo
    linhas: tuple[LinhaImportacaoCatalogo, ...]
    total_validadas: int
    total_rejeitadas: int


def registrar_importacao(
    inp: RegistrarImportacaoInput, *, repo: ImportacaoCatalogoRepository
) -> RegistrarImportacaoOutput:
    """Materializa o lote em staging. NENHUM ItemCatalogo nasce aqui."""
    importacao = ImportacaoCatalogo(
        id=uuid4(),
        tenant_id=inp.tenant_id,
        arquivo_sha256=inp.arquivo_sha256,
        arquivo_nome_hash=inp.arquivo_nome_hash,
        total_linhas=len(inp.linhas_parseadas),
        criado_por=inp.criado_por,
        criado_em=inp.agora,
    )
    linhas = tuple(
        LinhaImportacaoCatalogo(
            id=uuid4(),
            tenant_id=inp.tenant_id,
            importacao_id=importacao.id,
            linha_numero=parseada.linha_numero,
            status=parseada.status,
            codigo_interno=parseada.codigo_interno,
            tipo=parseada.tipo,
            nome=parseada.nome,
            unidade_medida=parseada.unidade_medida,
            preco_padrao=parseada.preco_padrao,
            categoria=parseada.categoria,
            descricao=parseada.descricao,
            codigo_fabricante=parseada.codigo_fabricante,
            motivo_rejeicao=parseada.motivo_rejeicao,
        )
        for parseada in inp.linhas_parseadas
    )
    repo.salvar_importacao(importacao, list(linhas))
    validadas = sum(1 for li in linhas if li.status == StatusLinhaImportacao.VALIDADA)
    return RegistrarImportacaoOutput(
        importacao=importacao,
        linhas=linhas,
        total_validadas=validadas,
        total_rejeitadas=len(linhas) - validadas,
    )


# === aceitar_linha (one-shot; reusa o caminho canônico) ===


@dataclass(frozen=True, slots=True)
class AceitarLinhaInput:
    tenant_id: UUID
    linha_id: UUID
    criado_por: UUID  # quem CONFERIU e aceitou (não quem subiu o arquivo)
    agora: datetime


@dataclass(frozen=True, slots=True)
class AceitarLinhaOutput:
    linha_id: UUID
    item: CadastrarItemOutput


def aceitar_linha(
    inp: AceitarLinhaInput,
    *,
    importacao_repo: ImportacaoCatalogoRepository,
    item_repo: ItemCatalogoRepository,
) -> AceitarLinhaOutput:
    """VALIDADA→ACEITA + `cadastrar_item` na MESMA transação do caller.

    Código que passou a existir entre o upload e o aceite →
    `CodigoDuplicadoError` (409) propaga e a linha PERMANECE validada (o
    operador decide rejeitar). Já aceita/rejeitada → RuntimeError (409).
    """
    linha = importacao_repo.obter_linha(tenant_id=inp.tenant_id, linha_id=inp.linha_id)
    if linha is None:
        raise LinhaImportacaoAusenteError(f"linha {inp.linha_id} inexistente no tenant.")
    if linha.status != StatusLinhaImportacao.VALIDADA:
        raise RuntimeError(
            f"linha {inp.linha_id} está '{linha.status.value}' — aceite é one-shot "
            "sobre linha validada."
        )
    if linha.preco_padrao is None:  # defesa: linha validada sempre tem preço
        raise RuntimeError(f"linha {inp.linha_id} validada sem preço — staging corrompido.")
    out = cadastrar_item(
        CadastrarItemInput(
            tenant_id=inp.tenant_id,
            codigo_interno=linha.codigo_interno,
            tipo=TipoItem(linha.tipo),
            nome=linha.nome,
            unidade_medida=linha.unidade_medida,
            preco_padrao=linha.preco_padrao,
            criado_por=inp.criado_por,
            agora=inp.agora,
            codigo_fabricante=linha.codigo_fabricante,
            descricao=linha.descricao,
            categoria=linha.categoria,
            motivo=f"importacao CSV lote {linha.importacao_id} linha {linha.linha_numero}",
            importacao=True,
        ),
        repo=item_repo,
    )
    importacao_repo.marcar_linha_aceita(
        tenant_id=inp.tenant_id, linha_id=inp.linha_id, item_criado_id=out.item.id
    )
    return AceitarLinhaOutput(linha_id=inp.linha_id, item=out)


# === rejeitar_linha (one-shot) ===


@dataclass(frozen=True, slots=True)
class RejeitarLinhaInput:
    tenant_id: UUID
    linha_id: UUID
    motivo: str

    def __post_init__(self) -> None:
        if not self.motivo.strip():
            raise ValueError("rejeitar_linha: motivo obrigatório.")


def rejeitar_linha(
    inp: RejeitarLinhaInput, *, importacao_repo: ImportacaoCatalogoRepository
) -> None:
    """VALIDADA→REJEITADA (conferência humana descartou a linha)."""
    linha = importacao_repo.obter_linha(tenant_id=inp.tenant_id, linha_id=inp.linha_id)
    if linha is None:
        raise LinhaImportacaoAusenteError(f"linha {inp.linha_id} inexistente no tenant.")
    importacao_repo.marcar_linha_rejeitada(
        tenant_id=inp.tenant_id, linha_id=inp.linha_id, motivo=inp.motivo
    )
