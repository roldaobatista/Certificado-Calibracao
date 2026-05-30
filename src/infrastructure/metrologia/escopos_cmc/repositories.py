"""Adapters Django dos Protocols do domínio escopos-cmc (M6 T-ECMC-016).

Implementam `EscopoRepository`/`EscopoExtraidoRepository` (domínio) sobre o ORM.
Mutação da raiz via CAS (`atualizar_com_lock` — revision); revogação one-shot
(o trigger WORM permite só `revogado_em` NULL→valor em linha CONFIRMADA).
Consumidos pelos use cases (Fatia 2). NÃO são singleton (TL-C-04).
"""

from __future__ import annotations

import datetime as _dt
from uuid import UUID

from src.domain.metrologia.escopos_cmc.entities import (
    EscopoCMCSnapshot,
    EscopoExtraido,
)
from src.domain.metrologia.escopos_cmc.enums import EstadoEscopo
from src.domain.metrologia.value_objects import FaixaMedicao, Grandeza
from src.infrastructure.metrologia.escopos_cmc import mappers
from src.infrastructure.metrologia.escopos_cmc.models import (
    EscopoCMC,
)
from src.infrastructure.metrologia.escopos_cmc.models import (
    EscopoExtraido as EscopoExtraidoModel,
)


class DjangoEscopoRepository:
    """Adapter ORM da raiz EscopoCMC (implementa EscopoRepository)."""

    def obter_por_id(self, escopo_id: UUID) -> EscopoCMCSnapshot | None:
        m = EscopoCMC.objects.filter(id=escopo_id).first()
        return mappers.model_para_snapshot(m) if m is not None else None

    def existe_chave_confirmada(
        self,
        *,
        tenant_id: UUID,
        grandeza: Grandeza,
        faixa: FaixaMedicao,
        procedimento_id: UUID | None,
        versao: int,
    ) -> bool:
        return EscopoCMC.objects.filter(
            tenant_id=tenant_id,
            grandeza=grandeza.value,
            faixa_min=faixa.inferior,
            faixa_max=faixa.superior,
            procedimento_id=procedimento_id,
            versao=versao,
        ).exists()

    def proxima_versao(
        self,
        *,
        tenant_id: UUID,
        grandeza: Grandeza,
        faixa: FaixaMedicao,
        procedimento_id: UUID | None,
    ) -> int:
        ultima = (
            EscopoCMC.objects.filter(
                tenant_id=tenant_id,
                grandeza=grandeza.value,
                faixa_min=faixa.inferior,
                faixa_max=faixa.superior,
                procedimento_id=procedimento_id,
            )
            .order_by("-versao")
            .values_list("versao", flat=True)
            .first()
        )
        return (ultima or 0) + 1

    def salvar_novo(self, snapshot: EscopoCMCSnapshot) -> None:
        EscopoCMC.objects.create(
            id=snapshot.id,
            tenant_id=snapshot.tenant_id,
            **mappers.snapshot_para_campos(snapshot),
        )

    def atualizar_com_lock(
        self, snapshot: EscopoCMCSnapshot, revision_anterior: int
    ) -> bool:
        """UPDATE CAS WHERE revision=esperada; rowcount=0 -> corrida (caller 409).

        NÃO muta campos metrológicos de linha CONFIRMADA (trigger PG bloqueia —
        INV-ECMC-003). Bump de revision aqui.
        """
        campos = mappers.snapshot_para_campos(snapshot)
        campos["revision"] = revision_anterior + 1
        atualizados = EscopoCMC.objects.filter(
            id=snapshot.id, revision=revision_anterior
        ).update(**campos)
        return atualizados == 1

    def revogar(
        self, *, escopo_id: UUID, revogado_em: _dt.datetime, motivo: str
    ) -> bool:
        """Revogação one-shot (ADR-0031): estado REVOGADO + revogado_em + motivo.
        False se não encontrado ou já revogado."""
        atualizados = (
            EscopoCMC.objects.filter(id=escopo_id, revogado_em__isnull=True)
            .update(
                estado=EstadoEscopo.REVOGADO.value,
                revogado_em=revogado_em,
                motivo_revogacao=motivo,
            )
        )
        return atualizados == 1

    def encerrar_vigencia(
        self, *, escopo_id: UUID, vigencia_fim: _dt.datetime, revision_anterior: int
    ) -> bool:
        """Encerra a vigência da versão superada (vigencia_fim NULL→valor, CAS).
        O trigger WORM permite só essa transição one-shot em linha CONFIRMADA."""
        atualizados = EscopoCMC.objects.filter(
            id=escopo_id, revision=revision_anterior, vigencia_fim__isnull=True
        ).update(vigencia_fim=vigencia_fim, revision=revision_anterior + 1)
        return atualizados == 1

    def listar_confirmados_vigentes(
        self, *, tenant_id: UUID, grandeza: Grandeza, em: _dt.datetime
    ) -> list[EscopoCMCSnapshot]:
        from django.db.models import Q

        qs = EscopoCMC.objects.filter(
            tenant_id=tenant_id,
            grandeza=grandeza.value,
            estado=EstadoEscopo.CONFIRMADO.value,
            revogado_em__isnull=True,
            vigencia_inicio__lte=em,
        ).filter(Q(vigencia_fim__isnull=True) | Q(vigencia_fim__gte=em))
        return [mappers.model_para_snapshot(m) for m in qs]


class DjangoEscopoExtraidoRepository:
    """Adapter ORM da staging EscopoExtraido (mutável, NÃO WORM — Fatia 4)."""

    def salvar_novo(self, snapshot: EscopoExtraido) -> None:
        EscopoExtraidoModel.objects.create(
            id=snapshot.id,
            tenant_id=snapshot.tenant_id,
            origem_pdf_storage_key=snapshot.origem_pdf_storage_key,
            numero_escopo_cgcre=snapshot.numero_escopo_cgcre,
            extraido_em=snapshot.extraido_em,
            linhas=[
                {
                    "grandeza_texto": linha.grandeza_texto,
                    "unidade": linha.unidade,
                    "cmc_texto": linha.cmc_texto,
                    "faixa_min": None if linha.faixa_min is None else str(linha.faixa_min),
                    "faixa_max": None if linha.faixa_max is None else str(linha.faixa_max),
                    "metodo_texto": linha.metodo_texto,
                    "confianca": str(linha.confianca),
                }
                for linha in snapshot.linhas
            ],
            confirmado_em=snapshot.confirmado_em,
            confirmado_por_id_hash=snapshot.confirmado_por_id_hash,
        )

    def obter_por_id(self, extraido_id: UUID) -> EscopoExtraido | None:
        m = EscopoExtraidoModel.objects.filter(id=extraido_id).first()
        if m is None:
            return None
        return EscopoExtraido(
            id=m.id,
            tenant_id=m.tenant_id,
            origem_pdf_storage_key=m.origem_pdf_storage_key,
            numero_escopo_cgcre=m.numero_escopo_cgcre,
            extraido_em=m.extraido_em,
            linhas=(),  # linhas cruas ficam no JSONField; Fatia 4 desserializa
            confirmado_em=m.confirmado_em,
            confirmado_por_id_hash=m.confirmado_por_id_hash,
        )

    def marcar_confirmado(
        self, *, extraido_id: UUID, confirmado_em: _dt.datetime, por_id_hash: str
    ) -> bool:
        atualizados = (
            EscopoExtraidoModel.objects.filter(id=extraido_id, confirmado_em__isnull=True)
            .update(confirmado_em=confirmado_em, confirmado_por_id_hash=por_id_hash)
        )
        return atualizados == 1
