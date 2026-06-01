"""Protocols dos repositórios do domínio certificados (M8 Fatia 1a, T-CER-016).

Use cases consomem estes Protocols; adapters Django concretos vivem em
`infrastructure/metrologia/certificados/repositories.py` (Fatia 1b — ADR-0072).
A tabela física `certificados` é achatada (`infrastructure/certificados/` —
ADR-0078); o adapter faz a ponte. Convenção M4/M6: `obter_*` retorna snapshot ou
None; mutação via CAS (`atualizar_com_lock`); marcação one-shot.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol, runtime_checkable
from uuid import UUID

from .entities import (
    AnaliseReconciliacaoCertificado,
    CertificadoSnapshot,
    PontoReconciliadoSnapshot,
)


@runtime_checkable
class CertificadoRepository(Protocol):
    """Raiz do agregado Certificado (WORM). CAS optimistic via `revision`."""

    def obter_por_id(self, certificado_id: UUID) -> CertificadoSnapshot | None: ...

    def existe_chave(
        self, *, tenant_id: UUID, calibracao_id: UUID, versao: int
    ) -> bool:
        """Idempotência da emissão: já existe certificado para
        (tenant, calibracao, versao)? Evita 2 emissões da mesma calibração."""
        ...

    def proximo_numero_interno(self, *, tenant_id: UUID) -> int:
        """Sequence PG `certificado_numero_seq` (buracos OK — INV-CER-NUM-002)."""
        ...

    def salvar_novo(
        self,
        certificado: CertificadoSnapshot,
        pontos: Sequence[PontoReconciliadoSnapshot],
    ) -> None:
        """INSERT atômico do `CertificadoSnapshot` + N `PontoReconciliadoSnapshot`
        numa única transação (bulk_create dos pontos). `status='emitido'`."""
        ...

    def marcar_substituida(
        self, *, certificado_id: UUID, revision_anterior: int
    ) -> bool:
        """Transição one-shot `EMITIDO → SUBSTITUIDA` na reemissão (CAS via
        `revision`). False se corrida/já substituída (caller 409). O link forward
        é implícito: a nova versão aponta backward via `versao_anterior_id`."""
        ...


@runtime_checkable
class AnaliseReconciliacaoRepository(Protocol):
    """Decisões WORM do RT por ponto, ligadas a `calibracao_id` (existem ANTES
    da emissão — pré-condição). Idempotência própria por ponto+correlation."""

    def salvar_decisao(self, decisao: AnaliseReconciliacaoCertificado) -> None: ...

    def listar_por_calibracao(
        self, *, tenant_id: UUID, calibracao_id: UUID
    ) -> list[AnaliseReconciliacaoCertificado]:
        """Decisões já tomadas para a calibração — alimenta
        `validar_completude_decisoes_rt` (perfil A)."""
        ...

    def existe_decisao_para_ponto(
        self, *, tenant_id: UUID, calibracao_id: UUID, ponto_calibracao: object
    ) -> bool:
        """Idempotência da decisão por ponto."""
        ...

    def obter_decisao_por_ponto(
        self, *, tenant_id: UUID, calibracao_id: UUID
    ) -> dict[object, AnaliseReconciliacaoCertificado]:
        """Mapa `ponto_calibracao → decisão` para aplicar exclusões/ressalvas na
        emissão (mais recente por ponto vence)."""
        ...
