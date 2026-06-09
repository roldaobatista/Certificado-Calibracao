---
owner: agente-ia
revisado-em: 2026-06-09
proximo-review: 2026-09-09
status: ready-for-implement
diataxis: reference
frente: configuracoes-sistema
tipo: tasks-faseamento
relacionados:
  - docs/faseamento/configuracoes-sistema/plan.md
---

# Tasks — frente `configuracoes-sistema` (núcleo)

## Fatia 1a — domínio puro
- **T-CFG-010** enums (`RegimeTributario`, `TipoImposto`, `TipoDocumento`, `RegimeNumeracao`).
- **T-CFG-011** value objects (`Cnpj` ADR-0017, `Aliquota`, `JanelaVigencia` reuso).
- **T-CFG-012** entities (`Empresa`, `Filial`, `Imposto`, `SerieDocumento`).
- **T-CFG-013** transicoes (`regime_numeracao_do_tipo`, `proximo_formatado`, `imposto_vigente_em`, `validar_uma_matriz`).
- **T-CFG-014** erros de domínio.
- **T-CFG-015** repository Protocols.
- **T-CFG-016** testes puros (≥ regime por tipo, vigência determinística, 1 matriz, formato).

## Fatia 1b — schema PG
- **T-CFG-020** models (4 agregados + `numero_documento_reservado`).
- **T-CFG-021** migration 0001 CreateModel + UNIQUE (INV-036/037/028).
- **T-CFG-022** migration 0002 RLS v2.
- **T-CFG-023** migration 0003 WORM Padrão B + trigger INV-028 + trigger INV-CFG-IMPOSTO-IMUTAVEL.
- **T-CFG-024** migration 0004 exclusion constraint btree_gist (INV-CFG-IMPOSTO-SEM-SOBREPOSICAO).
- **T-CFG-025** migration 0005 grants + 0006 seed authz `configuracoes_sistema.*`.
- **T-CFG-026** mappers + repositories Django + reserva gap-less (reuso motor certificados).
- **T-CFG-027** drill `validar_configuracoes_sistema`.
- **T-CFG-028** testes PG-real (RLS, INV-028, imposto imutável, não-sobreposição, 1 matriz, gap-less vs buracos).

## Fatia 2 — use cases + REST
- **T-CFG-030** use cases empresa/filial (atualizar, adicionar).
- **T-CFG-031** use cases imposto (cadastrar, encerrar vigência).
- **T-CFG-032** use cases série (criar, `reservar_numero` 2 regimes).
- **T-CFG-033** ViewSet + serializers + ACTION_MAP + Idempotency + perfil server-side + eventos `Config.*` (`ACOES_CONFIG`).
- **T-CFG-034** testes E2E.

## Fatia 3 — P7/P8/P9
- **T-CFG-040** família `INV-CFG-*` em REGRAS + reconciliar INV-028 (remover `NF`) + `TestINV_CFG_*`.
- **T-CFG-041** hooks (`serie-numeracao-regime-check`, `imposto-imutavel-check`) + casos `_test-runner`.
- **T-CFG-042** matriz-reconciliação (molde M7).
- **T-CFG-043** P8: promover ADR-0080 + frontmatters draft→stable.
- **T-CFG-044** P9: auditores roteados (INV-RITUAL-003).
