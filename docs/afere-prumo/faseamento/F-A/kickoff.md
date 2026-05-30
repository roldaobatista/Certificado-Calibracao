---
owner: <Quem>
revisado-em: 2026-05-28
status: draft
idioma: pt-BR
limite-linhas: 180
proposito: kickoff de Foundation (capacidade transversal — login, multi-tenant, observabilidade) — vem ANTES de qualquer Fase de produto
---

<!--
template: kickoff-foundation.template.md
uso: copiar para docs/faseamento/<F-A|F-B|F-C>/kickoff.md.
referência: ESTRUTURA-PROJETO-NOVO-DO-ZERO.md §1.13.3 (Foundation vs Fase de produto)
distinção:
  - Foundation (F-A, F-B, F-C…) = capacidade transversal sem a qual nenhum módulo funciona (login, multi-tenant, observabilidade, comunicação, identidade).
  - Fase de produto (F-1, F-2…) = grupo de funcionalidades de produto entregues juntas, depende de Foundations.
  - Foundations vêm ANTES. Nenhuma Fase de produto começa com Foundation pendente que ela exige.
par: kickoff-fase.template.md (kickoff de Fase de produto)
saída: finalizacao-fase.template.md (gate PASS ZERO ao fechar)
-->

# Kickoff Foundation <F-A|F-B|F-C> — <NomeDaFoundation>

> **Foundation** = peça transversal. Não é funcionalidade de cliente final. É infraestrutura/capacidade que viabiliza Fases de produto.

## 1. Identidade da Foundation

| Campo | Valor |
|---|---|
| ID | <F-A|F-B|F-C|F-D|...> |
| Nome | <ex: Autenticação multi-tenant; Observabilidade; Identidade> |
| Tipo | <auth|multi-tenant|observabilidade|comunicação|identidade|conformidade|outro> |
| Dono | <slug> |
| Prazo-alvo | 2026-05-28 |
| Bloqueia | <lista de F-N (fases de produto) que não podem começar sem esta Foundation> |

## 2. Por que esta Foundation existe

1-3 parágrafos respondendo:

- Qual capacidade transversal ela entrega?
- Quais Fases de produto seriam impossíveis (ou frágeis) sem ela?
- O que acontece se for adiada?

## 3. Escopo

### 3.1 Inclui

- <componente-1>
- <componente-2>
- <componente-3>

### 3.2 Não inclui (escopo desta Foundation)

- <fora-1> — vai pra <F-X | nunca>.
- <fora-2> — vai pra <F-X | nunca>.

## 4. Decisões fundadoras necessárias

Foundations geralmente exigem ADR. Listar e linkar:

| ADR | Tema | Status |
|---|---|---|
| ADR-NNNN | <ex: estratégia de auth — Cognito vs próprio> | proposta |
| ADR-NNNN | <ex: schema multi-tenant — RLS vs schema-per-tenant> | proposta |

## 5. Invariantes que esta Foundation cria

Foundations frequentemente introduzem INVs novas em `REGRAS-INEGOCIAVEIS.md`. Listar com IDs propostos:

| ID proposto | Regra | Hook que aplicará | Auditor |
|---|---|---|---|
| INV-<area>-NNN | <regra> | <hook.sh> | <auditor> |

## 6. Auditores que esta Foundation exige

Foundation crítica exige auditor próprio (ver `docs/governanca/catalogo-auditores.md`).

| Auditor | Cobertura | Criar nesta fase? |
|---|---|---|
| auditor-<area> | <INV-...> | sim/não — se existe |

## 7. Plano da Foundation (alto nível)

Detalhe em `plan.md` por componente. Aqui só os marcos:

| Marco | Critério | Prazo |
|---|---|---|
| M1 — esqueleto | <ex: middleware de tenant escrito> | 2026-05-28 |
| M2 — integrado | <ex: 1 endpoint usa o middleware> | 2026-05-28 |
| M3 — completo | <ex: 100% dos endpoints com middleware + auditor verde> | 2026-05-28 |

## 8. Quem é cliente da Foundation

Foundation atende **time interno**, não cliente final. Listar consumidores:

- Fase F-1 (módulo X) — depende da capacidade.
- Fase F-2 (módulo Y) — depende da capacidade.

## 9. Serviços críticos tocados por esta Foundation

Declarar quais serviços críticos esta Foundation cria ou altera (em branco = nenhum). Isso amarra a revisão operacional do fechamento (§10).

| Serviço crítico | Tipo de mexida | Dono de operação |
|---|---|---|
| <ex: autenticação; isolamento multi-tenant> | <novo / alterado / nenhum> | <slug> |

## 10. Riscos

| Risco | Impacto | Mitigação |
|---|---|---|
| <ex: complexidade subestimada> | atraso de Fases de produto | spike de 3 dias antes de comprometer escopo |
| <ex: ferramenta upstream muda> | breaking change | pinning + ADR |

## 11. Definição de "pronto" desta Foundation

Critério inegociável de PASS ZERO ao final (gate em `finalizacao-fase.md`):

- [ ] Todos os componentes em §3.1 implementados.
- [ ] INVs em §5 declaradas em REGRAS-INEGOCIAVEIS.md.
- [ ] Hooks e auditores em §5/§6 ativos.
- [ ] ADRs em §4 em status `aceita`.
- [ ] Documentação operacional: runbook(s) em `docs/operacao/runbooks/` quando aplicável.
- [ ] Para cada serviço crítico declarado em §9: indicadores de serviço (SLO) e roteiros de emergência (runbooks) revisados e aprovados pelo dono de operação.
- [ ] Zero achados CRÍTICO/ALTO/MÉDIO em aberto pelos auditores envolvidos.
- [ ] Pelo menos uma Fase de produto consumindo a Foundation, validando que ela serve.

## 12. Próximo passo

Após este kickoff:
1. Criar `plan.md` detalhado de cada componente.
2. Atualizar `.agent/CURRENT.md` apontando para `<F-N>`.
3. Começar implementação. Sem perguntar permissão para cada passo (INV-AGENT-004).
