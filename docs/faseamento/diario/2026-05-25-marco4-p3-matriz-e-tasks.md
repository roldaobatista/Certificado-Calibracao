---
owner: roldao
revisado_em: 2026-05-25
status: stable
diataxis: explanation
audiencia: agente
tipo: diario-fase
relacionados:
  - docs/faseamento/M4-calibracao/spec.md
  - docs/faseamento/M4-calibracao/plan.md
  - docs/faseamento/M4-calibracao/matriz-reconciliacao.md
  - docs/faseamento/M4-calibracao/tasks.md
  - docs/adr/0065-concorrencia-calibracao-metrologica.md
  - docs/adr/0024-regra-de-decisao-iso-17025.md
  - docs/adr/0063-rt-competencia-grandeza-diferida-marco4.md
  - REGRAS-INEGOCIAVEIS.md
---

# 2026-05-25 — Marco 4 P3 (matriz reconciliação + tasks.md) entregue

> Sessão sequencial ao P2 do mesmo dia. P3 do ritual Spec Kit consome as decisões cravadas pelo Roldão (D-M4-1..5) + absorve os 45 achados dos 4 reviews paralelos em retrofits de ADR/spec/PRD/REGRAS, materializando o plano em tasks granulares.

## Sequência

### 1. 5 decisões do Roldão registradas

- **D-M4-1:** Motor 2º caminho = **GUM clássico Python (Decimal) + Monte Carlo NumPy** (JCGM 101 + seed em `Calibracao.id`).
- **D-M4-2:** ADR-0063 = **Opção A lazy** (predicate em 3 use cases pós-config, NÃO em `iniciar_atividade`).
- **D-M4-3:** Corretora SUSEP humana = **sem previsão** → 9 GATE-SEG-* rastreados Wave A.
- **D-M4-4:** Consultor CGCRE humano = **sem previsão** → 2 matrizes técnicas preliminares pelo agente (selo `REQUER VALIDAÇÃO CGCRE HUMANO`).
- **D-M4-5:** OAB humana = **sem previsão** → 6 minutas canônicas preliminares pelo agente (selo `REQUER VALIDAÇÃO OAB HUMANA`).

### 2. ADR-0065 nova + retrofit ADR-0024 + retrofit ADR-0063 (commit `b1c1d6a`)

- **ADR-0065 NOVA:** Concorrência em calibração metrológica. 4 mecanismos cumulativos (UNIQUE composto em `leitura` + UNIQUE parcial em `padrao_usado` + optimistic lock CAS via `calibracao.revision` + advisory lock em `calcular_incerteza` + `append_evento_calibracao`) + `sequencia_local IDENTITY` por calibração. INVs CONC-001..004 + AUD-002. Hook `migration-concorrencia-calibracao-check.sh` em M4 P9.
- **ADR-0024 retrofit:** 6 zonas ILAC G8 (PASS / CONDITIONAL_PASS / PASS_COM_RESSALVA / CONDITIONAL_FAIL / FAIL_COM_RESSALVA / FAIL / NA) + PFA/PRA documentados (ILAC G8 §4.4 + JCGM 106 §9) + entidade `AceiteRegraDecisao` (Padrão B WORM) + 3 INVs DEC-004..006. Texto canônico `aceite-regra-decisao-v1.0.md` REQUER OAB humana.
- **ADR-0063 esclarecida:** Opção A lazy — predicate `rt_competencia_cobre` invocado em `configurar_calibracao` + `aprovar_revisao` + `aprovar_2a_conferencia`. `iniciar_atividade` fail-open by design documentado. T-CAL-RT-COMP-1..5 cravadas.

### 3. 24 INVs CAL novos em REGRAS-INEGOCIAVEIS.md (commit `b1c1d6a`)

CONC-001..004, AUD-002, DEC-004..006, INC-002..004, ANAL-001, RT-002, RAST-002, SUBC-005..006, NC-002..003, AMB-001, BACKUP-001, PAD-CASCADE-001, ANON-001, IDEMP-001, CONT-001, FRAUDE-RECEB-001.

### 4. Retrofit spec.md §16 + retrofit prd.md §11 (commit `e8c4126`)

- **spec.md §16** "Revisão P3 (2026-05-25)" absorve 10 BLOQUEANTE + 23 MÉDIO dos 4 reviews: 8 entidades novas (AceiteRegraDecisao, OverrideRegraDecisaoCliente, ReclamacaoCalibracao, ConsentimentoContatoTecnicoCliente, ConsentimentoFotoRecusado, AvaliacaoPeriodicaSubcontratado, PlanoAcaoProficienciaWarning, EventoBackupMetrologico) + campos novos em 9 entidades existentes + **§3.3 nova "Motor de cálculo"** (GUM Decimal + Monte Carlo NumPy + 30 fixtures replay + alerta divergência 0.1%/bloqueio 1%) + 9 eventos publicados novos + 2 consumers novos + 5 riscos novos R-M4-18..22 + 32 GATEs Wave A + 8 hooks novos M4 P9 (não 4) + critérios fechamento revisados 25 checagens drill.
- **prd.md §11** absorve 11 ACs novos cobrindo US-CAL-001/002/004/005/006/007/008/014/017 + **US-CAL-018 nova** (reclamação CDC art. 26 — 4 AC) + descrição estruturada por US.

Ambos status `draft → stable`.

### 5. Matriz reconciliação + tasks.md (este commit)

- **matriz-reconciliacao.md** com 9 seções: ACs ↔ INVs ↔ ADRs ↔ Hooks (todos ACs novos P3) + INVs novas ↔ Drills/Testes (25 INVs × testes) + ADRs ↔ entidades novas ↔ hooks + 33 GATEs Wave A ↔ dependências humanas + 8 hooks novos M4 P9 + 9 eventos publicados + 2 consumers + 5 riscos novos ↔ mitigações + critérios binários de fechamento P3 (17/20 ✅ — restam tasks.md + minutas + matrizes P3.5) + pendências P3.
- **tasks.md** com **160 T-CAL-NNN em 10 fases**: Fase 1 migrations (25) → Fase 2 domain (20) → Fase 3 motor §3.3 (15) → Fase 4 predicates+authz (15) → Fase 5 use cases (30) → Fase 6 queries (8) → Fase 7 jobs (9) → Fase 8 views REST (14) → Fase 9 hooks novos (8) → Fase 10 regressões+drill (16). Inclui **14 tarefas P3.5 paralelas** (minutas OAB + matrizes CGCRE + ADR-0028 rev 3 + DPIA).

### 6. CURRENT.md atualizado + diário criado

Reflete P3 entregue + próxima fatia P4 (Fase 1 migrations).

## Aprendizados desta sessão

1. **3 commits incrementais** ao invés de 1 monolítico — facilita rastreio + reversão se necessário. Batch 1 (ADRs + REGRAS) → Batch 2 (spec + prd) → Batch 3 (matriz + tasks).
2. **Estratégia §16/§11 pós-P3** funcionou tanto pro spec quanto pro PRD — adicionar seção consolidada no fim ao invés de editar 660+ linhas cirurgicamente. Preserva histórico P1 + crava estado P3 + auditável via matriz-reconciliacao.
3. **160 T-CAL pra M4 vs 147 T-OS pra M3** — coerente: M4 tem motor de cálculo + 6 zonas ILAC G8 + 19 tabelas + 8 hooks novos + 30 fixtures replay. Densidade técnica esperada.
4. **Hooks 312/312 mantidos verdes** ao longo dos 3 commits — sinal de que retrofit de docs/ADRs/REGRAS não tocou paths sensíveis com hook ativo.
5. **17/20 critérios de fechamento P3 ✅** — 3 restantes são P3.5 (minutas + matrizes — não bloqueiam P4 dogfooding) + tasks.md já entregue. P3 considera-se ENTREGUE com tasks.md gravado.
6. **GATE-CAL-MATRIZES-CGCRE** criado pra consolidar D-M4-4 — uma das 14 tarefas P3.5 pra agente redigir baseado em NIT-DICLA-030 + ILAC G8 + GUM JCGM 100, com selo CGCRE-pendente.

## Próximo passo

**P4 (`/implement`) — Fase 1 migrations (T-CAL-001..025)** assim que Roldão autorizar entrar. Sugestão de paralelização:
- Frente principal: Fase 1 → Fase 2 → Fase 3 → ... sequencial (dependências fortes).
- Frente paralela P3.5: 14 tarefas T-CAL-P35-* (minutas + matrizes + DPIA + ADR-0028 rev 3) podem ir em paralelo sem bloquear, agente cria como rascunhos com selos pendentes.

**Estimativa P4:** 2-3 semanas agente até `Calibracao.Aprovada` publicado em dogfooding + drill `validar_m4_calibracao` 25/25 PASS + auditores Família 5 P5.
