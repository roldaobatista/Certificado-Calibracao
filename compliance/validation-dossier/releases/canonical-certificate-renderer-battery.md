# Renderer determinístico e bateria canônica de certificados

## Escopo

- Renderer determinístico de certificado em PDF para regressão canônica.
- Catálogo de 30 snapshots, com 10 artefatos por perfil regulatório A/B/C.
- Ferramenta de sincronização de `baseline/`, `current/` e `manifest.yaml`.
- Regeneração automática de `current/` antes do `snapshot-diff-check`.

## Evidências executadas

- `pnpm exec tsx --test apps/api/src/domain/emission/certificate-renderer.test.ts apps/api/src/domain/emission/certificate-snapshot-catalog.test.ts`
- `pnpm exec tsc -p apps/api/tsconfig.json --noEmit`
- `pnpm exec tsx apps/api/src/domain/emission/certificate-snapshots-tool.ts sync`

## Limitações honestas

- O artefato gerado é um PDF determinístico para regressão, mas a conformidade PDF/A formal ainda depende de validador externo e dossiê dedicado.
- O renderer ainda não publica o binário oficial em storage/WORM nem fecha sozinho a persistência documental da emissão.
- Portal do cliente, download autenticado e assinatura criptográfica externa continuam fora desta fatia.
