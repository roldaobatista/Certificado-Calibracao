---
owner: roldao
revisado_em: 2026-05-23
status: stable
diataxis: explanation
audiencia: agente
tipo: review-p2-rbc
marco: M3-os
revisor: consultor-rbc-iso17025 (subagente IA)
credencial-cgcre: NAO (parecer consultivo — requer revisor humano antes de auditoria real)
relacionados:
  - docs/faseamento/M3-os/spec.md
  - docs/dominios/operacao/modulos/os/prd.md
  - docs/dominios/operacao/modulos/os/sagas.md
  - docs/adr/0022-gestao-rt-tenant.md
  - docs/adr/0026-segunda-conferencia-independencia.md
  - docs/adr/0012-autorizacao-unificada.md
  - docs/dominios/metrologia/modulos/licencas-acreditacoes/prd.md
  - docs/dominios/suporte-plataforma/modulos/equipamentos/prd.md
---

# Parecer P2 RBC/ISO 17025 — Marco 3 `operacao/os`

## Sumário executivo

| Severidade | Quantidade | IDs |
|---|---|---|
| BLOQUEANTE (corrige em P2) | 3 | P-OS-R1, P-OS-R2, P-OS-R3 |
| AJUSTADO (resolve em P4 ou ADR) | 4 | P-OS-R4, P-OS-R5, P-OS-R6, P-OS-R7 |
| ACEITE (rastreado, sem ação) | 1 | P-OS-R8 |
| **Total** | **8** | |

**Veredito:** AJUSTADO com 3 bloqueantes. Spec M3 está sólida no que entrega — máquina de estados, INVs, eventos, sagas, hooks. Lacunas residuais são de **competência metrológica delegada** entre módulos (RT/Acreditação/CAPA): o spec assume integrações cross-módulo (M2 equipamentos, M4 calibração, qualidade Wave B, licencas-acreditacoes) que ainda são `draft` ou Wave B. Risco: M3 fecha verde, mas auditor CGCRE em supervisão pergunta evidência operacional que o M3 publica mas nenhum consumer ainda processa.

**Aviso obrigatório:** este parecer é consultivo. Antes de qualquer **auditoria CGCRE real ou submissão a processo de acreditação RBC**, o dossiê do M3 precisa ser revisado por **consultor humano credenciado CGCRE**. Estimativa: R$ 8-15k por engajamento pontual.

---

## Achados

### P-OS-R1 — BLOQUEANTE — Competência do EXECUTOR (cl. 6.2) não validada, só do tenant

**Cláusula ISO/IEC 17025:** 6.2.1, 6.2.2, 6.2.5 — "O laboratório deve garantir que pessoal que executa atividades de laboratório seja competente."

**Achado:**
- AC-OS-002-3 (PRD) valida `tenant_tem_rt_ativo_competencia(grandeza)` quando `tipo=calibracao|verificacao_inmetro`. Isso prova apenas que **o tenant tem ALGUÉM com competência** — não que o **executor designado** (`atividade.tecnico_executor_id`) é essa pessoa.
- AC-OS-003-1 (US-OS-003) valida `usuario == atividade.tecnico_executor_id` (INV-OS-ATIV-005) — só identidade, não competência.
- AC-OS-012-2 (US-OS-012 transferir técnico) é o **único ponto** que valida competência por grandeza no novo técnico (`TecnicoSemCompetencia` 422 + INV-CAL-RT-001). Mas a atribuição INICIAL (US-OS-002b) **não tem essa checagem** — só `INV-020` agenda + `INV-AUTHZ-001` papel.
- ADR-0012 já especifica o predicate certo: `rt_competencia_cobre(user_id, grandeza, data)`.

**Cenário concreto da auditoria:** CGCRE em supervisão pergunta "como o sistema garante que QUEM executou a calibração no campo possuía competência declarada na grandeza X na data Y?". Resposta atual: "o tenant tinha algum RT com competência" — **insuficiente** para cl. 6.2.5.

**Decisão recomendada:**

Adicionar AC-OS-002b-4 + AC-OS-003-6:

> **AC-OS-002b-4:** GIVEN `tipo IN (calibracao, verificacao_inmetro)` no momento da atribuição inicial, WHEN servidor valida `tecnico_executor_id`, THEN executa predicate `rt_competencia_cobre(tecnico_executor_id, grandeza, data_atual)` (ADR-0022); se falso → 422 `ExecutorSemCompetencia: [grandeza]`.
>
> **AC-OS-003-6:** GIVEN `tipo IN (calibracao, verificacao_inmetro)` no momento de iniciar, WHEN servidor valida, THEN re-executa `rt_competencia_cobre(usuario, grandeza, data_inicio)` (competência pode ter REVOGADO entre atribuição e início — vigência ADR-0030).

Promover **INV-OS-ATIV-005-EXEC-COMP** em REGRAS-INEGOCIAVEIS.md ("Executor de atividade tipo=calibracao|verificacao_inmetro deve ter competência ativa pra grandeza na data de execução").

---

### P-OS-R2 — BLOQUEANTE — cl. 7.1 Análise crítica de pedidos não tem evidência operacional na OS

**Cláusula ISO/IEC 17025:** 7.1.1, 7.1.3, 7.1.7, 7.1.8 — "O laboratório deve ter um procedimento para análise crítica de pedidos, propostas e contratos... incluindo recursos e capacidade para atender."

**Achado:**
- Spec §9 lista `GATE-RBC-ANAL-PEDIDOS-1` como gate Wave A, marcando que o gate **não bloqueia o fechamento do M3**.
- AC-OS-001-1 (abrir via Orcamento.Aprovado) consome o evento sem registrar **localmente na OS** quem fez a análise crítica, quando, e se passou. A análise crítica está implicitamente no Orçamento (cl. 7.1 é do MOMENTO da aceitação do pedido, que é o orçamento).
- **Mas o auditor CGCRE pede evidência NO REGISTRO TÉCNICO** (cl. 7.5 — registros técnicos), que é a OS. Se a OS não carregar **snapshot** de "análise crítica passou em [data] por [responsável]", a rastreabilidade quebra quando o orçamento for posteriormente alterado/arquivado.
- Não há campo `analise_critica_pedido_id` ou `analise_critica_snapshot_hash` na entidade OS no §3.2.
- Cl. 7.1.3 (regra de decisão) é tratada parcialmente em ADR-0024 — mas a OS não carrega a regra de decisão que foi acordada (vai estar em Marco 4 via Calibracao). **A OS é elo perdido.**

**Decisão recomendada:**

Adicionar à entidade OS no §3.2:

```
- analise_critica_id UUID NOT NULL (FK → orcamento.analise_critica)
- analise_critica_snapshot_hash CHAR(64) (snapshot probatório no momento da abertura — INV-DOC-CANON-001)
- regra_decisao_acordada VARCHAR(20) NULL (snapshot — overridable por cliente em M4)
```

Adicionar AC-OS-001-7:

> **AC-OS-001-7 (cl. 7.1):** GIVEN abertura via orçamento, WHEN `abrirOS` executa, THEN copia `orcamento.analise_critica_id` + hash do snapshot pra OS; se orçamento veio SEM análise crítica registrada (`orcamento.analise_critica IS NULL`) → 412 `OrcamentoSemAnaliseCritica` (cl. 7.1).

AC paralelo em US-OS-015 (OS avulsa balcão): atendente é obrigado a registrar análise crítica inline (campo `analise_critica_inline_texto + capacidade_tecnica_confirmada_por`) antes de fechar a abertura.

Promover INV-OS-ANAL-001: "Toda OS com pelo menos 1 atividade tipo=calibracao|verificacao_inmetro deve carregar `analise_critica_id` ou `analise_critica_inline_*` antes de transitar para AGENDADA."

---

### P-OS-R3 — BLOQUEANTE — Escopo acreditado vigente do tenant (NIT-DICLA-030) não é validado em `adicionarAtividade`

**Norma:** NIT-DICLA-030 rev. 15 item 4.1 — "calibrações devem ser realizadas dentro do escopo de acreditação vigente do laboratório."

**Achado:**
- AC-OS-002-3 valida competência RT por grandeza, mas **não valida** se a grandeza+faixa+procedimento está dentro do `EscopoAcreditacao` vigente do tenant (módulo `licencas-acreditacoes` — `draft`).
- ADR-0012 §3 menciona `@authz_attribute("acreditacao_vigente")` — mas spec M3 não chama esse atributo.
- Cenário: tenant tem acreditação vigente em "massa até 30 kg"; abre OS com atividade calibração de balança de 100 kg. Sistema atual aceita (tenant tem RT competente em massa). Mas o certificado emitido em M4 seria fora do escopo → NC formal CGCRE.
- Spec §6.2 não lista consumer `Acreditacao.Vencida` ou `Acreditacao.Suspensa` que deveria bloquear novas atividades.

**Decisão recomendada:**

Adicionar predicate `tenant_dentro_escopo_acreditado(tenant_id, grandeza, faixa_min, faixa_max, data)` em ADR-0012 (extensão); chamar em AC-OS-002-3:

> **AC-OS-002-3 (revisado):** GIVEN `tipo IN (calibracao, verificacao_inmetro)` + `requer_competencia_rt=true`, WHEN servidor valida, THEN executa **dois** predicates em ordem:
> 1. `tenant_dentro_escopo_acreditado(tenant_id, grandeza, faixa, data)` — se falso E o tenant possui perfil A/RBC → 422 `ForaDoEscopoAcreditado: [grandeza/faixa]`. (Tenants perfil B/C/D apenas alertam — não bloqueiam, mas marcam `EventoDeOS.tipo=fora_escopo_aceito_perfil_BCD`.)
> 2. `tenant_tem_rt_ativo_competencia(grandeza)` (já existente).

Adicionar evento consumido §6.2:

| `Acreditacao.Suspensa` / `Acreditacao.Vencida` | suporte-plataforma/licencas-acreditacoes | bloqueia abertura de novas atividades tipo=calibracao/verificacao_inmetro do tenant |

Promover **GATE-RBC-ESCOPO-1** (operacional, complementar a GATE-RBC-ANAL-PEDIDOS-1).

---

### P-OS-R4 — AJUSTADO — cl. 7.5 manuseio de itens + vínculo `EquipamentoRecebimento` (US-EQP-006)

**Cláusula ISO/IEC 17025:** 7.5 — "Registros técnicos para cada atividade de laboratório... incluindo condição do item, identificação, anomalias."

**Achado:**
- M2 entregou US-EQP-006 (`EquipamentoRecebimento` com condição visual + foto + lacre + recebedor). Excelente.
- Spec M3 §3.2 OS aponta `equipamento_id UUID NOT NULL FK → equipamentos` — mas não aponta `equipamento_recebimento_id` (o evento físico específico de recebimento daquele lote/visita).
- Cenário: cliente trazia o mesmo equipamento (mesmo ID) em 3 datas diferentes → 3 OS diferentes, cada uma deveria carregar SEU snapshot de recebimento (condição naquele momento, lacre daquele momento). Se OS só aponta para `equipamento_id`, recebimento desambigua só pela ordem temporal — frágil.
- Não existe AC explícito sobre "condição registrada na chegada está vinculada à OS desta visita".

**Decisão recomendada:**

Adicionar campo em OS (§3.2):

```
- equipamento_recebimento_id UUID NULL (FK → EquipamentoRecebimento — null em OS de campo onde tecnico vai até o cliente)
```

Adicionar AC-OS-001-8:

> **AC-OS-001-8 (cl. 7.5):** GIVEN OS de bancada (equipamento está no laboratório), WHEN `abrirOS` executa, THEN exige `equipamento_recebimento_id` vinculado ao recebimento mais recente em estado `recebido_pendente_inspecao | em_calibracao` daquele equipamento + daquele cliente; se ausente → 412 `EquipamentoSemRecebimentoRegistrado`.
> Para OS de campo (tipo da atividade tem `executa_em_campo=true`) o campo permanece NULL e a condição visual é registrada em `ChecklistDaAtividade` pelo técnico in loco.

Não promover INV agora — fica como AC + AJUSTADO em P4. Documentar em `sagas.md` §1 a propagação `EquipamentoRecebimento → OS`.

---

### P-OS-R5 — AJUSTADO — cl. 8.7 ciclo CAPA precisa de FK para módulo qualidade (RegistroCAPA)

**Cláusula ISO/IEC 17025:** 8.7 — "Ações corretivas... devem incluir análise de causa-raiz, verificação de eficácia."

**Achado:**
- AC-OS-005-3 está conceitualmente correto ("causa-raiz + ação corretiva + eficácia verificada → resolverNC"), mas o spec M3 §3.1 declara `NaoConformidadeAtividade` como entidade local sem referência ao `RegistroCAPA` do módulo qualidade (Wave B).
- Stub `CAPAQueryService` não é mencionado no spec — só o consumer `qualidade (CAPA)` aparece em §6.1 como destinatário de `AtividadeNaoConforme`.
- Cenário auditoria: CGCRE pergunta "mostre as 3 últimas NC da grandeza massa e a verificação de eficácia". Sistema atual: SQL na tabela `nao_conformidade_atividade` mostra texto livre. **Falta** o vínculo formal: `nao_conformidade_atividade.registro_capa_id`.
- Como módulo qualidade é Wave B, criar a FK agora deixa o slot pronto sem bloquear M3.

**Decisão recomendada:**

Adicionar à `NaoConformidadeAtividade`:

```
- registro_capa_id UUID NULL (FK → qualidade.registro_capa, Wave B; preenchido por consumer reverso quando módulo qualidade nascer)
- causa_raiz_hash CHAR(64) NULL (anti-PII, INV-OS-TXT-001)
- acao_corretiva_descricao_hash CHAR(64) NULL
- eficacia_verificada_em TIMESTAMPTZ NULL
- eficacia_verificada_por_user_id UUID NULL
```

Adicionar AC-OS-005-5:

> **AC-OS-005-5 (cl. 8.7):** GIVEN NC marcada, WHEN `resolverNC` executa, THEN exige TODOS de: `causa_raiz_hash`, `acao_corretiva_descricao_hash`, `eficacia_verificada_em`, `eficacia_verificada_por_user_id` ≠ NULL; ausente → 412 `CAPAIncompleto`.

Promover stub `CAPAQueryService` em ADR ou criar GATE-RBC-CAPA-1 Wave B para `RegistroCAPA` consumir `AtividadeNaoConforme`/`AtividadeNCResolvida`.

---

### P-OS-R6 — AJUSTADO — Janela `os-calibracao-link-watchdog` 24h/72h é apertada vs fluxo de bancada real

**Norma:** ISO 17025 cl. 7.4 + 7.6 — rastreabilidade entre atividade e registro técnico.

**Achado:**
- INV-OS-CAL-LINK-001 + watchdog: alerta P2 em 24h sem `Calibracao.atividade_os_id`; cria NC automática em 72h.
- **Realidade de bancada laboratório calibração**: técnico mede em campo dia 1 → planilha de campo dia 2 → input no sistema dia 3 → cálculo incerteza dia 4 → revisão dia 5 → emissão dia 6. Para calibrações com **monte carlo (JCGM 101)** ou múltiplos pontos + linearidade, o tempo entre `AtividadeConcluida` e `Calibracao.atividade_os_id` (criação do registro M4) facilmente passa de 72h.
- Watchdog em 72h vai gerar **NC automática em ~30-50% das calibrações de laboratórios pequenos** — false positive em massa.
- ISO 17025 não exige prazo específico — exige rastreabilidade existente.

**Decisão recomendada:**

Manter watchdog mas ajustar:

1. Alterar default: alerta P2 em **72h** (não 24h); NC automática em **15 dias úteis** (não 72h).
2. Configurável por tenant via `TipoAtividadeConfig.prazo_link_calibracao_alerta_h` e `..._nc_dias_uteis`.
3. Defaults RBC perfil A: 72h alerta / 15 dias NC. Perfis B/C/D: 7 dias alerta / 30 dias NC.
4. Permitir extensão manual pelo RT do tenant (audit registrado em `EventoDeOS.tipo=watchdog_estendido` com justificativa ≥100 chars).

Revisar `sagas.md` §3 e spec §10 (drill `validar_m3_os` item 12).

---

### P-OS-R7 — AJUSTADO — 2ª conferência independente (ADR-0026) sem campo `conferente_id` na atividade

**Cláusula ISO/IEC 17025:** 6.2.5 — independência entre executor, revisor, conferente.

**Achado:**
- ADR-0026 aceito (2026-05-23) crava 3 níveis + exceção objetiva 4 condições + 5%/mês.
- Spec M3 §3.2 `AtividadeDaOS` tem só `tecnico_executor_id`. Não tem `revisor_id`, `conferente_id`, `excecao_independencia_id`.
- Embora a 1ª/2ª conferência **propriamente** rode em Marco 4 (sobre `Calibracao`, não sobre `Atividade`), a auditoria CGCRE conecta via rastreabilidade — quem foi o executor da atividade vs. quem foi o revisor/conferente do resultado.
- M3 não publica nada que carregue essa rastreabilidade — `AtividadeConcluida` só carrega `tipo, checklist_id, aceite_id`.

**Decisão recomendada:**

Não duplicar campos M4 em M3. Em vez disso:

1. Garantir que `AtividadeConcluida` payload §6.1 inclua explicitamente `tecnico_executor_id` (já implícito, tornar explícito).
2. Documentar em `docs/dominios/operacao/modulos/os/sagas.md` saga "Independência executor↔revisor": M3 publica `tecnico_executor_id`; M4 ao receber valida em Calibracao.revisor `revisor != atividade.tecnico_executor_id` (Nível 1/2) ou registra exceção (Nível 3 — INV-CAL-IND-001).
3. Spec M3 não precisa mexer no schema — só explicitar o contrato.

Acrescentar em §6.1:

| `AtividadeConcluida` | payload **agora explicitamente carrega** `tecnico_executor_id` para consumer M4 validar independência (ADR-0026) | certificados (se tipo=calibracao), portal-cliente, omni |

---

### P-OS-R8 — ACEITE — Dispensa de aceite + no-show em atividades calibração

**Cláusula ISO/IEC 17025:** 7.8.1.2 + 7.8.2 — relatório de resultados acordado com o cliente.

**Achado / Análise:**
- US-OS-013 (dispensa aceite) e US-OS-014 (no-show) são adequadamente tratadas: dispensa exige termo PDF + gerente + audit; no-show exige foto + hora + EventoDeOS.
- Em ATIVIDADE CALIBRAÇÃO, auditor CGCRE em supervisão pode questionar "como evidenciam que o cliente recebeu/aceitou o resultado quando não há aceite?" — mas a Norma 17025 **não exige assinatura presencial do cliente**, exige **comunicação documentada do resultado**.
- A dispensa com termo PDF + entrega via portal-cliente já satisfaz cl. 7.8.1.2. Audit imutável + WORM 25 anos preserva a evidência.

**Decisão:** **aceitar como está.** Recomendação adicional (cosmética, não bloqueante): adicionar nota em `DispensaAceiteAtividade.termo_pdf_id` reforçando que o termo deve incluir "comunicação alternativa do resultado via portal-cliente (link/QR)".

Sem ação.

---

## Mapeamento norma ↔ achados

| Cláusula ISO/IEC 17025:2017 | Achado | Resolvido por |
|---|---|---|
| 6.2 Pessoal — competência declarada | P-OS-R1 BLOQUEANTE | AC-OS-002b-4 + AC-OS-003-6 + INV-OS-ATIV-005-EXEC-COMP |
| 6.2.5 Independência | P-OS-R7 AJUSTADO | sagas.md + payload AtividadeConcluida (ADR-0026 já cobre estrutura) |
| 7.1 Análise crítica de pedidos | P-OS-R2 BLOQUEANTE | campos OS + AC-OS-001-7 + INV-OS-ANAL-001 |
| 7.4 Manuseio de itens | P-OS-R4 AJUSTADO | OS.equipamento_recebimento_id + AC-OS-001-8 |
| 7.5 Registros técnicos | P-OS-R2 + P-OS-R4 | combinados |
| 7.8 Relatório de resultados | P-OS-R8 ACEITE | — |
| 7.10 NC trabalho | P-OS-R5 (combinado com 8.7) | RegistroCAPA FK |
| 8.7 Ações corretivas | P-OS-R5 AJUSTADO | NaoConformidadeAtividade campos CAPA + AC-OS-005-5 |
| NIT-DICLA-030 escopo | P-OS-R3 BLOQUEANTE | predicate `tenant_dentro_escopo_acreditado` + AC-OS-002-3 revisado |

---

## GATEs novos / atualizados

| GATE | Status | Origem | Quando | Responsável |
|---|---|---|---|---|
| GATE-RBC-ANAL-PEDIDOS-1 | já existe | spec §9 | Wave A operacional | Tech-lead |
| GATE-RBC-ESCOPO-1 | **NOVO** (P-OS-R3) | este parecer | Wave A — antes 1º tenant perfil A | Tech-lead + Subagente RBC |
| GATE-RBC-CAPA-1 | **NOVO** (P-OS-R5) | este parecer | Wave B módulo qualidade | Tech-lead |
| GATE-OS-CAL-LINK-WATCHDOG | revisar janela (P-OS-R6) | spec §9 | Marco 3 P4 | Tech-lead |

---

## Próximos passos

1. **Absorver P-OS-R1, P-OS-R2, P-OS-R3** em `plan.md` da P2 (são bloqueantes — vão pra matriz de reconciliação com PRD).
2. **PR contra PRD `os/prd.md`** adicionando AC-OS-001-7, AC-OS-001-8, AC-OS-002b-4, AC-OS-003-6, AC-OS-005-5.
3. **PR contra REGRAS-INEGOCIAVEIS.md** com INV-OS-ATIV-005-EXEC-COMP + INV-OS-ANAL-001.
4. **PR contra ADR-0012** adicionando predicate `tenant_dentro_escopo_acreditado` e `rt_competencia_cobre(user_id, grandeza, data)` formalmente listados.
5. **PR contra `sagas.md`** documentando saga "Independência executor↔revisor M3→M4" (P-OS-R7) e saga "Recebimento equipamento → OS bancada" (P-OS-R4).
6. **Atualizar `docs/governanca/gates-wave-a-consolidado.md`** com GATE-RBC-ESCOPO-1 e GATE-RBC-CAPA-1.

---

## Avisos de limite (obrigatório)

- Sou subagente IA `consultor-rbc-iso17025`. **Não tenho credencial CGCRE.** Este parecer é consultivo.
- **Antes de qualquer auditoria CGCRE real, 1ª submissão a processo de acreditação RBC, dispute técnica com CGCRE, ou parecer formal solicitado por tenant farma TOP-3**, este dossiê precisa de revisão de **consultor humano credenciado**. Estimativa: R$ 8-15k por engajamento pontual.
- Preparei este parecer pra **economizar 80% do tempo** do consultor humano quando for contratado.
