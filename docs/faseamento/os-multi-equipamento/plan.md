---
owner: agente-ia
revisado-em: 2026-06-13
proximo-review: 2026-09-13
status: stable
proximo-passo: ready-for-implement
diataxis: reference
audiencia: [agente, tech-lead, auditor]
frente: os-multi-equipamento
tipo: plan
relacionados:
  - docs/faseamento/os-multi-equipamento/spec.md
  - docs/faseamento/os-multi-equipamento/reviews-consolidado.md
  - docs/faseamento/os-multi-equipamento/T-OSME-000-investigacao.md
  - docs/adr/0023-os-com-atividades.md
  - docs/adr/0041-os-concorrencia-atividades.md
---

# Plan — frente `os-multi-equipamento` (retrofit cirúrgico OS 1→N equipamentos)

> Deriva da `spec.md` v2 (P2 incorporado — `tech-lead` TL-OSME-01..10 + `consultor-rbc`
> RBC-OSME-01..05, AMBOS APROVA COM CORREÇÕES; batch Roldão D-OSME-3 = `ItemComercialOS`).
> Decisões D-OSME-1..5 cravadas na spec §3. Retrofit de **módulo FECHADO** (Marco 3) — disciplina
> reforçada: cada fatia roda em banco COM dados (não só CI vazio), drill forward+reverse obrigatório.

## Arquitetura (resumo operacional)

- **Tese:** equipamento sai da OS e vira PRÓPRIO da atividade. A infra de concorrência já chaveia
  pela atividade (`idx_atividade_em_execucao_por_equip`, `0005:87-89`) — **não move**. O retrofit
  troca a FONTE do `equipamento_id` (era cópia da OS via trigger; vira valor do INSERT) + renomeia a
  coluna (D-OSME-1) + relaxa `OS.equipamento` (D-OSME-2) + adiciona `ItemComercialOS` (D-OSME-3) +
  move `equipamento_recebimento_id` OS→atividade (D-OSME-5).
- **Ponto de maior risco (TL-OSME-01):** os 2 triggers PL/pgSQL (`0005`) referenciam a coluna por
  TEXTO LITERAL no corpo da função. `RenameField` (= `ALTER TABLE RENAME COLUMN`) propaga ao índice
  mas **NÃO recompila o corpo das funções** — erro só no 1º INSERT/UPDATE em runtime. Migration `0018`
  precisa `CREATE OR REPLACE` de AMBAS as funções (forward reescrita SEM o `SELECT ... FROM
  ordens_servico` mas MANTENDO integral o lookup de `tipo_bloqueia_concorrencia` — TL-OSME-05;
  imutável citando a coluna nova) + `reverse_sql` simétrico. **Drill em banco COM dados**, não CI vazio.
- **Detecção de baixado (Risco #1 / TL-OSME-02):** a query migra de `OS.equipamento_id` para
  `AtividadeDaOS.equipamento_id` — sem índice vira seq scan na tabela de atividades (maior que a de OS).
  Criar `atv_tenant_equip_estado_idx (tenant_id, equipamento_id, estado)`. 1 query, sem N+1 (só loga —
  TL-OSME-08).
- **`OSSnapshot.equipamento_id` → `UUID | None` (D-OSME-2):** muda contrato; `mypy strict` propaga
  para ~7 call-sites de leitura (`iniciar_atividade:178`, `operacoes_avancadas:120,176`, `queries/
  listagem:26,39`, `queries/visao_360:45,97`). Cada um que repassa o valor precisa aceitar None.
  `os_tenant_equip_idx` vira parcial `WHERE equipamento_id IS NOT NULL` (reverse = DROP+CREATE,
  lock momentâneo — TL-OSME-09).
- **3 call-sites que criam atividade (TL-OSME-03) — todos confiavam no trigger copiar da OS:**
  `abrir_os_via_orcamento` (envelope header→item), `adicionar_atividade` (precisa `equipamento_id`
  novo no input + enforcement INV-OS-EQP-001 hoje inexistente nesse caminho), `operacoes_avancadas`
  reabertura (clonar `equipamento_id` por atividade, não copiar da OS-mãe nullable), `criar_os_avulsa`
  (`ItemOSAvulsa.equipamento_id` + `payload_fingerprint` por equipamentos dos itens — D-OSME-4).
- **`ItemComercialOS` (D-OSME-3, decisão Roldão):** entidade LEVE separada (`os`, `tipo`
  deslocamento/taxa_visita/outro, `descricao_publica`, `valor`, `quantidade`, `origem_item_id?`).
  **Nunca** equipamento nem `tipo_bloqueia_concorrencia` (INV-OSME-ITEMCOM-001). Padrão A soft-delete
  (ADR-0031). Soma em `OS.valor_total`. NÃO é `AtividadeDaOS` (enum técnico fechado + bagagem não cabe —
  TL-OSME-04 resolvido). Itens sem `equipamento_id` no envelope viram isto.
- **Recebimento por instrumento (D-OSME-5 / RBC):** `equipamento_recebimento_id` move de `OS` para
  `AtividadeDaOS` (nullable). `EquipamentoRecebimento` JÁ é por instrumento (FK `equipamento`) — só o
  ponteiro mente. INV-OSME-RCB-001: atividade `requer_recebimento=true` ⟹ `equipamento_recebimento_id`
  NOT NULL **e** `EquipamentoRecebimento.equipamento_id == AtividadeDaOS.equipamento_id` (item recebido
  = item calibrado, cl. 7.4.2/7.8.2.1). NC parcial: atividade com recebimento `nao_conformidade_recebimento`
  não inicia; demais seguem (RBC-OSME-5). O conserto do SEAM de preenchimento (produtor publica
  `atividade_id`; `EquipamentoRecebimento.atividade_os_id`) = **GATE-OSME-RECEBIMENTO-7.5** (app
  `equipamentos`, fora do recorte).
- **Envelope `os.aberta` = v+1 ADITIVO (TL-OSME-10):** cada atividade no `payload_data` ganha
  `equipamento_id` (campo novo, retrocompatível) — não "inalterado". Saga downstream recebe shape estendido.
- **Camadas (ADR-0007 preservado):** domínio (`src/domain/operacao/os/`) sem `django.db`; use cases
  puros via `OSRepository`; infra (`src/infrastructure/ordens_servico/`) com models/migrations/repository.

## Cross-doc (P8 — emendas REAIS desta frente)

- **ADR-0023** (`docs/adr/0023-os-com-atividades.md`): emenda registrando a evolução — OS = container de
  N instrumentos (1 por atividade); §47-49 (1 instrumento) e §135 non-goal viram nota de superação.
- **ADR-0082 NOVA** "OS multi-equipamento": decisão do retrofit, abordagem cirúrgica, alternativas
  (predominante rejeitado; atividade-equip-NULL rejeitado), recebimento por instrumento, GATE.
- **REGRAS-INEGOCIAVEIS.md:** emenda INV-OS-ATIV-002 (`:146` — equipamento PRÓPRIO da atividade) +
  INV-OS-EQP-001 (`:159` — validar por atividade incl. `adicionarAtividade`) + INV-OSME-RCB-001 +
  INV-OSME-ITEMCOM-001 (novas). **NÃO reverter** INV-OS-CONC-001 (`:162` já cita `equipamento_id` —
  correto por antecipação, TL-OSME-06).
- **matriz-feature-perfil.md:** linha recebimento por instrumento perfil-aware (A exige; B/C/D conforme).
- **STATUS-GERADO.md** (via `scripts/status-projeto.sh`) + AGENTS §11 (ADR-0082) + §12: registrar GATE.
- Catálogo de eventos: nota envelope `os.aberta` v+1 aditivo (equipamento por atividade).

## Fatias

| Fatia | Entrega | Verificação (não declarar pronto sem rodar) |
|---|---|---|
| **1a domínio puro** | `entities.py`: `AtividadeSnapshot.equipamento_id` (rename, NOT NULL) + `equipamento_recebimento_id: UUID\|None`; `OSSnapshot.equipamento_id: UUID\|None` (remove `equipamento_recebimento_id` da OS). `value_objects.py`: enum `TipoItemComercial` (deslocamento/taxa_visita/outro) + `ItemComercialOS` snapshot. `ItemOrcamento.equipamento_id: UUID\|None`. `abrir_os_via_orcamento`: atividade recebe equip. do item; itens sem equip. → `ItemComercialOS`. Repository Protocol: métodos `salvar_item_comercial`, `listar_itens_comerciais_por_os`. | testes puros: item com equip → atividade; item sem equip → item comercial; OSSnapshot aceita equip None; soma valor_total inclui comerciais; mypy/ruff limpos |
| **1b schema PG (migration 0018)** | `models.py`: `OS.equipamento null=True`; remove `OS.equipamento_recebimento_id`; `AtividadeDaOS` rename `equipamento_id_desnormalizado`→`equipamento_id` (NOT NULL no nível lógico; coluna fica nullable p/ itens legados) + add `equipamento_recebimento_id`; índice parcial `os_tenant_equip_idx`; novo `atv_tenant_equip_estado_idx`; `CreateModel ItemComercialOS` + RLS. Migration `0018`: `RenameField` + `AlterField` + `RemoveField`/`AddField` + índices + `CreateModel` + **`RunSQL CREATE OR REPLACE` dos 2 triggers + `reverse_sql`**. RLS policy `item_comercial_os`. Repository Django (rename nos mappers). | **drill forward+reverse em banco COM dados** (2 OS + atividades pré-existentes): atividades preservam equip.; INSERT nova atividade OK (trigger forward); UPDATE atividade OK (trigger imutável c/ coluna nova); reverse restaura sem perda. `migrate` + `makemigrations --check` + RLS UNHAPPY cross-tenant `item_comercial_os` |
| **2 use cases + consumer + REST** | `adicionar_atividade` (+ `equipamento_id` input + pré-check INV-OS-EQP-001) · reabertura clona equip. por atividade · `criar_os_avulsa`/`ItemOSAvulsa` (+ equip. + fingerprint) · `consumers/orcamento.py` envelope header→item + pré-check TODOS equip. distintos · `consumers/equipamento.py` detecção por `AtividadeDaOS.equipamento_id` · CRUD `ItemComercialOS` (ação authz `os.gerir_item_comercial`) · `views.py`/`queries` filtro+agregação por atividade | testes: envelope multi-equip cria N atividades c/ equip. certo; UNHAPPY equip. baixado em 1 de 2 (US-OSME-004); reabertura preserva equip.; OS avulsa multi-equip; item comercial soma total; idempotência replay |
| **3 (P7) INVs + testes regressão/carga** | emenda INV-OS-ATIV-002 + INV-OS-EQP-001 + INV-OSME-RCB-001 + INV-OSME-ITEMCOM-001 em REGRAS + `TestINV_OSME_*` nomeadas + atualizar testes regressão existentes (`test_inv_os_eqp_001_baixado`, `test_inv_os_ativ_002_cross_tenant`, `test_inv_os_conc_001_unique_partial`) p/ multi-equip + **teste de carga** `tests/carga/test_concorrencia_cross_equipamento.py` (≥50 threads: 2 equip. diferentes mesma OS sem 412; mesmo equip. → 412) | hooks verdes (`_test-runner.sh`); regressão verde; carga PASS; `status-projeto.sh --check` |
| **P8** | ADR-0082 nova + emenda ADR-0023 + REGRAS + matriz-feature-perfil + STATUS-GERADO + AGENTS §11/§12 + matriz-reconciliacao ENXUTA + registro GATE-OSME-RECEBIMENTO-7.5 + frontmatters draft→stable | gate anti-drift; `status-projeto.sh --check` |
| **P9** | auditores roteados (INV-RITUAL-003): essenciais (qualidade·segurança·llm·idempotência·produto) + **performance OBRIGATÓRIO** (índices/seq scan/N+1) + **observabilidade** (migration/trigger/tenant_id) ; supplychain SÓ se dep nova (núcleo não traz); conformidade-lgpd só se tocar PII (não toca — equip. é técnico) ; drift-docs FORA. Verificação adversarial de TODO MÉDIO+ (R6); 2ª passada escopada (R5) | zero C/A/M (INV-RITUAL-001) → FECHADA + CURRENT.md; BAIXOs em lote (R10) |

## Riscos mapeados

1. **Triggers PL/pgSQL pós-rename (TL-OSME-01) — risco CRÍTICO.** Corpo da função guarda texto-fonte;
   `RENAME COLUMN` não recompila → erro só no 1º INSERT/UPDATE. `CREATE OR REPLACE` de AMBAS + reverse
   + **drill em banco COM dados** (não CI vazio). É o achado que passa em todo code review.
2. **Detecção de baixado vira seq scan (TL-OSME-02) — risco ALTO.** Índice `atv_tenant_equip_estado_idx`
   obrigatório; `auditor-performance` (P9) confirma.
3. **3 call-sites omitidos (TL-OSME-03).** `adicionar_atividade`/reabertura/`criar_os_avulsa` confiavam
   no trigger copiar da OS; sem o input de equipamento, atividade nasce sem equip. ou clona errado.
   Cada um com teste próprio.
4. **Concorrência cross-equipamento (Risco #2 / TL-OSME-07).** O índice parcial isola por `equipamento_id`
   (2 equip. distintos não colidem); a matriz ADR-0041 distingue grandeza, o índice não (débito M4
   pré-existente — non-goal explícito). Teste de carga ≥50 threads obrigatório.
5. **Recebimento por instrumento (D-OSME-5 / RBC) — risco ALTO de NC CGCRE.** Ponteiro move OS→atividade
   + INV-OSME-RCB-001 (item recebido = item calibrado). Seam de preenchimento = GATE (app equipamentos).
6. **`OSSnapshot.equipamento_id` nullable propaga via mypy (D-OSME-2).** ~7 call-sites de leitura; cada
   um precisa aceitar None. Não é trivial — é parte do esforço L.

## GATEs nascidos / rastreados

- **GATE-OSME-RECEBIMENTO-7.5** (RBC-OSME-4) — conserto do vínculo recebimento→atividade no app
  `equipamentos` (`EquipamentoRecebimento.atividade_os_id` + produtor publica `atividade_id` + consumer
  popula por instrumento). Esta frente entrega a estrutura conforme; o seam fecha na ativação da recepção.
- **Débito M4 grandeza na matriz ADR-0041** (TL-OSME-07) — não nasce aqui, só registrado como non-goal.

## Decisões do orquestrador (P3 — nenhuma de PRODUTO em aberto; D-OSME-3 já no batch Roldão)

1. **Migration única `0018`** (não fatiar em 2): rename + triggers + índices + OS/recebimento + ItemComercialOS
   na MESMA migration mantém a consistência atômica do schema (trigger e coluna renomeada não podem divergir
   entre migrations). `reverse_sql` simétrico restaura tudo.
2. **`ADR-0082`** — confirmar número livre no P8 (`docs/adr/` vai até 0081 hoje).
3. **`AtividadeDaOS.equipamento_id` permanece nullable no DDL** (não NOT NULL no banco) — itens legados +
   defesa; a obrigatoriedade "atividade técnica tem equipamento" é validada no use case + INV, não por
   `NOT NULL` de coluna (evita quebra de migration em dados legados sem equipamento). CHECK defensivo opcional.
4. **Recebimento move OS→atividade nesta frente; preenchimento = GATE.** Estrutura conforme agora; seam depois.
5. **`ItemComercialOS` Padrão A soft-delete** (editável antes do faturamento) — não WORM (não é registro
   probatório metrológico; é linha comercial).
