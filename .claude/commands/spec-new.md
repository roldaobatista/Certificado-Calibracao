---
description: Cria uma nova spec NNNN-slug.md em specs/ seguindo o padrão spec-driven
---

Crie uma nova spec em `specs/NNNN-$ARGUMENTS.md` onde `NNNN` é o próximo número disponível.

Estrutura obrigatória:

```markdown
# NNNN — $ARGUMENTS

> Status: draft | aprovada | em-implementação | done
> Owner: <agente responsável>
> PRD: §<seção>
> Criticality: blocker | high | medium | low

## Problema
<uma frase descrevendo o gap que esta spec resolve>

## Objetivo (Goal)
<o que será entregue>

## Não-objetivos (Non-goals)
<o que esta spec explicitamente não cobre>

## Critérios de aceite (AC)
- [ ] AC-1: ...
- [ ] AC-2: ...
- [ ] AC-3: ...

## Riscos regulatórios / metrológicos
<se aplicável — relação com PRD §9 e §16>

## Dependências
- Specs: NNNN
- Packages: ...
- Pacote normativo: ...

## Evidência
- Testes em `evals/ac/AC-<id>/*`
- Traceability em `compliance/validation-dossier/traceability-matrix.yaml`
```

Após criar, abra issue associada e aguarde aprovação antes de codar. Veja `harness/01-principios.md` §2 (spec-as-source).
