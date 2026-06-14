---
owner: agente-ia
revisado-em: 2026-06-13
proximo-review: 2026-09-13
status: stable
diataxis: explanation
audiencia: [agente, auditor]
frente: os-multi-equipamento
tipo: reviews-p2
relacionados:
  - docs/faseamento/os-multi-equipamento/spec.md
  - docs/faseamento/os-multi-equipamento/T-OSME-000-investigacao.md
---

# P2 — Revisões consolidadas + decisões — frente `os-multi-equipamento`

> `tech-lead-saas-regulado` + `consultor-rbc-iso17025`, 2026-06-13. Ambos **APROVA COM CORREÇÕES**.
> Batch Roldão resolveu D-OSME-3 (item comercial). **Resultado:** spec sobe para v2 com 3 CRÍTICOS de
> migration/índice/call-sites + recebimento por instrumento (cl. 7.5) + entidade `ItemComercialOS`.
> Esforço revisado: **M→L** (entidade nova de item comercial + recebimento por atividade + 3 call-sites
> a mais que a v1 não viu). Continua aditivo/reversível.

## Decisões cravadas

### Batch Roldão (2026-06-13)
- **D-OSME-3 — Roldão escolheu "JÁ como linha própria na OS".** Itens avulsos (deslocamento/taxa) viram
  **entidade `ItemComercialOS`** em Wave A (não diferir). NÃO via "atividade com equipamento NULL" (o
  tech-lead corretamente vetou poluir `AtividadeDaOS`): entidade própria LEVE, sem checklist/aceite/NC/
  concorrência. Resolve a contradição TL-OSME-04: `AtividadeDaOS` mantém `equipamento_id` NOT NULL
  (técnica); a linha comercial vai pra entidade separada. **GATE-OSME-ITEM-COMERCIAL deixa de ser GATE.**

### Técnicas — tech-lead (TL-OSME-*)
- **D-OSME-1 — RENOMEAR `equipamento_id_desnormalizado`→`equipamento_id`.** Semântica virou fonte própria;
  doc/teste já usam `equipamento_id` (REGRAS:162, `test_inv_os_conc_001:6`) — rename alinha código à verdade.
  **Condição (TL-OSME-01 CRÍTICO):** a migration `0018` precisa `RenameField` + `CREATE OR REPLACE` de
  **AMBAS** as funções PL/pgSQL (`_denormalize_check` reescrita SEM o `SELECT equipamento_id FROM ordens_servico`
  + `_imutavel_check` citando a coluna nova) com `reverse_sql` simétrico. O `RENAME COLUMN` propaga ao
  índice mas **NÃO recompila o corpo das funções** (guardam texto-fonte; erro só no 1º INSERT em runtime).
- **D-OSME-2 — `OS.equipamento`/`OSSnapshot.equipamento_id` NULLABLE, sem "predominante".** `os_tenant_equip_idx`
  vira parcial `WHERE equipamento_id IS NOT NULL`. Plan deve listar ~7 call-sites que leem
  `OSSnapshot.equipamento_id` como `UUID` e viram `UUID | None` (mypy strict propaga).
- **D-OSME-4 — OS avulsa aceita equipamento por item — exige mexer no DTO.** `ItemOSAvulsa` (`views.py:504`)
  + `criar_os_avulsa` ganham `equipamento_id`; o **`payload_fingerprint` de idempotência** (`views.py:517`)
  passa a usar os equipamentos dos itens (senão 2 OS avulsas com header igual mas equipamentos diferentes
  colidem idempotência).

### Metrológica — consultor RBC (RBC-OSME-*)
- **D-OSME-5 — recebimento POR INSTRUMENTO é REQUISITO de conformidade (não "default conservador").**
  cl. 7.4.3 (anormalidades de recebimento registradas POR item) + cl. 7.8.2.1(i) (certificado referencia
  identificação inequívoca + condição do item). `EquipamentoRecebimento` JÁ é por instrumento (FK
  `equipamento`); é o **ponteiro `OS.equipamento_recebimento_id` que mente** numa OS de N instrumentos.
  → mover o ponteiro `equipamento_recebimento_id` de `OS` para `AtividadeDaOS` (nullable). Risco #3
  **escalado MÉDIO→ALTO** (NC maior CGCRE se 3 instrumentos compartilham 1 recebimento).

### Arquitetura/sequenciamento — maestro (RBC-OSME-4)
- **Conserto do seam de PREENCHIMENTO do recebimento = `GATE-OSME-RECEBIMENTO-7.5`.** Descoberta RBC: o
  produtor `criar_recebimento` (`services_recebimento.py:249`) NÃO publica `os_id`/`atividade_id`; o
  consumer (`consumers/equipamento.py:73`) espera `os_id` → o ponteiro **provavelmente nunca é populado
  hoje** (dívida PRÉ-EXISTENTE de OUTRO app — `equipamentos`). **Decisão:** esta frente entrega a
  ESTRUTURA conforme (ponteiro por atividade + validação + invariante INV-OSME-RCB-001); o conserto do
  vínculo recebimento→atividade (`EquipamentoRecebimento.atividade_os_id` + produtor publica atividade_id +
  consumer popula por atividade) vira **GATE-OSME-RECEBIMENTO-7.5**, porque (a) é dívida de outro módulo,
  (b) recepção de bancada não está em operação real (dogfooding), (c) expandir agora estoura o cirúrgico.
  Não é mascaramento — é fronteira de módulo: a estrutura fica pronta; o seam fecha quando recepção ativar.
  - **Emenda 2026-06-14 (P9 — parecer `consultor-rbc-iso17025`):** "estrutura conforme + validação" acima
    lê-se como: a frente entrega a **estrutura de domínio** (`AtividadeSnapshot.equipamento_recebimento_id`)
    + **invariante INV-OSME-RCB-001 declarado** + **validação OS-level como ponte** (degeneração single-
    instrumento). O **enforcement POR ATIVIDADE** (item recebido == calibrado + NC parcial) depende do dado
    por-atividade do seam, logo **integra o GATE-OSME-RECEBIMENTO-7.5** — não é entregue agora (validaria
    contra coluna vazia). Ver emenda da spec §2 (US-OSME-007) + `tasks.md` T-OSME-034.

## Achados que entram na spec v2

| ID | Sev | Achado | Onde resolve |
|---|---|---|---|
| TL-OSME-01 | CRÍTICO | RenameField quebra os 2 triggers PL/pgSQL (corpo SQL literal) | §4 migration: CREATE OR REPLACE de ambas + reverse + drill em banco c/ dados |
| TL-OSME-02 | CRÍTICO | detecção de baixado vira seq scan (sem índice) | §4: `CREATE INDEX atv_tenant_equip_estado_idx (tenant_id, equipamento_id, estado)` |
| TL-OSME-03 | CRÍTICO | 3 call-sites omitidos criam atividade: `adicionar_atividade` (+ input equip. + INV-OS-EQP-001), reabertura (clonar por atividade), `criar_os_avulsa` | §2/§4 novos AC |
| TL-OSME-04 | ALTO | contradição D-OSME-3 vs AC-OSME-001-3/INV-OSME-001 | resolvida por D-OSME-3 Roldão: `ItemComercialOS` separada; remover AC-001-3 + INV-OSME-001 |
| TL-OSME-05 | ALTO | trigger forward reescrito não pode quebrar lookup `tipo_bloqueia_concorrencia` | §4: manter bloco lookup integral; só remove o SELECT da OS |
| TL-OSME-06 | ALTO | REGRAS:162 + teste já citam `equipamento_id` — não "corrigir" de volta | §5 nota |
| TL-OSME-07 | MÉDIO | matriz ADR-0041 distingue grandeza; índice não (débito M4 pré-existente) | §8 non-goal explícito |
| TL-OSME-08 | MÉDIO | sem N+1 na detecção (só loga); índice TL-02 cobre | confirmado, sem ação |
| TL-OSME-09 | MÉDIO | índice parcial reverse = DROP+CREATE (lock momentâneo) | §4 nota; teste reverse |
| TL-OSME-10 | MÉDIO | payload `os.aberta` é "v+1 aditivo" (atividade ganha equip.), não "inalterado" | §6 corrigir classificação |
| RBC-OSME-1 | MÉDIO | identificação inequívoca de N instrumentos iguais (cl. 7.4.2 + 7.8.2.1(i)) | INV-OSME-RCB-001: `EquipamentoRecebimento.equipamento_id == AtividadeDaOS.equipamento_id` |
| RBC-OSME-2 | MÉDIO | spec omite `OS.equipamento_recebimento_id` na tabela §4 | §4: ponteiro migra OS→AtividadeDaOS (nullable) |
| RBC-OSME-3 | BAIXO | AC-OSME-005-1 "conservador" minimiza obrigação | §2 reescrever (obrigação cl. 7.4.3, não preferência) |
| RBC-OSME-4 | ALTO | seam recebimento sem `os_id`/`atividade_id` (dívida pré-existente) | GATE-OSME-RECEBIMENTO-7.5 (decisão maestro acima) |
| RBC-OSME-5 | MÉDIO | recebimento NC parcial (1 de N recusado) bloqueia só aquela atividade | §2 novo AC: bloqueio por atividade |

## Invariantes (P8)
- **INV-OS-ATIV-002** (emenda): equipamento é PRÓPRIO da atividade (não herdado); herança = só tenant/cliente.
- **INV-OSME-RCB-001** (nova): atividade `requer_recebimento=true` ⟹ `equipamento_recebimento_id` NOT NULL
  **e** `EquipamentoRecebimento.equipamento_id == AtividadeDaOS.equipamento_id` (item recebido = item
  calibrado — cl. 7.4.2 + 7.8.2.1).
- **INV-OSME-ITEMCOM-001** (nova): `ItemComercialOS` nunca tem `equipamento_id` nem entra no índice de
  concorrência; soma em `OS.valor_total`/`valor_total_atualizado`.

## Próximos passos (ordem cravada)
1. **spec v2** (este consolidado) — feito junto deste doc.
2. **P3 plan/tasks** — fatias: (1) migration `0018` (rename + triggers CREATE OR REPLACE + índices + OS/recebimento
   nullable) · (2) `ItemComercialOS` (entidade+RLS+CRUD mínimo) · (3) envelope header→item + use cases (abrir/
   adicionar/avulsa/reabertura) + consumer detecção por atividade · (4) emendas REGRAS/ADR-0023 + ADR-0082 +
   testes regressão/carga.
3. **P4..P7 implementação** → P8 emendas → **P9 auditores** (idempotência + observabilidade + qualidade +
   produto + llm-correctness + performance OBRIGATÓRIOS — toca consumer/migration/índices) com 2ª passada
   escopada + verificação adversarial de TODO MÉDIO+ (INV-RITUAL-001 / R5-R6).
