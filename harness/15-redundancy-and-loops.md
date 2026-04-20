# 15 — Redundância, loops e auto-consistência

> **P0-11**: formaliza onde o harness exige **múltiplas execuções** ou **dupla checagem** para reduzir risco de falha silenciosa. "Passou uma vez" não basta em área regulatória.

## Racional

Em domínio regulado, um teste que passa uma vez pode estar escondendo:
- *Flakiness* (race conditions, dependência de ordem).
- Seed específico que esconde um bug de propriedade.
- Decisão regulatória que parece certa mas depende do contexto apresentado.
- Modelo de LLM com output estocástico em área onde determinismo é crítico.

A resposta não é "rodar tudo 10×". É aplicar redundância **onde o custo de erro é alto** — especificamente onde o falso-negativo gera dívida regulatória.

---

## 1. Property-based testing com N por criticidade

**Regra**: toda propriedade em `evals/sync-simulator/properties/`, `evals/regulatory/` ou `packages/engine-uncertainty/` roda N seeds, não 1.

| Criticidade do REQ | N (seeds) | Quando roda |
|---------------------|-----------|-------------|
| blocker (regra de §9) | **500** | CI por PR + noturno |
| high (AC §13 não-blocker) | 100 | CI por PR |
| medium (comportamento esperado) | 50 | CI por PR |
| low (utilitários, formatação) | 10 | CI por PR |

- Seeds **canônicos** (lista fixa) sempre rodam — garante reprodutibilidade.
- Seeds **aleatórios** preenchem o resto do N por execução.
- Falha em qualquer seed: trace arquivado em `evals/.../reports/<seed>.trace`, CI bloqueia.

### Configuração
`evals/property-config.yaml`:
```yaml
- req: REQ-§9.3-BLOCK-PADRAO-VENCIDO
  criticality: blocker
  N: 500
  canonical_seeds: [0xdeadbeef, 0xcafebabe, 0x13579bdf]
```

---

## 2. Flake gate (10× noturno)

**Regra**: teste que passa uma vez no CI roda **10× em pipeline noturno**. Se falhar 1 vez em 10, é *flaky* e bloqueia release até investigação.

- Cobertura inicial: `evals/regulatory/`, `evals/tenancy/`, `evals/sync-simulator/`, suite de integração `apps/api`.
- Falha transiente (timeout de rede, dependência externa) marcada manualmente como *infra* pelo `qa-acceptance`; não conta como flake real.
- Flake > 0% em área blocker = issue prioritária com SLA 48h.
- Registro em `compliance/validation-dossier/flake-log/YYYY-MM-DD.yaml`.

**Por que 10×** (não 100×): trade-off de custo vs sensibilidade. Probabilidade de detectar um flake de 10% com 10 runs ≈ 65%; de 5% ≈ 40%. Suficiente como triagem noturna; mais runs ficam em análise dedicada.

---

## 3. Dupla checagem regulatória

**Regra**: decisão do `regulator` em área blocker (§9 do PRD ou pacote normativo novo) roda **2× com contextos distintos**, e resultados são comparados.

### Passagem A
- Contexto: spec + AC + código atual.
- `regulator` interpreta: esta mudança viola alguma regra?

### Passagem B
- Contexto: spec + AC + **pacote normativo anexado explicitamente** (DOQ, NIT, ILAC relevantes).
- Mesma pergunta, contexto independente.

### Comparação
- Resultado igual → registra ambas as análises, segue.
- Resultado divergente → **gatilho D8 em `12-escalation-matrix.md`** (escalation automática).
- Divergência persistente em mais de 1 caso da mesma norma → sinal de ambiguidade do pacote normativo; abre PR em `compliance/normative-packages/drafts/`.

### Quando aplicar
- Toda mudança em `packages/normative-rules/**`.
- Toda nova regra de bloqueio em `apps/api/src/domain/emission/**`.
- Toda interpretação normativa inédita (nova norma, versão nova, caso não visto antes).

**Quando NÃO aplicar** (custo > benefício):
- Aplicação mecânica de regra já validada (CI passa, cenário já coberto em `evals/regulatory/`).
- Refactor sem mudança de comportamento.

---

## 4. Self-consistency em interpretação normativa nova

**Regra**: quando `regulator` interpreta norma pela **primeira vez** (caso sem precedente no repositório), roda a mesma interpretação **3× com temperatura 0** e varia apenas a ordem do contexto.

- 3 respostas idênticas → interpretação consolidada; grava em `compliance/regulator-decisions/<norma>-<caso>.md`.
- Divergência → escalation (D8) + exige revisor humano (`regulator` humano do time) antes de consolidar.
- Decisão consolidada vira precedente — próximas aplicações do mesmo caso consultam o registro em vez de re-interpretar.

**Custo controlado**: self-consistency só na primeira interpretação. A 2ª, 3ª, Nª consulta ao mesmo caso lê o registro (O(1)).

---

## 5. Dupla leitura em code review de área blocker

**Regra**: PR que toca áreas críticas (mesma lista de §14/L4) exige review de **2 agentes**, não 1:
- Agente dono do path (obrigatório).
- Agente adjacente (ex.: mudança em `engine-uncertainty` exige review de `regulator` + `metrology-calc`).

Lista adjacente:
| Path tocado | Review adicional obrigatório |
|-------------|------------------------------|
| `apps/api/src/domain/emission/**` | `regulator` + `metrology-calc` |
| `packages/engine-uncertainty/**` | `regulator` |
| `packages/normative-rules/**` | `metrology-calc` + `qa-acceptance` |
| `packages/audit-log/**` | `lgpd-security` |
| `packages/db/**` quando toca multi-tenant | `lgpd-security` |

`product-governance` valida que as duas reviews existem antes de liberar merge.

---

## 6. O que NÃO é loop de 10×

Não aplicar redundância mecânica em:
- Lint estático.
- Typecheck.
- Build.
- Aplicação de regra determinística já validada.
- Code formatting.

Custo de redundância precisa corresponder a risco. Em área determinística, 1 execução basta.

---

## 7. Orçamento da redundância

Redundância consome tokens/custo. Caps em `11-budgets.md` aplicam:
- N=500 para blocker é ~80k tokens por suite completa. Dentro do cap por PR (500k).
- Flake gate noturno tem budget próprio (job agendado, $3/noite).
- Dupla checagem regulatória: +15% sobre custo base de uma task. Aceito.
- Self-consistency 3× só na primeira interpretação: amortizado em precedentes.

Revisão trimestral em `adr/<n>-redundancy-budget.md` ajusta Ns com base em dado real (falhas detectadas / custo).

---

## 8. Relação com `12-escalation-matrix.md`

- D8 novo: **dupla checagem regulatória divergiu** — ver matriz.
- Gatilho automático de escalation sem esperar humano abrir.
- SLA igual ao D1 (24h consenso, 48h total).

## 9. Relação com `14-verification-cascade.md`

- Property tests e flake gate entram no L4 (integração).
- Dupla checagem regulatória entra no L1 (spec review) e L4.
- Self-consistency entra no L0 (épico) quando o épico cita norma nova.

## 10. Implementação bootstrap

Primeira fatia funcional em 2026-04-20:

- `evals/property-config.yaml` declara a propriedade RLS atual com `N: 500` e seeds canônicos.
- `tools/redundancy-check.ts` valida N mínimo por criticidade, seeds canônicos, vínculo com o dossiê e artefatos de flake/regulator decisions.
- `.github/workflows/nightly-flake-gate.yml` roda a suite sentinela de tenancy 10x em pipeline noturno.
- `compliance/validation-dossier/flake-log/` é o registro canônico de flakes.
- `compliance/regulator-decisions/` é o registro canônico de precedentes e self-consistency.
- `pnpm redundancy-check:plan` lista dupla checagem regulatória e reviews adjacentes por path alterado.
- `.claude/hooks/redundancy-check.sh` roda o gate no pre-commit canônico quando arquivos P0-11 entram no delta.

Pendências honestas:

- Classificação automática `flake` vs `infra`.
- Traces automáticos por seed em `evals/**/reports/`.
- Branch protection real para exigir os reviews adjacentes no GitHub.
- Execução automatizada da self-consistency 3x pelo agente `regulator`.
