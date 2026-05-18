# Plano de defesas anti-erros de IA — Aferê

> **Status (2026-05-17):** **parcialmente aplicado.** As defesas que NÃO dependem de stack já estão em produção (hooks pré-código + auditores Família 5 + auditor de drift). As defesas que dependem de stack (scopes ORM, linters de N+1, contract tests) ficam pendentes até **Foundation F-A** começar — stack está candidata em ADR-0001 (Django + Flutter + PostgreSQL), com 2 dos 3 portões fechados (Portão 1 diferido por decisão do Roldão).
> **Origem:** discussão da sessão de 2026-05-16 entre Roldão e Claude Code, a partir de duas listas de erros comuns de agentes de IA programando (25+ itens, compiladas pelo Roldão).
> **Não é** um plano de arquitetura do produto. É um plano de **defesa** do produto contra erros que IA tipicamente comete.

---

## Contexto da decisão

Roldão opera 100% com agentes (Claude Code + Codex CLI). Não vai contratar humano para programar. Por isso, critérios tradicionais ("é fácil achar dev?", "tem comunidade grande?") **não devem pesar** na escolha de stack. A escolha será revisitada com critérios próprios do Roldão (a definir).

Este plano funciona **independente da stack escolhida** — só as ferramentas concretas (qual linter, qual ORM, qual pacote de auditoria) mudam.

---

## Princípio geral

Existem 4 camadas de defesa contra erros de IA, da mais forte para a mais fraca:

1. **Hooks automáticos** — impossível para o agente burlar
2. **Testes obrigatórios** — portão de qualidade antes de commit
3. **Agentes revisores** — segunda opinião automatizada
4. **Decisões de base bem feitas** — previnem famílias inteiras de erro

Combinadas, cobrem ~95% dos erros conhecidos. Os 5% restantes (regra fiscal nova, decisão de produto, dado real errado, fraude) **sempre exigem humano**.

---

## Grupo 1 — Bloqueio automático por hook (confiabilidade ~99%)

Hook = script que roda automaticamente antes de cada ação do agente. Não depende do agente "lembrar" da regra. Não negocia.

| Erro | Como bloquear | Status |
|---|---|---|
| Migrations destrutivas (`DROP TABLE`, `TRUNCATE`, `dropIfExists`) | Hook `block-destructive.sh` | ✅ Implementado (validado por 14 casos em `_test-runner.sh`) |
| Senha em código, chave AWS, token GitHub | Hook `secrets-scanner.sh` | ✅ Implementado (12 casos no test-runner, inclui `.env.example` permitido) |
| `git push --force`, `git reset --hard`, `rm -rf`, `chmod 777`, `curl \| bash` | Hook `block-destructive.sh` | ✅ Implementado |
| Esquecer filtro por empresa (`.objects.all()` sem tenant) — versão Django | Hook `tenant-id-validator.sh` bloqueia `.objects.all()` em código não-teste sem filtro de tenant. | ✅ Implementado pra Django/PG (stack candidata) |
| Migration que cria tabela sem `tenant_id` | Hook `tenant-id-validator.sh` bloqueia `CreateModel`/`CREATE TABLE` sem coluna `tenant_id`, com allowlist de tabelas cross-tenant. | ✅ Implementado |
| Aceitar `tenant_id` vindo da tela | Pendente — depende de Foundation F-A começar (request shape define onde o hook procura). Hoje a regra está em INV-TENANT-* e o auditor de Segurança vai pegar em revisão. | ⏳ Pós-Foundation F-A |
| Gambiarras: `@ts-ignore`, `eslint-disable`, `pytest.skip` sem motivo, `assert True`, `type: ignore` solto, `# noqa` solto, `# pragma: no cover` | Hook `anti-mascaramento.sh` (TST-001/002/003) | ✅ Implementado (8 casos no test-runner cobrindo Python/TS/Dart) |
| Mock/dados falsos em arquivo de produção | Hook `mock-in-production.sh` — detecta `FAKE_*`/`MOCK_*`/`*_FAKE`/`*_DUMMY` em caixa alta, comentários `// MOCK` / `# FAKE DATA` / `HARDCODED`, `lorem ipsum`. Ignora `tests/`, `fixtures/`, `seeds/`, `factories/`, `mocks/`, `migrations/`, `examples/`, `docs/`. | ✅ Implementado (11 casos no test-runner) |
| Pular hook pre-commit (`--no-verify`, `-n` combinado, `--no-gpg-sign`) | Hook `block-destructive.sh` bloqueia em `git commit/push/merge/rebase/cherry-pick/am`. | ✅ Implementado (8 casos no test-runner) |
| Compromisso quebrado de invariante (INV-*) | Hook `INV-checker.sh` (PostToolUse) avisa quando código toca path crítico sem referenciar o INV correspondente. | ✅ Implementado |
| Path crítico sem `paths:` no frontmatter da rule | Hook `paths-frontmatter-validator.sh` bloqueia rule sem `paths:` (lazy load) | ✅ Implementado |
| Envelope de evento sem `tenant_id` / `correlation_id` / `event_id` | Hook `bus-envelope-validator.sh` (INV-INT-001/009) | ✅ Implementado |
| Endpoint sem checagem de autorização | Hook `authz-check.sh` (INV-AUTHZ-001) | ✅ Implementado |
| Provisionamento de tenant sem checkpoint atômico | Hook `provisioning-checkpoint-check.sh` (INV-INT-007, modo warning pré-código) | ✅ Implementado |

---

## Grupo 2 — Teste obrigatório como portão (confiabilidade ~95%)

Hook bloqueia commit se o teste do fluxo tocado não foi rodado e não está verde.

| Erro | Defesa |
|---|---|
| Caminho feliz só (sem teste de erro/permissão negada/dado faltando) | Convenção: para cada teste de sucesso, exigir contraparte de falha. Linter custom que conta `*_success` vs `*_failure` no mesmo arquivo. |
| Concorrência, estoque negativo, duplo clique | Testes que simulam 2 usuários ao mesmo tempo usando transação real do banco. Suite de testes de concorrência obrigatória em módulos: estoque, financeiro, comissão, OS. |
| Fluxo de ponta-a-ponta não testado | Suite E2E (robô que simula usuário no navegador) com fluxos críticos mapeados. Hook bloqueia commit em arquivo do fluxo se o E2E correspondente não rodou. |
| Idempotência (gerar financeiro 2x cria 2 contas) | Convenção: toda action que cria registro tem teste que chama 2x e confere se só criou 1. |
| Rollback no meio de fluxo (passo 4 falha, passos 1-3 ficam zumbi) | Testes de transação obrigatórios. Force-fail no passo N e verifica estado consistente. |

**Ponto fraco:** teste mal feito. Mitigação: subagente revisor de testes (Grupo 3) confere qualidade do teste, não só presença.

---

## Grupo 3 — Subagentes revisores especializados (confiabilidade ~80-90%)

Antes do agente principal encerrar a tarefa, um segundo agente especialista revisa a mudança. Se reprovar, o agente principal precisa refazer.

**Cobertura atual (2026-05-17):** projeto opera com 4 auditores Família 5 + 4 subagentes humanos-substitutos. A maior parte dos revisores que esta tabela pedia já está coberta.

| Erro | Defesa | Status |
|---|---|---|
| Não entender projeto antes de mexer | Regra #0 já no `CLAUDE.md` + `AGENTS.md`. Reforçada por revisão do `auditor-qualidade` (pega bypass silencioso). | ✅ Coberto |
| Inventar função/tabela/coluna que não existe | Regra obriga citar `arquivo:linha`. Revisão cabe ao `auditor-qualidade` + `tech-lead-saas-regulado` em mudanças estruturais. | ✅ Coberto |
| Corrigir bug criando falha de segurança | `auditor-seguranca` (Família 5) — bloqueia commit quando diff toca `auth/`, `tenant/`, `financeiro/`, `kms/`, `migrations/`, `.claude/hooks/`. | ✅ Coberto |
| Padrão de resposta da API quebrado | Contract test + revisão pelo `tech-lead-saas-regulado` em mudança de endpoint. Hook específico só faz sentido pós-Foundation F-A. | ⏳ Pós-Foundation F-A |
| Regra fiscal, auditoria, metrológica | `consultor-rbc-iso17025` (ISO 17025/NIT-DICLA/RBC) + `advogado-saas-regulado` (LGPD/fiscal) + `auditor-produto` (PRD non-goals). | ✅ Coberto |
| Solução simples demais em coisa crítica | `auditor-seguranca` pega ausência de transação/audit log em paths sensíveis; `auditor-qualidade` pega ausência de teste; `tech-lead-saas-regulado` revisa design. | ✅ Coberto |
| Solução complexa demais (over-engineering) | `tech-lead-saas-regulado` revisa proporção esforço/uso. Regra: começa simples, complexidade só com 3 usos repetidos. | ✅ Coberto |
| N+1 queries, query sem paginação, índice faltando | Agente revisor de performance e linter específico (Django Debug Toolbar / EXPLAIN ANALYZE) — implementar quando Foundation F-A começar. | ⏳ Pós-Foundation F-A |
| Telas sem integração real com backend | Contract test + `auditor-produto` valida AC binários da US. | ⏳ Pós-Foundation F-A (parte do contract test) |
| Documentação/seed/teste/tipos desatualizados — **DRIFT** | `auditor-drift-docs` (Família 5, criado 2026-05-17) — detecta 8 tipos de drift (D1–D8): pendência fantasma, status incoerente, data relativa, contagem desatualizada, link quebrado, ADR superada, glossário em deriva, self-reference quebrada. Sem poder de veto (consultivo). | ✅ Coberto |

---

## Grupo 4 — Decisões de arquitetura no `AGENTS.md`

Não previnem com hook. Previnem **decidindo bem desde o começo** e mantendo o `AGENTS.md` como lei do projeto.

| Erro | Defesa (decisão a registrar) | Status |
|---|---|---|
| Cada controller responde diferente | Padrão único de resposta de API decidido antes da primeira rota. Documentado com exemplo. Validado por contract test. | ⏳ ADR a criar (mini-ADR) antes da primeira rota |
| Status mudando para trás (ex: "pago" → "rascunho") | Máquina de estados explícita em código + tabela de transições válidas. Validada por teste. | ⏳ ADR-0005 (engine de automações/BPM) trata; specs detalham por módulo |
| Data, fuso, moeda errados | Banco em UTC, frontend mostra BR. Dinheiro em centavos inteiros, tipo `Money` obrigatório. | ⏳ Mini-ADR a criar antes da primeira tabela |
| Auditoria esquecida | WORM em Backblaze B2 + audit log automático. Decidido em AGENTS.md §9. | ✅ Decidido |
| Solução exagerada | Regra: começa simples; complexidade só com 3 usos repetidos. `tech-lead-saas-regulado` revisa. | ✅ Coberto |
| Multi-tenant ambíguo | ADR-0002 (schema-shared + RLS v2 + middleware Django injetando `tenant_id`). | ✅ Decidido |
| Permissões inconsistentes | ADR-0012 (AuthorizationProvider porta unificada). | ✅ Decidido |
| Convenções de nomenclatura | PT em código/docs/commits (D3 do v5 + AGENTS.md §8). Casing snake_case para banco; código segue Django/Flutter idiomático. | ✅ Decidido |

---

## O que NÃO dá pra prevenir 100% (5% que sobra)

Honestidade total:

1. **Regra fiscal/metrológica específica** (validade de certificado RBC, prazo INMETRO, regra nova de NFSe da prefeitura X) — IA não conhece. Precisa estar escrita em spec/AGENTS.md/runbook. Se não tiver, IA inventa.
2. **Decisão de produto** ("aceita desconto acima de 20%?", "esse cliente pode parcelar em 18x?") — exige humano.
3. **Dado real do cliente errado** — IA não tem como saber que o CNPJ X é fraude ou que o cliente Y reclamou ontem.
4. **Sabotagem deliberada** — se um agente está comprometido (prompt injection, supply chain), os hooks são primeira linha de defesa, mas não absoluta.

**Defesa contra esses 4:** revisão humana obrigatória em mudanças de financeiro, fiscal, dados de cliente real e código de segurança. Configurável via regra no `CLAUDE.md` que exige "confirme com Roldão antes de commitar" em pastas específicas (ex: `app/Financeiro/`, `app/Fiscal/`, `app/Auth/`).

---

## Roteiro de implementação — estado atual

### Passo 1 — Hooks Grupo 1 ✅ **APLICADO em 2026-05-17**

12 hooks ativos (`.claude/hooks/`):

1. `block-destructive.sh` — `rm -rf`, `git push --force`, `git reset --hard`, `DROP TABLE`, `TRUNCATE`, `chmod 777`, `curl|bash`, `mkfs`, `dd if=`, **`--no-verify`/`-n`/`--no-gpg-sign`** (adicionado 2026-05-17)
2. `secrets-scanner.sh` — `.env`, `.pem`, `.key`, tokens GH/AWS
3. `_test-runner.sh` — 66 casos cobrindo todos os hooks
4. `INV-checker.sh` — invariantes versionadas
5. `tenant-id-validator.sh` — `.objects.all()` sem filtro + migration sem `tenant_id` (Django/Alembic)
6. `anti-mascaramento.sh` — `assert True`, `pytest.skip` solto, `@ts-ignore`/`eslint-disable`/`# noqa`/`# type: ignore` sem justificativa, `# pragma: no cover`
7. `context-budget.sh` — orçamento de contexto
8. `paths-frontmatter-validator.sh` — rules sem `paths:`
9. `bus-envelope-validator.sh` — envelope de evento (INV-INT-001/009)
10. `authz-check.sh` — endpoint sem checagem (INV-AUTHZ-001)
11. `provisioning-checkpoint-check.sh` — checkpoint atômico (INV-INT-007)
12. **`mock-in-production.sh`** — dados falsos fora de tests/fixtures/seeds/factories/mocks/examples/migrations (adicionado 2026-05-17)

Bateria de testes: **66/66 verde** (validar com `bash .claude/hooks/_test-runner.sh`).

### Passo 2 — Decisões de base no `AGENTS.md` ✅ **APLICADO em parte**

Decididas em ADRs ativas:
- Multi-tenant: ADR-0002 (schema-shared + RLS v2)
- Permissão: ADR-0012 (AuthorizationProvider)
- Stack: ADR-0001 candidata (Django + Flutter + PostgreSQL)
- Auditoria: WORM em B2 (AGENTS.md §9)
- Idioma e casing: PT (D3 + AGENTS.md §8)

**Mini-ADRs a criar antes da primeira linha de código de produto (3 itens):**
- Padrão único de resposta de API (envelope sucesso/erro)
- Tipo `Money` em centavos inteiros
- Data/hora UTC no banco + BR no frontend (`America/Sao_Paulo`)

### Passo 3 — Subagentes revisores ✅ **APLICADO**

4 auditores Família 5 em `.claude/agents/`:
- `auditor-seguranca` — bloqueia commit em paths sensíveis
- `auditor-qualidade` — bloqueia commit por TST-* / mascaramento
- `auditor-produto` — bloqueia merge por AC binário / non-goal
- `auditor-drift-docs` — **NOVO 2026-05-17** — reporta 8 tipos de drift em docs (consultivo, sem veto)

4 subagentes humanos-substitutos:
- `tech-lead-saas-regulado`, `advogado-saas-regulado`, `corretora-seguros-saas`, `consultor-rbc-iso17025`

Pós-Foundation F-A serão criados (não antes — sem código não há o que revisar):
- Revisor de performance (N+1, paginação, índice)
- Revisor de contrato de API

### Passo 4 — Hook de teste obrigatório ⏳ **Pós-Foundation F-A**

Depende de o primeiro código existir. Será PreToolUse(Bash) em `git commit` checando que a suite tocada rodou + verde.

### Passo 5 — Pastas críticas "exigir Roldão" ⏳ **Pós-Foundation F-A**

Pastas concretas (`app/financeiro/`, `app/auth/`, etc.) ainda não existem. Pré-mapeadas em `CODEOWNERS` (D5 — 10 paths).

---

## Pendências e perguntas em aberto

1. ~~**Stack técnica**~~ → cravada candidata em ADR-0001 (Django + Flutter + PostgreSQL); 2 dos 3 portões fechados, Portão 1 diferido (`project_sem_cliente_externo_agora`).
2. **Domínio metrológico** — `consultor-rbc-iso17025` está em `.claude/agents/`; falta carregar specs/referências RBC/INMETRO/NFSe específicas. Bloqueante para auditoria de negócio fiscal.
3. **Limite de "pastas críticas"** — pré-mapeado em CODEOWNERS (D5 — 10 paths); concretizar quando Foundation F-A criar `app/auth/`, `app/financeiro/`, etc.
4. ~~**Estratégia multi-tenant**~~ → ADR-0002 (schema-shared + RLS v2 + middleware Django).
5. **Operação dual Claude + Codex** — hooks rodam em ambos (são scripts shell agnósticos); subagentes Claude não são acessíveis pelo Codex CLI. Decisão: cada CLI usa o que pode, e os auditores no servidor (camada B GitHub Action) são o lastro comum.
6. **3 mini-ADRs pendentes pré-código** — envelope de resposta API, tipo Money, fuso/data. Devem ser escritas antes da primeira tabela/rota.

---

## Histórico

- **2026-05-16** — Documento criado a partir da discussão da sessão. Implementação pendente da escolha de stack.
- **2026-05-17** — Plano aplicado parcialmente: 2 hooks reforçados/criados (`block-destructive` com `--no-verify`/`-n`, novo `mock-in-production.sh`), `_test-runner` estendido pra 66 casos (100% verde), `auditor-drift-docs` criado (`.claude/agents/` + `docs/governanca/auditor-drift-docs-prompt.md`), catálogo de auditores atualizado, drift de status corrigido. Resíduo (revisor de performance, contract test, mini-ADRs API/Money/fuso, Passo 5) fica pra Foundation F-A começar.
