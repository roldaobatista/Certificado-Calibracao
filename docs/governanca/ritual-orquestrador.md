---
owner: roldao
revisado_em: 2026-06-12
proximo_review: 2026-09-12
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
Pra cada Story: /specify → /plan → review 4 subagentes (lista defeitos de domínio candidatos) → /tasks
→ /implement EM FATIAS de ~20-25 tarefas (INV-RITUAL-002), cada fatia com mini-revisão dos auditores
   pertinentes (INV-RITUAL-003: 6 essenciais sempre + roteados por área, falha-aberto)
→ passada completa dos 10 auditores + suite completa como veredito de fechamento
→ loop até PASS com ZERO CRÍTICO/ALTO/MÉDIO (INV-RITUAL-001).
```

> **Atualizado 2026-05-29** (auditoria da máquina de dev — decisões do Roldão): fatiamento obrigatório (INV-RITUAL-002), roteamento de auditores por risco com travas (INV-RITUAL-003), e revisão profunda do plano reforçada. INV-RITUAL-001 (MÉDIO bloqueia fechamento) **mantido intacto** por decisão do Roldão.
>
> **Atualizado 2026-06-12** (auditoria de cerimônia do processo — aprovação integral Roldão): emendas R5/R6/R7/R8/R10/R20/R21/R22 incorporadas. Ver §7 Histórico.

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
- **Obrigatório (reforço 2026-05-29):** cada subagente lista explicitamente os **defeitos de domínio candidatos** que a implementação tende a cometer (ex: "hash de PII sem salt", "evento sem proteção anti-duplo-clique", "incerteza sem versão de motor"). Esta etapa é a de **maior proteção pelo menor custo** — pegou 3 erros metrológicos do M5 e uma funcionalidade-fantasma antes de uma linha de código. Os defeitos listados viram itens de checagem nas mini-revisões de fatia (§3.6).

**Loop:** se REPROVADO, corrige o plano e re-revisa. Limite anti-deadlock: 5 reprovações da mesma Story = Caso-limite 5.

### 3.4. /tasks — quebrar em T-MOD-NNN

Cada T-MOD-NNN tem:
- Descrição em 1 linha
- AC que cobre (T pode cobrir mais de um AC, ou um AC pode precisar de N Ts)
- Estimativa em commits (deve ser 1, raramente 2)
- Hook esperado (que validação deve passar)

### 3.5. /implement — executar EM FATIAS (INV-RITUAL-002)

- **Fatie o Marco em blocos de ~20-25 tarefas** que cabem numa sessão e fecham um incremento auditável (ex: M5 P1 domínio puro → P2 schema+RLS → P3 use cases → P4 porta → P5 REST…). **Proibido** o lote único de 130-160 tarefas.
- Cada commit cita `T-MOD-NNN: <descrição>` + opcional `(AC-MOD-NNN-N)`.
- Hooks rodam automático em cada commit (55 ativos — ver `docs/governanca/STATUS-GERADO.md` pra contagem viva). Se hook bloquear: corrige e tenta de novo. NUNCA bypass com `--no-verify`.
- **Ao fim de CADA fatia:** mini-revisão dos auditores pertinentes àquela camada (§3.6) — pega o defeito cedo, sobre ~20 tarefas, com causa-raiz rastreável. Não espere o módulo inteiro.

### 3.6. Review pós-implementação — auditores Família 5 ROTEADOS por risco (INV-RITUAL-003)

**Os 6 auditores ESSENCIAIS rodam SEMPRE em qualquer mudança de código** (do mais barato pro mais caro):
1. **Auditor de Qualidade** — cobertura, TST-001..004
2. **Auditor de Segurança** — SEC-*, INV-TENANT-*
3. **Auditor de LLM-correctness** — docstring que mente, `Any` de escape, código órfão de US/AC
4. **Auditor de Idempotência** — POST crítico / consumer sem proteção de replay (anti-duplo-clique)
5. **Auditor de Conformidade-LGPD** — PII sem base legal, migration PII sem hash+eliminação
6. **Auditor de Produto** (pre-merge) — ACs binários + non-goals

**Os demais rodam SÓ se o diff toca a área deles (roteador FALHA-ABERTO — na dúvida, RODA):**
- **Performance** — se toca `views.py`/`services.py`/`use_cases.py`/`domain` (N+1, timeout, rate-limit)
- **Supply-chain** — se toca `pyproject.toml`/`poetry.lock`/`Dockerfile`/`.github/workflows`
- **Observabilidade** — se toca `financeiro`/`auth`/`authz`/`tenant`/`kms`/`audit`/`views.py`
- **Drift-docs** — se toca docs de status/contagem (parte numérica já coberta por `scripts/status-projeto.sh --check`; o auditor foca no **semântico**: decisão em estado errado, frase que afirma "pronto" sobre código que não entrega)

**Travas (inegociáveis):**
- Pular auditor só por **extensão inerte** (`.md`, template de tela) — **nunca por código**.
- Na dúvida sobre a área, RODA (falha-aberto). Roteador que cala um auditor que devia rodar = vetor do bug fundador.
- **Roteamento ✅ VALIDADO e ATIVO (2026-05-29)** — evidência em `docs/governanca/validacao-roteador-auditores.md` (100% dos roteados com achado real em M3/M4 seriam disparados; 6 essenciais pegaram 100% dos CRÍTICOs). Re-validar quando surgir tipo de módulo de forma diferente (ex: só-infra/fila).

**Mini-revisão por fatia (§3.5):** ao fim de cada fatia, rodar só os essenciais + os roteados pela camada daquela fatia. A **passada completa dos 10 + suite completa** é o veredito de fechamento do Marco (não se pula).

**Na re-revisão (2ª passada — emenda R5 2026-06-12 — auditoria de cerimônia):** re-rodar SOMENTE os auditores que tiveram achado MÉDIO+, escopados ao diff do conserto. PROIBIDA "passada de confirmação" adicional após a re-passada (M5 gastou 4h numa 2ª passada completa que achou ZERO). Full re-run só se o conserto adicionou código novo substancial (nova feature/endpoint — não correção pontual de causa-raiz).

**Como invocar:** `Agent` tool com `subagent_type=auditor-<nome>`. Prompt completo em `docs/governanca/auditor-<nome>-prompt.md`.

**Output:** `PASS | CONCERNS: <lista> | FAIL: <regra violada + linha + sugestão>`. Registrar no consolidado por-módulo (`docs/faseamento/<marco>/auditoria-familia5.md`).

**Loop:** se FAIL, corrige e re-revisa. 5 reprovações da mesma Story = escalation.

**Verificação adversarial obrigatória (emenda R6 2026-06-12 — auditoria de cerimônia):** ANTES de iniciar o mutirão de conserto, todo achado MÉDIO+ da 1ª passada passa por 1 verificador cético independente. Prompt padrão: "tente REFUTAR este achado com evidência no código — cite arquivo, linha e argumento". Achado refutado é rebaixado/descartado com registro na matriz §8 (ata do P9). Padrão observado em M8: 4 de 5 MÉDIOs foram rebaixados/descartados na adversarial, poupando 4h de mutirão desnecessário. Agora é praxe obrigatória.

**Roteamento e aposentadorias formais (emenda R7 2026-06-12 — auditoria de cerimônia):**
- `auditor-drift-docs` SAI da lista de auditores de fechamento. Substituído por: (a) gate mecânico `scripts/status-projeto.sh --check` (contagens + status) + (b) varredura SEMÂNTICA mensal autônoma (pendência stale, ADR proposta já superada, draft fossilizado, link quebrado, frase que afirma "pronto" sobre código que não entrega). Evidência: 32 achados históricos, 0 bugs de produto.
- `auditor-supplychain` roda APENAS quando o diff da frente toca `pyproject.toml`, `poetry.lock`, `package*.json`, `Dockerfile`, `.github/workflows/**`. Fora disso: NÃO roda no fechamento. Evidência: 0 achados MÉDIO+ em toda a história.
- `auditor-conformidade-lgpd` roda APENAS quando o diff toca `models.py`, `serializers.py`, `migrations/**` ou `src/domain/**` com campo de pessoa física, ou eventos com payload de pessoa (PII). Fora disso: NÃO roda no fechamento. Formaliza a prática observada de M6 a M9.

**Gate de fechamento (INV-RITUAL-001 — inegociável):** a Fase/Marco/Story **só fecha** com os 3 auditores em **PASS** e **ZERO CRÍTICO / ZERO ALTO / ZERO MÉDIO** nas 3 lentes + pareceres dos subagentes sem REPROVADO. **MÉDIO bloqueia o fechamento igual a CRÍTICO/ALTO** — só é tolerável transitoriamente *dentro* do loop de correção, nunca no fechamento. Apenas BAIXO pode ser rastreado como GATE-* e não bloqueia. "Resolvido" exige evidência verificável (rodar o ambiente real), não suposição. Não existe "MÉDIO aceitável", "cosmético", "pré-existente" ou "diferido pra Wave A" — ver `feedback_resolver_nao_documentar`. Override exclusivo do Roldão via `# ritual-gate: skip -- APROVADO POR ROLDAO: <razão>` no commit; o agente nunca decide derrubar este gate. O hook `ritual-gate-check.sh` materializa a barreira.

**Tabela normativa de severidade por tipo de achado (emenda R8 2026-06-12 — auditoria de cerimônia):**

| Tipo de achado | Severidade canônica | Notas |
|---|---|---|
| Drift de contagem/status/data em doc (número desatualizado) | **BAIXO sempre** | Nunca ALTO/MÉDIO — M3 teve 8× errado |
| Nome/formato de teste (TST-004/006) | **BAIXO** | Verificação mecânica: usar `scripts/checa-tst-mecanico.sh --report` |
| Débito "forward-looking" de código que não existe ainda | **BAIXO ou GATE rastreado** | Nunca MÉDIO+ |
| Log/observabilidade ausente em path não-crítico | **BAIXO** | Path crítico = financeiro/auth/kms/audit/tenant |
| PII/segurança/WORM/isolamento tenant | **Régua cheia (pode ser CRÍTICO)** | OBS-CAL-01 M4 era "log" mas era trilha WORM obrigatória |
| Regulatório/perda de dados irreversível | **Régua cheia** | Sem rebaixamento por "já existe em outra camada" |

Auditor que quiser fugir desta tabela **precisa justificar explicitamente** no veredito. Achado sem justificativa de desvio = regulado pela tabela.

**BAIXOs em lote pós-fechamento (emenda R10 2026-06-12 — decisão Roldão — auditoria de cerimônia):** em módulo NÃO-metrológico, achados BAIXO são registrados na matriz §8 e consertados em LOTE imediatamente APÓS o fechamento (mesma sessão ou seguinte) — não travam nem serializam o ciclo. Em módulo metrológico (`metrologia/*`, calibração, certificados) o conserto de BAIXO continua dentro do ciclo antes de fechar. TODOS os achados continuam sendo consertados — a regra "resolver tudo" do Roldão não muda; muda apenas o momento em módulo operacional.

### 3.7. P8 enxuto — matriz-reconciliação (emenda R20 2026-06-12 — auditoria de cerimônia)

A matriz-reconciliação de cada módulo mantém SOMENTE:
- **§1 Rastreabilidade US/INV↔código** — qual US/INV está em qual arquivo/classe (única rastreabilidade que não existe em outro lugar).
- **§2 INV↔teste** — qual teste cobre qual INV (idem — não é verificável em git log).
- **§8 Ata do P9** — achados da 1ª passada + veredito adversarial + consertos + veredito 2ª passada.

**ABOLIDAS** as seções "entregas por fase" e "hooks novos por fase" — duplicam `git log` e `settings.json`; nenhum auditor as lê na prática.

**Rastreabilidade oficial:** portada por `INV-*` e `T-*`. IDs `AC-*` formais são opcionais — zero uso observado nas frentes M6→PPS, que fecharam 8/8 PASS sem eles.

### 3.8. Geração de tasks.md — workflow por risco (emenda R21 2026-06-12 — auditoria de cerimônia)

O workflow completo (multi-leitores + 3 lentes adversariais) para geração do `tasks.md` aplica-se SOMENTE em módulo de:
- Risco metrológico (`metrologia/*`, calibração, certificados, padrões, escopos-cmc, procedimentos).
- Risco financeiro alto (faturamento, billing-saas, NFS-e, gateway de pagamento).

Em módulo operacional comum (clientes, equipamentos, OS, agenda, agenda-tecnico, comunicação, etc.): usar P3 padrão (plano → revisão tech-lead → tasks). Não inflar o processo de geração de tasks com lentes extras.

### 3.9. Frontmatter draft→stable (emenda R22 2026-06-12 — auditoria de cerimônia)

Promoção de `status: draft` → `status: stable` deixa de ser passo formal de cada fechamento de módulo. Faz-se em **lote periódico**: fechamento de bloco de módulos (ex: fim de Wave A) ou auditoria mensal de docs. Docs estáveis há mais de 4 semanas sem edição substancial são candidatos à promoção em lote. O `auditor-drift-docs` semântico mensal identifica esses candidatos.

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
| 2026-05-29 | Fatiamento obrigatório (INV-RITUAL-002), roteamento de auditores por risco com travas (INV-RITUAL-003), revisão profunda do plano reforçada. INV-RITUAL-001 mantido por decisão do Roldão. |
| 2026-06-12 | **Auditoria de cerimônia do processo — aprovação integral Roldão (pacote B+D).** Emendas incorporadas: R5 (2ª passada escopada — proibida passada confirmatória), R6 (verificação adversarial de TODO MÉDIO+ antes do mutirão), R7 (aposentadoria drift-docs do fechamento; supplychain e conformidade-lgpd por gatilho de diff), R8 (tabela normativa de severidade por tipo de achado), R10 (BAIXOs em lote pós-fechamento em módulo não-metrológico — decisão explícita Roldão), R20 (P8 enxuto — matriz-reconciliação só §1/§2/§8), R21 (workflow multi-leitores de tasks só em módulo metrológico/financeiro), R22 (promoção draft→stable em lote periódico). |
