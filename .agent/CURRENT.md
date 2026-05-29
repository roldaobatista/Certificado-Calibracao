# .agent/CURRENT.md

> ≤40 linhas. Histórico expandido em `docs/faseamento/diario/`. **Modo:** AUTÔNOMO.
> Contagens vivas: `docs/governanca/STATUS-GERADO.md` (geradas por `scripts/status-projeto.sh`).

**Fase:** WAVE A em curso. 1º módulo = **M5 `metrologia/padroes`** (ADR-0040). Ritual Spec Kit rodado P1→P9; **P10 em curso** (construir os 3 itens que faltam pra fechar). Histórico detalhado P1→P10 em `docs/faseamento/diario/2026-05-29-m5-padroes-p1-p10.md`.

**M5 — estado:** P1-P8 entregues + GATE-OBS-PAD-WORM-1 resolvido (`0a48ea9`). P9 (10 auditores) deu 7 PASS + 2 FAIL (produto+performance) + drift-docs CONCERNS → 1 ALTO + 6 MÉDIO + 9 BAIXO. MÉDIO+ bloqueia (INV-RITUAL-001) — M5 segue **aberto**. Roldão decidiu construir os 3 (dossiê CGCRE + carta read-model + vínculo auxiliar CRUD) antes de encerrar. P10 backbone entregue (`b1ef289`): use cases + query services + repo + eventos prontos.

**FALTA pra encerrar M5 (próxima sessão):**
1. Endpoints REST: POST vínculo criar/revogar (emitir eventos), GET dossie-cgcre (gate perfil A), GET carta-controle (gate perfil A) — views.py + serializers + urls.
2. Migration 0007 seed authz das ações novas (gerir_vinculo_auxiliar + ler dossie/carta).
3. Emitir eventos de vínculo via `_publicar_evento_padrao`.
4. Testes E2E dos 4 endpoints + INV-PAD-007 ativado via REST.
5. PERF-001: teste assertNumQueries baseline + GATE-PAD-PERF-DISPONIVEIS + paginar saída `disponiveis`.
6. Docs: emendar AC-PAD-003-2 (bloqueio lógico); spec §6 +INV-PAD-004/010; plan §7 DoD +INV-PAD-010; matriz parar de mentir US-PAD-006/008-1/007-4; remover pendência §6 obsoleta; frontmatter draft→stable.
7. BAIXOs: mappers model concreto; teste baixar-evento; teste replay idemp.
8. **Re-rodar P9** (produto+performance+drift) até zerar MÉDIO+ → então encerrar M5.

**Suíte (2026-05-29):** hooks `_test-runner` 450/450 + gate anti-drift verde / 55 hooks. Drill `validar_m5_padroes` 43/43 PG-real. M5 ~57 testes verdes. ruff/mypy limpos.

**Melhorias de processo aplicadas (auditoria máquina-dev 2026-05-29):** fatiamento obrigatório (INV-RITUAL-002), roteamento de auditores por risco ATIVO (INV-RITUAL-003), contador automático de contagens (`scripts/status-projeto.sh`), guia de armadilhas de teste (`docs/operacao/testes-armadilhas.md`). Relatório + itens estagiados: `docs/faseamento/auditorias/AUDITORIA-MAQUINA-DEV-rodada-1.md`. INV-RITUAL-001 (MÉDIO bloqueia) mantido por decisão do Roldão.

**Decisões Roldão recentes:** HTMX + 5 SPAs / Aferê PJ separada depois / zero contratações externas até produção real / resolver TUDO (crítico→baixo) / fatiar + roteamento + banco-real-no-ciclo (auditoria 2026-05-29).

## Pendências cross-marco (TRACK Wave A)
- GATE-OS-VALIDAR-DRILL + GATE-CAL-DRILL-LOCAL — drills PG real (1d).
- GATE-OS-GRANDEZA-EM-ATIVIDADE — retrofit `AtividadeDaOS.grandeza` nos 3 use cases M3 (1.5d, fecha ADR-0063).
- T-CAL-125/129 — camada REST OrcamentoIncerteza/Subcontratacao ViewSet (destravados).
- T-CAL-130/131/133 — PadraoViewSet/Escopo/Proficiencia exigem módulos `escopos-cmc` + `procedimentos` (Wave A).
- F-C2 dev (structlog real + health/ready + SIGTERM + correlation_id). GATEs externos em `gates-externos-pre-producao.md` (a criar).
