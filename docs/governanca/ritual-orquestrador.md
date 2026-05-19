---
owner: roldao
revisado_em: 2026-05-18
proximo_review: 2026-08-18
status: stable
diataxis: how-to
audiencia: agente
relacionados:
  - .specify/memory/constitution.md
  - docs/governanca/catalogo-auditores.md
  - docs/governanca/limites-autonomia.md
  - docs/governanca/auditor-seguranca-prompt.md
  - docs/governanca/auditor-qualidade-prompt.md
  - docs/governanca/auditor-produto-prompt.md
  - .claude/agents/tech-lead-saas-regulado.md
  - .claude/agents/advogado-saas-regulado.md
  - .claude/agents/corretora-seguros-saas.md
  - .claude/agents/consultor-rbc-iso17025.md
---

# Ritual do orquestrador (runbook)

> **Pra quê:** materializar o ciclo Spec Kit + 4 subagentes + 3 auditores + 12 hooks que a Constituição §6 (IDs rastreáveis) e a decisão fundadora D1 (Spec Kit) exigem. Sem este runbook, agentes diferentes a cada sessão pulam o ciclo (foi o que aconteceu em F-A, F-B e Wave A Marco 1 — registrado em `docs/governanca/debitos-ritual.md`).
>
> **Status:** stable em 2026-05-18 após Roldão exigir orquestração de verdade.

---

## 1. Em uma frase

```
Pra cada Story: /specify → /plan → review 4 subagentes → /tasks → /implement → review 3 auditores → loop até PASS com ZERO CRÍTICO/ALTO/MÉDIO (INV-RITUAL-001).
```

---

## 2. Onde cada coisa vive

| Artefato | Caminho | Quando criar |
|---|---|---|
| PRD do módulo | `docs/dominios/<dominio>/modulos/<modulo>/prd.md` | Antes de codar o módulo |
| Stories `US-MOD-NNN` | Dentro do PRD do módulo, seção §6 | No `/specify` |
| Critérios de aceite `AC-MOD-NNN-N` | Dentro de cada Story (binário: passou/não passou) | No `/specify` |
| Plano de implementação | `docs/dominios/<dominio>/modulos/<modulo>/planos/US-MOD-NNN.md` | No `/plan` |
| Tasks `T-MOD-NNN` | `docs/dominios/<dominio>/modulos/<modulo>/tasks/US-MOD-NNN.md` | No `/tasks` |
| Pareceres de subagente | `docs/dominios/<dominio>/modulos/<modulo>/revisoes/US-MOD-NNN-<subagente>.md` | Antes de aprovar `/plan` |
| Output de auditor | `docs/governanca/trilha-auditoria-agentes.md` (append-only) | Em cada veto/PASS |
| Commit | mensagem `T-MOD-NNN: <descrição curta> (AC-MOD-NNN-N)` | Em cada `/implement` |
| Débito de ritual | `docs/governanca/debitos-ritual.md` | Quando descobrir gap retroativo |

---

## 3. Passo a passo da Story

### 3.1. /specify — escrever a Story

**Antes de fazer qualquer coisa, ler o PRD do módulo** (`docs/dominios/<dominio>/modulos/<modulo>/prd.md`). Se a Story que você pretende implementar já estiver lá (US-MOD-NNN), **use o ID existente**. Se não, propor adição ao PRD primeiro (envolve auditor de Produto).

**Cada Story tem obrigatoriamente:**

```markdown
### US-CLI-001: <título imperativo curto>
**Como** <persona>, **quero** <ação>, **para** <benefício>.

- **AC-CLI-001-1**: GIVEN <estado> WHEN <ação> THEN <resultado verificável binário>.
- **AC-CLI-001-2**: GIVEN ... WHEN ... THEN ...
- **AC-CLI-001-N**: ...

**Invariantes citadas:** INV-024, INV-TENANT-001, ...
**Dependências:** ADR-NNNN, módulo X, evento Y.
**Non-goals (esta Story NÃO faz):** ...
```

ACs **binários**: ou passa ou não passa. Não admite "parcialmente".

### 3.2. /plan — gerar plano sem código

```markdown
# Plano US-CLI-001

## Resumo (≤3 linhas)
...

## Sequência de tasks
- T-CLI-001: ...
- T-CLI-002: ...

## Modelos/tabelas envolvidos
...

## Endpoints/views envolvidos
...

## Hooks ativados (validações automáticas)
...

## Testes obrigatórios (cobrindo cada AC)
- AC-CLI-001-1: tests/test_clientes_X.py::test_NOME
- AC-CLI-001-2: ...

## Riscos / pontos sensíveis
...
```

### 3.3. Review do plano pelos 4 subagentes

**Critério de invocação por subagente** (não invoca todos sempre — só os pertinentes):

| Subagente | Quando invocar |
|---|---|
| `tech-lead-saas-regulado` | Toda Story que adiciona/altera modelo, migration, API, fluxo técnico não-trivial |
| `advogado-saas-regulado` | Story que toca LGPD (dados pessoais, consentimento, retenção, exclusão), contrato (clauses), regulatório |
| `corretora-seguros-saas` | Story que altera fluxo financeiro, exposição cyber, integração com terceiro pago, gateway de pagamento |
| `consultor-rbc-iso17025` | Story que toca certificado, padrão, RT, escopo acreditado, NIT-DICLA |

**Como invocar:** usar `Agent` tool com `subagent_type=tech-lead-saas-regulado` (ou outro), prompt incluindo a Story, ACs, plano, contexto.

**Output esperado de cada subagente:** parecer em `docs/dominios/<dominio>/modulos/<modulo>/revisoes/US-MOD-NNN-<subagente>.md` com:
- `APROVADO` | `APROVADO COM RESSALVAS: <lista>` | `REPROVADO: <motivo + correção exigida>`

**Loop:** se REPROVADO, corrige o plano e re-revisa. Limite anti-deadlock: 5 reprovações da mesma Story = Caso-limite 5.

### 3.4. /tasks — quebrar em T-MOD-NNN

Cada T-MOD-NNN tem:
- Descrição em 1 linha
- AC que cobre (T pode cobrir mais de um AC, ou um AC pode precisar de N Ts)
- Estimativa em commits (deve ser 1, raramente 2)
- Hook esperado (que validação deve passar)

### 3.5. /implement — executar

- Cada commit cita `T-MOD-NNN: <descrição>` + opcional `(AC-MOD-NNN-N)`
- Hooks rodam automático em cada commit (`block-destructive`, `secrets-scanner`, `tenant-id-validator`, `authz-check`, `anti-mascaramento`, etc — 15 ativos)
- Se hook bloquear: corrige e tenta de novo. NUNCA bypass com `--no-verify`.

### 3.6. Review pós-implementação pelos 3 auditores Família 5

**Ordem (do mais barato pro mais caro):**
1. **Auditor de Qualidade** (pre-commit): cobertura, TST-001..004
2. **Auditor de Segurança** (pre-commit): SEC-*, INV-TENANT-*
3. **Auditor de Produto** (pre-merge): ACs binários + non-goals

**Como invocar:** `Agent` tool com `subagent_type=auditor-qualidade` (ou outro). Prompt completo está em `docs/governanca/auditor-<nome>-prompt.md`.

**Output:** `PASS | CONCERNS: <lista> | FAIL: <regra violada + linha + sugestão>`. Append em `docs/governanca/trilha-auditoria-agentes.md`.

**Loop:** se FAIL, corrige e re-revisa. 5 reprovações da mesma Story = escalation.

**Gate de fechamento (INV-RITUAL-001 — inegociável):** a Fase/Marco/Story **só fecha** com os 3 auditores em **PASS** e **ZERO CRÍTICO / ZERO ALTO / ZERO MÉDIO** nas 3 lentes + pareceres dos subagentes sem REPROVADO. **MÉDIO bloqueia o fechamento igual a CRÍTICO/ALTO** — só é tolerável transitoriamente *dentro* do loop de correção, nunca no fechamento. Apenas BAIXO pode ser rastreado como GATE-* e não bloqueia. "Resolvido" exige evidência verificável (rodar o ambiente real), não suposição. Não existe "MÉDIO aceitável", "cosmético", "pré-existente" ou "diferido pra Wave A" — ver `feedback_resolver_nao_documentar`. Override exclusivo do Roldão via `# ritual-gate: skip -- APROVADO POR ROLDAO: <razão>` no commit; o agente nunca decide derrubar este gate. O hook `ritual-gate-check.sh` materializa a barreira.

---

## 4. Foundation vs Wave — diferença prática

**Foundation (F-A, F-B, F-C...)** é infraestrutura sem PRD de módulo. Stories são `US-FA-NNN` / `US-FB-NNN`:
- PRD-equivalente: seção §2 ou §3 do `docs/faseamento-foundation-waves.md` (entregáveis + critérios de saída)
- ACs: critérios de saída automáveis listados lá
- Auditores rodam só Segurança + Qualidade (não tem Produto pra Foundation — é infra)

**Wave (A, B, C)** = módulos de produto. Ritual completo.

---

## 5. Como invocar subagente / auditor (cookbook)

### Subagente especialista

```
Agent({
  description: "Review do plano US-CLI-001 pelo tech-lead",
  subagent_type: "tech-lead-saas-regulado",
  prompt: "Story em docs/dominios/comercial/modulos/clientes/prd.md §6 US-CLI-001. Plano em docs/.../planos/US-CLI-001.md. Foco da revisão: <pontos sensíveis>. Devolva parecer em formato APROVADO|REPROVADO com lista de ressalvas se houver. Salve em docs/.../revisoes/US-CLI-001-tech-lead.md"
})
```

### Auditor Família 5

```
Agent({
  description: "Auditor de Qualidade em US-CLI-001",
  subagent_type: "auditor-qualidade",
  prompt: "Story US-CLI-001 implementada. Diff: git diff main..HEAD. Cobertura: reports/coverage/index.html. Aplique docs/governanca/auditor-qualidade-prompt.md v1.0.0. Append resultado em docs/governanca/trilha-auditoria-agentes.md."
})
```

---

## 6. Sinais de que estou pulando o ritual (alerta vermelho)

- Escrevendo código sem ter aberto o PRD do módulo
- Sem ter criado Story `US-MOD-NNN`
- Sem ter invocado subagente algum
- Commit não cita `T-MOD-NNN`
- Não rodei auditor de Qualidade/Segurança/Produto antes do push
- Implementei "MVP do meu MVP" (subset da Story) sem documentar o restante
- Marquei fase/Marco/Story como FECHADA/PASS com achado MÉDIO (ou ALTO/CRÍTICO) ainda em aberto — ou rotulei MÉDIO como "aceitável/cosmético/pré-existente/diferido" (viola INV-RITUAL-001)

**Se notar qualquer sinal: PARAR. Voltar pro `/specify`.**

---

## 7. Histórico

| Data | Mudança |
|------|---------|
| 2026-05-18 | Criação após Roldão exigir "agente como orquestrador de verdade". Causa: agente entregou F-A, F-B e Wave A Marco 1 (clientes) sem seguir o ciclo. Débito retroativo em `docs/governanca/debitos-ritual.md`. |
