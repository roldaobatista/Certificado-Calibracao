"""Adapter real de ``ColaboradorCaixaPort`` + ``ColaboradorReferenciadoPort`` (Fatia 3a — T-CT-041).

``e_tecnico``: lê ``ColaboradorPapel`` (módulo ``colaboradores``, papel ``tecnico`` ativo)
  — molde ``ColaboradorAgendaAdapter``; zero extensão de ``colaboradores`` (D-CT-2/12).

``esta_referenciado``: guard de hard-delete (D-CT-12 / INV-CT-REF-001) — resolve
  ``colaborador_id → tecnico_hash`` e delega a
  ``CaixaTecnicoRepository.esta_referenciado_por_hash`` (caixa ativo / despesa pendente
  ou validada / adiantamento solicitado·aprovado·entregue). A assinatura
  ``(colaborador_id, tenant_id)`` casa com a porta COMPARTILHADA
  ``domain/rh_frota_qualidade/colaboradores/portas.py`` — é essa que o ``ColaboradorViewSet``
  consome quando o hard-delete físico existir.

**Débito GATE-CT-COLABORADOR-REFERENCIADO** (molde ``agenda/referenciado.py``): hoje o
fluxo de ``colaboradores`` é desligamento lógico e NÃO consulta nenhum
``ColaboradorReferenciadoPort``. O wiring em ``apps.py:ready()`` deixa o adapter PRONTO;
o consumo end-to-end fica pendente.

Refs: T-CT-041; D-CT-2/12; INV-CT-REF-001; ADR-0066; GATE-CT-COLABORADOR-REFERENCIADO.
"""

from __future__ import annotations

from uuid import UUID

from src.infrastructure.audit.services import hashear_pii_com_salt_tenant
from src.infrastructure.caixa_tecnico.repositories import CaixaTecnicoRepository

_PAPEL_TECNICO = "tecnico"


class ColaboradorCaixaAdapter:
    """Implementação real de ``ColaboradorCaixaPort`` + ``ColaboradorReferenciadoPort``."""

    def __init__(self, caixa_repo: CaixaTecnicoRepository | None = None) -> None:
        self._caixa_repo = caixa_repo if caixa_repo is not None else CaixaTecnicoRepository()

    def e_tecnico(self, tenant_id: UUID, colaborador_id: UUID) -> bool:
        """True se o colaborador tem papel ``TECNICO`` ativo no tenant (D-CT-2)."""
        from src.infrastructure.colaboradores.models import ColaboradorPapel

        return ColaboradorPapel.objects.filter(
            tenant_id=tenant_id,
            colaborador_id=colaborador_id,
            papel=_PAPEL_TECNICO,
            data_fim__isnull=True,
            revogado_em__isnull=True,
        ).exists()

    def esta_referenciado(self, colaborador_id: UUID, tenant_id: UUID) -> bool:
        """True se o colaborador tem vínculo ativo no caixa_tecnico (bloqueia hard-delete).

        Assinatura ``(colaborador_id, tenant_id)`` — porta compartilhada de colaboradores.
        """
        tecnico_hash = hashear_pii_com_salt_tenant(str(colaborador_id), tenant_id).split(":", 1)[1]
        return self._caixa_repo.esta_referenciado_por_hash(tenant_id, tecnico_hash)
