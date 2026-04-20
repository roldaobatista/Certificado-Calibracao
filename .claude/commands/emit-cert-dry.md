---
description: Planeja dry-run de emissão de certificado e falha fechado enquanto o pipeline real não existir
owner: backend-api
risk_level: blocker
required_commands: ["pnpm verification-cascade:plan -- --changed apps/api/src/domain/emission/dry-run.ts", "pnpm test:tools"]
---

# /emit-cert-dry

## Objetivo

Preparar a simulação de emissão por perfil A/B/C sem persistência, assinatura real ou QR, mantendo fail-closed até o pipeline de emissão existir.

## Execução

```bash
pnpm verification-cascade:plan -- --changed apps/api/src/domain/emission/dry-run.ts
pnpm test:tools
```

Quando o dry-run real for implementado em V1+, substituir a segunda linha pelo CLI de emissão em modo `--dry-run --profile $ARGUMENTS` e manter o plano L4.

## Evidência

- Registrar plano de verificação gerado pela cascata.
- Registrar que o dry-run real está indisponível quando não houver endpoint/CLI de emissão.
- Quando existir implementação, arquivar saída e artefatos em `compliance/validation-dossier/evidence/`.

## Escalonamento

- Tentativa de emissão real fora do pipeline assinado bloqueia release.
- Divergência de norma escala para `regulator`.
- Divergência de incerteza escala para `metrology-calc`.
- Divergência de template ou PDF escala para `web-ui` e `qa-acceptance`.

## Referências

- `harness/05-guardrails.md`
- `harness/14-verification-cascade.md`
- `PRD.md` §7.8, §7.9, §13
