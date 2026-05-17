# ADR-0000 — Uso de IA no produto e na operação

> **Status:** aceito (16/05/2026)
> **Autor:** Claude Code (orquestrador) + Roldão (decisor)
> **Origem:** Auditor 4 recomendou criar essa ADR como resposta integrada a 5 riscos identificados na auditoria do batch 1 do Discovery (R27, R28, R30, R31, R32). Antes mesmo de escolher stack técnica, as regras de uso de IA precisam estar fixas.
> **Numeração:** 0000 porque é fundadora — antecede até ADR-0001 (stack), que será escolhido com base nesta ADR.

---

## Contexto

O produto e a operação são tocados predominantemente por agentes de IA (Claude Code, Codex CLI, futuros auditores especialistas). Esse modelo concentra riscos novos que ERPs tradicionais não enfrentam:

- **R27** — Prompt injection via input de cliente final (campo de OS, observação de NC, descrição de instrumento) pode mover agente a executar ação indevida em outro tenant.
- **R28** — Anthropic (provedor atual) processa em EUA; cliente farma (Anvisa RDC 658/2022) ou financeiro pode exigir dados em território BR (Res. ANPD 19/2024 sobre transferência internacional).
- **R30** — Custo de token pode explodir não-linearmente se um tenant grande forçar contexto longo recorrente.
- **R31** — Anthropic pode descontinuar/mudar API (Opus 3 → 4.x já mostrou que prompts precisam reaprender em semanas).
- **R32** — Propriedade intelectual do código gerado por IA — sem cláusula clara, vira disputa futura.

Sem decisão prévia sobre como esses 5 riscos são tratados, qualquer escolha de stack/arquitetura herda débito de governança.

---

## Decisão

Adotar 5 princípios fundadores para uso de IA no produto e na operação:

### 1. Abstração obrigatória de provider

- **Toda chamada a LLM passa por uma camada de abstração** (LiteLLM, LangFuse, ou equivalente próprio) — nunca SDK do provedor direto no código de produto.
- **Suite de eval com baseline mantido** — conjunto de prompts críticos com saídas esperadas. Roda em CI a cada mudança de modelo OU de prompt.
- **Provider secundário pré-configurado** (mesmo que inativo): OpenAI, Google Vertex, AWS Bedrock — qualquer um que sirva como fallback. Switchover em ≤4 horas em caso de incidente.
- **Razão:** mitiga R31 (descontinuação) + R30 (negociação de custo entre providers).

### 2. Dados de cliente final não vão pra API por padrão

- **Política `opt-out` por padrão:** dados sensíveis de cliente final do tenant (CPF, CNPJ, valores financeiros, conteúdo de NC, resultados de calibração) **não são enviados pra API de LLM** sem opt-in explícito.
- **Sanitização obrigatória:** campos de texto livre que vão pro LLM passam por scrub de PII (remover CPF, telefone, e-mail, endereço — substituir por placeholder).
- **Auditoria de fluxo de dados:** todo chamada que envia dados de cliente vai pra `governanca/trilha-auditoria-agentes.md` com tag `data-leak-risk`.
- **DPA Anthropic em vigor + cláusula contratual** "dados regulados não passam pela API".
- **Roadmap de modelo BR** (Maritaca, Sabiá) caso cliente exija processamento em território BR.
- **Razão:** mitiga R28 (soberania) + LGPD Res. 19/2024 (transferência internacional).

### 3. Propriedade intelectual do output

- **Todo output gerado por IA é propriedade do Roldão / da empresa do produto.**
- **Cláusula explícita** em qualquer contrato de provedor (Anthropic Terms of Service confirma isso — manter por escrito).
- **Política de não-publicação cega:** código gerado por IA não é publicado em repositório público sem revisão humana e licença explícita.
- **Razão:** mitiga R32 (disputa de IP).

### 4. Hard cap de gasto por tenant

- **Cota diária e mensal de tokens por tenant** configurável.
- **Alertas em 70%, 90%, 100%** da cota.
- **Circuit breaker automático a 100%:** funcionalidades baseadas em IA degradam graciosamente (cai pra fluxo manual ou cache) — não bloqueia o sistema todo.
- **Painel de custo por tenant** acessível ao dono do tenant (transparência).
- **Razão:** mitiga R30 (explosão de custo não-linear).

### 5. Sanitização e segregação de input não-confiável

- **Todo input externo** (campo preenchido por cliente final, e-mail de fornecedor, PR comment, issue, anexo) é classificado como **`regulado-untrusted`**.
- **Agentes podem LER esse input pra fazer trabalho** (resumir, classificar, sugerir).
- **Agentes NÃO podem EXECUTAR ações em frentes sensíveis com base nesse input**, sem aprovação humana explícita:
  - emissão de certificado de calibração
  - emissão/cancelamento de nota fiscal
  - movimentação financeira
  - acesso a KMS / chaves
  - migração de banco
- **Sandboxing por tenant:** agente operando no tenant A não tem leitura de dados do tenant B (RLS PostgreSQL + checagem na camada de aplicação).
- **Red team interno trimestral:** equipe (ou agente auditor) tenta prompt injection nos campos públicos.
- **Razão:** mitiga R27 (prompt injection via cliente final).

---

## Consequências

### Positivas

- **5 riscos críticos mitigados num único movimento** (R27, R28, R30, R31, R32).
- **ADR-0001 (stack)** poderá ser escolhida com critérios objetivos (qual stack permite essa abstração de provider? hard cap por tenant? sanitização nativa?).
- **Onboarding de novo agente/dev fica padronizado** — todo mundo respeita as 5 regras desde o início.
- **Resposta pronta pra cliente que perguntar "vocês usam IA, como protegem meus dados?"** — vira material de marketing.

### Negativas

- **Custo adicional:** abstração de provider (~5-10% de overhead de tokens); sanitização (~3-5% de latência adicional); manutenção de suite de eval.
- **Velocidade reduzida em fase inicial:** desenvolver com essas 5 regras desde o dia 0 é mais lento que ignorar, descobrir o problema e corrigir.
- **Lock-in invertido:** ao usar abstração, perde alguns features específicos de provider (ex: cache de prompt Anthropic-só) — aceitável.

### Trade-offs explícitos

| Trade-off | Escolha tomada | Razão |
|---|---|---|
| Velocidade vs governança | Governança | Roldão não programa; bug regulatório custa multa ou perda de acreditação |
| Provider único (cache otimizado) vs multi-provider (custo+complexidade) | Multi-provider | R31 (descontinuação) é catastrófico em SaaS regulado |
| Dados sempre na API (UX rica) vs dados sanitizados (UX limitada) | Sanitização default | LGPD + Anvisa + cliente farma exigem |
| Hard cap automático (UX para) vs sem cap (custo livre) | Hard cap com degradação graciosa | Sustentabilidade financeira do negócio |

---

## Alternativas consideradas

1. **Single-provider sem abstração** — mais barato e rápido, mas R31 vira existencial. **Rejeitada.**
2. **Sem sanitização (cliente final assume risco)** — viola LGPD se vazar; rejeitada por compliance.
3. **Sem hard cap (cobrar custo do tenant via repasse)** — pode funcionar se houver cláusula contratual, mas vira atrito com cliente. **Adiada** (pode virar opção comercial pós-MVP).
4. **Adiar ADR-IA pra pós-stack** — risco de stack escolhida não suportar (ex: framework que amarra ao SDK Anthropic). **Rejeitada.**

---

## Itens a fazer (consequência operacional desta ADR)

- [ ] Criar `docs/seguranca/mcp-policy.md` aplicando regras desta ADR ao MCP.
- [ ] Criar `docs/seguranca/agente-input-nao-confiavel.md` operacionalizando regra #5.
- [ ] Criar `docs/governanca/eval-baseline.md` documentando a suite de eval.
- [ ] Incluir critério "permite abstração de provider" em ADR-0001 (stack).
- [ ] Cadastrar Anthropic DPA + cláusula de IP no acervo legal.
- [ ] Adicionar regra #5 (segregação) em `REGRAS-INEGOCIAVEIS.md` como INV-AGENT-001.

---

## Revisão

Esta ADR é fundadora. Revisão obrigatória se:
- Provider primário (Anthropic) mudar termos materialmente.
- Aparecer lei BR de IA (PL 2338/2023 já em tramitação na Câmara — vigência prevista 2026-2027).
- Anthropic abrir região BR (resolveria R28 em grande parte).
- Custo de IA cair ≥50% (mudaria balanço de hard cap).

Caso contrário, revisão anual junto com `painel-do-dono.md`.
