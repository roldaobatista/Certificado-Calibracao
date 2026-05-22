---
owner: roldao
revisado_em: 2026-05-23
proximo_review: 2026-08-23
status: draft
modulo: os
dominio: operacao
diataxis: explanation
audiencia: agente
---

# PRD — Módulo OS (Ordens de Serviço)

> **Revisado em 2026-05-23 (ADR-0023):** 1 OS contém N **AtividadeDaOS** (cada atividade tem seu próprio tipo + checklist + ciclo de estado). Caso comum: cliente traz instrumento e pede "consertem e calibrem" → 1 OS com 2 atividades (manutenção corretiva + calibração). Detalhes em `docs/adr/0023-os-com-atividades.md` + `modelo-de-dominio.md`.

## 1. O que este módulo é

Núcleo operacional do produto: registra todo trabalho a executar para o cliente. A OS é o **container comercial/financeiro/atendimento** (1 cliente, 1 instrumento, 1 fatura, 1 link no portal); o trabalho técnico se divide em **N atividades** de tipos distintos (calibração, manutenção corretiva, manutenção preventiva, instalação, verificação INMETRO, vistoria). Controla a máquina de estados da execução, dispara eventos pros demais domínios (Metrologia, Financeiro, Comercial) e garante rastreabilidade ISO 17025 + LGPD. **OP3 é a maior cobertura do MVP-1** (~75% mapeado em discovery).

## 2. Por que este módulo existe

Cobre BIG-01 (não perder informação entre WhatsApp/planilha/sistema), BIG-05 (técnico em campo sem rede) e parte de BIG-08 (frota+UMC+caixa). Hoje 90% das empresas-alvo controlam OS em Excel + WhatsApp — Dor #01, #05, #20 ranqueadas em `discovery/dores-mapeadas.md`.

## 3. Personas

`../personas.md` — P-OP-01 (técnico de campo), P-OP-02 (metrologista bancada), P-OP-03 (atendente), P-OP-04 (gerente operacional), P-OP-05 (cliente final).

## 4. Escopo MVP-1

- CRUD de OS + CRUD de **AtividadeDaOS** (1:N, ADR-0023) com 6 tipos (calibração, manutenção corretiva, manutenção preventiva, instalação, verif INMETRO, vistoria)
- Caso combinado suportado nativamente (manutenção + calibração na mesma OS, 2 atividades ordenadas)
- Máquina de estados explícita (INV-027) — OS computa estado a partir das atividades (INV-OS-ATIV-001)
- Máquina de estados própria por atividade (PENDENTE → EM_EXECUCAO → CONCLUIDA/NAO_CONFORME/CANCELADA)
- Checklist obrigatório **por atividade** (depende do tipo da atividade, não da OS)
- Técnico executor pode variar entre atividades da mesma OS (metrologista calibra, mecânico conserta)
- Atribuição a técnico geral + integração com Agenda
- App mobile offline-first (ver ADR-0004)
- Eventos `OSAberta`, `OSAtribuida`, `OSConcluida`, `OSCancelada` + novos `AtividadeIniciada`, `AtividadeConcluida`, `AtividadeNaoConforme`
- Reabertura cria **nova OS** referenciando a anterior (reabertura granular por atividade fica Wave B)
- Marcação de Não Conformidade por atividade (NC em atividade tipo=calibracao alimenta INV-012)
- Geolocalização em OS de campo (LGPD RAT-07)
- Audit log de toda ação CRUD (RAT-08) — eventos da OS e das atividades

## 5. Non-goals MVP-1

- Roteirização inteligente da frota (vai pra MVP-2 — OP3.3)
- Cálculo automático de TCO da frota
- OCR de foto pra extrair leitura do instrumento
- Pagamento da OS direto pelo cliente (vai pra Financeiro)
- Customização do fluxo de OS por tenant (ANTI-11 — proibido)
- **Faturamento por atividade** — Wave B (MVP-1 fatura OS atômica)
- **Reabertura granular por atividade** — Wave B (MVP-1 reabre OS toda)
- **Atividades de tenants diferentes na mesma OS** — proibido (INV-OS-ATIV-002 + INV-TENANT-001)

## 6. User Stories (resumo)

- **US-OS-001:** abrir OS a partir de Orçamento aprovado (Comercial) → estado RASCUNHO **com N atividades em PENDENTE** (uma por item de serviço do orçamento)
- **US-OS-002:** atribuir OS a técnico + validar agenda (INV-020 se UMC). Técnicos executores por atividade podem ser definidos no mobile.
- **US-OS-003:** técnico inicia **atividade específica** no mobile (offline ok) → atividade em EM_EXECUCAO + OS migra pra EM_EXECUCAO na 1ª iniciada
- **US-OS-004:** concluir atividade com checklist próprio completo → atividade em CONCLUIDA + OS migra pra CONCLUIDA quando TODAS terminais (INV-OS-ATIV-001) + dispara eventos
- **US-OS-005:** marcar NC em atividade tipo=calibracao → bloqueia certificado (INV-012) **sem invalidar outras atividades concluídas da mesma OS**
- **US-OS-006:** reabrir OS concluída → cria OS-filha **com rastreabilidade bidirecional**:
  - publica `OS.Reaberta(os_id=nova, os_origem_id=original, chamado_origem_id=opcional, motivo, garantia_procedente=bool)`
  - consumer `caixa-tecnico` marca despesas/adiantamentos da OS-mãe como "a reconciliar em fechamento de período" se garantia procedente
  - consumer `chamados` reabre chamado original (se existia) e vincula ao OS-filha
  - cliente externo é notificado via `portal-cliente` que sua reclamação virou retrabalho
  - INV-INT-010 (audit causation_id ligando OS-mãe + chamado + OS-filha)
- **US-OS-007:** cancelar OS com razão obrigatória → CANCELADA + libera agenda + cascateia em atividades PENDENTE/EM_EXECUCAO
- **US-OS-008:** gerente vê fila + redistribui OS quando técnico falta
- **US-OS-009 (ADR-0023):** abrir OS combinada manutenção + calibração — atendente cadastra 1 OS com 2 atividades (manutenção corretiva sequência=1, calibração sequência=2). Calibração só pode iniciar após manutenção concluída (validação opcional por `sequencia`). Cliente vê 1 OS, 1 fatura, 2 etapas no portal.
- **US-OS-010 (ADR-0023):** adicionar atividade a OS em andamento — atendente/técnico identifica necessidade nova (ex: durante calibração descobre que precisa de manutenção corretiva), adiciona atividade em PENDENTE sem fechar a OS.

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
