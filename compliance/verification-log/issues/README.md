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

Outros gatilhos podem ser adicionados sem mudar o path canônico.
