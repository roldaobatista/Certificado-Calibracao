# compliance/verification-log/ — Propagação L0-L5

**Owner:** `qa-acceptance` + `product-governance`.

Este diretório registra propagações bidirecionais da cascata de verificação definida em `harness/14-verification-cascade.md`.

## Quando registrar

Criar ou atualizar `compliance/verification-log/<REQ-id>.yaml` quando:

- correção L3 muda AC ou requisito e reabre L1;
- múltiplas specs do mesmo épico mostram o mesmo defeito e reabrem L0;
- mudança em L0, L1 ou L2 exige re-auditoria abaixo;
- uma mudança em área crítica exige full regression L4;
- release L5 depende de pareceres dos três auditores externos.

## Formato esperado

```yaml
- date: 2026-04-22
  trigger: L3 bug in emission flow
  propagated_up:
    - L1/REQ-PRD-13-03-CERTIFICATE-MEASUREMENT-DECLARATIONS
  propagated_down:
    - L4/full-regression
  re_audits_completed:
    - L4: 2026-04-23 via pnpm check:all
```

## Comandos

```bash
pnpm verification-cascade:check
pnpm verification-cascade:plan -- --changed packages/audit-log/src/verify.ts
pnpm exec tsx tools/verification-cascade.ts release-audits --release v1.0.0
```

O comando `plan` não substitui revisão humana: ele explicita os gates automáticos mínimos para o delta.
