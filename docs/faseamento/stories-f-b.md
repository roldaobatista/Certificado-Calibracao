---
owner: roldao
revisado_em: 2026-05-18
proximo_review: 2026-08-18
status: deprecated
diataxis: reference
audiencia: agente
substituido_por: docs/faseamento/F-B/spec.md
relacionados:
  - docs/faseamento-foundation-waves.md
  - docs/governanca/debitos-ritual.md
  - docs/adr/0006-feature-flags.md
  - docs/adr/0012-autorizacao-unificada.md
  - REGRAS-INEGOCIAVEIS.md
---

# Stories retrospectivas Foundation F-B

> **Pra quê:** F-B entregou app `authz` sem ritual Spec Kit. Este arquivo mapeia retroativamente em `US-FB-NNN` com ACs binários derivados dos critérios de saída em `docs/faseamento-foundation-waves.md` §3.

---

## US-FB-001: Promover ADRs 0006 (feature flags) e 0012 (autorização) proposta → aceita
**Como** orquestrador F-B, **quero** as ADRs gates de entrada formalizadas com adendos da aceitação, **para** registrar decisões na timeline antes do código.

- **AC-FB-001-1**: ADR-0012 status alterado pra `aceita` com 3 ajustes documentados (django-allauth diferido, cache LocMem, 4 perfis seed).
- **AC-FB-001-2**: ADR-0006 status alterado pra `aceita`.
- **AC-FB-001-3**: Tabela §11 do AGENTS.md reflete novo status.

**Tasks:** T-FB-001 (edit 0012), T-FB-002 (edit 0006), T-FB-003 (edit AGENTS.md).
**Commit referência:** `faaddaa`.

---

## US-FB-002: Porta `AuthorizationProvider` em camada de domínio
**Como** arquiteto do sistema, **quero** o contrato `AuthorizationProvider` como Protocol Python em `src/domain/authz/`, sem dependência Django, **para** que adapters futuros (Casbin/OPA) possam ser plugados sem reescrever domínio (ADR-0012).

- **AC-FB-002-1**: Arquivo `src/domain/authz/provider.py` define Protocol `AuthorizationProvider` com método `can(usuario_id, action, resource, tenant_id, purpose, at_time) -> AuthDecision`.
- **AC-FB-002-2**: Dataclass `AuthDecision` imutável (`frozen=True`) com campos `allowed, reason, perfis_aplicados, escopo_avaliado, audit_id`.
- **AC-FB-002-3**: `src/domain/authz/__init__.py` exporta porta + dataclass.
- **AC-FB-002-4**: Zero import de `django.*` em `src/domain/authz/`.

**Tasks:** T-FB-004 (provider.py), T-FB-005 (`__init__.py`).
**Commit referência:** `9a7560d`.

---

## US-FB-003: Adapter Django + 3 tabelas authz com RLS + trigger imutabilidade
**Como** infra, **quero** `DjangoAuthorizationProvider` que implementa a porta consultando `Perfil`, `PerfilAcao`, `AuthzDecision` (com hash chain + trigger anti-mutation), **para** materializar INV-AUTHZ-001/002.

- **AC-FB-003-1**: Modelos `Perfil` (catálogo, codigo unique, tenant_id NULL = global), `PerfilAcao` (M:N perfil × ação), `AuthzDecision` (audit síncrono com hash chain).
- **AC-FB-003-2**: Migration `0002_rls_e_trigger` ativa RLS em `authz_perfil`, `authz_perfil_acao`, `authz_decisions` + trigger PG `authz_decisions_anti_update` + `authz_decisions_anti_delete`.
- **AC-FB-003-3**: `DjangoAuthorizationProvider.can()` grava `AuthzDecision` ANTES de retornar (mesma transação).
- **AC-FB-003-4**: Cache local Django (`LocMemCache`) com TTL 5min + invalidação manual via `invalidate_user_cache()`.

**Tasks:** T-FB-006 (models), T-FB-007 (migration 0001), T-FB-008 (migration 0002 RLS+trigger), T-FB-009 (adapter), T-FB-010 (admin + apps).
**Commit referência:** `9a7560d`.

---

## US-FB-004: Seed de 4 perfis + matriz inicial
**Como** orquestrador F-B, **quero** os 4 perfis seed (admin_tenant, tecnico, rt_signatario, cliente_externo_leitura) + matriz de ações iniciais persistidos via migration data, **para** ter base de testes E2E pronta.

- **AC-FB-004-1**: Migration `0003_seed_perfis` insere 4 perfis no `authz_perfil` (tenant_id NULL).
- **AC-FB-004-2**: 9 entradas em `authz_perfil_acao` cobrindo 4 ações (os.criar, os.ler, certificado.emitir, fatura.estornar).
- **AC-FB-004-3**: Migration usa `atomic=False` por causa de ALTER TABLE + INSERT com triggers pending.

**Tasks:** T-FB-011 (migration seed).
**Commit referência:** `259889f`.

---

## US-FB-005: DRF permission `RequireAuthz` deny-by-default + decoradores
**Como** sistema, **quero** que toda view DRF passe pelo provider antes de retornar, e que decorators `@public` + `@requires_authz` cubram views Django regulares, **para** materializar INV-AUTHZ-001 na borda.

- **AC-FB-005-1**: `RequireAuthz` em `DEFAULT_PERMISSION_CLASSES` no settings.
- **AC-FB-005-2**: View sem `authz_action` declarada retorna 403 com mensagem "View sem 'authz_action' declarada".
- **AC-FB-005-3**: View com `authz_public = True` ou `@public` decorator passa sem `can()`.
- **AC-FB-005-4**: Hook `authz-check.sh` rejeita endpoint novo sem `can()` em pre-commit.

**Tasks:** T-FB-012 (permissions.py), T-FB-013 (decorators.py), T-FB-014 (atualizar settings).
**Commit referência:** `9a7560d`.

---

## US-FB-006: `MfaRequiredMiddleware` força TOTP pros perfis sensíveis (SEC-MFA-001)
**Como** sistema, **quero** middleware que rejeite request de usuário com perfil sensível sem TOTP verificado, **para** atender SEC-MFA-001 (admin_tenant, rt_signatario, financeiro).

- **AC-FB-006-1**: Usuário com `mfa_obrigatorio=True` sem `is_verified()` recebe 401 `reason: "mfa_required_user"`.
- **AC-FB-006-2**: Usuário com algum perfil em `PERFIS_SENSIVEIS` ({admin_tenant, rt_signatario, financeiro}) sem TOTP recebe 401 `reason: "mfa_required_perfil_sensivel"`.
- **AC-FB-006-3**: Tecnico (não-sensível) sem TOTP passa.
- **AC-FB-006-4**: Paths `/healthz`, `/admin/login`, `/api/schema`, `/api/docs`, `/static/`, `/media/`, `/accounts/` bypassam o middleware.

**Tasks:** T-FB-015 (middleware.py), T-FB-016 (registrar em MIDDLEWARE settings).
**Commit referência:** `9a7560d`.

---

## US-FB-007: Suite de testes F-B (30 testes) + drill `validar_f_b`
**Como** orquestrador F-B, **quero** suite cobrindo INV-AUTHZ-001/002/003 + SEC-MFA-001 + fuzzing 500 cross-tenant + management command que rode 7 critérios automáveis, **para** validar fase em 1 comando.

- **AC-FB-007-1**: 16 cenários E2E (4 perfis × 4 ações × pos+neg) em `test_authz_e2e.py`.
- **AC-FB-007-2**: 5 cenários audit imutável em `test_authz_audit_imutavel.py` (commit-before-response allowed/denied, trigger PG anti-UPDATE/anti-DELETE, hash chain).
- **AC-FB-007-3**: 3 cenários isolamento em `test_authz_isolamento.py` (sem perfil, multi-tenant fora da lista, decisions isoladas).
- **AC-FB-007-4**: 5 cenários MFA em `test_authz_mfa.py`.
- **AC-FB-007-5**: Fuzzing 500 cross-tenant em `test_authz_fuzzing.py` — zero vazamento.
- **AC-FB-007-6**: `manage.py validar_f_b` retorna 7/7 [OK] (hooks, trigger, hash chain, fuzzing, E2E, RequireAuthz importável, MFA).

**Tasks:** T-FB-017 a T-FB-022.
**Commit referência:** `edd2ab2`, `164b5f0`.

---

## Auditoria retroativa

Auditores Família 5 rodados em 2026-05-18 sobre o código F-B. Output em `docs/governanca/trilha-auditoria-agentes.md`.

**Drill `validar_f_b` em 2026-05-18 (canônico):** 7/7 critérios automáveis verde. Suite F-B: 30 passed. Hooks 103/103.
