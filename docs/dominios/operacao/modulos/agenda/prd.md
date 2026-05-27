---
owner: roldao
revisado-em: 2026-05-27
proximo-review: 2026-08-27
status: stable
modulo: agenda
dominio: operacao
diataxis: explanation
audiencia: agente
historico:
  - 2026-05-23 — versão inicial draft (calendário multi-técnico)
  - 2026-05-27 — Onda 3 saneamento BATCH B2 — frontmatter canônico, perfil ADR-0067 declarado (INV-020 Lei 13.103 só perfis A/B/C com técnico de campo), US-AG-001..013 reescritas em BDD GIVEN-WHEN-THEN, US-AG-014 nova (agenda considera RT substituto — ADR-0068), INV-AGENT-001 em texto livre, vocabulário Wave A/Wave B, status STABLE.
relacionados:
  - docs/adr/0023-os-com-atividades.md
  - docs/adr/0022-rt-tenant.md
  - docs/adr/0030-vigencia-canonica.md
  - docs/adr/0033-bus-idempotencia-consumer.md
  - docs/adr/0051-propagacao-adr0023-modulos.md
  - docs/adr/0067-perfil-regulatorio-tenant-entidade-temporal.md
  - docs/adr/0068-sucessao-substituicao-rt.md
  - docs/conformidade/comum/matriz-feature-perfil.md
  - docs/dominios/operacao/modulos/os/prd.md
  - docs/dominios/operacao/modulos/chamados/prd.md
---

# PRD — Módulo Agenda

## 1. O que este módulo é

Calendário gerencial multi-técnico que distribui OS, bloqueios e eventos pelos slots dos técnicos com **validação automática da jornada UMC (INV-020 — Lei 13.103)** quando aplicável, detecção de conflitos, deslocamento estimado, feriados e recorrência. **OP13 — Wave A** (NOVA, destacada de OP3 e OP10).

## 2. Por que este módulo existe

JTBD-009 (gerente não sabe onde técnico está hoje) + JTBD-010 (reagendar vira bagunça em planilha). Antes da auditoria 17/05, agenda estava embutida em OP3.1 e OP10 sem visão multi-técnico. Sem agenda formalizada, OS roda sem programação consistente — bloqueio estrutural do Wave A.

## 3. Personas

**Persona dominante:** P-OP-04 (gerente operacional). Detalhes em `../personas.md` — P-OP-04 (gerente operacional, primária), P-OP-01 (técnico — visualiza própria agenda), P-OP-03 (atendente — agenda chamado convertido em OS), P-OP-05 (cliente — vê janela proposta).

## 4. Perfil regulatório (ADR-0067)

| Feature | A — Acreditado RBC | B — Rastreável | C — Em preparação D→A | D — Comercial puro |
|---|---|---|---|---|
| **Agenda multi-técnico básica** (US-AG-001..010) | ✅ OBRIGATÓRIO | ✅ OBRIGATÓRIO | ✅ OBRIGATÓRIO | ✅ OBRIGATÓRIO |
| **Validação INV-020 jornada UMC (Lei 13.103)** — só técnico de campo em veículo UMC | ✅ OBRIGATÓRIO se `tenant_perfil_e(['A','B','C']) AND colaborador.is_tecnico_campo AND aloca_em_UMC` | ✅ OBRIGATÓRIO sob mesma condição | ✅ OBRIGATÓRIO sob mesma condição | ⚪ OPCIONAL (perfil D pode dispensar se sem técnico de campo) |
| **Agenda considera RT substituto** (US-AG-014 — ADR-0068) — em calibração perfil A | ✅ OBRIGATÓRIO (RT principal indisponível → sistema sugere RT substituto cadastrado) | 🟢 OPCIONAL_RECOMENDADO | 🟢 OPCIONAL_RECOMENDADO | ❌ DESABILITADO (perfil D não faz calibração regulada) |
| **Sugestão por competência (RTCompetencia por método — ADR-0022 v2)** | ✅ OBRIGATÓRIO | ✅ OBRIGATÓRIO | ✅ OBRIGATÓRIO | ⚪ OPCIONAL |

Predicate canônico: `tenant_perfil_e([...])` lê `Tenant.perfil_regulatorio` no banco — NUNCA do payload.

## 5. Escopo Wave A

- Calendário multi-técnico (visão dia/semana, colunas por técnico)
- Slots de tempo com eventos (OS, bloqueio, descanso, deslocamento, almoço, manutenção interna)
- **Validação INV-020** (Lei 13.103): hook bloqueia agendamento que viola jornada UMC — gated por perfil + tipo colaborador
- Detecção de conflito ao arrastar/criar (não permite 2 eventos no mesmo slot do mesmo técnico)
- Tempo de deslocamento estimado entre OS (geo/distância — fallback manual)
- Bloqueios (férias, treinamento, atestado)
- Feriados (nacional default + estadual/municipal + custom por tenant)
- Recorrência simples (semanal, mensal — manutenção preventiva)
- Reagendamento com auditoria + notificação cliente
- Capacidade do técnico (horas úteis / dia)
- Drag & drop com validação live
- Integração com Chamados (slot proposto ao converter em OS) e OS (atribuição liga slot)
- **Sugestão de RT substituto** quando RT principal indisponível (ADR-0068) — perfil A obrigatório

## 6. Não-objetivos Wave A

- **Tempo de deslocamento real-time** (M-AG-003) depende de `MapsProvider` (Wave B). Fallback Wave A: input manual do gerente.
- Roteirização inteligente (TSP) — Wave B (OP3.3)
- Sugestão automática de melhor técnico por skill/proximidade — Wave B
- Integração 2-way com Google/Outlook Calendar — Wave B
- Reserva de UMC (veículo) como recurso — Wave B
- Sincronização da agenda com app pessoal do técnico (push iOS/Android) — Wave B
- Bot que negocia horário com cliente via WhatsApp — não fazer

## 7. User Stories (BDD)

### US-AG-001 — Gerente vê semana multi-técnico em 1 tela

**Como** gerente (P-OP-04), **quero** ver semana multi-técnico em 1 tela, **para** distribuir trabalho com visão geral.

- **AC-AG-001-1**: GIVEN gerente abre agenda, WHEN UI renderiza, THEN exibe calendário semanal com 1 coluna por técnico + slots de 30min + cores por tipo de evento.
- **AC-AG-001-2**: GIVEN ≤ 20 técnicos no tenant, WHEN tela carrega, THEN p95 ≤ 1s sem degradar (NFR Wave A).

---

### US-AG-002 — Arrastar OS pra outro técnico/horário valida INV-020 + conflito

**Como** gerente (P-OP-04), **quero** arrastar OS pra outro técnico/horário com validação automática, **para** não criar conflito de jornada UMC.

- **AC-AG-002-1**: GIVEN gerente arrasta OS, WHEN solta no novo slot, THEN servidor valida ANTES de salvar: (a) sem conflito no técnico destino; (b) se aplicável INV-020 (perfil + técnico de campo + UMC), valida jornada.
- **AC-AG-002-2 (INV-020 gated por perfil — fecha L6)**: GIVEN `tenant_perfil_e(['A','B','C']) AND colaborador.is_tecnico_campo=true AND evento.aloca_em_UMC=true`, WHEN agenda salva, THEN executa validação Lei 13.103 (jornada + descanso); se viola → 422 `JornadaUMCViolada` + razão. Perfil D sem técnico de campo dispensa.
- **AC-AG-002-3 (read perfil)**: GIVEN sistema lê perfil pra gating, WHEN avalia, THEN lê `Tenant.perfil_regulatorio` do banco — NUNCA do payload.

**Invariantes:** `INV-020`, `INV-TENANT-PERFIL-002`.

---

### US-AG-003 — Bloqueio com mensagem clara em violação Lei 13.103

**Como** sistema, **quero** bloquear agendamento que viola Lei 13.103 com mensagem clara, **para** que gerente saiba como reagendar.

- **AC-AG-003-1**: GIVEN tentativa de salvar evento que excede jornada, WHEN servidor valida, THEN retorna `422 JornadaUMCViolada` + payload `{motivo, descanso_minimo_faltante_min, sugestao_proximo_slot_valido}`.
- **AC-AG-003-2**: GIVEN UI recebe erro, WHEN exibe, THEN mostra banner vermelho com texto humano + botão "agendar no próximo slot válido".

---

### US-AG-004 — Criar bloqueio com motivo

**Como** gerente (P-OP-04), **quero** criar bloqueio (férias, treinamento, atestado) com motivo, **para** que ninguém atribua OS naquele slot.

- **AC-AG-004-1**: GIVEN gerente clica "bloquear", WHEN preenche `tecnico_id` + `inicio` + `fim` + `motivo` (enum: ferias, treinamento, atestado, outro), THEN salva `BloqueioAgenda` + bloqueia atribuições no intervalo.
- **AC-AG-004-2**: GIVEN bloqueio cobre slot já atribuído, WHEN salva, THEN alerta + obriga reatribuição ou confirmação explícita.

---

### US-AG-005 — Feriados destacados + exigência de confirmação

**Como** sistema, **quero** destacar feriados (nacional + estadual + custom) e exigir confirmação ao agendar em feriado, **para** evitar agendamento acidental.

- **AC-AG-005-1**: GIVEN data é feriado nacional/estadual/municipal/custom, WHEN UI renderiza, THEN slot tem fundo cinza + ícone feriado.
- **AC-AG-005-2**: GIVEN gerente arrasta evento pra feriado, WHEN tenta salvar, THEN UI exibe modal "deseja agendar em feriado?" + exige confirmação explícita.

---

### US-AG-006 — Sugerir slot ao converter chamado em OS

**Como** atendente (P-OP-03), **quero** que sistema sugira slot livre do técnico competente ao converter chamado em OS, **para** acelerar agendamento.

- **AC-AG-006-1**: GIVEN chamado convertido em OS com atividade `tipo=calibracao`, WHEN servidor sugere técnico, THEN consulta primeiro RT substituto (ADR-0068) se principal indisponível, depois `RTCompetencia` por método (ADR-0022 v2), depois agenda livre no horizonte de 7 dias.
- **AC-AG-006-2**: GIVEN nenhum técnico competente disponível, WHEN sugestão executa, THEN retorna lista vazia + sugere agendar reunião com gerente.

**Dependências:** ADR-0022, ADR-0068.

---

### US-AG-007 — Técnico vê própria agenda no mobile

**Como** técnico (P-OP-01), **quero** ver minha própria agenda no mobile com tempo de deslocamento estimado, **para** planejar dia.

- **AC-AG-007-1**: GIVEN técnico abre app, WHEN agenda renderiza, THEN mostra eventos do dia ordenados + tempo de deslocamento estimado entre eventos (fallback manual Wave A).

---

### US-AG-008 — Reagendamento notifica cliente

**Como** gerente (P-OP-04), **quero** que reagendamento notifique cliente com nova janela proposta, **para** que cliente aprove.

- **AC-AG-008-1**: GIVEN evento reagendado + cliente vinculado, WHEN salva, THEN OmniChannel envia notificação WhatsApp/Email com nova janela + link de aprovação.
- **AC-AG-008-2**: GIVEN cliente recusa via portal, WHEN servidor recebe, THEN evento volta pro slot original + alerta gerente.

---

### US-AG-009 — Manutenção recorrente gera slots futuros

**Como** gerente (P-OP-04), **quero** que manutenção preventiva (semanal/mensal) gere slots futuros automaticamente, **para** não esquecer.

- **AC-AG-009-1**: GIVEN evento marcado como recorrente (semanal/mensal), WHEN salva, THEN job procrastinate gera próximas 12 ocorrências em batch (IDEMP-001 — ADR-0033).
- **AC-AG-009-2**: GIVEN evento recorrente alterado, WHEN gerente confirma "aplicar a todos", THEN propaga alteração; se "só esta", isola só a ocorrência.

---

### US-AG-010 — Capacidade do dia mostra ocupação

**Como** gerente (P-OP-04), **quero** ver capacidade do dia ("75% ocupado"), **para** decidir se aceito mais OS.

- **AC-AG-010-1**: GIVEN dia com `horas_alocadas / horas_uteis_dia >= 0.75`, WHEN UI renderiza, THEN exibe indicador amarelo "75% ocupado"; >= 90% → vermelho.

---

### US-AG-011 — Resolver conflito de agenda (A-AG-001)

**Como** atendente (P-OP-03), **quero** resolver conflito de agenda escolhendo entre {manter_novo, manter_antigo, reagendar_ambos}, **para** evitar dupla alocação.

- **AC-AG-011-1**: GIVEN conflito detectado, WHEN UI exibe modal, THEN opções `{manter_novo, manter_antigo, reagendar_ambos}` + razão obrigatória ≥ 30 chars.
- **AC-AG-011-2**: GIVEN atendente confirma, WHEN salva, THEN publica `Agenda.ConflitoResolvido` + audit + notifica técnicos afetados.

---

### US-AG-012 — Registrar no-show com custo de deslocamento (A-AG-002)

**Como** gerente (P-OP-04), **quero** registrar no-show com custo de deslocamento e decisão de cobrar cliente, **para** mensurar prejuízo.

- **AC-AG-012-1**: GIVEN técnico chega + cliente ausente, WHEN gerente registra no-show, THEN cria `RegistroNoShow` com `custo_deslocamento` + `decisao_cobrar` (sim/não).
- **AC-AG-012-2**: GIVEN `decisao_cobrar=true`, WHEN salva, THEN dispara cobrança via módulo financeiro (`AReceber.criar`).

---

### US-AG-013 — Agendar atividade da OS, não OS inteira (C-AG-001 / ADR-0051)

**Como** gerente (P-OP-04), **quero** agendar atividade específica da OS (não a OS inteira), **para** permitir atividades distintas em janelas diferentes.

- **AC-AG-013-1**: GIVEN OS com N atividades, WHEN gerente arrasta, THEN cada atividade tem seu próprio slot + técnico executor (ADR-0023 + ADR-0051).
- **AC-AG-013-2**: GIVEN duas atividades da mesma OS em técnicos diferentes, WHEN salva, THEN aceita (atividades independentes — manutenção mecânica + calibração metrológica).

**Dependências:** ADR-0023, ADR-0051.

---

### US-AG-014 — Agenda considera RT substituto (ADR-0068)

**Como** sistema, **quero** considerar RT substituto quando RT principal indisponível (férias, atestado, sucessão), **para** não bloquear agendamento de calibração em perfil A.

- **AC-AG-014-1 (perfil A — obrigatório)**: GIVEN tenant em perfil A + atividade `tipo=calibracao` + RT principal indisponível no slot (bloqueio ativo), WHEN sistema sugere executor, THEN consulta `RTSubstituto` ativo cadastrado em `metrologia/rt-tenant` (ADR-0068) com competência cobrindo a grandeza; se nenhum disponível → 412 `SemRTNoSlot` + sugere reagendar.
- **AC-AG-014-2 (perfil B/C — recomendado)**: GIVEN perfil B ou C + RT principal indisponível, WHEN sistema sugere, THEN emite warning ("operando sem RT substituto") mas permite atribuir; gerente confirma.
- **AC-AG-014-3 (perfil D — desabilitado)**: GIVEN perfil D, WHEN executa, THEN feature não aplica (perfil D não emite calibração regulada).
- **AC-AG-014-4 (read perfil)**: GIVEN sistema avalia gating, WHEN executa, THEN lê `Tenant.perfil_regulatorio` do banco — NUNCA do payload.

**Invariantes:** `INV-OS-ATIV-005-EXEC-COMP`, `INV-TENANT-PERFIL-002`.

**Dependências:** ADR-0022 v2 (RT por método), ADR-0068 (RT substituto), ADR-0067 (perfil regulatório).

---

## 8. Métricas

Ver `metricas.md`. Primárias (mínimo 2-3): % ocupação técnico, conflitos detectados/aceitos, reagendamentos por OS, % atribuições com RT substituto (perfil A).

## 9. NFR

- Drag & drop responsivo (< 200ms feedback)
- Validação INV-020 acontece **antes** de salvar (não pode aceitar e depois rejeitar)
- WCAG 2.1 AA (INV-016) — calendário acessível por teclado e leitor de tela
- Visão multi-técnico até 20 técnicos sem degradar (Wave A)

## 10. Dependências (ADRs)

ADR-0022 (RT tenant + RTCompetencia v2), ADR-0023 (OS com atividades), ADR-0030 (vigência canônica — bloqueios), ADR-0033 (bus idempotência), ADR-0051 (propagação ADR-0023 nos módulos operacionais), ADR-0067 (perfil regulatório), ADR-0068 (sucessão e substituição RT).

## 11. Glossário

Ver `glossario.md` + `docs/comum/glossario.md` + ADR-0037 (PT-EN).

## 12. Como evolui

US nova → próximo `US-AG-NNN`. Feature com gating por perfil → atualizar matriz canônica antes do merge.
