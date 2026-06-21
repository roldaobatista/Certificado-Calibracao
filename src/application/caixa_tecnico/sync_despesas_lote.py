"""Use case: sincronização offline de despesas em lote (US-CT-010 / Fatia 2).

Processa até 20 despesas enviadas pelo app do técnico em modo offline.
Atomicidade per-item: 1 item com erro não derruba o lote inteiro.
O savepoint por item é responsabilidade da VIEW, não deste use case.

Não publica eventos — a view faz isso dentro do ``transaction.atomic``.

Refs: D-CT-5; US-CT-010; LoteExcedido (413); INV-CT-FOTO-001.
"""

from __future__ import annotations

import base64
from dataclasses import dataclass, field
from datetime import date
from uuid import UUID

from src.domain.caixa_tecnico.enums import CategoriaDespesa, TipoDespesa
from src.domain.caixa_tecnico.erros import (
    CaixaTecnicoDesligado,
    CaixaTecnicoDomainError,
    LoteExcedido,
)
from src.infrastructure.caixa_tecnico.repositories import (
    CaixaTecnicoRepository,
    DespesaRepository,
)

from .lancar_despesa import LancarDespesaInput, LancarDespesaUseCase


@dataclass
class ItemLote:
    """Item individual do lote de sincronização offline (D-CT-5).

    ``foto_base64`` é a foto-comprovante codificada em Base64.
    ``client_offline_id`` é o UUID4 gerado pelo app para idempotência.
    """

    foto_base64: str
    foto_mime: str
    categoria: CategoriaDespesa
    valor_centavos: int
    data: date
    descricao: str | None = None
    km_percorridos: int | None = None
    client_offline_id: str | None = None
    os_id: UUID | None = None


@dataclass
class ResultadoItem:
    """Resultado do processamento de um item do lote.

    ``sucesso=True`` e ``codigo_http=201`` → item processado com êxito.
    ``sucesso=True`` e ``codigo_http=200`` → replay idempotente (dedup).
    ``sucesso=False`` → erro com descrição em ``erro`` e código HTTP correspondente.
    """

    indice: int
    sucesso: bool
    despesa_id: str | None  # None se falhou ou replay
    erro: str | None  # None se OK
    codigo_http: int  # 201 criado, 200 replay, 4xx erro


@dataclass
class SyncLoteInput:
    """Parâmetros de entrada para sincronização de lote (US-CT-010)."""

    tenant_id: UUID
    caixa_id: UUID
    colaborador_id: UUID
    itens: list[ItemLote] = field(default_factory=list)


@dataclass
class SyncLoteOutput:
    """Resultado da sincronização do lote."""

    resultados: list[ResultadoItem] = field(default_factory=list)


class SyncDespesasLoteUseCase:
    """Sincroniza um lote de despesas do app offline do técnico.

    Processa cada item independentemente: um erro em item individual
    não cancela os demais (atomicidade per-item via savepoint na VIEW).

    Dependências injetadas via construtor (hexagonal — ADR-0007).
    """

    LIMITE_LOTE = 20

    def __init__(
        self,
        caixa_repo: CaixaTecnicoRepository,
        despesa_repo: DespesaRepository,
        lancar_despesa_uc: LancarDespesaUseCase,
    ) -> None:
        self._caixa_repo = caixa_repo
        self._despesa_repo = despesa_repo
        self._lancar_despesa_uc = lancar_despesa_uc

    def executar(self, inp: SyncLoteInput) -> SyncLoteOutput:
        """Executa a sincronização do lote de despesas.

        Fluxo:
        1. Verifica limite do lote (≤20 itens).
        2. Valida caixa (ativo, não desligado).
        3. Para cada item, tenta lançar via ``LancarDespesaUseCase``.
           - Dedup por ``client_offline_id`` → sucesso com código 200 (replay).
           - Foto Base64 inválida → erro 400.
           - Erro de domínio (CaixaTecnicoDomainError) → erro com http_status do domínio.
           - ValueError → erro 422.
        4. Retorna lista de resultados por item.

        Returns:
            SyncLoteOutput com resultado individual de cada item.

        Raises:
            LoteExcedido: mais de 20 itens no lote (413).
            ValueError: caixa não encontrado.
            CaixaTecnicoDesligado: caixa desligado (409).
        """
        # 1. Verifica limite do lote
        if len(inp.itens) > self.LIMITE_LOTE:
            raise LoteExcedido(f"lote excede {self.LIMITE_LOTE} itens (recebido: {len(inp.itens)})")

        # 2. Valida caixa — falha rápida antes de processar qualquer item
        caixa = self._caixa_repo.obter_por_id(inp.tenant_id, inp.caixa_id)
        if caixa is None:
            raise ValueError("caixa não encontrado")
        if caixa.esta_desligado:
            raise CaixaTecnicoDesligado(
                f"CaixaTecnico {inp.caixa_id} está desligado — lote bloqueado"
            )

        # 3. Processa cada item independentemente
        resultados: list[ResultadoItem] = []

        for i, item in enumerate(inp.itens):
            # 3a. Dedup por client_offline_id
            if item.client_offline_id is not None:
                if self._despesa_repo.existe_gateway_offline(inp.tenant_id, item.client_offline_id):
                    resultados.append(
                        ResultadoItem(
                            indice=i,
                            sucesso=True,
                            despesa_id=None,
                            erro="replay idempotente",
                            codigo_http=200,
                        )
                    )
                    continue

            # 3b. Decodifica foto Base64
            try:
                foto_bytes = base64.b64decode(item.foto_base64)
            except Exception:
                resultados.append(
                    ResultadoItem(
                        indice=i,
                        sucesso=False,
                        despesa_id=None,
                        erro="foto_base64 inválido",
                        codigo_http=400,
                    )
                )
                continue

            # 3c. Lança despesa via use case
            try:
                lancar_input = LancarDespesaInput(
                    tenant_id=inp.tenant_id,
                    caixa_id=inp.caixa_id,
                    foto_bytes=foto_bytes,
                    foto_mime=item.foto_mime,
                    categoria=item.categoria,
                    valor_centavos=item.valor_centavos,
                    data=item.data,
                    colaborador_id=inp.colaborador_id,
                    descricao=item.descricao,
                    km_percorridos=item.km_percorridos,
                    client_offline_id=item.client_offline_id,
                    os_id=item.os_id,
                    tipo=TipoDespesa.NORMAL,
                )
                output = self._lancar_despesa_uc.executar(lancar_input)
                resultados.append(
                    ResultadoItem(
                        indice=i,
                        sucesso=True,
                        despesa_id=str(output.despesa.despesa_id),
                        erro=None,
                        codigo_http=201,
                    )
                )

            # 3d. Erro de domínio — mapeia http_status do próprio erro
            except CaixaTecnicoDomainError as exc:
                resultados.append(
                    ResultadoItem(
                        indice=i,
                        sucesso=False,
                        despesa_id=None,
                        erro=str(exc),
                        codigo_http=exc.http_status,
                    )
                )

            # 3e. Erro de validação / negócio sem http_status próprio
            except ValueError as exc:
                resultados.append(
                    ResultadoItem(
                        indice=i,
                        sucesso=False,
                        despesa_id=None,
                        erro=str(exc),
                        codigo_http=422,
                    )
                )

        return SyncLoteOutput(resultados=resultados)
