# .agent/CURRENT.md

> ≤40 linhas. Histórico expandido em `docs/faseamento/diario/`.

**Fase:** Marco 1 **FECHADO** + Marco 2 `equipamentos` em P4 (T-EQP-001
+ T-EQP-006 + T-EQP-002 entregues). Sessão encerrada 2026-05-21 noite.
**Modo:** AUTÔNOMO.

## Estado da suíte (verificado 2026-05-21 após T-EQP-002)

- Suite: **510 passed** (+27 desde encerramento: 18 SEC-QR-001 + 2 gate prod + 7 etiqueta)
- Hooks: **179/179** verdes (22 ativos — +1 `qr-hmac-check`)
- Cobertura: ≥85% global; ≥90% agregado clientes/ (Marco 1)
- Drills: `validar_f_a` 5/5 + `validar_f_b` + `validar_m1_clientes` verdes
- `makemigrations --check`: limpo; ruff + mypy zero issues

## Marco 1 `clientes` — FECHADO

P5 10 auditores Família 5 = ZERO CRÍTICO/ALTO/MÉDIO. Consolidado em
`docs/faseamento/M1-clientes/auditoria-familia5.md`. GATE-CLI-1..8
rastreados Wave A.

## Marco 2 `equipamentos` — em P4

- **P1+P2+P3**: spec forward (6 US + US-EQP-007, ~42 AC, 14 INVs) + plan
  com 4 reviews + matriz greenfield + 65 T-EQP-001..105 em 12 fases.
  Detalhes em `docs/faseamento/M2-equipamentos/`.
- **P4 T-EQP-001 ✅**: modelo `Equipamento` + migration RLS + 3 triggers PG
  (INV-EQP-001 snapshot imutável, anti-órfão LGPD, máquina 7 estados).
- **P4 T-EQP-006 ✅** (2026-05-21): SEC-QR-001 cravado — `QR_HMAC_KEY_REGISTRO`
  versionado prefixo `qrN:` + gate prod (chave dedicada ≥32, distinta de PII)
  + modelo `QRCode` (UNIQUE+RLS+trigger imutabilidade só `revogado_em` muta)
  + helper único `services_qr.py` + hook `qr-hmac-check.sh` (3 bloqueios) +
  18 regressão + SEC-QR-001 em `REGRAS-INEGOCIAVEIS.md`.
- **P4 T-EQP-002 ✅** (2026-05-21): etiqueta PDF — WeasyPrint 62.3+libpango/libcairo
  no Dockerfile + service `gerar_etiqueta_pdf` (60×40mm; TAG+NS+fabricante+
  nome_fantasia, sem PII) + `garantir_qrcode_vigente` idempotente consumindo
  T-EQP-006 + endpoint POST `/api/v1/equipamentos/{id}/etiqueta.pdf/` com
  Cache-Control private 60s + matriz authz (`equipamentos.ler` +
  `equipamentos.imprimir_etiqueta`) + 7 testes (happy + idempotência +
  cross-tenant 404 + authz 403 + anti-PII).

## Próximo passo

1. **T-EQP-003**: POST `/etiqueta.pdf/` exige `Idempotency-Key` (P-EQP-T6
   tabela PG 24h) — atualmente reusa o QR vigente mas não rejeita replay
   distinto com mesma chave.
2. **US-EQP-007** (T-EQP-061..065): RT tenant (P-EQP-R10 BLOQUEANTE RBC).
3. **Fundação restante** T-EQP-004/005/007/008/009/010/011 (UNIQUE parcial
   já existe via `Equipamento`; INV-EQP-LOC-001 validator; evento Criado).
4. Sequência em `docs/faseamento/M2-equipamentos/tasks.md` §"Próximo passo".

## Pendências rastreadas (não bloqueiam)

- ADR-0018 (PWA scanner QR) — aguardando aceite Roldão antes de US-EQP-003.
- ADR-0019 Pilar 2 — apólice cyber+E&O pré-1º tenant externo pago.
- GATE-EQP-1..PENTEST (14 itens Wave A — `docs/faseamento/M2-equipamentos/plan.md`).
