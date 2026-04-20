# 06 — Copy-lint regulatório

> **P0-5**: evita claims proibidos em site, portal, e-mails, onboarding, docs comerciais e PRD.

## Problema original

O próprio PRD contém, em wireframe, a frase "Emita certificados de calibração que passam em qualquer auditoria" — claim que o mesmo PRD proíbe em §2.3 e §14. Sem linter automático, esse risco se propaga para produção.

## Cobertura

Paths varridos por CI + hook `PreCommit`:

- `apps/web/**/*.{tsx,ts,md,mdx}`
- `apps/portal/**/*.{tsx,ts,md,mdx}`
- `apps/api/src/templates/emails/**`
- `compliance/**`
- `specs/**`
- `PRD.md`
- `ideia.md`
- `README.md`
- Release notes e changelog

## Padrões proibidos (regex)

```yaml
# packages/copy-lint/rules.yaml
forbidden:
  - pattern: '\bpassa(?:m)? em qualquer auditoria\b'
    severity: error
    reason: "Promessa de conformidade absoluta (PRD §2.3, §14)"
  - pattern: '100\s*%\s*conforme'
    severity: error
    reason: "Promessa de conformidade absoluta"
  - pattern: '\bgarantimos?\b.{0,40}\b(ISO|acredita[cç][aã]o|Inmetro|Cgcre)\b'
    severity: error
    reason: "Garantia indevida de acreditação/certificação"
  - pattern: '\baprovado (pelo|pela) (Inmetro|Cgcre)\b'
    severity: error
    reason: "Claim falso de aprovação oficial"
  - pattern: '\bsubstitui (o|a) auditori[ao]\b'
    severity: error
    reason: "Claim de substituição de auditoria"
  - pattern: '\bconformidade\s+total\b'
    severity: warning
    reason: "Revisar com jurídico"
```

## Claims aprovados

Vivem em `compliance/approved-claims.md`, com revisão jurídica datada. Exemplo de claims aprovados:

- "Plataforma metrológica que sustenta sua operação conforme ABNT NBR ISO/IEC 17025."
- "Bloqueia emissão fora das regras normativas automatizáveis configuradas no produto."
- "Pronto para o Certificado de Calibração Digital (DCC) conforme Plano Estratégico Inmetro 2024–2027."

Cada claim aprovado tem:
- Data da última revisão jurídica.
- Advogado/parecerista responsável.
- Limites de uso (onde pode e onde não pode aparecer).

## Fluxo

1. Desenvolvedor/agente edita copy.
2. Hook `PreCommit` roda `copy-lint` no delta. Claim proibido = commit bloqueado.
3. CI varre todo o repo a cada PR. Qualquer *error* = PR falha.
4. Claim novo (não listado em approved): agente `copy-compliance` sugere alternativa ou escala para `product-governance`.
5. `product-governance` só libera após revisão jurídica documentada em `compliance/legal-opinions/`.

## Aplicação imediata

- **Teste de fogo**: aplicar o linter ao `PRD.md` atual deve pegar a frase proibida do wireframe. Corrigir o PRD como primeira PR usando o linter já ativo.
- **Regressão**: esse teste fica permanente em `evals/copy-lint/prd-self-check.spec.ts`.

## Slash-command

`/claim-check <arquivo|glob>` — roda linter localmente e sugere reescrita via `copy-compliance`.
