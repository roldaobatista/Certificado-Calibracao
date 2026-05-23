---
owner: roldao
revisado-em: 2026-05-23
status: draft
finalidade: spec FORWARD do Marco 3 (`os`) — destravado pós Onda 6 saneamento. Base das ADRs 0023/0027/0029/0030/0031/0032/0041/0042 + VOs + hooks Onda 4 + auditoria 10 lentes pré-Marco 3 (R1+R2 fechadas) + Onda 6 auditor 5 (sagas + SLA + cancelamento parcial + concorrência tipos).
---

# Marco 3 — Ordens de Serviço (OS com Atividades) — spec FORWARD

> **Stub criado em 2026-05-23 (Onda 5 saneamento).** Marco 3 estava em "pre-spec" há semanas; Onda 6 destravou aceitando ADRs bloqueantes. Este documento é o ponto de entrada para iniciar o ritual Spec Kit do Marco 3.
>
> **Próximo passo:** `/plan` revisado por 4 subagentes (tech-lead, advogado, corretora, RBC) + matriz reconciliação + tasks.md detalhado.

---

## 1. Contexto e premissas

1.1. **ADRs aceitas (Onda 6 saneamento 2026-05-23):**
- ADR-0023 — OS com Atividades (1 OS contém N AtividadeDaOS, cada uma com tipo do enum fechado)
- ADR-0027 — Sync mobile com merge por atividade (LWW + IDEMP-001 + backlog visível)
- ADR-0029 — Canonicalização texto probatório (AceiteAtividade)
- ADR-0030 — Vigência temporal canônica (JanelaVigencia)
- ADR-0031 — Soft-delete em 3 padrões
- ADR-0032 — FK cross-módulo + ReferenciaPIIAnonimizavel
- ADR-0041 — Concorrência atividades no mesmo equipamento (Onda 6 auditor 5)
- ADR-0042 — Cancelamento parcial × Faturamento (Onda 6 auditor 5)

1.2. **VOs disponíveis (Onda 2):**
- `JanelaVigencia`, `ReferenciaPIIAnonimizavel`, `Telefone`, `UF`, `Dinheiro` (shared)
- `Grandeza`, `FaixaMedicao`, `IncertezaExpandida` (metrologia — para atividade tipo `calibracao`)

1.3. **Hooks ativos (Onda 4):**
- `vigencia-canonica-check.sh` — bloqueia colunas anti-padrão
- `soft-delete-padrao-check.sh` — Padrão A (estado-máquina) obrigatório em OS/Atividade
- `fk-pii-anonimizavel-check.sh` — FK PII em entidades B precisa de par hash+key_id
- `biometria-key-validator.sh` — BIOMETRIA_KEY_* dedicada por tenant
- `os-conclusao-todas-terminais-check.sh` — INV-OS-ATIV-001
- `frontmatter-revisado-em-check.sh`
- `spec-ac-binario-check.sh`

1.4. **PRD canônico:** `docs/dominios/operacao/modulos/os/prd.md` (status: stable; 10 US / 40 AC BDD).

1.5. **DPIA aprovada (minuta OAB pendente):** `docs/conformidade/comum/dpia/dpia-os.md`.

---

## 2. Entidades principais (a refinar em `/plan`)

| Entidade | Padrão soft-delete | Vigência? | FK PII? |
|---|---|---|---|
| `OS` | A (estado-máquina) | não | sim — `cliente_referencia_hash` |
| `AtividadeDaOS` | A (estado-máquina) | não | sim (via OS) |
| `EventoDeOS` | B (`revogado_em`) | não | sim — hash sanitizado |
| `AceiteAtividade` | B (imutável pós-coleta) | não | sim — biometria + cliente |
| `DelegacaoExecucao` | B (audit imutável) | não | sim — técnico delegante + delegado |
| `ChecklistDaAtividade` | A (estado por item) | não | não |
| `TipoAtividadeConfig` | C (`deletado_em`) | sim (procedimento) | não |

## 3. INVs já cravados em REGRAS-INEGOCIAVEIS.md (Onda 7 R2)

- INV-OS-ATIV-001..005 (5 INVs)
- INV-OS-TXT-001 (anti-PII em texto livre)
- INV-OS-GEO-001 (geo precisão)
- INV-OS-AUD-001 (audit sanitizado escrita)
- INV-OS-ACEITE-BIO-001 (biometria touch art. 11)
- INV-DOC-CANON-001 (canonicalização)
- RAT-07, RAT-08

## 4. AC binários esperados (delineados em PRD — alinhamento Onda 6 auditor 5 M5)

Numeração canônica (PRD §6 é fonte da verdade):

- US-OS-001 abrirOS (a partir de orçamento aprovado; INV-OS-EQP-001 + INV-OS-ANON-001)
- US-OS-002 adicionarAtividade (validação RT por tipo — INV-CAL-RT-001; sequência pós-terminal bloqueada)
- US-OS-002b atribuirTecnico (mantém compat anterior; agenda + UMC)
- US-OS-003 iniciarAtividade (validação matriz concorrência ADR-0041; geo opt-in)
- US-OS-004 concluirAtividade (watchdog INV-OS-CAL-LINK-001; notificação cliente)
- US-OS-005 marcarNaoConformidadeAtividade (CAPA TEMA-B.2)
- US-OS-006 reabrirOS (sucessão societária — INV-OS-SUC-001)
- US-OS-007 cancelarOS (SLA breach se prioridade alta/emergencia)
- US-OS-008 cancelarAtividade (escopo alterado → Financeiro — ADR-0042 / INV-OS-FAT-001)
- US-OS-009 OS combinada (manutenção + calibração ADR-0023)
- US-OS-010 adicionarAtividade em andamento
- US-OS-011 reagendarAtividade (Onda 6 — A2)
- US-OS-012 transferirTecnico (Onda 6 — A2)
- US-OS-013 dispensarAceiteCliente (Onda 6 — A2 + DispensaAceiteAtividade)
- US-OS-014 marcarNoShow (Onda 6 — A2 + RAT-08)
- US-OS-015 criarOSAvulsa (Onda 6 — M6, balcão sem orçamento)

Sagas inter-modulares: ver `docs/dominios/operacao/modulos/os/sagas.md`.

## 5. GATEs Wave A (subset M3)

- GATE-BUS-CONSUMER-IDEMP (migration consumer_idempotencia)
- GATE-BUS-HANDLERS (registry consumers)
- GATE-EQP-PWA-ADR (ADR-0018 aceite)
- GATE-RBC-ANAL-PEDIDOS-1 (cl. 7.1 análise crítica)
- GATE-LGPD-ART18-MODULOS (endpoint art. 18 em OS)
- GATE-SEG-VIST-1 (cláusula E&O `pareceres técnicos` quando tipo=vistoria)

Catálogo: `docs/governanca/gates-wave-a-consolidado.md`.

## 6. Non-goals (Marco 3)

- Editor visual de checklist (Wave B)
- Workflow paralelo de aprovação multi-nível (Wave B BPM)
- Integração WhatsApp Business para captura de aceite remoto (Wave B)
- Multimídia além de fotos (vídeos, áudios — Wave B)
- App nativo iOS/Android sem PWA primeiro (ADR-0018)

## 7. Próximo passo

Executar `/plan` com 4 subagentes (tech-lead, advogado, corretora, RBC). Sem isso, `/implement` está PROIBIDO (INV-RITUAL-001).

---

**Status:** stub destravado, aguarda `/plan` formal.
