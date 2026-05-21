# .agent/CURRENT.md

> ≤40 linhas. Histórico expandido em `docs/faseamento/diario/`.

**Fase:** Marco 1 **FECHADO** + Marco 2 `equipamentos` arrancado via
ritual Spec Kit (P1+P2+P3+P4 T-EQP-001 entregues). Sessão encerrada
2026-05-21. **Modo:** AUTÔNOMO.

## Estado da suíte (verificado 2026-05-21 ao encerrar sessão)

- Suite: **483+ passed** (475 Marco 1 + 8 T-EQP-001 fundação Marco 2)
- Hooks: **168/168** verdes (21 ativos)
- Cobertura: ≥85% global; ≥90% agregado clientes/ (Marco 1)
- Drills: `validar_f_a` 5/5 + `validar_f_b` + `validar_m1_clientes` verdes
- `makemigrations --check`: limpo; ruff + mypy zero issues

## Marco 1 `clientes` — FECHADO (commits 75c8b3c..d608071, 6 commits)

P5 10 auditores Família 5 rodada 2 reauditada = **ZERO CRÍTICO/ALTO/MÉDIO**.
Consolidado: `docs/faseamento/M1-clientes/auditoria-familia5.md` (stable).
Reparos causa-raiz: HMAC trigger PG (migration `audit/0015`), filter ORM
tenant_id em 6 rotas, property-based 1000 cadeias, `tests/regressao/inv_cli_*`
(22 testes), drift docs saneado. GATE-CLI-1..8 rastreados Wave A.

## Marco 2 `equipamentos` — em P4 (commits 39b605f..df72f68, 5 commits)

- **P1** spec forward (601 linhas): 6 US + US-EQP-007, ~42 AC, 14 INVs
  (3 novos: INV-EQP-001/002, SEC-QR-001), 14 non-goals, 12 eventos.
- **P2** plan + 4 reviews paralelos: 36 pontos — 3 BLOQUEANTES + 3 ALTOS
  RBC + ~12 MÉDIOS INV-RITUAL-001 absorvidos; 14 GATE-EQP-* rastreados.
- **P3** matriz greenfield + tasks: **65 T-EQP-001..105 planejadas** em
  12 fases (fundação → QR → RT → versionamento → aprovação → ficha →
  transferência → sucatamento → recebimento → hooks → regressão → drill).
- **P4 T-EQP-001 ✅**: modelo `Equipamento` + migration RLS + 3 triggers PG
  (INV-EQP-001 imutabilidade snapshot, anti-órfão LGPD, máquina estados
  7 valores) + 8 testes verdes.

## Próximo passo (retomar)

1. **T-EQP-002 + T-EQP-006**: PDF etiqueta WeasyPrint + QR HMAC versionado
   `QR_HMAC_KEY_REGISTRO` + hook `qr-hmac-check.sh`.
2. **US-EQP-007** (T-EQP-061..065): RT do tenant (P-EQP-R10 BLOQUEANTE RBC).
3. Sequência conforme `docs/faseamento/M2-equipamentos/tasks.md` §"Próximo passo".

## Pendências rastreadas (não bloqueiam)

- ADR-0018 (PWA scanner QR) — aguardando aceite Roldão antes de US-EQP-003.
- ADR-0019 Pilar 2 — apólice cyber+E&O pré-1º tenant externo pago.
- GATE-EQP-1..PENTEST (14 itens Wave A — `docs/faseamento/M2-equipamentos/plan.md`).
