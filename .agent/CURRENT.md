# .agent/CURRENT.md

> ≤40 linhas. Atualizado a cada conclusão de Marco F-A.

**Fase:** **Foundation F-A FECHADA (verde, 2026-05-18)** — aguardando autorização Roldão pra arrancar F-B
**Modo:** AUTÔNOMO durante F-A. F-B requer autorização explícita Roldão.

**F-A — resultado final:**
- ✅ 8 marcos entregues (gate + esqueleto + 4 tabelas + multi-tenancy + audit + 2 hooks + suite + convenções + drill)
- ✅ Drill 5/5 critérios automáveis verde (hooks 103/103, NOBYPASSRLS, trigger, hash chain, p99=6,1ms)
- ✅ Fuzzing 50 threads × 100 queries → **ZERO vazamento cross-tenant**
- ✅ Restore PG cronometrado: **2,52s** (limite 30min, folga 700x)
- ✅ Critério operacional aceito por evidência empírica (0 intervenções Roldão, 0 SEV-1, 0 vetos auditor, gasto LLM TBD-OK)
- ✅ 8 bugs encontrados pelo drill — todos corrigidos no mesmo dia + 3 medidas de prevenção aplicadas (hooks pyproject-validator + policy-test-coverage + memória durável)

**ADRs atualizadas no fechamento:**
- ADR-0001 (stack Django+Flutter+PostgreSQL): candidata → **aceita**
- ADR-0002 (multi-tenancy v2): aceita (desde 17/05)
- ADR-0007 (camada domínio + gerador): aceita (desde 17/05)
- `docs/faseamento-foundation-waves.md`: status draft → **stable**, §11 histórico atualizado

**Próximo passo lógico (PENDE autorização Roldão):**
Foundation F-B — autenticação + RBAC + AuthorizationProvider + MFA TOTP. Janela 2-3 semanas. Pré-requisitos:
- ADR-0012 (autorização unificada) ainda em proposta → precisa ser aceita
- ADR-0006 (feature flags) em proposta → consistente com ADR-0015 INV-INT-008
- 16 cenários E2E (4 perfis × 4 ações × positivo+negativo)
- django-allauth + django-otp integrados
- AuthorizationProvider porta + adapter local

**Estado do sistema agora:**
- Containers `afere-db` e `afere-app` continuam rodando no Docker do PC
- Banco `afere` populado com 12k linhas auditoria (drill)
- Banco `test_afere` com migrations aplicadas (pra pytest)
- Pra parar tudo: `docker compose down`

**Bloqueio:** F-B requer aprovação manual do Roldão (gate de fase).
