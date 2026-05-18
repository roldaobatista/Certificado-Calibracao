---
owner: roldao
revisado_em: 2026-05-17
proximo_review: 2026-08-17
status: draft
modulo: os
dominio: operacao
diataxis: explanation
audiencia: agente
---

# PRD — Módulo OS (Ordens de Serviço)

## 1. O que este módulo é

Núcleo operacional do produto: registra todo trabalho a executar (calibração, manutenção, instalação, verificação INMETRO, vistoria), controla a máquina de estados da execução, dispara eventos pros demais domínios (Metrologia, Financeiro, Comercial) e garante rastreabilidade ISO 17025 + LGPD. **OP3 é a maior cobertura do MVP-1** (~75% mapeado em discovery).

## 2. Por que este módulo existe

Cobre BIG-01 (não perder informação entre WhatsApp/planilha/sistema), BIG-05 (técnico em campo sem rede) e parte de BIG-08 (frota+UMC+caixa). Hoje 90% das empresas-alvo controlam OS em Excel + WhatsApp — Dor #01, #05, #20 ranqueadas em `discovery/dores-mapeadas.md`.

## 3. Personas

`../personas.md` — P-OP-01 (técnico de campo), P-OP-02 (metrologista bancada), P-OP-03 (atendente), P-OP-04 (gerente operacional), P-OP-05 (cliente final).

## 4. Escopo MVP-1

- CRUD de OS com tipos (calibração, manutenção, instalação, verif INMETRO, vistoria)
- Máquina de estados explícita (INV-027) com transições validadas
- Checklist obrigatório por tipo (foto, assinatura, padrão usado, peça)
- Atribuição a técnico + integração com Agenda
- App mobile offline-first (ver ADR-0004)
- Eventos `OSAberta`, `OSAtribuida`, `OSConcluida`, `OSCancelada`
- Reabertura cria **nova OS** referenciando a anterior
- Marcação de Não Conformidade (alimenta INV-012 em Metrologia)
- Geolocalização em OS de campo (LGPD RAT-07)
- Audit log de toda ação CRUD (RAT-08)

## 5. Non-goals MVP-1

- Roteirização inteligente da frota (vai pra MVP-2 — OP3.3)
- Cálculo automático de TCO da frota
- OCR de foto pra extrair leitura do instrumento
- Pagamento da OS direto pelo cliente (vai pra Financeiro)
- Customização do fluxo de OS por tenant (ANTI-11 — proibido)

## 6. User Stories (resumo)

- **US-OS-001:** abrir OS a partir de Orçamento aprovado (Comercial) → estado RASCUNHO
- **US-OS-002:** atribuir OS a técnico + validar agenda (INV-020 se UMC)
- **US-OS-003:** técnico inicia OS no mobile (offline ok) → EM_EXECUCAO
- **US-OS-004:** concluir OS com checklist completo → CONCLUIDA + dispara eventos
- **US-OS-005:** marcar NC na OS de calibração → bloqueia certificado (INV-012)
- **US-OS-006:** reabrir OS concluída → cria OS-filha **com rastreabilidade bidirecional**:
  - publica `OS.Reaberta(os_id=nova, os_origem_id=original, chamado_origem_id=opcional, motivo, garantia_procedente=bool)`
  - consumer `caixa-tecnico` marca despesas/adiantamentos da OS-mãe como "a reconciliar em fechamento de período" se garantia procedente
  - consumer `chamados` reabre chamado original (se existia) e vincula ao OS-filha
  - cliente externo é notificado via `portal-cliente` que sua reclamação virou retrabalho
  - INV-INT-010 (audit causation_id ligando OS-mãe + chamado + OS-filha)
- **US-OS-007:** cancelar OS com razão obrigatória → CANCELADA + libera agenda
- **US-OS-008:** gerente vê fila + redistribui OS quando técnico falta

Detalhes em `specs/` quando especificar feature a feature.

## 7. Métricas

Ver `metricas.md`. Primárias: % OS concluídas no prazo, tempo médio RASCUNHO→CONCLUIDA, taxa de retrabalho.

## 8. NFR

- Mobile funciona 100% offline; sync robusta (ADR-0004)
- Audit log imutável (INV-027 estado + RAT-08)
- Geolocalização opt-in com RIPD (LGPD RAT-07)
- WCAG 2.1 AA (INV-016)

## 9. Glossário

Ver `glossario.md`.

## 10. Como evolui

US nova → próximo ID `US-OS-NNN`. Mudança em AC implementado → ADR.
