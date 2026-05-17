---
owner: roldao
revisado_em: 2026-05-17
proximo_review: 2026-08-17
status: draft
diataxis: explanation
audiencia: agente
relacionados:
  - docs/prd.md
  - docs/dominios/suporte-plataforma/README.md
---

# PRD — Módulo Suporte SaaS

> **Meta-módulo:** suporte do PRÓPRIO produto Aferê para os usuários dos tenants. NÃO é suporte que o tenant oferece ao cliente final dele (isso fica em `operacao/chamados/`).

---

## 1. O que este módulo é

Central de atendimento INTERNA do produto. Quando o usuário do tenant tem problema com o Aferê (bug, dúvida de uso, sugestão), abre ticket aqui. Roteia pra equipe de suporte do Aferê (humano + agentes IA). Inclui base de conhecimento do produto, chat, status, evidências, roadmap público, votação de melhorias, comunicação de manutenção.

## 2. Por que este módulo existe

Confundir o suporte do SaaS com o suporte operacional que o tenant dá ao cliente dele gera caos. Cliente final reclama de balança quebrada → vai pro `operacao/chamados/`. Tenant usuário do Aferê reclama que botão de salvar não funciona → vem pra cá. Separação evita confusão e SLA misturado.

## 3. Personas

Ver `personas.md` + transversais em `../../personas.md`.

## 4. Escopo

- Central de suporte (portal) acessível dentro do produto.
- Abertura de ticket pelo usuário do tenant.
- Categorização (bug | dúvida | sugestão | acesso | financeiro do SaaS) + prioridade.
- SLA configurável por plano de assinatura.
- Base de conhecimento do produto (FAQ, tutoriais, vídeos curtos).
- Chat de suporte (humano + IA híbrido).
- Histórico de atendimento por usuário e por tenant.
- Status do ticket (aberto / em análise / aguardando usuário / resolvido / fechado).
- Evidências anexadas (print, vídeo, log do navegador).
- Acesso remoto registrado (quando suporte entra no tenant — logado com consentimento explícito).
- Bugs reportados → integração com tracker interno.
- Sugestões de melhoria → integração com roadmap.
- Roadmap público (alto nível) ou privado por tenant.
- Votação de melhorias.
- Comunicação de manutenção do sistema (banner, e-mail).

## 5. Non-goals

- NÃO atende cliente final do tenant (módulo `operacao/chamados/`).
- NÃO substitui ferramentas de helpdesk corporativas externas (Zendesk, Intercom) — Aferê tem o seu próprio embutido para ser fluxo único.
- NÃO faz cobrança/billing do SaaS (módulo `gestao-assinaturas-planos/` quando criado).
- NÃO permite que usuário de tenant A veja tickets de tenant B (`INV-TENANT-001`).
- NÃO faz acesso remoto sem consentimento ativo e logado.

## 6. User Stories

### US-SUP-001: Abrir ticket pelo usuário

**Como** usuário do tenant, **quero** abrir ticket dentro do Aferê sem sair pra outro sistema, **para** resolver dúvida rápido.

**AC:**
- **AC-SUP-001-1**: GIVEN usuário autenticado, WHEN clica "Falar com suporte" e preenche, THEN ticket criado com tenant_id, usuário, categoria, prioridade default, anexos.
- **AC-SUP-001-2**: GIVEN ticket criado, WHEN salvo, THEN número de protocolo + ETA do SLA exibidos.

---

### US-SUP-002: Categorização e priorização

**Como** atendente do suporte, **quero** categorizar e priorizar tickets, **para** atender o crítico primeiro.

**AC:**
- **AC-SUP-002-1**: GIVEN ticket aberto, WHEN categorizado como "bug crítico", THEN SLA P1 aplicado.
- **AC-SUP-002-2**: GIVEN priorização automática por palavras-chave, WHEN ticket entra, THEN sugestão pré-preenchida.

---

### US-SUP-003: SLA por plano

**Como** gestor do SaaS, **quero** SLA diferente por plano (free/pro/enterprise), **para** monetizar tier alto.

**AC:**
- **AC-SUP-003-1**: GIVEN tenant em plano Pro, WHEN ticket P1 criado, THEN ETA = 4h úteis.
- **AC-SUP-003-2**: GIVEN SLA violado, WHEN limite atingido, THEN alerta dispara + tenant notificado.

---

### US-SUP-004: Base de conhecimento

**Como** usuário, **quero** buscar resposta antes de abrir ticket, **para** resolver sozinho.

**AC:**
- **AC-SUP-004-1**: GIVEN texto digitado no campo de abertura, WHEN >= 4 caracteres, THEN sistema sugere artigos relevantes em tempo real.
- **AC-SUP-004-2**: GIVEN artigo consultado, WHEN marcado "resolveu", THEN ticket não é aberto e métrica de deflexão incrementa.

---

### US-SUP-005: Chat de suporte híbrido

**Como** usuário, **quero** chatear (com IA primeiro, humano depois), **para** resposta imediata.

**AC:**
- **AC-SUP-005-1**: GIVEN chat aberto, WHEN mensagem enviada, THEN agente IA responde em < 3s.
- **AC-SUP-005-2**: GIVEN usuário pede humano, WHEN solicitado, THEN handoff acontece com histórico preservado.

---

### US-SUP-006: Histórico de atendimento

**Como** atendente, **quero** ver todos os tickets anteriores do tenant/usuário, **para** contexto.

**AC:**
- **AC-SUP-006-1**: GIVEN ticket aberto, WHEN visualizado, THEN sidebar mostra últimos 10 tickets do mesmo tenant/usuário.

---

### US-SUP-007: Acesso remoto registrado

**Como** atendente de suporte, **quero** acessar o tenant do usuário com consentimento, **para** investigar bug específico.

**AC:**
- **AC-SUP-007-1**: GIVEN solicitação de acesso remoto, WHEN tenant admin aceita, THEN sessão criada com TTL (default 2h), todas as ações logadas, banner visível.
- **AC-SUP-007-2**: GIVEN sessão ativa, WHEN tenant admin revoga, THEN acesso encerra imediatamente.

---

### US-SUP-008: Reportar bug com evidências

**Como** usuário, **quero** anexar print/vídeo/log ao ticket, **para** acelerar diagnóstico.

**AC:**
- **AC-SUP-008-1**: GIVEN ticket categoria "bug", WHEN aberto, THEN sistema sugere captura automática de logs do navegador + screenshot opcional.

---

### US-SUP-009: Sugestões de melhoria e roadmap

**Como** usuário, **quero** sugerir melhoria e ver no que estão trabalhando, **para** influenciar produto.

**AC:**
- **AC-SUP-009-1**: GIVEN sugestão enviada, WHEN aprovada pelo gerente de produto, THEN aparece no roadmap público.
- **AC-SUP-009-2**: GIVEN sugestão visível, WHEN usuário vota, THEN voto computado uma vez por usuário.

---

### US-SUP-010: Roadmap visível

**Como** dono de tenant, **quero** ver o que vem nas próximas releases, **para** planejar.

**AC:**
- **AC-SUP-010-1**: GIVEN roadmap público, WHEN consultado, THEN exibe trimestres com itens em "Planejado", "Em construção", "Concluído".

---

### US-SUP-011: Comunicação de manutenção

**Como** equipe SaaS, **quero** avisar usuários antes/durante/após manutenção, **para** evitar surpresa.

**AC:**
- **AC-SUP-011-1**: GIVEN manutenção agendada, WHEN T-24h e T-1h, THEN banner aparece nos tenants afetados + e-mail enviado.
- **AC-SUP-011-2**: GIVEN manutenção em curso, WHEN status muda, THEN página de status atualiza.

---

## 7. Métricas de sucesso

Ver `metricas.md`. Resumo:
- Taxa de deflexão (base de conhecimento) > 40%.
- CSAT pós-ticket > 4.5/5.
- Cumprimento de SLA > 95%.

## 8. NFR

- **Performance:** abertura de ticket < 1s; busca BC < 500ms; chat resposta IA < 3s.
- **Disponibilidade:** SLO 99.9% (suporte cair afeta confiança).
- **Segurança:** SEC-001 (isolamento entre tenants em tickets), SEC-002 (consentimento e log em acesso remoto), `INV-TENANT-001`.
- **Acessibilidade:** WCAG AA.

## 9. Glossário

Ver `glossario.md`.

## 10. Como evolui

US nova → próximo ID livre (`US-SUP-NNN`). Mudança em AC implementado → ADR + teste.
