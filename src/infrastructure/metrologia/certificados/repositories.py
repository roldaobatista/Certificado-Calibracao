"""Adapters Django dos Protocols de domínio certificados (M8 Fatia 1b, T-CER-027b).

Implementam `CertificadoRepository` + `AnaliseReconciliacaoRepository`
(ADR-0007/0078). Usam `all_objects` (o default `objects` filtra só emitido-vigente —
precisamos ver substituida/revogado) + filtro `tenant_id` EXPLÍCITO além da RLS
(defesa em profundidade — molde M5/M6/M7). `salvar_novo` é atômico (cert + N pontos).
"""

from __future__ import annotations

from collections.abc import Sequence
from decimal import Decimal
from uuid import UUID

from django.db import connection, transaction

from src.domain.metrologia.certificados.entities import (
    AnaliseReconciliacaoCertificado,
    CertificadoSnapshot,
    PontoReconciliadoSnapshot,
)
from src.infrastructure.certificados.models import (
    AnaliseReconciliacaoCert,
    Certificado,
    PontoReconciliado,
    StatusCertificado,
)

from . import mappers


class DjangoCertificadoRepository:
    """Raiz do agregado Certificado (WORM). CAS via `revision`."""

    def obter_por_id(self, certificado_id: UUID) -> CertificadoSnapshot | None:
        m = Certificado.all_objects.filter(id=certificado_id).first()
        return mappers.certificado_model_para_snapshot(m) if m else None

    def existe_chave(self, *, tenant_id: UUID, calibracao_id: UUID, versao: int) -> bool:
        return Certificado.all_objects.filter(
            tenant_id=tenant_id, calibracao_id=calibracao_id, versao=versao
        ).exists()

    def proximo_numero_interno(self, *, tenant_id: UUID) -> int:
        """Sequence PG GLOBAL `certificado_numero_seq` (buracos OK — INV-CER-NUM-002).
        `tenant_id` ignorado (sequence é global; isolamento é da numeração visível)."""
        with connection.cursor() as cur:
            cur.execute("SELECT nextval('certificado_numero_seq')")
            return int(cur.fetchone()[0])

    def salvar_novo(
        self,
        certificado: CertificadoSnapshot,
        pontos: Sequence[PontoReconciliadoSnapshot],
    ) -> None:
        """INSERT atômico do cert + N pontos (WORM; `status='emitido'`)."""
        with transaction.atomic():
            Certificado.all_objects.create(
                id=certificado.id,
                tenant_id=certificado.tenant_id,
                equipamento_id=certificado.equipamento_id,
                **mappers.certificado_snapshot_para_campos(certificado),
            )
            PontoReconciliado.objects.bulk_create(
                [
                    PontoReconciliado(
                        id=p.id,
                        tenant_id=p.tenant_id,
                        certificado_id=p.certificado_id,
                        **mappers.ponto_snapshot_para_campos(p),
                    )
                    for p in pontos
                ]
            )

    def marcar_substituida(self, *, certificado_id: UUID, revision_anterior: int) -> bool:
        """Transição one-shot `EMITIDO → SUBSTITUIDA` (reemissão T-CER-043). CAS via
        `revision`; rowcount=0 → corrida/já substituída (caller 409). O trigger WORM
        (0004) permite emitido→substituida + bump revision."""
        n = Certificado.all_objects.filter(
            id=certificado_id,
            revision=revision_anterior,
            status=StatusCertificado.EMITIDO,
        ).update(status=StatusCertificado.SUBSTITUIDA, revision=revision_anterior + 1)
        return n == 1


class DjangoAnaliseReconciliacaoRepository:
    """Decisões WORM do RT por ponto, ligadas a `calibracao_id`."""

    def salvar_decisao(self, decisao: AnaliseReconciliacaoCertificado) -> None:
        AnaliseReconciliacaoCert.objects.create(
            id=decisao.id,
            tenant_id=decisao.tenant_id,
            **mappers.analise_snapshot_para_campos(decisao),
        )

    def listar_por_calibracao(
        self, *, tenant_id: UUID, calibracao_id: UUID
    ) -> list[AnaliseReconciliacaoCertificado]:
        qs = AnaliseReconciliacaoCert.objects.filter(
            tenant_id=tenant_id, calibracao_id=calibracao_id
        ).order_by("criado_em")
        return [mappers.analise_model_para_snapshot(m) for m in qs]

    def existe_decisao_para_ponto(
        self, *, tenant_id: UUID, calibracao_id: UUID, ponto_calibracao: Decimal
    ) -> bool:
        return AnaliseReconciliacaoCert.objects.filter(
            tenant_id=tenant_id,
            calibracao_id=calibracao_id,
            ponto_calibracao=ponto_calibracao,
        ).exists()

    def obter_decisao_por_ponto(
        self, *, tenant_id: UUID, calibracao_id: UUID
    ) -> dict[Decimal, AnaliseReconciliacaoCertificado]:
        """Mapa `ponto_calibracao → decisão` (mais recente por ponto vence)."""
        qs = AnaliseReconciliacaoCert.objects.filter(
            tenant_id=tenant_id, calibracao_id=calibracao_id
        ).order_by("criado_em")
        mapa: dict[Decimal, AnaliseReconciliacaoCertificado] = {}
        for m in qs:
            mapa[m.ponto_calibracao] = mappers.analise_model_para_snapshot(m)
        return mapa
