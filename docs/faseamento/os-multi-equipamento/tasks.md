---
owner: agente-ia
revisado-em: 2026-06-13
proximo-review: 2026-09-13
status: stable
proximo-passo: ready-for-implement
diataxis: reference
audiencia: [agente, auditor]
frente: os-multi-equipamento
tipo: tasks
relacionados:
  - docs/faseamento/os-multi-equipamento/plan.md
  - docs/faseamento/os-multi-equipamento/spec.md
---

# Tasks — frente `os-multi-equipamento` (retrofit cirúrgico OS 1→N equipamentos)

> T-OSME-NNN. Fatias do `plan.md`. Cada fatia fecha com verificação real (regra "não declarar
> pronto sem rodar") antes da próxima. Refs: AC-OSME-* (spec §2), D-OSME-* (spec §3), INV-OSME-*
> (spec §5), TL-OSME-* / RBC-OSME-* (reviews-consolidado). **Módulo FECHADO** → drill em banco
> COM dados em toda fatia de schema.

## Fatia 1a — domínio puro (`src/domain/operacao/os/`)

- [ ] **T-OSME-010** `value_objects.py` — enum `TipoItemComercial` (`deslocamento`/`taxa_visita`/`outro`).
      `TipoAtividade` permanece fechado (não adicionar — INV-OS-ATIV-003). Ref: D-OSME-3.
- [ ] **T-OSME-011** `entities.py` — `AtividadeSnapshot`: rename `equipamento_id_desnormalizado`→
      `equipamento_id` (UUID, fonte própria) + add `equipamento_recebimento_id: UUID|None`.
      `OSSnapshot`: `equipamento_id: UUID|None` + **remover** `equipamento_recebimento_id`. Novo
      `ItemComercialOSSnapshot` (id, tenant_id, os_id, tipo, descricao_publica, valor, quantidade,
      origem_item_id?). Ref: D-OSME-1/2/3/5; spec §4.
- [ ] **T-OSME-012** `repository.py` (Protocol) — add `salvar_item_comercial`,
      `listar_itens_comerciais_por_os`; ajustar assinaturas que liam `equipamento_id_desnormalizado`.
      `listar_atividades_em_execucao_por_equipamento` mantém (já por atividade). Ref: spec §4.
- [ ] **T-OSME-013** `abrir_os_via_orcamento.py` — `ItemOrcamento.equipamento_id: UUID|None`; item
      COM equip → `AtividadeSnapshot.equipamento_id`; item SEM equip → `ItemComercialOSSnapshot`
      (não atividade — TL-OSME-04); `OSSnapshot.equipamento_id=None` em multi-equip; soma comerciais
      em `valor_total`. Atividade planejada no payload `os.aberta` ganha `equipamento_id` (v+1 aditivo
      — TL-OSME-10). Ref: AC-OSME-002/006; D-OSME-2/3.
- [ ] **T-OSME-014** Testes puros (`tests/test_osme_dominio.py`): item c/ equip → atividade c/ equip;
      item s/ equip → item comercial; OSSnapshot aceita equip None; `valor_total` inclui comerciais;
      atividade planejada carrega equipamento. ruff/mypy limpos.

## Fatia 1b — schema PG (`src/infrastructure/ordens_servico/`)

- [ ] **T-OSME-020** `models.py` — `OS.equipamento` `null=True` (D-OSME-2); **remove**
      `OS.equipamento_recebimento_id`; `os_tenant_equip_idx` vira parcial `condition=Q(equipamento__isnull=False)`.
      `AtividadeDaOS`: rename campo → `equipamento_id` (docstring honesta: fonte própria, não desnormalizado)
      + add `equipamento_recebimento_id` (UUIDField null) + novo índice `atv_tenant_equip_estado_idx`
      `(tenant, equipamento_id, estado)` (TL-OSME-02). Novo model `ItemComercialOS` (Padrão A soft-delete,
      RLS herdado, nunca equipamento). Ref: spec §4; D-OSME-1/2/3/5.
- [ ] **T-OSME-021** Migration `0018_os_multi_equipamento` — `RenameField` equip. + `AlterField`
      (OS.equipamento null) + `RemoveField`/`AddField` recebimento + `RemoveIndex`/`AddIndex` parcial +
      `AddIndex atv_tenant_equip_estado_idx` + `CreateModel ItemComercialOS`. **`reverse` completo.**
      Ref: D-OSME-1/2/5; TL-OSME-09.
- [ ] **T-OSME-022** Migration `0018` (cont.) — **`RunSQL CREATE OR REPLACE` dos 2 triggers** (TL-OSME-01):
      forward `_denormalize_check` reescrita SEM `SELECT equipamento_id FROM ordens_servico` mas MANTENDO
      integral o lookup `tipo_bloqueia_concorrencia` (TL-OSME-05); imutável `_imutavel_check` citando
      `equipamento_id`. **`reverse_sql` simétrico** (restaura corpo antigo). Ref: TL-OSME-01/05.
- [ ] **T-OSME-023** Migration `0018` (cont.) — RLS policy `item_comercial_os` (FORCE + 4 policies
      tenant) + grants `app_user`. Ref: INV-TENANT-001/003; INV-OSME-ITEMCOM-001.
- [ ] **T-OSME-024** `repositories.py` + `mappers` — rename `equipamento_id_desnormalizado`→`equipamento_id`
      em TODOS os ~5 pontos (snapshot/mapper/queries); add CRUD `ItemComercialOS`; detecção/filtros por
      `AtividadeDaOS.equipamento_id`. Ref: D-OSME-1; spec §4.
- [ ] **T-OSME-025** **Drill forward+reverse em banco COM dados** (TL-OSME-01) — seed 2 OS single-equip +
      atividades ANTES de `0018`; aplica forward → atividades preservam equip.; INSERT nova atividade OK
      (trigger forward); UPDATE atividade OK (trigger imutável c/ coluna nova); `reverse` restaura sem perda.
      `migrate` + `makemigrations --check` + RLS UNHAPPY cross-tenant `item_comercial_os`. Testes PG-real
      (`tests/test_osme_schema_fatia1b.py`). Ref: riscos plan #1.

## Fatia 2 — use cases + consumers + REST

- [ ] **T-OSME-030** `consumers/orcamento.py` — `_parse_input` envelope header→item (`equipamento_id` por
      item; None → item comercial); pré-check itera TODOS os equip. distintos dos itens (422
      `EquipamentoBaixadoEmOS` se QUALQUER baixado). Atualizar docstring-contrato `:73-104`. Ref: AC-OSME-002/004.
- [ ] **T-OSME-031** `adicionar_atividade.py` — `equipamento_id` novo no input + pré-check INV-OS-EQP-001
      (equip. BAIXADO/DESCARTADO → 422) — enforcement hoje inexistente nesse caminho (TL-OSME-03). Ref: AC-OSME-003-1.
- [ ] **T-OSME-032** `operacoes_avancadas.py` — reabertura clona cada atividade com SEU `equipamento_id`
      (não copia da OS-mãe nullable) + `criar_os_avulsa`/`ItemOSAvulsa` ganham `equipamento_id` +
      `payload_fingerprint` por equipamentos dos itens (TL-OSME-03 / D-OSME-4). Ref: AC-OSME-003-2/3.
- [ ] **T-OSME-033** `consumers/equipamento.py` — detecção de baixado por `AtividadeDaOS.equipamento_id`
      → OSs pai distintas (usa `atv_tenant_equip_estado_idx`). Recebimento: popula
      `AtividadeDaOS.equipamento_recebimento_id` (estrutura; seam completo = GATE). Ref: AC-OSME-004; RBC-OSME-2.
- [ ] **T-OSME-034** Use case `abrir_os_via_orcamento` — validação recebimento por atividade
      (INV-OSME-RCB-001: `requer_recebimento` ⟹ recebimento NOT NULL + equip. recebido == calibrado) +
      NC parcial (atividade c/ recebimento `nao_conformidade_recebimento` não inicia; demais seguem —
      RBC-OSME-5). Ajustar AC-OS-001-8 de OS-level p/ atividade-level. Ref: AC-OSME-007; RBC-OSME-3/5.
- [ ] **T-OSME-035** `views.py` + `queries/` — CRUD `ItemComercialOS` (ação authz `os.gerir_item_comercial`,
      OS não-terminal); `GET /os/?equipamento_id=` filtra por atividade; `visao_360`/`listagem` agregam
      equip. das atividades + listam itens comerciais. ~7 call-sites `OSSnapshot.equipamento_id` → aceitar
      None (D-OSME-2). Ref: spec §7; D-OSME-2/3.
- [ ] **T-OSME-036** Testes (`tests/test_osme_fatia2.py`): envelope multi-equip → N atividades c/ equip.
      certo; **UNHAPPY equip. baixado em 1 de 2** (AC-OSME-004-2); reabertura preserva equip.; OS avulsa
      multi-equip; item comercial soma `valor_total`; recebimento por atividade (happy + NC parcial);
      idempotência replay → 1 OS; `assertNumQueries` (detecção sem N+1).

## Fatia 3 (P7) — INVs + testes regressão/carga

- [ ] **T-OSME-050** REGRAS-INEGOCIAVEIS.md — emenda INV-OS-ATIV-002 (equip. PRÓPRIO da atividade) +
      INV-OS-EQP-001 (valida por atividade incl. `adicionarAtividade`) + novas INV-OSME-RCB-001 +
      INV-OSME-ITEMCOM-001. **NÃO reverter** INV-OS-CONC-001 (`:162` já cita `equipamento_id` — TL-OSME-06).
      Ref: spec §5.
- [ ] **T-OSME-051** Atualizar testes regressão existentes p/ multi-equip: `test_inv_os_eqp_001_baixado`
      (OS 2 equip., 1 baixado), `test_inv_os_ativ_002_cross_tenant` (equip. próprio), `test_inv_os_conc_001_unique_partial`
      (coluna renomeada) + `TestINV_OSME_*` nomeadas (RCB-001 / ITEMCOM-001). Ref: TST-004.
- [ ] **T-OSME-052** Teste de carga `tests/carga/test_concorrencia_cross_equipamento.py` (≥50 threads):
      2 equip. DIFERENTES mesma OS EM_EXECUCAO simultâneo → sem 412 (AC-OSME-005-1); MESMO equip. → 412
      (AC-OSME-005-2). Ref: Risco #2; TL-OSME-07.
- [ ] **T-OSME-053** Hooks: confirmar `migration-concorrencia-os-check` ainda valida (coluna renomeada);
      ajustar se referenciar nome velho. `bash .claude/hooks/_test-runner.sh` verde.

## P8/P9 — fechamento

- [ ] **T-OSME-060** ADR-0082 nova "OS multi-equipamento" + emenda ADR-0023 (evolução 1→N instrumentos) +
      matriz-feature-perfil (recebimento perfil-aware) + STATUS-GERADO + AGENTS §11 (ADR-0082) / §12
      (GATE-OSME-RECEBIMENTO-7.5) + matriz-reconciliacao ENXUTA (AC/INV↔código, INV↔teste, ata P9) +
      frontmatters draft→stable. Verificar: `status-projeto.sh --check`. Ref: plan P8.
- [ ] **T-OSME-061** P9 auditores roteados (INV-RITUAL-003): essenciais (qualidade·segurança·llm·
      idempotência·produto) + **performance OBRIGATÓRIO** (índices/seq scan/N+1 — toca migration/consumer) +
      **observabilidade** (migration/trigger/tenant_id/correlation_id) ; supplychain SÓ se dep nova;
      conformidade-lgpd FORA (equip. é técnico, não PII) ; drift-docs FORA. Verificação adversarial de
      TODO MÉDIO+ antes do mutirão (R6); 2ª passada escopada ao diff do conserto (R5). Conserto causa-raiz
      → re-passada → zero C/A/M (INV-RITUAL-001) → FECHADA + CURRENT.md. BAIXOs em lote pós-fechamento (R10).
