# 0059 - Configuracoes canonicas da organizacao no back-office V1

## Contexto

O PRD detalha uma tela de Configuracoes da Organizacao com identidade, branding, perfil regulatorio, numeracao, seguranca, SSO/SAML, notificacoes e LGPD/DPO na secao 17.4.15. O repositorio ja cobre onboarding, auth, workspace, usuarios, padroes, procedimentos, trilha de auditoria e nao conformidades, mas ainda nao materializa uma leitura canonica que consolide o estado dessas configuracoes no back-office.

Sem essa fatia, a equipe consegue inferir parte da prontidao a partir de telas isoladas, mas nao tem uma visao auditavel do que esta configurado, em atencao ou bloqueado na organizacao ativa.

## Escopo

- Adicionar em `packages/contracts` um contrato compartilhado para:
  - resumo canonicamente tipado das configuracoes da organizacao;
  - secoes navegaveis por querystring;
  - detalhe da secao selecionada no proprio catalogo.
- Implementar em `apps/api/src/domain/settings` um builder canonico das configuracoes da organizacao.
- Expor em `apps/api/src/interfaces/http` o endpoint canonico `GET /settings/organization`.
- Materializar em `apps/web/src/settings` o loader e o view model legivel para configuracoes.
- Adicionar a pagina `apps/web/app/settings/organization/page.tsx`.
- Integrar atalhos de configuracoes a partir do workspace operacional.

## Fora de escopo

- Persistencia real das configuracoes, gravacao transacional, upload binario de logo ou configuracao SAML.
- CRUD real de plano, integracoes, notificacoes, DPO, consentimentos ou alteracao formal de perfil regulatorio.
- Dupla aprovacao persistida, workflow real de change management ou sincronizacao com billing.

## Criterios de aceite

- O contrato compartilhado representa resumo, secoes e detalhe da secao selecionada com status, checklist, evidencias e links relacionados.
- O builder canonico oferece um cenario operacional pronto, um cenario de renovacao em atencao e um cenario bloqueado por mudanca de perfil sem aprovacao.
- O endpoint `GET /settings/organization` responde com catalogo tipado e selecao por querystring.
- A pagina web traduz as configuracoes em leitura operacional legivel e permanece fail-closed sem payload valido do backend.
- O workspace passa a oferecer um atalho coerente para a leitura canonica de configuracoes.

## Evidencia

- `pnpm exec tsx --test apps/api/src/domain/settings/organization-settings-scenarios.test.ts`
- `pnpm exec tsx --test apps/web/src/settings/organization-settings-scenarios.test.ts`
- `pnpm exec tsx --test apps/api/src/app.test.ts`
- `pnpm check:all`
- `pnpm test:tenancy`
