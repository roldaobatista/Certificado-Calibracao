# .agent/CURRENT.md

> ≤40 linhas. Histórico expandido em `docs/faseamento/diario/`.

**Fase:** F-A+F-B + Marco 1 + Marco 2 + Marco 3 P4 Fase 4 fechados · **F-C1 P4 COMPLETA (Blocos 1..6 + catch-up)** (2026-05-24).
**Modo:** AUTÔNOMO.

## Estado da suíte (verificado 2026-05-24 pós Bloco 6 + fix test-infra)

- Hooks `_test-runner.sh`: **288/288** verdes (+8 FR1..FR8 do hook frontmatter-revisado-em-check).
- ruff: All checks passed em `src/infrastructure/audit/management/commands/validar_f_c1.py`.
- `validar_f_c1`: **10/10 PASS** em DB dev (com `--rapido` 9/9; sem flag 10/10).
- makemigrations --check: limpo após Blocos 4-6 + catch-up.
- **Pytest test_afere DESTRAVADO + 100% VERDE** (905/0/0) em 5 saltos:
  - Antes: 0 testes válidos (`relation tenants não existe`).
  - Salto 1 (6c5b795) — router fix + btree_gist init: 706 passed / 198 failed / 599 errors.
  - Salto 2 (revertido) — tentativa MIRROR fez pytest escrever em DEV; DEV recriado limpo.
  - Salto 3 (9c86767) — test_afere OWNER=app_user + descartável-check via psycopg: 708 / 197 / 0.
  - Salto 4 (14d2325, Task #9) — conftest restaura seeds via importlib das 21 migrations seed após cada TransactionTestCase: **902 / 3 / 0**.
  - Salto 5 (8688a7e, Task #10) — 3 fails restantes: testes RAISE-on-empty-table (auditoria vazia, policy USING não avaliada) + clear_registry contaminando registry de predicates: **905 / 0 / 0** verde 100%.

## F-C1 P4 — entregue (2026-05-24)

- Bloco 1 (T-FC1-01..03 settings prod) — commit ca25a47 (prévio).
- Bloco 2 (T-FC1-04..07 AdminHardeningMiddleware + admin_access + hook) — commit e7c64bc (prévio).
- Bloco 3 (T-FC1-08..11 webhook_out + SSRF + HMAC + DPA) — commits 7920fb8 + 3747341 (prévios).
- Bloco 4 (T-FC1-12 rotação dogfooding) — commit 3f5be6b. Procedimento canônico 5 chaves + drill aceitação arquivado. GATE-FC1-ROTACAO-DRILL-REAL aguarda execução real Roldão.
- Bloco 5 (T-FC1-13 break-glass) — commit f43faaa. INV-ADMIN-003 + Usuario.is_break_glass + criar_admin_recovery + runbook §11.bis. Wave A: U2F WebAuthn.
- Bloco 6 (T-FC1-14 drill validar_f_c1) — commit 33bf243. 10 drills end-to-end.
- Bônus: fix hook frontmatter-revisado-em (commit d19ad60) + drift spec admin_ops→audit (d6f3dbe) + catch-up migrations + insumo (5c8c421).

## Próximo passo

**P5 F-C1 — 10 auditores Família 5 em paralelo** (`docs/faseamento/F-C1/auditoria-familia5.md`). Critério: ZERO C/A/M (INV-RITUAL-001). Suite 905/0/0 verde + drill `validar_f_c1` 10/10 PASS + hooks 288/288 verdes = todos os pré-requisitos atendidos.

## Marcos anteriores fechados

- **F-A + F-B** — ritual Spec Kit completo. `docs/faseamento/{F-A,F-B}/auditoria-familia5.md`.
- **M1 `clientes`** — P5 10 auditores ZERO C/A/M. ADR-0021.
- **M2 `equipamentos`** — 65 T-EQP, P5 2ª passada ZERO C/A/M. CVE-2025-68616 WeasyPrint mitigado.
- **M3 OS** — P1+P2+P3 + P4 FASES 1-4 fechadas. P4 Fase 5 (Services + use cases — 15 US, T-OS-040..084 ~45 tarefas) é o próximo passo dessa frente (depois de F-C1 fechar).

## Pendências rastreadas

- 51+9 GATEs Wave A consolidados (`gates-wave-a-consolidado.md`).
- T-OS-040..147 restantes em `docs/faseamento/M3-os/tasks.md` (8 fases).
- Task #8 investigação pytest.
