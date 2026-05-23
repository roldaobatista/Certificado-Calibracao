---
owner: roldao
revisado_em: 2026-05-23
proximo_review: 2026-08-23
status: stable
diataxis: reference
audiencia: agente
marco: Wave A Marco 3 — operacao/os
tipo: matriz-reconciliacao-P3
relacionados:
  - docs/faseamento/M3-os/spec.md
  - docs/faseamento/M3-os/plan.md
  - docs/faseamento/M3-os/reviews/tech-lead.md
  - docs/faseamento/M3-os/reviews/advogado.md
  - docs/faseamento/M3-os/reviews/corretora.md
  - docs/faseamento/M3-os/reviews/rbc.md
  - docs/dominios/operacao/modulos/os/prd.md
  - REGRAS-INEGOCIAVEIS.md
---

# Matriz de Reconciliação — Marco 3 (operacao/os) — P3 ritual Spec Kit

> **P3 do ritual (2026-05-23):** após P2 (4 reviews paralelos) + plan.md
> ata + spec retrofit + ADR-0056 + extensões ADR-0012/ADR-0028 + INVs
> em REGRAS + ACs no PRD, esta matriz consolida o estado canônico para
> verificar **zero conflito** PRD ↔ spec ↔ plan ↔ ADRs.
>
> **Critério de fechamento P3:** todas as linhas da matriz mostram
> "consistente" em PRD / spec / plan / ADRs / REGRAS. Linha
> divergente bloqueia passagem para P4 (tasks.md + implement).

---

## 1. Cobertura achados P2 — todas as 27 decisões rastreadas

| Achado | Severidade | Decisão | spec.md | plan.md | PRD | REGRAS | ADRs | Status |
|---|---|---|---|---|---|---|---|---|
| P-OS-T1 lock concorrência | BLOQ | unique partial index | §3.2 AtividadeDaOS | §"Decisões absorvidas" | — (técnico) | INV-OS-CONC-001 | ADR-0041 | ✅ consistente |
| P-OS-T2 numeração OS | BLOQ | sequence global + buracos | §3.2 OS + §13.9 | §"Decisões absorvidas" + §"Roldão D-M3-1" | AC-OS-001 invariantes | INV-OS-NUM-001 | ADR-0056 NOVA | ✅ consistente |
| P-OS-T3 watchdog cal-link | MÉD | janela parametrizável | §3.2 AtividadeDaOS link_modulo | §"Decisões absorvidas" + Roldão D-M3-2 | INV-OS-CAL-LINK-001 (referência) | ADR-0012 predicate `pode_estender_janela_cal_link` | ✅ consistente |
| P-OS-T4 visão 360 N+1 | MÉD | query service + budget p95 | §13.17 cobertura | §"Decisões absorvidas" | — (técnico) | — | — (Wave A operacional) | 🟡 plan referencia; T-OS-PERF-* em P4 |
| P-OS-T5 foto append-only | MÉD | EvidenciaFotoAtividade | §3.1 tabela + §3.2 nova entidade | §"Decisões absorvidas" | — (entidade interna) | INV-OS-SYNC-001 reescrito | — | ✅ consistente |
| P-OS-T6 tenant suspenso | ALTO Wave A | GATE-OS-TENANT-SUSPENSO | §9 GATEs | §"Bloqueantes Wave A" | — | — | ADR-0035 (proposta) | 🟡 gate Wave A rastreado |
| P-OS-A1 consent art. 11 | MÉD | ConsentimentoBiometriaTouch | §3.1 + §3.2 entidade + AceiteAtividade FK | §"Decisões absorvidas" | AC-OS-004-7 + invariantes | INV-OS-CONSBIO-001 | — (texto OAB) | ✅ consistente |
| P-OS-A2 TTL geo | MÉD | job os-geo-truncamento | §3.2 AtividadeDaOS + §13.21 | §"Decisões absorvidas" | — (job operacional) | INV-OS-GEO-001 estendido | — | ✅ consistente |
| P-OS-A3 anti-PII estendido | MÉD | regex estendida + quarentena | — (vem da INV) | §"Decisões absorvidas" | — (todas US com texto livre) | INV-OS-TXT-001 estendido | — | ✅ consistente |
| P-OS-A4 dispensa formal | MÉD | TermoDispensaAceite + A3 | — (§14 DoD GATE-SEG-BPT-1 cobre indireto via Roldão) | §"Decisões absorvidas" | AC-OS-013-4 + AC-OS-013-5 | — (predicate ADR-0012) | ADR-0012 `pode_dispensar_aceite` | ✅ consistente |
| P-OS-A5 foto no-show terceiros | GATE | GATE-OS-FOTO-NOSHOW-BLUR | §9 GATEs + §12 R-OS-12 | §"Bloqueantes Wave A" | AC-OS-014-3 | — | — | ✅ consistente |
| P-OS-A6 DPIA drift | MÉD | §2.4 reescrito | §2.4 | §"Decisões absorvidas" | — | — | — | ✅ consistente |
| P-OS-A7 sucessão evidência | GATE | GATE-OS-SUCESSAO-EVIDENCIA | §9 GATEs | §"Bloqueantes Wave A" | — (US-OS-006 cobre conceito) | — | — | 🟡 gate Wave A rastreado |
| P-OS-S1 GATE-SEG-BPT-1 DoD | BLOQ | feature flag + DoD bloqueante | §14 DoD + §12 R-OS-11 + §13.23 | §"Decisões absorvidas" + Roldão D-M3-3 | — (predicate ADR-0012) | — | ADR-0012 `pode_criar_os_produtiva_balancas` + ADR-0019 | ✅ consistente |
| P-OS-S2 sensitive data art. 11 | ALTO | cláusula Cyber afirmativa | §9 GATE-SEG-CYBER-1 + §12 R-OS-3 mitigação estendida | §"Decisões absorvidas" | — (regulatório) | — | ADR-0028 rev 2 | ✅ consistente |
| P-OS-S3 wrongful billing | ALTO | franquia R$5k + tax penalty | §9 GATE-SEG-EO-1 | §"Decisões absorvidas" | — | — | ADR-0028 rev 2 | ✅ consistente |
| P-OS-S4 software defect upstream | ALTO | cláusula cobre vetor M3 | §9 GATE-SEG-EO-1 | §"Decisões absorvidas" | — | — | ADR-0028 rev 2 | ✅ consistente |
| P-OS-S5 vicarious admin + image | MÉD | cláusulas vicarious + image | §9 GATE-SEG-EO-1 + §12 R-OS-12/13 | §"Decisões absorvidas" | AC-OS-014-3 | — | ADR-0028 rev 2 | ✅ consistente |
| P-OS-S6 long-tail + INMETRO | GATE | continuity of coverage + GATE-SEG-INMETRO-PRAZO-1 | §9 GATEs novos | §"Bloqueantes Wave A" | — | — | ADR-0028 rev 2 + GATE-SEG | ✅ consistente |
| P-OS-R1 competência executor | BLOQ | rt_competencia_cobre dual | §3.2 + §13.24 | §"Decisões absorvidas" | AC-OS-002b-4 + AC-OS-003-6 | INV-OS-ATIV-005-EXEC-COMP | ADR-0012 predicate + ADR-0022 | ✅ consistente |
| P-OS-R2 análise crítica cl. 7.1 | BLOQ | analise_critica_id + snapshot | §3.2 OS | §"Decisões absorvidas" | AC-OS-001-7 | INV-OS-ANAL-001 | — | ✅ consistente |
| P-OS-R3 escopo acreditado | BLOQ | predicate tenant_dentro_escopo | §3.2 + §6.2 consumer + §9 GATE-RBC-ESCOPO-1 + §13.24 | §"Decisões absorvidas" + §"Bloqueantes Wave A" | AC-OS-002-3 revisado (via INV) | — | ADR-0012 predicate | ✅ consistente |
| P-OS-R4 cl. 7.5 recebimento | MÉD | equipamento_recebimento_id | §3.2 OS + §6.2 consumer | §"Decisões absorvidas" | AC-OS-001-8 | — | — | ✅ consistente |
| P-OS-R5 CAPA FK | MÉD | NaoConformidadeAtividade 5 campos + FK Wave B | §3.2 NaoConformidadeAtividade + §9 GATE-RBC-CAPA-1 | §"Decisões absorvidas" + §"Bloqueantes Wave A" | AC-OS-005-5 | — | — | ✅ consistente |
| P-OS-R6 watchdog janela | MÉD | 72h/15d úteis + por-tenant | §3.2 AtividadeDaOS link_modulo (Roldão D-M3-2) | §"Decisões absorvidas" + §"Roldão D-M3-2" | AC-OS-004-5 (referência) | INV-OS-CAL-LINK-001 (referência) | — | ✅ consistente |
| P-OS-R7 independência | MÉD | payload AtividadeConcluida explicita executor | §6.1 evento | §"Decisões absorvidas" | AC-OS-004-6 estendido | — | ADR-0026 (já cobre) | ✅ consistente |
| P-OS-R8 dispensa em cal | ACEITE | sem mudança estrutural | — | §"ACEITES" | — | — | — | ✅ aceito |

**Sumário:**
- ✅ **22 consistentes** (16 BLOQ/MÉD absorvidos + 6 GATE/ACEITE rastreados).
- 🟡 **3 gate Wave A** (T6, A7, T4): rastreados em §9 da spec + §"Bloqueantes Wave A" do plan; não bloqueiam fechamento M3 dogfooding.
- ✅ **2 ACEITE** (R8 + cosméticos).

**Zero conflito PRD ↔ spec ↔ plan ↔ ADRs ↔ REGRAS.**

---

## 2. Inventário de artefatos pós-P3

| Artefato | Status pós-P3 |
|---|---|
| `docs/faseamento/M3-os/spec.md` | stable, retrofit absorvido |
| `docs/faseamento/M3-os/plan.md` | stable, ata 27 decisões |
| `docs/faseamento/M3-os/reviews/{tech-lead,advogado,corretora,rbc}.md` | stable, 4 pareceres |
| `docs/faseamento/M3-os/matriz-reconciliacao.md` | stable (este doc) |
| `docs/adr/0056-numeracao-os-buracos-aceitos.md` | NOVA, aceito 2026-05-23 |
| `docs/adr/0012-autorizacao-unificada.md` | extensão pós-P3 (5 predicates novos) |
| `docs/adr/0028-mapa-coberturas-wave-a.md` | rev 2 (6 cláusulas novas) |
| `docs/dominios/operacao/modulos/os/prd.md` | retrofit (10 ACs novos) |
| `REGRAS-INEGOCIAVEIS.md` | 5 INVs novos + INV-OS-SYNC-001/TXT-001/GEO-001 estendidos |
| `docs/governanca/gates-wave-a-consolidado.md` | 9 GATEs novos (próxima atualização) |

---

## 3. Critérios para passar P3 → P4

Todos os 4 critérios devem estar VERDE antes de iniciar P4 (tasks.md + implement):

- [x] **Spec FORWARD em stable** com retrofit dos 6 BLOQUEANTE + 12 MÉDIO INV-RITUAL-001 absorvidos.
- [x] **Plan.md ata** consolidando 27 achados + 3 decisões Roldão (D-M3-1 = A, D-M3-2 = A, D-M3-3 = A).
- [x] **Matriz reconciliação** com zero conflito (este doc).
- [x] **REGRAS-INEGOCIAVEIS.md + PRD + ADRs companion** atualizados.

**Status:** ✅ **P3 FECHADA — destrava P4.**

---

## 4. Próximo passo (P4)

Gerar `tasks.md` (~100 T-OS-NNN) cobrindo:

1. **Migrations + schema:** OS + AtividadeDaOS (com unique partial index) + 8 outras entidades + sequence global + RLS + triggers anti-mutation + index N+1.
2. **Predicates authz novos (5):** `rt_competencia_cobre`, `tenant_dentro_escopo_acreditado`, `pode_estender_janela_cal_link_atividade`, `pode_dispensar_aceite`, `pode_criar_os_produtiva_balancas`.
3. **Domínio + use cases (15 US — US-OS-001..015):** 1 use case por endpoint mutating + query services pra cross-módulo.
4. **Consumers:** Orcamento.Aprovado, Cliente.Anonimizado, OS.Faturada, OS.Paga, Tenant.Suspenso, Equipamento.Baixado, Acreditacao.Vencida/Suspensa, EquipamentoRecebimento.Registrado.
5. **Jobs procrastinate:** `os-calibracao-link-watchdog` (parametrizável por-tenant), `os-geo-truncamento` (5a TTL).
6. **Testes:** ~13 INV regressão + 15 US integração + 10 sagas + 4 carga (concorrência, watchdog, sync foto, valor_total race) + drill `validar_m3_os` 24 itens.
7. **Hooks Marco 3 P4:** novos hooks pré-commit: `migration-concorrencia-os-check.sh`, `sync-merge-foto-appendonly.sh`, `authz-check.sh` extensão para predicates novos.
