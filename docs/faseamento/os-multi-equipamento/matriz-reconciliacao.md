---
owner: agente-ia
revisado-em: 2026-06-14
proximo-review: 2026-09-14
status: stable
diataxis: reference
audiencia: [agente, auditor]
frente: os-multi-equipamento
tipo: matriz-reconciliacao
relacionados:
  - docs/faseamento/os-multi-equipamento/spec.md
  - docs/faseamento/os-multi-equipamento/tasks.md
  - docs/adr/0082-os-multi-equipamento.md
---

# Matriz de reconciliação — frente `os-multi-equipamento` (P9, fechamento)

> Liga AC-OSME-* / INV-* ↔ código ↔ teste. Gerada no P9 (2026-06-14) após conserto
> dos achados do `auditor-produto` + validação funcional. Itens marcados **GATE** são
> deferidos a `GATE-OSME-RECEBIMENTO-7.5` por fronteira de módulo (não-mascaramento —
> ver emenda da spec §2 / parecer `consultor-rbc-iso17025`).

## AC ↔ código ↔ teste

| AC | Código | Teste | Status |
|---|---|---|---|
| AC-001-1 (equip. próprio da atividade, NOT NULL) | `models.py` `AtividadeDaOS.equipamento_id` + migration 0018 (RenameField) | `test_osme_migration_0018_drill`, `test_inv_os_ativ_002_cross_tenant` | ✅ |
| AC-001-2 (`OS.equipamento` nullable) | migration 0019 + `models.py` índice parcial | `test_osme_fatia1c::a/d` | ✅ |
| AC-001-3 (trigger imutável preservado) | migration 0018 RunSQL `CREATE OR REPLACE` | `test_osme_migration_0018_drill` | ✅ |
| AC-002-1/2/3 (envelope header→item; atividade c/ equip. próprio; replay idempotente) | `consumers/orcamento.py::_parse_input` + `abrir_os_via_orcamento` bifurcação | `test_osme_fatia2::a`, `test_osme_fatia2_leitura` | ✅ |
| AC-003-1 (`adicionar_atividade` + equip. + INV-OS-EQP-001) | `application/.../adicionar_atividade.py` + `serializers.py` (`equipamento_id`) + `views.py` `AtividadeViewSet.criar` (pre-check `precheck_equipamentos_nao_baixados`; ACTION_MAP corrigido) | `test_m3_os_adicionar_atividade`, `test_osme_api_fatia2::adicionar_atividade_equip_ativo/baixado` | ✅ (P9: serializer+pre-check REST) |
| AC-003-2 (reabertura clona equip. por atividade) | `operacoes_avancadas.py` | `test_osme_fatia2::d` | ✅ |
| AC-003-3 (OS avulsa equip. por item + `payload_fingerprint`) | `views.py` `OSViewSet.avulsa` (`equip_ids`) | `test_osme_fatia2`, `test_m3_os_operacoes_avancadas` | ✅ |
| AC-004-1/2 (detecção baixado por atividade, 1 query) | `consumers/equipamento.py` + índice `atv_tenant_equip_est_idx` | `test_inv_os_eqp_001_baixado`, `test_osme_fatia2::e` | ✅ |
| AC-005-1/2/3 (concorrência cross-equip sem falso-412) | índice parcial `idx_atividade_em_execucao_por_equip` | `test_inv_os_conc_001_unique_partial`, `test_concorrencia_cross_equipamento` (50 threads) | ✅ |
| AC-006-1 (item comercial = linha própria, leitura) | `queries/visao_360.py` (`equipamentos_distintos`+`itens_comerciais`), `queries/listagem.py`, `views.py` `ItemComercialOSViewSet` | `test_osme_fatia2_leitura::a/c/e` | ✅ (T-OSME-035) |
| AC-006-2 (nunca equip.; soma `valor_total`) | `models.py` `ItemComercialOS` + `_recalcular_valor_total_os` | `test_osme_fatia1c::b/c`, `test_osme_fatia2_leitura::c/e` | ✅ |
| AC-006-3 (item sem equip. → ItemComercialOS) | `abrir_os_via_orcamento.py` ramo `else` | `test_osme_fatia2::b` | ✅ |
| AC-007-1 (ponteiro recebimento → atividade) | migration 0018 `AtividadeDaOS.equipamento_recebimento_id` + `AtividadeSnapshot.equipamento_recebimento_id` (entities.py) + mapper | `test_osme_migration_0018_drill` (coluna) | ✅ (estrutura) |
| AC-007-2 parte **estrutura** + validação OS-level (ponte) | `abrir_os_via_orcamento.py:180-` (`EquipamentoSemRecebimentoRegistrado`, degeneração documentada) | `test_m3_os_abrir_via_orcamento` (AC-OS-001-8) | ✅ (ponte) |
| AC-007-2 parte **enforcement** (`recebido == calibrado`) | — | — | ⛔ **GATE-OSME-RECEBIMENTO-7.5** |
| AC-007-3 (NC parcial por atividade) | — | — | ⛔ **GATE-OSME-RECEBIMENTO-7.5** |
| AC-007-4 (seam de preenchimento) | — | — | ⛔ **GATE-OSME-RECEBIMENTO-7.5** |

## INV ↔ teste

| INV | Teste | Status |
|---|---|---|
| INV-OS-ATIV-002 (equip. próprio; herança só tenant/cliente) | `test_inv_os_ativ_002_cross_tenant` (happy + unhappy RLS + cross-tenant) | ✅ |
| INV-OS-EQP-001 (baixado bloqueia, por atividade) | `test_inv_os_eqp_001_baixado` (incl. multi-equip 1 sucata) | ✅ |
| INV-OS-CONC-001 (concorrência por equipamento) | `test_inv_os_conc_001_unique_partial` + carga cross-equip | ✅ |
| INV-OSME-ITEMCOM-001 (item comercial sem equip., fora do índice, soma valor) | `test_osme_fatia1c::b/c`, `test_osme_fatia2::b`, `test_osme_fatia2_leitura` | ✅ |
| INV-OSME-RCB-001 (recebimento por instrumento) | DECLARADO (REGRAS/ADR-0082); estrutura testada (`migration_0018_drill` coluna). Enforcement por atividade → GATE | 🟡 estrutura ✅ / enforcement ⛔ GATE |

## Non-goals respeitados

Máquina de estados, aceite, NC, checklist, evidência, SLA, sucessão — intocados. `OS.equipamento_recebimento_id`
**deprecado, não dropado** (ADR-0082, reversível). Dimensão grandeza ADR-0041 (débito M4) e telas/PDF fora.

## Ata P9 — mutirão de auditores (2026-06-14, 2ª sessão)

**Verificação funcional (precede o mutirão — regra "não declarar pronto sem rodar"):** a
regressão completa do módulo OS revelou **GATE VERMELHO** (10 falhas + 3 erros) NÃO pego antes:
os testes `test_inv_os_{ativ_001,ativ_005,fat_001,idemp_001}` (não atualizados na Fatia 3) abrem
OS via use case **direto** com contrato v1 (equipamento no header, item sem `equipamento_id`). O
use case `abrir_os_via_orcamento` documentava o fallback header→item (DTO `equipamento_id`) mas
**não o implementava** — só o consumer fazia. Causa-raiz: fallback movido para o use case (camada
de aplicação, spec-as-source) → 4 testes legítimos voltaram a verde **sem serem tocados**.

**Mutirão (1ª passada, 7 auditores roteados, Sonnet):**

| Auditor | Veredito | Achados MÉDIO+ | BAIXO |
|---|---|---|---|
| segurança | PASS | 0 | try/finally migration 0021 |
| idempotência | PASS | 0 | — |
| observabilidade | PASS | 0 | `correlation_id` ad-hoc (pré-existente) |
| qualidade | 1 MÉDIO | `test_leitura_d` dava ilusão de cobrir 422 do ViewSet (só testava enum) | `except` largo |
| llm-correctness | 1 ALTO + 2 MÉDIO | `except (KeyError, Exception)`; docstring "tipo_predominante calculado"; comentário "Soma em OS.valor_total" | — |
| performance | 1 ALTO + 1 MÉDIO | N+1 `visao_360` (4N queries); N+1 `os_do_tecnico` | nome índice em comentário |
| produto | 1 MÉDIO | AC-003-1: serializer REST sem `equipamento_id` nem pre-check INV-OS-EQP-001 | nome índice; cobertura REST |

**Consertos causa-raiz (verificação adversarial R6 feita em Opus antes do mutirão de conserto):**

1. **GATE VERMELHO** — fallback header→item no use case (`abrir_os_via_orcamento`); consumer mantém pre-check (helper extraído).
2. **except genérico** → `except (KeyError, InvalidOperation, ValueError, TypeError)`.
3. **N+1 `visao_360`** → 4 mapas agregados (`mapa_aceites/dispensas/ncs_ativas/evidencias_foto_por_os`); 7 queries fixas (O(1) em nº de atividades).
4. **N+1 `os_do_tecnico`** → `listar_os_por_tecnico_atividade` (JOIN único).
5. **AC-003-1** → `AdicionarAtividadeRequestSerializer.equipamento_id` + pre-check INV-OS-EQP-001 na view (helper `precheck_equipamentos_nao_baixados` compartilhado consumer↔view). **Descoberta:** ACTION_MAP `"criar": "os.atualizar"` (ação nunca seedada → 403 sempre); corrigido p/ `os.adicionar_atividade`.
6. **M1 + cobertura REST** → `tests/test_osme_api_fatia2.py` (6 testes APIClient: item comercial 201/422/authz-403/remover; adicionar atividade equip ativo/baixado).
7. **docstrings/comentários** corrigidos (tipo_predominante lido do snapshot; valor_total_atualizado; nome real do índice).

## Débitos registrados (não-bloqueantes desta frente)

- **GATE-OSME-RECEBIMENTO-7.5** — enforcement recebimento por atividade (AC-007-2b/3/4); dívida do app `equipamentos`.
- **GATE-OS-AUTHZ-ACTION-MAP** (descoberto no P9) — `os.atualizar` no ACTION_MAP de `reagendar`/`transferir`/`cancelar`/`dispensa` (`AtividadeViewSet`) e `cancelar`/`reabrir` (`OSViewSet`) **nunca foi seedada** → deny-by-default 403 nesses endpoints. Bug **pré-existente** fora do escopo OSME (não há ação canônica óbvia p/ cada um — exige decisão authz dedicada). `"criar"` já corrigido nesta frente.
- **N+1 `visao_360` — RESOLVIDO no P9** (bulk queries; não é mais débito).
- **Cobertura REST `ItemComercialOSViewSet` — RESOLVIDA no P9** (`test_osme_api_fatia2.py`).
- **BAIXO** — try/finally na migration 0021 (inócuo em produção: migrator é BYPASSRLS); `correlation_id` ad-hoc em eventos OS (pré-existente desde M3). Lote pós-fechamento (R10).
- **mypy global** com erros pré-existentes (`calibracao`/`equipamentos` — drift de stubs); frente os-multi-equipamento **limpa**.
