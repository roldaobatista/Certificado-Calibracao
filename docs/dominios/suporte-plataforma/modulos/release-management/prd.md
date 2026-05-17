---
owner: roldao
revisado_em: 2026-05-17
proximo_review: 2026-08-17
status: draft
diataxis: explanation
audiencia: agente
relacionados:
  - docs/prd.md
  - docs/adr/0006-feature-flags.md
  - docs/dominios/suporte-plataforma/README.md
---

# PRD — Módulo Release Management

> Gestão de versões e atualizações do produto Aferê: feature flags por tenant (cita ADR-0006), notas de versão, programa beta, ambiente de homologação, comunicação de breaking changes, migração de dados controlada.

---

## 1. O que este módulo é

Conjunto de capacidades pra evoluir o Aferê em produção sem quebrar usuários. Controla versão do sistema, feature flags por tenant (ver `docs/adr/0006-feature-flags.md`), notas de versão por módulo, aviso de manutenção, migração de dados, programa beta (tenants que recebem features antes), ambiente de homologação espelho da produção, registro de bugs corrigidos e breaking changes, comunicação automática a usuários quando algo relevante muda.

## 2. Por que este módulo existe

Sem release management formal, evolução vira lottery: feature nova quebra tenant antigo, breaking change pega cliente desavisado, rollback fica manual, migração de schema acontece sem janela. Em SaaS multi-tenant a regra é "evoluir todos juntos" — mas isso só é seguro com flags, beta e comunicação.

## 3. Personas

Ver `personas.md` + transversais em `../../personas.md`.

## 4. Escopo (o que ESTÁ neste módulo)

- Controle de versão do sistema (semver — `MAJOR.MINOR.PATCH`).
- Histórico de atualizações por ambiente (dev, homologação, produção).
- Notas de versão (release notes) por release + por módulo afetado.
- Aviso de manutenção (integra com `suporte-saas/comunicado-manutencao`).
- Migração de dados controlada (orchestrator + rollback).
- Recursos novos por cliente (associar feature a planos / tenants).
- **Feature flags por tenant** (ver `docs/adr/0006-feature-flags.md` para taxonomia e regras).
- Programa beta (tenants opt-in pra features novas).
- Ambiente de homologação (sandbox por tenant).
- Registro de bugs corrigidos por release.
- Registro de breaking changes (com janela de migração).
- Comunicação automática aos usuários (in-app + e-mail + roadmap).

## 5. Non-goals

- NÃO substitui CI/CD (esse fica em `seguranca/supply-chain/` quando criado).
- NÃO faz deploy efetivo (apenas orquestra liberação após deploy via ferramentas externas).
- NÃO armazena código fonte (Git é a fonte).
- NÃO substitui ferramentas de A/B testing avançado (flags aqui são on/off por tenant; experimentação fica fora do MVP).
- NÃO controla versão de aplicativos mobile externos (apenas backend + frontend web; mobile tem release próprio via stores).
- NÃO faz rollback automático de migração destrutiva sem aprovação humana (regra de segurança).

## 6. User Stories

### US-REL-001: Controle de versão do sistema

**Como** equipe Aferê, **quero** registrar cada release com versão semver, **para** rastreabilidade.

**AC:**
- **AC-REL-001-1**: GIVEN release publicado, WHEN registrado, THEN versão `MAJOR.MINOR.PATCH`, data, commit, ambiente.
- **AC-REL-001-2**: GIVEN nova versão MAJOR, WHEN registrada, THEN exige justificativa + lista de breaking changes.

---

### US-REL-002: Notas de versão por módulo

**Como** usuário tenant, **quero** ler o que mudou em cada release, **para** entender impacto.

**AC:**
- **AC-REL-002-1**: GIVEN release publicado, WHEN consultado, THEN notas exibem seções "Adicionado", "Modificado", "Corrigido", "Removido", "Breaking Changes" agrupadas por módulo.
- **AC-REL-002-2**: GIVEN release novo em produção, WHEN aplicado, THEN notificação in-app aparece para todos os tenants afetados.

---

### US-REL-003: Feature flags por tenant

**Como** gestor de produto, **quero** ligar/desligar feature por tenant, **para** rollout gradual.

**AC:**
- **AC-REL-003-1**: GIVEN feature flag criada, WHEN tenant específico marcado, THEN flag `true` só para esse tenant.
- **AC-REL-003-2**: GIVEN flag avaliada, WHEN consultada em request, THEN resposta < 10ms (cache local).
- **AC-REL-003-3**: GIVEN flag removida (cleanup), WHEN sem referência no código por 60 dias, THEN flag aposentada com auditoria.

Ver `docs/adr/0006-feature-flags.md` para regras de criação, escopos (boolean/percentage/segment), TTL recomendado e processo de cleanup.

---

### US-REL-004: Programa beta

**Como** dono de tenant, **quero** entrar no programa beta opt-in, **para** receber features antes.

**AC:**
- **AC-REL-004-1**: GIVEN tenant inscrito no beta, WHEN release beta é publicada, THEN flags beta são ativadas automaticamente.
- **AC-REL-004-2**: GIVEN beta com problema reportado, WHEN gravidade crítica, THEN flag desligada imediatamente sem precisar deploy.

---

### US-REL-005: Ambiente de homologação

**Como** tenant Enterprise, **quero** ambiente espelho pra validar features antes da prod, **para** treinar equipe.

**AC:**
- **AC-REL-005-1**: GIVEN tenant Enterprise, WHEN solicita homologação, THEN sandbox provisionado com snapshot recente dos dados (anonimizados).
- **AC-REL-005-2**: GIVEN homologação ativa, WHEN release nova, THEN homologação recebe antes da prod (janela de 7 dias).

---

### US-REL-006: Migração de dados controlada

**Como** equipe Aferê, **quero** orquestrar migração com rollback, **para** evitar perda.

**AC:**
- **AC-REL-006-1**: GIVEN migração destrutiva planejada (DROP COLUMN, etc.), WHEN agendada, THEN exige aprovação dupla + plano de rollback documentado.
- **AC-REL-006-2**: GIVEN migração em execução, WHEN falha em qualquer step, THEN rollback automático (até o checkpoint) + alerta.

---

### US-REL-007: Registro de bugs corrigidos

**Como** usuário, **quero** ver lista de bugs corrigidos por release, **para** verificar se meu reporte foi atendido.

**AC:**
- **AC-REL-007-1**: GIVEN ticket de bug fechado com link de release, WHEN release publicada, THEN ticket atualiza pra "corrigido em vX.Y.Z" + usuário original notificado.

---

### US-REL-008: Registro de breaking changes

**Como** integrador (API consumidor), **quero** saber com antecedência de breaking changes, **para** atualizar minha integração.

**AC:**
- **AC-REL-008-1**: GIVEN breaking change planejado, WHEN registrado, THEN janela mínima de 60 dias entre anúncio e quebra efetiva.
- **AC-REL-008-2**: GIVEN tenant usa endpoint deprecated, WHEN próximo do prazo, THEN aviso em headers HTTP + e-mail.

---

### US-REL-009: Comunicação automática aos usuários

**Como** equipe Aferê, **quero** que comunicações sigam fluxo padrão, **para** consistência.

**AC:**
- **AC-REL-009-1**: GIVEN release publicada com features novas, WHEN aplicada, THEN comunicação dispara: banner in-app + e-mail + entrada no roadmap "Concluído" + atualização da BC.

---

### US-REL-010: Recursos novos por cliente (gating por plano)

**Como** PM, **quero** liberar feature apenas para plano Pro+, **para** monetizar tier alto.

**AC:**
- **AC-REL-010-1**: GIVEN feature associada ao plano Pro, WHEN tenant Free tenta usar, THEN UI exibe "Disponível no plano Pro" + CTA upgrade.

---

### US-REL-011: Aviso de manutenção (integração)

**Como** equipe Aferê, **quero** que release com janela de indisponibilidade gere comunicado automático em `suporte-saas`, **para** não esquecer aviso.

**AC:**
- **AC-REL-011-1**: GIVEN release marca `requer_janela_manutencao=true`, WHEN agendada, THEN cria `ComunicadoManutencao` em `suporte-saas` automaticamente com T-24h.

---

## 7. Métricas de sucesso

Ver `metricas.md`. Resumo:
- % releases sem rollback > 95%.
- % flags removidas após 90 dias > 90% (anti-débito).
- Tempo médio entre breaking change anunciado e aplicado >= 60 dias.

## 8. NFR

- **Performance:** avaliação de feature flag < 10ms p95; consulta de release notes < 500ms.
- **Disponibilidade:** SLO 99.9% (flags caírem afetam todo o produto).
- **Segurança:** SEC-001 (criptografia at-rest de configs sensíveis), aprovação dupla pra ação destrutiva, `INV-001` audit em mudança de flag.
- **Acessibilidade:** WCAG AA (release notes legíveis).

## 9. Glossário

Ver `glossario.md`.

## 10. Como evolui

US nova → próximo ID livre (`US-REL-NNN`). Mudança em política de flags → ADR-0006 + bump CHANGELOG.
