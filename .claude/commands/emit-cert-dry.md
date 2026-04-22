---
description: Executa dry-run de emissao de certificado por perfil regulatorio e prepara a cascata L4
owner: backend-api
risk_level: blocker
required_commands: ["pnpm verification-cascade:plan -- --changed apps/api/src/domain/emission/dry-run.ts", "pnpm emit-cert-dry -- --profile B", "pnpm test:tools"]
---

# /emit-cert-dry

## Objetivo

Executar um dry-run regulatório de emissão por perfil A/B/C sem persistência, PDF/A ou assinatura real, consolidando os gates de V1 em um único relatório operacional.

## Execução

```bash
pnpm verification-cascade:plan -- --changed apps/api/src/domain/emission/dry-run.ts
pnpm emit-cert-dry -- --profile ${ARGUMENTS:-B}
pnpm test:tools
```

Para inspecionar todos os detalhes em automação, usar `pnpm emit-cert-dry -- --profile ${ARGUMENTS:-B} --json`.

## Evidência

- Registrar plano de verificação gerado pela cascata.
- Registrar a saída textual ou JSON do dry-run com o perfil executado.
- Arquivar a saída em `compliance/validation-dossier/evidence/` quando o dry-run fizer parte de release ou dossiê formal.

## Escalonamento

- Tentativa de emissão real fora do pipeline assinado bloqueia release.
- Divergência de norma escala para `regulator`.
- Divergência de incerteza escala para `metrology-calc`.
- Divergência de template ou PDF escala para `web-ui` e `qa-acceptance`.

## Referências

- `harness/05-guardrails.md`
- `harness/14-verification-cascade.md`
- `PRD.md` §7.8, §7.9, §13
