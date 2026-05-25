# .agent/CURRENT.md

> ≤40 linhas. Histórico expandido em `docs/faseamento/diario/`.

**Fase:** F-A+F-B + M1 + M2 + F-C1 + M3 OS FECHADAS. **M4 calibracao P3 ENTREGUE + P4 Fase 1 FECHADA (25/25) + P4 Fase 2 FECHADA (T-CAL-026..039 em 3 batches — 5 VOs + helpers crypto + 3 predicates; 105 testes verdes).**
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

## P4 Fase 1 — 23/25 migrations entregues hoje (23 entidades + triggers + cross-marco M3)

T-CAL-001..014 + T-CAL-015..017+021 + T-CAL-018..020+023 + T-CAL-024 fechadas em 12 commits incrementais (ac71dc0 → 3eb9b74 → 7780511 → 5754785 → bfd49b4 → 9e45e28 → e20f86a → [batch] → 65a75e0 → 774ba76 → a5aa840 → a40dcdd → 736e61b):

**23 entidades persistidas em PG (todas com RLS + triggers WORM/transição):**
1. `calibracao` (raiz agregado — 50 campos + CAS revision + 6 zonas ILAC G8 + PFA/PRA).
2. `leitura` (UNIQUE composto ADR-0065 + INV-CAL-CONC-001).
3. `leitura_correcao` (rasura digital cl. 7.5).
4. `condicoes_ambientais` (`dentro_tolerancia` GENERATED ABS+CASE).
5. `orcamento_incerteza` (algoritmo_1/2 JSONB + divergencia + replay_hash + bias).
6. `componente_incerteza` (Tipo A n≥6 CHECK + correlação self-FK CHECK).
7. `orcamento_por_ponto` (UNIQUE ponto).
8. `padrao_usado` (snapshot ADR-0040 + UNIQUE parcial + snapshot_lock one-way + trigger anti-snapshot-retroativo INV-CAL-RT-COMP-001 + vinculacao SI estruturada).
9. `recepcao_item_calibracao` (cl. 7.4 + CHECK XOR foto/recusa + CHECK INAPTO motivo).
10. `medicao_controle` (Western Electric + escore_z + trigger EXCEÇÃO job atualiza regra_we).
11. `evento_de_calibracao` (hash-chain por calibracao + sequencia_local IDENTITY via trigger + UNIQUE seq + append-only WORM).
12. `nao_conformidade` (CHECK XOR origem + trigger INV-CAL-NC-002/003 transição + estado-máquina 6 estados).
13. `analise_impacto_nc_proficiencia` (janela ao invés array — P-CAL-T8 + status RECALL_PENDENTE_M5).
14. `plano_acao_proficiencia_warning` (P-CAL-R8 |z|∈(2,3] + WORM full).
15. `laboratorio_subcontratado` (Padrão C soft-delete + PII Zona B + CHECK DPA internacional + vigencia ADR-0030).
16. `aceite_subcontratacao` (WORM + CHECK TOUCH→declaração + INV-CAL-SUBC-001).
17. `avaliacao_periodica_subcontratado` (WORM 1:N + CHECK score 0-10 + decisão MANTER/ACOMPANHAMENTO/DESCREDENCIAR).
18. `aceite_regra_decisao` (WORM + CHECK nivel_confianca [0.80, 0.99] + ADR-0024 revisado).
19. `override_regra_decisao_cliente` (WORM + contrato_clausula_id + justificativa ≥50 chars).
20. `reclamacao_calibracao` (estado-máquina RECEBIDA→EM_ANALISE→RESPONDIDA→ARQUIVADA + CHECK respondida completa + US-CAL-018 + CDC art. 26).
21. `consentimento_contato_tecnico_cliente` (WORM parcial + revogado_em LGPD art. 18 + CHECK temporal + trigger des-revogar bloqueado).
22. `consentimento_foto_recusado` (WORM + motivo ≥30 chars + texto_aviso REQUER OAB + P-CAL-A5).
23. `evento_backup_metrologico` (WORM append-only + resultado OK/FALHA_PARCIAL/FALHA_TOTAL + INV-CAL-BACKUP-001 retenção 25a).

**Cross-marco M3 (T-CAL-024):** `AtividadeDaOS.grandeza VARCHAR(50) DEFAULT ''` + index parcial `atv_tenant_grandeza_partial_idx` (ADR-0063 Opção A lazy).

**Total artefatos PG criados nesta sessão (12 commits):** ~27 funções PL/pgSQL + ~27 triggers + ~12 CHECK constraints + ~16 UNIQUE constraints + ~52 policies RLS + 1 GENERATED column + 1 sequence global + 1 index parcial cross-marco. Hooks `_test-runner.sh` 312/312 verdes ao longo dos 12 commits.

## Próxima fatia

**P4 Fase 2 FECHADA** (3 batches em 3 commits):
- Batch A (`ac33195`) — T-CAL-026..030: 5 VOs novos M4 — `VersaoMotorCalculo`, `EscoreZ`+`ClassificacaoZ`, `ZonaILACG8`, `HashVersionadoV0`, `IncertezaCombinada`. 36 testes.
- Batch B (`c8a3710`) — T-CAL-031..036: helpers crypto puros em `src/domain/metrologia/calibracao/hash_versionado.py` — `validar_versao`, `parsear_hash_versionado`, `formatar_hash_versionado`, `canonicalizar_payload_para_hmac`. 46 testes (replay determinístico 50x + 1-bit-diff).
- Batch C (`7088fc7`) — T-CAL-037..039: 3 predicates ABAC em `src/infrastructure/calibracao/predicates_calibracao.py` — `cmc_cobre` (STUB Wave A), `procedimento_vigente_para` (STUB Wave A), `pode_aprovar_revisao_2a_conferencia` (REAL — segregação funções cl. 6.2.5 + ADR-0026 exceção 4 condições). 23 testes.

**Total Fase 2: 105 testes verdes** + ruff/mypy limpos + hooks 312/312.

**Decisão de escopo (P4 Fase 2 Batch C):** Entities domain (originalmente T-CAL-040..045) DIFERIDAS para Fase 5 (use cases). Criar dataclasses domain agora sem consumidor seria especulação — quando use case precisar, dataclass nasce alinhada ao consumo real.

**Próxima fatia: P4 Fase 3 — Motor de cálculo §3.3 spec (T-CAL-046..060, 15 tarefas)**
- `src/domain/metrologia/calibracao/motor_calculo/`:
  - `gum_classico.py` — Decimal puro, NIT-DICLA-030 rev. 15
  - `monte_carlo.py` — NumPy, JCGM 101 BIPM, seed em Calibracao.id
  - `arredondamento.py` — NIT-DICLA-030 §7.5 (2 dígitos significativos)
  - `validacao_replay.py` — Replay determinístico CI (fixtures `tests/replay_metrologico/`)
- Algoritmos rodam paralelos; divergência >1% → estado volta `em_execucao` + NC automática.

**Paralelizável (P3.5 — não bloqueia P4 dogfooding):** 14 tarefas T-CAL-P35-* (minutas canônicas OAB + matrizes técnicas CGCRE + ADR-0028 rev 3 + DPIA-calibracao). Bloqueia 1º tenant externo pago.

**Paralelizável (P3.5 — não bloqueia P4 dogfooding):** 14 tarefas T-CAL-P35-* (minutas canônicas OAB + matrizes técnicas CGCRE + ADR-0028 rev 3 + DPIA-calibracao). Bloqueia 1º tenant externo pago.

## Pendências Wave A rastreadas (33 GATEs novos M4 — somam aos herdados)

GATE-CAL-* (12 RBC + 8 advogado + 3 tech-lead + 1 matrizes-CGCRE) + GATE-SEG-* (9 corretora) = 33 GATEs novos M4 + GATE-OS-* (~20 M3) + GATE-CYBER-BREAKGLASS-U2F-ENFORCE + GATE-HMAC-RETROFIT-MARCO-2-3 + GATE-KMS-IAM-LOCK + GATE-HMAC-DRILL + GATE-SEG-BPT-1 (emergencial dogfooding).
