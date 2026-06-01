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
from django.utils import timezone

from src.domain.metrologia.certificados.entities import (
    AnaliseReconciliacaoCertificado,
    CertificadoSnapshot,
    PontoReconciliadoSnapshot,
)
from src.domain.metrologia.certificados.numeracao import (
    TIPO_CERTIFICADO,
    TTL_RESERVA,
    ReservaNumero,
    montar_numero_certificado,
    proximo_sequencial,
)
from src.infrastructure.certificados.models import (
    AnaliseReconciliacaoCert,
    Certificado,
    NumeroCertificadoReservado,
    PontoReconciliado,
    StatusCertificado,
)

from . import mappers

# Namespace do advisory lock da numeração (distinto de audit/hash-chain — paralelo
# audit/services.py `_ADVISORY_LOCK_*`). Serializa reservas por (tenant, tipo, ano).
_ADVISORY_LOCK_NUMERACAO_CERT = 880_401


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

    def obter_revision_para_cas(
        self, *, tenant_id: UUID, certificado_id: UUID
    ) -> int | None:
        """Lê o `revision` do cert EMITIDO com `select_for_update` (CAS da reemissão —
        TL-A1). DEVE rodar DENTRO da `transaction.atomic` do caller (advisory lock por
        calibração ANTES, fechando o TOCTOU na origem). `None` se não existe ou não
        está EMITIDO (já substituído/revogado → caller 409)."""
        m = (
            Certificado.all_objects.select_for_update()
            .filter(
                id=certificado_id,
                tenant_id=tenant_id,
                status=StatusCertificado.EMITIDO,
            )
            .first()
        )
        return m.revision if m is not None else None

    def listar_pontos(
        self, *, certificado_id: UUID
    ) -> list[PontoReconciliadoSnapshot]:
        """Read-path dos pontos reconciliados (retrieve T-CER-045). SÓ campos
        persistidos, ordenados por ponto ASC — NUNCA reconsulta `cmc_para`/
        `tenant_perfil_e` (INV-CER-SNAPSHOT-CMC-001). RLS isola o tenant."""
        qs = PontoReconciliado.objects.filter(
            certificado_id=certificado_id
        ).order_by("ponto_calibracao")
        return [mappers.ponto_model_para_snapshot(m) for m in qs]


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


class DjangoNumeracaoCertificadoRepository:
    """Reserva → confirma → libera o número VISÍVEL (T-CER-033 / INV-CER-NUM-001).

    Serializa por (tenant, tipo, ano) com `pg_advisory_xact_lock` transacional; o
    INSERT é validado pelo trigger de consecutividade (0008). `reservar_numero` abre
    a própria transação (lock liberado ao fim → reservas concorrentes serializam);
    `confirmar_numero` roda DENTRO da `transaction.atomic` da emissão.
    """

    def reservar_numero(
        self,
        *,
        tenant_id: UUID,
        tenant_slug: str,
        ano: int,
        correlation_id: UUID,
        tipo: str = TIPO_CERTIFICADO,
    ) -> ReservaNumero:
        with transaction.atomic():
            with connection.cursor() as cur:
                cur.execute(
                    "SELECT pg_advisory_xact_lock(%s, hashtext(%s));",
                    [_ADVISORY_LOCK_NUMERACAO_CERT, f"{tenant_id}:{tipo}:{ano}"],
                )
            agora = timezone.now()
            # Libera expirados ANTES de calcular o próximo (reuso → densidade).
            NumeroCertificadoReservado.objects.filter(
                tenant_id=tenant_id, tipo=tipo, ano=ano,
                confirmado=False, ttl_expira_em__lt=agora,
            ).delete()
            em_uso = list(
                NumeroCertificadoReservado.objects.filter(
                    tenant_id=tenant_id, tipo=tipo, ano=ano
                ).values_list("sequencial", flat=True)
            )
            seq = proximo_sequencial(em_uso)
            numero = montar_numero_certificado(
                tenant_slug=tenant_slug, ano=ano, sequencial=seq
            )
            ttl = agora + TTL_RESERVA
            m = NumeroCertificadoReservado.objects.create(
                tenant_id=tenant_id, tipo=tipo, ano=ano, sequencial=seq,
                ttl_expira_em=ttl, confirmado=False, correlation_id=correlation_id,
            )
            return ReservaNumero(
                id=m.id,
                tenant_id=tenant_id,
                tipo=tipo,
                ano=ano,
                sequencial=seq,
                numero_certificado=numero.value,
                reservado_em=m.reservado_em,
                ttl_expira_em=ttl,
                confirmado=False,
                correlation_id=correlation_id,
            )

    def confirmar_numero(self, *, reserva_id: UUID, tenant_id: UUID) -> bool:
        """One-shot: só confirma reserva viva e não-confirmada (caller re-reserva
        se False). O caller envolve na `transaction.atomic` da emissão."""
        agora = timezone.now()
        n = NumeroCertificadoReservado.objects.filter(
            id=reserva_id, tenant_id=tenant_id, confirmado=False,
            ttl_expira_em__gte=agora,
        ).update(confirmado=True)
        return n == 1

    def liberar_expirados(
        self, *, tenant_id: UUID, ano: int, tipo: str = TIPO_CERTIFICADO
    ) -> int:
        agora = timezone.now()
        total, _ = NumeroCertificadoReservado.objects.filter(
            tenant_id=tenant_id, tipo=tipo, ano=ano,
            confirmado=False, ttl_expira_em__lt=agora,
        ).delete()
        return total
