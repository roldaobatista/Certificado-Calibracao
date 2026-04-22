# 0046 — Dry-run real de emissão controlada para V1

## Contexto

O roadmap V1 prevê emissão online controlada para perfis Tipo B e Tipo C, enquanto o harness já possui o slash-command `/emit-cert-dry`. Hoje esse comando ainda é apenas preparatório e fail-closed, sem consolidar em um único fluxo as validações já implementadas para equipamento, padrão, competência do signatário, numeração, declaração metrológica, audit trail e QR público.

## Escopo

- Adicionar em `apps/api/src/domain/emission` um agregador executável de dry-run de emissão.
- Consolidar em um único resultado os checks de perfil regulatório, cadastro de equipamento, elegibilidade do padrão, competência do signatário, numeração sequencial, declaração metrológica, audit trail e QR público.
- Materializar em `packages/contracts` o shape compartilhado do resultado do dry-run.
- Expor um CLI real em `tools/emit-cert-dry.ts` e script root `pnpm emit-cert-dry`.
- Atualizar `/emit-cert-dry` para usar a execução real em vez do modo apenas preparatório.
- Materializar em `apps/web/src/emission` uma leitura operacional do dry-run para o back-office.

## Fora de escopo

- Persistência real de OS, certificado, assinatura ou trilha de auditoria no banco.
- Geração de PDF/A final.
- Envio de e-mail, portal autenticado do cliente ou upload de artefatos regulatórios.
- RBAC completo, sessão real e workflow humano completo de revisão/aprovação.

## Critérios de aceite

- O dry-run retorna `ready` quando todas as pré-condições de emissão passam para um cenário Tipo B/C válido.
- O dry-run retorna `ready` para Tipo A apenas quando a emissão é permitida, podendo suprimir o símbolo quando o escopo acreditado não se aplica.
- O dry-run retorna `blocked` quando qualquer pré-condição falha, explicitando os checks bloqueantes.
- O CLI `pnpm emit-cert-dry -- --profile <A|B|C>` seleciona um cenário canônico e imprime um relatório legível.
- A tela do back-office traduz o resultado em checklist operacional sem importar pacotes críticos diretamente.

## Evidência

- `pnpm exec tsx --test apps/api/src/domain/emission/dry-run.test.ts`
- `pnpm exec tsx --test apps/web/src/emission/emission-dry-run-scenarios.test.ts`
- `pnpm exec tsx --test tools/emit-cert-dry.test.ts`
- `pnpm emit-cert-dry -- --profile B`
- `pnpm check:all`
