"""Erros de domínio da agenda (Fatia 1a — T-AGE-016).

Cada erro carrega ``reason`` — código estável que a aplicação mapeia para HTTP 4xx.
Hierarquia molde ``src/domain/contas_receber/erros.py``.

HTTP mapeado (pela view, nunca pelo domínio):
- 422 — validação de negócio (jornada, CNH, feriado).
- 412 — pré-condição falhou (sem RT no slot).
- 409 — conflito de recurso (overlap de agenda).
- 500 / dead-letter — indeterminado / fail-closed.
"""

from __future__ import annotations


class AgendaDomainError(Exception):
    """Base do domínio agenda (mapeada a 4xx/5xx pela aplicação)."""

    reason = "agenda_erro"


# --- Jornada UMC (422) ---


class JornadaUMCViolada(AgendaDomainError):
    """Alocação viola a jornada UMC (Lei 13.103 / INV-AG-JORNADA-UMC-001).

    Carrega ``motivo``, ``faltante_min`` e ``proximo_slot`` para que a
    aplicação devolva um 422 acionável ao frontend (US-AG-003 / AC-AG-003-1).

    Perfil-AGNÓSTICA: jornada é ordem pública trabalhista, não depende de
    perfil regulatório A/B/C/D (D-AGE-4 / RBC-AGE-01 / ADV-AGE-01).
    """

    reason = "JORNADA_UMC_VIOLADA"


# --- RT sem competência no slot (412) ---


class SemRTNoSlot(AgendaDomainError):
    """Perfil A determinístico: ausência de RT titular OU substituto competente
    no instante do slot → 412 (D-AGE-6 / INV-AG-PERFIL-001).

    O gate DURO de NC (cl. 6.2.5/7.8 — não emitir RBC sem signatário) vive
    na emissão (``certificados``); a agenda apenas alerta com 412 no perfil A
    determinístico.
    """

    reason = "SEM_RT_NO_SLOT"


# --- Conflito de overlap (409) ---


class ConflitoAgenda(AgendaDomainError):
    """Sobreposição de horário para o mesmo técnico (INV-AG-OVERLAP-001).

    Garantida pelo EXCLUDE GIST com ``tenant_id`` como 1ª coluna (D-AGE-13 /
    TL-AGE-01). O banco devolve violação de constraint; a view mapeia para 409.
    """

    reason = "CONFLITO_AGENDA"


# --- Motorista sem CNH (422) ---


class MotoristaSemCNH(AgendaDomainError):
    """``MOTORISTA_UMC`` com ``pendencia_cnh`` ou CNH vencida tentando alocar
    em evento ``aloca_em_umc=True`` (D-AGE-7 / INV-AG-CNH-001 / R13).

    A agenda checa via ``ColaboradorAgendaPort`` antes de gravar → 422.
    """

    reason = "MOTORISTA_SEM_CNH"


# --- Feriado não confirmado (422) ---


class FeriadoNaoConfirmado(AgendaDomainError):
    """Tentativa de agendar em feriado sem ``confirmar_feriado=True`` (D-AGE-10).

    O use case valida antes de gravar; a view mapeia para 422.
    """

    reason = "FERIADO_NAO_CONFIRMADO"


# --- Atividade obrigatória (422) ---


class AtividadeObrigatoria(AgendaDomainError):
    """``EventoAgenda`` do tipo ``os`` criado sem ``atividade_id`` (INV-AG-ATIVIDADE-001).

    Invariante do ``__post_init__`` da entidade; levantada antes de qualquer
    persistência.
    """

    reason = "ATIVIDADE_OBRIGATORIA"


# --- Perfil indeterminado (fail-closed) ---


class PerfilIndeterminado(AgendaDomainError):
    """``perfil_no_evento`` chegou ``None`` no consumer (INV-AG-PERFIL-001 / D-AGE-6).

    Consumer PROIBIDO de reler ``obter_perfil_tenant_corrente()`` no worker —
    perfil deve vir do envelope. ``None`` → fail-closed → dead-letter.
    Espelha ``PerfilIndeterminado`` de contas-receber.
    """

    reason = "PERFIL_INDETERMINADO"


# --- Regime indeterminado (advisory / fail-safe) ---


class RegimeIndeterminado(AgendaDomainError):
    """Papéis de campo conflitantes sem override humano (D-AGE-15 / INV-AG-REGIME-001).

    Não bloqueia a alocação — o sistema aloca com ``nao_aplica`` + audit WORM
    + pendência de enquadramento (warn, não erro fatal). Levantado para
    registrar a condição no log de auditoria.
    """

    reason = "REGIME_INDETERMINADO"


# --- Transição proibida (409) ---


class TransicaoEventoProibida(AgendaDomainError):
    """Transição de estado proibida pela máquina de estados (D-AGE-3).

    Ex.: tentar cancelar um evento ``concluido`` (terminal).
    """

    reason = "TRANSICAO_EVENTO_PROIBIDA"


# --- Evento não encontrado (404) ---


class EventoNaoEncontrado(AgendaDomainError):
    """Evento inexistente para o ``(tenant_id, evento_id)`` informado.

    A aplicação mapeia para 404 anti-oráculo (cross-tenant → None via RLS → 404).
    """

    reason = "EVENTO_NAO_ENCONTRADO"


# --- Conflito resolvido sem justificativa suficiente (422) ---


class JustificativaConflitoCurta(AgendaDomainError):
    """Justificativa de resolução de conflito com menos de 30 caracteres
    (US-AG-011 / AC-AG-011-2 — validação server-side).
    """

    reason = "JUSTIFICATIVA_CONFLITO_CURTA"
