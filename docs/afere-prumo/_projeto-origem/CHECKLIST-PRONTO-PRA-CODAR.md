---
owner: roldao
revisado-em: 2026-05-28
status: draft
origem: tasks.md
proximo: kickoff-fase.md
idioma: pt-BR
limite-linhas: 200
proposito: gate unico antes de abrir o primeiro pedido de revisao de codigo de produto
---

<!--
template: CHECKLIST-PRONTO-PRA-CODAR.md
uso: copiar para a raiz do repositório.
referência: ESTRUTURA-PROJETO-NOVO-DO-ZERO.md §C0
proposito: gate único antes de abrir o primeiro PR de código de produto.
            Se qualquer item estiver desmarcado, o repositório NÃO está pronto.
            ESTE é o gate para começar o PROJETO. Para começar uma FASE específica
            dentro do projeto, ver `kickoff-fase.md`.
-->

# Checklist — pronto pra codar — Aferê Prumo

> Todos os itens precisam estar marcados antes do primeiro commit de código de produto.
> Marcar exige link OU caminho de arquivo OU comando que comprova.

> **Este CHECKLIST vs `kickoff-fase.md` — dois gates, dois momentos.**
> - **CHECKLIST (este doc)** é o gate de **PROJETO**: "você está pronto para
>   entrar em desenvolvimento ativo?". Roda **PRIMEIRO**, no setup do projeto
>   inteiro, **uma única vez** antes do primeiro PR de código de produto.
> - **`kickoff-fase.md`** é o gate de **FASE**: "você está pronto para começar
>   ESTA fase específica?". Roda ao iniciar **cada nova fase** (`<F-1>`,
>   `<F-2>`, `<F-3>`, ...).
>
> A ordem real é: CHECKLIST (uma vez) → kickoff da primeira fase → execução →
> kickoff da próxima fase → execução → ... CHECKLIST nunca é re-executado
> por fase; cada fase nova tem seu próprio kickoff.

## Documentação canônica

| Item | O que isso quer dizer |
|---|---|
| [ ] `README.md` existe e está em status `stable` | Tem um arquivo de boas-vindas explicando o que é o projeto, e ele está aprovado (não é rascunho). |
| [ ] `AGENTS.md` existe e está em status `stable` | Tem um arquivo descrevendo como os agentes de IA devem se comportar neste projeto, e ele está aprovado. |
| [ ] `CONTRIBUTING.md` existe | Tem um arquivo explicando como qualquer pessoa pode contribuir/mexer no projeto. |
| [ ] `SECURITY.md` existe | Tem um arquivo explicando como reportar problemas de segurança. |
| [ ] `REGRAS-INEGOCIAVEIS.md` tem ≥10 IDs, cada um com hook OU auditor mapeado | A lista de regras "que nunca podem ser quebradas" existe, tem pelo menos 10 regras, e cada regra tem uma verificação automática ligada nela. |

## Discovery e decisões fundadoras

| Item | O que isso quer dizer |
|---|---|
| [ ] Descoberta: `descoberta/sintese-final.md` em status `stable` | A pesquisa inicial (entrevistas, dor do cliente, validações) terminou e o documento que resume tudo está aprovado. |
| [ ] `ADR-0000` (uso de IA) aceita | A decisão arquitetural número zero — sobre como o projeto usa IA — está registrada e aprovada. |
| [ ] `ADR-0001` (stack) aceita | A decisão arquitetural número um — quais tecnologias o projeto usa — está registrada e aprovada. |
| [ ] Glossário (`docs/glossario.md`) tem ≥20 termos | A lista de termos do projeto (palavras de negócio, siglas) tem pelo menos 20 entradas. |

## Produto e domínio

| Item | O que isso quer dizer |
|---|---|
| [ ] PRD raiz (`docs/PRD.md`) lista módulos com prioridade | O documento principal de produto lista todos os módulos/áreas e diz qual vem primeiro. |
| [ ] `docs/testes/estrategia.md` definida (pirâmide, gates, ferramentas) | Existe um plano de como o sistema vai ser testado — quais robôs simulam o usuário, quantos testes pequenos vs grandes. |
| [ ] Primeira fase (`<F-X>`) tem `spec.md` + `plan.md` + `tasks.md` preenchidos | A primeira fase do projeto tem os 3 documentos: o quê fazer, como fazer, lista de tarefinhas. |
| [ ] `tasks.md` referencia ACs do `spec.md` (coluna `ac-cobertos`) | Cada tarefa diz qual critério de aceite ela cumpre — assim dá pra saber se a tarefa entrega valor real. |
| [ ] `plan.md` referencia ACs do `spec.md` | O plano técnico cita os critérios de aceite que está atendendo — rastreabilidade do que será testado. |
| [ ] Testes 1:1 com ACs existem (em `plan.md` ou pasta de testes) | Para cada critério de aceite, existe um teste automatizado mapeado. |
| [ ] `kickoff-fase.md` da primeira fase está pronto | O documento de abertura da primeira fase está preenchido e revisado. |

## Governança técnica

| Item | O que isso quer dizer |
|---|---|
| [ ] Verificações automáticas que rodam antes de salvar (pre-commit) ativadas com hooks núcleo + extensão: | Antes de cada "salvar no sistema" (commit), uma bateria de checagens roda sozinha. |
| ↳ Núcleo: `block-destructive`, `secrets-scanner`, `validador de cabeçalho dos documentos` (`frontmatter-validator`), `anti-mascaramento`, `override-ledger` | Bloqueia comandos perigosos, procura senhas vazadas, confere cabeçalho dos docs, impede mascarar teste falho, registra exceções. |
| ↳ Extensão: `large-file-blocker`, `merge-conflict-marker`, `lockfile-tampering`, `migration-direction`, `env-file-leak` | Bloqueia arquivo gigante, marca de conflito esquecida, mexida indevida em arquivo de versões, migração na direção errada, vazamento de arquivo de senhas. |
| [ ] CI rodando os mesmos hooks do pre-commit (paridade local↔remoto) + auditores pesados + SBOM (lista de tudo que o sistema usa — bibliotecas, versões) | As mesmas verificações rodam também no servidor da empresa, mais checagens pesadas, mais o relatório de "o que está dentro" do sistema. |
| [ ] Pelo menos 5 auditores configurados em `.claude/agents/` — cada um com golden cases POSITIVO+NEGATIVO obrigatórios | Pelo menos 5 robôs revisores configurados, cada um com exemplo de coisa boa e coisa ruim pra treinar. |
| [ ] `CODEOWNERS` cobre paths críticos (config, migration, hook, auditor, `REGRAS-INEGOCIAVEIS.md`) | Cada arquivo importante tem um responsável definido — ninguém mexe nele sem revisão dessa pessoa. |

## Configuração do repositório

| Item | O que isso quer dizer |
|---|---|
| [ ] `.gitignore` cobre a stack escolhida + `.claude/settings.local.json` | A lista de arquivos "ignorar e não salvar" inclui tudo que a tecnologia usa + arquivo local de configuração. |
| [ ] `.mcp.json` + `docs/governanca/politica-mcp.md` (se o projeto usa MCP) | Se o projeto usa o protocolo MCP (conectores externos), existe a configuração e a política de uso. |
| [ ] `docs/nao-aplica.md` lista camadas puladas com justificativa + gatilho de reavaliação | Tem um documento listando o que decidimos NÃO fazer, por quê, e quando revisar essa decisão. |

## Status aceitos no checklist

**Somente dois estados: `[x]` (atendido com evidência) ou `[N/A]` (decisão de não aplicar — registrada em `docs/nao-aplica.md` com justificativa).**

`[parcial]` NÃO é aceito — ou está pronto com evidência, ou está marcado como N/A com decisão registrada. "Parcial" sem decisão = item ainda em aberto, não pode entrar no PR de fechamento do CHECKLIST.

## Estimativa de tempo por tipo de projeto

Tempo total esperado entre repositório vazio e este CHECKLIST 100% marcado, executado por agente IA. Em projeto solo enxuto, agente classifica automaticamente e segue (0-2 perguntas, não 4 fixas). Para projetos onde houver ambiguidade real, o agente preenche draft das respostas a partir da descoberta e pede confirmação consolidada (1 round). Sem resposta em 24h, agente aplica defaults conservadores documentados em `docs/nao-aplica.md`:

| Tipo de projeto | C0 (raiz) | C1 (descoberta) | C2-C5 (produto) | C6-C8 (operação) | C9 (harness) | **Total** |
|---|---:|---:|---:|---:|---:|---:|
| **Projeto pessoal solo enxuto** (CLI hobby, script) | 20 min | 10 min | 25 min | 10 min | 10 min | **~75 min** |
| **Biblioteca / SDK OSS** | 30 min | 15 min | 40 min | 20 min | 15 min | **~120 min** |
| **CLI tool (lançamento público)** | 25 min | 15 min | 35 min | 20 min | 15 min | **~110 min** |
| **App desktop (Electron/Tauri)** | 30 min | 20 min | 50 min | 35 min | 20 min | **~155 min** |
| **App mobile** | 30 min | 25 min | 55 min | 40 min | 20 min | **~170 min** |
| **SaaS B2B (sem regulação pesada)** | 30 min | 25 min | 60 min | 60 min | 20 min | **~195 min** |
| **SaaS regulado (LGPD/fiscal/saúde)** | 35 min | 30 min | 70 min | 130 min | 25 min | **~290 min** |
| **Pipeline de dados / ETL** | 30 min | 20 min | 50 min | 60 min | 20 min | **~180 min** |
| **Projeto IA/ML (produção)** | 35 min | 35 min | 75 min | 70 min | 25 min | **~240 min** |
| **Embedded / firmware** | 30 min | 25 min | 60 min | 45 min | 20 min | **~180 min** |

> Tempos assumem agente IA capaz, templates copiados de `templates/`, e humano respondendo a 4 perguntas de kickoff (proposito, stack, regulação, comunidade) em até 5 min cada.
> SaaS regulado tem custo extra em C6 (ROPA + retenção + DPIA) e C8 (runbooks + on-call + DR).

## PASS ZERO ao fechar este CHECKLIST

Este CHECKLIST é fechado com critério **PASS ZERO** (zero achados CRÍTICO, ALTO ou MÉDIO em aberto). Itens BAIXO podem ficar abertos com TTL declarado.

- [ ] Auditor-meta rodou sobre este arquivo e reportou zero CRÍTICO/ALTO/MÉDIO.
- [ ] Achados BAIXO documentados em `docs/governanca/registro-de-riscos.md` com TTL.

## Como usar este checklist

1. Marcar cada item APENAS com evidência (link, caminho, comando).
2. Item sem evidência fica desmarcado, mesmo que pareça pronto.
3. Quando todos marcados, mudar `status` no frontmatter para `stable` e abrir o primeiro PR de código.
4. Auditor-meta verifica este arquivo: marcação sem evidência gera finding CRÍTICO.
5. PASS ZERO obrigatório (zero achados CRÍTICO/ALTO/MÉDIO em aberto) — ver acima.

---
> Termos técnicos: ver `GLOSSARIO-ROLDAO.md` na raiz.
