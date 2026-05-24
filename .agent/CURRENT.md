# .agent/CURRENT.md

> ≤40 linhas. Histórico expandido em `docs/faseamento/diario/`.

**Fase:** F-A+F-B + Marco 1 + Marco 2 + Marco 3 P4 Fase 4 fechados · **F-C1 P4 COMPLETA (Blocos 1..6 + catch-up)** (2026-05-24).
**Modo:** AUTÔNOMO.

## Estado da suíte (verificado 2026-05-24 pós Bloco 6 + fix test-infra)

- Hooks `_test-runner.sh`: **288/288** verdes (+8 FR1..FR8 do hook frontmatter-revisado-em-check).
- ruff: All checks passed em `src/infrastructure/audit/management/commands/validar_f_c1.py`.
- `validar_f_c1`: **10/10 PASS** em DB dev (com `--rapido` 9/9; sem flag 10/10).
- makemigrations --check: limpo após Blocos 4-6 + catch-up.
- **Pytest test_afere DESTRAVADO** em 3 saltos (commits 6c5b795 → 9c86767):
  - Antes: 0 testes válidos (`relation tenants não existe`).
  - Salto 1 — router fix + btree_gist init: 706 passed / 198 failed / 599 errors.
  - Salto 2 (tentativa MIRROR): **DESASTRE** — pytest escreveu em DEV `afere` (733 tenants vazaram). DEV recriado limpo via DROP + migrate.
  - Salto 3 — test_afere OWNER=app_user + descartável-check via psycopg: **708 passed / 197 failed / 0 errors**.
  - **197 fails restantes**: TRUNCATE em TransactionTestCase limpa seeds (authz_perfil, tipo_atividade_config) entre tests; seed via RunPython da migration só roda 1x. → Task #9.
  - **Bloqueia P5 `auditor-qualidade`** até Task #9 resolver.

## F-C1 P4 — entregue (2026-05-24)

- Bloco 1 (T-FC1-01..03 settings prod) — commit ca25a47 (prévio).
- Bloco 2 (T-FC1-04..07 AdminHardeningMiddleware + admin_access + hook) — commit e7c64bc (prévio).
- Bloco 3 (T-FC1-08..11 webhook_out + SSRF + HMAC + DPA) — commits 7920fb8 + 3747341 (prévios).
- Bloco 4 (T-FC1-12 rotação dogfooding) — commit 3f5be6b. Procedimento canônico 5 chaves + drill aceitação arquivado. GATE-FC1-ROTACAO-DRILL-REAL aguarda execução real Roldão.
- Bloco 5 (T-FC1-13 break-glass) — commit f43faaa. INV-ADMIN-003 + Usuario.is_break_glass + criar_admin_recovery + runbook §11.bis. Wave A: U2F WebAuthn.
- Bloco 6 (T-FC1-14 drill validar_f_c1) — commit 33bf243. 10 drills end-to-end.
- Bônus: fix hook frontmatter-revisado-em (commit d19ad60) + drift spec admin_ops→audit (d6f3dbe) + catch-up migrations + insumo (5c8c421).

## Próximo passo

**Task #9** — resolver TRUNCATE+seed (197 fails). Recomendado: autouse fixture function-scope que detecta authz_perfil vazio e dispara `call_command('migrate', 'authz', '0003', fake=False)` OU re-roda seeds inline. **Bloqueia P5 F-C1** (auditor-qualidade exige suite verde).

**Depois disso: P5 F-C1 — 10 auditores Família 5 em paralelo** (`docs/faseamento/F-C1/auditoria-familia5.md`). Critério: ZERO C/A/M (INV-RITUAL-001).

## Marcos anteriores fechados

- **F-A + F-B** — ritual Spec Kit completo. `docs/faseamento/{F-A,F-B}/auditoria-familia5.md`.
- **M1 `clientes`** — P5 10 auditores ZERO C/A/M. ADR-0021.
- **M2 `equipamentos`** — 65 T-EQP, P5 2ª passada ZERO C/A/M. CVE-2025-68616 WeasyPrint mitigado.
- **M3 OS** — P1+P2+P3 + P4 FASES 1-4 fechadas. P4 Fase 5 (Services + use cases — 15 US, T-OS-040..084 ~45 tarefas) é o próximo passo dessa frente (depois de F-C1 fechar).

## Pendências rastreadas

- 51+9 GATEs Wave A consolidados (`gates-wave-a-consolidado.md`).
- T-OS-040..147 restantes em `docs/faseamento/M3-os/tasks.md` (8 fases).
- Task #8 investigação pytest.
