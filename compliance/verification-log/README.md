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
  ac_changed: true
  reqs_changed: false
  propagated_up:
    - L1/REQ-PRD-13-03-CERTIFICATE-MEASUREMENT-DECLARATIONS
  propagated_down:
    - L4/full-regression
  re_audits_completed:
    - L4: 2026-04-23 via pnpm check:all
```

Copiar a base canônica de `compliance/verification-log/_template.yaml` ao abrir um novo registro.

## Comandos

```bash
pnpm verification-cascade:check
pnpm verification-cascade:plan -- --changed packages/audit-log/src/verify.ts
pnpm verification-cascade:issue-drafts -- --write
pnpm exec tsx tools/verification-cascade.ts release-audits --release v1.0.0
```

O comando `plan` não substitui revisão humana: ele explicita os gates automáticos mínimos para o delta.

## Issues automáticas

Quando um finding de cascata é elegível para issue automática, o draft canônico é renderizado em `compliance/verification-log/issues/drafts/`.

- `compliance/verification-log/issues/_template.md` define o formato do corpo.
- `pnpm verification-cascade:issue-drafts -- --write` grava os drafts locais.
- O workflow `required-gates` usa o JSON desses drafts para abrir issue real no GitHub quando o token do Actions tem permissão.

O fluxo atual cobre:

- `CASCADE-003` para `snapshot-diff`;
- `CASCADE-007` para `spec-review-flag`, quando 3 correções consecutivas na mesma spec alteram AC/REQ sem evidência de re-auditoria L1.
- `CASCADE-008` para `epic-review-flag`, quando 3 correções consecutivas em múltiplas specs do mesmo épico alteram AC/REQ sem evidência de re-auditoria L0.

No `push` para `main`, o workflow `required-gates` também reconcilia as issues gerenciadas: reabre quando o finding volta e fecha quando o finding deixa de existir em `main`.

Outros gatilhos de propagação podem ampliar essa automação sem mudar o contrato do diretório.
