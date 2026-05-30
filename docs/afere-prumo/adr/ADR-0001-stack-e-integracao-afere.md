---
id: ADR-0001
titulo: Definir a stack da camada de IA e como ela se integra ao Aferê
status: aceita
data-proposta: 2026-05-28
data-aceite: 2026-05-29
depende-de: [ADR-0000]
bloqueia-fase: F-A
superseded-by:
owner: roldao
revisado-em: 2026-05-29
idioma: pt-BR
limite-linhas: 250
proposito: escolher a tecnologia de construção da camada de IA e o modo de integração com o ERP Aferê
---

# ADR-0001: Definir a stack da camada de IA e como ela se integra ao Aferê

> ✅ **FASE DE ARQUITETURA FECHADA — o dono declarou "arquitetura fechada" em 2026-05-29.** Este ADR está **ACEITO**.
> Gate de código **LIBERADO** (síntese `stable` + ADR-0001 `aceita`). Decisão final: **IA = domínio dentro do projeto do Aferê**, reusando as 19 portas (ver Decisão + revisão de 2026-05-29).

## Contexto

A camada de IA (este projeto) precisa **consultar e agir** sobre o ERP **Aferê**
(`Certificado de calibracao`), que é a fonte oficial de clientes, equipamentos, OS e
certificados. O Aferê é **Python 3.12 + Django 5.0 + DRF + PostgreSQL 16 + Poetry + Docker**,
multi-tenant com RLS e auditoria WORM, **em construção** (a integração nasce junto — vantagem).
Esta ADR decide **em que tecnologia construir a IA** e **como ela fala com o Aferê**. O phase-gate
bloqueia escrever código em `src/` até esta ADR ser **aceita**.

> **🔗 Baliza já fixada pelo dono (D-PROD-021, 2026-05-29) — esta ADR deve respeitar:** a camada de IA é
> **100% integrada ao Aferê** (fonte única, **sem base de dados paralela**) e a integração é **encapsulada num
> MÓDULO PRÓPRIO dedicado** (anti-corrosion layer; só ele conversa com o Aferê — os agentes não falam direto).
> Isso é **princípio decidido**, não está em aberto. O que **esta ADR ainda vai decidir** — **agora na etapa certa: a
> descoberta C1 foi ENCERRADA pelo dono em 2026-05-29 e este ADR está DESCONGELADO / em aceitação** — é o **COMO**
> desse módulo: qual das opções abaixo (módulo no Aferê × serviço separado × outra stack), contrato (API/DRF × banco
> × eventos), sincronização e autenticação.

## Opções consideradas

### Opção 1: IA como módulo dentro do Aferê (mesmo Python/Django, mesmo repositório)
- **Prós:** integração máxima (reusa modelos, RLS, auth, audit do Aferê); 1 stack só para a equipe/agentes manterem; sem duplicar regras de isolamento multi-empresa; deploy conjunto.
- **Contras:** acopla os dois; a IA pode pesar no ERP; evoluções de IA mexem no repo do ERP.
- **Custo:** baixo (reusa tudo do Aferê).

### Opção 2: IA como serviço separado, em Python, conversando com o Aferê por API interna (DRF)
- **Prós:** mesma linguagem (reuso de conhecimento), mas desacoplado (a IA escala/falha sem derrubar o ERP); contrato de API explícito; pode ter seu próprio ritmo de release.
- **Contras:** precisa de uma API interna bem definida no Aferê; um pouco mais de infra (2 serviços).
- **Custo:** médio.

### Opção 3: IA em outra stack (ex.: Node/TypeScript) consumindo o Aferê por API
- **Prós:** ecossistema rico de ferramentas de agentes; contratos de "tools" tipados.
- **Contras:** **segunda linguagem** para manter (a equipe é pequena e os agentes de IA já tocam o Aferê em Python); duplica modelos/validações; mais atrito de integração.
- **Custo:** alto (duas stacks).

## Decisão do dono registrada — fase de arquitetura ainda ABERTA

> ⚠️ **SUPERADO pela REVISÃO de 2026-05-29 (logo abaixo)** — após a verificação da arquitetura real do Aferê (19 portas prontas), o dono decidiu **IA como domínio DENTRO do Aferê**. O parágrafo a seguir (serviço vizinho) fica como histórico da deliberação.

✅ **Opção 2 — IA como serviço separado (vizinho) em Python, integrado ao Aferê por API interna.**
O dono escolheu o "sistema vizinho, separado" (em vez de morar dentro do Aferê). Motivo confirmado:
se a IA falhar ou ficar cara, **não derruba o ERP** que o cliente usa pra trabalhar; mesma linguagem
do Aferê (Python — sem segunda stack pra equipe/agentes dominarem); contrato de integração explícito,
desenhável agora que o Aferê está em construção. Mantém a baliza D-PROD-021: a integração é encapsulada
num **módulo próprio dedicado** (anti-corrosion layer) — só ele conversa com o Aferê. A ingestão dos
canais é detalhada abaixo.

#### 🔄 REVISÃO pós-verificação da arquitetura real do Aferê (2026-05-29) — recomendação ATUALIZADA
A verificação real do Aferê (ver seção "⚠️ A arquitetura REAL do Aferê" abaixo) achou **19 portas/adapters maduras** que a IA precisa REUSAR (LLMGateway+Maritaca, OmniChannel, DocumentSearch, BpmEngine **visual**, QueueProvider, RLS, Authz, Storage…). Isso **inverte o trade-off** de "serviço separado":
- Reusar 19 portas de um serviço **separado** exigiria o Aferê **expor todas via API** (trabalho enorme) **ou** a IA **reconstruir** o que precisa (duplicação — contra D-PROD-009/021).
- A auditoria cega validou "separado" **sem saber** dessas portas. A salvaguarda que os 10 pediram ("escrita no Aferê só pelas regras dele — RLS/domínio, nunca SQL direto") vale nos **dois** desenhos.

**✅ DECIDIDO pelo dono (2026-05-29) — a camada de IA = DOMÍNIO/apps Django DENTRO do projeto do Aferê** (não serviço de rede separado; revisa a escolha anterior de "serviço vizinho" à luz da arquitetura real do Aferê), que:
1. **Reusa as 19 portas por injeção de dependência** (import direto) — zero reconstrução.
2. **Escreve no Aferê SEMPRE pelas portas/serviços de aplicação** (aplicam RLS, validação, auditoria) — **nunca SQL direto** (preserva a salvaguarda dos 10 arquitetos).
3. **Carga pesada (transcrição, LLM, RAG) em workers de fila Procrastinate DEDICADOS** — isolam a carga e não travam o web do Aferê (entrega o isolamento que motivava "separado", sem duplicar tudo).
4. É o **"módulo próprio dedicado" do D-PROD-021** materializado como **domínio dedicado** (ex.: `copiloto`/`ia`), encapsulado, com kill-switch de custo no LLMGateway.
5. **Reversível:** se um dia precisar operar/escalar separada, a anti-corrosion layer permite extrair — YAGNI agora.

**Por que melhor:** reuso máximo das peças prontas; mais simples para equipe pequena (1 projeto, 1 deploy no VPS Hostinger); segurança herdada (RLS/authz/tenant); alinhamento total com D-PROD-021. O único ganho do "separado" (isolamento de deploy) é coberto pelos workers de fila dedicados + kill-switch.

### Canais e orquestração (input do dono, 2026-05-29 — fase ainda ABERTA)
- **Canais na 1ª versão:** **WhatsApp** (principal) + **e-mail** (Outlook 365) + **agenda**. **Conta Azul / financeiro → onda financeira** (não entra na V1 — confirma a `integracoes-externas.md` INT-004 e a Onda 3 da síntese). Teams/Drive/ClickUp → ondas seguintes.
- **WhatsApp:** caminho **OFICIAL da Meta via parceiro homologado (BSP)** — seguro (sem risco de bloqueio), rápido de ativar por empresa. Descarta apps não-oficiais (risco de ban). A Meta cobra por conversa/template → entra no custo (R-005).
- **Orquestração:** **não usar n8n de terceiro.** O dono optou por **ferramenta de fluxos PRÓPRIA**. **Decisão RATIFICADA pelo dono em 2026-05-29 APÓS a auditoria cega** (8/10 arquitetos desaconselharam o editor visual próprio agora; o dono viu o resultado e **manteve** — é visão de produto, D-PROD-011 "configurável por empresa"). *Implicação registrada: mais escopo inicial (R-001).* **Como construir de forma sã (decisão técnica do agente, incorporando a auditoria):** o editor visual é a **casca sobre uma fundação de configuração-em-dados** — fluxos modelados em **código (grafo de estados tipo LangGraph, com interrupt nativo para a aprovação humana)** + **configuração por empresa em tabelas** (setores ativos, prompts, tom, limiares); o editor visual **edita essas tabelas**, não reinventa o motor de fluxos. Assim o dono tem o editor visual E a arquitetura fica robusta. Escopo detalhado na F-A.
- **Operação financeira:** a IA **opera só o Aferê** (que já faz NFS-e via PlugNotas, boleto/PIX via Asaas, contas a receber e conciliação — D-PROD-022). **Sem Conta Azul** (legado fora do escopo, como o Auvo).

### Refinamentos da auditoria cega (2026-05-29 — incorporados; ver `AUDITORIA-CEGA-ARQUITETURA-2026-05-29.md`)
- **Contratos REST do Aferê co-desenhados AGORA** (o Aferê está em construção — janela barata): **idempotência** nas escritas (chave de idempotência), **webhooks de evento** do ERP, paginação, batch. O anti-corrosion layer encapsula isso.
- **Serviço de IA = Python assíncrono** + **fila via `QueueProvider` do Aferê** (impl real = **Procrastinate** sobre o próprio PostgreSQL — **NÃO Celery+Redis**, como eu/auditoria supusemos; confirmado no `pyproject.toml` do Aferê). Sem Redis extra. Consenso 10/10 da auditoria: serviço separado, mesma linguagem, escrita só via API.
- **Console/painel web de aprovação humana = item de 1ª classe da V1** (7/10) — é onde o human-in-the-loop acontece. Canais V1 passam a ser: WhatsApp + e-mail + agenda + **console de aprovação**.
- **WhatsApp via BSP modelo "own-your-WABA"** (ex.: 360dialog): a conta WhatsApp fica no nome do cliente, portável, sem lock-in nem markup por conversa.
- **Avisos proativos (recalibração) = templates pré-aprovados na Meta** (a janela de 24h + template aprovado da Cloud API restringe mensagem proativa — planejar desde já).

### ⚠️ A arquitetura REAL do Aferê muda o desenho da camada de IA (verificado 2026-05-29 em `C:/projetos/Certificado de calibracao`)
O Aferê é **muito mais maduro** do que eu supunha: tem um **anti-corrosion layer com 19 portas/adapters** prontas. **A camada de IA REUSA essas portas — não reconstrói:**
- **`LLMGateway`** (porta #3): LiteLLM + Anthropic + OpenAI + Google + **`MaritacaProvider`** (`model_class: fast | deep | br-sovereign`) + `embed()`. → O roteador multi-modelo e a abstração de LLM **já existem**; a IA usa esta porta. **Valida nossa aposta em Sabiá** — o Aferê já a previu para "soberania BR".
- **`OmniChannelProvider`** (porta #10): WhatsApp (Cloud API **direto da Meta** na 1ª impl; Twilio BSP como fallback) + e-mail + SMS + web chat — com template Meta, idempotência, HMAC, opt-out, DPA, custo monitorado. → A integração de canais **já existe**. *Divergência: o Aferê vai **Meta direto**, não "via BSP 360dialog" como decidimos — alinhar (ambos oficiais).*
- **`DocumentSearchProvider`** (porta #16): busca + OCR (PgFTS+Tesseract hoje; **busca vetorial planejada para V3**; `ClaudeVisionOcrProvider`). → O "cérebro/RAG" se encaixa aqui; a busca semântica/vetorial que a IA traz é a **evolução desta porta**.
- **`BpmEngineProvider`** (porta #13): **motor de automações com workflow VISUAL** (etapas, branches, paralelo, esperar humano) + DSL YAML, sobre Procrastinate. → **O editor visual do dono se constrói SOBRE este motor** (não do zero) — reconcilia a decisão do dono (D-PROD editor visual) com a auditoria cega.
- **`QueueProvider`** (#7 Procrastinate), **`MultiTenantDiscriminator`** (#9 RLS), **`AuthProvider`** (#6), **`AuthorizationProvider`** (#12), **`StorageProvider`** (#4), **`RuleEngineProvider`** (#14 regras), **`OutboundWebhookProvider`** (#19 — já integra com n8n/Zapier/Make), **`AnalyticsBackend`** (#15) → a IA herda/usa todas.

**Consequência (a decidir com o dono):** a camada de IA é **menos "construir do zero"** e mais **"orquestrar agentes sobre as portas do Aferê"**. Isso pode **refinar** a decisão "serviço vizinho separado": a IA pode viver **mais integrada** (apps/módulos dentro do projeto do Aferê, reusando as portas direto) em vez de um serviço totalmente separado que consome tudo por API. A auditoria cega validou "serviço separado" **sem saber** que o Aferê já tinha essas 19 portas — então essa decisão merece um segundo olhar à luz da arquitetura real.

## Consequências

### Positivas
- Uma linguagem só (Python) → manutenção mais simples para equipe pequena + agentes.
- Integração desenhada junto com o Aferê (sem engenharia reversa de sistema fechado).
- IA isolada → falha/custo da IA não derruba a operação do ERP.

### Negativas
- Precisa definir e versionar a API interna do Aferê (contrato).
- Dois serviços para operar (mitigado por Docker Compose, como o Aferê já usa).

### Reversibilidade
Média. Começar como módulo (Opção 1) e separar depois é factível; trocar de linguagem (Opção 3) seria caro.

## Non-goals
- Não decide o provedor de LLM (ADR-0000) nem o banco vetorial/multi-empresa (ADR-0002).
- Não decide ferramenta de ingestão (n8n vs próprio) — sub-decisão posterior.

## Como validar (gates)
- [ ] Contrato de integração IA↔Aferê definido (quais dados a IA lê/escreve, com que permissão).
- [ ] A IA nunca escreve direto no banco do Aferê sem passar pelas regras dele (RLS/audit).
- [ ] Ambiente sobe com `docker compose` junto do Aferê.
- [x] Decisão confirmada com o dono (módulo vs serviço vizinho) — **serviço vizinho**, 2026-05-29.

## Referências
- `docs/descoberta/integracoes-externas.md` (INT-000 Aferê)
- `C:/projetos/Certificado de calibracao/` (PRD + ARQUITETURA do Aferê)
- ADR-0000 (uso de IA), ADR-0002 (multi-empresa/armazenamento)
