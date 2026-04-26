---
release: pre-v1
epic: SPEC-0100
date: 2026-04-26
auditors:
  - senior-reviewer
verdict: proposed
---

# Dossiê de release — Plano de remediação dos achados da auditoria estática 2026-04-26

## Escopo

Consolidação dos 35 findings da auditoria estática externa realizada em 2026-04-26 sobre o repositório Aferê, com mapeamento do estado pós-remediação (commits `01d56f3` a `daf81ea`) e definição de waves executáveis de fechamento.

## Evidência revisada

- `compliance/audits/code/2026-04-26-static-external-audit.md` — parecer original com 35 findings.
- `apps/api/src/config/env.ts` — confirma `COOKIE_SECRET` com default previsível (F-001 aberto).
- `apps/api/src/app.ts` — confirma fallback `DATABASE_URL` para owner/app (F-002 aberto).
- `apps/api/src/domain/auth/route-authorization.ts` — confirma hook apenas para métodos mutáveis (F-004/F-033 aberto).
- `apps/api/src/interfaces/http/offline-sync.ts` — `/sync/review-queue` sem autenticação (F-005 aberto).
- `apps/api/src/interfaces/http/customer-registry.ts` e `quality-hub.ts` — cenários sem proteção `ALLOW_SCENARIO_ROUTES` (F-006 parcial).
- `apps/api/src/interfaces/http/auth-session.ts` — bootstrap com `hasAnyOrganization`, sem flag `BOOTSTRAP_ENABLED` (F-008 parcial).
- `apps/api/.env.example` — ausência de variáveis críticas (F-017 aberto).
- `apps/api/package.json` — `@trpc/server` em RC (F-025 aberto).
- `apps/web/next.config.mjs` e `apps/portal/next.config.mjs` — sem headers de segurança (F-021 aberto).
- `apps/web/package.json` e `apps/portal/package.json` — sem script `test` (F-022 parcial).
- `infra/modules/*` — stubs de KMS, queue, storage, PDF/A (F-014/F-032 parcial).
- `apps/android/src/*.ts` — placeholder TypeScript, não Kotlin (F-016 aberto).

## Decisões arquiteturais vinculadas

- **ADR 0065** (`adr/0065-rls-runtime-role-readiness.md`) — base para F-002.
- **ADR 0067** (`adr/0067-appuser-email-identity-scope.md`) — contexto para F-003/F-010.
- **SPEC-0099** (`specs/0099-rls-runtime-role-readiness.md`) — implementação de `withTenant()` já mergeada.
- **SPEC-0100** (`specs/0100-audit-findings-remediation-plan.md`) — este plano.

## Status dos findings

- **Fechados:** F-011, F-018, F-024, F-028, F-030 (5)
- **Parciais:** F-006, F-008, F-009, F-014, F-022, F-032 (6)
- **Abertos:** F-001, F-002, F-003, F-004, F-005, F-007, F-010, F-012, F-013, F-015, F-016, F-017, F-019, F-020, F-021, F-023, F-025, F-026, F-029, F-031, F-033, F-034, F-035 (24)

## Waves de execução propostas

| Wave | Foco | Semana | Findings principais |
|------|------|--------|---------------------|
| 1 | P0 Segurança/Isolamento | 1-2 | F-001, F-002, F-003*, F-004, F-005, F-006, F-008, F-017, F-023 |
| 2 | P1 Endurecimento | 3-4 | F-003 (conclusão), F-007, F-009, F-010, F-014, F-021, F-022, F-025, F-026, F-029, F-032 |
| 3 | P2 Arquitetura/Qualidade | 5 | F-012, F-013, F-019, F-020, F-031, F-035 |
| 4 | P3 Longo prazo | 6+ | F-015, F-016, F-027, F-034 |

*F-003 inicia na Wave 1 (hook auth estável) e conclui na Wave 2 (TOTP implementado).

## Riscos assumidos

- Wave 1 pode quebrar `check:all` se `COOKIE_SECRET` ou `DATABASE_APP_URL` forem exigidos em `test` sem atualizar CI; mitigar com variáveis no workflow.
- Wave 2 MFA pode atrasar; mitigar com flag de feature toggle.
- Wave 4 Android depende de decisão de produto (Kotlin real vs ajuste documental).

## Próximos passos

1. Aprovar SPEC-0100 em revisão por `senior-reviewer`.
2. Criar branch `feat/SPEC-0100-wave1` e iniciar F-001 + F-002 + F-017.
3. Executar `pnpm check:all` a cada tarefa; nunca empurrar vermelho.
4. Arquivar evidência de cada wave em `compliance/validation-dossier/evidence/SPEC-0100-wave<N>/`.
5. Ao final da Wave 2, solicitar parecer L5 de `metrology-auditor` e `legal-counsel` se houver mudança em emissão ou LGPD.

---

*Registro gerado em 2026-04-26 conforme harness de validação contínua.*
