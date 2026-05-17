---
owner: roldao
revisado_em: 2026-05-17
proximo_review: 2026-08-17
status: draft
diataxis: reference
audiencia: agente
relacionados:
  - docs/comum/glossario.md
  - docs/adr/0006-feature-flags.md
---

# Glossário — Módulo Release Management

> Termos específicos. Transversais em `docs/comum/glossario.md`.

---

| Termo | Definição (1 linha) | Sinônimos proibidos | Se vir na tela/log, significa | Origem |
|---|---|---|---|---|
| Release | Conjunto versionado de mudanças publicado | "deploy" (esse é a ação técnica) | unidade comunicável | semver.org |
| Versão semver | `MAJOR.MINOR.PATCH` | "número da release" (ambíguo) | identificação canônica | semver.org |
| MAJOR | Versão com breaking change | "versão grande" (impreciso) | quebra compatibilidade | semver.org |
| MINOR | Versão com feature compatível | — | adição sem quebra | semver.org |
| PATCH | Versão com correção compatível | "hotfix" (subconjunto) | bug fix | semver.org |
| Feature flag | Chave booleana/percentual que liga/desliga feature em runtime | "toggle" (ambíguo), "switch" | controle de rollout | ADR-0006 |
| Flag por tenant | Flag avaliada com escopo tenant_id | — | rollout segmentado | ADR-0006 |
| Flag percentual | Liberada para X% dos tenants/usuários | "canary parcial" | rollout gradual | ADR-0006 |
| Cleanup de flag | Remoção de flag morta do código + config | "limpeza" (ambíguo) | anti-débito técnico | ADR-0006 |
| Breaking change | Mudança que quebra contrato (API, schema, UX crítica) | "incompatível" | exige janela 60+ dias | Interno |
| Release notes | Documento humano descrevendo o que mudou | "changelog" (parcialmente) | comunicação a usuários | keepachangelog.com |
| CHANGELOG | Arquivo técnico estruturado de mudanças | "release notes" (impreciso) | técnico, para devs | keepachangelog.com |
| Programa beta | Tenants opt-in que recebem features antes | "preview" (ambíguo) | rollout antecipado | Interno |
| Ambiente homologação | Sandbox espelho de produção | "staging" (técnico) | tenant prova antes | Interno |
| Migração de dados | Transformação irreversível de schema/dados | "ETL" (ambíguo) | mudança estrutural | Interno |
| Rollback | Reverter release ou migração | "voltar" (ambíguo) | restaurar estado anterior | Padrão |
| Deprecation | Marcar funcionalidade pra remoção futura | "obsoleto" (pós-remoção) | aviso de fim de vida | RFC 8594 |
| Sunset | Data efetiva de remoção pós-deprecation | "fim de vida" (ambíguo) | dia X em que para | RFC 8594 |
| Recurso por plano | Feature gateada por plano comercial | "feature paga" (ambíguo) | tier comercial | Interno |
| Janela de manutenção | Período comunicado de indisponibilidade | "downtime" (técnico) | aviso ao usuário | Interno |

---

## Como evolui

Termo novo → adicionar + verificar conflito com glossário comum. Mudança em política de flags → ADR-0006.
