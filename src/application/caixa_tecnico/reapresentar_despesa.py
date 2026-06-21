"""Use case: reapresentação de despesa rejeitada (US-CT-007 / Fatia 2).

O técnico reapresenta a despesa com nova foto após rejeição.
A transição ``rejeitada → pendente`` é validada pela máquina de estados.

Não publica eventos — a view faz isso dentro do ``transaction.atomic``.

Refs: D-CT-3; US-CT-007; INV-CT-FOTO-001.
"""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass
from uuid import UUID

from src.domain.caixa_tecnico.entities import Despesa
from src.domain.caixa_tecnico.enums import EstadoDespesa
from src.domain.caixa_tecnico.portas import FotoComprovanteStoragePort
from src.domain.caixa_tecnico.transicoes_despesa import (
    validar_transicao as validar_transicao_despesa,
)
from src.infrastructure.caixa_tecnico.repositories import DespesaRepository


@dataclass
class ReapresentarDespesaInput:
    """Parâmetros de entrada para reapresentação de despesa (US-CT-007).

    ``colaborador_id`` é utilizado para rastreabilidade futura;
    não altera o GPS em Wave A (coordenada permanece None).
    """

    tenant_id: UUID
    despesa_id: UUID
    foto_bytes: bytes
    foto_mime: str
    colaborador_id: UUID


class ReapresentarDespesaUseCase:
    """Reapresenta uma despesa rejeitada com nova foto-comprovante.

    Dependências injetadas via construtor (hexagonal — ADR-0007).
    """

    def __init__(
        self,
        despesa_repo: DespesaRepository,
        foto_storage: FotoComprovanteStoragePort,
    ) -> None:
        self._despesa_repo = despesa_repo
        self._foto_storage = foto_storage

    def executar(self, inp: ReapresentarDespesaInput) -> Despesa:
        """Executa a reapresentação da despesa.

        Fluxo:
        1. Carrega a despesa existente.
        2. Valida transição de estado: deve estar em ``rejeitada``.
        3. Processa nova foto-comprovante.
        4. Salva nova foto e atualiza despesa com estado ``pendente``.

        Returns:
            Despesa atualizada com novo estado ``pendente`` e nova foto.

        Raises:
            ValueError: despesa não encontrada.
            TransicaoInvalida: despesa não está no estado ``rejeitada`` (422).
            FotoComprovanteObrigatoria: nova foto inválida (412).
        """
        # 1. Carrega despesa
        despesa = self._despesa_repo.obter_por_id(inp.tenant_id, inp.despesa_id)
        if despesa is None:
            raise ValueError("despesa não encontrada")

        # 2. Valida transição de estado (rejeitada → pendente)
        validar_transicao_despesa(de=despesa.estado, para=EstadoDespesa.PENDENTE)

        # 3. Processa nova foto
        bytes_limpos, novo_foto_hash = self._foto_storage.validar_e_processar(
            inp.tenant_id, inp.foto_bytes, inp.foto_mime
        )

        # 4. Salva nova foto
        nova_foto_url = self._foto_storage.salvar(inp.tenant_id, novo_foto_hash, bytes_limpos)

        # 5. Constrói nova versão da despesa (frozen → dataclasses.replace)
        despesa_atualizada = dataclasses.replace(
            despesa,
            estado=EstadoDespesa.PENDENTE,
            foto_hash=novo_foto_hash,
            foto_url=nova_foto_url,
            rejeitado_em=None,
            motivo_rejeicao=None,
        )

        # 6. Persiste
        self._despesa_repo.atualizar(inp.tenant_id, despesa_atualizada)

        return despesa_atualizada
