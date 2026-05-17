# Próximos artefatos referenciados (checklist consolidada)

> **Por que existe:** auditoria 4 identificou que os 4 docs do Discovery batch 1 referenciam 21+ documentos que ainda não existem. Sem essa lista, vira "promessa fantasma" — alguém lê um doc, vai procurar a referência, não acha, perde tempo.
>
> **Atualização:** 2026-05-16 — inventário inicial pós-auditoria do batch 1.
> **Quem mantém:** agente atualiza a cada rodada (cria entrada quando novo doc é referenciado em algum lugar; marca ✅ quando o doc passa a existir).

---

## Como ler esta lista

- **Status:** ⏳ pendente | 🟡 em andamento | ✅ existe
- **Prioridade:** 🔴 obrigatório pro MVP | 🟡 próximo | ⚪ lazy/pós-deploy
- **Bloqueia:** o que NÃO consigo fazer enquanto esse artefato não existir

---

## 📋 Inventário (21 artefatos)

### Discovery (Família 0)

| # | Artefato | Caminho | Status | Prio | Referenciado em | Bloqueia |
|---|---|---|---|---|---|---|
| 1 | `personas-detalhadas.md` | `docs/discovery/` | ✅ **criado 17/05/2026** | 🔴 | `dominio-de-negocio.md` §Saída | (resolvido) |
| 2 | `dores-mapeadas.md` | `docs/discovery/` | ✅ **criado 17/05/2026 (batch 3)** | 🔴 | `dominio-de-negocio.md` §Saída + insights da jornada atual | (resolvido — re-rankear pós-Onda 1 de entrevistas) |
| 3 | `jobs-to-be-done.md` | `docs/discovery/` | ✅ **criado 17/05/2026** | 🟡 | `documentos-do-projeto.md` v5 §Família 0 | (resolvido) |
| 4 | `jornada-atual-sem-produto.md` | `docs/discovery/` | ✅ **criado 17/05/2026** | 🔴 | `documentos-do-projeto.md` v5 §Família 0 | (resolvido) |
| 5 | `opportunity-solution-tree.md` | `docs/discovery/` | ✅ **criado 17/05/2026 (batch 3)** | 🔴 | `documentos-do-projeto.md` v5 §Família 0 | (resolvido — alimenta `sintese-final.md`) |
| 6 | `assumption-map.md` | `docs/discovery/` | ✅ **criado 17/05/2026 (batch 3)** | 🔴 | `documentos-do-projeto.md` v5 §Família 0 | (resolvido — 12 LEAPs identificados; validar em `validacao-ativa.md`) |
| 7 | `validacao-ativa.md` | `docs/discovery/` | ⏳ | 🔴 | `riscos.md` (TAM) + `dominio-de-negocio.md` (Portal cliente) | Decisão de seguir/parar |
| 8 | `treinamento-entrevista-roldao.md` | `docs/discovery/` | ⏳ | 🔴 | `documentos-do-projeto.md` v5 §Família 0 | Entrevistas piloto |
| 9 | `entrevistas-clientes.md` | `docs/discovery/` | ⏳ | 🔴 | `documentos-do-projeto.md` v5 §Família 0 | Síntese final |
| 10 | `precificacao-mercado.md` | `docs/discovery/` | ⏳ | 🟡 | `documentos-do-projeto.md` v5 §Família 0 | Modelo de negócio |
| 11 | `spikes-tecnicos/` (3+) | `docs/discovery/spikes-tecnicos/` | ⏳ | 🟡 | `normas-e-regulacao.md` §8.3 | ADR-0001 (stack) |
| 12 | `sintese-final.md` ⭐ | `docs/discovery/` | ⏳ | 🔴 | Tudo | MVP-1 + faseamento + stack + modelo negócio |

### Comum / transversal

| # | Artefato | Caminho | Status | Prio | Referenciado em | Bloqueia |
|---|---|---|---|---|---|---|
| 13 | `glossario.md` | `docs/comum/` | ⏳ | 🔴 | `dominio-de-negocio.md` §Saída | Nomenclatura de tabelas/campos |

### Regras e arquitetura

| # | Artefato | Caminho | Status | Prio | Referenciado em | Bloqueia |
|---|---|---|---|---|---|---|
| 14 | `REGRAS-INEGOCIAVEIS.md` | raiz | ⏳ | 🔴 | `normas-e-regulacao.md` §scope + §8 | Hooks bloqueantes |
| 15 | `faseamento-modulos.md` | `docs/` | ⏳ | 🔴 | `riscos.md` + `dominio-de-negocio.md` §Mapa | Ordem dos N módulos em produção |
| 16 | `adr/0001-stack.md` | `docs/adr/` | ⏳ | 🔴 | R23 + R "Stack inviável" | TUDO pós-stack |

### Segurança / governança

| # | Artefato | Caminho | Status | Prio | Referenciado em | Bloqueia |
|---|---|---|---|---|---|---|
| 17 | `mcp-policy.md` | `docs/seguranca/` | ⏳ | 🔴 | R27 (prompt injection) | MCP em produção |
| 18 | `agente-input-nao-confiavel.md` | `docs/seguranca/` | ⏳ | 🔴 | R27 (prompt injection) | MCP em produção |

### Conformidade

| # | Artefato | Caminho | Status | Prio | Referenciado em | Bloqueia |
|---|---|---|---|---|---|---|
| 19 | `retencao-matriz.md` | `docs/conformidade/comum/` | ⏳ | 🔴 | `riscos.md` (conflito tríplice) + `normas` §8.2 | Resposta a pedidos LGPD |
| 20 | `seguranca-dados.md` | `docs/conformidade/comum/` | ⏳ | 🔴 | `riscos.md` (LGPD vazamento) | Compliance ANPD |
| 21 | `fiscal-contingencia.md` | `docs/conformidade/comum/` | ⏳ | 🔴 | `normas` §8.2 | Operação fiscal |
| 22 | `lgpd-resposta-titular.md` | `docs/conformidade/comum/` | ⏳ | 🔴 | `normas` §8.2 | Direitos do titular |
| 23 | `lgpd-incidente-3-dias-uteis.md` (nome correto — R22) | `docs/conformidade/comum/` | ⏳ | 🔴 | `normas` §8.2 | Runbook de incidente |
| 24 | `nfse-por-municipio.md` | `docs/conformidade/comum/` | ⏳ | 🔴 | `normas` §8.2 | Operação fiscal |
| 25 | `17025-mapping.md` (cláusula → feature) | `docs/dominios/metrologia/modulos/calibracao/` | ⏳ | 🔴 | `normas` §8.2 | Auditoria Cgcre |

### Operação

| # | Artefato | Caminho | Status | Prio | Referenciado em | Bloqueia |
|---|---|---|---|---|---|---|
| 26 | `dr-plan.md` (3 cenários) | `docs/operacao/` | ⏳ | 🔴 | `riscos.md` (Hostinger SPOF) | Pré-deploy |

### ADRs específicas

| # | Artefato | Caminho | Status | Prio | Referenciado em | Bloqueia |
|---|---|---|---|---|---|---|
| 27 | ADR fiscal (BaaS único) | `docs/adr/` | ⏳ | 🔴 | R16 + Auditor 2 sugestão | Pós-stack |
| 28 | `adr/0003-mobile-tecnico-campo.md` | `docs/adr/` | ⏳ | 🔴 | `dominio-de-negocio.md` §Mapa | Pós-stack |
| 29 | **ADR-0000 — Uso de IA** — abstração provider + opt-out dados cliente + IP output + hard cap por tenant + suite de eval baseline + sanitização input não-confiável | `docs/adr/0000-uso-de-ia.md` | ✅ **criado 16/05/2026** | 🔴 | R-027, R-028, R-010, R-031, R-032 | (resolvido) |

---

## Como esta lista evolui

- **Quando um artefato é referenciado em qualquer doc:** entrada nova nesta lista.
- **Quando o artefato passa a existir:** marcar ✅ + remover de "bloqueia" onde aparecer.
- **Revisão obrigatória a cada milestone:** fim de cada rodada do Discovery, antes do `sintese-final.md`, antes de qualquer ADR.
- **Limite:** se essa lista passar de 40 itens, é sinal de que estamos gerando débito documental. Forçar redução.
