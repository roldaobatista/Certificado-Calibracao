"""Adapter Django do Protocol ``EventoAgendaRepository`` (Fatia 1b, T-AGE-021 — ADR-0007).

Implementa o repositório do domínio sobre o ORM. Concorrência de overlap garantida
pelo EXCLUDE GIST do banco (migration 0003) — sem advisory lock (PLAN-AGE-06).
Tabelas WORM (EventoAuditoriaAgenda / RegistroNoShow / RegimeJornadaColaborador)
protegidas por trigger 0004 (INSERT-only). Consumido pelos use cases (Fatia 2).
NÃO é singleton.
"""

from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from django.db import models as dj_models

from src.domain.operacao.agenda.entities import (
    EventoAgenda,
    EventoAuditoriaAgenda,
    Feriado,
    RegimeJornadaColaborador,
    RegistroNoShow,
)
from src.infrastructure.agenda import mappers
from src.infrastructure.agenda.models import EventoAgenda as EventoAgendaModel
from src.infrastructure.agenda.models import (
    EventoAuditoriaAgenda as EventoAuditoriaAgendaModel,
)
from src.infrastructure.agenda.models import Feriado as FeriadoModel
from src.infrastructure.agenda.models import (
    RegimeJornadaColaborador as RegimeJornadaColaboradorModel,
)
from src.infrastructure.agenda.models import RegistroNoShow as RegistroNoShowModel


class DjangoEventoAgendaRepository:
    """Adapter ORM da raiz EventoAgenda (implementa o Protocol EventoAgendaRepository)."""

    # --- EventoAgenda ---

    def obter_por_id(self, *, tenant_id: UUID, evento_id: UUID) -> EventoAgenda | None:
        """Retorna o evento ou None (cross-tenant → None via RLS → 404 anti-oráculo)."""
        m = EventoAgendaModel.objects.filter(tenant_id=tenant_id, id=evento_id).first()
        return mappers.model_para_evento(m) if m is not None else None

    def salvar_novo(self, evento: EventoAgenda) -> None:
        """Persiste um evento novo (INSERT).

        Violação do EXCLUDE GIST (overlap) → IntegrityError → use case converte
        em ConflitoAgenda(409) (PLAN-AGE-06 — sem advisory lock).
        """
        campos = mappers.evento_para_campos(evento)
        EventoAgendaModel.objects.create(
            id=evento.id,
            tenant_id=evento.tenant_id,
            **campos,
        )

    def atualizar(self, *, tenant_id: UUID, evento: EventoAgenda) -> None:
        """Atualiza estado + timestamps (bump de ``revision``).

        Eventos passados imutáveis via convenção (D-AGE-3) — move = update +
        append EventoAuditoriaAgenda. O trigger 0004 NÃO bloqueia UPDATE em
        EventoAgenda (só nas tabelas WORM — auditoria/no-show/regime).
        """
        atualizadas = EventoAgendaModel.objects.filter(tenant_id=tenant_id, id=evento.id).update(
            estado=evento.estado.value,
            inicia_at=evento.inicia_at,
            termina_at=evento.termina_at,
            aloca_em_umc=evento.aloca_em_umc,
            confirmar_feriado=evento.confirmar_feriado,
            revision=dj_models.F("revision") + 1,
        )
        if atualizadas != 1:
            raise RuntimeError(
                f"atualizar evento: esperava 1 linha, afetou {atualizadas} "
                f"(evento {evento.id})."
            )

    def listar_por_tecnico_no_dia(
        self,
        *,
        tenant_id: UUID,
        tecnico_id: UUID,
        data: date,
    ) -> list[EventoAgenda]:
        """Lista eventos do técnico em um dia específico (para validação de jornada)."""
        qs = EventoAgendaModel.objects.filter(
            tenant_id=tenant_id,
            tecnico_id=tecnico_id,
            inicia_at__date=data,
        ).exclude(estado="cancelado")
        return [mappers.model_para_evento(m) for m in qs]

    def listar_por_tenant(
        self,
        *,
        tenant_id: UUID,
        tecnico_id: UUID | None = None,
        inicia_apos: datetime | None = None,
        inicia_antes: datetime | None = None,
    ) -> list[EventoAgenda]:
        """Lista eventos com filtros opcionais (grade multi-técnico — 1 query agregada, O(1) em técnicos).

        PLAN-AGE-04: nunca 1 query/técnico. O filtro por ``tecnico_id`` é opcional para
        a grade; se omitido, retorna todos os técnicos do tenant num único queryset.
        """
        qs = EventoAgendaModel.objects.filter(tenant_id=tenant_id)
        if tecnico_id is not None:
            qs = qs.filter(tecnico_id=tecnico_id)
        if inicia_apos is not None:
            qs = qs.filter(inicia_at__gte=inicia_apos)
        if inicia_antes is not None:
            qs = qs.filter(inicia_at__lt=inicia_antes)
        return [mappers.model_para_evento(m) for m in qs]

    def salvar_auditoria(self, registro: EventoAuditoriaAgenda) -> None:
        """Persiste registro de auditoria WORM (INSERT-only — INV-AG-AUDIT-WORM-001).

        Trigger 0004 bloqueia UPDATE e DELETE nesta tabela.
        """
        EventoAuditoriaAgendaModel.objects.create(
            id=registro.id,
            tenant_id=registro.tenant_id,
            evento_id=registro.evento_id,
            acao=registro.acao.value,
            actor_usuario_id=registro.actor_usuario_id,
            occurred_at=registro.occurred_at,
            payload_resumo=registro.payload_resumo,
        )

    def salvar_no_show(self, registro: RegistroNoShow) -> None:
        """Persiste registro de no-show WORM (INSERT-only — INV-AG-AUDIT-WORM-001)."""
        RegistroNoShowModel.objects.create(
            id=registro.id,
            tenant_id=registro.tenant_id,
            evento_id=registro.evento_id,
            tecnico_id=registro.tecnico_id,
            ocorrido_em=registro.ocorrido_em,
            custo_estimado=registro.custo_estimado,
            cobrar_cliente=registro.cobrar_cliente,
            registrado_por_usuario_id=registro.registrado_por_usuario_id,
            observacao=registro.observacao,
        )

    def tem_agenda_futura(self, *, tenant_id: UUID, colaborador_id: UUID) -> bool:
        """True se o técnico tem eventos futuros (para ``esta_referenciado`` — D-AGE-12)."""
        from django.utils import timezone

        return (
            EventoAgendaModel.objects.filter(
                tenant_id=tenant_id,
                tecnico_id=colaborador_id,
                inicia_at__gt=timezone.now(),
            )
            .exclude(estado="cancelado")
            .exists()
        )

    def listar_feriados(
        self,
        *,
        tenant_id: UUID,
        data_inicio: date,
        data_fim: date,
    ) -> list[Feriado]:
        """Lista feriados (nacionais + custom do tenant) no intervalo (D-AGE-10)."""
        qs = FeriadoModel.objects.filter(
            data__gte=data_inicio,
            data__lte=data_fim,
            ativo=True,
        ).filter(
            # nacionais (tenant=None) OU custom do tenant
            dj_models.Q(tenant__isnull=True) | dj_models.Q(tenant_id=tenant_id)
        )
        return [mappers.model_para_feriado(m) for m in qs]

    def salvar_feriado(self, feriado: Feriado) -> None:
        """Persiste feriado custom do tenant (INSERT)."""
        FeriadoModel.objects.create(
            id=feriado.id,
            tenant_id=feriado.tenant_id,
            data=feriado.data,
            descricao=feriado.descricao,
            nacional=feriado.nacional,
            ativo=feriado.ativo,
        )

    def salvar_regime_override(self, override: RegimeJornadaColaborador) -> None:
        """Persiste override de regime de jornada (INSERT-com-vigência WORM)."""
        RegimeJornadaColaboradorModel.objects.create(
            id=override.id,
            tenant_id=override.tenant_id,
            colaborador_id=override.colaborador_id,
            regime=override.regime.value,
            vigencia_inicio=override.vigencia_inicio,
            vigencia_fim=override.vigencia_fim,
            definido_por_usuario_id=override.definido_por_usuario_id,
            fonte=override.fonte.value,
            justificativa=override.justificativa,
        )
