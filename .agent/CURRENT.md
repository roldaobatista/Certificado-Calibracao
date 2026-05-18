# .agent/CURRENT.md

> ≤40 linhas. Atualizado a cada fechamento de Foundation/Wave.

**Fase:** **Foundation F-B FECHADA (verde, 2026-05-18)** — aguardando autorização Roldão pra arrancar Wave A
**Modo:** AUTÔNOMO durante F-A + F-B. Wave A requer autorização explícita.

**F-B — resultado final:**
- ✅ ADRs 0012 + 0006 promovidas proposta → **aceita**
- ✅ App `authz` criado: porta `AuthorizationProvider` (domain) + adapter Django + 3 tabelas + 4 perfis seed
- ✅ `RequireAuthz` DRF permission deny-by-default + decorator `@public` + `@requires_authz`
- ✅ `MfaRequiredMiddleware` (SEC-MFA-001) força TOTP pros perfis sensíveis
- ✅ INV-AUTHZ-001/002/003 cravadas e testadas
- ✅ Drill 7/7 critérios automáveis verde
- ✅ 88 passed, 1 skipped (58 F-A + 30 F-B: 16 E2E + 5 audit + 3 isolamento + 5 MFA + 1 fuzzing 500)
- ✅ Hooks 103/103 verdes

**Ajustes na aceitação ADR-0012:**
- django-allauth diferido pra Wave A (Django auth nativo + django-otp atendem)
- Cache em `LocMemCache` em F-B; Redis em Wave A (sem mexer no domain)
- 4 perfis seed em F-B; os 12 restantes destravam por módulo na Wave A

**Estado do sistema agora:**
- Containers `afere-db` e `afere-app` rodando
- Banco `afere` com schema authz; `test_afere` recriado com grants + extensões
- 9 entradas matriz `authz_perfil_acao` seed; 0 decisões em `authz_decisions` (banco virgem pós-drill)
- Pra parar tudo: `docker compose down`

**Próximo passo lógico (PENDE autorização Roldão):**
Wave A — MVP-1 com 18 módulos (faseamento §4). Pré-requisitos:
- F-A + F-B verdes ✅
- 18 PRDs Wave A em `stable` (escrever)
- 6 ADRs em proposta precisam ser aceitas (0003, 0004, 0008, 0009, 0010, 0014, 0015, 0016)
- 3 hooks complementares já existem ✅

**Bloqueio:** Wave A requer aprovação manual do Roldão (gate de fase).
