---
owner: Roldão
revisado-em: 2026-05-17
status: draft
modulo: chamados
dominio: operacao
---

# PRD — Módulo Chamados (Helpdesk)

## 1. O que este módulo é

Porta de entrada de qualquer demanda do cliente: WhatsApp, telefone, portal, email. O chamado nasce, é triado em ≤ 30s, recebe SLA e ou (a) vira OS quando exige execução, ou (b) é fechado direto por orientação. **OP16 — Wave B**.

## 2. Por que este módulo existe

Dor #20 (atendente reabre WhatsApp 5x e perde contexto) + Dor #05 (cliente reclama que nunca sabe o status). Cobre JTBD-008 (triagem 30s), JTBD-016 (abrir em 1 min), JTBD-020 (não copiar info 3x), JTBD-086 (WhatsApp em 1 clique).

## 3. Personas

`../personas.md` — P-OP-03 (atendente, primária), P-OP-04 (gerente — supervisão SLA), P-OP-05 (cliente final, autor do chamado).

## 4. Escopo MVP-1 Wave B

- CRUD de chamado com canal de origem rastreado
- Triagem rápida (tipo, urgência, equipamento, cliente) ≤ 30s
- Cálculo automático de SLA baseado em (tipo × urgência)
- Detecção de duplicados (cliente + equipamento + janela 7 dias) — sugere mesclar, **nunca mescla sozinho**
- Regra de distribuição sugere atendente/técnico (humano confirma)
- Escalonamento automático de SLA (75% do prazo → notifica; 100% → escala pra gerente)
- Conversão em OS preservando histórico (chamado vira `os_origem`)
- Fechamento sem OS com razão obrigatória
- Integração WhatsApp (link "fale com a gente" — Solution 8.2)
- Audit log RAT-08

## 5. Non-goals MVP-1

- Bot/IA respondendo o cliente sozinho (humano sempre na triagem)
- Mescla automática de duplicados (sempre humano decide)
- Pesquisa de satisfação dentro do chamado (vai pra Comercial NPS)
- Base de conhecimento integrada (MVP-2)
- Roteamento por SLA financeiro / contrato premium (MVP-2)
- Métricas avançadas estilo Zendesk (CSAT, FRT por agente) — MVP-2

## 6. User Stories (resumo)

- **US-CH-001:** atendente recebe chamado via WhatsApp (link) e triagem ≤ 30s
- **US-CH-002:** sistema sugere duplicado quando atende-regra cliente+equip+7d
- **US-CH-003:** SLA é calculado automaticamente baseado em (tipo, urgência)
- **US-CH-004:** chamado a 75% do SLA dispara notificação ao atendente; 100% escala pro gerente
- **US-CH-005:** atendente converte chamado em OS preservando histórico (`os_origem`)
- **US-CH-006:** atendente fecha chamado sem OS com razão obrigatória
- **US-CH-007:** gerente vê fila de SLA estourando em uma tela (mapa de calor)
- **US-CH-008:** cliente recebe link WhatsApp pra acompanhar chamado

## 7. Métricas

Ver `metricas.md`. Primárias: tempo médio de triagem, % SLA cumprido, % chamados duplicados detectados.

## 8. NFR

- Triagem deve completar em < 30s (UI otimizada — atalhos teclado + valores default)
- WCAG AA (INV-016)
- LGPD: número WhatsApp do cliente é dado pessoal — mascarar exibições conforme RAT-03

## 9. Glossário

Ver `glossario.md`.

## 10. Como evolui

US nova → próximo `US-CH-NNN`.
