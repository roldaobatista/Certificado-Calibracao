---
owner: roldao
revisado_em: 2026-05-19
proximo_review: 2026-08-19
status: stable
diataxis: reference
audiencia: agente
fase: Foundation F-B
tipo: matriz-reconciliacao-spec-codigo
relacionados:
  - docs/faseamento/F-B/spec.md
  - docs/faseamento/F-B/plan.md
---

# Foundation F-B — Reconciliação spec ↔ código (P8)

> Mede a `spec.md` F-B (corrigida pós-review) contra o código real.
> `OK` (satisfaz — evidência), `GAP`→`T-FB-NNN` (conserto causa-raiz),
> `TRACK` (gate Wave A). Base do `OK`: frentes desta sessão
> (`32aa278`/`53e3cc2`/`7924390`) + leitura direta + Família 5 F-A.

## Matriz

| AC | Estado | Evidência / ação |
|----|--------|------------------|
| AC-FB-001-1..3 | OK | `src/domain/authz/provider.py` Protocol puro, AuthDecision frozen, zero django |
| AC-FB-001-4 | OK | assinatura `can()` inalterada (BLOQ-3 governa ip_hash via contexto) |
| AC-FB-002-1..5 | OK | models + RLS + trigger + cache LocMem; migrations 0001..0005 from-scratch (verificado nesta sessão) |
| AC-FB-003-1..5 | OK | FB-C1+C3 `32aa278` — helper único, pré-tenant por-usuário, policy fonte única, `_normalizar_para_hash`, T-FA-01 herdado |
| AC-FB-004-1..3 | OK | seed 0003; SANEA-04 respeitado |
| AC-FB-005-1..2 | OK | RequireAuthz em DEFAULT_PERMISSION_CLASSES, deny-by-default |
| AC-FB-005-3..5 | OK | FB-C2 `53e3cc2` — `is_public` fonte única + hook + `test_authz_require_authz.py` (cobre FB-A7) |
| **AC-FB-006-2** | **GAP** | **T-FB-01**: `register_predicate(nome,fn)` sem escopo; `_decidir` roda todos os predicates ignorando action (FB-A1) |
| **AC-FB-006-3** | **GAP** | **T-FB-02**: 3 cópias de vigência; `_tem_perfil_sensivel` (middleware:98) só `valido_de__lte`, ignora `valido_ate`; dup `models_q_valido_ate_ok` em django_provider:406 |
| AC-FB-007-1..2 | OK | MfaRequiredMiddleware 401 mfa_required_* (rodada 1 verde) |
| **AC-FB-007-3** | **GAP** | **T-FB-02** (mesma raiz — janela completa única) |
| AC-FB-007-4..5 | OK | técnico passa; paths públicos bypass |
| **AC-FB-007-6** | **GAP** | **T-FB-03**: testes MFA usam stub `_FakeUserMFAOff`, não `django-otp is_verified()` real (FB-A6 / TST-003) |
| **AC-FB-008-1** | **GAP** | **T-FB-04**: `ip_hash` 100% vazio (FB-A5); precisa HMAC via contextvar, no payload E coluna |
| AC-FB-008-2 | OK | tasks sem request → ip_hash vazio (documentado) |
| **AC-FB-008-3** | **GAP** | **T-FB-05**: `resource`/`escopo_avaliado` sem allowlist — só docstring "sem PII cru" (C-A2.1) |
| AC-FB-009-1 | OK | `test_authz_e2e.py` 16 cenários |
| AC-FB-009-2 | OK | FB-C4+C5 `7924390` — verificar_integridade_cadeia_authz + test_adulteracao_no_meio |
| AC-FB-009-3 | OK | `validar_f_b` robusto: SEEDA partições conhecidas (3 tenants + pré-tenant ua/ub) e verifica o que semeou — controlado, não falso-verde por omissão (P8-verify BAIXO-1 resolvido) |
| AC-FB-009-4 | OK | fuzzing {A,B}→C bloqueado (rodada 1) |
| **AC-FB-009-5** | **GAP** | **T-FB-06**: não existe teste de atomicidade/rollback-órfão (BLOQ-4) |
| §3 critério 7 | OK | herdado AC-FA-008-6 (`test_t_fa_06` anti-falso-verde) |

### Gates Wave A (TRACK — não bloqueiam F-B)

| Gate | Item |
|------|------|
| GATE-1..7 | herdados de F-A (B2/WORM cobre authz; ADR-0020; NTP; pattern ::uuid) |
| GATE-FB-1 | 1º perfil tenant-specific → regenerar `authz_perfil_acao_select` (INV-AUTHZ-004) |
| GATE-FB-2 | retenção `authz_decisions`+`ip_hash` na matriz tríplice + RAT (advogado) |
| GATE-FB-3 | redator PII se `resource` exceder id/ref em Wave A |
| GATE-FB-4 | alinhar texto INV-AUTHZ-002 em REGRAS (vedar PII por valor) — junto de ADR-0020 (CODEOWNERS) |

## Tarefas de conserto (P8) — causa-raiz

| T-FB | AC | Conserto (raiz) | Bloqueia F-B? |
|------|----|-----------------|---------------|
| **T-FB-01** | AC-FB-006-2 | `register_predicate(nome, fn, *, actions, resource_prefix)`; sem escopo → erro import-time; `_decidir` só avalia predicates aplicáveis; action sem predicate → ABAC neutro (NÃO deny). Testes: predicate fora de escopo não roda; sem-escopo→erro registro | Sim |
| **T-FB-02** | AC-FB-006-3 / 007-3 | módulo único `usuario/vigencia.py` `janela_vigente_ok(agora)` (`valido_de` E `valido_ate`); consumido por `_resolver_perfis_vigentes`, `_tem_perfil_sensivel`, middleware; **remove** dup `models_q_valido_ate_ok` (django_provider + middleware). Teste: perfil sensível expirado → middleware deixa passar | Sim |
| **T-FB-03** | AC-FB-007-6 | teste com `TOTPDevice` real `django-otp` (confirmado/não) + `OTPMiddleware`/sessão; remove stub `_FakeUserMFAOff` dos casos de integração | Sim |
| **T-FB-04** | AC-FB-008-1 | `ip_hash_context` contextvar; `RequireAuthz` extrai IP → HMAC-SHA256 (chave família PII F-A) → set contextvar; `_gravar_audit` lê → `_payload_para_hash` **e** coluna. Teste: ip_hash preenchido + entra no hash (round-trip íntegro) + sem request → vazio | Sim |
| **T-FB-05** | AC-FB-008-3 | `_normalizar_para_hash` (ou guarda dedicada) aplica **allowlist de chaves** em `resource`/`escopo_avaliado`; chave fora → fail-loud. Teste: chave de PII livre → erro claro antes da transação | Sim |
| **T-FB-06** | AC-FB-009-5 | teste rollback-órfão: `transaction.atomic()` → `can()` → `set_rollback(True)`/raise → nova transação confirma `AuthzDecision` ausente; e caso commit → presente | Sim |

FB-A7 (AC-FB-005-5) já fechado em FB-C2 — confirmado OK na matriz.
6 T-FB causa-raiz; GATE-FB-* rastreados. Nenhum reabre arquitetura.

## Desfecho P8 (2026-05-19) — 6/6 T-FB FECHADOS causa-raiz

| T-FB | Desfecho | Prova |
|------|----------|-------|
| T-FB-01 | ✅ | `register_predicate` exige escopo (erro import-time); `_decidir`→`predicates_aplicaveis(action)`; ação sem predicate=ABAC neutro. Testes binding |
| T-FB-02 | ✅ | `usuario/vigencia.py` fonte ÚNICA (janela completa); 3 cópias removidas; perfil sensível expirado não barra MFA. Testes |
| T-FB-03 | ✅ | testes `django-otp` REAL (`TOTPDevice`+`OTPMiddleware`+`otp_login`) — mata o stub `_FakeUserMFAOff` (FB-A6) |
| T-FB-04 | ✅ | `ip_hash` HMAC versionado via `ip_hash_context` (token+reset no middleware, não param de can()); no payload E coluna (round-trip íntegro); coluna→TextField (migration 0006). Testes |
| T-FB-05 | ✅ | `_validar_resource_sem_pii` allowlist de topo (imposta por código); `cpf`/`nome`→fail-loud antes da transação. Testes |
| T-FB-06 | ✅ | teste rollback-órfão (atomicidade real — não "commit antes do retorno"); + caso commit persiste |
| FB-A7 | ✅ | já fechado FB-C2 (`test_authz_require_authz.py`) — confirmado |

**Suite 293 passed; hooks 118/118; makemigrations limpo; drill
`validar_f_b` 7/7 VERDE** (cadeia robusta por-tenant + pré-tenant
por-usuário, adulteração detectada, 40 inserts concorrentes íntegros).
GATE-FB-2/3/4 + GATE-1..7 rastreados (não bloqueiam F-B dogfooding).

> **Próximo:** P9 (3 auditores Família 5, loop até zero crítico/alto)
> → **fechar Foundation** (F-A + F-B).
