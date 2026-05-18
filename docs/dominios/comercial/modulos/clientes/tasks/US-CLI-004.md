---
owner: roldao
revisado_em: 2026-05-18
proximo_review: 2026-08-18
status: stable
diataxis: reference
audiencia: agente
us: US-CLI-004
plano: docs/dominios/comercial/modulos/clientes/planos/US-CLI-004.md
historico:
  - 2026-05-18 noite final — criado retroativo (D1 do `docs/governanca/debitos-ritual.md`).
---

# Tasks T-CLI-019..T-CLI-030 — US-CLI-004 (bloqueio manual + automatico ADR-0015)

> Mapeamento retroativo. Implementacao em commit `58d08df`.

## Mapa task -> commit -> AC -> ressalva

| Task | Descricao | Commit | AC | Endereca |
|---|---|---|---|---|
| T-CLI-019 | Modelo `ClienteBloqueio` (1:N) em `models.py` + property `Cliente.bloqueado` | 58d08df | AC-1, AC-2 | TL1 tech-lead |
| T-CLI-020 | Migration `0008_clientebloqueio.py` + UNIQUE INDEX parcial (cliente_id) WHERE desbloqueado_em IS NULL + CHECK constraints | 58d08df | AC-1 | TL1, TL4 (CHECK enum) |
| T-CLI-021 | Field `Tenant.bloqueio_automatico_inadimplencia_habilitado` (default False) + migration `tenant 0002` | 58d08df | AC-3 | TL5 tech-lead (opt-in tenant) |
| T-CLI-022 | Constants em `bloqueio.py` (MOTIVOS_VALIDOS, CAUSATION_TYPES, JUSTIFICATIVA_MIN_CHARS) | 58d08df | AC-1 | R2 advogado (enum estavel) |
| T-CLI-023 | Predicate registry em `authz/predicates.py` + `predicate cliente_nao_bloqueado` em `clientes/predicates_authz.py` | 58d08df | AC-2, AC-4 | TL2 tech-lead (canal unico authz) |
| T-CLI-024 | Estender `DjangoAuthorizationProvider._decidir()` pra consultar predicates registrados | 58d08df | AC-2, AC-4 | INV-AUTHZ-004 preventiva |
| T-CLI-025 | Endpoints POST `/clientes/{id}/bloquear/` + `/desbloquear/` + idempotencia no-op + `confirmacao_comunicacao_previa` + observacao anti-PII | 58d08df | AC-1, AC-2 | TL3 (idempotencia) + R2 (PII) + R3 (CDC/Lei 14181) |
| T-CLI-026 | Audit `cliente.bloqueado` / `cliente.desbloqueado` com `justificativa_hash` + `event_id` | 58d08df | AC-1, AC-3 | R1 advogado (audit sem PII) |
| T-CLI-027 | Protocol `InadimplenciaSource` + adapter `MockInadimplenciaSource` + command `job_inadimplencia_alertas` | 58d08df | AC-3 | TL5 (ADR-0015 fluxo 4) |
| T-CLI-028 | Migration seed `clientes/0010_seed_authz_bloquear.py` — admin_tenant apenas | 58d08df | AC-1 | SEC-LEAST-PRIV |
| T-CLI-029 | INV-CLI-BLOQ-001 em `REGRAS-INEGOCIAVEIS.md` + atualizar `debitos-ritual.md` com debitos Wave A (R5 procrastinate + R6 gerente_financeiro) | 58d08df | — | TL5 + R5/R6 |
| T-CLI-030 | 15 testes em `tests/test_clientes_us_cli_004_bloquear.py` | 58d08df | todas | todas |

## Pareceres

- `revisoes/US-CLI-004-tech-lead.md` — APROVADO COM RESSALVAS (TL1 modelo 1:N, TL2 predicate registry, TL3 idempotencia, TL4 CHECK enum, TL5 procrastinate diferido)
- `revisoes/US-CLI-004-advogado.md` — APROVADO COM RESSALVAS (R1 audit sem PII, R2 enum + regex anti-PII, R3 CDC/Lei 14.181, R6 view sanitizada admin Afere)

## Total

12 tasks. 15 testes. Commit `58d08df`.
