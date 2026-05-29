# .agent/CURRENT.md

> ≤40 linhas. Histórico expandido em `docs/faseamento/diario/`. **Modo:** AUTÔNOMO.
> Contagens vivas: `docs/governanca/STATUS-GERADO.md` (geradas por `scripts/status-projeto.sh`).

**Fase:** WAVE A em curso. 1º módulo = **M5 `metrologia/padroes`** (ADR-0040). Ritual Spec Kit rodado P1→P9; **P10 em curso** (construir os 3 itens que faltam pra fechar). Histórico detalhado P1→P10 em `docs/faseamento/diario/2026-05-29-m5-padroes-p1-p10.md`.

**M5 — estado:** P1-P8 entregues + GATE-OBS-PAD-WORM-1 resolvido (`0a48ea9`). P9 (10 auditores) deu 7 PASS + 2 FAIL (produto+performance) + drift-docs CONCERNS → 1 ALTO + 6 MÉDIO + 9 BAIXO. MÉDIO+ bloqueia (INV-RITUAL-001) — M5 segue **aberto**. Roldão decidiu construir os 3 (dossiê CGCRE + carta read-model + vínculo auxiliar CRUD) antes de encerrar. P10 backbone entregue (`b1ef289`): use cases + query services + repo + eventos prontos.

**P10 ENTREGUE (2026-05-29) — falta só VERIFICAR e confirmar:**
- ✅ Fatia A: REST vínculo auxiliar (CRUD) + dossiê CGCRE + carta-controle (gate perfil A) + migration 0007 seed authz + eventos vínculo + 12 E2E + PERF-001 baseline. INV-PAD-007 provado via REST. Commits `d6e1f69`/`d37011c`/`152fbf1`.
- ✅ Re-passada INV-RITUAL-003 (9 auditores): 7 PASS + 2 CONCERNS; 3 MÉDIO detectados e resolvidos na 2ª leva (`dab606e`): AC-PAD-006-1 dossiê +uso_em_calibracoes(M4)+ancora hash-chain(ADR-0064); AC-PAD-008-1 carta gate ≥10 pontos/24m; drift D4 contagem. BAIXOs: idempotency hook cobre metrologia/*; 2 BAIXO viram GATE (GATE-LGPD-PAD-DOSSIE-1 + GATE-OBS-PAD-CORRELACAO-LOG).

**PENDENTE pra FECHAR M5 (Docker caiu — engine WSL travado em 2026-05-29; reabrir Docker Desktop):**
1. **Verificar a 2ª leva** (commit `dab606e` é WIP não-rodado): `ruff` + `mypy query_service.py` + `pytest --no-cov --reuse-db tests/test_m5_padroes_api_p5.py tests/test_m5_padroes_api_p10.py` (rodar p5 antes pra primar reseed da 0007). Consertar o que falhar.
2. **Re-passada de CONFIRMAÇÃO** (só produto + drift-docs — os 2 que tinham CONCERNS) até zero MÉDIO+.
3. Só então: encerrar M5 + promover frontmatter dos docs M5 `draft→stable`.
Hooks 450/450 + 2 gates verdes (local, não dependem de Docker).

**Suíte (2026-05-29):** hooks `_test-runner` 450/450 + gate anti-drift verde / 55 hooks. Drill `validar_m5_padroes` 43/43 PG-real. M5 ~57 testes verdes. ruff/mypy limpos.

**Melhorias de processo aplicadas (auditoria máquina-dev 2026-05-29):** fatiamento obrigatório (INV-RITUAL-002), roteamento de auditores por risco ATIVO (INV-RITUAL-003), contador automático de contagens (`scripts/status-projeto.sh`), guia de armadilhas de teste (`docs/operacao/testes-armadilhas.md`). Relatório + itens estagiados: `docs/faseamento/auditorias/AUDITORIA-MAQUINA-DEV-rodada-1.md`. INV-RITUAL-001 (MÉDIO bloqueia) mantido por decisão do Roldão.

**Decisões Roldão recentes:** HTMX + 5 SPAs / Aferê PJ separada depois / zero contratações externas até produção real / resolver TUDO (crítico→baixo) / fatiar + roteamento + banco-real-no-ciclo (auditoria 2026-05-29).

## Pendências cross-marco (TRACK Wave A)
- GATE-OS-VALIDAR-DRILL + GATE-CAL-DRILL-LOCAL — drills PG real (1d).
- GATE-OS-GRANDEZA-EM-ATIVIDADE — retrofit `AtividadeDaOS.grandeza` nos 3 use cases M3 (1.5d, fecha ADR-0063).
- T-CAL-125/129 — camada REST OrcamentoIncerteza/Subcontratacao ViewSet (destravados).
- T-CAL-130/131/133 — PadraoViewSet/Escopo/Proficiencia exigem módulos `escopos-cmc` + `procedimentos` (Wave A).
- F-C2 dev (structlog real + health/ready + SIGTERM + correlation_id). GATEs externos em `gates-externos-pre-producao.md` (a criar).
