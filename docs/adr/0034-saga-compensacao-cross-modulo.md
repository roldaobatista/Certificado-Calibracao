---
adr: 0034
titulo: Saga + compensação cross-módulo (Orquestrada vs Coreografia)
owner: roldao
revisado-em: 2026-05-22
status: proposta
proposto-por: agente (auditoria projeto-inteiro 10 lentes — Onda 1 transversal, C-INT-03)
revisado-por: tech-lead-saas-regulado
bloqueia-fase: Wave A Marco 3 (`os`) — primeira saga real Orçamento→OS→Cert→NF→CR
depende-de: ADR-0033 (idempotência consumer), ADR-0015 (lifecycle), ADR-0014 (transições regulatórias)
---

# ADR-0034 — Saga + compensação cross-módulo

## O QUE

Cravar **padrão único** de orquestração de fluxos cross-módulo que não cabem em 1 evento:

1. **Saga Orquestrada** (Process Manager) é o padrão default no Aferê.
2. **Coreografia** (eventos puros sem orquestrador) é exceção justificada por ADR.
3. Toda saga tem mapa explícito `passo → evento → handler → compensação → dono` em `docs/comum/sagas-cross-modulo.md`.

## PORQUE

- Auditoria Onda 1 detectou C-INT-03: 4 sagas críticas sem mapa formal (Orçamento→OS→Cert→NF→CR; Cancelamento cert pós-NF; M&A cliente com OS aberta; Suspensão tenant com NFs em vôo).
- Coreografia pura escala mal: bug em handler N gera cascata muda. Sem orquestrador, não há ponto único para auditar o estado da saga.
- ADR-0015 fluxo 1 já adotou state machine para provisioning — generalizar.

## COMO

### Decisão: Orquestrada como default

- Saga vive em tabela `<dominio>_saga_<nome>` com colunas:
  - `id uuid PK`, `tipo_saga varchar(80)`, `estado varchar(40)`, `dados jsonb`, `tenant_id uuid`, `correlation_id uuid`, `criada_em`, `atualizada_em`, `concluida_em`, `falhou_em`, `motivo_falha text`.
- Cada saga implementa **state machine não-reversível** — transição inválida levanta exceção (cravado em código + trigger PG quando crítico).
- Orquestrador é módulo dono da saga (não módulo "automacoes-bpm" genérico em Wave A; pode migrar para BPM Wave B).
- Cada passo é consumer de evento (ADR-0033) — compensação é publicação de evento inverso.

### Exemplo (Saga 1 — Orçamento→OS→Cert→NF→CR)

| Passo | Evento gatilho | Handler/efeito | Compensação | Dono |
|---|---|---|---|---|
| 1 | `Orcamento.Aprovado` | cria OS rascunho | `OS.Cancelada` | `comercial/orcamentos` |
| 2 | `OS.Concluida` | dispara emissão certificado | `Certificado.NaoEmitir` | `operacao/os` |
| 3 | `Certificado.Emitido` | dispara NF-e | `Certificado.Revogado` | `metrologia/certificados` |
| 4 | `Fiscal.NFSeEmitida` | abre conta a receber | `NotaFiscal.CartaCorrecao` ou `NotaFiscal.Cancelada` | `fiscal` |
| 5 | `ContasReceber.Pago` | fecha saga `concluida` | n/a (terminal) | `financeiro/contas-receber` |

### Compensação — princípios

1. **Append-only** — compensação **nunca** apaga o passo anterior. Cria evento inverso ou marca registro como "compensado".
2. **Justificativa obrigatória** — toda compensação carrega texto ≥30 chars em `motivo_compensacao` (auditável).
3. **Janela** — fluxo regulatório (NF-e, certificado) tem **janela curta** (24h pós-emissão) para compensação leve (CC-e); fora da janela, exige fluxo formal (cancelamento + carta + audit).
4. **Saga falha não-recuperável** publica evento `<Saga>.Falhou` → dispatcher humano (admin Aferê).

### Ordem garantida cross-módulo (Onda 1 médio — saga PlanoMudouModulos)

Para fluxos com efeito em cascata, ADR explicita ordem:

**`BillingSaas.PlanoMudouModulos`:**
1. `billing-saas` publica (origem) e marca saga `aguardando_authz`.
2. `acesso-seguranca` consome → invalida sessões e cache → publica `AcessoSeguranca.SessoesAjustadas`.
3. `feature-flags` consome → atualiza `tenant_features` → publica `Features.Sincronizado`.
4. Módulos consumidores (calibracao, fiscal, etc.) consomem `Features.Sincronizado` (não o `PlanoMudouModulos` direto) → atualizam funcionalidades visíveis.
5. Fail-loud: se passo 3 não confirmar em 5 min → alerta P1; saga vai para `dead_letter_events` se 5 retries esgotarem.

## ID

- **INV-SAGA-001** — toda saga cross-módulo tem tabela persistente `<dominio>_saga_<nome>` com state machine declarada (`docs/comum/sagas-cross-modulo.md`). Coreografia pura sem orquestrador exige ADR-irmã justificando.
- **INV-SAGA-002** — compensação é **publicação de evento**, nunca DELETE/UPDATE retroativo no passo anterior (WORM regulatório preservado).
- **INV-SAGA-003** — compensação fora da janela (>24h) **proibida** em fluxo regulatório (NF-e cancelada, cert revogado) sem assinatura A3 + audit imutável + justificativa ≥30 chars.
- **INV-SAGA-004** — saga sem terminal (`concluida` ou `falhou`) em 24h dispara alerta P1 (saga zumbi).

## NON-GOAL

- **Não** implementa engine BPMN/BPEL — saga é código Python (state machine em models) + ADR-0005 (Camada 2 templates) quando aplicar.
- **Não** garante distributed transaction (2PC). Eventual consistency assumida; ADR-0033 cobre at-least-once.
- **Não** substitui retry de procrastinate — saga **usa** retry/dead-letter da ADR-0033.

## Consequências

**Boas:** auditor de produto/segurança consegue auditar saga ponto a ponto; compensação tem janela explícita; ordem garantida resolve gap "BillingSaas → módulos consumidores" detectado na auditoria.

**Ruins:** boilerplate em cada saga (tabela + state machine); custo manutenção quando saga cresce >10 passos (avaliar split).

## Referências cruzadas

- `docs/comum/sagas-cross-modulo.md` — mapa das 4 sagas críticas
- ADR-0033 (idempotência + dead-letter — base)
- ADR-0015 (lifecycle tenant — saga 1 já em produção)
- ADR-0035 (tenant suspenso — saga "NFs em vôo" entra lá)
