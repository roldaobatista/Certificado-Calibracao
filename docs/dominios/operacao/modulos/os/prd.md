---
owner: roldao
revisado_em: 2026-05-23
proximo_review: 2026-08-23
status: stable
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

## 6. User Stories (com AC binários — INV-OS-ATIV-*)

### US-OS-001 — Abrir OS a partir de Orçamento aprovado

**Como** P-OP-03 atendente, **quero** que orçamento aprovado vire OS automaticamente, **para** não digitar dados 2x.

- **AC-OS-001-1:** GIVEN Orcamento.Aprovado consumido pelo módulo OS, WHEN `abrirOS` executa, THEN cria OS em RASCUNHO + N AtividadeDaOS em PENDENTE (uma por item de serviço do orçamento, com `tipo` derivado do catálogo) + publica `OSAberta` com payload `{tenant_id, os_id, cliente_id_hash, atividades_planejadas: [{atividade_id, tipo, sequencia}], correlation_id, abertura_at}`.
- **AC-OS-001-2:** GIVEN orçamento sem itens, WHEN tenta abrir OS, THEN retorna 400 `OrcamentoSemItensCarrinho`.
- **AC-OS-001-3:** GIVEN payload com `Idempotency-Key`, WHEN replay ocorre, THEN retorna mesma OS (não cria duplicada).
- **AC-OS-001-4:** GIVEN orçamento cross-tenant, WHEN tenta abrir, THEN bloqueia com 422 `OrcamentoCrossTenant` (INV-TENANT-001).
- **Invariantes:** INV-027, INV-026, INV-TENANT-001, INV-OS-ATIV-002, INV-OS-ATIV-003.

### US-OS-002 — Atribuir técnico geral + executor por atividade

**Como** P-OP-04 gerente, **quero** atribuir técnico geral da OS + executores por atividade, **para** ter mecânico em manutenção e metrologista em calibração na mesma OS.

- **AC-OS-002-1:** GIVEN OS em RASCUNHO + técnico tem agenda válida (INV-020 se UMC), WHEN `atribuirTecnico` executa, THEN OS vira AGENDADA + publica `OSAtribuida`.
- **AC-OS-002-2:** GIVEN UMC + agenda viola Lei 13.103, WHEN tenta atribuir, THEN bloqueia com 422 + razão.
- **AC-OS-002-3:** GIVEN atividade com `tecnico_executor_id` definido, WHEN `iniciarAtividade` executa, THEN só o executor designado pode iniciar (RBAC + INV-AUTHZ-001).
- **Invariantes:** INV-020, INV-AUTHZ-001, INV-027.

### US-OS-003 — Iniciar atividade no mobile (offline-first)

**Como** P-OP-01 técnico, **quero** iniciar atividade específica no app, **para** trabalhar offline sem perder dados.

- **AC-OS-003-1:** GIVEN atividade em PENDENTE, OS em AGENDADA, usuário = `atividade.tecnico_executor_id`, WHEN `iniciarAtividade` executa, THEN atividade vira EM_EXECUCAO + OS vira EM_EXECUCAO se for a 1ª + publica `AtividadeIniciada` com `client_event_id`.
- **AC-OS-003-2:** GIVEN POST sem `Idempotency-Key`, WHEN tenta iniciar, THEN 400 `IdempotencyKeyAusente`.
- **AC-OS-003-3:** GIVEN replay (mesmo `client_event_id` + `Idempotency-Key`), WHEN servidor recebe, THEN retorna mesma resposta + não duplica evento (IDEMP-001).
- **AC-OS-003-4:** GIVEN gate de `sequencia` ativo + atividade N-1 não terminal, WHEN tenta iniciar atividade N, THEN 412 `SequenciaPendente`.
- **AC-OS-003-5:** GIVEN geo opt-in ativo, WHEN inicia, THEN captura `geo` com precisão limitada (INV-OS-GEO-001).
- **Invariantes:** INV-OS-ATIV-002, INV-OS-ATIV-005, IDEMP-001, INV-OS-GEO-001, RAT-07.

### US-OS-004 — Concluir atividade

**Como** P-OP-01 ou P-OP-02, **quero** concluir atividade com checklist próprio, **para** liberar a próxima.

- **AC-OS-004-1:** GIVEN atividade em EM_EXECUCAO + `ChecklistDaAtividade` 100% preenchido + `AceiteAtividade` gravado quando exigido pelo tipo, WHEN `concluirAtividade` executa, THEN atividade vira CONCLUIDA + publica `AtividadeConcluida`.
- **AC-OS-004-2:** GIVEN checklist incompleto, WHEN tenta concluir, THEN 412 `ChecklistIncompleto: [campo_X, campo_Y]`.
- **AC-OS-004-3:** GIVEN TODAS atividades em estado terminal (CONCLUIDA/NAO_CONFORME/CANCELADA), WHEN última atividade conclui, THEN OS vira CONCLUIDA + publica `OSConcluida` com `tipo_predominante` calculado.
- **AC-OS-004-4:** GIVEN executor ≠ usuário autenticado, WHEN tenta concluir, THEN 403 `NaoEExecutor` (INV-OS-ATIV-005).
- **Invariantes:** INV-OS-ATIV-001, INV-OS-ATIV-005, INV-027, IDEMP-001.

### US-OS-005 — Marcar NC em atividade tipo=calibracao

**Como** P-OP-02 metrologista ou RT, **quero** marcar NC em atividade de calibração, **para** bloquear certificado sem invalidar outras atividades.

- **AC-OS-005-1:** GIVEN atividade tipo=calibracao em EM_EXECUCAO, WHEN `marcarNaoConformidadeAtividade` executa com `razao_nao_conformidade` (≥30 chars, anti-PII via INV-OS-TXT-001), THEN atividade vira NAO_CONFORME + publica `AtividadeNaoConforme` + bloqueia emissão certificado (INV-012).
- **AC-OS-005-2:** GIVEN OS com múltiplas atividades + 1 marcada NC, WHEN consultar OS, THEN `os.nao_conformidade_global=true` mas outras atividades permanecem em estados próprios.
- **AC-OS-005-3:** GIVEN NC com causa-raiz registrada + ação corretiva executada + eficácia verificada (ciclo CAPA TEMA-B.2), WHEN `resolverNC` executa, THEN atividade volta para EM_EXECUCAO + publica `AtividadeNCResolvida` + libera certificado.
- **AC-OS-005-4:** GIVEN `razao_nao_conformidade` com PII, WHEN tenta marcar, THEN 400 `TextoComPII` (INV-OS-TXT-001).
- **Invariantes:** INV-012, INV-OS-ATIV-001, INV-OS-TXT-001.

### US-OS-006 — Reabrir OS concluída

**Como** P-OP-04 gerente, **quero** reabrir OS concluída com rastreabilidade, **para** atender reclamação de garantia.

- **AC-OS-006-1:** GIVEN OS em CONCLUIDA/FATURADA/PAGA, WHEN `reabrirOS(motivo, garantia_procedente)` executa, THEN cria NOVA OS com `os_origem_id` + clona atividades (PENDENTE + sequencia=1) conforme TEMA-E.10 + publica `OS.Reaberta(os_id=nova, os_origem_id=original, chamado_origem_id, motivo, garantia_procedente, correlation_id)`.
- **AC-OS-006-2:** GIVEN reabertura, WHEN OS-filha criada, THEN `OS-filha.tenant_id == OS-mae.tenant_id` (INV-OS-ATIV-005 cross-tenant) — senão 422 `ReaberturaCrossTenant`.
- **AC-OS-006-3:** GIVEN `garantia_procedente=true`, WHEN consumer `caixa-tecnico` recebe `OS.Reaberta`, THEN marca despesas/adiantamentos da OS-mãe como "a reconciliar em fechamento de período".
- **AC-OS-006-4:** GIVEN chamado_origem_id presente, WHEN consumer `chamados` recebe, THEN reabre chamado original e vincula à OS-filha.
- **AC-OS-006-5:** GIVEN portal-cliente plugado, WHEN OS reaberta, THEN cliente externo é notificado.
- **Invariantes:** INV-INT-010, INV-OS-ATIV-002, INV-OS-ATIV-005, INV-027.

### US-OS-007 — Cancelar OS

**Como** P-OP-04 gerente, **quero** cancelar OS com razão obrigatória, **para** liberar agenda e cascatear atividades.

- **AC-OS-007-1:** GIVEN OS em RASCUNHO/AGENDADA/EM_EXECUCAO + `razao_cancelamento` (≥30 chars, anti-PII), WHEN `cancelarOS` executa, THEN OS vira CANCELADA + cascateia atividades em PENDENTE/EM_EXECUCAO pra CANCELADA + publica `OSCancelada` + libera agenda.
- **AC-OS-007-2:** GIVEN OS em FATURADA/PAGA, WHEN tenta cancelar, THEN 412 `EstadoTerminalProibeCancelamento`.
- **AC-OS-007-3:** GIVEN cancelamento, WHEN cascateia atividades, THEN atividades CONCLUIDA da mesma OS permanecem CONCLUIDA (não retornam).
- **Invariantes:** INV-027, INV-OS-TXT-001.

### US-OS-008 — Cancelar atividade individualmente (MED-6 tech-lead)

**Como** P-OP-04 gerente, **quero** cancelar UMA atividade da OS sem cancelar a OS toda, **para** ajustar escopo (ex: cliente desistiu da manutenção mas mantém calibração).

- **AC-OS-008-1:** GIVEN atividade em PENDENTE/EM_EXECUCAO + `razao_cancelamento`, WHEN `cancelarAtividade(atividade_id, razao)` executa, THEN atividade vira CANCELADA + publica `AtividadeCancelada`.
- **AC-OS-008-2:** GIVEN atividade cancelada + ela era a única não-terminal, WHEN cancela, THEN OS vira CONCLUIDA via INV-OS-ATIV-001 (com `tipo_predominante` recalculado).
- **AC-OS-008-3:** GIVEN OS sem nenhuma atividade ativa (todas canceladas), WHEN cancela última, THEN OS vira CANCELADA (não CONCLUIDA — sem trabalho efetivo).
- **Invariantes:** INV-OS-ATIV-001, INV-OS-TXT-001.

### US-OS-009 — OS combinada (ADR-0023)

**Como** P-OP-03 atendente, **quero** cadastrar 1 OS com manutenção + calibração, **para** atender "consertem e calibrem".

- **AC-OS-009-1:** GIVEN cliente traz instrumento com defeito + pede calibração, WHEN atendente cadastra, THEN cria 1 OS com 2 AtividadeDaOS (`manutencao_corretiva` sequencia=1 + `calibracao` sequencia=2).
- **AC-OS-009-2:** GIVEN OS combinada criada + gate de sequência ativo, WHEN tenta iniciar atividade 2 (calibração) antes da atividade 1 (manutenção) estar em estado terminal, THEN 412 `SequenciaPendente`.
- **AC-OS-009-3:** GIVEN atividade 1 CONCLUIDA, WHEN atividade 2 inicia, THEN gate de sequência libera.
- **AC-OS-009-4:** GIVEN atividade 1 NAO_CONFORME (manutenção falhou), WHEN consulta gate de sequência, THEN atividade 2 fica bloqueada até resolução NC ou cancelamento atividade 1.
- **AC-OS-009-5:** GIVEN OS combinada concluída, WHEN cliente acessa portal, THEN vê 1 OS com 2 etapas + 2 `AceiteAtividade` separados + 1 fatura.
- **Invariantes:** INV-OS-ATIV-001, INV-OS-ATIV-003.

### US-OS-010 — Adicionar atividade a OS em andamento (ADR-0023)

**Como** P-OP-01 técnico ou P-OP-04 gerente, **quero** adicionar atividade durante a execução, **para** cobrir necessidade detectada (ex: durante calibração descobre que precisa manutenção).

- **AC-OS-010-1:** GIVEN OS em RASCUNHO/AGENDADA/EM_EXECUCAO + `tipo` válido + tenant ativo, WHEN `adicionarAtividade(os_id, tipo, sequencia)` executa, THEN nova atividade em PENDENTE + publica `AtividadeAdicionada`.
- **AC-OS-010-2:** GIVEN OS em CONCLUIDA/FATURADA/PAGA, WHEN tenta adicionar, THEN 412 `OSEmEstadoTerminal — abra reabertura`.
- **AC-OS-010-3:** GIVEN adicionar atividade tipo=calibracao a OS já em andamento, WHEN executor não é metrologista, THEN 403 `PerfilSemCompetencia` (INV-AUTHZ-001).
- **Invariantes:** INV-OS-ATIV-001, INV-OS-ATIV-003.

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
