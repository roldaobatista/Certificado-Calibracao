---
owner: roldao
revisado-em: 2026-05-27
status: stable
proposito: instrução canônica para um agente IA construir a estrutura documental completa de QUALQUER projeto de software novo, do zero, antes da primeira linha de código.
publico-alvo: agente IA (Claude Code, Codex CLI, Cursor, Windsurf, Kiro) operando em repositório recém-criado.
---

# Estrutura canônica de docs para projeto NOVO — manual do agente IA

> **Para o agente IA que estiver lendo:** este documento é a sua "receita de bolo" pra montar do zero a base documental de qualquer projeto de software. Cada seção lista um arquivo ou pasta, explica **por que existe**, **o que tem dentro**, **gatilho de criação** e **tamanho-alvo**. Você deve criar **somente o que faz sentido pro tipo de projeto** — não fabrique documentos vazios só pra cumprir checklist. Quando uma camada não se aplica (ex: projeto sem multi-tenancy não precisa de ADR de RLS), deixe a pasta inexistente e registre o porquê em `docs/non-aplica.md`.

---

## 0. Como o agente usa este documento

1. **Antes de criar qualquer arquivo**, leia o repo atual e o pedido do humano. Identifique:
   - Tipo de software (web app, mobile, CLI, biblioteca, SaaS, ERP, jogo, IA/ML, embarcado, etc.)
   - Quem é o cliente (interno/externo, regulado/não-regulado, B2B/B2C)
   - Restrições óbvias (idioma, geografia, orçamento, prazo)
2. **Confirme entendimento** com o humano em 2-4 perguntas curtas antes de gerar tudo. Use `AskUserQuestion`. Não invente respostas.
3. **Crie em ordem de camada** (0 → 11). Camadas posteriores dependem das anteriores.
4. **Pare e peça revisão humana** ao final de cada camada se o projeto for grande, ou ao final de tudo se for pequeno.
5. **Não escreva código de produto** enquanto qualquer camada bloqueante (0-7) estiver incompleta.

### Marcações universais que você verá

- 🟢 **OBRIGATÓRIO** — todo projeto precisa, sem exceção.
- 🟡 **RECOMENDADO** — quase todo projeto se beneficia; documente decisão de pular.
- 🔵 **CONDICIONAL** — só se a condição listada for verdadeira.
- ⚪ **OPCIONAL** — crie só quando o padrão aparecer 3+ vezes.

---

## 1. Princípios universais (válidos para qualquer projeto)

Esses princípios sustentam toda a estrutura. Eles devem aparecer transcritos ou referenciados em `AGENTS.md`, `CONTRIBUTING.md` e `constitution.md`:

1. **Documento é estado compartilhado** — agente que decide sem doc inventa diferente toda vez.
2. **Spec gera código** (spec-as-source), não código gera spec. Se mudar comportamento, atualize a spec antes ou junto.
3. **Conciso vence completo** — `AGENTS.md` ≤ 300 linhas, `CLAUDE.md`/equivalente ≤ 150 linhas, ADR ≤ 200 linhas.
4. **Non-goals explícitos** — toda spec/ADR declara o que NÃO está no escopo.
5. **IDs rastreáveis** — `US-<MOD>-NNN` → `AC-<MOD>-NNN-N` → `T<MOD>NNN` → commit.
6. **Negócio vence conveniência do agente** — não otimizar pelo que IA erra menos; otimizar pelo cliente/produto.
7. **Regra crítica vira hook**, não só doc — toda regra que pode ser violada por descuido vira execução automática (pre-commit, pre-tool).
8. **Frontmatter obrigatório** em todo doc: `owner`, `revisado-em` (data ISO), `status` (`draft|stable|deprecated|superseded`). Sem isso, o doc apodrece silenciosamente.
9. **Verificar antes de afirmar** — nunca dizer "pronto" sem executar o comando de verificação.
10. **Causa raiz, nunca sintoma** — teste falhou = código errado, nunca silenciar teste.

---

## 2. Camada 0 — Raiz do repositório (governança imediata)

> **Quando criar:** primeira coisa, no momento `git init`. Bloqueia tudo abaixo.

### 🟢 `README.md`
**Tamanho:** 1 página (≤120 linhas).
**Contém:**
- Nome do projeto (1 linha) + 1 frase do que é
- Estado atual (`alpha`/`beta`/`prod`) + versão
- Como rodar localmente (3-5 comandos)
- Como rodar testes (1 comando)
- Link pra `AGENTS.md` ("documentação completa")
- Licença + autor
**NÃO contém:** roadmap longo, arquitetura, decisões técnicas — isso vai em outros docs.

### 🟢 `AGENTS.md`
**Tamanho:** ≤ 300 linhas. Se passar, fatie em sub-docs e referencie.
**Contém (seções fixas):**
1. **Identidade do produto** — nome (marcar `PROVISÓRIO` se ainda não definido), escopo de 1 parágrafo, modelo de negócio, cliente piloto.
2. **Stack candidata** — tabela `Camada | Escolha | Notas`. Marcar "candidata" até validação real.
3. **Princípios não-negociáveis** — referência ao `constitution.md` + `REGRAS-INEGOCIAVEIS.md`.
4. **Decisões fundadoras (D1..DN)** — tabela das decisões que NÃO podem ser reabertas sem ADR.
5. **Modelo de agentes** — quais subagentes existem (`tech-lead`, `advogado`, etc.) e quais auditores rodam pré-commit.
6. **Comandos canônicos** — tabela `Operação | Comando`.
7. **Política de commits** — atômicos, mensagem, hooks proibidos (`--no-verify`, etc.).
8. **Convenções** — idioma, pastas-chave, nomenclatura.
9. **Segurança/dados** — multi-tenancy, KMS, WORM, retenção (se aplicável).
10. **ADRs ativas** — tabela `# | Tema | Status | Bloqueia fase | Depende de`.
11. **Pendências (gates)** — o que falta pra próxima fase abrir.

**Frontmatter NÃO leva** (é raiz). Mas leva título + 1 parágrafo de status no topo com data.

### 🟢 `CLAUDE.md` (ou `.cursorrules`, `.windsurfrules`, `AGENTS.md` específico)
**Tamanho:** ≤ 150 linhas.
**Contém:**
- Linha 1: `@AGENTS.md` (importa o canônico)
- Perfil do usuário (CRÍTICO se o humano é não-técnico): linguagem obrigatória, tabela de tradução, pró-atividade.
- Regra #0 (investigar antes de mexer em lógica de negócio).
- Idioma do canal.
- Estado do ambiente (o que existe e o que não existe ainda).
- Notas de plataforma (Windows/Linux/Mac diferenças).
- O QUE NÃO REPETIR: tudo que já está em `AGENTS.md`. Este arquivo é **adendo do harness**, não cópia.

### 🟢 `CONTRIBUTING.md`
**Tamanho:** 50-150 linhas.
**Contém:**
- Fluxo do agente: ler spec → propor plano → revisão → implementar → auditar → commit.
- Fluxo do humano: como propor mudança, como abrir ADR, como reportar bug.
- Quality gates obrigatórios antes de commit (lint, types, testes do diff).
- O que NUNCA fazer (`--no-verify`, push --force em main, etc.).
- Como rodar auditores localmente.

### 🟢 `CODEOWNERS`
**Tamanho:** 20-80 linhas.
**Contém:**
- Paths críticos (cada um com owner): `financeiro/`, `auth/`, `tenant/`, `kms/`, `migrations/`, `.claude/hooks/`, `.github/workflows/`, `CODEOWNERS` (sim, ele próprio).
- Em projetos solo: owner é o dono mesmo. O valor é forçar revisão extra (ver hook abaixo).

### 🟢 `LICENSE`
Decisão consciente: MIT/Apache 2.0/proprietária/AGPL. Não copiar cego.

### 🟢 `CHANGELOG.md`
Formato [Keep a Changelog](https://keepachangelog.com). Vazio no início com seção `## [Unreleased]`.

### 🟢 `REGRAS-INEGOCIAVEIS.md`
**Tamanho:** cresce com o projeto; começa com 5-10 regras.
**Contém:**
- IDs estáveis e categorizados: `INV-NNN` (invariantes de negócio), `INV-TENANT-NNN` (multi-tenancy), `SEC-NNN` (segurança), `TST-NNN` (testes), `INV-AGENT-NNN` (operação do agente IA).
- Cada regra: `ID | Regra (1 frase) | Justificativa (1 frase) | Hook que aplica (se existe) | Auditor que verifica`.
- **Fonte única** — toda outra doc referencia por ID, nunca redeclara.

### 🟢 `.gitignore`
Específico da stack. Inclui sempre: `.env*`, `*.log`, `__pycache__`, `node_modules`, `dist/`, `build/`, `.DS_Store`, `Thumbs.db`, `coverage/`, `.idea/`, `.vscode/settings.json` (mas versionar `.vscode/extensions.json`).

### 🟡 `.editorconfig`
Padroniza tabs/espaços/line-endings entre editores. 10 linhas, copy-paste seguro.

---

## 3. Camada 1 — Discovery (Família 0)

> **Quando criar:** antes de qualquer ADR. Bloqueia decisões arquiteturais.
> **Pula apenas se:** projeto é continuação óbvia de outro já documentado, OU é experimento pessoal de ≤2 dias.

Pasta: `docs/discovery/`

### 🟢 `problema.md` (1-3 páginas)
- Dor real, com evidências (cita conversa/email/dado).
- Quem sente a dor e quanto custa hoje (em tempo, dinheiro ou risco).
- Por que solução existente não resolve.

### 🟢 `personas.md` (1-2 páginas por persona, 2-5 personas)
- Nome (fictício), papel, contexto técnico, frustrações, "job to be done".
- Distinguir **usuário** de **comprador** se forem pessoas diferentes.

### 🟢 `jornadas.md` (1 página por jornada, 3-7 jornadas)
- Fluxo ponta-a-ponta do que a persona faz HOJE (sem o produto) e o que vai fazer DEPOIS (com o produto).
- Marca **momentos de dor** e **momentos de delight**.

### 🟡 `entrevistas/` (pasta)
- 1 arquivo por entrevista: `EE-NNN-<nome>.md`.
- Mínimo 3 entrevistas com OUTRAS pessoas se o cliente piloto é o próprio dono ("founder is customer" — risco crítico).
- `sintese.md` agrega padrões.

### 🟢 `concorrentes.md`
- Tabela `Concorrente | Pontos fortes | Pontos fracos | Preço | Mystery shopping (sim/não)`.
- Pra cada concorrente sério: pasta com print/captura/notas.

### 🔵 `mercado-regulatorio.md` (se o domínio é regulado)
- Leis, normas, órgãos fiscalizadores, prazos.
- Para cada item: link oficial + 1 parágrafo do que exige.

### 🟢 `glossario.md`
- Termos do domínio com definição canônica.
- Marca tradução PT↔EN se o produto é bilíngue.
- **Toda outra doc usa estes termos.** Inconsistência de termo = bug.

### 🟢 `non-goals.md`
- Lista numerada do que o produto NUNCA fará (ou não fará na V1).
- Cada non-goal com justificativa de 1 linha.

### 🟢 `riscos.md`
- IDs `R-NNN`. Cada risco: descrição, probabilidade (A/M/B), impacto (A/M/B), mitigação, responsável.

### 🟡 `restricoes.md`
- Orçamento, prazo, equipe disponível, geografia, idioma, dependências externas.

### 🟡 `hipoteses-validar.md`
- O que ainda é suposição (não evidência). Cada hipótese com critério de validação.

### 🟢 `metricas-norte.md`
- **North Star Metric** (1 só).
- 3-5 métricas guardrail (o que NÃO pode piorar enquanto a NS melhora).
- Como medir cada uma (fonte de dado, fórmula).

### 🔵 `dados-existentes.md` (se vai migrar de sistema legado)
- O que existe, em qual formato, quantos registros, qualidade dos dados.

### 🔵 `integracoes-externas.md` (se depende de APIs/sistemas terceiros)
- Lista de integrações obrigatórias com: provedor, finalidade, SLA conhecido, custo, plano B.

### 🟢 `sintese-final.md`
- **Destrava ADRs.** Resume os 14 artefatos acima em 2-4 páginas.
- Status `stable` aqui significa "pode começar a decidir arquitetura".

---

## 4. Camada 2 — Decisões arquiteturais (ADRs)

Pasta: `docs/adr/`. Formato de nome: `NNNN-titulo-em-kebab-case.md`.

### 🟢 Template ADR (fixo pra todo projeto)

```markdown
---
id: ADR-NNNN
titulo: <título curto>
status: proposta | aceito | superseded | deprecated
data-proposta: YYYY-MM-DD
data-aceite: YYYY-MM-DD | null
depende-de: [ADR-XXXX, ADR-YYYY]
bloqueia-fase: <F-A|M1|Wave A|...> | null
superseded-by: ADR-ZZZZ | null
owner: <quem>
revisado-em: YYYY-MM-DD
---

# ADR-NNNN: <título>

## Contexto
<2-5 parágrafos. Por que precisamos decidir agora? O que muda se NÃO decidirmos?>

## Opções consideradas
### Opção 1: <nome>
- Prós:
- Contras:
- Custo (tempo/dinheiro/risco):

### Opção 2: <nome>
...

## Decisão
<1-3 parágrafos. Qual opção e por quê.>

## Consequências
- **Positivas:**
- **Negativas / dívida assumida:**
- **Reversibilidade:** fácil | média | difícil | irreversível

## Non-goals (o que esta ADR NÃO decide)
- ...

## Como validar (gates)
- GATE-<NOME>-N: <critério binário verificável>

## Referências
- <links, papers, threads de discussão>
```

### ADRs mínimas comuns (criar conforme aplicável)

- 🟢 **ADR-0000** — Uso de IA / agentes (como agentes participam do desenvolvimento, limites).
- 🟢 **ADR-0001** — Stack principal (linguagem, framework, banco). **Sempre com portões de validação**, não escolha definitiva.
- 🔵 **ADR-0002** — Multi-tenancy (se SaaS).
- 🔵 **ADR-0003** — Estratégia mobile (se tem app).
- 🔵 **ADR-0004** — Sync offline (se mobile com conectividade ruim).
- 🟡 **ADR-00NN** — Feature flags.
- 🟡 **ADR-00NN** — Autorização/autenticação.
- 🟡 **ADR-00NN** — Estratégia de UI (SSR/SPA/hybrid).
- 🔵 **ADR-00NN** — KMS / gestão de chaves (se cripto).
- 🔵 **ADR-00NN** — Storage de arquivos (se manipula).
- 🟡 **ADR-00NN** — Observabilidade (logs/métricas/traces).
- 🟡 **ADR-00NN** — Filas/jobs assíncronos.

**Regra:** uma decisão arquitetural não-trivial = uma ADR. Numeração nunca é reciclada (ADR superseded vira `status: superseded`, nunca apagada).

---

## 5. Camada 3 — Arquitetura

Pasta: `docs/arquitetura/`

### 🟢 `visao-geral.md`
- Diagrama C4 nível 1 (contexto) e nível 2 (containers).
- Use Mermaid ou link pra imagem versionada em `docs/arquitetura/diagramas/`.
- Lista de componentes principais com 1 frase cada.

### 🟢 `anti-corrosion-layer.md` (também chamado "ports/adapters" ou "hexagonal")
- Pra cada integração externa = **uma porta** (interface).
- Tabela: `Porta | Adapter atual | Adapters alternativos | INV relacionadas`.
- Portas comuns: `Fiscal`, `Signature`, `Storage`, `Auth`, `Queue`, `MultiTenant`, `Payment`, `Email`, `LLM`, `Analytics`, `OmniChannel`.
- Crítico pra trocar provedor sem reescrever produto.

### 🟢 `modelo-dados-canonico.md`
- Entidades raiz com: campos obrigatórios, invariantes, relações.
- Diagrama ER simplificado.
- Distinguir entidade **temporal** (com vigência), **append-only** (WORM), **mutável** (config).

### 🟡 `eventos-canonicos.md`
- Catálogo de eventos de domínio: nome, payload, produtor, consumidores.
- Versionamento de schema (`_schema_version: vN`).
- Regras de idempotência e dead-letter.

### 🟢 `seguranca-baseline.md`
- Threat model resumido (STRIDE).
- Onde estão secrets, como rotacionar.
- Política de senhas/sessão.
- Multi-tenancy isolation (se aplicável).

### 🟡 `observabilidade-baseline.md`
- Pra cada serviço crítico: logs estruturados, métricas obrigatórias, traces.
- SLOs e alertas.
- Onde olhar (dashboard URL placeholder).

---

## 6. Camada 4 — Produto (PRD e specs de módulo)

### 🟢 `docs/prd.md` (PRD raiz)
- Visão de 1 página.
- Lista de módulos com prioridade (MVP / V1 / V2 / backlog).
- Sucesso = North Star + métricas guardrail.
- Cronograma de alto nível (trimestres, não dias).

### Por módulo: `docs/dominios/<dominio>/modulos/<modulo>/`

### 🟢 `spec.md`
- **User stories** com IDs `US-<MOD>-NNN`. Formato: "Como <persona>, quero <ação>, para <benefício>".
- **Acceptance criteria** `AC-<MOD>-NNN-N` — **binários e verificáveis** (cada AC vira teste).
- **Invariantes** `INV-<MOD>-NNN` — regras que NUNCA podem ser violadas no módulo.
- **Non-goals** — explícitos.
- **Dependências** de outros módulos / ADRs.

### 🟢 `plan.md`
- Como implementar (passo a passo, ordem).
- Estimativa em "fatias verticais" (não tarefas técnicas).
- Riscos específicos do módulo.

### 🟢 `tasks.md`
- IDs `T<MOD>NNN`, rastreáveis até commit.
- Cada task: descrição, AC que satisfaz, estimativa, dependência.

### 🟡 `prd-ux.md` (se módulo tem tela)
- Para cada tela: **5 estados** obrigatórios (loading, empty, error, success, partial).
- Checklist a11y (WCAG 2.1 AA).
- Mockups linkados (Figma/print).

### 🟡 `auditoria-familia5.md`
- Saída dos auditores (segurança/qualidade/produto/etc.) com PASS/FAIL/CONCERN.
- Atualizado a cada passada.

---

## 7. Camada 5 — Faseamento

Pasta: `docs/faseamento/`

### 🟢 `faseamento-foundation-waves.md`
- **Foundations (F-A, F-B, F-C…)** — capacidades transversais sem as quais nenhum módulo de produto funciona (multi-tenant, auth, observabilidade).
- **Waves** — grupos de módulos entregues juntos.
- Diagrama de dependência (Foundation → Wave A → Wave B).

### 🟢 `faseamento-modulos.md`
- Lista numerada de TODOS os módulos previstos (mesmo os "longe").
- Pra cada um: nome, prioridade, depende-de, fase prevista.

### Por fase: `docs/faseamento/<fase>/`
- `spec.md` — o que a fase entrega (lista de US e ADRs envolvidas).
- `plan.md` — como vamos construir (ordem, equipe, risco).
- `tasks.md` — `T-<FASE>-NNN`.
- `auditoria-familia5.md` — auditoria de saída antes de fechar a fase.

### 🟡 `docs/faseamento/auditorias/`
- Auditorias transversais (ex: "10 lentes pré-Wave A").
- Cada auditoria com: data, lentes aplicadas, achados (CRÍTICO/ALTO/MÉDIO/BAIXO/CONCERN), plano de conserto.

---

## 8. Camada 6 — Conformidade (CONDICIONAL — só se regulado)

Pasta: `docs/conformidade/`

### 🔵 `lgpd/` ou `gdpr/` ou `ccpa/` (privacidade de dados)
- `bases-legais.md` — pra cada campo PII: base legal (consentimento/contrato/legítimo interesse/obrigação legal).
- `matriz-retencao.md` — campo × prazo × justificativa legal.
- `canal-titular.md` — como o titular exerce direitos (acesso/correção/eliminação/portabilidade).
- `ripd-template.md` — Relatório de Impacto à Proteção de Dados.
- `crypto-shredding.md` — como apaga dado por crypto-shredding sem violar WORM.

### 🔵 `fiscal/` (se emite NF/calcula impostos)
- Por país/região: regras, layouts, prazos de envio.

### 🔵 `setoriais/` (ISO/HIPAA/PCI-DSS/SOC2/etc.)
- Por norma: cláusulas aplicáveis, evidências necessárias, ciclo de auditoria.

### 🟡 `comum/retencao-matriz.md`
- Tabela única que casa retenção fiscal × privacidade × setorial — onde houver conflito, prevalece o **mais longo**.

---

## 9. Camada 7 — Governança e auditoria

Pasta: `docs/governanca/`

### 🟢 `raci.md`
- Tabela `Atividade | Responsável | Aprovador | Consultado | Informado`.

### 🟢 `limites-agente-ia.md`
- O que IA NÃO pode fazer sozinha (deletar dados de prod, rotacionar credencial, abrir gasto, mudar visibilidade de repo).
- O que IA pode fazer autonomamente.
- Critérios de escalação pra humano.

### 🟢 `catalogo-auditores.md`
- Lista de auditores ativos. Pra cada um: versão, severidade que bloqueia (commit/merge/fase), prompt de origem.
- **Auditores comuns** (criar conforme valor):
  1. `auditor-seguranca` — SEC-*, INV-TENANT-*
  2. `auditor-qualidade` — TST-*, cobertura, mascaramento de teste
  3. `auditor-produto` — AC binários, non-goals, glossário
  4. `auditor-drift-docs` — pendência marcada que já foi feita, ADR superseda
  5. `auditor-llm-correctness` — docstring que mente, `Any` de fuga, código órfão de US
  6. `auditor-performance` — N+1, timeout, rate-limit
  7. `auditor-observabilidade` — trilha auditável, tenant_id/correlation_id
  8. `auditor-idempotencia` — POST sem `Idempotency-Key`, consumer sem replay protection
  9. `auditor-supplychain` — dep nova sem justificativa, sem pin
  10. `auditor-conformidade-lgpd` — PII sem base legal, endpoint expõe PII sem sanitização

### 🟢 `auditor-<nome>-prompt.md` (1 arquivo por auditor)
- Prompt versionado: papel, regras que verifica (com IDs), formato de saída, severidade.
- Versão semântica (1.0.0, 1.1.0, ...). Mudança de prompt = bump.

### 🟢 `politica-commits.md`
- Atômico, mensagem (formato livre vs Conventional Commits — decidir).
- Co-Authored-By obrigatório se IA gerou.
- Lista de flags proibidas: `--no-verify`, `--no-gpg-sign`, `--force` em main, etc.

---

## 10. Camada 8 — Operação e Segurança

### Pasta `docs/operacao/`

- 🟢 `setup-local.md` — instalar dependências, subir banco, primeiro `make run`.
- 🟡 `runbooks/` — 1 arquivo por procedimento operacional (subir/derrubar, rollback, backup, restore).
- 🟡 `incidentes/` — post-mortems (template fixo: o que houve, impacto, causa raiz, ações corretivas).
- 🔵 `dr-backup.md` — disaster recovery: RTO, RPO, drill de restore (data do último).

### Pasta `docs/seguranca/`

- 🟢 `threat-model.md` — STRIDE por componente crítico.
- 🟡 `mcp-policy.md` — se usa MCP servers, quais aprovados e por quê.
- 🟢 `supply-chain.md` — política de deps novas (justificativa + CVE check), pin de versões, SHA pin de actions/imagens.
- 🟢 `secrets-rotation.md` — pra cada secret: onde mora, cadência de rotação, último drill.

---

## 11. Camada 9 — Harness do agente IA

Pasta: `.claude/` (ou equivalente — `.cursor/`, `.windsurf/`, `.kiro/`)

### 🟢 `settings.json`
- Permissões (allow/deny por ferramenta).
- Hooks (PreToolUse, PostToolUse, etc.).
- Modelo padrão.

### 🟢 `hooks/`
- 1 hook = 1 arquivo `.sh` (ou `.js`/`.py`).
- **Crítico:** `_test-runner.sh` com casos verdes versionados. Cada hook tem casos POSITIVO (deve passar) e NEGATIVO (deve bloquear).
- Hooks comuns universais:
  - `block-destructive.sh` — bloqueia `rm -rf /`, `drop database`, `git push --force`, etc.
  - `secrets-scanner.sh` — bloqueia commit com regex de chave AWS/GCP/Stripe/etc.
  - `paths-frontmatter-validator.sh` — bloqueia doc novo sem frontmatter.
  - `anti-mascaramento.sh` — bloqueia `assert True`, `@pytest.skip` sem motivo, `# type: ignore` solto.
- Hooks específicos do domínio: criar conforme regra crítica aparece.

### 🟢 `agents/`
- Subagentes especialistas (1 arquivo `.md` por agente).
- Frontmatter: `name`, `description` (com gatilho concreto), `tools` (restringe), `model`.
- **Humano-substitutos** comuns: `tech-lead`, `advogado`, `corretora-seguros`, `consultor-setorial`.
- **Auditores** (descritos na Camada 7).

### ⚪ `commands/`
- Slash commands. Criar quando padrão repetir 3x.

### ⚪ `skills/`
- Habilidades reutilizáveis. Criar quando padrão repetir 3x.

### ⚪ `rules/`
- Regras com `paths:` no frontmatter (lazy load por caminho tocado).

### 🟡 `output-styles/`
- Tom canônico. Útil quando humano tem preferência forte (idioma, concisão, sem emoji, etc.).

### 🟢 `.mcp.json` (na raiz, NÃO em `.claude/`)
- MCP servers plugados. Começar com github; adicionar playwright/postgres/etc. sob demanda.

---

## 12. Camada 10 — Convenções e índice

### 🟢 `docs/CONVENCOES-DOC.md`
- **Frontmatter obrigatório** (formato exato).
- Idioma (PT/EN/bilíngue).
- Nomenclatura: pasta em kebab-case, arquivo em kebab-case, IDs em UPPER_SNAKE.
- Como linkar entre docs (sempre relativo).
- Como marcar TODO/FIXME (com data e dono).

### 🟢 `docs/INDICE.md` (sitemap navegável)
- Árvore de pastas com 1 linha de descrição cada.
- Atualizado a cada doc novo (auditor-drift-docs cobra).

### 🟢 `docs/documentos-do-projeto.md`
- Tabela: `Caminho | Status | Owner | Última revisão | Bloqueia?`.
- Útil pra ver de longe quanto está `draft` vs `stable`.

---

## 13. Camada 11 — Estado vivo

### 🟢 `.agent/CURRENT.md` (ou `STATE.md`)
- O que está em foco AGORA (1-2 parágrafos).
- Atualizado **toda sessão** que muda foco.
- Lê primeiro toda vez que um agente entra.

### 🟢 `MEMORY.md` (no harness, ex: `~/.claude/projects/<proj>/memory/MEMORY.md`)
- Índice de memórias persistentes do agente.
- Fatos do usuário (perfil, preferências), do projeto (decisões fora-do-código), referências externas.

---

## 14. Fluxo de trabalho completo — o ritual

> **Esta seção descreve COMO o trabalho acontece** depois que a estrutura documental existe. É o "como rodar a roda" — não confunda com a estrutura em si (seções 2-13).

### 14.1 Visão macro (de cima)

```
   DISCOVERY (Camada 1)
          ↓
   ADRs aceitas (Camada 2)  ←──── subagentes especialistas opinam
          ↓
   FASEAMENTO (Foundations + Waves + Marcos — Camada 5)
          ↓
   ┌────────────────────────────────────────┐
   │  RITUAL POR STORY (Spec Kit)           │
   │  /specify → /plan → /tasks → /implement│
   │       ↑              ↓                 │
   │       └── loop até PASS ZERO C/A/M ────┤
   └────────────────────────────────────────┘
          ↓
   MARCO FECHADO → atualiza AGENTS.md §ADRs + §Pendências
          ↓
   GATEs BAIXO (carryover) rastreados → próxima Wave
```

---

### 14.2 Início de sessão — leitura obrigatória

Toda sessão de agente IA começa lendo, **nesta ordem**:

```
1. .specify/memory/constitution.md   (princípios fundadores)
2. REGRAS-INEGOCIAVEIS.md            (INV-*, SEC-*, TST-*)
3. .agent/CURRENT.md                 (foco AGORA)
4. AGENTS.md                         (canônico produto/arquitetura)
5. CLAUDE.md / .cursorrules / etc.   (adendo do harness em uso)
6. docs/dominios/<dom>/modulos/<mod>/ (spec do módulo em foco)
```

**Pular qualquer item** = agente inventa diferente toda vez (viola Princípio §1.1 — "documento é estado compartilhado").

---

### 14.3 Criação de documento novo (PRD / Spec / ADR)

```
┌─────────────────────────────────────────────────────────┐
│  Humano pede ou agente identifica gap                   │
└─────────────────────────────────────────────────────────┘
                          ↓
            ┌─────────────────────────┐
            │ Qual tipo de doc?       │
            └─────────────────────────┘
              ↓          ↓         ↓
        ┌────────┐  ┌────────┐  ┌────────┐
        │  PRD   │  │  ADR   │  │ Spec US│
        │ módulo │  │        │  │        │
        └────────┘  └────────┘  └────────┘
              ↓          ↓         ↓
   ┌─────────────────────────────────────────┐
   │ Criar arquivo com FRONTMATTER obrigat.: │
   │  owner / revisado-em / status: draft    │
   └─────────────────────────────────────────┘
                          ↓
   ┌─────────────────────────────────────────┐
   │ Convocar subagentes pertinentes:        │
   │  • tech-lead       (arquitetura)        │
   │  • especialista-legal (LGPD/contratos)  │
   │  • especialista-risco (segurança/seguro)│
   │  • especialista-domínio (regulatório)   │
   └─────────────────────────────────────────┘
                          ↓
   ┌─────────────────────────────────────────┐
   │ Cada um responde:                       │
   │   APROVADO | RESSALVAS | REPROVADO      │
   │ Parecer vira arquivo em                 │
   │  docs/.../revisoes/<US-ID>-<agente>.md  │
   └─────────────────────────────────────────┘
                          ↓
                          ↓ LOOP se REPROVADO
                          ↓ (limite: 5 reprovações = escalation humano)
                          ↓
   ┌─────────────────────────────────────────┐
   │ Doc promovido de draft → stable         │
   │ Atualiza INDICE.md +                    │
   │ documentos-do-projeto.md +              │
   │ AGENTS.md §ADRs se for ADR              │
   └─────────────────────────────────────────┘
```

**Critério de invocação por subagente** (não invoca todos sempre — só os pertinentes ao escopo da decisão):

| Subagente | Quando invocar |
|---|---|
| `tech-lead` | Toda decisão que adiciona/altera modelo, migration, API, fluxo técnico não-trivial |
| `especialista-legal` | Decisão que toca privacidade (dados pessoais, consentimento, retenção), contrato, regulatório |
| `especialista-risco` | Decisão que altera fluxo financeiro, exposição cyber, integração com terceiro pago |
| `especialista-domínio` | Decisão que toca regra do domínio (regulado: norma X; jogo: balanceamento; ML: viés do modelo) |

---

### 14.4 Ritual Spec Kit por Story (o coração)

```
       ┌─────────────────────────────────────┐
       │  /specify  — escrever a Story       │
       │                                     │
       │  US-MOD-NNN: <título>               │
       │   Como <persona>, quero <ação>,     │
       │   para <benefício>                  │
       │   AC-MOD-NNN-1: GIVEN/WHEN/THEN     │
       │   AC-MOD-NNN-N: ... (BINÁRIO)       │
       │   Invariantes citadas: INV-*        │
       │   Non-goals: ...                    │
       └─────────────────────────────────────┘
                       ↓
       ┌─────────────────────────────────────┐
       │  /plan  — plano SEM código          │
       │                                     │
       │  • Sequência T-MOD-NNN              │
       │  • Modelos/migrations               │
       │  • Endpoints/views                  │
       │  • Hooks que vão validar            │
       │  • Testes 1:1 com ACs               │
       │  • Riscos                           │
       └─────────────────────────────────────┘
                       ↓
       ┌─────────────────────────────────────┐
       │  REVIEW dos N subagentes            │
       │  (só os pertinentes — não todos)    │
       │                                     │
       │  Output: APROVADO|RESSALVAS|REPROV. │
       └─────────────────────────────────────┘
                       ↓
          ┌────────────┴────────────┐
          │ Algum REPROVADO?        │
          └────────────┬────────────┘
              SIM ←────┤────→ NÃO
               │            ↓
               │       ┌─────────────────────────┐
               │       │  /tasks                 │
               │       │  Quebra em T-MOD-NNN    │
               │       │  (1-2 commits cada)     │
               │       └─────────────────────────┘
               │            ↓
               │       ┌─────────────────────────┐
               │       │  /implement             │
               │       │  Código por T-MOD-NNN   │
               │       └─────────────────────────┘
               │            ↓
        Corrige plano       ↓
        ←───────────────────┘
                       (volta pro review)
```

**Anatomia de uma Story** (template fixo, copy-paste):

```markdown
### US-MOD-NNN: <título imperativo curto>
**Como** <persona>, **quero** <ação>, **para** <benefício>.

- **AC-MOD-NNN-1**: GIVEN <estado> WHEN <ação> THEN <resultado verificável binário>.
- **AC-MOD-NNN-2**: GIVEN ... WHEN ... THEN ...

**Invariantes citadas:** INV-NNN, INV-TENANT-NNN
**Dependências:** ADR-NNNN, módulo X, evento Y
**Non-goals (esta Story NÃO faz):** ...
```

ACs **binários**: ou passa ou não passa. Não admite "parcialmente".

---

### 14.5 Durante o `/implement` — defesa em camadas

```
   AGENTE EDITA ARQUIVO
          ↓
   ┌──────────────────────────────────────────────┐
   │  CAMADA 1 — HOOKS pre-tool / pre-commit      │
   │  (orquestrados por _test-runner.sh)          │
   │                                              │
   │  Sempre rodam (qualquer diff):               │
   │   • block-destructive    (rm -rf, drop)     │
   │   • secrets-scanner      (regex chaves)     │
   │   • anti-mascaramento    (skip, assert True)│
   │   • paths-frontmatter    (doc sem header)   │
   │   • context-budget       (arquivo > limite) │
   │                                              │
   │  Condicionais por path:                     │
   │   • tenant-id-validator  (queries)          │
   │   • migration-rls-check  (migrations)       │
   │   • audit-immutability   (audit/)           │
   │   • [+ outros específicos do domínio]       │
   └──────────────────────────────────────────────┘
                  ↓
          ┌───────┴───────┐
          │ Hook bloqueou?│
          └───────┬───────┘
       SIM ←──────┤──────→ NÃO
        ↓                   ↓
   Corrige causa raiz   Commit aceito
   (NUNCA --no-verify)  (cita T-MOD-NNN)
        ↓                   ↓
   Volta ao edit       Próxima task
```

**Regra mestre:** toda regra crítica vira **hook**, não só doc. Hook é executável; doc é prosa que ninguém lê em hora de pressa.

---

### 14.6 Auditoria pós-implementação — gate de fechamento

Acontece **antes de fechar Story / Fase / Marco**. INV-RITUAL-001 (ou equivalente) é o gate inegociável.

```
                  ┌──────────────────────────┐
                  │  1ª PASSADA — N auditores │
                  │  rodam em paralelo        │
                  └──────────────────────────┘
                              ↓
   ┌─────────────┬────────────┴────────────┬─────────────┐
   ↓             ↓                         ↓             ↓
┌────────┐  ┌────────┐  ┌────────┐  ┌──────────┐  ┌────────┐
│seguranç│  │qualida │  │produto │  │drift-docs│  │llm-corr│
└────────┘  └────────┘  └────────┘  └──────────┘  └────────┘
┌────────┐  ┌────────┐  ┌────────┐  ┌──────────┐  ┌──────────────┐
│ perf   │  │  obs   │  │ idemp  │  │supplychain│  │ priv-mecânico│
└────────┘  └────────┘  └────────┘  └───────────┘  └──────────────┘

   Output de cada: PASS | CONCERNS | FAIL
   Classificação: CRÍTICO | ALTO | MÉDIO | BAIXO
                          ↓
              ┌────────────────────┐
              │ Algum C/A/M aberto?│
              └────────────────────┘
                  SIM ↓        ↓ NÃO
                      │        │
                      │        └──→ FASE/MARCO FECHA
                      │              (só BAIXO vira GATE da próxima Wave)
                      ↓
              [vai pra Seção 14.7 — loop de conserto]
```

**Regra de ouro:** MÉDIO bloqueia igual a CRÍTICO/ALTO. Não existe "MÉDIO aceitável", "diferido", "cosmético". Override só do humano dono via comentário no commit (`# ritual-gate: skip -- APROVADO POR <DONO>: <razão>`).

**Ordem padrão (do mais barato pro mais caro em tokens):** Qualidade → Segurança → Produto → demais.
**Paralelo quando independentes** — auditores sem dependência entre si rodam simultâneo.

---

### 14.7 Loop de conserto causa-raiz (batches)

Quando auditores retornam FAIL, agrupar correções por **eixo** (não por arquivo):

```
   ┌──────────────────────────────────────────┐
   │  PADRÃO DE BATCHES (exemplo de 6):       │
   │                                          │
   │  Batch S1: drift-docs (corrigir antes,   │
   │            senão batches seguintes geram │
   │            mais drift)                   │
   │  Batch S2: segurança + privacidade       │
   │  Batch S3: idempotência                  │
   │  Batch S4: observabilidade               │
   │  Batch S5: produto + qualidade           │
   │  Batch S6: drift residual S4-S5          │
   │  Batch S6.1: drift interno do drift      │
   └──────────────────────────────────────────┘
                          ↓
              ┌────────────────────┐
              │  2ª PASSADA dos N  │
              └────────────────────┘
                          ↓
              Ainda tem C/A/M? → SIM → mais batches
                          ↓ NÃO
              ┌────────────────────┐
              │  3ª/4ª PASSADA se  │
              │  drift-docs ainda  │
              │  CONCERNS          │
              └────────────────────┘
                          ↓
                    MARCO FECHADO
                    PASS ZERO C/A/M
```

**Princípio:** conserto na **causa raiz**, nunca no sintoma. Se hook detecta bug em N lugares, conserta o **gerador** desses lugares, não os N lugares individualmente.

---

### 14.8 Fechamento de Fase/Marco

```
   Marco PASS ZERO C/A/M
          ↓
   ┌──────────────────────────────────────────────┐
   │ 1. auditoria-familia5.md §VEREDITO FINAL     │
   │    consolidada                               │
   │                                              │
   │ 2. ADRs aceitas no escopo → AGENTS.md §ADRs  │
   │                                              │
   │ 3. AGENTS.md §Pendências — move de           │
   │    "pendência" para "já feito"               │
   │                                              │
   │ 4. .agent/CURRENT.md atualizado (novo foco)  │
   │                                              │
   │ 5. CHANGELOG.md seção [Unreleased]           │
   │                                              │
   │ 6. GATEs BAIXO → rastreados próxima Wave     │
   │                                              │
   │ 7. MEMORY.md atualizado (sessão / projeto)   │
   └──────────────────────────────────────────────┘
```

---

### 14.9 Auditoria transversal (a cada N marcos)

Não amarrada a Story específica — varredura ampla, com **lentes múltiplas** (segurança / privacidade / arquitetura / produto / risco / regulatório / etc.):

```
   ┌──────────────────────────────────────────┐
   │  Auditoria N lentes pré-Wave             │
   │                                          │
   │  Saída: lista de achados                 │
   │   X CRÍTICOS                             │
   │   Y ALTOS                                │
   │   Z MÉDIOS                               │
   │                                          │
   │  Consolidado em                          │
   │  docs/faseamento/auditorias/             │
   │  PRE-WAVE-<X>-CONSOLIDADO-rodada-N.md    │
   └──────────────────────────────────────────┘
                       ↓
            Plano de N ondas de conserto
                       ↓
       Cada onda → novas ADRs + tasks de saneamento
                       ↓
       Achados podem virar ADR estrutural nova
       + sprints de saneamento antes da Wave começar
```

---

### 14.10 Bug em comportamento — Regra #0 (investigar antes de mexer)

Quando humano reporta bug (comportamento errado, tela errada, cálculo errado):

```
   ┌──────────────────────────────────────────┐
   │ 1. NÃO MEXER NO CÓDIGO AINDA             │
   └──────────────────────────────────────────┘
                       ↓
   ┌──────────────────────────────────────────┐
   │ 2. LER ESTADO REAL                       │
   │    • SELECT no banco                     │
   │    • logs do app                         │
   │    • payload IPC / network               │
   │    • console navegador                   │
   │    O que está SALVO lá?                  │
   └──────────────────────────────────────────┘
                       ↓
   ┌──────────────────────────────────────────┐
   │ 3. RASTREAR O FLUXO                      │
   │    Onde dado é gerado/salvo/lido?        │
   │    Builders duplicados?                  │
   └──────────────────────────────────────────┘
                       ↓
   ┌──────────────────────────────────────────┐
   │ 4. CONFIRMAR ENTENDIMENTO                │
   │    Pergunta curta se ambíguo             │
   └──────────────────────────────────────────┘
                       ↓
   ┌──────────────────────────────────────────┐
   │ 5. CONSERTAR NA CAUSA RAIZ               │
   │    NUNCA mudar template pra esconder bug │
   │    de dados.                             │
   │                                          │
   │    Volta pro ritual Spec Kit:            │
   │    /specify → /plan → /tasks → /implement│
   └──────────────────────────────────────────┘
```

---

### 14.11 Matriz de responsabilidade (quem faz o quê)

| Ator | Função | Quando aparece |
|---|---|---|
| **Humano dono** | Decisão de produto, override de gates, autorização de gastos | Em escalations e fechamentos |
| **Agente IA principal** (Claude/Cursor/Codex/etc.) | Implementa, escreve docs, propõe planos | Sempre |
| **Subagentes humano-substitutos** (tech-lead, advogado, corretora, especialista-domínio) | Revisão estratégica de plano | Antes do `/tasks` |
| **Auditores Família 5** (10 prompts versionados) | Veto pre-commit/pre-merge automático | Em todo commit + fechamento de marco |
| **Hooks** (executáveis em pre-tool/pre-commit) | Bloqueio mecânico de erros conhecidos | Em toda edição/commit |
| **Humano licenciado** (advogado real, contador, especialista certificado) | Assinatura legal/parecer formal | SOB DEMANDA, só pré-produção real |

---

### 14.12 Sinais de que o fluxo quebrou (alerta vermelho)

Agente IA deve **PARAR** se notar qualquer um:

- Escrevendo código sem ter aberto o PRD do módulo
- Sem ter criado Story `US-MOD-NNN`
- Sem ter invocado subagente algum em decisão não-trivial
- Commit não cita `T-MOD-NNN`
- Não rodei auditor antes do push/merge
- Implementei subset da Story sem documentar o restante
- Marquei marco FECHADO com MÉDIO em aberto (viola gate)
- Rotulei MÉDIO como "aceitável/cosmético/diferido"
- Mudei template/UI pra "resolver" comportamento sem ter olhado os dados
- O humano corrigiu minha interpretação 2x na mesma conversa

→ **Voltar pro `/specify` e investigar.**

---

### 14.13 Foundation vs Wave — diferença prática

**Foundation (F-A, F-B, F-C…)** é infraestrutura sem PRD de módulo:
- Stories são `US-FA-NNN`, ACs no doc da própria fase.
- Auditores rodam **só os de infraestrutura** (segurança, qualidade, performance, observabilidade, idempotência, supply-chain) — não tem Produto pra Foundation.

**Wave (A, B, C)** = módulos de produto entregues juntos:
- Ritual completo, incluindo auditor de Produto.

---

### 14.14 Ciclo consolidado por Marco (visão final)

```
┌────────────────────────────────────────────────────────────────────┐
│                                                                    │
│   PRD do módulo (stable)                                           │
│      ↓                                                             │
│   Spec da fase em docs/faseamento/<fase>/                         │
│      ↓                                                             │
│   Plano revisado pelos N subagentes humanos-substitutos           │
│      ↓                                                             │
│   tasks.md com T-<MOD>-NNN                                         │
│      ↓                                                             │
│   ┌─────────────────────────────────────────┐                     │
│   │  LOOP POR TASK:                         │                     │
│   │   /implement → hooks → commit           │                     │
│   │   (cada commit cita T-MOD-NNN)          │                     │
│   └─────────────────────────────────────────┘                     │
│      ↓                                                             │
│   1ª passada — N auditores Família 5                               │
│      ↓ (se FAIL)                                                   │
│   Batches conserto causa-raiz (S1..SN)                             │
│      ↓                                                             │
│   2ª passada — N auditores                                         │
│      ↓ (se ainda FAIL)                                             │
│   Mais batches                                                     │
│      ↓                                                             │
│   3ª/4ª passada se drift-docs ainda CONCERNS                       │
│      ↓                                                             │
│   PASS ZERO C/A/M (gate satisfeito)                                │
│      ↓                                                             │
│   MARCO FECHADO + ADRs aceitas + AGENTS.md atualizado              │
│      ↓                                                             │
│   GATEs BAIXO carryover rastreados próxima Wave                    │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
```

---

## 15. Ordem prática de produção (cenário perfeito)

| Semana | Entrega |
|--------|---------|
| 0 | Camada 0 (raiz) + esqueleto `constitution.md` + 5-10 INV iniciais |
| 1-3 | Camada 1 (Discovery 15 artefatos) — não pula nada se "founder is customer" |
| 4 | Camada 2 (ADRs 0000-0005) + Camada 12 (convenções) |
| 5 | Camada 3 (arquitetura) + Camada 7 (governança esqueleto) |
| 6 | Camada 4 (PRD raiz + 1ª onda specs) |
| 7 | Camada 5 (faseamento Foundation+Waves) |
| 8 | Camada 6 (conformidade — se regulado) + Camada 8 (operação+segurança esqueleto) |
| 9 | Camada 9 (harness IA: settings, hooks mínimos, 4 agentes essenciais) |
| 10 | Camada 11 (estado vivo) + revisão geral dos 4 auditores principais |
| 11+ | **Primeira linha de código** da Foundation F-A com auditores rodando |

**Projeto pequeno (≤3 meses, 1 dev):** comprima pra 1-2 semanas, mas NÃO PULE camadas — corte profundidade, não largura.

---

## 16. Critério "pronto pra começar a codar"

Antes de escrever a primeira linha de código de produto, valide:

- [ ] `README.md` + `AGENTS.md` + `CONTRIBUTING.md` existem e estão `stable`.
- [ ] `REGRAS-INEGOCIAVEIS.md` tem ≥ 10 IDs com hook ou auditor mapeado.
- [ ] Discovery: `sintese-final.md` em `stable`.
- [ ] ADR-0000 (uso de IA) + ADR-0001 (stack) aceitas.
- [ ] Glossário tem ≥ 20 termos.
- [ ] PRD raiz lista módulos com prioridade.
- [ ] Foundation F-A tem `spec.md` + `plan.md` + `tasks.md`.
- [ ] `.claude/hooks/` tem ao menos 4 hooks: block-destructive, secrets-scanner, frontmatter-validator, anti-mascaramento.
- [ ] Pelo menos 3 auditores configurados (segurança, qualidade, produto).
- [ ] `CODEOWNERS` cobre paths críticos previstos.
- [ ] `.gitignore` cobre a stack escolhida.

Faltando qualquer item: **NÃO CODE**. Volte e complete.

---

## 17. Anti-padrões que destroem a estrutura

1. **Pular Discovery** — "vou descobrir codando". Resultado: refatoração total em 3 meses.
2. **ADR retroativa** — codar e DEPOIS escrever ADR justificando. Resultado: ADR vira ficção.
3. **Doc sem frontmatter** — apodrece sem ninguém perceber. Auditor de drift cobra.
4. **`status: draft` por > 30 dias** — promova pra `stable` ou delete.
5. **Pasta criada vazia "pra depois"** — só cria quando tem conteúdo real.
6. **Spec sem AC binário** — "deve ser rápido" não é AC. "P95 < 200ms em 1k req/s" é.
7. **Auditor sem versão** — quando muda prompt, comportamento muda silenciosamente.
8. **Regra crítica só em doc** — vira hook ou auditor, senão alguém vai violar.
9. **Glossário inconsistente** — termo diferente em docs diferentes. Cliente fica perdido.
10. **`AGENTS.md` > 300 linhas** — ninguém lê. Fatie.
11. **Copiar template de outro projeto sem auditar** — herda decisões irrelevantes.
12. **Documentar antes de validar com humano** — gera 500 páginas que ninguém vai usar.

---

## 18. Adaptação por tipo de projeto

| Tipo | Camadas críticas | Pode reduzir |
|------|------------------|--------------|
| **Biblioteca open-source** | 0, 2 (ADRs), 4 (specs por feature), 9 (hooks pra qualidade) | 1 (Discovery resumida), 6 (geralmente N/A), 8 (operação N/A) |
| **CLI / dev tool** | 0, 2, 3, 4, 9 | 1 (resumida), 5 (faseamento simples), 6 |
| **Web app B2C** | 0, 1 (Discovery FORTE), 2, 4, 5, 6 (privacidade), 8 | 9 (harness leve) |
| **SaaS B2B** | TODAS | nenhuma |
| **SaaS regulado** (saúde, financeiro, gov) | TODAS + Camada 6 reforçada | nenhuma — adiciona auditorias externas |
| **Mobile app** | 0, 1, 2 (ADRs sync/offline), 3, 4, 5 | 8 (se backend é de terceiros) |
| **Embedded / IoT** | 0, 2 (hardware), 3, 4, 8 (operação crítica) | 6 (geralmente N/A) |
| **IA/ML produto** | 0, 1 (datasets!), 2 (model lifecycle), 3, 4, 6 (vieses, transparência), 9 (eval) | — |
| **Jogo** | 0, 1 (playtest!), 2, 3, 4 (game design doc no lugar do PRD) | 6 (depende), 8 (depende de online) |
| **Experimento ≤ 2 dias** | 0 mínimo (README + LICENSE), nada mais | TUDO o resto |

---

## 19. Como o agente IA cria a estrutura (passo prático)

Ao receber pedido tipo "criar projeto novo", siga:

1. **Pergunte ao humano** (máx 4 perguntas via `AskUserQuestion`):
   - Tipo de software? (web/mobile/CLI/biblioteca/SaaS/outro)
   - Regulado? Se sim, qual norma?
   - Cliente é o próprio dono ou externo?
   - Idioma do projeto (código/docs/canal)?

2. **Gere `docs/non-aplica.md`** listando camadas que NÃO vão existir e por quê. Isso evita auditor reclamar depois.

3. **Crie Camada 0** primeiro, com `AGENTS.md` em estado `draft` mas completo na estrutura (seções vazias OK, marcadas `<!-- PREENCHER -->`).

4. **Pause e mostre ao humano** a estrutura Camada 0. Peça confirmação antes de seguir.

5. **Para Camadas 1-7**: gere **um esqueleto por arquivo** (frontmatter + seções + 1 parágrafo "preencher"). Não fabrique conteúdo de domínio que você não sabe.

6. **Camada 9 (harness)**: gere com conteúdo real, copy-paste seguro (hooks funcionais, auditores prontos).

7. **Ao terminar**: escreva `docs/CHECKLIST-PRONTO-PRA-CODAR.md` com os 11 itens da Seção 15 marcados ☐/☑.

8. **Reporte ao humano** em formato: "criei N arquivos, M deles esqueleto pra você preencher, K com conteúdo real. Próximo passo é preencher Discovery."

---

## 20. Manutenção da estrutura

- **Semanal:** rodar `auditor-drift-docs` em modo consultivo.
- **A cada doc novo:** atualizar `docs/INDICE.md` e `docs/documentos-do-projeto.md`.
- **A cada ADR aceita:** atualizar tabela em `AGENTS.md` §11.
- **A cada fase fechada:** mover de "pendência" pra "já feito" em `AGENTS.md` §12.
- **A cada hook novo:** adicionar caso de teste em `_test-runner.sh`.
- **A cada auditor com prompt novo:** bump de versão no `catalogo-auditores.md`.

---

## 21. Referência rápida — arquivos mínimos absolutos (projeto micro)

Se o projeto é tão pequeno que você só pode criar 10 arquivos, crie estes:

1. `README.md`
2. `LICENSE`
3. `.gitignore`
4. `AGENTS.md` (≤100 linhas)
5. `CONTRIBUTING.md` (≤30 linhas)
6. `REGRAS-INEGOCIAVEIS.md` (5 regras)
7. `docs/discovery/sintese-final.md` (1 página)
8. `docs/adr/0000-uso-de-ia.md`
9. `docs/adr/0001-stack.md`
10. `.claude/settings.json` + `.claude/hooks/block-destructive.sh`

Tudo o mais é crescimento orgânico — adicione quando o projeto pedir, não antes.

---

**Fim do manual.**

Última atualização: 2026-05-27.
Versão: 1.1.0 (adiciona Seção 14 — Fluxo de trabalho completo / ritual).
Inspirado na estrutura e nos rituais reais de um projeto SaaS regulado em produção, generalizado para qualquer tipo de software.
