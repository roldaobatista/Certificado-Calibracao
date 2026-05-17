---
owner: Roldão
revisado-em: 2026-05-17
status: draft
modulo: crm
dominio: comercial
diataxis: explanation
---

# PRD — Módulo CRM

## 1. O que este módulo é

CRM **contínuo** (não morre após emitir certificado) que captura lead → oportunidade → orçamento → cliente → retenção. Inclui funil kanban configurável, lead scoring por sinais reais do produto (calibração vencendo, NPS, OS concluída), tarefas automáticas e NPS pós-OS. **Diferencial defensável #5 + #8**: concorrentes nacionais matam o cliente no CRM após emitir certificado.

## 2. Por que existe

Decisão fundadora de PRODUTO 3 (Cliente nunca morre no CRM) + BIG-10 (Cliente 360°) + BIG-11 (Automações configuráveis). Dores: D-002 (R$ 3-8k/mês perdidos por esquecer renovação), "pipeline em planilha que ninguém olha", "cliente sumiu e nunca soubemos".

## 3. Personas

Ver `../../personas.md`. Dominante: P-COM-02 Vendedor + P-COM-01 Atendente (caixa de entrada WhatsApp). P-COM-05 Dono configura automações.

## 4. Escopo MVP-1

**Wave A (semanas 1-13):**
- Caixa de entrada (leads não-convertidos vindos de WhatsApp/formulário/import)
- Conversão lead → cliente (US-CRM-001) — JTBD-086 (1 clique)
- Tarefas manuais atribuídas a vendedor

**Wave B (semanas 14-22):**
- Funil kanban configurável + drag-and-drop
- Lead scoring + lista do dia (JTBD-083)
- NPS pós-OS automático (JTBD-085)
- Engine de automações simples (Solution 5.2 — MVP completo é V2)
- Sandbox de automação (JTBD-087 — mitigação R-novo CRM-1)
- Motivo de perda + análise de churn

## 5. Non-goals

- **E-mail marketing massivo** — fora do escopo (RAT-06 só permite mensagens transacionais)
- **Telefonia integrada (VoIP, click-to-call)** — V2
- **Lead scoring custom com fórmula visual complexa** — V3 (MVP usa regras pré-definidas + pesos configuráveis)
- **Multi-pipeline simultâneo por vendedor** — MVP-1 tem 1 pipeline padrão + 1 pipeline customizável
- **Integração com Facebook/Google Ads como fonte de lead** — V2
- **Webhook entrante de formulário web** — Wave B só (não MVP-1)
- **Bot de WhatsApp com NLP** — fora; integração WhatsApp BSP (F-E) é transacional
- **Forecasting com IA** — V2

## 6. User Stories

### US-CRM-001: Converter lead WhatsApp em cliente em 1 clique (JTBD-086)
**Como** atendente, **quero** botão único no card de lead que cria cliente master + oportunidade + (opcional) chamado, **para** não digitar mesma info em 3 telas.
- AC-1: GIVEN lead na caixa de entrada com {nome, telefone, mensagem inicial} WHEN clico "converter" THEN abre modal pré-preenchido com escolha de tipo PF/PJ + completar dados mínimos.
- AC-2: Cria cliente master + cria oportunidade no funil padrão (etapa "novo") + dispara evento `Lead.Convertido`.
- **INV:** INV-024 (dedup), INV-TENANT-001.

### US-CRM-002: Ver lista do dia priorizada (JTBD-083)
**Como** vendedor, **quero** abrir CRM e ver lista ordenada por sinais (calibração vencendo / NPS detrator / sem contato 90d / parcela vencida / OS recém-fechada), **para** não decidir no improviso.
- AC-1: Lista gerada a cada login + atualizada a cada hora.
- AC-2: Cada card mostra **por quê** está no topo (sinais ativos).
- AC-3: Limite 30 clientes/dia (configurável).

### US-CRM-003: Disparar NPS automático pós-OS (JTBD-085)
**Como** dono, **quero** que toda OS concluída dispare pesquisa NPS em 24h, **para** capturar feedback enquanto experiência está fresca.
- AC-1: Evento `OS.Concluida` → job agenda envio NPS em D+1.
- AC-2: Resposta detrator (0-6) cria tarefa automática "Ligar urgente" pro vendedor responsável + alerta gerente.

### US-CRM-004: Configurar automação em sandbox antes de ativar (JTBD-087 + R-novo CRM-1)
**Como** dono, **quero** que toda nova automação mostre simulação "se rodasse hoje, dispararia em X clientes — eis a lista", **para** evitar disparo em massa errado.
- AC-1: Toda nova regra exige passar por sandbox antes de ativar.
- AC-2: Sandbox mostra lista de clientes afetados + permite revisar.
- **Risco mitigado:** R-novo CRM-1 (mensagem indevida → reclamação).

### US-CRM-005: Funil kanban configurável
**Como** dono, **quero** customizar etapas do funil (1 pipeline custom + 1 padrão), **para** refletir meu processo real.
- AC-1: Drag-and-drop entre colunas.
- AC-2: Mover para "perdido" pede motivo obrigatório (dropdown + texto livre).

### US-CRM-006: Caixa de entrada WhatsApp/import
**Como** atendente, **quero** ver lista de leads novos (vindos de WhatsApp + import manual) ANTES de virarem cliente.

### US-CRM-007: Visão 360° puxa timeline do cliente (já em módulo Clientes)
Este módulo **consome** a tela `/clientes/{id}` — não duplica.

## 7. Métricas

Ver `metricas.md`. Resumo: taxa lead → cliente > 25%, NPS médio ≥ 60, tempo médio resposta NPS detrator < 4h, % automações testadas em sandbox = 100%.

## 8. NFR

- Performance: lista do dia p95 < 2s; movimento de card kanban < 500ms.
- Disponibilidade: 99.5%.
- LGPD: RAT-06 obrigatório para envios WhatsApp; opt-out respeitado em todas automações.
- Segurança: sandbox obrigatório (`INV-AGENT-001` — input não-confiável vindo de campos de CRM passa por sanitizer antes de chegar a LLM/automação).

## 9. Glossário

Ver `glossario.md`.
