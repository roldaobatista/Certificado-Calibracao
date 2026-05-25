# .agent/CURRENT.md

> ≤40 linhas. Histórico expandido em `docs/faseamento/diario/`.

**Fase:** F-A+F-B + M1 + M2 + F-C1 + M3 OS FECHADAS. **M4 calibracao P3 ENTREGUE + P4 Fase 1 primeira fatia ENTREGUE (T-CAL-001/002 em commit `ac71dc0`).**
**Modo:** AUTÔNOMO.

## Estado da suíte (2026-05-25)

- pytest geral: **905/0/0** em 26min (último run 2026-05-24).
- Hooks `_test-runner.sh`: **312/312** verdes / **42 hooks ativos**.
- ruff/mypy: limpos nos paths novos.

## M4 calibracao — P3 entregue (matriz reconciliação + tasks.md)

P3 do ritual Spec Kit completo em 3 commits hoje:

- `b1c1d6a` — ADR-0065 nova (concorrência calibração — UNIQUE composto + CAS + advisory lock) + retrofit ADR-0024 (6 zonas ILAC G8 + PFA/PRA + AceiteRegraDecisao) + retrofit ADR-0063 (Opção A lazy — predicate em 3 use cases pós-config) + 24 INVs CAL novos em REGRAS-INEGOCIAVEIS.md.
- `e8c4126` — spec.md §16 absorve 10 BLOQUEANTE + 23 MÉDIO dos 4 reviews + PRD §11 com 11 ACs novos + US-CAL-018 nova (reclamação CDC art. 26). Status spec.md + prd.md draft → stable.
- (este commit) — matriz-reconciliacao.md (zero conflito PRD ↔ spec ↔ plan ↔ ADRs ↔ REGRAS) + tasks.md com 160 T-CAL-NNN em 10 fases (Fase 1 migrations 25 / Fase 2 domain 20 / Fase 3 motor §3.3 15 / Fase 4 predicates+authz 15 / Fase 5 use cases 30 / Fase 6 queries 8 / Fase 7 jobs 9 / Fase 8 views REST 14 / Fase 9 hooks novos 8 / Fase 10 regressões+drill 16) + 14 tarefas P3.5 paralelas (minutas OAB + matrizes CGCRE + ADR-0028 rev 3 + DPIA).

## Decisões cravadas (P2 → P3)

- D-M4-1: GUM Decimal + Monte Carlo NumPy ✓
- D-M4-2: ADR-0063 Opção A lazy ✓
- D-M4-3, D-M4-4, D-M4-5: sem previsão de contratação → agente cria minutas/matrizes preliminares com selos REQUER {OAB,CGCRE,SUSEP} HUMANO.

## P4 Fase 1 — 9/25 migrations entregues hoje (7 entidades + triggers)

T-CAL-001 a T-CAL-007 fechadas em 6 commits incrementais (ac71dc0 → 3eb9b74 → 7780511 → 5754785 → bfd49b4 → 9e45e28):

**Entidades persistidas em PG com RLS + triggers WORM:**
1. `calibracao` (raiz agregado — 50 campos §3.2 + §16.4 + CAS revision + 6 zonas ILAC G8 + PFA/PRA).
2. `leitura` (cl. 7.5 + UNIQUE composto ADR-0065 + INV-CAL-CONC-001).
3. `leitura_correcao` (rasura digital cl. 7.5 + anti-fraude COR-001).
4. `condicoes_ambientais` (cl. 6.3.1 + `dentro_tolerancia` GENERATED via ABS+CASE IMMUTABLE).
5. `orcamento_incerteza` (cl. 7.6 + GUM JCGM 100 + algoritmo_1/2_resultado JSONB + divergencia_pct + replay_determinismo_hash).
6. `componente_incerteza` (NIT-DICLA-030 §6.3/§7.4 + Tipo A n≥6 CHECK + correlação self-FK + coeficiente CHECK).
7. `orcamento_por_ponto` (1:N + UNIQUE ponto).

**Triggers PG criados:** 6 anti-mutation WORM + 1 populador (`calibracao_numero_exibido` BEFORE INSERT) + 1 imutabilidade terminal (`calibracao_anti_mutation_terminal_check` — 18 campos forensicos bloqueiam UPDATE pós-aprovada/rejeitada/cancelada).

**CHECK constraints DDL:** `ck_componente_tipo_a_n_min` + `ck_componente_correlacao_coef`.

**Suite:** pytest regressão 168/168 passou. Hooks `_test-runner.sh` 312/312 verdes ao longo dos 6 commits.

## Próxima fatia

**P4 Fase 1 continuação (T-CAL-008..025) — 16 migrations restantes:**
- PadraoUsado (snapshot ADR-0040 + snapshot_lock pós em_revisao_1) + RecepcaoItemCalibracao (cl. 7.4 — análise crítica + foto + recusa) + MedicaoControle (Western Electric P-CAL-R8 + escore_z) + EventoDeCalibracao (hash-chain por calibracao_id + sequencia_local + advisory lock).
- NaoConformidade (cl. 7.10/8.7 + decisão parar/continuar + notificação cliente) + AnaliseImpactoNCProficiência (janela ao invés de array — P-CAL-T8 reescrito) + PlanoAcaoProficienciaWarning (|z|∈(2,3]).
- LaboratorioSubcontratado (cl. 6.6.2 + avaliação periódica + país) + AceiteSubcontratacao (touch/A3 + consentimento contato PF) + AvaliacaoPeriodicaSubcontratado.
- Entidades novas P3: AceiteRegraDecisao + OverrideRegraDecisaoCliente + ReclamacaoCalibracao + ConsentimentoContatoTecnicoCliente + ConsentimentoFotoRecusado + EventoBackupMetrologico.
- Migration cross-marco M3 (`AtividadeDaOS.grandeza`) — ADR-0063 Opção A.

**Paralelizável (P3.5 — não bloqueia P4 dogfooding):** 14 tarefas T-CAL-P35-* (minutas canônicas OAB + matrizes técnicas CGCRE + ADR-0028 rev 3 + DPIA-calibracao). Bloqueia 1º tenant externo pago.

## Pendências Wave A rastreadas (33 GATEs novos M4 — somam aos herdados)

GATE-CAL-* (12 RBC + 8 advogado + 3 tech-lead + 1 matrizes-CGCRE) + GATE-SEG-* (9 corretora) = 33 GATEs novos M4 + GATE-OS-* (~20 M3) + GATE-CYBER-BREAKGLASS-U2F-ENFORCE + GATE-HMAC-RETROFIT-MARCO-2-3 + GATE-KMS-IAM-LOCK + GATE-HMAC-DRILL + GATE-SEG-BPT-1 (emergencial dogfooding).
