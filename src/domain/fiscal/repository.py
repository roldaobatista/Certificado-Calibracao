"""Protocols dos repositórios do domínio fiscal (Fatia 1a — T-FIS-015).

Use cases (Fatia 2) consomem estes Protocols; adapters Django concretos vivem em
`infrastructure/fiscal/repositories.py` (Fatia 1b). Convenção M4/M6/M8: `obter_*`
retorna entidade ou `None`; idempotência de NEGÓCIO via `existe_chave`
(`(tenant, origem_id, versao)` — D-FIS-2/INV-FIS-005).
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable
from uuid import UUID

from .entities import NotaFiscalServico


@runtime_checkable
class NotaFiscalServicoRepository(Protocol):
    """Raiz do agregado NotaFiscalServico (WORM Padrão B)."""

    def obter_por_id(
        self, *, tenant_id: UUID, nfse_id: UUID
    ) -> NotaFiscalServico | None: ...

    def existe_chave(
        self, *, tenant_id: UUID, origem_id: UUID, versao: int
    ) -> bool:
        """Idempotência de negócio: já existe nota para (tenant, origem, versao)?
        Evita 2 emissões da mesma origem mesmo com Idempotency-Key diferente."""
        ...

    def obter_por_origem(
        self, *, tenant_id: UUID, origem_id: UUID, versao: int
    ) -> NotaFiscalServico | None:
        """Nota existente da origem (para 409 retornando a nota em PENDING —
        D-FIS-3, sem 2ª chamada ao provider)."""
        ...

    def salvar_nova(self, nota: NotaFiscalServico) -> None:
        """INSERT da nota emitida (status PENDING/AUTHORIZED/REJECTED)."""
        ...

    def atualizar_status(
        self, *, tenant_id: UUID, nfse_id: UUID, nota: NotaFiscalServico
    ) -> None:
        """Aplica transição de estado válida (PENDING→terminal; AUTHORIZED→CANCELED
        — D-FIS-4). Concorrência protegida pelo advisory lock da view + triggers
        one-shot do banco (`cancelado_em`/`emitido_em`), não por CAS na entidade. A
        imutabilidade probatória vive no evento append-only, não no UPDATE de
        `status`."""
        ...
