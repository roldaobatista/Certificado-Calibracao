---
owner: roldao
revisado-em: 2026-05-30
status: draft
idioma: pt-BR
proposito: documento-ponte — como o Aferê Prumo (camada de IA) encaixa no plano geral do Aferê; entrega para o desenvolvimento do Aferê
relacionado:
  - docs/adr/ADR-0000-uso-de-ia.md
  - docs/adr/ADR-0001-stack-e-integracao-afere.md
  - docs/adr/ADR-0002-multi-empresa-e-armazenamento.md
  - docs/descoberta/sintese-final.md
  - docs/descoberta/agentes.md
afere: C:/projetos/Certificado de calibracao (verificado 2026-05-30)
---

# Encaixe do Aferê Prumo no plano do Aferê

> **O que é este documento:** a ponte entre o projeto `balancas-solution-ia` (descoberta + arquitetura do
> **Aferê Prumo**, a camada de IA) e o projeto `Certificado de calibracao` (o **Aferê**, onde o código vive).
> Decisão fechada (ADR-0001): a IA é um **domínio DENTRO do Aferê**, reusando as portas dele. Logo, a construção
> do Aferê Prumo acontece **no roadmap do Aferê**, seguindo o ritual do Aferê (PRD por módulo → spec → plan →
> tasks → implementação). Este doc é a **entrega para o desenvolvimento do Aferê**.

## 📌 Resumo pro dono

- O Aferê Prumo (IA) vai morar **dentro do Aferê** e usar as peças que o Aferê tem. **Problema:** as peças que a
  IA mais precisa — o **cérebro de IA (LLM)**, o **WhatsApp**, o **motor de automações** e a **busca por
  significado** — estão planejadas pro Aferê, mas **lá na frente** (Wave B/C, depois do sistema básico ficar pronto)
  e **nenhuma foi construída ainda**.
- **Decisão central (precisa de você):** **antecipar** essas peças (construir antes, numa trilha de IA dedicada)
  para o Aferê Prumo sair mais cedo — **ou esperar** o Aferê chegar nelas no ritmo normal (mais demorado).
- **O que NÃO muda:** as fundações de que a IA depende (multi-empresa, login, segurança) **já estão prontas** no
  Aferê. E o Aferê Prumo precisa do Aferê **rodando com dados reais** (clientes, OS, certificados) pra ter sobre o
  que agir — e isso é justamente o que o MVP-1 do Aferê entrega.

## 1. Estado REAL do Aferê (verificado 2026-05-30)

| Fase do Aferê | O que é | Status |
|---|---|---|
| **Foundation F-A** | Multi-empresa + RLS + auditoria | ✅ **fechada** (18/05) |
| **Foundation F-B** | Login + permissões (RBAC + AuthorizationProvider) + MFA | ✅ **fechada** (18/05) |
| **Foundation F-C1** | Endurecimento de segurança (hardening, webhook SSRF) | ✅ **fechada** (24/05) |
| **Foundation F-C2/F-C3** | Observabilidade + resiliência (logs, métricas, circuit breaker) | 🔄 em andamento |
| **Wave A — MVP-1 (18 módulos)** | O sistema útil no dia a dia | 🔄 **4 de 18 fechados**: `clientes`, `equipamentos`, `ordens_servico`, `calibracao` |
| **Wave B (27 módulos)** | Produto completo | ⏳ planejado |
| **Wave C / V2** | Avançado (inclui "BI semântico" com LLM+embeddings) | ⏳ planejado |

> O Aferê é Python 3.12 + Django 5 + DRF + PostgreSQL 16, multi-tenant com **RLS** (defesa em 4 camadas),
> fila **Procrastinate**, hospedagem **Hostinger SP**. Tem **19 portas/adapters** (anti-corrosion layer), mas
> várias ainda **só documentadas, não codadas**.

## 2. Do que o Aferê Prumo depende (dependências reais)

| Peça do Aferê | Pra que a IA usa | Onde está no roadmap do Aferê HOJE | No código? |
|---|---|---|---|
| **Multi-empresa + RLS** (F-A) | Isolar dados por empresa | ✅ pronto | ✅ existe |
| **Login + permissões** (F-B `AuthorizationProvider`) | Quem pode o quê; acesso por audiência | ✅ pronto | ✅ existe |
| **Auditoria + webhook out** | Trilha; integrar n8n/Zapier | ✅ pronto | ✅ existe (`audit`, `webhook_out`) |
| **Fila `QueueProvider` (Procrastinate)** | Rodar transcrição/LLM/RAG nos "fundos" | usada desde F-A | 🟡 parcial (base existe) |
| **Módulos núcleo** (`clientes`, `os`, `equipamentos`, `calibracao`) | A IA age sobre eles | Wave A — 4 fechados | ✅ existem |
| **`LLMGateway` (+Maritaca)** | **Cérebro de linguagem** (entender/redigir/embeddings) | ADR-0059 — Onda 3 do plano-v2 | ❌ **não existe** |
| **`OmniChannelProvider` (WhatsApp)** | **Canal** com o cliente | módulo `comunicacao-omnichannel` — **Wave B.1** | ❌ **não existe** |
| **`DocumentSearchProvider` (busca/RAG)** | **Cérebro de conhecimento** (busca por significado) | `gestao-documental` — Wave B.3 (vetorial só V3) | ❌ **não existe** |
| **`BpmEngineProvider` (motor de automações)** | **Orquestração + base do editor visual** | `automacoes-bpm` — **Wave B.3** (ADR-0005) | ❌ **não existe** |
| **`RuleEngineProvider`** | Regras de negócio (desconto, alçada) | Wave B | ❌ não existe |
| **Transcrição de áudio (STT)** | Voz do cliente → texto (whisper local) | não está no roadmap do Aferê | ❌ a criar (nova porta) |

**Leitura:** as fundações estão prontas; o que falta são as **4 peças de IA** (LLM, WhatsApp, busca semântica,
motor de automações) — todas em Wave B/C do Aferê, **nenhuma construída**. Mais a **transcrição de áudio**, que
nem está no roadmap do Aferê ainda (é capacidade nova que o Aferê Prumo traz).

## 3. O problema de encaixe (a decisão central)

As peças da IA estão majoritariamente **em Wave B/C** do Aferê — **depois** do MVP-1. Dois caminhos:

- **(A) Esperar** o Aferê chegar em Wave B/C no ritmo normal. Simples de planejar, mas **empurra o Aferê Prumo
  pra muito longe** (Wave B só começa após 90 dias de Wave A em produção).
- **(B) Antecipar** as 4 peças de IA numa **trilha dedicada** (uma "Foundation de IA" / "Wave A-IA"), construída
  assim que o núcleo do MVP-1 tiver dados reais — para o Aferê Prumo sair **bem mais cedo**, sem esperar o
  Aferê inteiro.

**🟢 Recomendação do agente: caminho (B), faseado.** Motivos: (1) o Aferê Prumo é um **produto** que o dono quer
validar, não um "extra" de Wave C; (2) as 4 peças são **portas já desenhadas** (anti-corrosion) — antecipá-las não
quebra o plano, só muda a ordem; (3) o Aferê Prumo precisa de **operação real** pra agir — então faz sentido vir
**logo após o núcleo do MVP-1** (clientes/OS/calibração já fechados; faltam certificados/orçamentos/fiscal), quando
já há dado real na Balanças Solution. **A decisão final de roadmap é do dono + time do Aferê.**

## 4. Trilha de IA proposta (ordem de construção, encaixada no Aferê)

> Mapeia as **ondas do Aferê Prumo** (síntese §4.1) contra as **peças do Aferê** a construir. Cada item segue o
> ritual do Aferê: PRD do módulo → spec → plan → tasks → implementação + drill PASS ZERO.

| Passo | Onda do Aferê Prumo | Peça(s) do Aferê a construir antes | Tipo |
|---|---|---|---|
| **IA-0** | Fundação de IA | `LLMGateway` (ADR-0059) + `QueueProvider` completo + **nova porta STT** (whisper local) | Foundation |
| **IA-1** | Onda 0 — Cérebro | `DocumentSearchProvider` com **busca vetorial (pgvector + híbrida)** + ingestão das 1.099 fontes | Foundation/módulo |
| **IA-2** | Onda 1 — Atendimento WhatsApp | `OmniChannelProvider` (WhatsApp Meta direto) + domínio **`copiloto`** (roteador + agente de atendimento + Inbox de aprovação) | módulo |
| **IA-3** | Onda 1.5 — Lembrete de prazo | agente de prazos (usa `calibracao`/`certificados` + OmniChannel) | módulo |
| **IA-4** | Onda 2 — Comercial | agente de orçamento (usa `orcamentos` do Aferê — Wave A) | módulo |
| **IA-5** | Onda 3+ — Financeiro / Metrologia / Gestão | agentes por setor + `BpmEngineProvider` (motor de automações) + **editor visual** sobre ele | módulos |

> **Editor visual (decisão do dono):** entra junto/depois do `BpmEngineProvider` (passo IA-5) — é a **casca visual
> sobre o motor de automações** do Aferê, não um produto do zero.

## 5. O que a IA CRIA de novo no Aferê (domínios + portas)

- **Domínio novo:** `src/domain/copiloto` (+ `src/application/copiloto`) — os agentes por setor, o roteador, a
  Inbox de aprovação humana, as regras de comportamento (configuráveis por empresa).
- **Portas novas/implementações a codar em `src/infrastructure/`:** `llm/` (LLMGateway + Maritaca + LiteLLM),
  `omnichannel/` (WhatsApp), `docsearch/` (busca vetorial), `bpm/` (motor de automações), `stt/` (transcrição local — **porta nova**, não estava no anti-corrosion layer).
- **Reusa direto (não recria):** `multitenant`, `authz`, `audit`, `webhook_out`, `tenant`, `usuario`, e os
  módulos núcleo (`clientes`, `os`, `equipamentos`, `calibracao`, `certificados`, `orcamentos`).

## 6. Entrega para o desenvolvimento do Aferê (o "passar para o outro agente")

Quando esta documentação fechar, o **time/agente do Aferê** recebe:
1. **Este documento** (mapa de encaixe).
2. Os **3 ADRs do Aferê Prumo** (`docs/adr/ADR-0000/0001/0002`) — uso de IA, stack/integração, multi-empresa.
3. A **descoberta** (`docs/descoberta/`) — em especial `agentes.md` (10 fichas-contrato dos agentes = o "PRD" dos
   agentes), `sintese-final.md`, `regras-negocio.md`, `exemplos-saida-ia.md`.
4. O **cérebro coletado** (`dados-reais/_banco/cerebro/`, 1.099 fontes) — insumo do `DocumentSearchProvider`.

O agente do Aferê então: (a) **encaixa a trilha de IA no roadmap do Aferê** (decide a ordem/antecipação com o
dono); (b) abre os **ADRs do Aferê** que faltam para as portas de IA (ADR-0059 LLM já previsto; criar para
STT/omnichannel-antecipado/docsearch-vetorial/bpm); (c) segue o **ritual do Aferê** módulo a módulo.

## 7. ⚠️ A decisão que precisa do dono (antes de passar pro Aferê)

**Quando o Aferê Prumo entra no roadmap do Aferê?**
- **(B1 — recomendado)** Logo após o **núcleo do MVP-1** (quando certificados + orçamentos + fiscal fecharem, somando aos 4 já prontos) — antecipando as peças de IA numa trilha dedicada. Aferê Prumo sai junto com / logo após o MVP-1.
- **(B2)** Em **paralelo** ao restante do Wave A (arriscado — divide o time pequeno).
- **(A)** Só em **Wave B/C** (ritmo normal — Aferê Prumo fica pra bem depois).

> Esta é decisão de **produto + roadmap**, do dono junto com o time do Aferê. Recomendação: **B1**.

## 8. Pendências de documentação do Aferê Prumo (antes de entregar)

- [x] Descoberta (`sintese-final.md` stable) + ADRs aceitos.
- [x] Este mapa de encaixe.
- [ ] **PRD consolidado** (`docs/PRD.md`) — pode ser derivado de `agentes.md` (já tem as 10 fichas) + ondas da síntese.
- [ ] Confirmar com o dono a **decisão da §7** (quando entra no roadmap).
- [ ] `docs/testes/estrategia.md` (pode herdar a do Aferê, que já tem pirâmide + drills).
