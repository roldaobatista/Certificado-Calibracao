"""Adapter Django do Protocol do domínio procedimentos-calibracao (M7 T-PROC-026).

Implementa `ProcedimentoRepository` (domínio) sobre o ORM. Mutação da raiz via
CAS (`atualizar_com_lock` — revision); revogação one-shot; superseção
(`encerrar_vigencia`) sob advisory lock no use case (Fatia 2). NÃO é singleton
(C-3 / TL-C-04). Filtro `tenant_id` EXPLÍCITO além da RLS (defesa em profundidade).
"""

from __future__ import annotations

import datetime as _dt
from uuid import UUID

from django.db.models import Q

from src.domain.metrologia.procedimentos_calibracao.entities import (
    ProcedimentoSnapshot,
)
from src.domain.metrologia.procedimentos_calibracao.enums import EstadoProcedimento
from src.domain.metrologia.value_objects import FaixaMedicao, Grandeza
from src.infrastructure.metrologia.procedimentos_calibracao import mappers
from src.infrastructure.metrologia.procedimentos_calibracao.models import (
    ProcedimentoCalibracao,
)


class DjangoProcedimentoRepository:
    """Adapter ORM da raiz ProcedimentoCalibracao (implementa ProcedimentoRepository)."""

    def obter_por_id(self, procedimento_id: UUID) -> ProcedimentoSnapshot | None:
        m = ProcedimentoCalibracao.objects.filter(id=procedimento_id).first()
        return mappers.model_para_snapshot(m) if m is not None else None

    def existe_chave(self, *, tenant_id: UUID, codigo: str, versao: int) -> bool:
        return ProcedimentoCalibracao.objects.filter(
            tenant_id=tenant_id, codigo=codigo, versao=versao
        ).exists()

    def proxima_versao(self, *, tenant_id: UUID, codigo: str) -> int:
        ultima = (
            ProcedimentoCalibracao.objects.filter(tenant_id=tenant_id, codigo=codigo)
            .order_by("-versao")
            .values_list("versao", flat=True)
            .first()
        )
        return (ultima or 0) + 1

    def salvar_novo(self, snapshot: ProcedimentoSnapshot) -> None:
        ProcedimentoCalibracao.objects.create(
            id=snapshot.id,
            tenant_id=snapshot.tenant_id,
            **mappers.snapshot_para_campos(snapshot),
        )

    def atualizar_com_lock(
        self, snapshot: ProcedimentoSnapshot, revision_anterior: int
    ) -> bool:
        """UPDATE CAS WHERE revision=esperada; rowcount=0 -> corrida (caller 409).

        Edição de RASCUNHO e transição RASCUNHO->PUBLICADO. NÃO muta campos
        técnicos de linha PUBLICADA (trigger PG bloqueia — INV-PROC-003).
        """
        campos = mappers.snapshot_para_campos(snapshot)
        campos["revision"] = revision_anterior + 1
        atualizados = ProcedimentoCalibracao.objects.filter(
            id=snapshot.id, revision=revision_anterior
        ).update(**campos)
        return atualizados == 1

    def vigente_anterior(
        self,
        *,
        tenant_id: UUID,
        codigo: str,
        grandeza: Grandeza,
        faixa: FaixaMedicao,
    ) -> ProcedimentoSnapshot | None:
        """Versão PUBLICADA vigente (vigencia_fim NULL) da mesma chave natural —
        a ser encerrada na superseção (INV-PROC-008)."""
        m = ProcedimentoCalibracao.objects.filter(
            tenant_id=tenant_id,
            codigo=codigo,
            grandeza=grandeza.value,
            faixa_min=faixa.inferior,
            faixa_max=faixa.superior,
            estado=EstadoProcedimento.PUBLICADO.value,
            vigencia_fim__isnull=True,
            revogado_em__isnull=True,
        ).first()
        return mappers.model_para_snapshot(m) if m is not None else None

    def encerrar_vigencia(
        self, *, procedimento_id: UUID, vigencia_fim: _dt.datetime, revision_anterior: int
    ) -> bool:
        """Encerra a vigência da versão superada (vigencia_fim NULL→valor, CAS).
        O trigger WORM permite só essa transição one-shot em linha PUBLICADA."""
        atualizados = ProcedimentoCalibracao.objects.filter(
            id=procedimento_id, revision=revision_anterior, vigencia_fim__isnull=True
        ).update(vigencia_fim=vigencia_fim, revision=revision_anterior + 1)
        return atualizados == 1

    def revogar(
        self, *, procedimento_id: UUID, revogado_em: _dt.datetime, motivo: str
    ) -> bool:
        """Revogação one-shot (ADR-0031): estado REVOGADO + revogado_em + motivo.
        False se não encontrado ou já revogado."""
        atualizados = ProcedimentoCalibracao.objects.filter(
            id=procedimento_id, revogado_em__isnull=True
        ).update(
            estado=EstadoProcedimento.REVOGADO.value,
            revogado_em=revogado_em,
            motivo_revogacao=motivo,
        )
        return atualizados == 1

    def vigente_em(
        self,
        *,
        tenant_id: UUID,
        grandeza: Grandeza,
        faixa: FaixaMedicao,
        em: _dt.datetime,
    ) -> ProcedimentoSnapshot | None:
        """Procedimento PUBLICADO + vigente em `em` que CONTÉM a faixa para a
        grandeza (contenção total — INV-PROC-001). Fail-closed (None se nenhum)."""
        qs = (
            ProcedimentoCalibracao.objects.filter(
                tenant_id=tenant_id,
                grandeza=grandeza.value,
                estado=EstadoProcedimento.PUBLICADO.value,
                revogado_em__isnull=True,
                vigencia_inicio__lte=em,
            )
            .filter(Q(vigencia_fim__isnull=True) | Q(vigencia_fim__gte=em))
        )
        for m in qs:
            proc_faixa = FaixaMedicao(m.faixa_min, m.faixa_max, m.unidade)
            if faixa.inferior >= proc_faixa.inferior and faixa.superior <= proc_faixa.superior:
                if faixa.unidade == proc_faixa.unidade:
                    return mappers.model_para_snapshot(m)
        return None
