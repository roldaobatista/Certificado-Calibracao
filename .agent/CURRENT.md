# .agent/CURRENT.md

> ≤40 linhas curtas. Histórico detalhado em `docs/faseamento/diario/`. Contagens vivas: `docs/governanca/STATUS-GERADO.md`.

**Modo:** AUTÔNOMO. **Fase:** Wave A em curso.

## FILA DE FRENTES — ordem de dependência CRAVADA (Roldão 2026-06-16: "todos em sequência de dependência, não perguntar")

Receita fechada (config→pps→precificacao→colaboradores→orcamentos→contas-receber). Fila dos faltantes Wave A
(topo-sort do `plano-dependencia-sistema.md`; cada um respeita suas deps já construídas; **seguir em ordem, sem perguntar**):

1. **`agenda`** (N5) ← PRÓXIMA. OS já tem gancho fail-open lazy esperando (atribuição de técnico); valida INV-020 (Lei 13.103). Dep: os(✓)+colaboradores(✓).
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

- Fatias 1a..3d + P8 (ADR-0084) + P9 (auditores: 7 PASS + 1 MÉDIO idempotência consertado — `UniqueConstraint`
  `gateway_event_id`/migration 0008; 2ª passada RESOLVIDO). Commits `79bf494`/`227c522`/`853f12c`/`671194f`/`aae7f08`/
  `d0eac7d`/`4f0f05f` (+conserto P9). Detalhe: `docs/faseamento/contas-receber/` + matriz §8 + diário. Gatilho =
  `os.concluida`; bus FAN-OUT [[fan-out-bus-consumers-os-concluida]]; INV-FIN-* no mestre; 3 hooks novos.
- **Débitos rastreados (Wave B / re-review):** desbloqueio SEM grace (assimetria c/ adapter 3b); snapshot webhook =
  valor_original (sem juros); desconto-pontualidade pré-venc sem fórmula; isolamento por-consumer do bus; GATE-CR-REPROVA-PAGA
  + GATE-CR-OBS-OS-SEM-CERT (ADR-0084); A3 real override (GATE-CR-A3); Asaas real (GATE-CR-ASAAS).
- **`orcamentos`** fechou antes (2026-06-15, ADR-0083). Detalhe no diário + [[estado-do-projeto-wave-a-em-curso]].

## Pendência de produto aberta

Terminologia B/C/D do M6 — veto item-a-item do Roldão pendente (cl. 8.1.3 "capacidade interna declarada").

## Ponteiros

- Contagens: `docs/governanca/STATUS-GERADO.md` · ADRs: `docs/adr/INDICE.md` · matriz: `docs/faseamento/orcamentos/matriz-reconciliacao.md`
- Proibido commit isolado de CURRENT.md — handoff entra no commit da fatia (R16).
