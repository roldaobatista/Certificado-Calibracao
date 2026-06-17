# .agent/CURRENT.md

> ≤40 linhas curtas. Histórico detalhado em `docs/faseamento/diario/`. Contagens vivas: `docs/governanca/STATUS-GERADO.md`.

**Modo:** AUTÔNOMO. **Fase:** Wave A em curso.

## FILA DE FRENTES — ordem de dependência CRAVADA (Roldão 2026-06-16: "todos em sequência de dependência, não perguntar")

Receita fechada (config→pps→precificacao→colaboradores→orcamentos→contas-receber). Fila dos faltantes Wave A
(topo-sort do `plano-dependencia-sistema.md`; cada um respeita suas deps já construídas; **seguir em ordem, sem perguntar**):

1. **`agenda`** (N5) ← EM CURSO. Fatia 1a (domínio, 69 testes) + Fatia 1b (schema PG, 28 testes; 65/65 drill estrutural; 8 migrations; EXCLUDE GIST; WORM triggers; seed feriados) CONCLUÍDAS. **PRÓXIMO = Fatia 2** (use cases + REST, T-AGE-030..038). Dep: os(✓)+colaboradores(✓).
2. **`caixa-tecnico`** (N5) — destrava app-tecnico/despesas/custeio-real.
3. **`chamados`** (N5) — entrada de demanda → vira OS. Dep: clientes(✓)+os(✓).
4. **`contas-pagar`** (N5) — par do CR; destrava despesas (precisa cadastro fornecedor mínimo).
5. **`estoque`** (N3, atrasado) — pré-req de app-tecnico/custeio-real. Dep: pps(✓)+os(✓)+equipamentos(✓).
6. **`frota`** (N4) · **`treinamentos`** (N3) · **`seguranca-trabalho`** (N3) — suporte; dep colaboradores/equipamentos (✓).
7. **N6:** `comissoes` (gatilha por recebimento ✓) → `despesas` → `app-tecnico` → `contabilidade-export`.
8. **N7+:** `fornecedores` → `crm` → `contratos` → `qualidade` → `custeio-real` (fecha stub precificacao) → níveis 8–10.

**DIFERIDOS (bloqueio externo — só quando Roldão liberar credencial/serviço):** `certificados-digitais` (Lacuna Web PKI/A3),
`comunicacao-omnichannel` (SMS/WhatsApp/e-mail real), `billing-saas` (gateway+fiscal reais), `integracoes-externas` (OAuth).

- **Para o Roldão (quando ativar e-mail real do CR):** criar `.env` com `EMAIL_HOST`/`EMAIL_HOST_USER`/
  `EMAIL_HOST_PASSWORD`/`DEFAULT_FROM_EMAIL` (SMTP). Hoje modo teste (não envia). Disparo a PF real só após GATE-LGPD-RAT.

## Última frente FECHADA — `contas-receber` MÓDULO 100% Wave A (2026-06-16)

- Fatias 1a..3d + P8 (ADR-0084) + P9 (7 PASS + 1 MÉDIO idempotência consertado). Gatilho `os.concluida`; bus FAN-OUT
  [[fan-out-bus-consumers-os-concluida]]. Detalhe completo + débitos Wave B: `docs/faseamento/contas-receber/` (matriz §8) + diário.
- **`orcamentos`** fechou antes (2026-06-15, ADR-0083). [[estado-do-projeto-wave-a-em-curso]].

## Pendência de produto aberta

Terminologia B/C/D do M6 — veto item-a-item do Roldão pendente (cl. 8.1.3 "capacidade interna declarada").

## Ponteiros

- Contagens: `docs/governanca/STATUS-GERADO.md` · ADRs: `docs/adr/INDICE.md` · matriz: `docs/faseamento/orcamentos/matriz-reconciliacao.md`
- Proibido commit isolado de CURRENT.md — handoff entra no commit da fatia (R16).
