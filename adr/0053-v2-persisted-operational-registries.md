# ADR 0053 — Cadastros operacionais persistidos para V2

## Status

Aceito

## Contexto

Após a fundação persistida de V1, o projeto ainda mantinha usuários operacionais, clientes, padrões, procedimentos e equipamentos presos a cenários de leitura. O backlog foundation-first passou a exigir V2 completa antes da abertura real do fluxo de OS em V3.

## Decisão

Adotar uma camada persistida de cadastros operacionais para V2 com os seguintes pilares:

1. `packages/db/prisma/schema.prisma` passa a modelar `customers`, `standards`, `standard_calibrations`, `procedure_revisions`, `equipment` e `registry_audit_events`.
2. A migração V2 habilita tenancy explícita com RLS e policies em todas as novas tabelas.
3. O backend centraliza a persistência de cadastros em `RegistryPersistence`, preservando `?scenario=` apenas como fallback canônico.
4. `apps/api` expõe rotas autenticadas de leitura e escrita para usuários, clientes, padrões, procedimentos e equipamentos.
5. `apps/web` passa a encaminhar o cookie atual para os loaders de cadastros e a operar em modo persistido sem carregar links internos com `?scenario=`.
6. Busca, filtros, arquivamento e trilha mínima são tratados como parte do fechamento de V2, não como refinamento opcional.

## Consequências

### Positivas

- Fecha a lacuna entre catálogos demonstrativos e cadastros reais do domínio operacional.
- Destrava V3 sobre registros reais de usuários, clientes, padrões, procedimentos e equipamentos.
- Mantém a cobertura existente dos cenários canônicos, enquanto o caminho persistido vira o modo operacional padrão.

### Limitações honestas

- A trilha V2 cobre criação, atualização e arquivamento mínimos; ainda não substitui o audit trail crítico do fluxo de emissão.
- O front oferece formulários reais e filtros locais, mas ainda não materializa edição rica por entidade nem paginação server-side.
- O detalhamento de OS recentes, anexos binários e documentos vinculados permanece simplificado até V3/V4.
