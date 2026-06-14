"""Adapter Django do `OSRepository` (ADR-0007) — T-OS-040.

Implementa o Protocol `src.domain.operacao.os.repository.OSRepository`
sobre Django ORM + raw SQL (sequence global).

Use cases (`src.application.operacao.os.*`) recebem este adapter via DI
e ignoram Django.
"""

from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import UUID

from django.db import connection

if TYPE_CHECKING:
    from django.db.models import Q

from src.domain.operacao.os.entities import (
    AceiteAtividadeSnapshot,
    AtividadeSnapshot,
    ChecklistItemSnapshot,
    ConsentimentoBiometriaTouchSnapshot,
    DispensaAceiteAtividadeSnapshot,
    EventoDeOSSnapshot,
    EvidenciaFotoAtividadeSnapshot,
    ItemComercialOSSnapshot,
    NaoConformidadeAtividadeSnapshot,
    OSSnapshot,
    SLAContratoSnapshot,
    TipoAtividadeConfigSnapshot,
)
from src.domain.operacao.os.value_objects import (
    EstadoAtividade,
    EstadoChecklistItem,
    EstadoOS,
    PrecedenteDispensa,
    PrioridadeSLA,
    TipoAtividade,
    TipoEventoDeOS,
    TipoFotoEvidencia,
    TipoItemComercial,
)
from src.infrastructure.ordens_servico.models import (
    OS,
    AceiteAtividade,
    AtividadeDaOS,
    ChecklistDaAtividade,
    ConsentimentoBiometriaTouch,
    DispensaAceiteAtividade,
    EventoDeOS,
    EvidenciaFotoAtividade,
    ItemComercialOS,
    NaoConformidadeAtividade,
    SLAContrato,
    TipoAtividadeConfig,
)

# =============================================================
# Conversao Model -> Snapshot
# =============================================================


def _os_to_snapshot(o: OS) -> OSSnapshot:
    return OSSnapshot(
        id=o.id,
        tenant_id=o.tenant_id,
        numero_os=o.numero_os,
        cliente_id=o.cliente_id,
        cliente_referencia_hash=o.cliente_referencia_hash,
        cliente_key_id=o.cliente_key_id,
        equipamento_id=o.equipamento_id,
        equipamento_recebimento_id=o.equipamento_recebimento_id,
        orcamento_origem_id=o.orcamento_origem_id,
        os_origem_id=o.os_origem_id,
        sucessao_societaria_id=o.sucessao_societaria_id,
        estado=EstadoOS(o.estado),
        tipo_predominante=o.tipo_predominante,
        nao_conformidade_global=o.nao_conformidade_global,
        valor_total=Decimal(o.valor_total),
        valor_total_atualizado=Decimal(o.valor_total_atualizado),
        analise_critica_id=o.analise_critica_id,
        analise_critica_snapshot_hash=o.analise_critica_snapshot_hash,
        regra_decisao_acordada=o.regra_decisao_acordada,
        criada_em=o.criada_em,
        atualizada_em=o.atualizada_em,
        criada_por_user_id=o.criada_por_user_id,
    )


def _atividade_to_snapshot(a: AtividadeDaOS) -> AtividadeSnapshot:
    return AtividadeSnapshot(
        id=a.id,
        tenant_id=a.tenant_id,
        os_id=a.os_id,
        tipo=TipoAtividade(a.tipo),
        sequencia=a.sequencia,
        estado=EstadoAtividade(a.estado),
        tecnico_executor_id=a.tecnico_executor_id,
        agendada_para=a.agendada_para,
        iniciada_em=a.iniciada_em,
        concluida_em=a.concluida_em,
        valor_unitario_snapshot=Decimal(a.valor_unitario_snapshot),
        link_modulo_tecnico_id=a.link_modulo_tecnico_id,
        geo_lat=a.geo_lat,
        geo_long=a.geo_long,
        geo_municipio_hash=a.geo_municipio_hash,
        equipamento_id=a.equipamento_id,
        tipo_bloqueia_concorrencia=a.tipo_bloqueia_concorrencia,
        # Recebimento por instrumento (cl. 7.4.3 — ADR-0082). NULL até GATE-OSME-RECEBIMENTO-7.5.
        equipamento_recebimento_id=a.equipamento_recebimento_id,
        grandeza=a.grandeza,
    )


def _aceite_to_snapshot(x: AceiteAtividade) -> AceiteAtividadeSnapshot:
    return AceiteAtividadeSnapshot(
        id=x.id,
        tenant_id=x.tenant_id,
        atividade_id=x.atividade_id,
        consentimento_id=x.consentimento_id,
        cliente_referencia_hash=x.cliente_referencia_hash,
        cliente_key_id=x.cliente_key_id,
        texto_canonicalizado=x.texto_canonicalizado,
        texto_hash=x.texto_hash,
        biometria_payload_encrypted=(
            bytes(x.biometria_payload_encrypted)
            if x.biometria_payload_encrypted
            else None
        ),
        biometria_key_id=x.biometria_key_id,
        coletado_em=x.coletado_em,
        geo_lat=x.geo_lat,
        geo_long=x.geo_long,
        geo_municipio_hash=x.geo_municipio_hash,
        criado_em=x.criado_em,
    )


def _consentimento_to_snapshot(
    c: ConsentimentoBiometriaTouch,
) -> ConsentimentoBiometriaTouchSnapshot:
    return ConsentimentoBiometriaTouchSnapshot(
        id=c.id,
        tenant_id=c.tenant_id,
        atividade_id=c.atividade_id,
        cliente_referencia_hash=c.cliente_referencia_hash,
        cliente_key_id=c.cliente_key_id,
        texto_canonico_id=c.texto_canonico_id,
        texto_hash=c.texto_hash,
        versao_politica=c.versao_politica,
        concedido_em=c.concedido_em,
        tela_renderizada_evidencia=(
            bytes(c.tela_renderizada_evidencia)
            if c.tela_renderizada_evidencia
            else None
        ),
        criado_em=c.criado_em,
    )


def _dispensa_to_snapshot(
    d: DispensaAceiteAtividade,
) -> DispensaAceiteAtividadeSnapshot:
    return DispensaAceiteAtividadeSnapshot(
        id=d.id,
        tenant_id=d.tenant_id,
        atividade_id=d.atividade_id,
        motivo_hash=d.motivo_hash,
        autorizado_por_gerente_id=d.autorizado_por_gerente_id,
        a3_assinatura_hash=d.a3_assinatura_hash,
        a3_certificado_emissor_hash=d.a3_certificado_emissor_hash,
        a3_assinada_em=d.a3_assinada_em,
        termo_pdf_b2_uri=d.termo_pdf_b2_uri,
        termo_pdf_sha256=d.termo_pdf_sha256,
        precedente_tipo=PrecedenteDispensa(d.precedente_tipo),
        precedente_evento_id=d.precedente_evento_id,
        criado_em=d.criado_em,
    )


def _evidencia_to_snapshot(
    e: EvidenciaFotoAtividade,
) -> EvidenciaFotoAtividadeSnapshot:
    return EvidenciaFotoAtividadeSnapshot(
        id=e.id,
        tenant_id=e.tenant_id,
        atividade_id=e.atividade_id,
        tipo=TipoFotoEvidencia(e.tipo),
        b2_uri=e.b2_uri,
        foto_sha256=e.foto_sha256,
        client_event_id=e.client_event_id,
        client_event_created_at=e.client_event_created_at,
        enviada_em=e.enviada_em,
        tecnico_executor_id=e.tecnico_executor_id,
        geo_lat=e.geo_lat,
        geo_long=e.geo_long,
        geo_municipio_hash=e.geo_municipio_hash,
        revogado_em=e.revogado_em,
        criado_em=e.criado_em,
    )


def _evento_to_snapshot(ev: EventoDeOS) -> EventoDeOSSnapshot:
    return EventoDeOSSnapshot(
        id=ev.id,
        tenant_id=ev.tenant_id,
        os_id=ev.os_id,
        atividade_id=ev.atividade_id,
        tipo=TipoEventoDeOS(ev.tipo),
        payload_hash=ev.payload_hash,
        payload_data=dict(ev.payload_data or {}),
        correlation_id=ev.correlation_id,
        actor_user_id=ev.actor_user_id,
        occurred_at=ev.occurred_at,
        criado_em=ev.criado_em,
    )


def _checklist_to_snapshot(c: ChecklistDaAtividade) -> ChecklistItemSnapshot:
    return ChecklistItemSnapshot(
        id=c.id,
        tenant_id=c.tenant_id,
        atividade_id=c.atividade_id,
        ordem=c.ordem,
        descricao_hash=c.descricao_hash,
        descricao_publica=c.descricao_publica,
        estado=EstadoChecklistItem(c.estado),
        valor_hash=c.valor_hash,
        valor_publico=c.valor_publico,
        preenchido_por_user_id=c.preenchido_por_user_id,
        preenchido_em=c.preenchido_em,
        evidencia_foto_id=c.evidencia_foto_id,
        criado_em=c.criado_em,
        atualizado_em=c.atualizado_em,
    )


def _nc_to_snapshot(n: NaoConformidadeAtividade) -> NaoConformidadeAtividadeSnapshot:
    return NaoConformidadeAtividadeSnapshot(
        id=n.id,
        tenant_id=n.tenant_id,
        atividade_id=n.atividade_id,
        razao_nao_conformidade_hash=n.razao_nao_conformidade_hash,
        marcada_em=n.marcada_em,
        marcada_por_user_id=n.marcada_por_user_id,
        registro_capa_id=n.registro_capa_id,
        causa_raiz_hash=n.causa_raiz_hash,
        acao_corretiva_descricao_hash=n.acao_corretiva_descricao_hash,
        eficacia_verificada_em=n.eficacia_verificada_em,
        eficacia_verificada_por_user_id=n.eficacia_verificada_por_user_id,
        revogado_em=n.revogado_em,
        criado_em=n.criado_em,
    )


def _sla_to_snapshot(s: SLAContrato) -> SLAContratoSnapshot:
    return SLAContratoSnapshot(
        id=s.id,
        tenant_id=s.tenant_id,
        cliente_id=s.cliente_id,
        prioridade=PrioridadeSLA(s.prioridade),
        prazo_atendimento_horas=s.prazo_atendimento_horas,
        prazo_conclusao_horas=s.prazo_conclusao_horas,
        descricao_publica=s.descricao_publica,
        vigencia_inicio=s.vigencia_inicio,
        vigencia_fim=s.vigencia_fim,
        revogado_em=s.revogado_em,
        motivo_revogacao_hash=s.motivo_revogacao_hash,
        criado_em=s.criado_em,
        atualizado_em=s.atualizado_em,
    )


def _tipo_config_to_snapshot(t: TipoAtividadeConfig) -> TipoAtividadeConfigSnapshot:
    return TipoAtividadeConfigSnapshot(
        id=t.id,
        tenant_id=t.tenant_id,
        tipo=TipoAtividade(t.tipo),
        requer_competencia_rt=t.requer_competencia_rt,
        tipo_bloqueia_concorrencia=t.tipo_bloqueia_concorrencia,
        executa_em_campo=t.executa_em_campo,
        prazo_link_calibracao_alerta_h=t.prazo_link_calibracao_alerta_h,
        prazo_link_calibracao_nc_dias_uteis=t.prazo_link_calibracao_nc_dias_uteis,
        deletado_em=t.deletado_em,
        criado_em=t.criado_em,
        atualizado_em=t.atualizado_em,
    )


def _item_comercial_to_snapshot(i: ItemComercialOS) -> ItemComercialOSSnapshot:
    return ItemComercialOSSnapshot(
        id=i.id,
        tenant_id=i.tenant_id,
        os_id=i.os_id,
        tipo=TipoItemComercial(i.tipo),
        descricao_publica=i.descricao_publica,
        valor=Decimal(i.valor),
        quantidade=i.quantidade,
        origem_item_id=i.origem_item_id,
    )


# =============================================================
# DjangoOSRepository
# =============================================================


class DjangoOSRepository:
    """Implementacao concreta do `OSRepository` Protocol sobre Django ORM.

    UoW = Django `transaction.atomic` chamado pelo use case. Adapter expoe
    operacoes atomicas; o caller compoe a transacao.
    """

    # ---- OS ----

    def get_os_by_id(self, os_id: UUID, /) -> OSSnapshot | None:
        try:
            return _os_to_snapshot(OS.objects.get(id=os_id))
        except OS.DoesNotExist:
            return None

    def listar_os_por_tenant(
        self,
        tenant_id: UUID,
        /,
        *,
        estado: str | None = None,
        cliente_id: UUID | None = None,
        equipamento_id: UUID | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[OSSnapshot]:
        # ADR-0082 / D-OSME-2: OS multi-equipamento tem OS.equipamento_id=NULL.
        # O filtro por equipamento deve usar AtividadeDaOS.equipamento_id (spec §7).
        # Delegamos para listar_os_por_equipamento_atividade quando filtro presente.
        if equipamento_id is not None:
            return self.listar_os_por_equipamento_atividade(
                tenant_id,
                equipamento_id,
                estado=estado,
                limit=limit,
                offset=offset,
            )
        qs = OS.objects.filter(tenant_id=tenant_id)
        if estado is not None:
            qs = qs.filter(estado=estado)
        if cliente_id is not None:
            qs = qs.filter(cliente_id=cliente_id)
        qs = qs.order_by("-criada_em")[offset : offset + limit]
        return [_os_to_snapshot(o) for o in qs]

    def proximo_numero_os(self) -> int:
        """ADR-0056 + INV-OS-NUM-001 — sequence global `os_numero_seq_global`."""
        with connection.cursor() as cur:
            cur.execute("SELECT nextval('os_numero_seq_global')")
            row = cur.fetchone()
        if row is None:
            raise RuntimeError("sequence os_numero_seq_global indisponivel")
        return int(row[0])

    def salvar_os(self, snapshot: OSSnapshot, /) -> OSSnapshot:
        """INSERT/UPDATE da OS. Use case envolve em transaction.atomic."""
        try:
            obj = OS.objects.get(id=snapshot.id)
            # UPDATE — apenas campos mutaveis (estado, valores, tipo_predominante,
            # nao_conformidade_global, sucessao, regra_decisao, equipamento_recebimento).
            obj.estado = snapshot.estado.value
            obj.tipo_predominante = snapshot.tipo_predominante
            obj.nao_conformidade_global = snapshot.nao_conformidade_global
            obj.valor_total = snapshot.valor_total
            obj.valor_total_atualizado = snapshot.valor_total_atualizado
            obj.sucessao_societaria_id = snapshot.sucessao_societaria_id
            obj.regra_decisao_acordada = snapshot.regra_decisao_acordada
            obj.equipamento_recebimento_id = snapshot.equipamento_recebimento_id
            obj.save()
        except OS.DoesNotExist:
            obj = OS.objects.create(
                id=snapshot.id,
                tenant_id=snapshot.tenant_id,
                numero_os=snapshot.numero_os,
                cliente_id=snapshot.cliente_id,
                cliente_referencia_hash=snapshot.cliente_referencia_hash,
                cliente_key_id=snapshot.cliente_key_id,
                equipamento_id=snapshot.equipamento_id,
                equipamento_recebimento_id=snapshot.equipamento_recebimento_id,
                orcamento_origem_id=snapshot.orcamento_origem_id,
                os_origem_id=snapshot.os_origem_id,
                sucessao_societaria_id=snapshot.sucessao_societaria_id,
                estado=snapshot.estado.value,
                tipo_predominante=snapshot.tipo_predominante,
                nao_conformidade_global=snapshot.nao_conformidade_global,
                valor_total=snapshot.valor_total,
                valor_total_atualizado=snapshot.valor_total_atualizado,
                analise_critica_id=snapshot.analise_critica_id,
                analise_critica_snapshot_hash=snapshot.analise_critica_snapshot_hash,
                regra_decisao_acordada=snapshot.regra_decisao_acordada,
                criada_por_user_id=snapshot.criada_por_user_id,
            )
        return _os_to_snapshot(obj)

    # ---- AtividadeDaOS ----

    def get_atividade_by_id(self, atividade_id: UUID, /) -> AtividadeSnapshot | None:
        try:
            return _atividade_to_snapshot(AtividadeDaOS.objects.get(id=atividade_id))
        except AtividadeDaOS.DoesNotExist:
            return None

    def listar_atividades_por_os(self, os_id: UUID, /) -> list[AtividadeSnapshot]:
        return [
            _atividade_to_snapshot(a)
            for a in AtividadeDaOS.objects.filter(os_id=os_id).order_by("sequencia")
        ]

    def listar_atividades_em_execucao_por_equipamento(
        self, tenant_id: UUID, equipamento_id: UUID, /
    ) -> list[AtividadeSnapshot]:
        """INV-OS-CONC-001 (ADR-0041) — leitura sem lock; constraint declarativa
        no DB (`idx_atividade_em_execucao_por_equip`) eh quem garante exclusao."""
        return [
            _atividade_to_snapshot(a)
            for a in AtividadeDaOS.objects.filter(
                tenant_id=tenant_id,
                equipamento_id=equipamento_id,
                estado=EstadoAtividade.EM_EXECUCAO.value,
            )
        ]

    def salvar_atividade(self, snapshot: AtividadeSnapshot, /) -> AtividadeSnapshot:
        try:
            obj = AtividadeDaOS.objects.get(id=snapshot.id)
            obj.estado = snapshot.estado.value
            obj.tecnico_executor_id = snapshot.tecnico_executor_id
            obj.agendada_para = snapshot.agendada_para
            obj.iniciada_em = snapshot.iniciada_em
            obj.concluida_em = snapshot.concluida_em
            obj.valor_unitario_snapshot = snapshot.valor_unitario_snapshot
            obj.link_modulo_tecnico_id = snapshot.link_modulo_tecnico_id
            obj.geo_lat = snapshot.geo_lat
            obj.geo_long = snapshot.geo_long
            obj.geo_municipio_hash = snapshot.geo_municipio_hash
            obj.save()
        except AtividadeDaOS.DoesNotExist:
            # ADR-0082 / INV-OS-ATIV-002 (emenda os-multi-equipamento):
            # equipamento_id e PROPRIO da atividade. O trigger BEFORE INSERT usa
            # COALESCE(NEW.equipamento_id, OS.equipamento_id): se o snapshot traz o
            # equipamento_id, passamos no INSERT para que o trigger preserve o valor.
            # Em OS single-equip legada com snapshot.equipamento_id=None o trigger
            # copia de OS.equipamento_id (compat). Em OS multi-equip com OS.equipamento_id=NULL
            # o trigger devolveria NULL — por isso o snapshot DEVE trazer o valor (AC-OSME-002-2).
            # tipo_bloqueia_concorrencia: sempre omitido no INSERT (trigger preenche via config).
            create_kwargs: dict[str, object] = {
                "id": snapshot.id,
                "tenant_id": snapshot.tenant_id,
                "os_id": snapshot.os_id,
                "tipo": snapshot.tipo.value,
                "sequencia": snapshot.sequencia,
                "estado": snapshot.estado.value,
                "tecnico_executor_id": snapshot.tecnico_executor_id,
                "agendada_para": snapshot.agendada_para,
                "iniciada_em": snapshot.iniciada_em,
                "concluida_em": snapshot.concluida_em,
                "valor_unitario_snapshot": snapshot.valor_unitario_snapshot,
                "link_modulo_tecnico_id": snapshot.link_modulo_tecnico_id,
                "geo_lat": snapshot.geo_lat,
                "geo_long": snapshot.geo_long,
                "geo_municipio_hash": snapshot.geo_municipio_hash,
                # tipo_bloqueia_concorrencia preenchido via trigger BEFORE INSERT
                # (ADR-0082 / INV-OS-CONC-001) — adapter NUNCA passa no INSERT.
            }
            if snapshot.equipamento_id is not None:
                # Passa equipamento_id para que o trigger preserve (nao substitua pelo da OS).
                # Trigger usa IF NEW.equipamento_id IS NULL THEN copia OS, senao preserva.
                create_kwargs["equipamento_id"] = snapshot.equipamento_id
            if snapshot.equipamento_recebimento_id is not None:
                # Recebimento por instrumento (cl. 7.4.3 — ADR-0082). So presente quando o
                # seam GATE-OSME-RECEBIMENTO-7.5 estiver ativo; hoje fica None (degeneracao OS-level).
                create_kwargs["equipamento_recebimento_id"] = snapshot.equipamento_recebimento_id
            obj = AtividadeDaOS.objects.create(**create_kwargs)
        return _atividade_to_snapshot(obj)

    # ---- AceiteAtividade (Padrao B imutavel) ----

    def get_aceite_por_atividade(
        self, atividade_id: UUID, /
    ) -> AceiteAtividadeSnapshot | None:
        try:
            return _aceite_to_snapshot(
                AceiteAtividade.objects.get(atividade_id=atividade_id)
            )
        except AceiteAtividade.DoesNotExist:
            return None

    def salvar_aceite(
        self, snapshot: AceiteAtividadeSnapshot, /
    ) -> AceiteAtividadeSnapshot:
        """Padrao B — adapter so faz INSERT. Trigger PG bloqueia UPDATE/DELETE."""
        obj = AceiteAtividade.objects.create(
            id=snapshot.id,
            tenant_id=snapshot.tenant_id,
            atividade_id=snapshot.atividade_id,
            consentimento_id=snapshot.consentimento_id,
            cliente_referencia_hash=snapshot.cliente_referencia_hash,
            cliente_key_id=snapshot.cliente_key_id,
            texto_canonicalizado=snapshot.texto_canonicalizado,
            texto_hash=snapshot.texto_hash,
            biometria_payload_encrypted=snapshot.biometria_payload_encrypted,
            biometria_key_id=snapshot.biometria_key_id,
            coletado_em=snapshot.coletado_em,
            geo_lat=snapshot.geo_lat,
            geo_long=snapshot.geo_long,
            geo_municipio_hash=snapshot.geo_municipio_hash,
        )
        return _aceite_to_snapshot(obj)

    # ---- ConsentimentoBiometriaTouch ----

    def get_consentimento_por_atividade(
        self, atividade_id: UUID, /
    ) -> ConsentimentoBiometriaTouchSnapshot | None:
        try:
            return _consentimento_to_snapshot(
                ConsentimentoBiometriaTouch.objects.get(atividade_id=atividade_id)
            )
        except ConsentimentoBiometriaTouch.DoesNotExist:
            return None

    def salvar_consentimento(
        self, snapshot: ConsentimentoBiometriaTouchSnapshot, /
    ) -> ConsentimentoBiometriaTouchSnapshot:
        """Padrao B — adapter so faz INSERT."""
        obj = ConsentimentoBiometriaTouch.objects.create(
            id=snapshot.id,
            tenant_id=snapshot.tenant_id,
            atividade_id=snapshot.atividade_id,
            cliente_referencia_hash=snapshot.cliente_referencia_hash,
            cliente_key_id=snapshot.cliente_key_id,
            texto_canonico_id=snapshot.texto_canonico_id,
            texto_hash=snapshot.texto_hash,
            versao_politica=snapshot.versao_politica,
            concedido_em=snapshot.concedido_em,
            tela_renderizada_evidencia=snapshot.tela_renderizada_evidencia,
        )
        return _consentimento_to_snapshot(obj)

    # ---- DispensaAceiteAtividade ----

    def get_dispensa_por_atividade(
        self, atividade_id: UUID, /
    ) -> DispensaAceiteAtividadeSnapshot | None:
        try:
            return _dispensa_to_snapshot(
                DispensaAceiteAtividade.objects.get(atividade_id=atividade_id)
            )
        except DispensaAceiteAtividade.DoesNotExist:
            return None

    def salvar_dispensa(
        self, snapshot: DispensaAceiteAtividadeSnapshot, /
    ) -> DispensaAceiteAtividadeSnapshot:
        obj = DispensaAceiteAtividade.objects.create(
            id=snapshot.id,
            tenant_id=snapshot.tenant_id,
            atividade_id=snapshot.atividade_id,
            motivo_hash=snapshot.motivo_hash,
            autorizado_por_gerente_id=snapshot.autorizado_por_gerente_id,
            a3_assinatura_hash=snapshot.a3_assinatura_hash,
            a3_certificado_emissor_hash=snapshot.a3_certificado_emissor_hash,
            a3_assinada_em=snapshot.a3_assinada_em,
            termo_pdf_b2_uri=snapshot.termo_pdf_b2_uri,
            termo_pdf_sha256=snapshot.termo_pdf_sha256,
            precedente_tipo=snapshot.precedente_tipo.value,
            precedente_evento_id=snapshot.precedente_evento_id,
        )
        return _dispensa_to_snapshot(obj)

    # ---- EvidenciaFotoAtividade ----

    def listar_evidencias_foto_por_atividade(
        self, atividade_id: UUID, /
    ) -> list[EvidenciaFotoAtividadeSnapshot]:
        return [
            _evidencia_to_snapshot(e)
            for e in EvidenciaFotoAtividade.objects.filter(atividade_id=atividade_id)
        ]

    def salvar_evidencia_foto(
        self, snapshot: EvidenciaFotoAtividadeSnapshot, /
    ) -> EvidenciaFotoAtividadeSnapshot:
        """Padrao B append-only — adapter so faz INSERT; trigger PG bloqueia UPDATE."""
        obj = EvidenciaFotoAtividade.objects.create(
            id=snapshot.id,
            tenant_id=snapshot.tenant_id,
            atividade_id=snapshot.atividade_id,
            tipo=snapshot.tipo.value,
            b2_uri=snapshot.b2_uri,
            foto_sha256=snapshot.foto_sha256,
            client_event_id=snapshot.client_event_id,
            client_event_created_at=snapshot.client_event_created_at,
            enviada_em=snapshot.enviada_em,
            tecnico_executor_id=snapshot.tecnico_executor_id,
            geo_lat=snapshot.geo_lat,
            geo_long=snapshot.geo_long,
            geo_municipio_hash=snapshot.geo_municipio_hash,
        )
        return _evidencia_to_snapshot(obj)

    def revogar_evidencia_foto(
        self, foto_id: UUID, /
    ) -> EvidenciaFotoAtividadeSnapshot:
        """LGPD art. 18 — UPDATE apenas `revogado_em`. Trigger PG enforca."""
        from django.utils import timezone

        obj = EvidenciaFotoAtividade.objects.get(id=foto_id)
        obj.revogado_em = timezone.now()
        obj.save(update_fields=["revogado_em"])
        return _evidencia_to_snapshot(obj)

    # ---- EventoDeOS (Padrao B append-only) ----

    def publicar_evento(self, snapshot: EventoDeOSSnapshot, /) -> EventoDeOSSnapshot:
        """INSERT em `evento_de_os` (timeline da OS). Trigger PG enforca append-only.

        INT-01 Onda PRE-A.4 (auditoria 10 lentes pré-Wave A — fecha L7#1):
        eventos mapeados em `MAPA_TIPO_EVENTO_OS_PARA_ACAO_BUS` cruzam pro `bus_outbox`
        na MESMA `transaction.atomic` do caller. Antes M3 OS gravava so timeline
        e Saga 1 (Orçamento→OS→Cert→NF→CR) quebrava no passo 2-3.
        """
        from src.domain.operacao.os.value_objects import (
            MAPA_TIPO_EVENTO_OS_PARA_ACAO_BUS,
        )

        obj = EventoDeOS.objects.create(
            id=snapshot.id,
            tenant_id=snapshot.tenant_id,
            os_id=snapshot.os_id,
            atividade_id=snapshot.atividade_id,
            tipo=snapshot.tipo.value,
            payload_hash=snapshot.payload_hash,
            payload_data=snapshot.payload_data,
            correlation_id=snapshot.correlation_id,
            actor_user_id=snapshot.actor_user_id,
            occurred_at=snapshot.occurred_at,
        )

        # INT-01: se evento eh Integration Event, cruza pro bus_outbox.
        # causation_id reusa o ID do snapshot — idempotente em (causation_id, acao)
        # via ON CONFLICT DO NOTHING no INSERT do outbox.
        acao_bus = MAPA_TIPO_EVENTO_OS_PARA_ACAO_BUS.get(snapshot.tipo)
        if acao_bus is not None:
            # Import diferido pra evitar ciclo modulo (audit -> ordens_servico)
            from src.infrastructure.audit.event_helpers import publicar_evento

            payload_bus = {
                "os_id": str(snapshot.os_id),
                "atividade_id": str(snapshot.atividade_id) if snapshot.atividade_id else None,
                "tipo_evento_os": snapshot.tipo.value,
                **(snapshot.payload_data or {}),
            }
            resource_summary = f"OS#{snapshot.os_id} {snapshot.tipo.value}"
            publicar_evento(
                acao=acao_bus,
                payload=payload_bus,
                causation_id=snapshot.id,
                tenant_id=snapshot.tenant_id,
                usuario_id=snapshot.actor_user_id,
                resource_summary=resource_summary,
                cadeia=False,  # cadeia hash-chain mora em evento_de_os local
                outbox=True,
            )

        return _evento_to_snapshot(obj)

    def listar_eventos_por_os(
        self, os_id: UUID, /, *, limit: int = 100
    ) -> list[EventoDeOSSnapshot]:
        qs = EventoDeOS.objects.filter(os_id=os_id).order_by("-occurred_at")[:limit]
        return [_evento_to_snapshot(e) for e in qs]

    # ---- ChecklistDaAtividade (Padrao A — estado por item) ----

    def listar_checklist_por_atividade(
        self, atividade_id: UUID, /
    ) -> list[ChecklistItemSnapshot]:
        return [
            _checklist_to_snapshot(c)
            for c in ChecklistDaAtividade.objects.filter(
                atividade_id=atividade_id
            ).order_by("ordem")
        ]

    def salvar_checklist_item(
        self, snapshot: ChecklistItemSnapshot, /
    ) -> ChecklistItemSnapshot:
        try:
            obj = ChecklistDaAtividade.objects.get(id=snapshot.id)
            obj.estado = snapshot.estado.value
            obj.valor_hash = snapshot.valor_hash
            obj.valor_publico = snapshot.valor_publico
            obj.preenchido_por_user_id = snapshot.preenchido_por_user_id
            obj.preenchido_em = snapshot.preenchido_em
            obj.evidencia_foto_id = snapshot.evidencia_foto_id
            obj.save()
        except ChecklistDaAtividade.DoesNotExist:
            obj = ChecklistDaAtividade.objects.create(
                id=snapshot.id,
                tenant_id=snapshot.tenant_id,
                atividade_id=snapshot.atividade_id,
                ordem=snapshot.ordem,
                descricao_hash=snapshot.descricao_hash,
                descricao_publica=snapshot.descricao_publica,
                estado=snapshot.estado.value,
                valor_hash=snapshot.valor_hash,
                valor_publico=snapshot.valor_publico,
                preenchido_por_user_id=snapshot.preenchido_por_user_id,
                preenchido_em=snapshot.preenchido_em,
                evidencia_foto_id=snapshot.evidencia_foto_id,
            )
        return _checklist_to_snapshot(obj)

    # ---- NaoConformidadeAtividade ----

    def get_nc_ativa_por_atividade(
        self, atividade_id: UUID, /
    ) -> NaoConformidadeAtividadeSnapshot | None:
        try:
            return _nc_to_snapshot(
                NaoConformidadeAtividade.objects.get(
                    atividade_id=atividade_id, revogado_em__isnull=True
                )
            )
        except NaoConformidadeAtividade.DoesNotExist:
            return None

    # ---- Leituras agregadas por OS (anti-N+1 da visao_360 — ADR-0082 P9) ----
    # Substituem as 4 queries-por-atividade do loop de `visao_360_da_os`: cada
    # mapa abaixo resolve em 1 query (filter por atividade__os_id), tornando a
    # visao 360 O(1) em queries independente do numero de atividades da OS.

    def mapa_aceites_por_os(
        self, os_id: UUID, /
    ) -> dict[UUID, AceiteAtividadeSnapshot]:
        return {
            a.atividade_id: _aceite_to_snapshot(a)
            for a in AceiteAtividade.objects.filter(atividade__os_id=os_id)
        }

    def mapa_dispensas_por_os(
        self, os_id: UUID, /
    ) -> dict[UUID, DispensaAceiteAtividadeSnapshot]:
        return {
            d.atividade_id: _dispensa_to_snapshot(d)
            for d in DispensaAceiteAtividade.objects.filter(atividade__os_id=os_id)
        }

    def mapa_ncs_ativas_por_os(
        self, os_id: UUID, /
    ) -> dict[UUID, NaoConformidadeAtividadeSnapshot]:
        return {
            n.atividade_id: _nc_to_snapshot(n)
            for n in NaoConformidadeAtividade.objects.filter(
                atividade__os_id=os_id, revogado_em__isnull=True
            )
        }

    def mapa_evidencias_foto_por_os(
        self, os_id: UUID, /
    ) -> dict[UUID, list[EvidenciaFotoAtividadeSnapshot]]:
        resultado: dict[UUID, list[EvidenciaFotoAtividadeSnapshot]] = {}
        for e in EvidenciaFotoAtividade.objects.filter(atividade__os_id=os_id):
            resultado.setdefault(e.atividade_id, []).append(
                _evidencia_to_snapshot(e)
            )
        return resultado

    def salvar_nc(
        self, snapshot: NaoConformidadeAtividadeSnapshot, /
    ) -> NaoConformidadeAtividadeSnapshot:
        try:
            obj = NaoConformidadeAtividade.objects.get(id=snapshot.id)
            obj.registro_capa_id = snapshot.registro_capa_id
            obj.causa_raiz_hash = snapshot.causa_raiz_hash
            obj.acao_corretiva_descricao_hash = snapshot.acao_corretiva_descricao_hash
            obj.eficacia_verificada_em = snapshot.eficacia_verificada_em
            obj.eficacia_verificada_por_user_id = snapshot.eficacia_verificada_por_user_id
            obj.revogado_em = snapshot.revogado_em
            obj.save()
        except NaoConformidadeAtividade.DoesNotExist:
            obj = NaoConformidadeAtividade.objects.create(
                id=snapshot.id,
                tenant_id=snapshot.tenant_id,
                atividade_id=snapshot.atividade_id,
                razao_nao_conformidade_hash=snapshot.razao_nao_conformidade_hash,
                marcada_em=snapshot.marcada_em,
                marcada_por_user_id=snapshot.marcada_por_user_id,
                registro_capa_id=snapshot.registro_capa_id,
                causa_raiz_hash=snapshot.causa_raiz_hash,
                acao_corretiva_descricao_hash=snapshot.acao_corretiva_descricao_hash,
                eficacia_verificada_em=snapshot.eficacia_verificada_em,
                eficacia_verificada_por_user_id=snapshot.eficacia_verificada_por_user_id,
                revogado_em=snapshot.revogado_em,
            )
        return _nc_to_snapshot(obj)

    # ---- SLAContrato ----

    def get_sla_vigente(
        self, tenant_id: UUID, cliente_id: UUID, /
    ) -> SLAContratoSnapshot | None:
        """ADR-0030: vigencia = (vigencia_inicio <= now) AND (vigencia_fim IS NULL
        OR vigencia_fim > now) AND revogado_em IS NULL."""
        from django.utils import timezone

        now = timezone.now()
        qs = (
            SLAContrato.objects.filter(
                tenant_id=tenant_id,
                cliente_id=cliente_id,
                vigencia_inicio__lte=now,
                revogado_em__isnull=True,
            )
            .filter(models_Q_vigencia_aberta_ou_futura(now))
            .order_by("-vigencia_inicio")
        )
        obj = qs.first()
        if obj is None:
            return None
        return _sla_to_snapshot(obj)

    # ---- TipoAtividadeConfig ----

    def get_tipo_atividade_config(
        self, tenant_id: UUID, tipo: TipoAtividade, /
    ) -> TipoAtividadeConfigSnapshot | None:
        try:
            return _tipo_config_to_snapshot(
                TipoAtividadeConfig.objects.get(
                    tenant_id=tenant_id, tipo=tipo.value, deletado_em__isnull=True
                )
            )
        except TipoAtividadeConfig.DoesNotExist:
            return None

    def listar_tipos_atividade_config(
        self, tenant_id: UUID, /
    ) -> Iterable[TipoAtividadeConfigSnapshot]:
        return [
            _tipo_config_to_snapshot(t)
            for t in TipoAtividadeConfig.objects.filter(
                tenant_id=tenant_id, deletado_em__isnull=True
            ).order_by("tipo")
        ]

    # ---- ItemComercialOS (D-OSME-3 / INV-OSME-ITEMCOM-001) ----

    def salvar_item_comercial(
        self, snapshot: ItemComercialOSSnapshot, /
    ) -> ItemComercialOSSnapshot:
        """INSERT do ItemComercialOS. Padrao A — deletar via deletado_em (UPDATE direto)."""
        try:
            obj = ItemComercialOS.all_objects.get(id=snapshot.id)
            # UPDATE apenas campos mutaveis (tipo, descricao, valor, quantidade).
            obj.tipo = snapshot.tipo.value
            obj.descricao_publica = snapshot.descricao_publica
            obj.valor = snapshot.valor
            obj.quantidade = snapshot.quantidade
            obj.origem_item_id = snapshot.origem_item_id
            obj.save()
        except ItemComercialOS.DoesNotExist:
            obj = ItemComercialOS.objects.create(
                id=snapshot.id,
                tenant_id=snapshot.tenant_id,
                os_id=snapshot.os_id,
                tipo=snapshot.tipo.value,
                descricao_publica=snapshot.descricao_publica,
                valor=snapshot.valor,
                quantidade=snapshot.quantidade,
                origem_item_id=snapshot.origem_item_id,
            )
        return _item_comercial_to_snapshot(obj)

    def listar_itens_comerciais_por_os(
        self, os_id: UUID, /
    ) -> list[ItemComercialOSSnapshot]:
        """Retorna itens comerciais ativos (nao deletados) da OS, por ordem de criacao."""
        return [
            _item_comercial_to_snapshot(i)
            for i in ItemComercialOS.objects.filter(os_id=os_id).order_by("criado_em")
        ]

    def remover_item_comercial(
        self,
        item_id: UUID,
        /,
        *,
        removido_por_usuario_id: UUID | None,
        motivo: str,
    ) -> ItemComercialOSSnapshot:
        """Soft-delete Padrao A (ADR-0031): seta deletado_em + metadados.

        INV-OSME-ITEMCOM-001: item comercial pode ser removido antes do
        faturamento. Use case valida estado da OS antes de chamar.
        """
        from django.utils import timezone

        obj = ItemComercialOS.all_objects.get(id=item_id)
        obj.deletado_em = timezone.now()
        obj.deletado_por_usuario_id = removido_por_usuario_id
        obj.deletado_motivo = motivo[:200]
        obj.save(update_fields=["deletado_em", "deletado_por_usuario_id", "deletado_motivo"])
        return _item_comercial_to_snapshot(obj)

    def listar_os_por_equipamento_atividade(
        self,
        tenant_id: UUID,
        equipamento_id: UUID,
        /,
        *,
        estado: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[OSSnapshot]:
        """Lista OSs cujas ATIVIDADES contenham o equipamento (ADR-0082 filtro REST).

        Usa AtividadeDaOS.equipamento_id — cobre OS multi-equipamento onde
        OS.equipamento_id pode ser NULL (D-OSME-2). Sem N+1: JOIN via ORM
        com atv_tenant_equip_est_idx (TL-OSME-02; nome real da migration 0018,
        abreviado de `atv_tenant_equip_estado_idx` citado na spec/plan).
        """
        qs = OS.objects.filter(
            tenant_id=tenant_id,
            atividades__tenant_id=tenant_id,
            atividades__equipamento_id=equipamento_id,
        )
        if estado is not None:
            qs = qs.filter(estado=estado)
        qs = qs.distinct().order_by("-criada_em")[offset : offset + limit]
        return [_os_to_snapshot(o) for o in qs]

    def listar_os_por_tecnico_atividade(
        self,
        tenant_id: UUID,
        tecnico_user_id: UUID,
        /,
        *,
        limit: int = 50,
        offset: int = 0,
    ) -> list[OSSnapshot]:
        """Lista OSs cujas ATIVIDADES tenham o tecnico como executor (T-OS-087).

        JOIN via ORM com DISTINCT (1 query) — substitui o loop anterior que fazia
        1 query de atividades POR OS do tenant (ADR-0082 P9 — anti-N+1).
        """
        qs = (
            OS.objects.filter(
                tenant_id=tenant_id,
                atividades__tenant_id=tenant_id,
                atividades__tecnico_executor_id=tecnico_user_id,
            )
            .distinct()
            .order_by("-criada_em")[offset : offset + limit]
        )
        return [_os_to_snapshot(o) for o in qs]


def models_Q_vigencia_aberta_ou_futura(now: datetime) -> Q:
    """Helper local: vigencia_fim IS NULL OR vigencia_fim > now."""
    from django.db.models import Q

    return Q(vigencia_fim__isnull=True) | Q(vigencia_fim__gt=now)
