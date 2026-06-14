---
owner: agente-ia
revisado-em: 2026-06-13
proximo-review: 2026-09-13
status: draft
diataxis: reference
audiencia: [agente, auditor]
frente: os-multi-equipamento
tipo: spec
versao: 2
relacionados:
  - docs/faseamento/os-multi-equipamento/T-OSME-000-investigacao.md
  - docs/faseamento/os-multi-equipamento/reviews-consolidado.md
  - docs/adr/0023-os-com-atividades.md
  - docs/adr/0041-os-concorrencia-atividades.md
---

# Spec v2 — frente `os-multi-equipamento` (retrofit cirúrgico OS 1→N equipamentos)

> Recorte sobre o módulo OS **fechado** (Marco 3). Origem: R-ORC-3 (Roldão). Pré-requisito de
> `orcamentos`. Base: T-OSME-000 + reviews P2 (`tech-lead` + `consultor-rbc`, ambos APROVA C/ CORREÇÕES)
> + batch Roldão (D-OSME-3 = item comercial como linha na OS). **v2 (2026-06-13):** incorpora 3 CRÍTICOS
> de migration/índice/call-sites, recebimento por instrumento (cl. 7.5) e a entidade `ItemComercialOS`.
> Esforço **M→L**, aditivo/reversível. Insumo para P3 (plan/tasks).

## 1. Tese e fronteira

A OS deixa de ser container de **1 equipamento** (`OS.equipamento` FK NOT NULL) e passa a conter:
**(a)** N atividades técnicas, cada uma com SEU equipamento (`AtividadeDaOS.equipamento_id`, NOT NULL),
**(b)** N **itens comerciais** sem equipamento (`ItemComercialOS` — deslocamento/taxa, decisão Roldão
D-OSME-3). É **aditivo e reversível** — a coluna alvo das atividades e o índice de concorrência
(`INV-OS-CONC-001`) **já existem e já chaveiam pela atividade** (T-OSME-000 §1); a "desnormalização"
vira fonte (renomeada). O recebimento do item calibrando (`equipamento_recebimento_id`) migra de 1-por-OS
para **por atividade** (por instrumento — cl. 7.4.3/7.8.2.1, D-OSME-5).

**O que NÃO é (fronteiras):**
- **Não refaz a OS** — retrofit cirúrgico: migration RELAXANTE (não destrutiva, reversível), `CREATE OR
  REPLACE` dos triggers, ~19 call-sites. Não toca máquina de estados, aceite, NC, checklist, evidência,
  SLA, sucessão.
- **Não publica `OS.Aberta`** — já publica (`os.aberta` cruza o `bus_outbox` via INT-01, T-OSME-000 §2).
  O consumer que fecha `aprovado_pendente_os→convertido` é frente `orcamentos`.
- **Não cria o módulo `orcamentos`** — só estabiliza o ENVELOPE (header→item).
- **Não conserta o seam de PREENCHIMENTO do recebimento** (produtor `criar_recebimento` não publica
  `atividade_id`; `EquipamentoRecebimento` sem `atividade_os_id`) — dívida pré-existente de outro app
  (`equipamentos`) = **GATE-OSME-RECEBIMENTO-7.5**. Esta frente entrega só a ESTRUTURA conforme (RBC-OSME-4).
- **Não resolve a dimensão grandeza da matriz ADR-0041** (débito M4 pré-existente, TL-OSME-07).
- **Não muda a relação OS↔Cliente** (1:1) nem o enum técnico `TipoAtividade` (fechado).

## 2. User stories e critérios de aceite (binários)

**US-OSME-001 — OS com N equipamentos (1 por atividade técnica).**
- AC-001-1: uma OS pode conter atividades de equipamentos DISTINTOS; cada `AtividadeDaOS` tem o seu
  `equipamento_id` (NOT NULL — não mais herdado da OS).
- AC-001-2: `OS.equipamento` aceita `NULL` (migration relaxante); OS multi-equip grava `NULL` (D-OSME-2);
  OS single-equip legada/avulsa pode manter o equipamento na OS.
- AC-001-3: trigger de imutabilidade pós-INSERT do `equipamento_id` da atividade **permanece**.

**US-OSME-002 — Envelope `Orcamento.Aprovado` carrega equipamento por item.**
- AC-002-1: cada item do envelope carrega `equipamento_id` (UUID); itens sem equipamento são itens
  comerciais (US-OSME-006), não atividades. `equipamento_id` do header torna-se opcional/derivado.
- AC-002-2: `abrir_os_via_orcamento` cria cada atividade com o `equipamento_id` do seu item; nenhuma
  atividade depende de cópia do header.
- AC-002-3: replay idempotente (não duplica OS) — `@consumer_idempotente` inalterado.

**US-OSME-003 — Criação/adição de atividade por equipamento (3 call-sites — TL-OSME-03).**
- AC-003-1: `adicionar_atividade` a OS existente recebe `equipamento_id` no input e valida
  INV-OS-EQP-001 (equipamento BAIXADO/DESCARTADO → 422) — enforcement hoje inexistente nesse caminho.
- AC-003-2: reabertura (`operacoes_avancadas`) clona cada atividade com **seu** `equipamento_id` (não
  perde para NULL ao copiar da OS-mãe nullable).
- AC-003-3: OS avulsa (`POST /os/avulsa`) aceita `equipamento_id` por item (D-OSME-4); o
  `payload_fingerprint` de idempotência usa os equipamentos dos itens.

**US-OSME-004 — Detecção de equipamento baixado por atividade (Risco #1 ALTO).**
- AC-004-1: `Equipamento.Baixado`/`Descartado` localiza OSs afetadas via `AtividadeDaOS.equipamento_id`
  → OSs pai, usando o índice novo `atv_tenant_equip_estado_idx` (TL-OSME-02).
- AC-004-2: pré-check de abertura rejeita 422 `EquipamentoBaixadoEmOS` se QUALQUER equipamento distinto
  dos itens estiver BAIXADO/DESCARTADO. **Teste UNHAPPY explícito**: OS de 2 equipamentos, 1 baixado →
  rejeita; equipamento baixado fora de qualquer atividade → 0 OSs (sem falso-positivo).

**US-OSME-005 — Concorrência cross-equipamento sem falso-412 (Risco #2 MÉDIO).**
- AC-005-1: 2 atividades bloqueantes de equipamentos DIFERENTES, na mesma OS, EM_EXECUCAO simultâneas →
  sem 412 (índice parcial isola por `equipamento_id`).
- AC-005-2: 2 atividades bloqueantes do MESMO equipamento (mesma OS ou OSs distintas) → 412
  `ConcorrenciaAtividadesIncompativel`.
- AC-005-3: teste de carga novo (`tests/carga/`, ≥50 threads) confirma AC-005-1 e AC-005-2.

**US-OSME-006 — Itens comerciais na OS (`ItemComercialOS` — decisão Roldão D-OSME-3).**
- AC-006-1: a OS pode ter N `ItemComercialOS` (deslocamento/taxa/outro) sem equipamento; aparecem como
  linha própria na OS (não embutido só no total).
- AC-006-2: `ItemComercialOS` nunca tem `equipamento_id` nem entra no índice de concorrência
  (INV-OSME-ITEMCOM-001); seu valor soma em `OS.valor_total`/`valor_total_atualizado`.
- AC-006-3: itens sem `equipamento_id` no envelope `Orcamento.Aprovado` viram `ItemComercialOS` (não
  `AtividadeDaOS`); itens com `equipamento_id` viram atividade técnica.

**US-OSME-007 — Recebimento por instrumento, cl. 7.5/7.4.3 (Risco #3 ALTO — D-OSME-5).**
- AC-007-1: `equipamento_recebimento_id` migra de `OS` para `AtividadeDaOS` (nullable). Em OS de bancada
  com atividade `requer_recebimento=true`, o vínculo é **obrigatoriamente por atividade** (cl. 7.4.3 —
  anormalidades registradas por item); 1-por-OS só admissível em OS single-instrumento (degenera).
- AC-007-2: INV-OSME-RCB-001 — atividade `requer_recebimento=true` ⟹ `equipamento_recebimento_id`
  NOT NULL **e** `EquipamentoRecebimento.equipamento_id == AtividadeDaOS.equipamento_id` (item recebido =
  item calibrado — cl. 7.4.2 + 7.8.2.1).
- AC-007-3 (RBC-OSME-5): recebimento NC parcial — atividade cujo `EquipamentoRecebimento.status_fluxo_lab`
  for `nao_conformidade_recebimento` **não inicia**; as demais atividades da OS seguem (bloqueio por
  atividade, não por OS).
- AC-007-4: o conserto do seam de preenchimento (produtor publica `atividade_id`;
  `EquipamentoRecebimento.atividade_os_id`) = **GATE-OSME-RECEBIMENTO-7.5** (RBC-OSME-4) — fora desta frente.

## 3. Decisões cravadas (D-OSME-1..5)

- **D-OSME-1 — RENOMEAR `equipamento_id_desnormalizado`→`equipamento_id`** (tech-lead). Semântica virou
  fonte; doc/teste já usam o nome novo (REGRAS:162). **Migration obrigatória (TL-OSME-01):** `RenameField`
  + `CREATE OR REPLACE` de AMBAS as funções PL/pgSQL (forward reescrita SEM `SELECT ... FROM ordens_servico`
  mas mantendo o lookup de `tipo_bloqueia_concorrencia` integral — TL-OSME-05; imutável citando a coluna
  nova) + `reverse_sql` simétrico + teste pós-migration que INSERE e ATUALIZA atividade (exercita ambos
  triggers) em banco COM dados.
- **D-OSME-2 — `OS.equipamento`/`OSSnapshot.equipamento_id` NULLABLE**, sem "predominante". `os_tenant_equip_idx`
  vira parcial `WHERE equipamento_id IS NOT NULL`. `OSSnapshot.equipamento_id` vira `UUID | None`; o plan
  lista os ~7 call-sites de leitura (`iniciar_atividade:178`, `operacoes_avancadas:120,176`, `queries/
  listagem:26,39`, `queries/visao_360:45,97`) — mypy strict propaga.
- **D-OSME-3 — itens comerciais = entidade `ItemComercialOS`** (Roldão) — linha própria na OS já em Wave A.
  NÃO via `AtividadeDaOS` com equipamento NULL (tech-lead vetou poluir o agregado técnico).
- **D-OSME-4 — OS avulsa aceita equipamento por item** — `ItemOSAvulsa.equipamento_id` + `criar_os_avulsa`
  distribui por atividade + `payload_fingerprint` por equipamentos dos itens.
- **D-OSME-5 — recebimento POR INSTRUMENTO** (consultor RBC) — requisito cl. 7.4.3/7.8.2.1, não preferência.
  Ponteiro migra OS→`AtividadeDaOS`.

## 4. Mudanças no modelo (domínio + infra)

| Elemento | Hoje | Depois |
|---|---|---|
| `OS.equipamento` (`models.py:51`) | FK `PROTECT` **NOT NULL** | FK `PROTECT` **`null=True`** |
| `os_tenant_equip_idx` (`models.py:159`) | `(tenant, equipamento)` | **parcial** `WHERE equipamento_id IS NOT NULL` |
| `OS.equipamento_recebimento_id` (`models.py:128`) | 1 por OS | **removido da OS** → `AtividadeDaOS.equipamento_recebimento_id` (nullable) — RBC-OSME-2 |
| `AtividadeDaOS.equipamento_id_desnormalizado` (`:244`) | desnormalizado da OS | **`equipamento_id`** fonte própria, **NOT NULL** (técnica); D-OSME-1 |
| `AtividadeDaOS.equipamento_recebimento_id` (novo) | — | nullable; vínculo por instrumento (cl. 7.5) |
| índice novo `atv_tenant_equip_estado_idx` (TL-OSME-02) | — | `(tenant_id, equipamento_id, estado)` — cobre detecção de baixado |
| Trigger forward `*_denormalize_check` (`0005:39-52`) | copia equip. da OS + lookup `tipo_bloqueia` | `CREATE OR REPLACE`: remove só o `SELECT equipamento_id FROM ordens_servico`; **mantém** lookup `tipo_bloqueia_concorrencia` integral (TL-OSME-05) |
| Trigger imutabilidade `*_imutavel_check` (`0005:65-83`) | bloqueia UPDATE, cita coluna velha | `CREATE OR REPLACE` citando `equipamento_id` (TL-OSME-01) |
| Índice `idx_atividade_em_execucao_por_equip` (`0005:87-89`) | `(tenant, equipamento_id_desnormalizado)` | **não move**; acompanha o rename da coluna |
| `OSSnapshot.equipamento_id` (`entities.py:36`) | `UUID` | `UUID \| None` |
| `AtividadeSnapshot` (`entities.py:74`) | `equipamento_id_desnormalizado: UUID\|None` | `equipamento_id: UUID` + `equipamento_recebimento_id: UUID\|None` |
| `ItemOrcamento` DTO (`abrir_os_via_orcamento.py:57`) | `{tipo, sequencia, valor_unitario, requer_recebimento}` | **+ `equipamento_id: UUID\|None`** (None ⟹ item comercial) |
| `ItemOSAvulsa` (`views.py:504`) | sem equipamento | **+ `equipamento_id: UUID\|None`** (D-OSME-4) |

**Entidade nova `ItemComercialOS`** (D-OSME-3): `id`, `tenant_id` (FK PROTECT), `os` (FK PROTECT), `tipo`
(enum: `deslocamento`/`taxa_visita`/`outro`), `descricao_publica` (sem PII), `valor` (Decimal 14,2),
`quantidade` (default 1), `origem_item_id?` (rastreio do orçamento), `criado_em`/`atualizado_em`. Padrão A
soft-delete (ADR-0031) — pode ser editado/cancelado antes do faturamento. RLS + tenant herdado. **Nunca**
tem `equipamento_id` nem `tipo_bloqueia_concorrencia`.

**Migration `0018_os_multi_equipamento`** (app `ordens_servico`): `RenameField` + `AlterField(OS.equipamento
null=True)` + remove `OS.equipamento_recebimento_id` / add `AtividadeDaOS.equipamento_recebimento_id` +
`RemoveIndex/AddIndex` parcial + `AddIndex atv_tenant_equip_estado_idx` + `CreateModel ItemComercialOS` +
`RunSQL CREATE OR REPLACE` dos 2 triggers (com `reverse_sql`). **Não há `DROP COLUMN` de dado de negócio**
(o `equipamento_recebimento_id` da OS é ponteiro denormalizado nunca populado — RBC-OSME-4; mover não perde
dado). Reversível. **Não exige confirmação destrutiva do Roldão.**

## 5. Invariantes — emendas (P8 crava em REGRAS)

| INV | Mudança |
|---|---|
| **INV-OS-ATIV-002** (`REGRAS:146`, `ADR-0023:143`) | reescrever: herda `tenant_id`+`cliente_id` da OS; **`equipamento_id` é PRÓPRIO da atividade** (não herdado). Cross-tenant continua proibido. |
| **INV-OS-EQP-001** (`REGRAS:159`) | enforcement passa a validar equip. POR ATIVIDADE, incl. `adicionarAtividade` (TL-OSME-03). |
| **INV-OS-CONC-001** (`REGRAS:156,162`) | já cita `equipamento_id` (correto por antecipação — TL-OSME-06); **não reverter** para nome velho. |
| **INV-OSME-RCB-001** (nova) | atividade `requer_recebimento=true` ⟹ `equipamento_recebimento_id` NOT NULL **e** `EquipamentoRecebimento.equipamento_id == AtividadeDaOS.equipamento_id` (CHECK/validação use case). |
| **INV-OSME-ITEMCOM-001** (nova) | `ItemComercialOS` nunca tem equipamento nem entra no índice de concorrência; soma em `valor_total`. |

**Comportamento por perfil regulatório (ADR-0067 / `docs/conformidade/comum/matriz-feature-perfil.md`):**
- INV-OS-EQP-001 (equipamento baixado bloqueia) e INV-OS-CONC-001 (concorrência metrológica) = **Absolutas
  (todos perfis A/B/C/D)** — não variam por perfil.
- Recebimento por instrumento (INV-OSME-RCB-001, cl. 7.4.3) = **perfil-aware**: perfil A (RBC acreditado)
  exige registro de condição de recebimento POR instrumento (NC maior CGCRE se ausente — RBC-OSME-3);
  perfis B/C/D conforme matriz-feature-perfil.md (precedente: `prazo_link_calibracao_*` já varia por perfil
  no `TipoAtividadeConfig`). Linha na matriz cravada no P8.
- `ItemComercialOS` + retrofit estrutural (equipamento por atividade) = sem dimensão regulatória
  (comercial/estrutural — comportamento idêntico em todos os perfis).

## 6. Envelope, eventos e seams

- **Envelope `Orcamento.Aprovado` (header→item):** `equipamento_id` migra do header para cada item
  (None ⟹ `ItemComercialOS`); `equipamento_recebimento_id` por item de bancada (cl. 7.5). Atualizar a
  docstring-contrato em `consumers/orcamento.py:73-104` e `_parse_input`. A spec de `orcamentos` sobe para
  v2 consumindo este envelope. **INV-ORC-APROVADO-ENVELOPE** (spec orçamentos) referencia esta versão.
- **`os.aberta` = envelope v+1 ADITIVO (TL-OSME-10):** cada atividade planejada no `payload_data` ganha
  `equipamento_id` (campo novo, retrocompatível). Não há novo evento; consumidores da saga downstream
  (`value_objects.py:128`) recebem o shape estendido.
- **Consome:** `Equipamento` (status, por atividade); `TipoAtividadeConfig` (flag concorrência);
  `audit.event_helpers.publicar_evento` (inalterado).

## 7. REST

`POST /v1/os/avulsa` (`views.py:519`) aceita `itens[{..., equipamento_id}]` + `itens_comerciais[]`
(D-OSME-4). `GET /v1/os/?equipamento_id=` filtra OSs com ALGUMA atividade no equipamento (via
`AtividadeDaOS.equipamento_id`). `visao_360`/`listagem` agregam os equipamentos das atividades + listam
`ItemComercialOS`. CRUD mínimo de `ItemComercialOS` (adicionar/remover linha numa OS não-terminal) sob
ação authz `os.gerir_item_comercial`. Sem outros endpoints novos.

## 8. Non-goals

Reabertura granular por atividade (ADR-0023 difere) · módulo `orcamentos` (frente própria) · consumer
`os.aberta` no orçamento (frente orçamentos) · telas/PDF · enum `TipoAtividade` · relação OS↔Cliente ·
**dimensão grandeza da matriz ADR-0041** (débito M4 pré-existente — TL-OSME-07) · **seam de preenchimento
do recebimento** (produtor publica `atividade_id` + `EquipamentoRecebimento.atividade_os_id` —
GATE-OSME-RECEBIMENTO-7.5).

## 9. GATEs rastreados

**GATE-OSME-RECEBIMENTO-7.5** (RBC-OSME-4) — conserto do vínculo recebimento→atividade no produtor/entidade
do app `equipamentos` (`EquipamentoRecebimento.atividade_os_id` + produtor publica `atividade_id` +
consumer popula `AtividadeDaOS.equipamento_recebimento_id` por instrumento). Esta frente entrega a estrutura
conforme; o seam fecha quando a recepção de bancada for ativada. Cobre RBC-OSME-1/4/5 no nível de produção real.

## 10. Log de revisões

- v1 (2026-06-13): insumo P2.
- v2 (2026-06-13): incorpora P2 — `tech-lead` (TL-OSME-01..10, APROVA C/ CORREÇÕES) + `consultor-rbc`
  (RBC-OSME-1..5, APROVA C/ CORREÇÕES) + batch Roldão (D-OSME-3 = `ItemComercialOS` linha na OS). Detalhe:
  `reviews-consolidado.md`. Esforço M→L. Próximo: P3 plan/tasks.
