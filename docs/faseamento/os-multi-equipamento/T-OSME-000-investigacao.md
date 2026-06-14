---
owner: agente-ia
revisado-em: 2026-06-13
proximo-review: 2026-09-13
status: stable
diataxis: explanation
audiencia: [agente, auditor]
frente: os-multi-equipamento
tipo: investigacao-p0
relacionados:
  - docs/faseamento/orcamentos/reviews-consolidado.md
  - docs/adr/0023-os-com-atividades.md
  - docs/adr/0041-concorrencia-atividade-os.md
  - src/infrastructure/ordens_servico/models.py
  - src/infrastructure/ordens_servico/migrations/0005_concorrencia_desnormalizacao_e_index.py
---

# T-OSME-000 — Investigação regra #0 — frente `os-multi-equipamento`

> **Pra quê:** ler o estado REAL (código + invariantes + envelope) do módulo OS **fechado**
> antes de escrever a spec do retrofit 1→N equipamentos. Molde: `T-ORC-000-investigacao.md`.
> **Origem:** dependência DURA descoberta no P2 de `orcamentos` (R-ORC-3 do Roldão — "tanto
> orçamento quanto OS devem permitir N equipamentos, cada um com seus itens + itens compartilhados
> sem equipamento"). Sequenciamento cravado: **esta frente ANTES de `orcamentos` chegar em P3**
> (peça compartilhada feita 1x — `feedback_ordem_dependencia`).
> **Fonte:** 3 subagentes Explore (call-sites · invariantes/ADR · envelope/outbox) + leitura
> direta de `models.py`, `value_objects.py`, `repositories.py`, `abrir_os_via_orcamento.py`,
> `consumers/orcamento.py`, 2026-06-13.

## 1. Estado real — OS é módulo FECHADO com 1 equipamento, MAS a infra por-atividade já existe

- **OS hoje = 1 equipamento, NOT NULL:** `OS.equipamento` FK `PROTECT` **não-nullable**
  (`models.py:51-56`), com índice `os_tenant_equip_idx` em `(tenant, equipamento)` (`models.py:159`).
  Help-text já amarra `INV-OS-EQP-001`.
- **Atividade HERDA o equipamento da OS hoje:** `AtividadeDaOS.equipamento_id_desnormalizado`
  (`models.py:244-252`) é populado por **trigger BEFORE INSERT** que faz
  `SELECT equipamento_id FROM ordens_servico WHERE id=NEW.os_id`
  (`migrations/0005_*.py:39-41`, trigger `atividade_da_os_concorrencia_denormalize_trg`).
  Um segundo trigger torna o campo **imutável pós-INSERT** (`atividade_da_os_concorrencia_imutavel_trg`).
- **🔑 A INFRA QUE TORNA O RETROFIT CIRÚRGICO:** o índice de concorrência metrológica
  `INV-OS-CONC-001` **já chaveia pela ATIVIDADE, não pela OS**:
  `CREATE UNIQUE INDEX idx_atividade_em_execucao_por_equip ON atividade_da_os
  (tenant_id, equipamento_id_desnormalizado) WHERE estado='em_execucao' AND
  tipo_bloqueia_concorrencia=TRUE` (`migrations/0005_*.py:87-89`). **Não move.** Já está pronto
  pra N equipamentos distintos por OS — só falta a fonte do `equipamento_id_desnormalizado`
  deixar de ser "cópia da OS" e virar "equipamento próprio da atividade".

## 2. Premissa do review de orçamentos que esta investigação CORRIGE

- **TL-ORC-03 dizia "a OS NÃO publica `OS.Aberta` de volta hoje" — DESATUALIZADO.** Verificação
  direta: a OS **JÁ publica** `os.aberta` no `bus_outbox`. Caminho:
  `abrir_os_via_orcamento` grava `EventoDeOSSnapshot(tipo=OS_ABERTA)` (`abrir_os_via_orcamento.py:236-250`)
  → `repository.publicar_evento` (`repositories.py:584-635`) consulta
  `MAPA_TIPO_EVENTO_OS_PARA_ACAO_BUS` (`value_objects.py:126-152`, linha 128: `OS_ABERTA → "os.aberta"`)
  → chama `audit.event_helpers.publicar_evento(acao="os.aberta", outbox=True, cadeia=False)` na
  MESMA `transaction.atomic` (infra **INT-01 / Onda PRE-A.4**).
- **Consequência no escopo:** o item "OS publica `OS.Aberta` de volta" do `CURRENT.md` **já está
  feito**. O que falta pra fechar `aprovado_pendente_os→convertido` é o **consumer no lado de
  `orcamentos`** que escuta `os.aberta` e marca convertido — **isso é frente `orcamentos`, NÃO esta.**
  O `payload_data` de `os.aberta` já carrega `orcamento_id` (`abrir_os_via_orcamento.py:221`),
  então o consumer do orçamento terá como correlacionar. **Esta frente só GARANTE o payload certo.**

## 3. O contrato que muda — envelope `Orcamento.Aprovado` (header → item)

Envelope canônico de hoje (`consumers/orcamento.py:73-150`, espelhado em `_parse_input`):

```
payload{
  ..., equipamento_id (1, header), equipamento_recebimento_id? (1, header), ...,
  itens:[{tipo, sequencia, valor_unitario, requer_recebimento}]   ← SEM equipamento
}
```

`ItemOrcamento` (DTO, `abrir_os_via_orcamento.py:57-66`) NÃO tem `equipamento_id`. O use case usa
`payload.equipamento_id` único pra a OS (`:168`) e deixa `equipamento_id_desnormalizado=None` na
atividade (`:207`) confiando no trigger copiar da OS. **Retrofit:** `equipamento_id` sai do header,
entra em CADA item; itens compartilhados (deslocamento/taxa) têm `equipamento_id=null`.

## 4. Inventário de call-sites de equipamento na OS (subagente Explore 1)

| # | Arquivo:linha | O que faz | Ação no retrofit |
|---|---|---|---|
| 1 | `migrations/0005_*.py:39-41,58-61` | Trigger copia `OS.equipamento_id`→atividade | **MUDA**: atividade traz o seu; trigger para de copiar equip. (mantém cópia de `tipo_bloqueia_concorrencia`) |
| 2 | `migrations/0005_*.py:65-83` | Trigger imutabilidade pós-INSERT | **MANTÉM** |
| 3 | `migrations/0005_*.py:87-89` | Índice `idx_atividade_em_execucao_por_equip` | **NÃO MOVE** (já por atividade) |
| 4 | `models.py:51-56` | `OS.equipamento` FK NOT NULL | **MUDA**: → `null=True` (migration relaxante) |
| 5 | `models.py:159` | índice `os_tenant_equip_idx` | revisar (vira parcial `WHERE equipamento_id IS NOT NULL` ou cai) |
| 6 | `models.py:244-252` | `AtividadeDaOS.equipamento_id_desnormalizado` | **vira FONTE** (decisão D-OSME-1: rename vs manter nome) |
| 7 | `consumers/orcamento.py:48-53,172-181` | pré-check equip. BAIXADO/DESCARTADO (1 equip.) | **MUDA**: validar TODOS os equip. distintos dos itens |
| 8 | `consumers/orcamento.py:108-120,128` | parse itens + `equipamento_id` header | **MUDA**: `equipamento_id` por item; header opcional/removido |
| 9 | `consumers/equipamento.py:25-49` | `Equipamento.Baixado/Descartado` → filtra `OS.equipamento_id` | **MUDA (Risco #1 ALTO)**: filtrar `AtividadeDaOS.equipamento_id_desnormalizado` → OSs pai |
| 10 | `consumers/equipamento.py:70-96` | `equipamento_recebimento.registrado` → `OS.equipamento_recebimento_id` | revisar (cl. 7.5 — ver Risco #3) |
| 11 | `abrir_os_via_orcamento.py:57-66,78,168,207` | DTO + grava equip. na OS + atividade NULL | **MUDA**: `ItemOrcamento.equipamento_id`; atividade recebe o seu; OS nullable |
| 12 | `repositories.py:73,109,317-327,394-403` | snapshot + filtros + `listar_atividades_em_execucao_por_equipamento` | leitura; ajustar onde lê `OS.equipamento_id` |
| 13 | `views.py:229,238,519,536-540` | query param `?equipamento_id` + POST `/os/avulsa` | **MUDA**: OS avulsa precisa equip. por atividade |
| 14 | `queries/listagem.py:26,39,52` · `queries/visao_360.py:45-46,97-98` | DTOs leem `OS.equipamento_id` | ajustar p/ agregar equip. das atividades |
| 15 | `operacoes_avancadas.py:120-121` | reabertura clona `equipamento_id` da OS-mãe | **MUDA**: clonar por atividade |
| 16 | `domain/operacao/os/entities.py:36,74` · `repository.py:51,69-77` | `OSSnapshot.equipamento_id`; protocol | `OSSnapshot.equipamento_id` → `UUID \| None` |

Testes a tocar: `tests/test_m3_os_consumer_orcamento.py`, `tests/test_m3_os_views_api.py`,
`tests/regressao/test_inv_os_eqp_001_baixado.py`, `tests/regressao/test_inv_os_ativ_002_cross_tenant.py`,
`tests/regressao/test_inv_os_conc_001_unique_partial.py` (+ teste de carga concorrência).

## 5. Invariantes e ADR afetados (subagente Explore 2 — texto literal confirmado)

| ID | Onde | Estado hoje | Emenda no retrofit |
|---|---|---|---|
| **INV-OS-ATIV-002** | `REGRAS:146` + `ADR-0023:143-144` | "AtividadeDaOS **herda** equipamento_id **da OS pai**" | reescrever: equipamento é **próprio da atividade** (não herdado); herança permanece só `tenant_id`/`cliente_id` |
| **INV-OS-EQP-001** | `REGRAS:159` | bloqueio valida "abrirOS/adicionarAtividade" (já fala atividade) | manter texto; ajustar enforcement p/ validar equip. POR ATIVIDADE |
| **INV-OS-CONC-001** | `REGRAS:156,162` | índice já em `equipamento_id` da atividade | texto OK; só renomear coluna se D-OSME-1 = rename |
| **ADR-0023** | `docs/adr/0023-*.md` | "OS = container 1 instrumento" (`:47-49`); non-goal `:135` "não redefine os 5 tipos" | **emenda**: OS = container de N instrumentos (1 por atividade); registrar evolução do desenho original |

Nenhum outro `INV-OS-*` menciona equipamento. **ADR nova = 0082** "OS multi-equipamento".

## 6. Três riscos (do P2 de orçamentos — confirmados no código)

- **Risco #1 — ALTO — detecção de equipamento baixado.** `consumers/equipamento.py:25-49` filtra
  `OS.objects.filter(equipamento_id=...)`. Numa OS multi-equip., a OS pai não tem mais o equipamento;
  precisa migrar pra `AtividadeDaOS.equipamento_id_desnormalizado` → OSs pai distintas + **teste
  UNHAPPY explícito** (`feedback_nao_declarar_pronto_sem_rodar`).
- **Risco #2 — MÉDIO — concorrência cross-equipamento.** 2 atividades de equipamentos DIFERENTES na
  mesma OS, EM_EXECUCAO simultâneo, **não** podem dar falso-412. O índice parcial já isola por
  `equipamento_id_desnormalizado` (deve funcionar), mas exige **teste de carga novo** confirmando.
- **Risco #3 — MÉDIO — `equipamento_recebimento_id` é 1 por OS.** cl. 7.5 ISO 17025 (recebimento do
  item calibrando) pode exigir **recebimento POR INSTRUMENTO**. → **acionar `consultor-rbc-iso17025`
  no P2** (decisão metrológica, não do Roldão — `feedback_ordem_dependencia`).

## 7. Recorte do retrofit proposto (cirúrgico, aditivo/reversível — esforço M)

1. **Migration RELAXANTE** (não destrutiva): `OS.equipamento` → `null=True`; `equipamento_id_desnormalizado`
   vira fonte (D-OSME-1: `RenameField`→`equipamento_id` **recomendado** por honestidade semântica, ou
   manter nome — tech-lead decide). `CREATE OR REPLACE` do trigger forward (para de copiar equip. da OS;
   mantém `tipo_bloqueia_concorrencia`). Índice de concorrência **intacto**.
2. **Envelope header→item**: `ItemOrcamento.equipamento_id: UUID | None`; `equipamento_id` do header vira
   opcional/derivado; pré-check de baixado itera os equipamentos distintos.
3. **Use case** `abrir_os_via_orcamento`: atividade recebe `equipamento_id` do seu item; `OSSnapshot.equipamento_id`
   nullable (null em OS multi-equip; ou "predominante" — D-OSME-2).
4. **Consumer `equipamento.py`** (Risco #1): detecção por atividade.
5. **Emendas**: ADR-0023 + INV-OS-ATIV-002 (REGRAS) + ADR-0082 nova.
6. **Itens compartilhados na OS** (deslocamento/taxa, `equipamento_id=null`): **D-OSME-3** — modelagem
   técnica (ver §8). NÃO viram `AtividadeDaOS` (enum técnico fechado + bagagem checklist/aceite/NC).

## 8. Decisões abertas (classificadas por dono — batch no P2)

**TÉCNICA/ARQUITETURA — subagente `tech-lead-saas-regulado` (P2):**
- **D-OSME-1** — `equipamento_id_desnormalizado`: `RenameField`→`equipamento_id` (honesto, toca ~6
  call-sites + entities; índice/trigger acompanham) **vs** manter nome (cirúrgico, mas docstring mente —
  `auditor-llm-correctness` pega). *Recomendação: renomear* (semântica deixou de ser "desnormalização").
- **D-OSME-2** — `OSSnapshot.equipamento_id` nullable: deixar `null` em OS multi-equip **vs** derivar
  "equipamento predominante". *Recomendação: `null`* + manter `os_tenant_equip_idx` como índice parcial
  (`WHERE equipamento_id IS NOT NULL`) pra OS single-equip legada/avulsa.
- **D-OSME-3** — itens compartilhados/comerciais na OS: entidade leve `ItemComercialOS` agora **vs**
  somar no `valor_total` e diferir entidade pra faturamento-por-item (Wave B já difere). *Recomendação:
  diferir entidade (GATE-OSME-ITEM-COMERCIAL); a OS Wave A modela atividades técnicas com equipamento, o
  valor comercial entra em `valor_total`* — não reduz R-ORC-3 (o ORÇAMENTO lista os itens compartilhados).
- **D-OSME-4** — OS avulsa (`POST /os/avulsa`, `views.py:519`): aceitar `equipamento_id` por atividade no
  payload. *Recomendação: sim, mesmo contrato do envelope.*

**METROLÓGICA — subagente `consultor-rbc-iso17025` (P2):**
- **D-OSME-5** (Risco #3) — `equipamento_recebimento_id` 1-por-OS vs por-instrumento (cl. 7.5). Decisão
  do consultor; default conservador: por atividade quando `requer_recebimento=true`.

**PRODUTO — Roldão (só se P2 revelar caminho ambíguo):** nenhuma decisão de produto NOVA identificada —
R-ORC-1/2/3 já cravaram o requisito (N equipamentos + itens compartilhados). Levar ao batch SÓ se
tech-lead/consultor escalarem.

## 9. Próximos passos do ritual

P1 spec (recorte §7) → P2 revisões `tech-lead-saas-regulado` + `consultor-rbc-iso17025` (+ batch Roldão
SÓ se houver decisão de produto) → P3 plan/tasks (1 migration+trigger+índice / 2 envelope+use case+consumer /
3 emendas+testes regressão+carga) → P4..P7 implementação → P8 emendas cross-doc → P9 auditores roteados
(idempotência + observabilidade + qualidade + produto + llm-correctness OBRIGATÓRIOS — toca consumer/migration)
com 2ª passada escopada + verificação adversarial de todo MÉDIO+ (INV-RITUAL-001 / R5-R6).
