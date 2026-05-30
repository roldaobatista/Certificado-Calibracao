---
owner: roldao
revisado-em: 2026-05-28
status: draft
idioma: pt-BR
limite-linhas: 150
proposito: README raiz do projeto destino — visão de 1 minuto, links para AGENTS/REGRAS/CLAUDE e fluxo de leitura
---

<!--
template: README.md
uso: copiar para a raiz do repositório do PROJETO DESTINO e preencher placeholders <...>.
referência: ESTRUTURA-PROJETO-NOVO-DO-ZERO.md §C0
Nota: este é o template para o README.md do PROJETO DESTINO.
      Não confundir com `templates/README.md` (catálogo dos templates do método).
-->

# Aferê Prumo

<1 frase do que é o produto>

**Estado:** <alpha|beta|prod> · **Versão:** <0.1.0> · **Licença:** <MIT|Apache-2.0|proprietária>

<!-- Badges opcionais (descomentar e ajustar):
[![CI](<URL-do-badge-de-CI>)](<URL>)
[![Cobertura](<URL-do-badge-de-cobertura>)](<URL>)
[![Versão](<URL-do-badge-de-versão>)](<URL>)
-->

## Rodar localmente
```bash
<comando 1>
<comando 2>
<comando 3>
```

## Rodar testes
```bash
<comando de teste>
```

## Contratos deste projeto (leitura obrigatória para contribuir)

Este projeto segue o método [Modelo Projeto Novo](https://github.com/<org>/modelo-projeto-novo) — método canônico que agentes IA seguem para estruturar projetos do zero. Os documentos abaixo são **contratuais** (vinculam humano e agente IA) e seguem hierarquia de precedência declarada em `.claude/memory/constitution.md`:

| Documento | O que define |
|---|---|
| [`.claude/memory/constitution.md`](./.claude/memory/constitution.md) | Princípios fundadores. Autoridade máxima. |
| [`REGRAS-INEGOCIAVEIS.md`](./REGRAS-INEGOCIAVEIS.md) | Regras não-negociáveis (segurança, qualidade, processo). |
| [`AGENTS.md`](./AGENTS.md) | Contrato canônico de produto/processo (identidade, stack, comandos). |
| [`CLAUDE.md`](./CLAUDE.md) | Adendo específico do harness Claude Code. |
| [`SECURITY.md`](./SECURITY.md) | Política de segurança e canal de divulgação responsável. |
| [`CONTRIBUTING.md`](./CONTRIBUTING.md) | Fluxo de contribuição (humanos e agentes). |
| [`MAINTAINERS.md`](./MAINTAINERS.md) | Lista de mantenedores ativos, processo de release, sucessão. |

> **Hierarquia em conflito:** constitution > REGRAS-INEGOCIAVEIS > AGENTS > CLAUDE. O documento mais alto vence.

## Documentação completa

- [`docs/INDICE.md`](./docs/INDICE.md) — sitemap navegável.
- [`docs/documentos-do-projeto.md`](./docs/documentos-do-projeto.md) — status de cada documento contratual.
- [`docs/nao-aplica.md`](./docs/nao-aplica.md) — camadas do método que não se aplicam a este projeto (com justificativa).

## Glossário

- [`GLOSSARIO-ROLDAO.md`](./GLOSSARIO-ROLDAO.md) — termos técnicos traduzidos para linguagem de dono não-técnico (PR, commit, lint, deploy, etc.).
- [`docs/glossario.md`](./docs/glossario.md) — glossário de termos do **domínio do produto** (entidades, papéis, estados).

## Histórico de mudanças

Ver [`CHANGELOG.md`](./CHANGELOG.md) (formato [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/), versionamento [SemVer](https://semver.org/lang/pt-BR/)).

## Suporte e contato

- **Bugs e dúvidas técnicas:** abrir issue em <URL-do-repositório>/issues.
- **Reportar vulnerabilidade de segurança:** ver [`SECURITY.md`](./SECURITY.md) (NÃO abrir issue pública).
- **Discussão de produto / RFC:** <canal — Discord, GitHub Discussions, e-mail>.
- **Contato direto do mantenedor principal:** <email-ou-handle>.

## Licença

<MIT|Apache-2.0|proprietária> · Autor: <nome> · <ano>

Ver [`LICENSE`](./LICENSE) para texto completo.
