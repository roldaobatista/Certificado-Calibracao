"""Adapter Django do CalibracaoRepository (P4 Fase 5 Batch A — T-CAL-079).

Implementa o Protocol src.domain.metrologia.calibracao.repository.CalibracaoRepository
sobre Django ORM + raw SQL (sequence global).

Use cases (src/application/metrologia/calibracao/*) recebem este adapter
via DI e ignoram Django (ADR-0007 spec-as-source).
"""

from __future__ import annotations

from uuid import UUID

from django.db import connection

from src.domain.metrologia.calibracao.entities import CalibracaoSnapshot
from src.domain.metrologia.calibracao.enums import (
    EstadoCalibracao,
    OrigemRecepcao,
    RegraDecisao,
    TipoAcreditacao,
)
from src.domain.metrologia.calibracao.value_objects import ZonaILACG8
from src.infrastructure.calibracao.models import Calibracao


class DjangoCalibracaoRepository:
    """Implementa CalibracaoRepository com Django ORM + sequence PG."""

    def proximo_numero_interno(self) -> int:
        """nextval('calibracao_numero_seq_global') — ADR-0056 + INV-CAL-NUM-001."""
        with connection.cursor() as cur:
            cur.execute("SELECT nextval('calibracao_numero_seq_global')")
            row = cur.fetchone()
        if row is None:
            raise RuntimeError("sequence calibracao_numero_seq_global indisponivel")
        return int(row[0])

    def obter_por_id(self, calibracao_id: UUID) -> CalibracaoSnapshot | None:
        try:
            obj = Calibracao.objects.get(id=calibracao_id)
        except Calibracao.DoesNotExist:
            return None
        return self._to_snapshot(obj)

    def salvar_nova(self, snapshot: CalibracaoSnapshot) -> None:
        """INSERT explicito. Trigger PG preenche numero_exibido (migration 0003).

        Use case envolve em transaction.atomic externamente. Aqui apenas
        materializa o snapshot em uma linha PG.
        """
        Calibracao.objects.create(
            id=snapshot.id,
            tenant_id=snapshot.tenant_id,
            numero_interno=snapshot.numero_interno,
            # numero_exibido: GENERATED pelo trigger PG; NAO setamos aqui.
            atividade_os_id=snapshot.atividade_os_id,
            instrumento_id=snapshot.instrumento_id,
            snapshot_equipamento_json=snapshot.snapshot_equipamento_json,
            cliente_id=snapshot.cliente_id,
            cliente_referencia_hash=snapshot.cliente_referencia_hash,
            cliente_key_id=snapshot.cliente_key_id,
            tipo_acreditacao=snapshot.tipo_acreditacao.value,
            status=snapshot.status.value,
            revision=snapshot.revision,
            regra_decisao=snapshot.regra_decisao.value,
            regra_decisao_acordada_em=snapshot.regra_decisao_acordada_em,
            regra_decisao_acordada_documento_id=snapshot.regra_decisao_acordada_documento_id,
            versao_motor_calculo=snapshot.versao_motor_calculo,
            procedimento_id=snapshot.procedimento_id,
            procedimento_versao_snapshot=snapshot.procedimento_versao_snapshot,
            escopo_id=snapshot.escopo_id,
            analise_critica_pedido_id=snapshot.analise_critica_pedido_id,
            analise_critica_pedido_inline_hash=snapshot.analise_critica_pedido_inline_hash,
            capacidade_tecnica_confirmada_por_user_id=snapshot.capacidade_tecnica_confirmada_por_user_id,
            correlation_id=snapshot.correlation_id,
            causation_id=snapshot.causation_id,
            criada_por_user_id=snapshot.criada_por_user_id,
            # criada_em: auto_now_add no model — Django seta automatico.
        )

    def atualizar_com_lock(
        self, snapshot: CalibracaoSnapshot, revision_anterior: int
    ) -> bool:
        """UPDATE com CAS optimistic (ADR-0065 — INV-CAL-CONC-003).

        Atualiza APENAS campos mutaveis pos-RECEPCIONADA (status, regra_decisao
        acordada, versao_motor_calculo). Campos forensicos (tenant, numero,
        cliente_hash, criada_em, correlation_id) sao imutaveis — trigger PG
        bloqueia ALTER em status terminal.
        """
        import json as _json

        with connection.cursor() as cur:
            cur.execute(
                """
                UPDATE calibracao
                SET status = %s,
                    revision = revision + 1,
                    regra_decisao = %s,
                    regra_decisao_acordada_em = %s,
                    regra_decisao_acordada_documento_id = %s,
                    versao_motor_calculo = %s,
                    procedimento_id = %s,
                    procedimento_versao_snapshot = %s::jsonb,
                    escopo_id = %s,
                    analise_critica_pedido_id = %s,
                    analise_critica_pedido_inline_hash = %s,
                    capacidade_tecnica_confirmada_por_user_id = %s,
                    executor_id = %s,
                    revisor_id = %s,
                    conferente_id = %s,
                    snapshot_competencia_revisor_json = %s::jsonb,
                    snapshot_competencia_conferente_json = %s::jsonb,
                    excecao_2a_conf_id = %s,
                    zona_ilac_g8 = %s,
                    decisao = %s,
                    pfa_calculada = %s,
                    pra_calculada = %s
                WHERE id = %s
                  AND revision = %s
                """,
                [
                    snapshot.status.value,
                    snapshot.regra_decisao.value,
                    snapshot.regra_decisao_acordada_em,
                    snapshot.regra_decisao_acordada_documento_id,
                    snapshot.versao_motor_calculo,
                    snapshot.procedimento_id,
                    _json.dumps(snapshot.procedimento_versao_snapshot),
                    snapshot.escopo_id,
                    snapshot.analise_critica_pedido_id,
                    snapshot.analise_critica_pedido_inline_hash,
                    snapshot.capacidade_tecnica_confirmada_por_user_id,
                    snapshot.executor_id,
                    snapshot.revisor_id,
                    snapshot.conferente_id,
                    (
                        _json.dumps(snapshot.snapshot_competencia_revisor_json)
                        if snapshot.snapshot_competencia_revisor_json is not None
                        else None
                    ),
                    (
                        _json.dumps(snapshot.snapshot_competencia_conferente_json)
                        if snapshot.snapshot_competencia_conferente_json is not None
                        else None
                    ),
                    snapshot.excecao_2a_conf_id,
                    snapshot.zona_ilac_g8.value,
                    snapshot.decisao,
                    snapshot.pfa_calculada,
                    snapshot.pra_calculada,
                    str(snapshot.id),
                    revision_anterior,
                ],
            )
            return bool(cur.rowcount == 1)

    @staticmethod
    def _to_snapshot(obj: Calibracao) -> CalibracaoSnapshot:
        """Converte Model PG -> Snapshot frozen."""
        return CalibracaoSnapshot(
            id=obj.id,
            tenant_id=obj.tenant_id,
            numero_interno=obj.numero_interno,
            numero_exibido=obj.numero_exibido,
            origem_recepcao=(
                OrigemRecepcao.ATIVIDADE_OS
                if obj.atividade_os_id is not None
                else OrigemRecepcao.AVULSA
            ),
            atividade_os_id=obj.atividade_os_id,
            instrumento_id=obj.instrumento_id,
            snapshot_equipamento_json=obj.snapshot_equipamento_json,
            cliente_id=obj.cliente_id,
            cliente_referencia_hash=obj.cliente_referencia_hash,
            cliente_key_id=obj.cliente_key_id,
            tipo_acreditacao=TipoAcreditacao(obj.tipo_acreditacao),
            status=EstadoCalibracao(obj.status),
            revision=obj.revision,
            regra_decisao=RegraDecisao(obj.regra_decisao),
            regra_decisao_acordada_em=obj.regra_decisao_acordada_em,
            regra_decisao_acordada_documento_id=obj.regra_decisao_acordada_documento_id,
            versao_motor_calculo=obj.versao_motor_calculo or "",
            procedimento_id=obj.procedimento_id,
            procedimento_versao_snapshot=obj.procedimento_versao_snapshot or {},
            escopo_id=obj.escopo_id,
            analise_critica_pedido_id=obj.analise_critica_pedido_id,
            analise_critica_pedido_inline_hash=obj.analise_critica_pedido_inline_hash or "",
            capacidade_tecnica_confirmada_por_user_id=obj.capacidade_tecnica_confirmada_por_user_id,
            executor_id=obj.executor_id,
            revisor_id=obj.revisor_id,
            conferente_id=obj.conferente_id,
            snapshot_competencia_revisor_json=obj.snapshot_competencia_revisor_json,
            snapshot_competencia_conferente_json=obj.snapshot_competencia_conferente_json,
            excecao_2a_conf_id=obj.excecao_2a_conf_id,
            zona_ilac_g8=ZonaILACG8(obj.zona_ilac_g8),
            decisao=obj.decisao or "NA",
            pfa_calculada=obj.pfa_calculada,
            pra_calculada=obj.pra_calculada,
            correlation_id=obj.correlation_id,
            causation_id=obj.causation_id,
            criada_em=obj.criada_em,
            criada_por_user_id=obj.criada_por_user_id,
        )
