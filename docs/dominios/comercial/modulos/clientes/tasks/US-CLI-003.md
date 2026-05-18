---
owner: roldao
revisado_em: 2026-05-18
proximo_review: 2026-08-18
status: stable
diataxis: reference
audiencia: agente
us: US-CLI-003
plano: docs/dominios/comercial/modulos/clientes/planos/US-CLI-003.md
---

# Tasks T-CLI-041..T-CLI-060 — US-CLI-003 (importacao 1-clique CSV)

> Saida do `/tasks` do Spec Kit. Cada commit cita o ID + AC coberto.
> Pareceres absorvidos: `revisoes/US-CLI-003-tech-lead.md` (12 ressalvas) + `revisoes/US-CLI-003-advogado.md` (9 ressalvas).

## Mapa rapido task -> commit -> AC -> ressalva

| Task | Descricao | Commit | AC | Endereca |
|---|---|---|---|---|
| T-CLI-041 | Settings: `DATA_UPLOAD_MAX_MEMORY_SIZE=2 MiB` + `FILE_UPLOAD_MAX_MEMORY_SIZE` | ae9f143 | AC-1 | R1 tech-lead |
| T-CLI-042 | `csv_safety.sanitizar_celula_csv` (CSV/formula injection) | ae9f143 | AC-2 | R2 tech-lead |
| T-CLI-043 | `csv_io.ler_csv_normalizado` + `sugerir_mapeamento` + detectores sensiveis/CPF responsavel | ae9f143 | AC-1 | R5, R6 tech-lead + R9 advogado |
| T-CLI-044 | `ClienteRepository.bulk_upsert` + DTOs `ClienteImportacaoInput`, `LinhaRejeitada`, `ResultadoImportacao` no domain | ae9f143 | AC-2 | R8 tech-lead |
| T-CLI-045 | Migration `0012` — modelo `ClienteImportacaoDeclaracao` + RLS + CHECKs | ae9f143 | AC-2 | R6 advogado |
| T-CLI-046 | Migration `0012` — campos LGPD novos no `Cliente` (`aceite_lgpd_base_legal`, `evidencia_externa`, `pendente`, `cpf_responsavel_legal`) | ae9f143 | AC-2 | R2, R8 advogado |
| T-CLI-047 | `application/comercial/clientes/importar_clientes.py` — use case puro | ae9f143 | AC-1, AC-2 | R8 tech-lead + R1, R2, R9 advogado |
| T-CLI-048 | `DjangoClienteRepository.bulk_upsert` — advisory lock por tenant + sanitizacao | ae9f143 | AC-2 | R3 tech-lead |
| T-CLI-049 | Predicate ABAC `tenant_nao_suspenso` (stub) | ae9f143 | AC-2 | R4 tech-lead |
| T-CLI-050 | Validador PJ-com-PF: heuristica `_email_e_pessoal` no use case decide entre 3 valores de dispensa | ae9f143 | AC-2 | R1 advogado |
| T-CLI-051 | `try/finally` em ambas as actions garante delete de tempfile | ae9f143 | AC-1, AC-2 | R3 advogado |
| T-CLI-052 | RAT-17 acrescentado em `docs/conformidade/comum/lgpd-rat.md` | ae9f143 | — | R4 advogado |
| T-CLI-053 | Migration `audit/0007` — finalidade `consulta_relatorio_importacao` no enum + CHECK | ae9f143 | AC-2 | R7 advogado |
| T-CLI-054 | Actions DRF: `importar_preview`, `importar_executar`, `importacoes` + `ACTION_MAP` | ae9f143 | AC-1, AC-2 | R6 tech-lead + R6, R7 advogado |
| T-CLI-055 | Serializers: `ImportarPreviewSerializer`, `ImportarExecutarSerializer`, `DeclaracaoProcedenciaSerializer` | ae9f143 | AC-1, AC-2 | R6 tech-lead |
| T-CLI-056 | Migration `0013` — seed `clientes.importar` apenas `admin_tenant` | ae9f143 | AC-2 | R4 advogado + TL7 |
| T-CLI-057 | Audit `cliente.importacao_executada` payload sanitizado (totais + hashes salgados) | ae9f143 | AC-2 | R5 advogado + R10 tech-lead |
| T-CLI-058 | Rejeicao `documento_pertence_a_cliente_mesclado` quando documento existe em soft-deleted | ae9f143 | AC-2 | E risco tech-lead |
| T-CLI-059 | URL patterns: `POST /importar-preview/`, `POST /importar-executar/`, `GET /importacoes/` (via DefaultRouter) | ae9f143 | AC-1, AC-2 | — |
| T-CLI-060 | Suite de 39 testes em `tests/test_clientes_us_cli_003_importar.py` | ae9f143, 7c793e8 | AC-1, AC-2 | todas |

## Apendice — tasks complementares pos-auditoria

Apos os 3 auditores Familia 5 rodarem (Qualidade + Seguranca + Produto), foi gravado FAIL critico do Auditor de Seguranca:

| Task | Descricao | Commit | Endereca |
|---|---|---|---|
| T-CLI-061 | Helper `audit.services.hashear_pii_com_salt_tenant(valor, tenant_id)` | 7c793e8 | FAIL critico auditor Seguranca |
| T-CLI-062 | Refatorar 4 audit calls em `clientes/views.py` (`cliente.criado`, `cliente.mesclado`, `cliente.bloqueado`, `cliente.desbloqueado`) pra usar o helper | 7c793e8 | FAIL critico auditor Seguranca |
| T-CLI-063 | Teste anti-regressao `test_audit_documento_hash_eh_salgado_por_tenant` | 7c793e8 | FAIL critico auditor Seguranca |
| T-CLI-064 | 3 testes unhappy `importar_clientes` (`documento_ausente`, `documento_tamanho_invalido`, `nome_ausente`) | 7c793e8 | CONCERN auditor Qualidade |

## Total

- **20 tasks principais** (T-CLI-041..T-CLI-060) executadas em commit `ae9f143`.
- **4 tasks pos-auditoria** (T-CLI-061..T-CLI-064) executadas em commit `7c793e8`.
- **39 testes verdes + 1 skip-marker** (ADR-0015 fluxo 3 pendente).
- **Cobertura final: 86.01%** global (eram 85.44% antes dos 4 testes pos-auditoria).
