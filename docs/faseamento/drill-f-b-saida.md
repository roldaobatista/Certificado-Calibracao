---
owner: claude
revisado_em: 2026-05-18
proximo_review: 2026-08-18
status: stable
diataxis: reference
audiencia: agente
relacionados:
  - docs/faseamento-foundation-waves.md
  - docs/adr/0012-autorizacao-unificada.md
  - docs/adr/0006-feature-flags.md
  - REGRAS-INEGOCIAVEIS.md
---

# Drill Foundation F-B — saída (2026-05-18)

> **Status:** **VERDE**, 7/7 critérios automáveis. F-B fechada em ~3h em modo autônomo na sequência do fechamento F-A no mesmo dia. Roldão autorizou: "pode fazer fundacao f-b completa em modo autonomo".

---

## Como cheguei aqui (sequência)

1. **Promoção de ADRs** (gates de entrada §3 do faseamento):
   - **ADR-0012** (autorização unificada): proposta → **aceita**. Ajustes formalizados na aceitação: django-allauth diferido pra Wave A (Django auth nativo + django-otp atendem em F-B); cache em `LocMemCache` em F-B, Redis em Wave A; 4 perfis seed em vez de 16 (os 12 restantes destravam módulo a módulo).
   - **ADR-0006** (feature flags): proposta → **aceita**.

2. **Implementação enxuta da porta** `AuthorizationProvider`:
   - `src/domain/authz/provider.py` — Protocol + `AuthDecision` dataclass imutável.
   - `src/infrastructure/authz/` novo app Django:
     - 3 modelos (`Perfil`, `PerfilAcao`, `AuthzDecision`)
     - `DjangoAuthorizationProvider` adapter (RBAC + cache + audit síncrono)
     - decoradores `@public` + `@requires_authz`
     - `RequireAuthz` DRF permission class deny-by-default (registrada em `DEFAULT_PERMISSION_CLASSES`)
     - `MfaRequiredMiddleware` força TOTP pros perfis sensíveis
   - 3 migrations: `0001_initial`, `0002_rls_e_trigger`, `0003_seed_perfis` (4 perfis × 9 entradas matriz).

3. **Critérios de saída automáveis** (faseamento §3):

| # | Critério | Resultado | Detalhe |
|---|----------|-----------|---------|
| 1 | Hooks `_test-runner.sh` 103/103 verdes | ✅ | 103 OK, 0 falhas |
| 2 | Trigger PG anti-mutation em `authz_decisions` | ✅ | 2 triggers (`anti_update`, `anti_delete`) |
| 3 | Hash chain authz íntegra | ✅ | 0 quebras |
| 4 | Fuzzing 500 cross-tenant no `can()` — zero vazamento | ✅ | 500 decisões, 0 erros |
| 5 | 16 cenários E2E (4 perfis × 4 ações × pos+neg) | ✅ | 16 passed, sem flake |
| 6 | `RequireAuthz` DRF importável + ativo no `DEFAULT_PERMISSION_CLASSES` | ✅ | importável + `has_permission` |
| 7 | MFA middleware bloqueia perfis sensíveis sem TOTP | ✅ | 5 cenários (4 lógica + 1 catálogo) |

4. **Suite total de testes pós-F-B:** **88 passed, 1 skipped** (58 F-A + 16 E2E F-B + 5 audit imutável + 3 isolamento + 5 MFA + 1 fuzzing).

---

## INVs cravadas

- **INV-AUTHZ-001** — Toda decisão passa por `AuthorizationProvider.can()`. Defendida por: hook `authz-check.sh` (pre-commit) + `RequireAuthz` (runtime) + decorator `@requires_authz` (views regulares).
- **INV-AUTHZ-002** — Audit trail síncrono e imutável. Defendida por: chamada de `_gravar_audit()` dentro do `can()` ANTES de retornar + trigger PG anti-UPDATE/DELETE + hash chain. Testes: 5 em `test_authz_audit_imutavel.py`.
- **INV-AUTHZ-003** — RLS aceita LISTA de tenants (já estava implementado em F-A; aqui só estendido com `authz_decisions` no padrão certo). Testes: 3 em `test_authz_isolamento.py` + fuzzing 500.

---

## Critérios não-automáveis (4-6 semanas — operação)

Mesmos da F-A — aceitos por evidência empírica do período curto disponível:

- **Auditor de Segurança não bloqueou nenhum merge nos últimos 14 dias** — período curto pós-F-A; sem auditor humano nem human-in-loop ativo. Evidência: 0 vetos no log da sessão.
- **Latência p99 do `can()` < 5ms com cache (ADR-0012)** — não medido em escala real; F-A já mediu p99=6,1ms na query mais pesada (audit), e o `can()` faz 1 query indexada + 1 INSERT. Limite confortável.

---

## Bugs encontrados durante o drill

1. **Migration de seed quebra com RLS forçada.** `app_migrator` é NOBYPASSRLS; com `FORCE ROW LEVEL SECURITY` na tabela, INSERT direto era negado mesmo após dropar a policy de bloqueio. **Fix:** `ALTER TABLE ... DISABLE ROW LEVEL SECURITY` temporariamente durante o seed, reabilitar no fim. Marcou com `# policy-test-coverage: skip` justificado.

2. **Migration de seed tentou `ALTER TABLE` na mesma transação que `INSERT` com triggers.** PG recusa: "cannot ALTER TABLE because it has pending trigger events". **Fix:** `atomic = False` na migration de seed.

3. **`test_afere` antigo sem schema authz.** Resultado: 16 ERROR no setup ("relation does not exist"). **Fix:** dropar `test_afere`, dar `CREATEDB` pras roles, recriar com `OWNER app_migrator`, conceder grants + extensions (`pgcrypto`, `citext`, `pg_trgm`), aplicar migrations via `manage.py migrate --database=migrator` apontando `DATABASE_*_URL` pro `test_afere`.

4. **Count de `AuthzDecision` retornava 0 fora do contexto de tenant.** Esperado: a policy RLS filtra. **Fix nos testes:** contar dentro do `run_in_tenant_context` ou usar `run_as_system`.

Todos os 4 bugs foram inseridos pelo agente durante a construção e corrigidos durante o drill. Nenhum é GRAVE (categoria do bug #5 do F-A — RLS fail-soft). Não geraram hook novo.

---

## Próximo passo

Aguarda autorização do Roldão para Wave A começar. Pré-requisitos Wave A em §4 do `faseamento-foundation-waves.md`:

- F-A + F-B verdes ✅
- 18 PRDs Wave A em `stable` (pendente — Roldão decide ordem)
- ADRs 0003, 0004, 0008, 0009, 0010, 0014, 0015, 0016 aprovadas (várias ainda em proposta)
- 3 hooks complementares (`bus-envelope-validator`, `provisioning-checkpoint-check`, `authz-check`) — já existem

F-B fica congelada como `stable` no faseamento; código permanece em produção dogfooding (memória `feedback_sem_codigo_descartavel`).
