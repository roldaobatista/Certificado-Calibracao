---
owner: roldao
revisado_em: 2026-05-18
proximo_review: 2026-08-18
status: stable
diataxis: reference
audiencia: agente
us: US-CLI-005
plano: docs/dominios/comercial/modulos/clientes/planos/US-CLI-005.md
historico:
  - 2026-05-18 noite final — criado retroativo (D1 do `docs/governanca/debitos-ritual.md`).
---

# Tasks T-CLI-009..T-CLI-018 — US-CLI-005 (mesclar clientes + soft-delete)

> Mapeamento retroativo. Implementacao em commit `953838f`.

## Mapa task -> commit -> AC -> ressalva

| Task | Descricao | Commit | AC | Endereca |
|---|---|---|---|---|
| T-CLI-009 | Migration `0005_soft_delete.py` — campos `deletado_em`, `deletado_por_usuario_id`, `deletado_motivo_categoria` no `Cliente` + index parcial | 953838f | AC-2 | R4 advogado |
| T-CLI-009b | Migration `0006_unique_doc_ativo.py` — UNIQUE INDEX parcial (tenant_id, tipo_pessoa, documento) WHERE deletado_em IS NULL | 953838f | AC-2 | R4 advogado (reativacao pos-mesclagem) |
| T-CLI-010 | `ClienteAtivosManager` (default) filtra soft-deleted; `Cliente.all_objects` expoe deletados (auditoria) | 953838f | AC-2 | TL3 tech-lead |
| T-CLI-011 | Use case puro `application/comercial/clientes/mesclar_clientes.py` recebendo `ClienteRepository` Protocol (ADR-0007) | 953838f | AC-1 | TL1 tech-lead (camada dominio) |
| T-CLI-012 | Protocol `ClienteRepository` em `src/domain/comercial/clientes/repository.py` + adapter `DjangoClienteRepository` em infrastructure | 953838f | AC-1 | TL1 + TL2 (DI) |
| T-CLI-013 | Validacoes: tenants_diferentes, vencedor/perdedor inexistentes, perdedor ja deletado, mesma entidade — todas com ErroMesclagem (code estavel) | 953838f | AC-1, AC-4 | TL5 (defesa profundidade) + TL1 |
| T-CLI-014 | Constants em `mesclagem.py` (MOTIVOS_VALIDOS, JUSTIFICATIVA_MIN, regex anti-PII) | 953838f | AC-3 | R2 advogado (motivo categoria enum) |
| T-CLI-015 | Endpoint POST `/clientes/{vencedor}/mesclar/{perdedor}/` — recebe sobrescritas + motivo_categoria + motivo_observacao | 953838f | AC-1 | TL1 + TL2 |
| T-CLI-016 | Audit `cliente.mesclado` com `vencedor_id`, `perdedor_id`, `campos_sobrescritos_keys`, `motivo_categoria`, hashes (sem PII cru) | 953838f | AC-3 | R1 advogado |
| T-CLI-017 | Migration seed `clientes/0007_seed_authz_mesclar.py` — admin_tenant apenas | 953838f | AC-1 | SEC-LEAST-PRIV |
| T-CLI-018 | 9 testes em `tests/test_clientes_us_cli_005_mesclar.py` | 953838f | todas | todas |

## Pareceres

- `revisoes/US-CLI-005-tech-lead.md` — APROVADO COM RESSALVAS (TL1 Repository Protocol, TL2 DI, TL3 soft-delete manager, TL5 cross-tenant, TL6 transaction)
- `revisoes/US-CLI-005-advogado.md` — APROVADO COM RESSALVAS (R1 audit sem PII, R2 motivo categoria enum, R3 nao eh "esquecimento", R4 UNIQUE INDEX parcial reativacao)

## Total

11 tasks. 9 testes. Commit `953838f`.
