---
owner: roldao
revisado-em: 2026-05-23
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

> Numeração canônica (Onda 6 — auditor 5): US-OS-001..010 conforme abaixo. Stub do faseamento `M3-os/spec.md` §4 deve refletir esta lista.

**Como** P-OP-03 atendente, **quero** que orçamento aprovado vire OS automaticamente, **para** não digitar dados 2x.

- **AC-OS-001-1:** GIVEN Orcamento.Aprovado consumido pelo módulo OS, WHEN `abrirOS` executa, THEN cria OS em RASCUNHO + N AtividadeDaOS em PENDENTE (uma por item de serviço do orçamento, com `tipo` derivado do catálogo) + publica `OSAberta` com payload `{tenant_id, os_id, cliente_id_hash, atividades_planejadas: [{atividade_id, tipo, sequencia}], correlation_id, abertura_at}`.
- **AC-OS-001-2:** GIVEN orçamento sem itens, WHEN tenta abrir OS, THEN retorna 400 `OrcamentoSemItensCarrinho`.
- **AC-OS-001-3:** GIVEN payload com `Idempotency-Key`, WHEN replay ocorre, THEN retorna mesma OS (não cria duplicada).
- **AC-OS-001-4:** GIVEN orçamento cross-tenant, WHEN tenta abrir, THEN bloqueia com 422 `OrcamentoCrossTenant` (INV-TENANT-001).
- **AC-OS-001-5 (Onda 6 auditor 5 — INV-OS-EQP-001):** GIVEN equipamento em estado `BAIXADO/DESCARTADO`, WHEN tenta criar OS, THEN bloqueia com 422 `EquipamentoBaixadoEmOS`.
<!-- frontmatter-revisado-em: skip -- edit preserva frontmatter no topo -->
- **AC-OS-001-6 (Onda 6 auditor 5 — INV-OS-ANON-001):** GIVEN cliente com OS em RASCUNHO/AGENDADA/EM_EXECUCAO + módulo Clientes recebe pedido de anonimização (Zona A/B ADR-0021), WHEN consulta dependências OS, THEN bloqueia com 409 `AnonimizacaoBloqueadaPorOSAberta` + emite `AnonimizacaoBloqueada` com payload `{cliente_id_hash, motivo=os_aberta, os_ids_bloqueantes}`.
- **AC-OS-001-7 (P3 RBC P-OS-R2 — cl. 7.1 análise crítica):** GIVEN abertura via orçamento, WHEN `abrirOS` executa, THEN copia `orcamento.analise_critica_id` + hash do snapshot pra OS (`analise_critica_snapshot_hash` — INV-DOC-CANON-001); se orçamento veio SEM análise crítica registrada (`orcamento.analise_critica IS NULL`) → 412 `OrcamentoSemAnaliseCritica` (INV-OS-ANAL-001).
- **AC-OS-001-8 (P3 RBC P-OS-R4 — cl. 7.5 manuseio de itens):** GIVEN OS de bancada (equipamento no laboratório), WHEN `abrirOS` executa, THEN exige `equipamento_recebimento_id` vinculado ao recebimento mais recente em estado `recebido_pendente_inspecao | em_calibracao` daquele equipamento + cliente; ausente → 412 `EquipamentoSemRecebimentoRegistrado`. Para OS de campo (`TipoAtividadeConfig.executa_em_campo=true`) o campo permanece NULL e condição é registrada em `ChecklistDaAtividade` in loco.
- **Invariantes:** INV-027, INV-026, INV-TENANT-001, INV-OS-ATIV-002, INV-OS-ATIV-003, INV-OS-EQP-001, INV-OS-ANON-001, INV-OS-ANAL-001, INV-OS-NUM-001.

### US-OS-002 — Adicionar atividade a OS (cadastro inicial ou em andamento)

> Renumerado em Onda 6 auditor 5: US-OS-002 = adicionarAtividade. Atribuir técnico vira US-OS-002b (mantendo compat com PRD pré-Onda 6 — não-quebrante).

**Como** P-OP-03 atendente ou P-OP-04 gerente, **quero** adicionar atividade a uma OS (no cadastro inicial ou durante execução), **para** cobrir necessidade detectada.

- **AC-OS-002-1:** GIVEN OS em RASCUNHO/AGENDADA/EM_EXECUCAO + `tipo` válido (INV-OS-ATIV-003) + tenant ativo, WHEN `adicionarAtividade(os_id, tipo, sequencia)` executa, THEN nova atividade em PENDENTE + publica `AtividadeAdicionada`.
- **AC-OS-002-2:** GIVEN OS em CONCLUIDA/FATURADA/PAGA, WHEN tenta adicionar, THEN 412 `OSEmEstadoTerminal — abra reabertura`.
- **AC-OS-002-3 (Onda 6 auditor 5 — A6 RT obrigatório):** GIVEN `tipo` com `TipoAtividadeConfig.requer_competencia_rt=true` (calibracao, verificacao_inmetro), WHEN servidor valida, THEN executa predicate `tenant_tem_rt_ativo_competencia(grandeza)` (INV-CAL-RT-001 + ADR-0022); se falso → 422 `TenantSemRTAtivo: [grandeza]`.
- **AC-OS-002-4:** GIVEN `sequencia` ≤ menor `sequencia` em estado terminal CONCLUIDA, WHEN servidor recebe, THEN 412 `SequenciaInvalidaPosTerminal` (preserva linearidade).
- **Invariantes:** INV-OS-ATIV-001, INV-OS-ATIV-003, INV-CAL-RT-001.

### US-OS-002b — Atribuir técnico geral + executor por atividade

**Como** P-OP-04 gerente, **quero** atribuir técnico geral da OS + executores por atividade, **para** ter mecânico em manutenção e metrologista em calibração na mesma OS.

- **AC-OS-002-1:** GIVEN OS em RASCUNHO + técnico tem agenda válida (INV-020 se UMC), WHEN `atribuirTecnico` executa, THEN OS vira AGENDADA + publica `OSAtribuida`.
- **AC-OS-002-2:** GIVEN UMC + agenda viola Lei 13.103, WHEN tenta atribuir, THEN bloqueia com 422 + razão.
<!-- frontmatter-revisado-em: skip -- edit preserva frontmatter no topo -->
- **AC-OS-002-3:** GIVEN atividade com `tecnico_executor_id` definido, WHEN `iniciarAtividade` executa, THEN só o executor designado pode iniciar (RBAC + INV-AUTHZ-001).
- **AC-OS-002b-4 (P3 RBC P-OS-R1 — cl. 6.2 competência executor):** GIVEN `tipo IN (calibracao, verificacao_inmetro)` no momento da atribuição inicial, WHEN servidor valida `tecnico_executor_id`, THEN executa predicate `rt_competencia_cobre(tecnico_executor_id, grandeza, data_atual)` (ADR-0022); se falso → 422 `ExecutorSemCompetencia: [grandeza]` (INV-OS-ATIV-005-EXEC-COMP).
- **Invariantes:** INV-020, INV-AUTHZ-001, INV-027, INV-OS-ATIV-005-EXEC-COMP.

### US-OS-003 — Iniciar atividade no mobile (offline-first)

**Como** P-OP-01 técnico, **quero** iniciar atividade específica no app, **para** trabalhar offline sem perder dados.

- **AC-OS-003-1:** GIVEN atividade em PENDENTE, OS em AGENDADA, usuário = `atividade.tecnico_executor_id`, WHEN `iniciarAtividade` executa, THEN atividade vira EM_EXECUCAO + OS vira EM_EXECUCAO se for a 1ª + publica `AtividadeIniciada` com `client_event_id`.
- **AC-OS-003-2:** GIVEN POST sem `Idempotency-Key`, WHEN tenta iniciar, THEN 400 `IdempotencyKeyAusente`.
- **AC-OS-003-3:** GIVEN replay (mesmo `client_event_id` + `Idempotency-Key`), WHEN servidor recebe, THEN retorna mesma resposta + não duplica evento (IDEMP-001).
- **AC-OS-003-4:** GIVEN gate de `sequencia` ativo + atividade N-1 não terminal, WHEN tenta iniciar atividade N, THEN 412 `SequenciaPendente`.
<!-- frontmatter-revisado-em: skip -- edit preserva frontmatter no topo -->
- **AC-OS-003-5:** GIVEN geo opt-in ativo, WHEN inicia, THEN captura `geo` com precisão limitada (INV-OS-GEO-001).
- **AC-OS-003-6 (P3 RBC P-OS-R1 — cl. 6.2 competência executor no início):** GIVEN `tipo IN (calibracao, verificacao_inmetro)` no momento de iniciar, WHEN servidor valida, THEN re-executa predicate `rt_competencia_cobre(usuario, grandeza, data_inicio)` (competência pode ter revogado entre atribuição e início — vigência ADR-0030); se falso → 422 `ExecutorSemCompetenciaNaData` (INV-OS-ATIV-005-EXEC-COMP).
- **Invariantes:** INV-OS-ATIV-002, INV-OS-ATIV-005, INV-OS-ATIV-005-EXEC-COMP, IDEMP-001, INV-OS-GEO-001, RAT-07.

### US-OS-004 — Concluir atividade

**Como** P-OP-01 ou P-OP-02, **quero** concluir atividade com checklist próprio, **para** liberar a próxima.

- **AC-OS-004-1:** GIVEN atividade em EM_EXECUCAO + `ChecklistDaAtividade` 100% preenchido + `AceiteAtividade` gravado quando exigido pelo tipo, WHEN `concluirAtividade` executa, THEN atividade vira CONCLUIDA + publica `AtividadeConcluida`.
- **AC-OS-004-2:** GIVEN checklist incompleto, WHEN tenta concluir, THEN 412 `ChecklistIncompleto: [campo_X, campo_Y]`.
- **AC-OS-004-3:** GIVEN TODAS atividades em estado terminal (CONCLUIDA/NAO_CONFORME/CANCELADA), WHEN última atividade conclui, THEN OS vira CONCLUIDA + publica `OSConcluida` com `tipo_predominante` calculado (regra de empate: `calibracao` sempre vence — alimenta KPI ISO 17025; vide modelo-de-dominio.md).
- **AC-OS-004-4:** GIVEN executor ≠ usuário autenticado, WHEN tenta concluir, THEN 403 `NaoEExecutor` (INV-OS-ATIV-005).
- **AC-OS-004-5 (Onda 6 auditor 5 — INV-OS-CAL-LINK-001):** GIVEN atividade `tipo=calibracao` CONCLUIDA sem FK reversa `Calibracao.atividade_os_id` em ≤24h, WHEN watchdog `os-calibracao-link-watchdog` consulta, THEN dispara alerta P2 ao RT + gerente; após 72h cria NC automática `NaoConformidade.tipo=link_calibracao_faltando` + bloqueia emissão de certificado.
<!-- frontmatter-revisado-em: skip -- edit preserva frontmatter no topo -->
- **AC-OS-004-6 (Onda 6 auditor 5 — notificação):** GIVEN atividade CONCLUIDA, WHEN servidor processa, THEN publica `AtividadeConcluida` + portal-cliente recebe notificação + OmniChannel envia se `cliente.opt_in_whatsapp=true`. Payload de `AtividadeConcluida` explicita `tecnico_executor_id` + `consentimento_id` (consumer M4 valida independência ADR-0026 — P-OS-R7).
- **AC-OS-004-7 (P3 advogado P-OS-A1 — consentimento art. 11 antes de aceite):** GIVEN tela de aceite renderizada com texto canônico de consentimento art. 11 LGPD + botão "concordo e assino" SEPARADO de "concluir", WHEN cliente toca em concordar, THEN cria `ConsentimentoBiometriaTouch` ANTES de `AceiteAtividade` (FK 1:1, INV-OS-CONSBIO-001); sem consentimento → 412 `ConsentimentoBiometriaAusente`. Texto canônico: `docs/conformidade/comum/termos/consentimento-biometria-touch.md` (REQUER OAB — GATE-OS-CONSBIO-TEXTO-OAB).
- **Invariantes:** INV-OS-ATIV-001, INV-OS-ATIV-005, INV-027, IDEMP-001, INV-OS-CAL-LINK-001, INV-OS-CONSBIO-001.

### US-OS-005 — Marcar NC em atividade tipo=calibracao

**Como** P-OP-02 metrologista ou RT, **quero** marcar NC em atividade de calibração, **para** bloquear certificado sem invalidar outras atividades.

- **AC-OS-005-1:** GIVEN atividade tipo=calibracao em EM_EXECUCAO, WHEN `marcarNaoConformidadeAtividade` executa com `razao_nao_conformidade` (≥30 chars, anti-PII via INV-OS-TXT-001), THEN atividade vira NAO_CONFORME + publica `AtividadeNaoConforme` + bloqueia emissão certificado (INV-012).
- **AC-OS-005-2:** GIVEN OS com múltiplas atividades + 1 marcada NC, WHEN consultar OS, THEN `os.nao_conformidade_global=true` mas outras atividades permanecem em estados próprios.
- **AC-OS-005-3:** GIVEN NC com causa-raiz registrada + ação corretiva executada + eficácia verificada (ciclo CAPA TEMA-B.2), WHEN `resolverNC` executa, THEN atividade volta para EM_EXECUCAO + publica `AtividadeNCResolvida` + libera certificado.
<!-- frontmatter-revisado-em: skip -- edit preserva frontmatter no topo -->
- **AC-OS-005-4:** GIVEN `razao_nao_conformidade` com PII, WHEN tenta marcar, THEN 400 `TextoComPII` (INV-OS-TXT-001).
- **AC-OS-005-5 (P3 RBC P-OS-R5 — cl. 8.7 ciclo CAPA completo):** GIVEN NC marcada, WHEN `resolverNC` executa, THEN exige TODOS de: `causa_raiz_hash` (anti-PII INV-OS-TXT-001), `acao_corretiva_descricao_hash` (anti-PII), `eficacia_verificada_em ≠ NULL`, `eficacia_verificada_por_user_id ≠ NULL`; ausente → 412 `CAPAIncompleto`. FK opcional `registro_capa_id` preenchida pelo consumer reverso quando módulo qualidade Wave B nascer (GATE-RBC-CAPA-1).
- **Invariantes:** INV-012, INV-OS-ATIV-001, INV-OS-TXT-001.

### US-OS-006 — Reabrir OS concluída

**Como** P-OP-04 gerente, **quero** reabrir OS concluída com rastreabilidade, **para** atender reclamação de garantia.

- **AC-OS-006-1:** GIVEN OS em CONCLUIDA/FATURADA/PAGA, WHEN `reabrirOS(motivo, garantia_procedente)` executa, THEN cria NOVA OS com `os_origem_id` + clona atividades (PENDENTE + sequencia=1) conforme TEMA-E.10 + publica `OS.Reaberta(os_id=nova, os_origem_id=original, chamado_origem_id, motivo, garantia_procedente, correlation_id)`.
- **AC-OS-006-2:** GIVEN reabertura, WHEN OS-filha criada, THEN `OS-filha.tenant_id == OS-mae.tenant_id` (INV-OS-ATIV-005 cross-tenant) — senão 422 `ReaberturaCrossTenant`.
- **AC-OS-006-3:** GIVEN `garantia_procedente=true`, WHEN consumer `caixa-tecnico` recebe `OS.Reaberta`, THEN marca despesas/adiantamentos da OS-mãe como "a reconciliar em fechamento de período".
- **AC-OS-006-4:** GIVEN chamado_origem_id presente, WHEN consumer `chamados` recebe, THEN reabre chamado original e vincula à OS-filha.
- **AC-OS-006-5:** GIVEN portal-cliente plugado, WHEN OS reaberta, THEN cliente externo é notificado.
- **AC-OS-006-6 (Onda 6 auditor 5 — INV-OS-SUC-001):** GIVEN OS-mãe pertence a cliente anonimizado (Zona A/B ADR-0021) + flag `sucessao_societaria_id` informada, WHEN cria OS-filha, THEN preserva `cliente_id_hash` (referência audit) + grava `sucessao_societaria_id` (FK pra registro M&A) + OS-filha vai pra `cliente_id` sucessor.
- **AC-OS-006-7 (Onda 6 auditor 5 — bloqueio sem sucessão):** GIVEN OS-mãe em cliente anonimizado SEM `sucessao_societaria_id`, WHEN tenta reabrir, THEN 412 `ClienteAnonimizadoSemSucessao`.
- **Invariantes:** INV-INT-010, INV-OS-ATIV-002, INV-OS-ATIV-005, INV-027, INV-OS-SUC-001.

### US-OS-007 — Cancelar OS

**Como** P-OP-04 gerente, **quero** cancelar OS com razão obrigatória, **para** liberar agenda e cascatear atividades.

- **AC-OS-007-1:** GIVEN OS em RASCUNHO/AGENDADA/EM_EXECUCAO + `razao_cancelamento` (≥30 chars, anti-PII), WHEN `cancelarOS` executa, THEN OS vira CANCELADA + cascateia atividades em PENDENTE/EM_EXECUCAO pra CANCELADA + publica `OSCancelada` + libera agenda.
- **AC-OS-007-2:** GIVEN OS em FATURADA/PAGA, WHEN tenta cancelar, THEN 412 `EstadoTerminalProibeCancelamento`.
<!-- frontmatter-revisado-em: skip -- edit preserva frontmatter no topo -->
- **AC-OS-007-3:** GIVEN cancelamento, WHEN cascateia atividades, THEN atividades CONCLUIDA da mesma OS permanecem CONCLUIDA (não retornam).
- **AC-OS-007-4 (Onda 6 auditor 5 — SLA):** GIVEN OS com SLA contratual (`SLA.prioridade=alta|emergencia`), WHEN cancela, THEN dispara consumer `comercial/sla-breach` registrando descumprimento; cliente recebe notificação via portal + OmniChannel se opt-in.
- **Invariantes:** INV-027, INV-OS-TXT-001.

### US-OS-008 — Cancelar atividade individualmente (MED-6 tech-lead)

**Como** P-OP-04 gerente, **quero** cancelar UMA atividade da OS sem cancelar a OS toda, **para** ajustar escopo (ex: cliente desistiu da manutenção mas mantém calibração).

- **AC-OS-008-1:** GIVEN atividade em PENDENTE/EM_EXECUCAO + `razao_cancelamento`, WHEN `cancelarAtividade(atividade_id, razao)` executa, THEN atividade vira CANCELADA + publica `AtividadeCancelada`.
- **AC-OS-008-2:** GIVEN atividade cancelada + ela era a única não-terminal, WHEN cancela, THEN OS vira CONCLUIDA via INV-OS-ATIV-001 (com `tipo_predominante` recalculado).
- **AC-OS-008-3:** GIVEN OS sem nenhuma atividade ativa (todas canceladas), WHEN cancela última, THEN OS vira CANCELADA (não CONCLUIDA — sem trabalho efetivo).
- **AC-OS-008-4 (ADR-0042 — Onda 6 auditor 5):** GIVEN atividade cancelada com sucesso, WHEN servidor processa, THEN recalcula `valor_faturavel = sum(atividades_não_canceladas.valor_unitario_snapshot)` + publica `OS.EscopoAlterado` com payload `{tenant_id, os_id, atividade_id_cancelada, valor_removido, valor_total_atualizado, motivo_hash, correlation_id}` → consumer `financeiro/contas-receber` atualiza `ContasReceber.valor` (se ainda não FATURADA) OR emite alerta NC fiscal manual (se já FATURADA — gate Wave B).
- **Invariantes:** INV-OS-ATIV-001, INV-OS-TXT-001, INV-OS-FAT-001.

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
<!-- frontmatter-revisado-em: skip -- edit preserva frontmatter no topo -->
- **AC-OS-010-4 (novo Onda 7D — NOVO-MÉD-2 produto R2):** GIVEN tentativa de adicionar atividade com `sequencia` ≤ menor `sequencia` em estado terminal CONCLUIDA, WHEN servidor recebe, THEN 412 `SequenciaInvalidaPosTerminal` — não permite voltar atrás criando atividade entre 2 terminais.
- **Invariantes:** INV-OS-ATIV-001, INV-OS-ATIV-003.

### US-OS-011 — Reagendar atividade (Onda 6 auditor 5 — A2 reagendamento)

**Como** P-OP-04 gerente, **quero** reagendar atividade sem cancelar a OS, **para** acomodar mudança de cronograma do cliente.

- **AC-OS-011-1:** GIVEN atividade em PENDENTE/AGENDADA + nova_data válida + motivo (≥30 chars, anti-PII INV-OS-TXT-001), WHEN `reagendarAtividade(atividade_id, nova_data, motivo)` executa, THEN atualiza `agendada_para` + grava `EventoDeOS.tipo=atividade_reagendada` com `motivo_hash`.
- **AC-OS-011-2:** GIVEN atividade EM_EXECUCAO, WHEN tenta reagendar, THEN 412 `AtividadeEmExecucaoNaoPodeReagendar`.
- **AC-OS-011-3:** GIVEN reagendamento OK, WHEN portal-cliente plugado, THEN notifica cliente "reagendada para [data]".
- **Invariantes:** INV-OS-TXT-001, INV-AUTHZ-001.

### US-OS-012 — Transferir técnico executor (Onda 6 auditor 5 — A2 troca técnico)

**Como** P-OP-04 gerente, **quero** transferir atividade para outro técnico, **para** cobrir falta/redistribuição.

- **AC-OS-012-1:** GIVEN atividade em PENDENTE/AGENDADA + novo técnico com agenda válida (INV-020 UMC se aplicável) + motivo (≥30 chars), WHEN `transferirTecnico(atividade_id, novo_tecnico_id, motivo)` executa, THEN atualiza `tecnico_executor_id` + grava `EventoDeOS.tipo=atividade_tecnico_transferido`.
- **AC-OS-012-2:** GIVEN `tipo IN (calibracao, verificacao_inmetro)` + novo técnico sem competência ativa pra grandeza, WHEN servidor valida, THEN 422 `TecnicoSemCompetencia` (INV-CAL-RT-001).
- **AC-OS-012-3:** GIVEN transferência OK, WHEN portal-cliente plugado, THEN notifica cliente "técnico [hash] atribuído".
- **Invariantes:** INV-AUTHZ-001, INV-CAL-RT-001, INV-OS-TXT-001.

### US-OS-013 — Dispensar aceite cliente (Onda 6 auditor 5 — A2)

**Como** P-OP-04 gerente, **quero** dispensar `AceiteAtividade` em situação excepcional (cliente recusa / ausente após no-show), **para** liberar conclusão técnica com rastreabilidade.

- **AC-OS-013-1:** GIVEN atividade em EM_EXECUCAO + motivo (≥30 chars, anti-PII) + termo PDF anexado, WHEN `dispensarAceiteCliente(atividade_id, motivo, termo_pdf_id)` executa, THEN cria `DispensaAceiteAtividade(atividade_id, motivo, autorizado_por_gerente_id=sessao.usuario.id, termo_pdf_id)`.
- **AC-OS-013-2:** GIVEN dispensa gravada, WHEN técnico chama `concluirAtividade`, THEN servidor aceita sem `AceiteAtividade` (consulta `DispensaAceiteAtividade` ativo).
- **AC-OS-013-3:** GIVEN usuário sessão sem papel gerente, WHEN tenta dispensar, THEN 403 `SemAutorizacaoGerencial`.
<!-- frontmatter-revisado-em: skip -- edit preserva frontmatter no topo -->
- **AC-OS-013-4:** GIVEN dispensa, WHEN certificado / fatura é gerada, THEN marca "aceite dispensado por gerência (ref: [dispensa_id_hash])". Rodapé inclui link público (QR) para o cliente consultar o termo PDF — direito à informação CDC art. 6º III.
- **AC-OS-013-5 (P3 advogado P-OS-A4 — termo formal CDC art. 39):** GIVEN dispensa solicitada, WHEN gerente confirma, THEN servidor gera `TermoDispensaAceite` a partir de template canonicalizado (INV-DOC-CANON-001) contendo OBRIGATORIAMENTE: (a) descrição objetiva da circunstância (3 cenários: recusa formal / ausência pós no-show registrado / impossibilidade técnica de captura); (b) referência ao no-show vinculado quando aplicável; (c) hash da foto de evidência (no-show ou recusa); (d) declaração de boa-fé do gerente; (e) **assinatura A3 do gerente** (não só sessão autenticada). Dispensa SEM precedente (sem no-show registrado nem recusa explícita gravada) → 412 `DispensaSemPrecedente`. **REQUER OAB:** modelo do `TermoDispensaAceite`.
- **Invariantes:** INV-AUTHZ-001, INV-OS-TXT-001, RAT-08.

### US-OS-014 — Marcar no-show de cliente (Onda 6 auditor 5 — A2)

**Como** P-OP-01 técnico, **quero** marcar quando cliente não comparece, **para** documentar visita perdida + cobrar deslocamento.

- **AC-OS-014-1:** GIVEN atividade em AGENDADA (campo) + foto evidencia + hora, WHEN `marcarNoShow(atividade_id, foto_evidencia, hora)` executa, THEN atividade permanece em PENDENTE + grava `EventoDeOS.tipo=no_show_cliente` + dispara consumer `caixa-tecnico` (gera custo deslocamento — Wave B `GATE-FIN-NOSHOW-COBR`).
<!-- frontmatter-revisado-em: skip -- edit preserva frontmatter no topo -->
- **AC-OS-014-2:** GIVEN no-show registrado, WHEN portal-cliente plugado, THEN notifica cliente "técnico esteve em [hash endereço]; reagende".
- **AC-OS-014-3 (P3 advogado P-OS-A5 — aviso terceiros na foto):** GIVEN captura de foto de no-show, WHEN técnico abre câmera, THEN UX exibe aviso "evite enquadrar pessoas; capture apenas a fachada e o número do imóvel" + campo `foto_no_show_avisos_terceiros_acknowledged BOOLEAN` que o técnico marca antes de salvar (audit do consentimento operador com a regra). Blur automático de rostos antes do upload fica em GATE-OS-FOTO-NOSHOW-BLUR Wave A2.
- **Invariantes:** RAT-07, RAT-08.

### US-OS-015 — Criar OS avulsa balcão (Onda 6 auditor 5 — M6 avulsa)

**Como** P-OP-03 atendente, **quero** cadastrar OS direto no balcão sem passar por orçamento, **para** atender cliente walk-in.

- **AC-OS-015-1:** GIVEN cliente + equipamento cadastrados + atividades a executar, WHEN `criarOSAvulsa(cliente_id, equipamento_id, atividades)` executa, THEN cria OS em RASCUNHO + N atividades em PENDENTE com `valor_unitario_snapshot` = preço da tabela vigente NA DATA (INV-CLI-PRICE-001 Onda 4).
- **AC-OS-015-2:** GIVEN tabela de preços sem entrada para o tipo de atividade, WHEN servidor valida, THEN 422 `PrecoTabelaAusente`.
- **AC-OS-015-3:** GIVEN sucesso, WHEN cliente assina, THEN portal-cliente gera link `os/avulsa/{id}` com QR pra acompanhamento.
- **Invariantes:** INV-026, INV-CLI-PRICE-001, INV-OS-ATIV-003.

### Apêndice — notificação ao cliente (Onda 6 auditor 5 — M7)

Para US-OS-004, US-OS-005, US-OS-006, US-OS-007 e US-OS-008: toda transição publica para o **portal-cliente** (sempre) + dispara **OmniChannel** (WhatsApp/e-mail) **se `cliente.opt_in_<canal>=true`**. Payload do canal externo NUNCA carrega PII em texto — só hashes + identificador da OS no portal.

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
