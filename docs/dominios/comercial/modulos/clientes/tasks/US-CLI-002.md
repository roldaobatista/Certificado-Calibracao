---
owner: roldao
revisado_em: 2026-05-18
proximo_review: 2026-08-18
status: stable
diataxis: reference
audiencia: agente
us: US-CLI-002
plano: docs/dominios/comercial/modulos/clientes/planos/US-CLI-002.md
historico:
  - 2026-05-18 noite final — criado retroativo (D1 do `docs/governanca/debitos-ritual.md`).
---

# Tasks T-CLI-031..T-CLI-040 — US-CLI-002 (visao 360 + INV-013)

> Mapeamento retroativo. Implementacao em commit `deee31d`.

## Mapa task -> commit -> AC -> ressalva

| Task | Descricao | Commit | AC | Endereca |
|---|---|---|---|---|
| T-CLI-031 | Tabela `acessos_dados_cliente` em `audit/` (migration `0004`) + RLS v2 + indices | deee31d | AC-2 | R1 advogado |
| T-CLI-032 | Enum `FinalidadeAcessoCliente` (TextChoices) + CHECK constraint (migration `0005`) | deee31d | AC-2, AC-3 | R2 advogado |
| T-CLI-033 | `registrar_acesso_dados_cliente()` em `audit/services.py` (INSERT-only) | deee31d | AC-2 | R1 advogado |
| T-CLI-034 | Indice expressional `auditoria(tenant_id, payload_jsonb->>'cliente_id', timestamp DESC)` na migration `0005` | deee31d | AC-1 | TL1 tech-lead (performance timeline) |
| T-CLI-035 | Endpoint `GET /api/v1/clientes/{id}/visao-360/?finalidade=X` na view | deee31d | AC-1, AC-2 | R2 advogado (finalidade obrigatoria) |
| T-CLI-036 | Logica: registrar acesso ANTES de ler timeline (INV-013) + LIMIT 200 | deee31d | AC-2 | TL5 tech-lead (DoS) |
| T-CLI-037 | `docs/conformidade/comum/finalidades-acesso-dados.md` (8 finalidades) | deee31d | AC-3 | R2 advogado |
| T-CLI-038 | Migration `clientes/0011_seed_authz_visao360.py` — 4 perfis seed (admin, tecnico, rt_signatario, cliente_externo_leitura) | deee31d | AC-1 | SEC-LEAST-PRIV |
| T-CLI-039 | Atualizar `debitos-ritual.md` com debitos Wave A (outbox pattern) + Wave B (portal titular) | deee31d | — | TL4 tech-lead |
| T-CLI-040 | 7 testes em `tests/test_clientes_us_cli_002_visao360.py` | deee31d | AC-1, AC-2, AC-3 | todas |

## Pareceres

- `revisoes/US-CLI-002-tech-lead.md` — APROVADO COM RESSALVAS (TL1 indice expressional, TL2 outbox debito, TL4 audit-as-event, TL5 LIMIT 200)
- `revisoes/US-CLI-002-advogado.md` — APROVADO COM RESSALVAS (R1 recurso sem PII cru, R2 enum 8 finalidades + CHECK)

## Total

10 tasks. 7 testes. Commit `deee31d`.
