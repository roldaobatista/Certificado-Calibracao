# .agent/CURRENT.md

> ≤40 linhas. Histórico expandido em `docs/faseamento/diario/`.

**Fase:** **Wave A Marco 2 `equipamentos` em ritual Spec Kit P2**
(2026-05-21). Marco 1 `clientes` **FECHADO** via ritual completo no
mesmo dia. **Modo:** AUTÔNOMO.

## Estado da suíte (verificado 2026-05-21 pós Marco 1 P5 reauditado)

- Suite: **475 passed**, cobertura **86.78% global** / **90% agregado clientes/**
- Hooks: **168/168** verdes (21 ativos; +`lgpd-policy-unica` +`csv-safety-import` Marco 1)
- Drills: `validar_f_a` 5/5 + `validar_f_b` + `validar_m1_clientes` verdes
- `makemigrations --check`: limpo

## Marco 1 `clientes` — FECHADO (commits 75c8b3c..d608071)

P5 10 auditores Família 5 — rodada 1: 7 PASS + 3 FAIL (segurança, qualidade,
drift-docs). Rodada 2 reauditada após conserto causa-raiz: **ZERO CRÍTICO/ALTO/MÉDIO**.
Consolidado: `docs/faseamento/M1-clientes/auditoria-familia5.md`.

Reparos causa-raiz no fechamento:
- ALTO-1 SEC: migration `audit/0015` substitui SHA256 cru por `pii_hash_hmac` (HMAC + GUC `app.pii_hash_key_ativa`)
- MÉDIO-1 SEC: `Cliente.objects.filter(tenant_id=active, id=...)` em 6 rotas (defesa em profundidade)
- MÉDIO-1 QUAL: property-based `resolver_cliente_canonico` 100→1000 cadeias
- MÉDIO-2 QUAL: cobertura clientes/ 87→90% (+10 testes endpoints/clean)
- MÉDIO-3 QUAL: criado `tests/regressao/inv_cli_*.py` (22 testes)
- 8 ALTO drift-docs: AGENTS/CLAUDE/CURRENT/spec números atualizados, ADR-0020/0021 listadas, §12 saneado

Gates Wave A rastreados (não bloqueiam): GATE-CLI-1..8.

## Marco 2 `equipamentos` — em P2 (2026-05-21)

- P1 spec forward ✅ (commit `39b605f`): `docs/faseamento/M2-equipamentos/spec.md`,
  6 US + US-EQP-002b, ~42 AC, 12 non-goals, 3 INVs novos (INV-EQP-001/002, SEC-QR-001),
  12 eventos no bus, 6 portas/stubs (BloqueioClienteQueryService real via Marco 1).
- P2 em andamento: 4 reviews paralelos dos subagentes (tech-lead, advogado, RBC, corretora).
- Próximo: absorver bloqueantes em `plan.md` → P3 matriz greenfield → P4 implementação T-EQP.

## Pendências rastreadas (não bloqueiam fechamento)

- ADR-0018 (PWA scanner QR) — aguardando aceite Roldão antes de US-EQP-003.
- Apólice cyber + RC profissional pré-1º tenant externo pago (ADR-0019 Pilar 2).
- Marco 1 GATE-CLI-1..8 (Wave A — módulos futuros + endurecimento operacional).
