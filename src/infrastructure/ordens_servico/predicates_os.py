"""Predicates ABAC do modulo `ordens_servico` (T-OS-023..027 / Fase 3 P4 Marco 3).

5 predicates exigidos pela P3 retrofit (matriz reconciliacao §"Decisoes
absorvidas") + spec §13.10/§13.23/§13.24:

- `rt_competencia_cobre` — INV-OS-ATIV-005-EXEC-COMP / P-OS-R1.
  Valida que o tecnico_executor designado tem RT ativo no tenant E que
  ha `RTCompetencia` cobrindo a grandeza da atividade na `data`.
- `tenant_dentro_escopo_acreditado` — P-OS-R3 / GATE-RBC-ESCOPO-1.
  Valida que o tenant esta dentro do escopo acreditado pra grandeza+faixa.
  STUB Wave A — modulo `licencas-acreditacoes` ainda nao existe; ate la
  retorna `(True, "")` (fail-open documentado por GATE-RBC-ESCOPO-1).
- `pode_estender_janela_cal_link_atividade` — exclusivo gerente/RT.
- `pode_dispensar_aceite` — P-OS-A4 / GATE-OS-CONSBIO-TEXTO-OAB.
  Valida precedente obrigatorio (no_show OR recusa OR impossibilidade).
- `pode_criar_os_produtiva_balancas` — P-OS-S1 / R-OS-11 / GATE-SEG-BPT-1.
  Consulta feature flag `OS_PRODUTIVO_DOGFOODING_BS` (default False).
  Soh aplica ao tenant `balancas-solution` (dogfooding interno).

Contrato com `AuthorizationProvider`:
- Cada predicate recebe APENAS `resource: dict[str, Any]` (assinatura
  fixa em `PredicateFn`). Caller injeta `tenant_id` / `user_id` /
  `grandeza` / `data` dentro do dict.
- Retorno: `(True, "")` quando ALLOW (ou predicate nao aplica), ou
  `(False, "reason_estavel")` quando DENY. `reason` curta e estavel —
  consumers comparam string.
- Predicates SEM `tenant_id` em resource sao geralmente fail-open (nao
  aplica) — `AuthorizationProvider` ja injeta tenant via middleware;
  rota interna cuida.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

# Slug do tenant Balancas Solution (dogfooding interno P-OS-S1).
# Hardcoded aqui porque eh UMA constante de produto, nao config dinamica.
TENANT_BALANCAS_SLUG = "balancas-solution"

# Feature flag P-OS-S1 (consultada em `pode_criar_os_produtiva_balancas`).
FEATURE_KEY_OS_PRODUTIVO_BS = "OS_PRODUTIVO_DOGFOODING_BS"
FEATURE_MODULO_OS_PRODUTIVO_BS = "ordens_servico"


def _coerce_uuid(raw: object) -> UUID | None:
    """Helper: converte raw para UUID; None se invalido/ausente."""
    if raw is None:
        return None
    try:
        return UUID(str(raw))
    except (ValueError, TypeError):
        return None


# =============================================================
# T-OS-023 — rt_competencia_cobre
# Escopo: actions onde o `tecnico_executor_id` precisa estar competente
# pra grandeza da atividade — `atividade.atribuir`, `atividade.iniciar`,
# `os.adicionar_atividade` (quando a atividade carrega grandeza).
# Politica de fail-open CONTROLADA: se o `resource` nao traz `grandeza`
# (= atividade nao-calibracao), o predicate NAO aplica (True, "").
# Quando traz grandeza E faltar info pra avaliar (tenant/user/data) -> DENY.
# =============================================================


def rt_competencia_cobre(resource: dict[str, Any]) -> tuple[bool, str]:
    """Predicate ABAC — RT do tenant precisa cobrir a grandeza na data.

    Resource esperado:
        tenant_id: UUID (obrigatorio quando ha grandeza).
        executor_user_id: UUID — usuario que vai executar (obrigatorio).
        grandeza: str — slug da grandeza (lowercase + underscore).
          Ausente OU "" => predicate nao aplica (atividade nao-calibracao).
        data: ISO date "YYYY-MM-DD" — data alvo (declarado_em <= data
          < vigente_ate). Default = hoje.

    Reasons estaveis:
        rt_competencia_resource_invalido — campos obrigatorios ausentes.
        rt_inativo_no_tenant — sem RT vigente vinculado ao usuario.
        rt_competencia_grandeza_nao_coberta — RT existe mas sem competencia
          na grandeza+data.
    """
    grandeza = resource.get("grandeza") or ""
    if not grandeza:
        return True, ""  # nao aplica (manutencao/instalacao/etc.)

    tenant_id = _coerce_uuid(resource.get("tenant_id"))
    user_id = _coerce_uuid(resource.get("executor_user_id"))
    if tenant_id is None or user_id is None:
        return False, "rt_competencia_resource_invalido"

    from datetime import date

    data_raw = resource.get("data")
    if data_raw is None:
        data_alvo = date.today()
    else:
        try:
            data_alvo = date.fromisoformat(str(data_raw))
        except (ValueError, TypeError):
            return False, "rt_competencia_resource_invalido"

    # Import tardio — apps loading
    from django.db.models import Q

    from src.infrastructure.responsavel_tecnico.models import (
        ResponsavelTecnicoTenant,
        RTCompetencia,
    )

    rt_ativo_ids = list(
        ResponsavelTecnicoTenant.objects.filter(
            tenant_id=tenant_id,
            usuario_id=user_id,
            encerrado_em__isnull=True,
        ).values_list("id", flat=True)
    )
    if not rt_ativo_ids:
        return False, "rt_inativo_no_tenant"

    grandeza_norm = grandeza.lower().strip()
    cobre = RTCompetencia.objects.filter(
        tenant_id=tenant_id,
        rt_id__in=rt_ativo_ids,
        grandeza=grandeza_norm,
        declarado_em__lte=data_alvo,
    ).filter(Q(vigente_ate__isnull=True) | Q(vigente_ate__gt=data_alvo))
    if not cobre.exists():
        return False, "rt_competencia_grandeza_nao_coberta"
    return True, ""


# =============================================================
# T-OS-024 — tenant_dentro_escopo_acreditado (STUB Wave A)
# GATE-RBC-ESCOPO-1: modulo `licencas-acreditacoes` ainda nao existe.
# Ate la o predicate fica REGISTRADO (contrato cravado) mas retorna
# True (fail-open). Auditoria/log marca evento `EventoDeOS.tipo=
# fora_escopo_aceito_perfil_BCD` quando consumer vier (T-OS-035).
# Quando modulo entrar em Wave A: substituir o stub por consulta a
# `EscopoAcreditadoTenant(tenant_id, grandeza, faixa_min, faixa_max,
# vigente_em(data))`. Soh tenants perfil A/RBC viram bloqueio duro;
# B/C/D continuam fail-open.
# =============================================================


def tenant_dentro_escopo_acreditado(resource: dict[str, Any]) -> tuple[bool, str]:
    """Predicate ABAC — escopo acreditado do tenant cobre a grandeza+faixa.

    STUB Wave A (GATE-RBC-ESCOPO-1). Retorna `(True, "")` ate o modulo
    `licencas-acreditacoes` existir. Contrato preservado: caller injeta
    `tenant_id`, `grandeza`, `faixa_min`, `faixa_max`, `data` pra que
    a substituicao do stub seja drop-in.

    Reasons (quando deixar de ser STUB):
        fora_do_escopo_acreditado — tenant perfil A sem cobertura.
        escopo_resource_invalido — campos obrigatorios ausentes.
    """
    # GATE-RBC-ESCOPO-1: predicate consultivo. Bloqueio duro entra com
    # `licencas-acreditacoes` + ADR de perfil RBC do tenant.
    return True, ""


# =============================================================
# T-OS-025 — pode_estender_janela_cal_link_atividade
# Spec §3.2 / P-OS-R2 — soh gerente_operacional ou rt_signatario podem
# estender a janela do watchdog cal-link de uma atividade especifica.
# Predicate consulta `perfis` do usuario no resource (caller injeta).
# =============================================================

_PERFIS_PODEM_ESTENDER_CAL_LINK: frozenset[str] = frozenset(
    {"gerente_operacional", "rt_signatario", "signatario", "admin_tenant"}
)


def pode_estender_janela_cal_link_atividade(
    resource: dict[str, Any],
) -> tuple[bool, str]:
    """Predicate ABAC — soh perfis gerente/RT podem estender janela watchdog.

    Resource esperado:
        perfis: list[str] — codigos dos perfis do usuario no tenant.
        atividade_id: UUID — atividade alvo (validacao de tenant em outra camada).

    Reasons:
        sem_perfil_para_estender_janela — perfil insuficiente.
        cal_link_resource_invalido — campos obrigatorios ausentes.
    """
    perfis_raw = resource.get("perfis")
    if not isinstance(perfis_raw, list | tuple | set | frozenset):
        return False, "cal_link_resource_invalido"

    perfis = {str(p) for p in perfis_raw}
    if not perfis & _PERFIS_PODEM_ESTENDER_CAL_LINK:
        return False, "sem_perfil_para_estender_janela"
    return True, ""


# =============================================================
# T-OS-026 — pode_dispensar_aceite (P-OS-A4)
# Dispensa SOH permitida quando ha precedente registrado:
#   - EventoDeOS.tipo='no_show_cliente' pra atividade, OU
#   - EvidenciaFotoAtividade com `tipo_evidencia` recusa_explicita, OU
#   - `precedente_tipo='impossibilidade_tecnica'` (autorizada por gerente).
# Ate o modulo de qualidade Wave B integrar todos os tipos, predicate
# usa `precedente_tipo` declarado pelo caller + valida precedent_evento_id.
# =============================================================

_PRECEDENTES_VALIDOS: frozenset[str] = frozenset(
    {"no_show", "recusa_explicita", "impossibilidade_tecnica"}
)


def pode_dispensar_aceite(resource: dict[str, Any]) -> tuple[bool, str]:
    """Predicate ABAC — dispensa de aceite exige precedente (P-OS-A4).

    Resource esperado:
        tenant_id: UUID.
        atividade_id: UUID — atividade alvo.
        precedente_tipo: str — um de {no_show, recusa_explicita,
          impossibilidade_tecnica}.
        precedente_evento_id: UUID | None — referencia ao evento
          precedente (obrigatorio quando tipo != impossibilidade_tecnica).

    Reasons:
        dispensa_sem_precedente — tipo precedente ausente/invalido.
        dispensa_evento_inexistente — precedente_evento_id nao corresponde
          a EventoDeOS no_show_cliente desta atividade (quando exigido).
        dispensa_resource_invalido — campos obrigatorios ausentes.
    """
    tenant_id = _coerce_uuid(resource.get("tenant_id"))
    atividade_id = _coerce_uuid(resource.get("atividade_id"))
    if tenant_id is None or atividade_id is None:
        return False, "dispensa_resource_invalido"

    precedente_tipo = str(resource.get("precedente_tipo") or "").strip()
    if precedente_tipo not in _PRECEDENTES_VALIDOS:
        return False, "dispensa_sem_precedente"

    # `impossibilidade_tecnica` precisa apenas autorizacao do gerente
    # (validada na camada de application via a3_assinatura_hash). Os outros
    # dois exigem precedente_evento_id (FK polimorfica em DispensaAceiteAtividade).
    if precedente_tipo == "impossibilidade_tecnica":
        return True, ""

    precedente_evento_id = _coerce_uuid(resource.get("precedente_evento_id"))
    if precedente_evento_id is None:
        return False, "dispensa_sem_precedente"

    # Para precedente=no_show: confere EventoDeOS no_show_cliente real
    # nesta atividade. Para recusa_explicita: confere EvidenciaFotoAtividade
    # (entidade Marco 3 ja existe).
    from src.infrastructure.ordens_servico.models import (
        EventoDeOS,
        EvidenciaFotoAtividade,
    )

    if precedente_tipo == "no_show":
        existe = EventoDeOS.objects.filter(
            tenant_id=tenant_id,
            atividade_id=atividade_id,
            id=precedente_evento_id,
            tipo="no_show_cliente",
        ).exists()
    else:  # recusa_explicita
        existe = EvidenciaFotoAtividade.objects.filter(
            tenant_id=tenant_id,
            atividade_id=atividade_id,
            id=precedente_evento_id,
        ).exists()
    if not existe:
        return False, "dispensa_evento_inexistente"
    return True, ""


# =============================================================
# T-OS-027 — pode_criar_os_produtiva_balancas (P-OS-S1 + GATE-SEG-BPT-1)
# Predicate especifico do tenant Balancas Solution (dogfooding). Para
# qualquer outro tenant retorna True (nao aplica). Para BS consulta a
# feature flag `OS_PRODUTIVO_DOGFOODING_BS`. Default = False enquanto
# apolice BPT nao for emitida (R-OS-11 risco depositario CC art. 627).
# =============================================================


def pode_criar_os_produtiva_balancas(resource: dict[str, Any]) -> tuple[bool, str]:
    """Predicate ABAC — bloqueia OS produtiva em Balancas ate apolice BPT.

    Resource esperado:
        tenant_id: UUID — tenant da OS.

    Reasons:
        balancas_dogfooding_bloqueado — flag OS_PRODUTIVO_DOGFOODING_BS = False.
        balancas_resource_invalido — tenant_id ausente.
    """
    tenant_id = _coerce_uuid(resource.get("tenant_id"))
    if tenant_id is None:
        return False, "balancas_resource_invalido"

    # Import tardio — apps loading
    from src.infrastructure.feature_flag.models import FeatureFlag
    from src.infrastructure.tenant.models import Tenant

    tenant = Tenant.objects.filter(id=tenant_id).only("slug").first()
    if tenant is None or tenant.slug != TENANT_BALANCAS_SLUG:
        return True, ""  # nao aplica

    flag = (
        FeatureFlag.objects.filter(
            tenant_id=tenant_id,
            modulo=FEATURE_MODULO_OS_PRODUTIVO_BS,
            feature_key=FEATURE_KEY_OS_PRODUTIVO_BS,
        )
        .only("ativo")
        .first()
    )
    if flag is None or not flag.ativo:
        return False, "balancas_dogfooding_bloqueado"
    return True, ""
