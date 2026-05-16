# Plano de defesas anti-erros de IA — Aferê

> **Status:** plano de implementação pendente.
> **Pré-requisito bloqueante:** escolha da arquitetura/stack técnica do Aferê. Os hooks, linters, scopes e revisores deste plano são específicos por linguagem/framework — só dá pra implementar com a stack decidida.
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
| Migrations destrutivas (`dropIfExists`, `DROP TABLE`, `TRUNCATE`) | Hook `block-destructive.sh` | **Já implementado** (commit `dd967b4`) |
| Senha em código, chave AWS, token GitHub | Hook `secrets-scanner.sh` | **Já implementado** |
| `git push --force`, `git reset --hard`, `rm -rf` | Hook `block-destructive.sh` | **Já implementado** |
| Esquecer filtro por empresa (`Model::all()` sem tenant) | Hook bloqueia gravação de `::all()` / `.findMany()` / `objects.all()` sem comentário justificando. Alternativa preferida: scope global por tenant no ORM, que torna esquecer impossível por design. | Pendente (depende da stack) |
| Aceitar `tenant_id` vindo da tela | Hook procura `request->tenant_id`, `req.body.tenantId`, `request.data.get('tenant_id')` e bloqueia. | Pendente (depende da stack) |
| Gambiarras: `@ts-ignore`, `eslint-disable`, `any`, `catch(e){}` vazio, `phpstan-ignore`, `mypy: ignore` | Hook bloqueia gravação com esses padrões. Whitelist em arquivos legados, se houver. | Pendente (depende da stack) |
| Mock/dados falsos em arquivo de produção | Hook bloqueia array literal de "dados" fora de `*.test.*`, `*fixture*`, `*seed*`, `tests/`. | Pendente (depende da stack) |
| Pular hook pre-commit (`--no-verify`) | Hook `block-destructive.sh` deve incluir esse padrão (verificar se já está coberto). | Verificar |

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

| Erro | Defesa |
|---|---|
| Não entender projeto antes de mexer | Regra #0 já no `CLAUDE.md`. Reforçada por **agente revisor de contexto** que checa se houve grep/leitura dos arquivos afetados antes da mudança. |
| Inventar função/tabela/coluna que não existe | Regra obriga citar `arquivo:linha` ao referenciar código existente. Revisor confere se a citação existe de verdade no repositório. |
| Corrigir bug criando falha de segurança | **Agente de segurança** roda em mudanças de auth, permissão, middleware, validação de input. Cheia padrões OWASP + checklist específico do Aferê. |
| Padrão de resposta da API quebrado | Schema validado em teste automático (contract test) + **agente revisor de contrato API** confere consistência. |
| Regra fiscal, auditoria, metrológica | **Agente "auditor de negócio"** que conhece o domínio metrologia/calibração (RBC, INMETRO, NFSe, validade de certificado). Roda em mudanças no módulo de calibração e financeiro. |
| Solução simples demais em coisa crítica (baixa de estoque direto no controller) | Revisor sinaliza quando código toca estoque/financeiro/comissão sem transação, sem ledger, sem auditoria. |
| Solução complexa demais (event+listener+job+service+repository+DTO pra observação) | Revisor sinaliza over-engineering: pergunta "esse fluxo é executado mais de 3 vezes? precisa mesmo de todas as camadas?". |
| N+1 queries, query sem paginação, índice faltando | Linter específico (ex: Laravel Debugbar / Django Debug Toolbar em modo teste) + **agente revisor de performance**. |
| Telas sem integração real com backend | Revisor frontend valida que botão chama endpoint real, payload bate, erro é tratado. |
| Documentação/seed/teste/tipos desatualizados | Revisor checklist: README, OpenAPI, seeders, factories, testes, tipos compartilhados, traduções, changelog. |

---

## Grupo 4 — Decisões de arquitetura no `AGENTS.md`

Não previnem com hook. Previnem **decidindo bem desde o começo** e mantendo o `AGENTS.md` como lei do projeto.

| Erro | Defesa (decisão a registrar no `AGENTS.md`) |
|---|---|
| Cada controller responde diferente | Padrão único de resposta de API decidido antes da primeira rota. Documentado com exemplo. Validado por contract test. |
| Status mudando para trás (ex: "pago" → "rascunho") | Máquina de estados explícita em código + tabela de transições válidas. Validada por teste. |
| Data, fuso, moeda errados | **Banco em UTC, frontend mostra BR (America/Sao_Paulo).** **Dinheiro sempre em centavos inteiros, nunca float.** Tipo `Money` custom obrigatório. |
| Auditoria esquecida | Toda tabela crítica nasce com colunas `created_by`, `updated_by`, `created_at`, `updated_at` + middleware de audit log automático em models marcados como "auditáveis". |
| Solução exagerada | Regra: começa simples. Sobe complexidade só com 3 usos repetidos do mesmo padrão. |
| Multi-tenant ambíguo | Estratégia escolhida (banco único+coluna, schema separado, banco separado) decidida e documentada. Não muda depois. |
| Permissões inconsistentes | Modelo de permissão único (RBAC, ABAC ou híbrido) decidido. Toda nova feature usa o mesmo. |
| Convenções de nomenclatura | Documentadas no `AGENTS.md`: snake_case para banco, camelCase ou snake_case para código (uma só), nomes em inglês ou pt-BR (um só). |

---

## O que NÃO dá pra prevenir 100% (5% que sobra)

Honestidade total:

1. **Regra fiscal/metrológica específica** (validade de certificado RBC, prazo INMETRO, regra nova de NFSe da prefeitura X) — IA não conhece. Precisa estar escrita em spec/AGENTS.md/runbook. Se não tiver, IA inventa.
2. **Decisão de produto** ("aceita desconto acima de 20%?", "esse cliente pode parcelar em 18x?") — exige humano.
3. **Dado real do cliente errado** — IA não tem como saber que o CNPJ X é fraude ou que o cliente Y reclamou ontem.
4. **Sabotagem deliberada** — se um agente está comprometido (prompt injection, supply chain), os hooks são primeira linha de defesa, mas não absoluta.

**Defesa contra esses 4:** revisão humana obrigatória em mudanças de financeiro, fiscal, dados de cliente real e código de segurança. Configurável via regra no `CLAUDE.md` que exige "confirme com Roldão antes de commitar" em pastas específicas (ex: `app/Financeiro/`, `app/Fiscal/`, `app/Auth/`).

---

## Roteiro de implementação (depois da escolha de stack)

Ordem de retorno:

### Passo 1 — Expandir hooks pra cobrir o Grupo 1 completo
- **Tempo:** 1-2h de implementação
- **Ganho:** ~10 dos 25+ erros viram impossíveis de cometer
- **Inclui:**
  - `::all()` sem tenant
  - `tenant_id` vindo do request
  - Gambiarras (`@ts-ignore`, `any`, `eslint-disable`, `catch vazio`, equivalentes na stack escolhida)
  - Mock em arquivo de produção
  - Verificar/incluir bloqueio de `--no-verify`
- **Validar com:** estender `.claude/hooks/_test-runner.sh` com casos novos. Manter 100% verde.

### Passo 2 — Definir o `AGENTS.md` canônico
- **Tempo:** 1 sessão de decisão com Roldão
- **Ganho:** previne os erros mais caros de desfazer depois (Grupo 4)
- **Decisões obrigatórias antes da primeira linha de código:**
  - Padrão único de resposta de API (com exemplo de sucesso e erro)
  - Multi-tenant: estratégia + onde tenant_id é injetado
  - Permissão: modelo (RBAC/ABAC) e ferramenta
  - Auditoria: quais tabelas, quais colunas, qual middleware
  - Dinheiro: tipo `Money` em centavos inteiros, biblioteca específica
  - Data/hora: UTC no banco, BR no frontend, biblioteca específica
  - Máquina de estados: ferramenta/padrão
  - Nomenclatura: idioma, casing, plural/singular
  - Estrutura de pastas: por domínio ou por camada
  - Testes: ferramentas (unit, integração, E2E, concorrência)
  - Linter/formatter: ferramentas e regras
  - Migrations: convenção (aditivas, reversíveis, com seed de teste)

### Passo 3 — Criar 3 subagentes revisores
- **Tempo:** 2-3h
- **Ganho:** cobre Grupo 3 (~80-90% dos erros de julgamento)
- **Agentes:**
  - **Revisor de segurança** — auth, permissão, middleware, validação de input, OWASP top 10, vazamento multi-tenant
  - **Revisor de negócio** — regra metrológica (RBC/INMETRO), workflow de OS, financeiro, comissão, idempotência, auditoria
  - **Revisor de performance** — N+1, paginação, índice, transação em pontos críticos, query sem filtro de tenant
- **Disparo:** rodam automaticamente antes do agente principal declarar tarefa concluída em arquivos das pastas correspondentes.

### Passo 4 — Hook de teste obrigatório
- **Tempo:** 1h depois que o primeiro código existir
- **Ganho:** cobre Grupo 2 (~95% dos erros de comportamento)
- **Funcionamento:**
  - Hook PreCommit (ou PreToolUse no Bash de `git commit`) inspeciona quais arquivos vão entrar no commit.
  - Para cada arquivo, identifica qual suite de teste cobre. Se a suite não rodou nos últimos N minutos OU rodou e não está verde, bloqueia.
  - E2E obrigatório se o arquivo é de fluxo crítico mapeado.

### Passo 5 — Marcar pastas críticas com "exigir Roldão"
- **Tempo:** 15min
- **Ganho:** rede de segurança final pros 5% que IA não cobre
- **Configuração:** regra no `CLAUDE.md` / `AGENTS.md` listando pastas como `app/Financeiro/`, `app/Fiscal/`, `app/Auth/`, `db/migrations/` com instrução "antes de commitar mudança aqui, confirme com Roldão e mostre diff explicado em linguagem de negócio".

---

## Pendências e perguntas em aberto

1. **Stack técnica do Aferê** — bloqueia o plano todo. Critérios de decisão a serem definidos pelo Roldão.
2. **Domínio metrológico** — coletar spec/referência das regras RBC, INMETRO, NFSe relevantes pra alimentar o agente "auditor de negócio". Sem isso, o agente vai inventar.
3. **Limite de "pastas críticas"** — definir lista exata quando o produto começar a tomar forma.
4. **Estratégia multi-tenant** — banco único + coluna `tenant_id`, schema por tenant, ou banco por tenant. Decisão impacta hooks, scopes, backup, custos.
5. **Operação dual Claude + Codex** — os hooks rodam em ambos? Os subagentes revisores são compartilhados ou cada CLI tem o seu? (memória `project_dual_tooling.md` tem contexto)

---

## Histórico

- **2026-05-16** — Documento criado a partir da discussão da sessão. Implementação pendente da escolha de stack.
