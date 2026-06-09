"""Adapter Django do Protocol `NotaFiscalServicoRepository` (Fatia 1b, T-FIS-022).

Implementa o repository do domínio sobre o ORM. Mutação de status via CAS
(`atualizar_status` com WHERE revision) — o trigger WORM permite só transição de
`status`/timestamps; campos probatórios são imutáveis. Consumido pelos use cases
(Fatia 2). NÃO é singleton.
"""

from __future__ import annotations

from uuid import UUID

from src.domain.fiscal.entities import NotaFiscalServico
from src.infrastructure.fiscal import mappers
from src.infrastructure.fiscal.models import NotaFiscalServico as NotaFiscalServicoModel


class DjangoNotaFiscalServicoRepository:
    """Adapter ORM da raiz NotaFiscalServico (implementa o Protocol do domínio)."""

    def obter_por_id(
        self, *, tenant_id: UUID, nfse_id: UUID
    ) -> NotaFiscalServico | None:
        m = NotaFiscalServicoModel.objects.filter(
            tenant_id=tenant_id, id=nfse_id
        ).first()
        return mappers.model_para_entidade(m) if m is not None else None

    def existe_chave(self, *, tenant_id: UUID, origem_id: UUID, versao: int) -> bool:
        return NotaFiscalServicoModel.objects.filter(
            tenant_id=tenant_id, origem_id=origem_id, versao=versao
        ).exists()

    def obter_por_origem(
        self, *, tenant_id: UUID, origem_id: UUID, versao: int
    ) -> NotaFiscalServico | None:
        m = NotaFiscalServicoModel.objects.filter(
            tenant_id=tenant_id, origem_id=origem_id, versao=versao
        ).first()
        return mappers.model_para_entidade(m) if m is not None else None

    def salvar_nova(self, nota: NotaFiscalServico) -> None:
        campos = mappers.entidade_para_campos(nota)
        NotaFiscalServicoModel.objects.create(
            id=nota.nfse_id,
            tenant_id=nota.tenant_id,
            correlation_id=nota.nfse_id,
            **campos,
        )

    def atualizar_status(
        self,
        *,
        tenant_id: UUID,
        nfse_id: UUID,
        nota: NotaFiscalServico,
        revision_atual: int,
    ) -> None:
        """Transição de estado via CAS (WHERE revision). Só campos mutáveis
        (status/timestamps/motivo) — trigger WORM bloqueia o resto. `revision_atual`
        é detalhe de infra (optimistic lock), não vive na entidade (molde M8)."""
        atualizadas = NotaFiscalServicoModel.objects.filter(
            tenant_id=tenant_id, id=nfse_id, revision=revision_atual
        ).update(
            status=nota.status.value,
            emitido_em=nota.emitido_em,
            cancelado_em=nota.cancelado_em,
            motivo_cancelamento=nota.motivo_cancelamento or "",
            revision=revision_atual + 1,
        )
        if atualizadas != 1:
            raise RuntimeError(
                "CAS falhou em NotaFiscalServico (revision divergente ou corrida)."
            )
