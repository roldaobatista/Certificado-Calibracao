---
owner: roldao
revisado_em: 2026-05-25
status: stable
diataxis: explanation
audiencia: agente
tipo: diario-fase
relacionados:
  - docs/faseamento/auditorias/PRE-M4-CALIBRACAO-saneamento.md
  - docs/faseamento/M4-calibracao/spec.md
  - docs/adr/0040-padrao-metrologico-entidade-separada.md
  - docs/adr/0064-rotacao-chave-hmac-retencao-metrologica-25a.md
---

# 2026-05-25 — Saneamento pré-Marco 4 + P1 Marco 4 entregue

> Sessão pós-fechamento M3 OS. Aplicação da lição `feedback_auditar_antes_de_replicar_molde` — auditar criticamente o molde M3 antes de replicar pra M4.

## Sequência

### 1. Levantamento de pendências M4 (paralelo, 4 leituras)

- `docs/faseamento/M3-os/auditoria-familia5.md` — 5 batches conserto causa-raiz documentados.
- `docs/faseamento/auditorias/OS-CAL-CONSOLIDADO-rodada-1.md` — 179 achados (10 lentes).
- `docs/faseamento/auditorias/OS-CAL-CONSOLIDADO-rodada-2.md` — 80 achados novos pós-retrofit.
- `docs/faseamento/auditorias/OS-CAL-RESOLUCAO-rodada-2.md` — 5 ondas (7A-7E) resolveram 65% (52/80). 28 GATEs Wave A criados.

### 2. Dossiê consolidado `PRE-M4-CALIBRACAO-saneamento.md`

7 seções: estado real M4 (PRD draft + 17 US + 14 entidades retrofitadas + 11 ADRs M4); 10 lições G1..G10 do M3 OS; GATEs Wave A aplicáveis; itens MÉDIO/BAIXO não-resolvidos; pré-requisitos por gate (P1/P4/P5/fechamento/1º tenant externo); sumário pro Roldão.

### 3. 3 perguntas respondidas por Roldão

- **ADR-0040** — padrão metrológico em módulo `padroes` SEPARADO (não herdeiro de Equipamento).
- **Subcontratação cl. 6.6** — US-CAL-017 NOVA Wave A (não non-goal).
- **HMAC vs WORM 25a** — rotação anual + histórico KMS Multi-Region (ADR-0064 a criar).

### 4. Saneamento aplicado (commit `27f7699`)

- ADR-0040 frontmatter status `proposta → aceito` (2026-05-25).
- ADR-0064 criada — formato canônico `v<NN>$<base64>` + INV-HMAC-001..005 + 4 GATEs vinculados (RETROFIT-MARCO-2-3, KMS-IAM-LOCK, DRILL, retrofit hashes).
- US-CAL-017 no PRD calibracao — 6 AC + 2 entidades novas (`LaboratorioSubcontratado` + `AceiteSubcontratacao`) + 2 eventos + 4 INV-CAL-SUBC-*.
- Drift AGENTS §11 zerado — ADRs 0021/0024/0025/0026 mostravam 🟡 proposta mas frontmatter era aceito; corrigido; ADR-0040/0064 adicionadas; §12 cita dossiê.

### 5. P1 Marco 4 — spec FORWARD (commit `08264cf`)

`docs/faseamento/M4-calibracao/spec.md` (676 linhas, 13 seções):
- Escopo + 15 non-goals (NG-CAL-1..15).
- 17 entidades + schema sketch + máquina de estados.
- 24 INV-CAL-* + 5 INV-HMAC-* + 6 INV-PAD-* + 4 INV-CAL-SUBC-* + 4 INV-CAL-FRAUDE-* a cravar P3.
- 23 eventos publicados + 8 consumidos.
- 17 user stories ref PRD.
- 17 riscos R-M4-01..17 mapeados (R-M4-11..17 cobrem G1..G10 lições M3).
- 10 lições G1..G10 do M3 OS aplicadas DESDE 1ª linha M4 P4.
- Critérios fechamento M4 + dependências P1→P5.

## Validações antes de cada commit

- Hooks `_test-runner.sh`: **312/312 PASS** após cada modificação.
- Grep palavras-coringa em linhas AC-* do spec M4: zero.

## Próximo passo

**P2 (`/plan`):** gerar `docs/faseamento/M4-calibracao/plan.md` + submeter aos 4 subagentes em paralelo (tech-lead-saas-regulado, advogado-saas-regulado, corretora-seguros-saas, consultor-rbc-iso17025).

## Commits desta sessão

- `27f7699` chore(saneamento pre-M4 calibracao): ADR-0040 + ADR-0064 aceitas, US-CAL-017 adicionada, drift AGENTS zerado
- `08264cf` docs(M4 P1): spec FORWARD calibracao (676 linhas) aplicando 10 lições M3 OS
