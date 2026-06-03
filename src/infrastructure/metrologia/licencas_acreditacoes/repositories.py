"""Adapters Django dos Protocols de domínio licencas-acreditacoes (M9, T-LIC-021).

Implementam `DocumentoRegulatorioRepository` + `RevisaoRepository` +
`AlertaRepository` + `BloqueioRepository` (ADR-0007/0072). Defesa em profundidade
(molde M5-M8): TODA query filtra `tenant_id` EXPLÍCITO além da RLS. `salvar_novo` é
atômico (documento raiz + revisão v1). O `status_cache` é derivado por
`calcular_status` na escrita — verdade é `vigencia_fim` vs hoje (recalculado no job).
"""

from __future__ import annotations

from datetime import UTC, date, datetime, time
from uuid import UUID

from django.db import transaction
from django.utils import timezone

from src.domain.metrologia.licencas_acreditacoes.entities import (
    AlertaVencimento,
    BloqueioOperacional,
    DocumentoRegulatorio,
    EventoEmergencial,
    RevisaoDocumento,
)
from src.domain.metrologia.licencas_acreditacoes.enums import StatusAlerta
from src.domain.metrologia.licencas_acreditacoes.transicoes import calcular_status
from src.infrastructure.metrologia.licencas_acreditacoes.models import (
    AlertaVencimento as AlertaVencimentoModel,
)
from src.infrastructure.metrologia.licencas_acreditacoes.models import (
    BloqueioOperacional as BloqueioOperacionalModel,
)
from src.infrastructure.metrologia.licencas_acreditacoes.models import (
    DocumentoRegulatorio as DocumentoRegulatorioModel,
)
from src.infrastructure.metrologia.licencas_acreditacoes.models import (
    EventoEmergencialLicenca as EventoEmergencialModel,
)
from src.infrastructure.metrologia.licencas_acreditacoes.models import (
    RevisaoDocumento as RevisaoDocumentoModel,
)

from . import mappers


class DjangoDocumentoRegulatorioRepository:
    """Raiz do agregado (Padrão B WORM). `status_cache` derivado na escrita."""

    def salvar_novo(
        self, documento: DocumentoRegulatorio, revisao_inicial: RevisaoDocumento
    ) -> None:
        """INSERT atômico do documento + revisão v1 (caller pode envolver em outro
        atomic maior — p.ex. promoção CGCRE D-LIC-4)."""
        status = calcular_status(
            vigencia_fim=documento.vigencia_fim, hoje=timezone.now().date()
        )
        with transaction.atomic():
            DocumentoRegulatorioModel.objects.create(
                status_cache=status.value,
                **mappers.documento_snapshot_para_campos(documento),
            )
            RevisaoDocumentoModel.objects.create(
                **mappers.revisao_snapshot_para_campos(revisao_inicial),
            )

    def obter_por_id(
        self, *, tenant_id: UUID, documento_id: UUID
    ) -> DocumentoRegulatorio | None:
        m = DocumentoRegulatorioModel.objects.filter(
            id=documento_id, tenant_id=tenant_id
        ).first()
        return mappers.documento_model_para_snapshot(m) if m else None

    def existe_chave(
        self, *, tenant_id: UUID, tipo: str, numero: str, orgao_emissor: str
    ) -> bool:
        return DocumentoRegulatorioModel.objects.filter(
            tenant_id=tenant_id, tipo=tipo, numero=numero, orgao_emissor=orgao_emissor
        ).exists()

    def obter_por_chave_natural(
        self, *, tenant_id: UUID, tipo: str, numero: str, orgao_emissor: str
    ) -> DocumentoRegulatorio | None:
        m = DocumentoRegulatorioModel.objects.filter(
            tenant_id=tenant_id, tipo=tipo, numero=numero, orgao_emissor=orgao_emissor
        ).first()
        return mappers.documento_model_para_snapshot(m) if m else None

    def atualizar_vigencia_cache(
        self,
        *,
        tenant_id: UUID,
        documento_id: UUID,
        vigencia_inicio: date,
        vigencia_fim: date,
    ) -> None:
        """Renovação: avança a vigência da raiz (revisão append-only separada) +
        recalcula `status_cache`. Mutável dentro do Padrão B (não é WORM)."""
        status = calcular_status(vigencia_fim=vigencia_fim, hoje=timezone.now().date())
        DocumentoRegulatorioModel.objects.filter(
            id=documento_id, tenant_id=tenant_id
        ).update(
            vigencia_inicio=vigencia_inicio,
            vigencia_fim=vigencia_fim,
            status_cache=status.value,
        )


class DjangoRevisaoRepository:
    """Histórico versionado append-only (INV-LIC-WORM-001) — nunca update/delete."""

    def append(self, revisao: RevisaoDocumento) -> None:
        RevisaoDocumentoModel.objects.create(
            **mappers.revisao_snapshot_para_campos(revisao),
        )

    def listar_por_documento(
        self, *, tenant_id: UUID, documento_id: UUID
    ) -> list[RevisaoDocumento]:
        qs = RevisaoDocumentoModel.objects.filter(
            tenant_id=tenant_id, documento_id=documento_id
        ).order_by("numero_revisao")
        return [mappers.revisao_model_para_snapshot(m) for m in qs]

    def proximo_numero_revisao(self, *, tenant_id: UUID, documento_id: UUID) -> int:
        ultima = (
            RevisaoDocumentoModel.objects.filter(
                tenant_id=tenant_id, documento_id=documento_id
            )
            .order_by("-numero_revisao")
            .values_list("numero_revisao", flat=True)
            .first()
        )
        return (ultima or 0) + 1


class DjangoAlertaRepository:
    """Alertas idempotentes por (tenant, documento, janela_dias) — UNIQUE."""

    def agendar(self, alerta: AlertaVencimento) -> None:
        """Idempotente: a UNIQUE absorve reagendamento duplicado (ON CONFLICT via
        ignore_conflicts — anti-corrida no job diário)."""
        AlertaVencimentoModel.objects.bulk_create(
            [AlertaVencimentoModel(**mappers.alerta_snapshot_para_campos(alerta))],
            ignore_conflicts=True,
        )

    def cancelar_pendentes(self, *, tenant_id: UUID, documento_id: UUID) -> int:
        n = AlertaVencimentoModel.objects.filter(
            tenant_id=tenant_id,
            documento_id=documento_id,
            status=StatusAlerta.PENDENTE.value,
        ).delete()
        return n[0]


class DjangoBloqueioRepository:
    """Bloqueios operacionais (INV-032). `data_fim_bloqueio is NULL` = ativo."""

    def abrir(self, bloqueio: BloqueioOperacional) -> None:
        BloqueioOperacionalModel.objects.create(
            **mappers.bloqueio_snapshot_para_campos(bloqueio),
        )

    def resolver_ativos(
        self, *, tenant_id: UUID, documento_id: UUID, em: date
    ) -> int:
        # `data_fim_bloqueio` é DateTimeField; o Protocol passa `date` (dia da
        # renovação). Combina em meia-noite UTC aware (evita warning naive×aware).
        em_dt = datetime.combine(em, time.min, tzinfo=UTC)
        return BloqueioOperacionalModel.objects.filter(
            tenant_id=tenant_id,
            documento_id=documento_id,
            data_fim_bloqueio__isnull=True,
        ).update(data_fim_bloqueio=em_dt)

    def obter_ativo(
        self, *, tenant_id: UUID, documento_id: UUID
    ) -> BloqueioOperacional | None:
        m = BloqueioOperacionalModel.objects.filter(
            tenant_id=tenant_id,
            documento_id=documento_id,
            data_fim_bloqueio__isnull=True,
        ).first()
        return mappers.bloqueio_model_para_snapshot(m) if m else None


class DjangoEventoEmergencialRepository:
    """Liberação excepcional auditada (INV-033) — append-only WORM (trigger 0003)."""

    def registrar(self, evento: EventoEmergencial) -> None:
        EventoEmergencialModel.objects.create(
            **mappers.evento_emergencial_snapshot_para_campos(evento),
        )
