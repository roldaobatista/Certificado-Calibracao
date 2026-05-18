---
owner: roldao
revisado_em: 2026-05-18
proximo_review: 2026-08-18
status: stable
diataxis: reference
audiencia: agente
us: US-CLI-001
plano: docs/dominios/comercial/modulos/clientes/planos/US-CLI-001.md
historico:
  - 2026-05-18 noite final — criado retroativo (D1 do `docs/governanca/debitos-ritual.md`).
---

# Tasks T-CLI-001..T-CLI-008 — US-CLI-001 (cadastro PF/PJ + LGPD + evento + 409)

> Mapeamento retroativo. Implementacao em commit `b130577` (parte LGPD + evento + 409) sobre `ee75ac0` (CRUD basico).

## Mapa task -> commit -> AC -> ressalva

| Task | Descricao | Commit | AC | Endereca |
|---|---|---|---|---|
| T-CLI-001 | `lgpd.py` com constants (`VERSAO_VIGENTE`, `TEXTOS_HISTORICOS`, `ORIGENS_VALIDAS`, `DISPENSAS_VALIDAS`) | b130577 | AC-2 | R2 advogado |
| T-CLI-002 | `docs/conformidade/comum/finalidades-lgpd.md` (catalogo curto) | b130577 | AC-2 | R2 advogado |
| T-CLI-003 | Migration `0004_aceite_lgpd_e_origem.py` — 5 campos LGPD no `Cliente` | b130577 | AC-2 | R3 advogado |
| T-CLI-004 | `Cliente.clean()` aplica regras PF (aceite obrigatorio) vs PJ (dispensa OU aceite) | b130577 | AC-2 | R3 advogado |
| T-CLI-005 | `ClienteSerializer` aceita 5 campos; `aceite_lgpd_versao` injetada auto + `origem='balcao'` default | b130577 | AC-2 | TL2 tech-lead (snapshot legal) |
| T-CLI-006 | `ClienteViewSet.create/perform_create` — IP hash + dedup via queryset (nao IntegrityError) + audit `cliente.criado` | b130577 | AC-1, AC-3 | TL1 (cross-tenant safe) + TL3 (audit sem PII cru) |
| T-CLI-007 | Mensagem de erro VO CPF/CNPJ pra documento estrangeiro | b130577 | AC-1 | — |
| T-CLI-008 | 8 testes em `tests/test_clientes_us_cli_001_completa.py` | b130577 | AC-1, AC-2, AC-3 | todas |

## Pareceres

- `revisoes/US-CLI-001-tech-lead.md` — APROVADO COM RESSALVAS (3 ressalvas: TL1 cross-tenant safe, TL2 snapshot legal, TL3 audit sem PII)
- `revisoes/US-CLI-001-advogado.md` — APROVADO COM RESSALVAS (3 ressalvas: R1 dispensa PJ, R2 origem rastreavel, R3 dispensa motivo enum)

## Total

8 tasks. 8 testes. Commit `b130577` (sobre `ee75ac0` que ja tinha o CRUD basico).
