# Spec 0083 — Renderer determinístico de certificado e bateria canônica de snapshots

## Contexto

O repositório já possui dry-run de emissão, prévia tipada do certificado, fluxo persistido de revisão/assinatura e Gate 7 estrutural para snapshot-diff. Mesmo assim, `compliance/validation-dossier/snapshots/` ainda guarda apenas artefatos dogfood em texto, e a bateria final de 30 certificados canônicos segue pendente porque não existe um renderer determinístico de certificado.

Sem esta fatia, o harness consegue bloquear drift estrutural do manifesto, mas ainda não compara artefatos reais da peça documental emitida pela trilha de emissão.

## Escopo

- Implementar em `apps/api/src/domain/emission` um renderer determinístico de certificado em PDF.
- Criar um catálogo interno com 30 snapshots canônicos de certificado, sendo 10 por perfil A/B/C.
- Adicionar ferramenta em `tools/` para regenerar `baseline/`, `current/` e `manifest.yaml` a partir do catálogo canônico.
- Fazer `snapshot-diff-check` passar a regenerar `current/` antes da comparação byte-a-byte do Gate 7.
- Atualizar o dossiê de snapshots para substituir os artefatos dogfood por PDFs determinísticos reais.

## Fora de escopo

- Atestação formal de conformidade PDF/A por validador externo, ICC profile homologado ou laudo de arquivamento de longo prazo.
- Assinatura digital qualificada, carimbo do tempo oficial, ICP-Brasil ou PKI externa.
- Persistência binária do PDF emitido em object storage/WORM.
- Download no portal do cliente, e-mail transacional ou UI final do renderer.

## Critérios de aceite

- `apps/api/src/domain/emission/certificate-renderer.ts` gera bytes determinísticos de PDF para a peça canônica de certificado.
- O renderer deixa explícito no artefato e no código que a conformidade PDF/A formal ainda depende de validação externa, sem alegar completude regulatória inexistente.
- `apps/api/src/domain/emission/certificate-snapshot-catalog.ts` materializa 30 snapshots canônicos, com distribuição 10/10/10 entre perfis A/B/C.
- `tools/certificate-snapshots.ts` consegue regenerar `current/`, `baseline/` e `manifest.yaml`.
- `package.json` passa a regenerar `current/` antes de `snapshot-diff-check`.
- `compliance/validation-dossier/snapshots/` deixa de depender dos `.txt` dogfood e passa a versionar os PDFs canônicos.

## Evidência

- `pnpm exec tsx --test apps/api/src/domain/emission/certificate-renderer.test.ts`
- `pnpm exec tsx --test tools/certificate-snapshots.test.ts`
- `pnpm snapshot-diff-check`
- `pnpm check:all`
- `pnpm test:tenancy`
