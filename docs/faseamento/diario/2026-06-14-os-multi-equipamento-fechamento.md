---
owner: claude-code
revisado-em: 2026-06-14
status: stable
---

# Diário — fechamento da frente `os-multi-equipamento` (2026-06-14)

> Retrofit cirúrgico da OS (módulo M3, fechado): 1→N equipamentos por ATIVIDADE +
> entidade `ItemComercialOS` (deslocamento/taxa) + recebimento por instrumento (estrutura).
> Aditivo/reversível. ADR-0082 + emenda ADR-0023. Detalhe vivo: `docs/faseamento/os-multi-equipamento/`.

---

## Ritual P0→P9 — FECHADA

- **Fatias:** 1a (domínio: `TipoItemComercial`, `ItemComercialOSSnapshot`, `ItemOrcamento.equipamento_id`) ·
  1b (schema: rename `equipamento_id_desnormalizado`→`equipamento_id`, migration 0018 + triggers V2 COALESCE) ·
  1c (`OS.equipamento` nullable migration 0019 + entidade `ItemComercialOS` migration 0020) ·
  2 (envelope header→item, bifurcação atividade/comercial, detecção por atividade) ·
  2-leitura (T-OSME-035: `ItemComercialOSViewSet` CRUD + visão 360/listagem agregam equip./itens comerciais +
  migration 0021 seed `os.gerir_item_comercial`) · 3 (INVs + testes regressão/carga).

## P9 — mutirão de auditores (2ª sessão, 2026-06-14)

- **Verificação funcional ANTES do mutirão** (regra "não declarar pronto sem rodar") pegou **GATE VERMELHO**:
  regressão do módulo OS com 10 falhas + 3 erros. Causa-raiz: o use case `abrir_os_via_orcamento` documentava
  o fallback header→item (DTO `equipamento_id`) mas **não o implementava** — só o consumer fazia; os testes
  `test_inv_os_{ativ_001,ativ_005,fat_001,idemp_001}` chamam o use case direto (contrato v1). Conserto: fallback
  movido para o use case (camada de aplicação) → 4 testes legítimos voltaram a verde **sem serem tocados**.
- **1ª passada (7 auditores roteados, Sonnet):** segurança/idempotência/observabilidade PASS; qualidade 1 MÉDIO;
  llm-correctness 1 ALTO + 2 MÉDIO; performance 1 ALTO + 1 MÉDIO; produto 1 MÉDIO.
- **Consertos causa-raiz** (verificação adversarial R6 em Opus antes do mutirão): except genérico → captura
  específica; N+1 `visao_360` → 4 mapas agregados (7 queries fixas); N+1 `os_do_tecnico` → JOIN único;
  AC-003-1 → serializer `equipamento_id` + pre-check INV-OS-EQP-001 na view (helper compartilhado consumer↔view) +
  **descoberta** do bug ACTION_MAP `os.atualizar` (nunca seedado) → `criar` corrigido p/ `os.adicionar_atividade`;
  testes de API via APIClient (`test_osme_api_fatia2.py`, 6 testes) fecham M1 + débito de cobertura REST; docstrings.
- **2ª passada escopada (R5, 4 auditores que tiveram MÉDIO+):** 4/4 PASS — "0 achados MÉDIO+ — conserto confirma".
  **INV-RITUAL-001 satisfeito** (zero Crítico/Alto/Médio).
- **Verificação independente:** regressão completa do módulo OS = **96 testes verdes**; mypy/ruff limpos nos
  arquivos da frente. Detalhe + ata completa: `docs/faseamento/os-multi-equipamento/matriz-reconciliacao.md`.

## Débitos rastreados (não-bloqueantes)

- **GATE-OSME-RECEBIMENTO-7.5** — enforcement recebimento por atividade (AC-007-2b/3/4); dívida do app `equipamentos`
  (produtor `criar_recebimento` ainda não publica `atividade_id`). Estrutura + INV-OSME-RCB-001 declarado entregues.
- **GATE-OS-AUTHZ-ACTION-MAP** (descoberto no P9) — `os.atualizar` no ACTION_MAP de
  reagendar/transferir/cancelar/dispensa (`AtividadeViewSet`) e cancelar/reabrir (`OSViewSet`) nunca foi seedada →
  deny 403. Bug pré-existente fora do escopo OSME (cada endpoint exige decisão authz dedicada).
- **BAIXO (lote R10):** try/finally na migration 0021 (inócuo em produção — migrator BYPASSRLS); `correlation_id`
  ad-hoc em eventos OS (pré-existente desde M3); teste importa helper privado `_recalcular_valor_total_os`.

ADR aceita: **0082** (OS multi-equipamento) + emenda **0023** (evolução 1→N instrumentos).
