# Verification Issues

Registro canônico dos drafts usados para abrir issues automáticas da cascata de verificação.

## Estrutura

- `_template.md` define o corpo Markdown base.
- `drafts/` recebe os arquivos renderizados pela automação.

## Como gerar

```bash
pnpm verification-cascade:issue-drafts -- --write
```

O comando só grava drafts quando `tools/verification-cascade.ts` encontra findings elegíveis.

Findings suportados hoje:

- `CASCADE-003` para snapshot diff;
- `CASCADE-007` para `spec-review-flag` em re-auditoria L1.
- `CASCADE-008` para `epic-review-flag` em re-auditoria L0.

No `push` para `main`, o workflow também reconcilia issues gerenciadas já existentes: cria, reabre, atualiza ou fecha conforme o conjunto atual de drafts.

Outros gatilhos podem ser adicionados sem mudar o path canônico.
