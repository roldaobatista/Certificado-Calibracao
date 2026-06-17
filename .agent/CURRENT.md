# .agent/CURRENT.md

> ≤40 linhas curtas. Histórico detalhado em `docs/faseamento/diario/`. Contagens vivas: `docs/governanca/STATUS-GERADO.md`.

**Modo:** AUTÔNOMO. **Fase:** Wave A em curso.

## FILA DE FRENTES — ordem de dependência CRAVADA (Roldão 2026-06-16: "todos em sequência de dependência, não perguntar")

Receita fechada (config→pps→precificacao→colaboradores→orcamentos→contas-receber). Faltantes Wave A (topo-sort do `plano-dependencia-sistema.md`; deps já construídas; **seguir em ordem, sem perguntar**):

1. **`caixa-tecnico`** (N5) ← EM CURSO/PRÓXIMO — destrava app-tecnico/despesas/custeio-real.
2. **`chamados`** (N5) — entrada de demanda → vira OS. Dep: clientes(✓)+os(✓).
3. **`contas-pagar`** (N5) — par do CR; destrava despesas (precisa cadastro fornecedor mínimo).
4. **`estoque`** (N3, atrasado) — pré-req de app-tecnico/custeio-real. Dep: pps(✓)+os(✓)+equipamentos(✓).
5. **`frota`** (N4) · **`treinamentos`** (N3) · **`seguranca-trabalho`** (N3) — suporte; dep colaboradores/equipamentos (✓).
6. **N6:** `comissoes` (gatilha por recebimento ✓) → `despesas` → `app-tecnico` → `contabilidade-export`.
7. **N7+:** `fornecedores` → `crm` → `contratos` → `qualidade` → `custeio-real` (fecha stub precificacao) → níveis 8–10.

**DIFERIDOS (bloqueio externo — só quando Roldão liberar credencial/serviço):** `certificados-digitais` (Lacuna Web PKI/A3),
`comunicacao-omnichannel` (SMS/WhatsApp/e-mail real), `billing-saas` (gateway+fiscal reais), `integracoes-externas` (OAuth).

- **Para o Roldão (quando ativar e-mail real do CR):** criar `.env` com `EMAIL_HOST`/`EMAIL_HOST_USER`/
  `EMAIL_HOST_PASSWORD`/`DEFAULT_FROM_EMAIL` (SMTP). Hoje modo teste (não envia). Disparo a PF real só após GATE-LGPD-RAT.

## Última frente FECHADA — `agenda` MÓDULO 100% Wave A (2026-06-17)

- Fatias 1a..3d + P8 (matriz) + P9 (lgpd PASS + 6 MÉDIO consertados na causa-raiz; 2ª passada 6 PASS, sem novo MÉDIO+).
  **179 testes** (era 173). Sem ADR nova (D-AGE-15 já em P3). Detalhe + GATEs: `docs/faseamento/agenda/matriz-reconciliacao.md` §5/§8.
- **GATE-AGE-RT-WIRING aberto** — US-AG-014 saiu **predicado-only** (`rt_port` não invocado; 412 `SemRTNoSlot` nunca disparado;
  advisory por D-AGE-6). **DECISÃO ROLDÃO PENDENTE:** wirar 412 fail-closed perfil A no Wave A ou diferir. +GATEs: NO-SHOW-AGENDA, RTSUBSTITUICAO-FORMAL, COLABORADOR-REFERENCIADO.
- **`contas-receber`** fechou antes (2026-06-16, ADR-0084; bus FAN-OUT [[fan-out-bus-consumers-os-concluida]]). [[estado-do-projeto-wave-a-em-curso]].

## Pendência de produto aberta

Terminologia B/C/D do M6 — veto item-a-item do Roldão pendente (cl. 8.1.3 "capacidade interna declarada").

## Ponteiros

- Contagens: `docs/governanca/STATUS-GERADO.md` · ADRs: `docs/adr/INDICE.md` · matriz: `docs/faseamento/orcamentos/matriz-reconciliacao.md`
- Proibido commit isolado de CURRENT.md — handoff entra no commit da fatia (R16).
