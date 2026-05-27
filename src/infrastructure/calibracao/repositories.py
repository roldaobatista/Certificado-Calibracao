"""Adapter Django dos repositorios M4 calibracao.

Implementa Protocols em src.domain.metrologia.calibracao.repository sobre
Django ORM + raw SQL (sequence global + advisory lock hash-chain).

Use cases (src/application/metrologia/calibracao/*) recebem estes adapters
via DI e ignoram Django (ADR-0007 spec-as-source).

Conteudo:
- DjangoCalibracaoRepository — raiz agregado (P4 Fase 5 Batch A T-CAL-079).
- DjangoEventoDeCalibracaoRepository — trilha WORM hash-chain (OBS-CAL-01
  conserto P5 2026-05-27 — ADR-0064 HMAC + ADR-0065 advisory lock).
"""

from __future__ import annotations

import hashlib
import hmac as _hmac
from uuid import UUID

from django.db import connection

from src.domain.metrologia.calibracao.entities import (
    CalibracaoSnapshot,
    EventoDeCalibracaoSnapshot,
)
from src.domain.metrologia.calibracao.enums import (
    EstadoCalibracao,
    OrigemRecepcao,
    RegraDecisao,
    TipoAcreditacao,
)
from src.domain.metrologia.calibracao.hash_versionado import (
    VERSAO_HMAC_ATUAL,
    canonicalizar_payload_para_hmac,
    formatar_hash_versionado,
)
from src.domain.metrologia.calibracao.value_objects import ZonaILACG8
from src.infrastructure.calibracao.lgpd import _CHAVE_HMAC_WAVE_A
from src.infrastructure.calibracao.models import Calibracao, EventoDeCalibracao

# Classe de lock por tabela — namespace de 2 args
# (pg_advisory_xact_lock(int4, int4)). Isola hash-chain de calibracao de
# qualquer outro advisory lock (paralelo audit/services.py _ADVISORY_LOCK_*).
_ADVISORY_LOCK_CLASSE_EVENTO_CAL = 0x_CA1_AED  # 'cal aed' — eventos calibracao


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
        """Le snapshot (RLS aplicado + filtro tenant_id EXPLICITO).

        SEG-CAL-02 conserto P5 2026-05-27: defesa em profundidade — alem da
        RLS (politica `calibracao_tenant_isolation_select`), filtramos
        tenant_id no ORM tambem. Se contexto multitenant ausente (sessao
        sem `app.tenant_ids` setado), retorna None em vez de aceitar leitura
        confiando 100% na RLS (paralelo INV-TENANT-001).
        """
        from src.infrastructure.multitenant.context import active_tenant_context

        tenant_id = active_tenant_context.get()
        if tenant_id is None:
            return None
        try:
            obj = Calibracao.objects.get(
                id=calibracao_id, tenant_id=tenant_id
            )
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
                    pra_calculada = %s,
                    subcontratado_id = %s,
                    aceite_subcontratacao_id = %s,
                    certificado_subcontratado_snapshot_json = %s::jsonb,
                    recebedor_user_id = %s,
                    motivo_cancelamento_hash = %s
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
                    snapshot.subcontratado_id,
                    snapshot.aceite_subcontratacao_id,
                    (
                        _json.dumps(snapshot.certificado_subcontratado_snapshot_json)
                        if snapshot.certificado_subcontratado_snapshot_json is not None
                        else None
                    ),
                    snapshot.recebedor_user_id,
                    snapshot.motivo_cancelamento_hash,
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
            subcontratado_id=obj.subcontratado_id,
            aceite_subcontratacao_id=obj.aceite_subcontratacao_id,
            certificado_subcontratado_snapshot_json=obj.certificado_subcontratado_snapshot_json,
            recebedor_user_id=obj.recebedor_user_id,
            correlation_id=obj.correlation_id,
            causation_id=obj.causation_id,
            criada_em=obj.criada_em,
            criada_por_user_id=obj.criada_por_user_id,
            motivo_cancelamento_hash=obj.motivo_cancelamento_hash or "",
        )


class DjangoEventoDeCalibracaoRepository:
    """Implementa EventoDeCalibracaoRepository — trilha WORM hash-chain.

    OBS-CAL-01 conserto P5 2026-05-27. ADR-0064 (HMAC versionado v<NN>$<base64>)
    + ADR-0065 (advisory lock por calibracao). Trigger PG popula sequencia_local
    BEFORE INSERT (migration 0009).

    Concorrencia:
    - `pg_advisory_xact_lock(_ADVISORY_LOCK_CLASSE_EVENTO_CAL, hashtext(...))`
      serializa escritores da MESMA calibracao. Sob `ATOMIC_REQUESTS=True`
      e dentro do atomic do CALLER, o lock vive ate o COMMIT do request.
    - Hash anterior eh lido DENTRO do lock; INSERT acontece DENTRO do lock;
      garante ordem total da cadeia.
    - Caller responsavel por envolver em `transaction.atomic` (rollback
      unificado com use case de negocio que disparou o evento).

    Imutabilidade:
    - Trigger `evento_de_calibracao_append_only_trg` (migration 0009) bloqueia
      UPDATE + DELETE — append-only WORM ate 25a (ISO 17025 cl. 8.4).
    """

    def obter_ultimo_hash(
        self, *, tenant_id: UUID, calibracao_id: UUID
    ) -> str:
        """Hash do ultimo elo da cadeia desta calibracao (vazio se nenhum)."""
        ultimo = (
            EventoDeCalibracao.objects.filter(
                tenant_id=tenant_id, calibracao_id=calibracao_id
            )
            .order_by("-sequencia_local")
            .values_list("evento_hash", flat=True)
            .first()
        )
        return ultimo or ""

    def salvar_em_cadeia(
        self, snapshot: EventoDeCalibracaoSnapshot
    ) -> EventoDeCalibracaoSnapshot:
        """Advisory lock + SELECT MAX hash + INSERT — tudo no atomic do caller.

        Caller passa snapshot com `sequencia_local=None`, `evento_anterior_hash=""`,
        `evento_hash=""`. Retorna snapshot encadeado completo.

        Hash calculado: HMAC-SHA256(
          canonicalize({
            "tenant_id": str,
            "calibracao_id": str,
            "tipo": str,
            "payload_sanitizado": dict,
            "evento_anterior_hash": str,
            "occurred_at": isoformat str,
            "correlation_id": str,
          }),
          chave_v<VERSAO_HMAC_ATUAL>,
        ) formatado v<NN>$<base64> (ADR-0064 + INV-HMAC-002).
        """
        chave_cadeia = f"{snapshot.tenant_id}|{snapshot.calibracao_id}"
        with connection.cursor() as cur:
            cur.execute(
                "SELECT pg_advisory_xact_lock(%s, hashtext(%s));",
                [_ADVISORY_LOCK_CLASSE_EVENTO_CAL, chave_cadeia],
            )

        evento_anterior_hash = self.obter_ultimo_hash(
            tenant_id=snapshot.tenant_id, calibracao_id=snapshot.calibracao_id
        )

        payload_canonico = {
            "tenant_id": str(snapshot.tenant_id),
            "calibracao_id": str(snapshot.calibracao_id),
            "tipo": snapshot.tipo,
            "payload_sanitizado": snapshot.payload_sanitizado,
            "evento_anterior_hash": evento_anterior_hash,
            "occurred_at": snapshot.occurred_at.isoformat(),
            "correlation_id": str(snapshot.correlation_id),
        }
        bytes_canon = canonicalizar_payload_para_hmac(payload_canonico)
        mac = _hmac.new(_CHAVE_HMAC_WAVE_A, bytes_canon, hashlib.sha256)
        evento_hash = formatar_hash_versionado(VERSAO_HMAC_ATUAL, mac.digest())

        # INSERT — trigger PG `evento_de_calibracao_seq_populator` popula
        # sequencia_local BEFORE INSERT (MAX+1 dentro da calibracao).
        obj = EventoDeCalibracao.objects.create(
            id=snapshot.id,
            tenant_id=snapshot.tenant_id,
            calibracao_id=snapshot.calibracao_id,
            tipo=snapshot.tipo,
            payload_sanitizado=snapshot.payload_sanitizado,
            evento_anterior_hash=evento_anterior_hash,
            evento_hash=evento_hash,
            correlation_id=snapshot.correlation_id,
            causation_id=snapshot.causation_id,
            actor_user_id=snapshot.actor_user_id,
            actor_user_id_hash=snapshot.actor_user_id_hash,
            occurred_at=snapshot.occurred_at,
        )

        # Trigger populou sequencia_local; recarrega o campo
        # (Django nao trouxe de volta no create — RETURNING incompleto).
        obj.refresh_from_db(fields=["sequencia_local"])

        # Snapshot atualizado: copia + 3 campos encadeados.
        from dataclasses import replace
        return replace(
            snapshot,
            sequencia_local=obj.sequencia_local,
            evento_anterior_hash=evento_anterior_hash,
            evento_hash=evento_hash,
        )
