"""Predicates ABAC do modulo `calibracao` (T-CAL-037..039 / P4 Fase 2 Batch C).

3 predicates exigidos pelo plan.md M4 + spec §3.1 + ADRs 0024/0026/0040/0063:

- `cmc_cobre` (T-CAL-037) — INV-CAL-CMC-001 / P-CAL-R1.
  Valida que tenant RBC tem CMC (Calibration & Measurement Capability)
  declarada na CGCRE cobrindo a grandeza + faixa solicitada na
  configuracao da calibracao (US-CAL-002).
  STUB Wave A — modulo `escopo_acreditado` nao existe; ate la
  retorna `(True, "")` (fail-open documentado por GATE-CAL-CMC-1).

- `procedimento_vigente_para` (T-CAL-038) — US-CAL-016.
  Valida que o tenant tem procedimento tecnico vigente para a grandeza
  na data da configuracao (cl. 7.2 + INV-CAL-PROC-001).
  STUB Wave A — modulo `procedimentos_tecnicos` nao existe; fail-open.

- `pode_aprovar_revisao_2a_conferencia` (T-CAL-039) — INV-CAL-FRAUDE-CONF-001
  + INV-CAL-FRAUDE-REV-001 + ADR-0026.
  Valida segregacao de funcoes: revisor != executor; conferente != revisor
  e != executor. ADR-0026 abre excecao objetiva (4 condicoes + 5%/mes).
  Real (nao stub) — opera sobre IDs cru no resource sem precisar DB.

Contrato (PredicateFn):
- Cada predicate recebe `resource: dict[str, Any]` (mesma interface dos
  predicates_os T-OS-023..027).
- Retorna `(True, "")` quando ALLOW OU quando predicate nao aplica
  (fail-open semantico).
- Retorna `(False, "reason_estavel")` quando DENY.
- Reasons curtas e estaveis — consumers comparam string.

Diferenca vs predicates_os:
- predicates_os foca em RT competencia + escopo + dispensa OS.
- predicates_calibracao foca em CMC + procedimento + segregacao de funcoes
  ISO 17025 cl. 6.2/7.7.

Por que `_calibracao` no nome:
- Symmetric com `predicates_os` (modulo ordens_servico).
- Marco 4 pode adicionar mais predicates aqui (saga subcontratacao,
  override regra decisao, override 2a conferencia) sem colidir com nomes
  do M3.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

# Slugs de excecoes ADR-0026 — 2a conferencia pode ser pelo proprio revisor
# em 4 condicoes objetivas:
#  1. Tenant <= 5 calibracoes/mes (laboratorio pequeno).
#  2. Grandeza com escopo CMC limitado (so 1 RT competente).
#  3. Atividade urgente (cliente em recall obrigatorio).
#  4. Documentacao tecnica auto-suficiente (rastreabilidade reforcada).
#
# Cada excecao registrada em EventoDeCalibracao tipo=excecao_2a_conferencia
# com motivo_canonicalizado (cl. 7.8.6 + ADR-0026).
EXCECOES_2A_CONFERENCIA = frozenset(
    {
        "TENANT_PEQUENO_5_CAL_MES",
        "GRANDEZA_RT_UNICO_TENANT",
        "CALIBRACAO_URGENTE_RECALL",
        "DOC_TECNICA_AUTO_SUFICIENTE",
    }
)


def _coerce_uuid(raw: object) -> UUID | None:
    """Helper: converte raw para UUID; None se invalido/ausente."""
    if raw is None:
        return None
    try:
        return UUID(str(raw))
    except (ValueError, TypeError):
        return None


# =============================================================
# T-CAL-037 — cmc_cobre (STUB Wave A — GATE-CAL-CMC-1)
# Escopo: actions onde tenant RBC configura calibracao com grandeza+faixa
# que deve estar dentro do CMC declarado na CGCRE.
# Quando modulo `escopo_acreditado` entrar em Wave A: substituir o stub
# por consulta a `EscopoAcreditadoTenant(tenant_id, grandeza, faixa_min,
# faixa_max, vigente_em(data))` — drop-in (contrato resource preservado).
# =============================================================


def cmc_cobre(resource: dict[str, Any]) -> tuple[bool, str]:
    """Predicate ABAC — CMC do tenant RBC cobre grandeza + faixa solicitada.

    **DEPRECATED 2026-05-30 (ADR-0073 / M6 escopos-cmc Fatia 3 — T-ECMC-040):**
    A validacao de cobertura de faixa CMC MIGROU para DENTRO do use case
    `configurar_calibracao` (chamada `escopos_cmc.query_service.cobre`), porque o
    permission layer DRF nao tem dado metrologico server-side (grandeza/faixa) no
    momento em que o predicate e avaliado (ver ADR-0073 Contexto). Este predicate
    permanece registrado em `apps.py` como NO-OP documentado durante a transicao
    (remocao coordenada futura — nao no mesmo commit). O anti-fraude de perfil
    (itens 1-3 abaixo, ADR-0067) continua valido e ainda e exercitado nos testes;
    a contencao de faixa (`cmc_fora_do_escopo`) NAO e mais responsabilidade deste
    predicate.

    **RETROFIT 2026-05-27 (T-SAN-PERFIL-018 / Sprint 2 ADR-0067):**
    Antes da auditoria 10 lentes, este predicate lia `tipo_acreditacao` do
    PAYLOAD da request — vulneravel a fraude documental (FAIL L6 da auditoria
    2026-05-27). Operador autenticado em qualquer tenant podia mandar
    `tipo_acreditacao=RBC` no JSON e gerar certificado fraudulento.

    Solucao canonica:
    1. Le perfil regulatorio do TENANT via ContextVar (nao do payload).
    2. Tenant nao-A (B/C/D) tentando submeter `tipo_acreditacao=RBC` no
       payload = 412 `tipo_acreditacao_divergente_do_tenant` + evento
       `tentativa_downgrade_perfil` (AC-SAN-PERFIL-002-2). View handler
       captura o reason e grava evento WORM.
    3. Compat-shim: se payload mandar `tipo_acreditacao` (legado), o valor e
       IGNORADO + WARN log `payload_tipo_acreditacao_obsoleto` (AC-006-3).
       Compat-shim vigora ate fim de Wave A modulo `certificados`.

    Resource esperado:
        tenant_id: UUID (obrigatorio).
        grandeza: str — slug da grandeza (lowercase). Ausente => DENY
          quando perfil='A' (CMC exige declarar grandeza).
        faixa_min: str | Decimal — limite inferior da faixa solicitada.
        faixa_max: str | Decimal — limite superior.
        data: ISO date "YYYY-MM-DD" — data alvo (CMC vigente em).
        tipo_acreditacao: **DEPRECATED**. Compat-shim ate fim de Wave A:
          se presente E divergente do tenant, retorna DENY com reason
          `tipo_acreditacao_divergente_do_tenant`.

    Reasons estaveis:
        cmc_fora_do_escopo — tenant A com grandeza+faixa fora do CMC.
        cmc_grandeza_resource_ausente — A sem campo grandeza no resource.
        cmc_resource_invalido — tenant_id ausente.
        tipo_acreditacao_divergente_do_tenant — payload tenta RBC em tenant
          nao-A (fraude tentada — FAIL L6 fechado).
        tenant_perfil_indisponivel — ContextVar vazio E DB falhou (fail-closed).
    """
    import logging

    from src.infrastructure.authz.perfil_tenant_helper import (
        obter_perfil_tenant_corrente,
    )

    log = logging.getLogger(__name__)

    tenant_id = _coerce_uuid(resource.get("tenant_id"))
    if tenant_id is None:
        return False, "cmc_resource_invalido"

    perfil = obter_perfil_tenant_corrente()
    if not perfil:
        # Fail-closed: ContextVar vazio + DB falhou (job sem middleware OU
        # tenant em estado invalido). Loga ERROR pra alerta.
        log.error(
            "cmc_cobre: perfil_regulatorio indisponivel para tenant=%s "
            "(ContextVar vazio + fallback DB falhou). Bloqueando.",
            tenant_id,
        )
        return False, "tenant_perfil_indisponivel"

    # Compat-shim: payload legado mandando `tipo_acreditacao`. Detecta divergencia.
    # AC-006-3 + AC-002-2 — fraude tentada quando perfil!=A mas payload diz RBC.
    payload_tipo = (resource.get("tipo_acreditacao") or "").strip().upper()
    if payload_tipo:
        log.warning(
            "payload_tipo_acreditacao_obsoleto: campo `tipo_acreditacao` no "
            "payload e DEPRECATED (T-SAN-PERFIL-018). Perfil canonico vem de "
            "Tenant.perfil_regulatorio via ContextVar. Removendo no fim de Wave A."
        )
        if payload_tipo == "RBC" and perfil != "A":
            # Fraude tentada — operador em tenant B/C/D enviou tipo_acreditacao=RBC
            # no payload. Bloqueia + reason estavel (view registra evento WORM).
            return False, "tipo_acreditacao_divergente_do_tenant"

    # Perfil != A nao precisa validar CMC (CMC so vale para acreditados RBC).
    if perfil != "A":
        return True, ""

    grandeza = (resource.get("grandeza") or "").strip().lower()
    if not grandeza:
        return False, "cmc_grandeza_resource_ausente"

    # GATE-CAL-CMC-PREDICATE STUB Wave A (ADR-0066 — paralelo a ADR-0063 do M3 OS).
    # Modulo `metrologia/escopos-cmc` ainda nao existe. Fail-open lazy controlado:
    # quando modulo entrar em Wave A:
    #   from src.infrastructure.metrologia.escopos_cmc.repository import escopo_repo
    #   if not escopo_repo.cobre(tenant_id, grandeza, faixa_min, faixa_max, data):
    #       return False, "cmc_fora_do_escopo"
    # Ate la, fail-open com log consultivo. Bloqueio efetivo entra automaticamente
    # quando modulo for criado.
    return True, ""


# =============================================================
# T-CAL-038 — procedimento_vigente_para (STUB Wave A — GATE-CAL-PROC-1)
# Cl. 7.2 ISO 17025 + INV-CAL-PROC-001 — tenant precisa ter procedimento
# tecnico documentado vigente na data da calibracao.
# =============================================================


def procedimento_vigente_para(resource: dict[str, Any]) -> tuple[bool, str]:
    """Predicate ABAC — procedimento tecnico vigente na data (cl. 7.2).

    Resource esperado:
        tenant_id: UUID.
        grandeza: str — slug. Ausente => predicate nao aplica.
        data: ISO date "YYYY-MM-DD" — data alvo.

    Reasons estaveis:
        procedimento_inexistente — tenant nao tem procedimento p/ grandeza.
        procedimento_vencido — procedimento existe mas vigente_ate < data.
        procedimento_resource_invalido — tenant_id ausente.
    """
    tenant_id = _coerce_uuid(resource.get("tenant_id"))
    if tenant_id is None:
        return False, "procedimento_resource_invalido"

    grandeza = (resource.get("grandeza") or "").strip().lower()
    if not grandeza:
        # Atividade nao-calibracao (sem grandeza) — predicate nao aplica.
        return True, ""

    # GATE-CAL-PROC-1 STUB: modulo `procedimentos_tecnicos` nao existe.
    # Quando entrar em Wave A:
    #   from src.infrastructure.procedimentos_tecnicos.repository import proc_repo
    #   vigente = proc_repo.vigente_em(tenant_id, grandeza, data)
    #   if vigente is None: return False, "procedimento_inexistente"
    #   if vigente.vigente_ate < data_alvo: return False, "procedimento_vencido"
    return True, ""


# =============================================================
# T-CAL-039 — pode_aprovar_revisao_2a_conferencia (REAL, nao stub)
# Segregacao de funcoes ISO 17025 cl. 6.2.5 + INV-CAL-FRAUDE-REV-001 +
# INV-CAL-FRAUDE-CONF-001 + ADR-0026 (excecao objetiva 4 condicoes).
# =============================================================


def pode_aprovar_revisao_2a_conferencia(
    resource: dict[str, Any],
) -> tuple[bool, str]:
    """Predicate ABAC — segregacao de funcoes ISO 17025 cl. 6.2.5.

    Resource esperado:
        action: str — "revisao" | "2a_conferencia". Define qual
          regra de segregacao se aplica.
        executor_id: UUID — quem executou as medicoes (US-CAL-004).
        revisor_id: UUID — quem aprovou a revisao (US-CAL-007).
          Obrigatorio quando action=2a_conferencia.
        conferente_id: UUID — quem aprovou a 2a conferencia (US-CAL-008).
          Sempre obrigatorio.
        excecao_motivo: str | None — codigo ADR-0026 (opcional):
          TENANT_PEQUENO_5_CAL_MES | GRANDEZA_RT_UNICO_TENANT |
          CALIBRACAO_URGENTE_RECALL | DOC_TECNICA_AUTO_SUFICIENTE.

    Regras:
        action=revisao: revisor_id != executor_id (ou excecao ADR-0026).
        action=2a_conferencia: conferente_id != revisor_id E
          conferente_id != executor_id (ou excecao ADR-0026).

    Reasons estaveis:
        fraude_revisor_eh_executor — INV-CAL-FRAUDE-REV-001.
        fraude_conferente_eh_revisor_ou_executor — INV-CAL-FRAUDE-CONF-001.
        excecao_adr_0026_invalida — codigo de excecao fora da whitelist.
        revisao_conferencia_resource_invalido — campos obrigatorios ausentes.
    """
    action = (resource.get("action") or "").strip().lower()
    if action not in {"revisao", "2a_conferencia"}:
        return False, "revisao_conferencia_resource_invalido"

    executor_id = _coerce_uuid(resource.get("executor_id"))
    if executor_id is None:
        return False, "revisao_conferencia_resource_invalido"

    excecao = resource.get("excecao_motivo")
    if excecao is not None:
        if excecao not in EXCECOES_2A_CONFERENCIA:
            return False, "excecao_adr_0026_invalida"
        # ADR-0026: excecao registrada -> ALLOW (caller persiste evento
        # EventoDeCalibracao tipo=excecao_2a_conferencia com motivo).
        return True, ""

    if action == "revisao":
        revisor_id = _coerce_uuid(resource.get("revisor_id"))
        if revisor_id is None:
            return False, "revisao_conferencia_resource_invalido"
        if revisor_id == executor_id:
            return False, "fraude_revisor_eh_executor"
        return True, ""

    # action == "2a_conferencia"
    revisor_id = _coerce_uuid(resource.get("revisor_id"))
    conferente_id = _coerce_uuid(resource.get("conferente_id"))
    if revisor_id is None or conferente_id is None:
        return False, "revisao_conferencia_resource_invalido"
    if conferente_id == revisor_id or conferente_id == executor_id:
        return False, "fraude_conferente_eh_revisor_ou_executor"
    return True, ""
