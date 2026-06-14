---
owner: agente-ia
revisado-em: 2026-06-14
status: aceito
adr: 0082
relacionados: [0023, 0030, 0031, 0032, 0041, 0067]
---

# ADR-0082 — OS multi-equipamento (equipamento por atividade)

**Status:** aceito (2026-06-14 — frente `os-multi-equipamento`, pré-requisito de `orcamentos`. Criada na P2; implementada nas Fatias 1a..2: rename + migrations 0018/0019/0020 + bifurcação atividade/comercial + detecção por atividade. Reviews: tech-lead TL-OSME-01..10 + consultor-rbc RBC-OSME-01..05, ambos APROVA C/ CORREÇÕES; batch Roldão D-OSME-3.)

## Contexto

A OS (ADR-0023) nasceu como container de **1 equipamento**: `OS.equipamento` FK NOT NULL,
e cada `AtividadeDaOS` herdava esse equipamento via trigger (`equipamento_id_desnormalizado`
copiado de `OS.equipamento_id`). O cenário real de assistência técnica metrológica, porém,
combina N instrumentos num único atendimento (o cliente traz 3 balanças para calibrar +
deslocamento). A decisão de produto **R-ORC-3 (Roldão, 2026-06-13)** cravou: "tanto orçamento
quanto OS devem permitir N equipamentos, cada um com seus itens, mais itens compartilhados
sem equipamento (deslocamento/taxa)". Isso contradiz o modelo de 1 equipamento e torna a OS
um **pré-requisito** do módulo `orcamentos` — sem o retrofit, o orçamento nasceria com o
contrato de evento errado.

Descoberta que torna o retrofit **cirúrgico**: o índice de concorrência metrológica
(`idx_atividade_em_execucao_por_equip`, INV-OS-CONC-001) **já chaveava pela ATIVIDADE**
(`atividade_da_os.equipamento_id_desnormalizado`), não pela OS. A infra de equipamento-por-
atividade já existia — faltava só inverter a FONTE da verdade.

## Decisão

1. **Equipamento vive na ATIVIDADE.** `equipamento_id_desnormalizado` é renomeado para
   `AtividadeDaOS.equipamento_id` (fonte própria, não cópia). `OS.equipamento` passa a
   `null=True` e fica NULL em OS multi-equipamento; `os_tenant_equip_idx` vira índice parcial
   (`WHERE equipamento_id IS NOT NULL`) — serve OS single-equipamento legada/avulsa, onde o
   campo é mantido por compatibilidade (1 equipamento distinto → preenche; >1 → NULL).
2. **Trigger forward COALESCE.** A função `atividade_da_os_concorrencia_denormalize_check`
   passa a `COALESCE(NEW.equipamento_id, OS.equipamento_id)`: preserva o equipamento do INSERT
   (item) e só cai no fallback da OS quando a atividade vem sem equipamento (compat single-equip).
   O `CREATE OR REPLACE` recompila ambas as funções PL/pgSQL — o `RENAME COLUMN` propaga ao
   índice mas NÃO ao corpo das funções (TL-OSME-01).
3. **Itens comerciais = entidade própria `ItemComercialOS`** (decisão Roldão D-OSME-3): linha
   leve (deslocamento/taxa_visita/outro) SEM equipamento e SEM `tipo_bloqueia_concorrencia`,
   nunca no índice de concorrência (INV-OSME-ITEMCOM-001); soma em `OS.valor_total`. NÃO é
   `AtividadeDaOS` (o enum técnico é fechado e a entidade carrega checklist/aceite/NC que não
   cabem numa taxa).
4. **Envelope `Orcamento.Aprovado` header→item.** `equipamento_id` migra do header para cada
   item; item com equipamento → `AtividadeSnapshot`; item sem → `ItemComercialOS`. Pré-check de
   equipamento baixado (INV-OS-EQP-001) itera todos os equipamentos distintos dos itens.
5. **Recebimento por instrumento** (consultor RBC — cl. 7.4.3/7.8.2.1): o ponteiro
   `equipamento_recebimento_id` migra de `OS` para `AtividadeDaOS` (INV-OSME-RCB-001). O
   preenchimento do vínculo recebimento→atividade depende do app `equipamentos` publicar
   `atividade_id` — fica em **GATE-OSME-RECEBIMENTO-7.5**.

## Alternativas rejeitadas

| Alternativa | Por que NÃO |
|---|---|
| **Equipamento "predominante" na OS** | Estado derivado redundante que diverge das atividades (fonte de bug de consistência); a UI agrega das atividades quando precisa. OS multi-equip = NULL é honesto (D-OSME-2). |
| **Item comercial como `AtividadeDaOS` com `equipamento_id=NULL`** | Polui o agregado técnico: `TipoAtividade` é enum fechado (sem "taxa"), e a atividade carrega checklist/aceite/NC/concorrência que não fazem sentido para deslocamento. Entidade separada é mais limpa (TL-OSME-04). |
| **Manter `equipamento_id_desnormalizado` (sem rename)** | A semântica deixou de ser "desnormalização da OS" e virou fonte; o nome mentiria (auditor-llm-correctness). Doc e teste já usavam `equipamento_id` por antecipação. |
| **DROP de `OS.equipamento_recebimento_id`** | Migration destrutiva; o campo é ponteiro denormalizado provavelmente nunca populado (seam quebrado). Depreciado em vez de dropado (não-destrutivo/reversível). |

## Consequências

### Positivas
- OS reflete a operação real (N instrumentos + custos comerciais num atendimento).
- Concorrência metrológica isola corretamente por equipamento distinto (2 equipamentos
  diferentes na mesma OS podem estar EM_EXECUCAO sem falso-412).
- Cadeia de custódia conforme: certificado → atividade → recebimento daquele instrumento.
- Retrofit aditivo e reversível (migrations relaxantes, sem perda de dado).

### Negativas (mitigáveis)
- `OSSnapshot.equipamento_id` vira `UUID | None` — propaga via mypy aos call-sites de leitura.
- A dimensão **grandeza** da matriz ADR-0041 continua não resolvida pelo índice (débito M4
  pré-existente — TL-OSME-07; não piora).
- O recebimento por instrumento é estrutura + invariante; o enforcement completo depende do
  GATE-OSME-RECEBIMENTO-7.5 (seam no app equipamentos).

## Non-goals
- NÃO resolve o seam de preenchimento do recebimento (produtor publicar `atividade_id`) — GATE.
- NÃO resolve a dimensão grandeza da matriz de concorrência ADR-0041 (débito M4).
- NÃO muda a relação OS↔Cliente (1:1) nem o enum `TipoAtividade`.
- NÃO modela faturamento por item (Wave B) — `ItemComercialOS` soma em `valor_total`.

## Invariantes (emendadas/novas — REGRAS-INEGOCIAVEIS.md)
- **INV-OS-ATIV-002** (emendada): equipamento é PRÓPRIO da atividade (não herdado da OS).
- **INV-OS-EQP-001** (emendada): bloqueio validado por equipamento de cada atividade.
- **INV-OSME-RCB-001** (nova): recebimento por instrumento (atividade); item recebido = calibrado.
- **INV-OSME-ITEMCOM-001** (nova): `ItemComercialOS` nunca tem equipamento nem entra no índice
  de concorrência.
- **INV-OS-CONC-001**: inalterada na semântica (já chaveava pela atividade).

## GATEs
- **GATE-OSME-RECEBIMENTO-7.5** — vínculo recebimento→atividade no app `equipamentos`
  (`EquipamentoRecebimento.atividade_os_id` + produtor publica `atividade_id`).
