---
adr: 0051
titulo: Propagação de ADR-0023 (OS com Atividades) aos módulos Wave A — Orçamento, Agenda, App Técnico, Contas a Receber
status: aceito
data: 2026-05-23
proposto-por: agente (Onda 9 — auditoria Wave A operacional, achados C-ORC-001, C-APP-001, C-AG-001)
revisado-por: tech-lead-saas-regulado
aceito-em: 2026-05-27
bloqueia-fase: Wave A (Marco 3 `os` + módulos consumidores)
depende-de: ADR-0023 (OS com Atividades), ADR-0027 (sync mobile merge por atividade), ADR-0029 (canonicalização texto probatório)
---

# ADR-0051 — Propagação de ADR-0023 aos módulos Wave A

## Contexto

ADR-0023 estabeleceu que **1 OS contém N `AtividadeDaOS`** (cada uma com tipo + checklist + estado próprios). Sem propagação aos módulos consumidores, o modelo da OS vira inconsistente com o resto da Wave A:

- **Orçamento** ainda mapeia `ItemOrcamento` para "OS inteira" — caso combinado (manutenção + calibração) força 2 orçamentos.
- **Agenda** ainda agenda `EventoAgenda.os_id` — não permite janelas distintas por atividade (calibração em laboratório vs manutenção em campo).
- **App Técnico** mostra OS como bloco único — técnico executa checklist único, não consegue concluir atividade A sem atividade B.
- **Contas a Receber** ainda factura "valor da OS" — não permite faturamento parcial por atividade concluída (cenário: manutenção entrega antes da calibração).

## Decisão

### 1. Orçamento (C-ORC-001)

`ItemOrcamento` ganha campo opcional `tipo_atividade_alvo` (enum: `calibracao | manutencao | instalacao | verificacao_inmetro | vistoria | OUTRO`). Aprovação de orçamento gera **1 OS com N AtividadeDaOS** (1:1 com itens marcados como atividade alvo).

- Itens sem `tipo_atividade_alvo` viram linhas comerciais da OS mas não geram atividade (ex: deslocamento, taxa de visita).
- Caso combinado: orçamento com 1 item `tipo_atividade_alvo=manutencao` + 1 item `tipo_atividade_alvo=calibracao` → 1 OS com 2 atividades.

### 2. Agenda (C-AG-001)

`EventoAgenda.os_id` é substituído por `EventoAgenda.atividade_id` (FK para `AtividadeDaOS`). `EventoAgenda.os_id` continua como campo **derivado** (denormalização cacheada — `atividade.os_id`).

- Cada atividade da OS pode ter janela própria.
- Detecção de conflito continua valendo (por técnico × janela).
- Migração de eventos legados pré-Marco 3 não se aplica (não há legado).

### 3. App Técnico (C-APP-001)

`ServicoExecutado`, `ConsumoPeca`, `Foto`, `Checklist`, `AssinaturaAceite` deixam de ser filhos diretos de `OS` e passam a ser filhos de `AtividadeDaOS`. Cada um carrega FK `atividade_id` (NOT NULL).

- Checklist é por atividade — tipo manutenção tem checklist próprio, tipo calibração tem outro.
- Conclusão de atividade gera evento `AtividadeDaOS.Concluida` (consumido por agenda, contas-receber, sync).
- OS só fecha quando **todas** atividades estão em estados terminais (ver ADR-0023 máquina de estados).

### 4. AssinaturaAceite + canonicalização (C-APP-002)

`AssinaturaAceite` ganha campo `corpo_canonico_hash` (SHA-256 do texto canonicalizado conforme ADR-0029, função `canonicalizar_texto_termo`). Conteúdo do termo é por atividade (texto distinto para manutenção vs calibração).

### 5. Sync mobile (já coberto por ADR-0027)

Merge por `atividade_id` (LWW) — reuso direto de ADR-0027.

### 6. Contas a Receber

`Fatura.itens[]` aceita referência a `atividade_id` (não só `os_id`). Permite faturamento parcial de OS combinada. Quando última atividade é concluída e fatura emitida, máquina de estados da OS transita para `FATURADA`.

## Consequências

**Positivas:**
- Caso combinado (manutenção + calibração) deixa de ser hack (2 OS) ou perda de checklist (1 tipo dominante).
- Faturamento parcial por atividade vira possível (cliente paga manutenção antes da calibração ficar pronta).
- Agenda multi-técnico real: atividades distintas da mesma OS atribuídas a técnicos diferentes em janelas diferentes.

**Negativas:**
- Migração de schema considerável (cinco entidades ganham `atividade_id`) — Wave A Marco 3 absorve antes de gerar dados.
- App técnico exige redesign de tela "OS em execução" (lista de atividades, não bloco único).
- Eventos cresceram: `AtividadeDaOS.Iniciada`, `AtividadeDaOS.Concluida`, `AtividadeDaOS.Bloqueada` (consumers ajustam).

## Invariantes derivadas

- **INV-APP-ADR0023-001** — `ServicoExecutado`, `ConsumoPeca`, `Foto`, `Checklist`, `AssinaturaAceite` exigem `atividade_id NOT NULL` (FK para `AtividadeDaOS`). Hook valida.
- **INV-AG-ADR0023-001** — `EventoAgenda.atividade_id NOT NULL` quando `tipo=os`. `os_id` é derivado.
- **INV-APP-CANON-001** — `AssinaturaAceite.corpo_canonico_hash` calculado via `canonicalizar_texto_termo` (ADR-0029).

## Non-goals

- Faturamento por atividade sem que OS contenha múltiplas atividades — irrelevante (OS com 1 atividade fatura tudo de uma vez).
- Atribuir atividade da mesma OS a tenants diferentes — proibido (atividade herda `tenant_id` da OS).

## Referências

- ADR-0023 (OS com Atividades), ADR-0027 (sync mobile), ADR-0029 (canonicalização texto probatório).
- Achados Onda 9: C-ORC-001, C-APP-001, C-APP-002, C-AG-001.
