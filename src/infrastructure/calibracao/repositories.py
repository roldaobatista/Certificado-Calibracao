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
    ComponenteIncertezaSnapshot,
    EventoDeCalibracaoSnapshot,
    LeituraCorrecaoSnapshot,
    LeituraSnapshot,
    NaoConformidadeSnapshot,
    OrcamentoIncertezaSnapshot,
    OrigemLeitura,
    ReclamacaoCalibracaoSnapshot,
)
from src.domain.metrologia.calibracao.enums import (
    AcaoCorretivaTipo,
    ClienteNotificadoVia,
    DecisaoContinuarOuParar,
    DecisaoReclamacao,
    DistribuicaoIncerteza,
    EstadoCalibracao,
    EstadoNaoConformidade,
    EstadoReclamacao,
    FormulaCalculoComponente,
    OrigemRecepcao,
    RegraDecisao,
    TipoAcreditacao,
    TipoOrigemComponente,
)
from src.domain.metrologia.calibracao.hash_versionado import (
    VERSAO_HMAC_ATUAL,
    canonicalizar_payload_para_hmac,
    formatar_hash_versionado,
)
from src.domain.metrologia.calibracao.value_objects import ZonaILACG8
from src.domain.metrologia.value_objects import FaixaMedicao, Grandeza
from src.infrastructure.calibracao.lgpd import _CHAVE_HMAC_WAVE_A
from src.infrastructure.calibracao.models import (
    Calibracao,
    ComponenteIncerteza,
    EventoDeCalibracao,
    Leitura,
    LeituraCorrecao,
    NaoConformidade,
    OrcamentoIncerteza,
    ReclamacaoCalibracao,
)

# §16.6 — Tipo B com dof=infinito vira sentinela no PG (coluna grau_liberdade
# eh NOT NULL no model). Espelha o tratamento de OrcamentoIncerteza.grau_liberdade_efetivo
# no use case calcular_orcamento_incerteza. Round-trip: None->sentinela na
# escrita; sentinela->None na leitura (preserva semantica "infinito").
_DOF_INFINITO_SENTINELA = "999999.00"

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
            # ADR-0076: vazio em RECEPCIONADA (cravado so na configuracao).
            grandeza_calibrada=(
                snapshot.grandeza_calibrada.value
                if snapshot.grandeza_calibrada
                else ""
            ),
            faixa_calibrada_min=(
                snapshot.faixa_calibrada_declarada.inferior
                if snapshot.faixa_calibrada_declarada
                else None
            ),
            faixa_calibrada_max=(
                snapshot.faixa_calibrada_declarada.superior
                if snapshot.faixa_calibrada_declarada
                else None
            ),
            unidade_calibrada=(
                snapshot.faixa_calibrada_declarada.unidade
                if snapshot.faixa_calibrada_declarada
                else ""
            ),
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
                    motivo_cancelamento_hash = %s,
                    grandeza_calibrada = %s,
                    faixa_calibrada_min = %s,
                    faixa_calibrada_max = %s,
                    unidade_calibrada = %s
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
                    # ADR-0076: faixa calibrada declarada (decompoe VOs).
                    (
                        snapshot.grandeza_calibrada.value
                        if snapshot.grandeza_calibrada
                        else ""
                    ),
                    (
                        snapshot.faixa_calibrada_declarada.inferior
                        if snapshot.faixa_calibrada_declarada
                        else None
                    ),
                    (
                        snapshot.faixa_calibrada_declarada.superior
                        if snapshot.faixa_calibrada_declarada
                        else None
                    ),
                    (
                        snapshot.faixa_calibrada_declarada.unidade
                        if snapshot.faixa_calibrada_declarada
                        else ""
                    ),
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
            # ADR-0076: faixa calibrada declarada (reconstroi VOs do dominio).
            grandeza_calibrada=(
                Grandeza(obj.grandeza_calibrada) if obj.grandeza_calibrada else None
            ),
            faixa_calibrada_declarada=(
                FaixaMedicao(
                    obj.faixa_calibrada_min,
                    obj.faixa_calibrada_max,
                    obj.unidade_calibrada,
                )
                if (
                    obj.faixa_calibrada_min is not None
                    and obj.faixa_calibrada_max is not None
                    and obj.unidade_calibrada
                )
                else None
            ),
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


class DjangoLeituraRepository:
    """Implementa `LeituraRepository` (P4 Fase 8 Wave A — T-CAL-124).

    Append-only WORM (INV-CAL-WORM-001) — trigger PG bloqueia UPDATE/DELETE.
    UNIQUE composto (tenant, calibracao, ponto, repeticao) enforce idempotencia
    forte (ADR-0065). UNIQUE parcial em (tenant, calibracao, client_event_id)
    enforce idempotencia sync mobile (ADR-0027).
    """

    def salvar_nova(self, snapshot: LeituraSnapshot) -> None:
        Leitura.objects.create(
            id=snapshot.id,
            tenant_id=snapshot.tenant_id,
            calibracao_id=snapshot.calibracao_id,
            ponto_calibracao=snapshot.ponto_calibracao,
            numero_repeticao=snapshot.numero_repeticao,
            valor_lido=snapshot.valor_lido,
            unidade=snapshot.unidade,
            origem=snapshot.origem.value,
            timestamp=snapshot.timestamp,
            executor_id_hash=snapshot.executor_id_hash,
            client_event_id=snapshot.client_event_id,
            correlation_id=snapshot.correlation_id,
        )

    def obter_por_id(self, leitura_id: UUID) -> LeituraSnapshot | None:
        from src.infrastructure.multitenant.context import active_tenant_context

        tenant_id = active_tenant_context.get()
        if tenant_id is None:
            return None
        try:
            obj = Leitura.objects.get(id=leitura_id, tenant_id=tenant_id)
        except Leitura.DoesNotExist:
            return None
        return self._to_snapshot(obj)

    def obter_por_client_event(
        self,
        tenant_id: UUID,
        calibracao_id: UUID,
        client_event_id: UUID,
    ) -> LeituraSnapshot | None:
        try:
            obj = Leitura.objects.get(
                tenant_id=tenant_id,
                calibracao_id=calibracao_id,
                client_event_id=client_event_id,
            )
        except Leitura.DoesNotExist:
            return None
        return self._to_snapshot(obj)

    @staticmethod
    def _to_snapshot(obj: Leitura) -> LeituraSnapshot:
        return LeituraSnapshot(
            id=obj.id,
            tenant_id=obj.tenant_id,
            calibracao_id=obj.calibracao_id,
            ponto_calibracao=obj.ponto_calibracao,
            numero_repeticao=obj.numero_repeticao,
            valor_lido=obj.valor_lido,
            unidade=obj.unidade,
            origem=OrigemLeitura(obj.origem),
            timestamp=obj.timestamp,
            executor_id_hash=obj.executor_id_hash,
            client_event_id=obj.client_event_id,
            correlation_id=obj.correlation_id,
        )


class DjangoLeituraCorrecaoRepository:
    """Implementa `LeituraCorrecaoRepository` (rasura digital cl. 7.5 — T-CAL-124)."""

    def salvar_nova(self, snapshot: LeituraCorrecaoSnapshot) -> None:
        # `corrigido_em` no model usa auto_now_add; ignoramos `snapshot.corrigido_em`
        # aqui pra preservar autoridade do clock PG (cl. 7.5 — momento da rasura).
        LeituraCorrecao.objects.create(
            id=snapshot.id,
            tenant_id=snapshot.tenant_id,
            leitura_id=snapshot.leitura_id,
            valor_original=snapshot.valor_original,
            valor_corrigido=snapshot.valor_corrigido,
            razao_correcao_canonicalizada=snapshot.razao_correcao_canonicalizada,
            razao_correcao_hash=snapshot.razao_correcao_hash,
            corretor_id_hash=snapshot.corretor_id_hash,
            correlation_id=snapshot.correlation_id,
        )

    def obter_por_id(
        self, correcao_id: UUID
    ) -> LeituraCorrecaoSnapshot | None:
        from src.infrastructure.multitenant.context import active_tenant_context

        tenant_id = active_tenant_context.get()
        if tenant_id is None:
            return None
        try:
            obj = LeituraCorrecao.objects.get(
                id=correcao_id, tenant_id=tenant_id
            )
        except LeituraCorrecao.DoesNotExist:
            return None
        return self._to_snapshot(obj)

    def listar_por_leitura(
        self, leitura_id: UUID
    ) -> list[LeituraCorrecaoSnapshot]:
        qs = LeituraCorrecao.objects.filter(leitura_id=leitura_id).order_by(
            "corrigido_em"
        )
        return [self._to_snapshot(obj) for obj in qs]

    @staticmethod
    def _to_snapshot(obj: LeituraCorrecao) -> LeituraCorrecaoSnapshot:
        return LeituraCorrecaoSnapshot(
            id=obj.id,
            tenant_id=obj.tenant_id,
            leitura_id=obj.leitura_id,
            valor_original=obj.valor_original,
            valor_corrigido=obj.valor_corrigido,
            razao_correcao_canonicalizada=obj.razao_correcao_canonicalizada,
            razao_correcao_hash=obj.razao_correcao_hash,
            corretor_id_hash=obj.corretor_id_hash,
            corrigido_em=obj.corrigido_em,
            correlation_id=obj.correlation_id,
        )


class DjangoNaoConformidadeRepository:
    """Implementa `NaoConformidadeRepository` (T-CAL-128).

    `transitar_estado` faz UPDATE atomico WHERE estado=esperado —
    rowcount=0 indica corrida (estado mudou concorrente). Cumpre o
    contrato Protocol em src/domain/.../calibracao/repository.py.
    """

    def obter_por_id(
        self, nc_id: UUID
    ) -> NaoConformidadeSnapshot | None:
        from src.infrastructure.multitenant.context import active_tenant_context

        tenant_id = active_tenant_context.get()
        if tenant_id is None:
            return None
        try:
            obj = NaoConformidade.objects.get(id=nc_id, tenant_id=tenant_id)
        except NaoConformidade.DoesNotExist:
            return None
        return self._to_snapshot(obj)

    def salvar_novo(self, snapshot: NaoConformidadeSnapshot) -> None:
        NaoConformidade.objects.create(
            id=snapshot.id,
            tenant_id=snapshot.tenant_id,
            calibracao_id=snapshot.calibracao_id,
            origem_proficiencia_id=snapshot.origem_proficiencia_id,
            descricao_canonicalizada=snapshot.descricao_canonicalizada,
            descricao_hash=snapshot.descricao_hash,
            estado=snapshot.estado.value,
            causa_raiz_canonicalizada=snapshot.causa_raiz_canonicalizada,
            causa_raiz_hash=snapshot.causa_raiz_hash,
            acao_corretiva_descricao_hash=(
                snapshot.acao_corretiva_descricao_hash
            ),
            acao_corretiva_tipo=(
                snapshot.acao_corretiva_tipo.value
                if snapshot.acao_corretiva_tipo is not None
                else ""
            ),
            acao_executada_em=snapshot.acao_executada_em,
            eficacia_verificada_em=snapshot.eficacia_verificada_em,
            eficacia_verificada_por_user_id=(
                snapshot.eficacia_verificada_por_user_id
            ),
            responsavel_acao_user_id=snapshot.responsavel_acao_user_id,
            responsavel_acao_user_id_hash=(
                snapshot.responsavel_acao_user_id_hash
            ),
            decisao_continuar_ou_parar=(
                snapshot.decisao_continuar_ou_parar.value
            ),
            cliente_notificado_em=snapshot.cliente_notificado_em,
            cliente_notificado_via=(
                snapshot.cliente_notificado_via.value
                if snapshot.cliente_notificado_via is not None
                else ""
            ),
            cliente_notificado_documento_id=(
                snapshot.cliente_notificado_documento_id
            ),
            autorizacao_retomada_user_id=(
                snapshot.autorizacao_retomada_user_id
            ),
            autorizacao_retomada_em=snapshot.autorizacao_retomada_em,
            correlation_id=snapshot.correlation_id,
        )

    def transitar_estado(
        self,
        snapshot: NaoConformidadeSnapshot,
        estado_anterior: EstadoNaoConformidade,
    ) -> bool:
        # UPDATE atomico WHERE estado=esperado (CAS sem revision).
        # Tenant filter explicito + RLS (defesa em profundidade).
        from src.infrastructure.multitenant.context import active_tenant_context

        tenant_id = active_tenant_context.get()
        if tenant_id is None:
            return False
        rowcount = NaoConformidade.objects.filter(
            id=snapshot.id,
            tenant_id=tenant_id,
            estado=estado_anterior.value,
        ).update(
            estado=snapshot.estado.value,
            causa_raiz_canonicalizada=snapshot.causa_raiz_canonicalizada,
            causa_raiz_hash=snapshot.causa_raiz_hash,
            acao_corretiva_descricao_hash=(
                snapshot.acao_corretiva_descricao_hash
            ),
            acao_corretiva_tipo=(
                snapshot.acao_corretiva_tipo.value
                if snapshot.acao_corretiva_tipo is not None
                else ""
            ),
            acao_executada_em=snapshot.acao_executada_em,
            eficacia_verificada_em=snapshot.eficacia_verificada_em,
            eficacia_verificada_por_user_id=(
                snapshot.eficacia_verificada_por_user_id
            ),
            decisao_continuar_ou_parar=(
                snapshot.decisao_continuar_ou_parar.value
            ),
            cliente_notificado_em=snapshot.cliente_notificado_em,
            cliente_notificado_via=(
                snapshot.cliente_notificado_via.value
                if snapshot.cliente_notificado_via is not None
                else ""
            ),
            cliente_notificado_documento_id=(
                snapshot.cliente_notificado_documento_id
            ),
            autorizacao_retomada_user_id=(
                snapshot.autorizacao_retomada_user_id
            ),
            autorizacao_retomada_em=snapshot.autorizacao_retomada_em,
        )
        return rowcount == 1

    @staticmethod
    def _to_snapshot(obj: NaoConformidade) -> NaoConformidadeSnapshot:
        return NaoConformidadeSnapshot(
            id=obj.id,
            tenant_id=obj.tenant_id,
            calibracao_id=obj.calibracao_id,
            origem_proficiencia_id=obj.origem_proficiencia_id,
            descricao_canonicalizada=obj.descricao_canonicalizada,
            descricao_hash=obj.descricao_hash,
            estado=EstadoNaoConformidade(obj.estado),
            causa_raiz_canonicalizada=obj.causa_raiz_canonicalizada,
            causa_raiz_hash=obj.causa_raiz_hash,
            acao_corretiva_descricao_hash=obj.acao_corretiva_descricao_hash,
            acao_corretiva_tipo=(
                AcaoCorretivaTipo(obj.acao_corretiva_tipo)
                if obj.acao_corretiva_tipo
                else None
            ),
            acao_executada_em=obj.acao_executada_em,
            eficacia_verificada_em=obj.eficacia_verificada_em,
            eficacia_verificada_por_user_id=(
                obj.eficacia_verificada_por_user_id
            ),
            responsavel_acao_user_id=obj.responsavel_acao_user_id,
            responsavel_acao_user_id_hash=obj.responsavel_acao_user_id_hash,
            decisao_continuar_ou_parar=DecisaoContinuarOuParar(
                obj.decisao_continuar_ou_parar
            ),
            cliente_notificado_em=obj.cliente_notificado_em,
            cliente_notificado_via=(
                ClienteNotificadoVia(obj.cliente_notificado_via)
                if obj.cliente_notificado_via
                else None
            ),
            cliente_notificado_documento_id=(
                obj.cliente_notificado_documento_id
            ),
            autorizacao_retomada_user_id=obj.autorizacao_retomada_user_id,
            autorizacao_retomada_em=obj.autorizacao_retomada_em,
            correlation_id=obj.correlation_id,
        )


class DjangoReclamacaoCalibracaoRepository:
    """Implementa `ReclamacaoCalibracaoRepository` (T-CAL-132).

    Estado-maquina: RECEBIDA -> EM_ANALISE -> RESPONDIDA. CAS sem
    revision; `transitar_estado` faz UPDATE WHERE estado=esperado.
    """

    def obter_por_id(
        self, reclamacao_id: UUID
    ) -> ReclamacaoCalibracaoSnapshot | None:
        from src.infrastructure.multitenant.context import active_tenant_context

        tenant_id = active_tenant_context.get()
        if tenant_id is None:
            return None
        try:
            obj = ReclamacaoCalibracao.objects.get(
                id=reclamacao_id, tenant_id=tenant_id
            )
        except ReclamacaoCalibracao.DoesNotExist:
            return None
        return self._to_snapshot(obj)

    def salvar_nova(self, snapshot: ReclamacaoCalibracaoSnapshot) -> None:
        ReclamacaoCalibracao.objects.create(
            id=snapshot.id,
            tenant_id=snapshot.tenant_id,
            calibracao_id=snapshot.calibracao_id,
            certificado_id=snapshot.certificado_id,
            cliente_referencia_hash=snapshot.cliente_referencia_hash,
            relato_canonicalizado=snapshot.relato_canonicalizado,
            relato_hash=snapshot.relato_hash,
            estado=snapshot.estado.value,
            rt_atribuido_user_id_hash=snapshot.rt_atribuido_user_id_hash,
            resposta_canonicalizada=snapshot.resposta_canonicalizada,
            resposta_hash=snapshot.resposta_hash,
            decisao=snapshot.decisao.value if snapshot.decisao else "",
            aberta_em=snapshot.aberta_em,
            prazo_resposta_dia_util=snapshot.prazo_resposta_dia_util,
            respondida_em=snapshot.respondida_em,
            correlation_id=snapshot.correlation_id,
        )

    def transitar_estado(
        self,
        snapshot: ReclamacaoCalibracaoSnapshot,
        estado_anterior: EstadoReclamacao,
    ) -> bool:
        from src.infrastructure.multitenant.context import active_tenant_context

        tenant_id = active_tenant_context.get()
        if tenant_id is None:
            return False
        rowcount = ReclamacaoCalibracao.objects.filter(
            id=snapshot.id,
            tenant_id=tenant_id,
            estado=estado_anterior.value,
        ).update(
            estado=snapshot.estado.value,
            rt_atribuido_user_id_hash=snapshot.rt_atribuido_user_id_hash,
            resposta_canonicalizada=snapshot.resposta_canonicalizada,
            resposta_hash=snapshot.resposta_hash,
            decisao=snapshot.decisao.value if snapshot.decisao else "",
            respondida_em=snapshot.respondida_em,
        )
        return rowcount == 1

    @staticmethod
    def _to_snapshot(
        obj: ReclamacaoCalibracao,
    ) -> ReclamacaoCalibracaoSnapshot:
        return ReclamacaoCalibracaoSnapshot(
            id=obj.id,
            tenant_id=obj.tenant_id,
            calibracao_id=obj.calibracao_id,
            certificado_id=obj.certificado_id,
            cliente_referencia_hash=obj.cliente_referencia_hash,
            relato_canonicalizado=obj.relato_canonicalizado,
            relato_hash=obj.relato_hash,
            estado=EstadoReclamacao(obj.estado),
            rt_atribuido_user_id_hash=obj.rt_atribuido_user_id_hash,
            resposta_canonicalizada=obj.resposta_canonicalizada,
            resposta_hash=obj.resposta_hash,
            decisao=DecisaoReclamacao(obj.decisao) if obj.decisao else None,
            aberta_em=obj.aberta_em,
            prazo_resposta_dia_util=obj.prazo_resposta_dia_util,
            respondida_em=obj.respondida_em,
            correlation_id=obj.correlation_id,
        )


class DjangoOrcamentoIncertezaRepository:
    """Implementa `OrcamentoIncertezaRepository` (T-CAL-125 — destrava
    GATE-CAL-DOMAIN-MODEL-DRIFT).

    Persiste OrcamentoIncerteza (1) + ComponenteIncerteza[] (1:N) atomicamente.
    Caller (ViewSet/use case) envolve em `transaction.atomic`. Ambas as tabelas
    sao WORM (trigger PG bloqueia UPDATE/DELETE — migration 0006).

    Proveniencia §16.6 (NIT-DICLA-030) viaja nos snapshots de componente:
    tipo_origem_componente/distribuicao/divisor/formula_calculo (NOT NULL) +
    s_x/n_amostras do CHECK Tipo A (ck_componente_tipo_a_n_min). O use case
    `calcular_orcamento_incerteza` ja valida n>=6 + s_x antes de chegar aqui.

    Sentinela dof-infinito: ComponenteIncerteza.grau_liberdade eh NOT NULL no
    model; Tipo B com dof=infinito (snapshot.grau_liberdade=None) grava
    `_DOF_INFINITO_SENTINELA` e relê como None (preserva semantica).
    """

    def salvar_orcamento_com_componentes(
        self,
        orcamento: OrcamentoIncertezaSnapshot,
        componentes: list[ComponenteIncertezaSnapshot],
    ) -> None:
        # `calculado_em` no model usa auto_now_add — preserva autoridade do
        # clock PG (cl. 7.6 — momento do calculo). Ignoramos snapshot.calculado_em.
        OrcamentoIncerteza.objects.create(
            id=orcamento.id,
            tenant_id=orcamento.tenant_id,
            calibracao_id=orcamento.calibracao_id,
            u_combinada=orcamento.u_combinada,
            grau_liberdade_efetivo=orcamento.grau_liberdade_efetivo,
            k=orcamento.k,
            U_expandida=orcamento.U_expandida,
            nivel_confianca=orcamento.nivel_confianca,
            documentacao_agregacao=orcamento.documentacao_agregacao,
            versao_motor_calculo=orcamento.versao_motor_calculo,
            algoritmo_1_resultado=orcamento.algoritmo_1_resultado,
            algoritmo_2_resultado=orcamento.algoritmo_2_resultado,
            divergencia_pct=orcamento.divergencia_pct,
            replay_determinismo_hash=orcamento.replay_determinismo_hash,
            bias_orcado=orcamento.bias_orcado,
            bias_origem=orcamento.bias_origem,
            arredondamento_aplicado_regra=orcamento.arredondamento_aplicado_regra,
            correlation_id=orcamento.correlation_id,
        )
        for comp in componentes:
            ComponenteIncerteza.objects.create(
                id=comp.id,
                tenant_id=comp.tenant_id,
                orcamento_incerteza_id=comp.orcamento_incerteza_id,
                nome_componente=comp.nome_componente,
                tipo_componente=comp.tipo_componente,
                tipo_origem_componente=comp.tipo_origem_componente.value,
                distribuicao=comp.distribuicao.value,
                divisor=comp.divisor,
                formula_calculo=comp.formula_calculo.value,
                valor_estimativa=comp.valor_estimativa,
                contribuicao=comp.contribuicao,
                grau_liberdade=(
                    comp.grau_liberdade
                    if comp.grau_liberdade is not None
                    else _DOF_INFINITO_SENTINELA
                ),
                fonte_default_padrao_id=comp.fonte_default_padrao_id,
                correlacao_com_componente_id_id=comp.correlacao_com_componente_id,
                coeficiente_correlacao=comp.coeficiente_correlacao,
                n_amostras=comp.n_amostras,
                s_x=comp.s_x,
            )

    def obter_por_id(
        self, orcamento_id: UUID
    ) -> OrcamentoIncertezaSnapshot | None:
        from src.infrastructure.multitenant.context import active_tenant_context

        tenant_id = active_tenant_context.get()
        if tenant_id is None:
            return None
        try:
            obj = OrcamentoIncerteza.objects.get(
                id=orcamento_id, tenant_id=tenant_id
            )
        except OrcamentoIncerteza.DoesNotExist:
            return None
        return self._orcamento_to_snapshot(obj)

    def listar_componentes(
        self, orcamento_id: UUID
    ) -> list[ComponenteIncertezaSnapshot]:
        qs = ComponenteIncerteza.objects.filter(
            orcamento_incerteza_id=orcamento_id
        ).order_by("nome_componente")
        return [self._componente_to_snapshot(obj) for obj in qs]

    @staticmethod
    def _orcamento_to_snapshot(
        obj: OrcamentoIncerteza,
    ) -> OrcamentoIncertezaSnapshot:
        return OrcamentoIncertezaSnapshot(
            id=obj.id,
            tenant_id=obj.tenant_id,
            calibracao_id=obj.calibracao_id,
            u_combinada=obj.u_combinada,
            grau_liberdade_efetivo=obj.grau_liberdade_efetivo,
            k=obj.k,
            U_expandida=obj.U_expandida,
            nivel_confianca=obj.nivel_confianca,
            documentacao_agregacao=obj.documentacao_agregacao,
            versao_motor_calculo=obj.versao_motor_calculo,
            algoritmo_1_resultado=obj.algoritmo_1_resultado,
            algoritmo_2_resultado=obj.algoritmo_2_resultado,
            divergencia_pct=obj.divergencia_pct,
            replay_determinismo_hash=obj.replay_determinismo_hash,
            bias_orcado=obj.bias_orcado,
            bias_origem=obj.bias_origem,
            arredondamento_aplicado_regra=obj.arredondamento_aplicado_regra,
            calculado_em=obj.calculado_em,
            correlation_id=obj.correlation_id,
        )

    @staticmethod
    def _componente_to_snapshot(
        obj: ComponenteIncerteza,
    ) -> ComponenteIncertezaSnapshot:
        # Sentinela dof-infinito -> None (round-trip Tipo B).
        grau = obj.grau_liberdade
        grau_liberdade = (
            None if str(grau) == _DOF_INFINITO_SENTINELA else grau
        )
        return ComponenteIncertezaSnapshot(
            id=obj.id,
            tenant_id=obj.tenant_id,
            orcamento_incerteza_id=obj.orcamento_incerteza_id,
            nome_componente=obj.nome_componente,
            tipo_componente=obj.tipo_componente,
            tipo_origem_componente=TipoOrigemComponente(obj.tipo_origem_componente),
            distribuicao=DistribuicaoIncerteza(obj.distribuicao),
            divisor=obj.divisor,
            formula_calculo=FormulaCalculoComponente(obj.formula_calculo),
            valor_estimativa=obj.valor_estimativa,
            contribuicao=obj.contribuicao,
            grau_liberdade=grau_liberdade,
            n_amostras=obj.n_amostras,
            s_x=obj.s_x,
            correlacao_com_componente_id=obj.correlacao_com_componente_id_id,
            coeficiente_correlacao=obj.coeficiente_correlacao,
            fonte_default_padrao_id=obj.fonte_default_padrao_id,
        )
