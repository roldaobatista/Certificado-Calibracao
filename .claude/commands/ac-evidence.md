---
description: Verifica rastreabilidade e evidência dos critérios de aceite do PRD §13
owner: qa-acceptance
risk_level: high
required_commands: ["pnpm validation-dossier:check", "pnpm verification-cascade:check"]
---

# /ac-evidence

## Objetivo

Confirmar que critérios de aceite do PRD §13 estão mapeados em requisitos, testes planejados ou ativos e evidência arquivável no dossiê.

## Execução

```bash
pnpm validation-dossier:check
pnpm verification-cascade:check
```

Se `$ARGUMENTS` trouxer um REQ ou AC específico, filtrar a análise humana na saída do dossiê sem reduzir o gate automático.

## Evidência

- Registrar resumo de cobertura do dossiê.
- Registrar REQs sem teste ativo como planejados, sem inflar cobertura validada.
- Para execução real de teste, arquivar output em `compliance/validation-dossier/evidence/<REQ-id>/`.

## Escalonamento

- REQ blocker sem teste ativo antes de release escala para `qa-acceptance` e `product-governance`.
- Critério §13 sem mapeamento escala para o agente dono da área e reabre L1.
- Evidência ausente em release bloqueia L5.

## Referências

- `harness/04-compliance-pipeline.md`
- `harness/14-verification-cascade.md`
- `compliance/validation-dossier/requirements.yaml`
