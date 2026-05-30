# .agent/CURRENT.md

> ≤40 linhas. Histórico expandido em `docs/faseamento/diario/`. **Modo:** AUTÔNOMO.
> Contagens vivas: `docs/governanca/STATUS-GERADO.md` (geradas por `scripts/status-projeto.sh`).

**Fase:** WAVE A em curso. **M5 `metrologia/padroes` FECHADO (2026-05-29)** — 1º módulo Wave A entregue. Histórico P1→P10 em `docs/faseamento/diario/2026-05-29-m5-padroes-p1-p10.md`; reconciliação + veredito em `docs/faseamento/M5-padroes/matriz-reconciliacao.md` (§7).

**M5 — fechamento:** ritual completo P1→P10. P9 (10 auditores) abriu achados; Roldão mandou construir os 3 (dossiê CGCRE + carta read-model + vínculo auxiliar CRUD); P10 entregou via REST (INV-PAD-007 provado ponta-a-ponta). Re-passada INV-RITUAL-003 (9 auditores) + confirmação (8 auditores) = **8 PASS, zero achado bloqueante** — todos os achados de gravidade média resolvidos na causa-raiz; 3 BAIXO viraram GATE rastreado (GATE-LGPD-PAD-DOSSIE-1 / GATE-OBS-PAD-CORRELACAO-LOG / GATE-SEG-PAD-DEFESA-PROFUNDIDADE). Verificação independente: **p5+p10 23/23 verde**, ruff/mypy limpos, hooks 450/450 + 2 gates, drill `validar_m5_padroes` 43/43. INV-RITUAL-001 satisfeito. Frontmatter dos docs M5 promovido `draft→stable`. Commits da fase: `d6e1f69`/`d37011c`/`152fbf1`/`dab606e` + fechamento.

**EM CURSO — M6 `metrologia/escopos-cmc` (3º módulo Wave A; decisão Roldão 2026-05-29):** ritual P0-P3 (planejamento) FECHADO. Dossiê (workflow 5 leitores, 80 achados) → spec v2 → plan v2 `ready-for-tasks` → tasks (5 fatias, T-ECMC-NNN). Revisões tech-lead + RBC = APROVA COM CORREÇÕES (2 CRÍTICO + 6 ALTO) → **3 ADRs aceitas: 0073** (validação metrológica no use case, não no permission layer DRF), **0074** (cobertura RBC tridimensional: faixa ⊆ escopo + U≥CMC ILAC-P14 §5.5 + menor-CMC-por-faixa; INV-ECMC-009), **0075** (capacidade interna B/C/D ≠ CMC acreditada A — separação terminológica cl. 8.1.3) + emenda ADR-0066. Decisões Roldão: rótulo "CMC (menor incerteza declarada)" + **extração automática do PDF CGCRE** (com conferência humana — Fatia 4) + **todos os perfis declaram** (A=RBC, B/C/D=capacidade interna). Investigação T-ECMC-000 (regra #0): `cmc_cobre` testado isolado (49 verdes), sem teste view-level — wire-in é adição no use case, não drop-in. **Próximo: /implement Fatia 1a (domínio puro), ambiente de pé.** Docs em `docs/faseamento/M6-escopos-cmc/`.

**Pendente do M6 (decisão de produto aberta ao Roldão — veto):** terminologia de B/C/D ("Capacidade interna declarada (sem acreditação RBC)" — refinamento RBC da decisão do Roldão por cl. 8.1.3).

**Próximo módulo Wave A (após M6):** `metrologia/procedimentos-calibracao` (destrava GATE-CAL-PROC-PREDICATE) — ou outro à escolha do Roldão.

**Suíte (2026-05-29):** hooks `_test-runner` 450/450 + gate anti-drift verde / 55 hooks. Drill `validar_m5_padroes` 43/43 PG-real. M5 ~57 testes verdes. ruff/mypy limpos.

**Melhorias de processo aplicadas (auditoria máquina-dev 2026-05-29):** fatiamento obrigatório (INV-RITUAL-002), roteamento de auditores por risco ATIVO (INV-RITUAL-003), contador automático de contagens (`scripts/status-projeto.sh`), guia de armadilhas de teste (`docs/operacao/testes-armadilhas.md`). Relatório + itens estagiados: `docs/faseamento/auditorias/AUDITORIA-MAQUINA-DEV-rodada-1.md`. INV-RITUAL-001 (MÉDIO bloqueia) mantido por decisão do Roldão.

**Decisões Roldão recentes:** HTMX + 5 SPAs / Aferê PJ separada depois / zero contratações externas até produção real / resolver TUDO (crítico→baixo) / fatiar + roteamento + banco-real-no-ciclo (auditoria 2026-05-29).

## Pendências cross-marco (TRACK Wave A)
- GATE-OS-VALIDAR-DRILL + GATE-CAL-DRILL-LOCAL — drills PG real (1d).
- GATE-OS-GRANDEZA-EM-ATIVIDADE — retrofit `AtividadeDaOS.grandeza` nos 3 use cases M3 (1.5d, fecha ADR-0063).
- T-CAL-125/129 — camada REST OrcamentoIncerteza/Subcontratacao ViewSet (destravados).
- T-CAL-130/131/133 — PadraoViewSet/Escopo/Proficiencia exigem módulos `escopos-cmc` + `procedimentos` (Wave A).
- F-C2 dev (structlog real + health/ready + SIGTERM + correlation_id). GATEs externos em `gates-externos-pre-producao.md` (a criar).
