# Documentos do projeto Aferê (v5)

> **Pra que serve:** mapa de TODOS os documentos que o projeto precisa pra funcionar 100% tocado por agentes de IA, sem o Roldão precisar virar programador.
>
> **Status:** ✅ existe | ⏳ falta criar | 🟡 parcial | ❌ removido
> **Prioridade:** 🔴 MVP-obrigatório | 🟡 próximo | ⚪ lazy
>
> **Atualização:** 2026-05-16 (v5 — incorpora 2ª auditoria de 10 agentes + revelação "founder is customer" + escopo de N módulos a descobrir)

---

## ⚠️ AVISO IMPORTANTE — Nome, escopo, contagem

### Nome "Aferê" = PROVISÓRIO
Não comprar `afere.com.br` ainda. Decisão final adiada até antes de: domínio, código com slug `afere`, primeiro cliente externo, INPI.

### Escopo real
**ERP COMPLETO de gestão para empresas de assistência técnica + calibração.** **N módulos a descobrir** (mín 6 confirmados; total real é saída do discovery — pode ser 11, 21 ou 50).

6 módulos hoje confirmados: CRM, Financeiro de alto nível (NF-e/NFS-e, conciliação, etc.), Orçamentos, Chamados, Ordens de Serviço, Calibração (ISO 17025 — diferencial central).

### Founder is customer ⭐
Roldão É o primeiro cliente. Tem empresa de assistência técnica + calibração rodando hoje.
- **Vantagem:** dor real validada, acesso a feedback 24/7.
- **Risco grave:** customização disfarçada de produto. Mitigação obrigatória = Família 0 Discovery rigorosa, incluindo entrevistas com OUTRAS empresas e OPERADORES (não só donos).

### Fase atual
Pré-discovery. MVP-1 e contagem final de módulos serão **saídas do discovery**, não premissas.

---

## 🧩 Princípio fundador da v5: estrutura híbrida por DOMÍNIO → MÓDULO

A v4 propôs `docs/modulos/<modulo>/`. Com N podendo ser 50+, isso vira labirinto. v5 adiciona **camada por DOMÍNIO acima de módulo**:

```
docs/
├── comum/                          ← transversal a todos os domínios e módulos
└── dominios/
    └── <dominio>/                  ← agrupador (exemplos a confirmar no discovery):
        ├── README.md               ← visão do domínio, lista de módulos
        └── modulos/
            └── <modulo>/
                ├── glossario.md
                ├── prd.md
                ├── modelo-de-dominio.md
                ├── contratos/{ui,api,exports}.md
                ├── personas.md
                └── metricas.md
```

**Exemplos de domínios** (saída do discovery confirma):
- Comercial — CRM, Orçamentos, Pedidos, Contratos, Comissões...
- Operação — OS, Chamados, Agenda, Estoque, Técnico de campo...
- Financeiro — Contas a pagar/receber, Fluxo de caixa, Conciliação, NF-e/NFS-e...
- Metrologia — Calibração ISO 17025, Padrões, Rastreabilidade, Certificados...
- Suporte/Plataforma — RH, Permissões/RBAC, Configurações, Tenants...

**Por quê camada de domínio:**
- Acomoda 6 ou 50 módulos sem refator
- Compliance/contratos/eventos costumam ser por domínio, não por módulo
- Agente carrega "domínio em foco" sem puxar 50 pastas

---

## Por que este projeto precisa de mais documento que um projeto normal

Projeto normal tem programador humano. Agente de IA começa do zero a cada conversa — se decisão não está escrita, ele inventa, e a invenção muda toda vez. Documento = trilho.

---

## 6 princípios + 2 regras mestres

1. Documento = estado compartilhado.
2. Spec gera código (spec-as-source).
3. Conciso vence completo (CLAUDE.md/AGENTS.md ≤ 200 linhas).
4. Fases de 5–15 min com critério binário.
5. Non-goals explícitos.
6. IDs rastreáveis (`US-<MOD>-NNN` → `AC-<MOD>-NNN-N` → `T<MOD>NNN` → commit).

**Regra mestre 1:** regra crítica vira **hook**, não doc.
**Regra mestre 2 (NOVA, da auditoria):** **fonte única por tipo de informação**; outros docs referenciam por ID, não duplicam.

---

## 5 decisões fundadoras

| # | Decisão | Detalhe |
|---|---------|---------|
| **D1** | Adotar **Spec Kit** | Framework leve. |
| **D2** | **Spec-as-source** | Spec PT é a verdade. |
| **D3** | **Nomenclatura híbrida** | PT em tudo, exceto 7 arquivos de ferramenta. |
| **D4** | **Devcontainer** | Após ADR-0001. |
| **D5** | **CODEOWNERS expandido** (revisada v5) | Não só 5 paths "anti-bypass"; agora também 5 pastas críticas de ERP financeiro: `financeiro/`, `auth/`, `tenant/`, `kms/`, `migrations/`. Auditor 1 alertou: 5 paths originais é fraco demais pra ERP financeiro. |

**Decisão NOVA (não numerada — saiu da interrupção do Roldão em 2026-05-16):**
> **Discovery rigorosa não se reduz por argumento "lean".** Família 0 mantém os 11 artefatos originais + 4 sugeridos pelo Auditor 6 = **15 artefatos**. Mitigação obrigatória do risco "founder is customer".

---

## Síntese das 2 auditorias

**Auditoria 1 (sobre v2, 2026-05-16):** 10 auditores apontaram 7 ajustes obrigatórios, incorporados na v3.

**Auditoria 2 (sobre v4, 2026-05-16):** 10 auditores, escopo já corrigido (ERP de 6+ módulos). Convergência fundamental: **escopo grande demais sem faseamento e validação externa**. Ajustes incorporados na v5:

| Ajuste | Vindo de |
|---|---|
| Multi-tenancy como ADR-0002 obrigatório | A1, A3, A4, A7 |
| `acionamento-agente.md` (watchdog) promovido ⚪ → 🔴 | A4 |
| `incidente-postmortem.md` (template) promovido ⚪ → 🔴 | A4 |
| `capacity-planning.md` novo 🔴 | A3, A4 |
| `contingencia-fiscal.md` separado de fiscal.md, 🔴 | A4, A5 |
| `multi-tenant-ops.md` novo 🔴 | A1, A4 |
| `seguranca/agente-input-nao-confiavel.md` novo 🔴 | A1 |
| `docs/INDICE.md` + `docs/INDEX.yaml` novos 🔴 | A7, A8 |
| `conformidade/comum/retencao-matriz.md` novo 🔴 | A1, A4, A5 |
| `seguranca-dados.md` promovido 🟡 → 🔴 (ANPD 72h) | A5 |
| Quebrar `padroes-tecnicos.md` em 8 docs | A3 |
| Hierarquia de regras (REGRAS = fonte única) | A7, A8 |
| Materializar Família 5 — 3 auditores com prompt+trigger+veto reais | A10 |
| `docs/tutoriais/dono/` (Diátaxis tutorial pro Roldão) | A8 |
| `docs/modulos/_TEMPLATE/` + `docs/CONVENCOES-DOC.md` | A8 |
| ADR-0003 mobile-tecnico-campo obrigatório | A3 |
| Família 6 calibração: cláusulas ISO 8.5/8.6/8.7 | A5 |
| Família 0 expandida: +4 artefatos (OST, assumption-map, jornada-atual, validacao-ativa) | A6 |
| Família 0: `treinamento-entrevista-roldao.md` | A2 |
| Camada por DOMÍNIO acima de módulo (esta v5) | A3, A8 |
| CODEOWNERS expandido | A1 |

---

## As 8 famílias de documento (v5)

### Família 0 — Discovery (NOVA na v3, EXPANDIDA na v5) ⏳

**15 artefatos** (11 originais + 4 do Auditor 6). Bloqueia todas as outras famílias do MVP até `sintese-final.md` ficar pronta.

| Artefato | Prio | Quem produz | O que contém |
|---|---|---|---|
| `concorrentes.md` | 🔴 | Agente | Bling, Tiny, Omie, Conta Azul, Granatum + nichos calibração. Feature matrix, preço, gaps. |
| `normas-e-regulacao.md` | 🔴 | Agente | ISO 17025, RBC, NF-e/NFS-e por município, LGPD, open banking, PCI. |
| `treinamento-entrevista-roldao.md` (NOVO) | 🔴 | Agente | Roteiro literal por persona, perguntas proibidas (sugestivas), template ata, gravação. Roldão treina em 2 entrevistas piloto antes de valer. |
| `entrevistas-clientes.md` | 🔴 | Roldão + Agente sintetiza | **3 ondas** (Auditor 6): onda 1 = 3 donos de OUTRAS empresas (problema), onda 2 = 6 operadores (3 perfis: atendente, técnico, financeiro), onda 3 = 3 entrevistas de validação de solução com protótipo de papel. Total 12, em 3 ciclos. |
| `dores-mapeadas.md` | 🔴 | Agente | Métrica de priorização **expandida** (Auditor 6): agudez × frequência × disposição a pagar × **SOLVABILITY** (cara de resolver?) × **REACH** (quanto mercado tem essa dor?) × **evitabilidade** (workaround manual aceitável?). |
| `jobs-to-be-done.md` | 🟡 | Agente | O que cada perfil "contrata" o software pra resolver. |
| `personas-detalhadas.md` | 🔴 | Agente | Dono, atendente, técnico de campo, financeiro, vendedor, metrologista. Goals/frustrations/jornada. |
| `dominio-de-negocio.md` | 🔴 | Agente | Como uma assistência técnica + laboratório funciona. **Base do glossário comum.** Mapeia também os N módulos prováveis e seus domínios. |
| `jornada-atual-sem-produto.md` (NOVO) | 🔴 | Agente + Roldão | Como SUA empresa + outras resolvem HOJE (planilha? Bling+WhatsApp? caderno?). Mapeia status quo antes de propor solução. |
| `opportunity-solution-tree.md` (NOVO) | 🔴 | Agente | Teresa Torres. Hierarquia outcome → opportunities → solutions → experiments. Sem isso, dores viram lista plana. |
| `assumption-map.md` (NOVO) | 🔴 | Agente + Roldão | David Bland. 4 quadrantes (desejabilidade/viabilidade/factibilidade/ética) × confiança (sei/não sei). Destaca leap-of-faith. |
| `validacao-ativa.md` (NOVO) | 🔴 | Roldão + Agente | Smoke test (fake-door landing), Willingness-to-Pay test, carta-de-intenção assinada de 3+ empresas. Auto-reportado em entrevista mente. |
| `precificacao-mercado.md` | 🟡 | Agente | Per-user / per-módulo / flat / %. Range por porte. |
| `spikes-tecnicos/` | 🟡 | Agente | POCs: emitir NF-e em município com padrão próprio, integração bancária, cálculo de incerteza, XML INMETRO, multi-tenant isolation. |
| `riscos.md` | 🔴 | Agente + Roldão | Regulatório, técnico, mercado, time, **customização disfarçada** (founder is customer). |
| `sintese-final.md` ⭐ | 🔴 | Agente + Roldão | **Saídas:** cliente ideal, **N total de módulos**, plano de **faseamento** (qual MÓDULO-1, MÓDULO-2... entra em produção), modelo de negócio (SaaS multi-tenant vs on-prem), stack candidate, mobile sim/não. Trava critério de saída antes de começar (nº mín entrevistas, saturação documentada, leap-of-faith validados). |

---

### Família 1 — Contrato dos agentes 🟡

| Doc | Status | Prio | O que é |
|-----|--------|------|---------|
| `CLAUDE.md` | ✅ | 🔴 | Só adendos de harness Claude Code. ≤ 150 linhas. |
| `AGENTS.md` | ⏳ | 🔴 | Canônico de produto/arquitetura. ≤ 250 linhas. |
| `.claude/settings.json` | ✅ | 🔴 | |
| `.claude/hooks/` | ✅ | 🔴 | + anti-mascaramento + context-budget + INV-checker + tenant-id-validator + paths-frontmatter-validator |
| `.claude/agents/` | ⏳ | ⚪ | |
| `.claude/skills/` | ⏳ | ⚪ | |
| `.claude/commands/` | ⏳ | ⚪ | |
| `.claude/rules/` | ⏳ | 🟡 | `paths:` frontmatter validado por hook |
| `.mcp.json` | 🟡 | 🔴 | |
| `docs/roteamento-dual.md` | ⏳ | 🟡 | Fronteira AGENTS.md vs CLAUDE.md + roteamento Claude/Codex + quando 3 auditores entram. |
| `docs/orcamento-contexto.md` | ⏳ | 🔴 | Teto **em tokens reais** (não linhas — Auditor 7) + hook que tokeniza. |
| `docs/INDEX.yaml` (NOVO) | ⏳ | 🔴 | Machine-readable: `{path, módulo, dominio, tokens_estimados, carrega_quando}`. Hook em SessionStart lê INDEX + CURRENT.md e **injeta só subset necessário** via `@path`. |

---

### Família 2 — Produto (híbrida 3 níveis: comum → domínio → módulo) ⏳

#### Comum (transversal)
| Doc | Prio | Conteúdo |
|-----|------|----------|
| `docs/comum/glossario.md` ⭐ | 🔴 | Termos transversais (cliente, fatura, usuário, permissão, tenant). Coluna "se você vir isto na tela/log, significa…" — tradutor PT↔EN de campo. |
| `docs/prd.md` | 🔴 | Visão consolidada do produto: o que é, pra quem, dor, escopo MVP-1 (saída discovery), non-goals. |
| `docs/comum/personas.md` | 🔴 | Personas transversais (dono, gerente). Específicas vão no módulo. |
| `docs/painel-do-dono.md` | 🔴 | Índice navegável pro Roldão. Aviso visual quando agente toca um dos 10 paths CODEOWNERS. Regra de priorização entre domínios (cliente pagante > prazo legal > débito técnico > melhoria) — Auditor 2. |
| `docs/como-os-agentes-trabalham-pra-mim.md` | 🔴 | 1 página PT-BR puro. |
| `docs/MAPA-DO-DONO.md` (NOVO) | 🔴 | Lista numerada dos **7 docs que o Roldão obrigatoriamente lê/aprova**: síntese-discovery, prd, painel-do-dono, status-semanal, go-live-checklist, caminho-reclamacao, changelog. Resto marcado "uso interno dos agentes". (Auditor 2) |
| `docs/comum/metricas-sucesso.md` | ⚪ | Lazy. |

#### Por domínio (criar quando domínio entrar no faseamento)
| Doc por domínio | Prio | Conteúdo |
|---|---|---|
| `docs/dominios/<dominio>/README.md` | 🔴 | Visão do domínio, lista de módulos, fronteiras com outros domínios. |
| `docs/dominios/<dominio>/personas.md` | 🟡 | Personas específicas do domínio. |

#### Por módulo (criar quando módulo entrar no faseamento; ver `_TEMPLATE/`)
| Doc por módulo | Prio | Conteúdo |
|---|---|---|
| `glossario.md` | 🔴 (no faseamento) | Termos específicos. Não duplicar comum. Hook valida. |
| `prd.md` | 🔴 | User stories `US-<MOD>-NNN` + AC Given-When-Then + non-goals. |
| `personas.md` | 🟡 | Papéis específicos (técnico de campo pra OS; metrologista pra calibração). |
| `metricas.md` | ⚪ | Lazy. |

---

### Família 3 — Arquitetura técnica + Segurança ⏳

#### Raiz (alta visibilidade)
| Doc | Prio | O que é |
|-----|------|---------|
| `REGRAS-INEGOCIAVEIS.md` | 🔴 | **Fonte única de regras críticas.** Funde INVARIANTES + TESTES + SECURITY com IDs `INV-NNN` (negócio), `INV-TENANT-NNN` (multi-tenancy), `TST-NNN` (regras de teste), `SEC-NNN` (segurança). Outros docs **citam IDs, não duplicam texto**. Cada regra tem hook que valida. |
| `CONTRIBUTING.md` | 🟡 | Fluxo do AGENTE. |
| `ARQUITETURA.md` | 🟡 | 1 página apontando pra `docs/arquitetura/`. |

#### Arquitetura
| Doc | Prio | O que é |
|-----|------|---------|
| `docs/arquitetura/overview.md` | 🟡 | Code map, entry points, boundaries (Auditor 3). |
| `docs/arquitetura/cross-cutting/erro.md` | 🟡 | NOVO — Auditor 3 quebrou em 8. |
| `docs/arquitetura/cross-cutting/log.md` | 🟡 | |
| `docs/arquitetura/cross-cutting/retry.md` | 🟡 | |
| `docs/arquitetura/cross-cutting/timeout.md` | 🟡 | |
| `docs/arquitetura/cross-cutting/idempotencia.md` | 🟡 | |
| `docs/arquitetura/cross-cutting/transacao.md` | 🟡 | |
| `docs/arquitetura/cross-cutting/auth-rbac.md` | 🟡 | |
| `docs/arquitetura/cross-cutting/validacao.md` | 🟡 | |
| `docs/comum/integracoes-inter-modulos.md` | 🔴 | NOVO — Auditor 3. Contratos entre domínios/módulos (eventos: `OSConcluida` → quem consome, schema versionado, idempotência, ordem). |
| `docs/comum/governanca-modelo-comum.md` | 🔴 | NOVO — Auditor 3 + 8. Critério explícito de promoção/rebaixamento (ex: "entidade é comum se ≥2 módulos usam SEM extensão"); processo de versionamento. |
| `docs/CODEMAP.md` | ⚪ | Lazy. |

#### ADRs
| Doc | Prio | O que é |
|-----|------|---------|
| `docs/adr/0001-stack.md` ⭐ | 🔴 (pós-discovery) | Stack escolhida com base na síntese final. |
| `docs/adr/0002-multi-tenancy.md` (NOVO) | 🔴 | Schema-per-tenant vs row-level security (RLS PostgreSQL) com benchmark em VPS KVM 4. Auditor 1 + 3 + 4 + 7. |
| `docs/adr/0003-mobile-tecnico-campo.md` (NOVO) | 🔴 | PWA vs React Native vs Capacitor. Auditor 3. |
| `docs/adr/0004+.md` | 🟡 | 1 por decisão nova. |

#### Segurança
| Doc | Prio | O que é |
|-----|------|---------|
| `docs/seguranca/mcp-policy.md` | 🔴 | Threat model do MCP: allowlist tools, defesa contra prompt injection via PR/issue. |
| `docs/seguranca/agente-input-nao-confiavel.md` (NOVO) | 🔴 | Auditor 1. Todo input externo (PR comment, issue, email, anexo de cliente) classificado como "regulado-untrusted"; agentes podem ler mas **não podem executar ações em financeiro/KMS/migrations** sem aprovação humana explícita. |
| `docs/seguranca/supply-chain.md` | 🔴 | Lockfile, SBOM, allowlist registries, hook "pacote novo = ADR". |
| `docs/seguranca/classificacao-dados.md` | 🟡 | Público/interno/confidencial/regulado. |
| `docs/comum/isolamento-multi-tenant.md` (NOVO) | 🔴 | Auditor 1. INV-TENANT-001 ("toda query SQL/ORM contém `tenant_id` no WHERE — enforced por linter") + SEC-TENANT-001 ("RLS ativa em todas tabelas de cliente"). |
| `docs/comum/integracoes-externas/` (NOVO) | 🟡 | Auditor 3. Pasta com 1 doc por parceiro (SEFAZ, Pluggy/Belvo, Bling/Tiny pra migração, gateway pagamento, e-mail transacional, WhatsApp Business). Cada: auth, retry, circuit breaker, fallback, custo/mês. |

#### Por domínio/módulo (específico)
| Doc do módulo | Prio | Conteúdo |
|---|---|---|
| `docs/dominios/<dominio>/modulos/<modulo>/modelo-de-dominio.md` | 🟡 | Entidades específicas. |
| `docs/dominios/<dominio>/modulos/<modulo>/contratos/{ui,api,exports}.md` | 🟡 | Específicos do módulo. |
| `docs/dominios/<dominio>/modulos/<modulo>/adr/NNNN-<decisao>.md` | 🟡 | ADRs específicas. |

---

### Família 4 — Operação ⏳ (REORGANIZADA — vários docs promovidos)

| Doc | Prio | Mudança |
|-----|------|---------|
| `docs/operacao/runbook.md` | 🟡 | |
| `docs/operacao/backup-restore.md` | 🟡 | + Distinguir trilha imutável (eventos) vs estado mutável (documentos fiscais corrigíveis). Crypto-shredding por tenant pra LGPD. |
| `docs/operacao/dr-plan.md` | 🔴 | **PROMOVIDO.** 3 cenários explícitos (Auditor 4): (a) falha de serviço RTO 15min; (b) VM corrompida RTO 1h; (c) Hostinger BR fora RTO 4h via provedor secundário (Magalu/Oracle/AWS sa-east-1) com IaC pronto + ensaio trimestral. |
| `docs/operacao/observabilidade.md` | 🔴 | **PROMOVIDO.** SLO **por módulo** (Auditor 4): Financeiro 99.95%, Calibração emissão 99.9%, CRM 99.5%. Não SLO único pra ERP. |
| `docs/operacao/deploy.md` | 🟡 | |
| `docs/operacao/go-live-checklist.md` | 🔴 | **PROMOVIDO.** |
| `docs/operacao/acionamento-agente.md` (NOVO 🔴) | 🔴 | **PROMOVIDO de ⚪.** Watchdog: alerta Grafana/Axiom → webhook → spawn agente Claude/Codex com contexto incidente → escalation se não resolver em N min → humano (Roldão) WhatsApp/SMS. Sem isso, 1º deploy 24/7 cai sexta 19h e fica até segunda 8h. |
| `docs/operacao/incidente-postmortem.md` | 🔴 | **PROMOVIDO de ⚪.** Template precisa existir ANTES do 1º incidente. |
| `docs/operacao/capacity-planning.md` (NOVO 🔴) | 🔴 | NOVO. Tenants/VPS, teto vertical KVM 4, plano de sharding por tenant. |
| `docs/operacao/multi-tenant-ops.md` (NOVO 🔴) | 🔴 | NOVO. Runbook "reiniciar/restaurar/suspender tenant X sem afetar Y". Debugging com tenant_id obrigatório em todo log/trace. LGPD exclusão (15 dias) via crypto-shredding. |
| `docs/operacao/maintenance-windows.md` (NOVO 🔴) | 🔴 | NOVO. Regra: zero deploy em dia útil 8h–20h salvo P0. Janela padrão sáb 2h–5h BRT. |
| `docs/operacao/rotacao-credenciais.md` | ⚪ | |
| `docs/operacao/provisionamento.md` | ⚪ | |
| `CHANGELOG.md` (raiz) | 🔴 | Keep a Changelog 1.1. |

---

### Família 5 — Governança IA 🟡 (MATERIALIZAR os 3 auditores — Auditor 10)

| Doc | Status | Prio | Conteúdo |
|-----|--------|------|----------|
| `docs/governanca/catalogo-auditores.md` | ⏳ | 🔴 | **MATERIALIZADO** (sai de vaporware): cada auditor tem prompt versionado, trigger (evento + condição), set mínimo de contexto, poder de veto materializado (bloqueia merge? bloqueia deploy? gera issue?), output destination. |
| `docs/governanca/auditor-seguranca-prompt.md` | ⏳ | 🔴 | NOVO. Prompt completo do Auditor 1. |
| `docs/governanca/auditor-qualidade-prompt.md` | ⏳ | 🔴 | NOVO. Prompt completo do Auditor 2. |
| `docs/governanca/auditor-produto-prompt.md` | ⏳ | 🔴 | NOVO. Prompt completo do Auditor 3. |
| `docs/governanca/limites-autonomia.md` | ⏳ | 🔴 | 5 casos-limite + **limites $/dados/SLA explícitos** (Auditor 2). |
| `docs/governanca/status-semanal.md` | ⏳ | 🔴 | Auto-gerado. Topo: "essa semana o módulo X precisa de você por Y" (escolha forçada, não buffet — Auditor 2). |
| `docs/governanca/auditoria-decisoes-autonomas.md` (NOVO) | 🔴 | Auditor 2. Lista filtrada do que agentes decidiram SEM consultar Roldão. |
| `docs/governanca/caminho-reclamacao.md` | ⏳ | 🟡 | |
| `docs/governanca/metricas-operacao-agentes.md` | ⏳ | 🟡 | Tokens, retrabalho, tempo entrega. |
| `docs/governanca/trilha-auditoria-agentes.md` | ⏳ | 🔴 | **PROMOVIDO.** Auditor 1. Append-only, retenção 2 anos. Query padrão "quem tocou tenant Y entre HH:MM" testada em drill trimestral. |
| `docs/governanca/RACI-incidente-ai.md` (NOVO) | 🔴 | Auditor 1. Quem responde se agente vaza dado do tenant Y às 14h: Anthropic? Hostinger? Roldão? Inclui cláusula DPA por provedor. |
| `docs/plano-defesas-anti-erros-ia.md` | ✅ | — | Vira anexo que referencia IDs de REGRAS-INEGOCIAVEIS (Auditor 8). |
| `.specify/memory/constitution.md` | ⏳ | 🔴 | 6 princípios + 5 decisões fundadoras. Cita IDs INV-, não duplica. |

---

### Família 6 — Conformidade (híbrida) ⏳ (LACUNAS GRAVES PREENCHIDAS — Auditor 5)

#### Comum
| Doc | Prio | Conteúdo |
|-----|------|----------|
| `docs/conformidade/comum/lgpd-rat.md` | 🔴 | Registro Atividades Tratamento + DPO obrigatório (multi-tenant em larga escala — Enunciado CD/ANPD 4) + política confidencialidade. |
| `docs/conformidade/comum/seguranca-dados.md` | 🔴 | **PROMOVIDO de 🟡.** Inclui: (a) playbook incidente ANPD 72h (Resolução 15/2024); (b) RIPD/DPIA template (LGPD art. 38); (c) mapeamento bases legais por operação CRUD. |
| `docs/conformidade/comum/fiscal.md` | 🔴 (se módulo financeiro) | **Matriz município × padrão NFS-e** (ABRASF/Nacional/proprietário SP/RJ/BH/Curitiba) — Auditor 5. |
| `docs/conformidade/comum/fiscal-contingencia.md` (NOVO) | 🔴 | NOVO — separado. SVC-AN/SVC-RS, EPEC, CC-e, cancelamento <24h, inutilização de numeração. |
| `docs/conformidade/comum/retencao-matriz.md` (NOVO) | 🔴 | NOVO — Auditor 1+4+5. Matriz `categoria_dado × base_legal × prazo × fonte × acao_pos_prazo`. Reconcilia Receita 5 anos × ISO 17025 8.4 (~25 anos) × LGPD direito ao esquecimento. Exclusão lógica + log WORM da exclusão + crypto-shredding. |
| `docs/conformidade/comum/pci-dss.md` | ⚪ | Lazy. |
| `docs/conformidade/comum/open-banking.md` | ⚪ | Lazy. |

#### Por módulo — Calibração (módulo regulado)
| Doc | Prio | Conteúdo + cláusula |
|-----|------|----------------------|
| `docs/dominios/metrologia/modulos/calibracao/conformidade-iso-17025.md` | 🔴 | Cláusulas ISO 17025:2017 → invariantes (INV-NNN). **Inclui 7.7, 7.8, 7.10, 7.11, 8.3, 8.4, 8.5, 8.6, 8.7** (Auditor 5 adicionou 8.5/8.6/8.7). |
| `docs/dominios/metrologia/modulos/calibracao/responsabilidade-tecnica.md` | 🔴 | Signatário humano por certificado (RBC NIT-DICLA-021). Reconcilia com LGPD (base legal "cumprimento de obrigação regulatória" art. 7º II + 11 II 'a'). |
| `docs/dominios/metrologia/modulos/calibracao/validacao-software.md` | 🟡 | IQ/OQ/PQ ou ILAC G8/EURACHEM. Casos com valores VIM/BIPM. |
| `docs/dominios/metrologia/modulos/calibracao/controle-certificado-emitido.md` | 🟡 | WORM. Revisão = nova versão visível, original preservado. Teste automatizado tenta mutar e falha. Cláusula 8.4. |
| `docs/dominios/metrologia/modulos/calibracao/garantia-validade-7.7.md` | 🟡 | Replay determinístico, segundo caminho de cálculo independente da IA, hash. Detecta "IA inventou número". |

---

### Família 7 — Evolução pós-MVP ⏳ (todos lazy/pós-deploy)

| Doc | Prio | Quando |
|-----|------|--------|
| `docs/evolucao/roadmap.md` | ⚪ | Quando MVP-1 definido + plano de faseamento criado |
| `docs/evolucao/backlog-priorizado.md` | ⚪ | Pós primeiro deploy |
| `docs/evolucao/feedback-producao.md` | ⚪ | Pós primeiro cliente externo |
| `docs/evolucao/releases-planejados.md` | ⚪ | Quando frequência virar previsível |
| `docs/evolucao/kill-criteria.md` (NOVO) | 🟡 | Auditor 9. Quando descontinuar feature/módulo. |

---

### Família 8 — Docs externos ⏳ (todos lazy)

| Doc | Quando |
|-----|--------|
| `docs/externos/manual-cliente.md` | Quando 1º cliente externo for usar |
| `docs/externos/marketing/` | Quando MVP-1 pronto pra vender |
| `docs/externos/onboarding-cliente.md` | Quando 2º cliente entrar |
| ~~API pública~~ | Fora do mapa até decisão consciente |

---

### Família extra — Sessão & handoff + Tutoriais

| Doc | Prio | O que é |
|-----|------|---------|
| `.agent/SESSION.md` | 🔴 | Histórico curto entre sessões. |
| `.agent/CURRENT.md` | 🔴 | ≤10 linhas: US-ID + AC ativos + branch. Atualizado por hook session-start. |
| `.github/CODEOWNERS` | 🔴 | **D5 expandida.** 5 paths anti-bypass + `financeiro/`, `auth/`, `tenant/`, `kms/`, `migrations/` (Auditor 1). |
| `.github/ISSUE_TEMPLATE/ai-task.md` | ⚪ | |
| `.devcontainer/` | 🟡 | Após ADR-0001. |
| `.env.example` | 🟡 | Após ADR-0001. |
| `README.md` | 🔴 | Visão geral + mapa de navegação. |
| `LICENSE` | 🟡 | Antes do 1º release público. |
| `docs/INDICE.md` (NOVO) | 🔴 | Sitemap humano com matriz Diátaxis × audiência (humano/agente/cliente/regulador/auditor). |
| `docs/CONVENCOES-DOC.md` (NOVO) | 🔴 | Frontmatter obrigatório (owner, revisado-em, status: draft/stable/deprecated), regra comum-vs-módulo, sistema de IDs, convenção de linkagem cruzada. |
| `docs/tutoriais/dono/` (NOVO) | 🔴 | Diátaxis tutorial pro Roldão (não-técnico). Mín 3: `primeiro-pedido-ao-agente.md`, `ler-status-semanal.md`, `aprovar-mudanca-irreversivel.md`. |
| `docs/modulos/_TEMPLATE/` (NOVO) | 🔴 | Estrutura padrão dos 6 docs por módulo (uniformidade + habilita CODEMAP auto-gerado por boundary). |
| `docs/faseamento-modulos.md` (NOVO) | 🔴 (pós-discovery) | Ordem em que os N módulos entram em produção. Critério: dor + diferencial + dependência. Saída da `sintese-final` do discovery. |

---

## Nova ordem de criação (por rodadas)

### 🔬 Rodada 0 — Discovery (15 artefatos, bloqueia tudo)
0a. `concorrentes.md`, `normas-e-regulacao.md`, `dominio-de-negocio.md`, `riscos.md` (esboço) — agente sozinho
0b. **`treinamento-entrevista-roldao.md` + 2 entrevistas piloto** (revisadas por auditor)
0c. Onda 1: 3 entrevistas com donos de OUTRAS empresas → `entrevistas-clientes.md`
0d. Onda 2: 6 entrevistas com OPERADORES (3 perfis)
0e. `personas-detalhadas.md`, `jobs-to-be-done.md`, `jornada-atual-sem-produto.md`
0f. `dores-mapeadas.md` (com 6 dimensões), `opportunity-solution-tree.md`, `assumption-map.md`
0g. `spikes-tecnicos/` (NF-e municipal, multi-tenant, cálculo incerteza)
0h. `validacao-ativa.md` (smoke test + WTP test + cartas de intenção)
0i. Onda 3: 3 entrevistas de validação com protótipo de papel
0j. `precificacao-mercado.md`, `riscos.md` (final)
0k. `sintese-final.md` ⭐ → define **N módulos**, **MVP-1**, **faseamento**, **modelo negócio**, **stack candidate**

### 🔴 Rodada 1 — Fundação (pós-discovery)
1. `docs/comum/glossario.md` + `docs/dominios/<dominio-MVP-1>/README.md`
2. `docs/dominios/<dom>/modulos/<MVP-1>/glossario.md` + `prd.md`
3. `docs/prd.md` (visão consolidada)
4. `docs/painel-do-dono.md` + `docs/MAPA-DO-DONO.md` + `docs/como-os-agentes-trabalham-pra-mim.md`
5. `docs/INDICE.md` + `docs/CONVENCOES-DOC.md` + `docs/modulos/_TEMPLATE/`
6. `docs/tutoriais/dono/` (mín 3 tutoriais)
7. `README.md`, `docs/faseamento-modulos.md`

### 🔴 Rodada 2 — Stack + contrato dos agentes
8. `adr/0001-stack.md` ⭐, `adr/0002-multi-tenancy.md`, `adr/0003-mobile-tecnico-campo.md`
9. `AGENTS.md` + fronteira vs `CLAUDE.md`
10. `roteamento-dual.md`, `orcamento-contexto.md`, `INDEX.yaml`
11. `.agent/CURRENT.md` + `.agent/SESSION.md`

### 🔴 Rodada 3 — Conformidade do MVP-1
12. `conformidade/comum/lgpd-rat.md`, `seguranca-dados.md` (ANPD 72h), `retencao-matriz.md`
13. Se MVP-1 = financeiro/orçamento: `fiscal.md` + `fiscal-contingencia.md`
14. Se MVP-1 = calibração: docs Família 6 calibração (todas)
15. `seguranca/supply-chain.md`, `mcp-policy.md`, `agente-input-nao-confiavel.md`
16. `comum/isolamento-multi-tenant.md` + `comum/governanca-modelo-comum.md`

### 🔴 Rodada 4 — Trava de segurança + 3 auditores
17. `.github/CODEOWNERS` (10 paths)
18. `REGRAS-INEGOCIAVEIS.md` com IDs INV/INV-TENANT/TST/SEC
19. Hooks: anti-mascaramento, INV-checker, context-budget, tenant-id-validator, paths-frontmatter-validator
20. `.specify/memory/constitution.md`
21. **Família 5 materializada:** `catalogo-auditores.md` + 3 prompts de auditor + `limites-autonomia.md` + `RACI-incidente-ai.md`

### 🔴 Rodada 5 — Governança operacional
22. `status-semanal.md`, `auditoria-decisoes-autonomas.md`, `trilha-auditoria-agentes.md`

### 🎉 Rodada 6 — PRIMEIRA FEATURE DO MVP-1
23. `docs/dominios/<dom>/modulos/<MVP-1>/specs/001-<feature>/{spec,plan,tasks}.md`
24. `CHANGELOG.md`

### 🔴 Rodada 7 — Operação antes do 1º deploy
25. `operacao/{runbook, backup-restore, dr-plan (3 cenários), observabilidade (SLO por módulo), deploy, go-live-checklist, acionamento-agente, incidente-postmortem, capacity-planning, multi-tenant-ops, maintenance-windows}.md`
26. `.devcontainer/` + `.env.example` + `LICENSE`

### 🟡 Rodada 8 — Pós primeiro deploy
27. `evolucao/roadmap.md` + `backlog-priorizado.md` + `feedback-producao.md`
28. `governanca/metricas-operacao-agentes.md`

### 🟡 Rodada 9+ — Próximos módulos
29. Por cada módulo novo entrando: repete Rodada 1 (glossário+PRD) + Rodada 3 (conformidade específica)

### ⚪ Lazy
- Restante Família 4
- Família 7 completa
- Família 8 completa
- `personas-jornadas.md`, `metricas-sucesso.md`
- `CODEMAP.md`, `ISSUE_TEMPLATE/`
- `.claude/{agents,skills,commands}/*`
- `conformidade/comum/{pci-dss, open-banking}.md`
- ADRs específicos de módulo

---

## O que NÃO criar agora

- Doc de feature não decidida
- Runbook de problema não ocorrido (exceto template postmortem 🔴)
- ADR sem demanda
- Template vazio
- **Doc sem dor concreta hoje**
- **Doc de módulo fora do faseamento atual**

---

## O que mudou da v4 pra v5

| Mudança | Vindo de |
|---|---|
| Família 0 expandida 11→15 artefatos (treinamento, OST, assumption-map, jornada-atual, validacao-ativa) | Auditor 6 + 2; **Roldão vetou redução** |
| **Camada DOMÍNIO acima de módulo** (`docs/dominios/<dom>/modulos/<mod>/`) | Auditor 3 + 8 |
| Multi-tenancy ADR-0002 obrigatório + `isolamento-multi-tenant.md` + INV-TENANT- | 4 auditores |
| Mobile ADR-0003 obrigatório | Auditor 3 |
| Quebra `padroes-tecnicos.md` em 8 docs | Auditor 3 |
| Watchdog/postmortem/capacity/multi-tenant-ops/maintenance-windows promovidos ⚪→🔴 | Auditor 4 |
| `seguranca/agente-input-nao-confiavel.md` | Auditor 1 |
| `governanca/auditoria-decisoes-autonomas.md` + `RACI-incidente-ai.md` | Auditor 1 + 2 |
| `conformidade/comum/{retencao-matriz, fiscal-contingencia, seguranca-dados promovido}.md` | Auditor 4 + 5 |
| Família 6 calibração cobre 8.5/8.6/8.7 ISO | Auditor 5 |
| `INDICE.md` (humano) + `INDEX.yaml` (máquina) | Auditor 7 + 8 |
| `CONVENCOES-DOC.md` + `modulos/_TEMPLATE/` + `tutoriais/dono/` | Auditor 8 |
| `MAPA-DO-DONO.md` (7 docs obrigatórios pro dono) | Auditor 2 |
| Família 5 MATERIALIZADA: 3 prompts de auditor + triggers + veto | Auditor 10 |
| `comum/integracoes-inter-modulos.md` + `integracoes-externas/` | Auditor 3 |
| `comum/governanca-modelo-comum.md` (fronteira comum vs módulo) | Auditor 3 + 8 |
| Hierarquia de regras: REGRAS-INEGOCIAVEIS = fonte única; outros citam IDs | Auditor 7 + 8 |
| CODEOWNERS expandido: 5 + 5 paths | Auditor 1 |
| Hooks novos: tenant-id-validator, paths-frontmatter-validator, context-budget em tokens | Auditor 7 |
| `evolucao/kill-criteria.md` | Auditor 9 |
| `operacao/dr-plan.md` com 3 cenários explícitos + SLO por módulo | Auditor 4 |
| `faseamento-modulos.md` (saída discovery, ordem dos N módulos em produção) | Roldão (founder is customer + N a descobrir) |

---

## Estrutura de pastas final v5

```
Certificado de calibracao/
├── CLAUDE.md, AGENTS.md, README.md, ARQUITETURA.md
├── REGRAS-INEGOCIAVEIS.md, CONTRIBUTING.md, CHANGELOG.md, LICENSE
├── .gitignore, .env.example, .mcp.json
│
├── .claude/, .specify/memory/constitution.md, .agent/{SESSION,CURRENT}.md
├── .github/{CODEOWNERS, ISSUE_TEMPLATE/}, .devcontainer/
│
└── docs/
    ├── ambiente-claude-code.md  ✅, plano-defesas-anti-erros-ia.md ✅
    ├── documentos-do-projeto.md ✅ (este, v5)
    ├── INDICE.md, INDEX.yaml, CONVENCOES-DOC.md, MAPA-DO-DONO.md
    ├── prd.md, painel-do-dono.md, como-os-agentes-trabalham-pra-mim.md
    ├── roteamento-dual.md, orcamento-contexto.md, faseamento-modulos.md
    │
    ├── discovery/                       FAMÍLIA 0 — 15 artefatos
    │   ├── concorrentes.md
    │   ├── normas-e-regulacao.md
    │   ├── treinamento-entrevista-roldao.md
    │   ├── entrevistas-clientes.md
    │   ├── dores-mapeadas.md
    │   ├── jobs-to-be-done.md
    │   ├── personas-detalhadas.md
    │   ├── dominio-de-negocio.md
    │   ├── jornada-atual-sem-produto.md
    │   ├── opportunity-solution-tree.md
    │   ├── assumption-map.md
    │   ├── validacao-ativa.md
    │   ├── precificacao-mercado.md
    │   ├── spikes-tecnicos/
    │   ├── riscos.md
    │   └── sintese-final.md ⭐
    │
    ├── comum/                           transversal
    │   ├── glossario.md ⭐
    │   ├── personas.md, metricas-sucesso.md
    │   ├── modelo-de-dominio.md, schema-banco.md
    │   ├── contratos/{ui,api,exports}.md
    │   ├── isolamento-multi-tenant.md  (NOVO)
    │   ├── integracoes-inter-modulos.md (NOVO)
    │   ├── governanca-modelo-comum.md   (NOVO)
    │   └── integracoes-externas/        (NOVO — 1 doc por parceiro)
    │
    ├── dominios/                        NOVO — camada acima de módulo
    │   ├── _TEMPLATE-dominio/           (estrutura padrão)
    │   └── <dominio>/                   (a descobrir: comercial, operacao, financeiro, metrologia, suporte, ...)
    │       ├── README.md
    │       ├── personas.md
    │       └── modulos/
    │           ├── _TEMPLATE/           (estrutura padrão dos 6 docs por módulo)
    │           └── <modulo>/
    │               ├── glossario.md, prd.md, personas.md, metricas.md
    │               ├── modelo-de-dominio.md
    │               ├── contratos/{ui,api,exports}.md
    │               ├── adr/             (ADRs específicos do módulo)
    │               └── specs/<NNN-feature>/{spec,plan,tasks}.md
    │
    ├── adr/                             ADRs transversais
    │   ├── 0001-stack.md ⭐
    │   ├── 0002-multi-tenancy.md         (NOVO)
    │   ├── 0003-mobile-tecnico-campo.md  (NOVO)
    │   └── 0004+
    │
    ├── arquitetura/
    │   ├── overview.md
    │   └── cross-cutting/               (NOVO — quebrado em 8)
    │       ├── erro.md, log.md, retry.md, timeout.md
    │       ├── idempotencia.md, transacao.md
    │       ├── auth-rbac.md, validacao.md
    │
    ├── seguranca/
    │   ├── mcp-policy.md
    │   ├── agente-input-nao-confiavel.md (NOVO)
    │   ├── supply-chain.md
    │   └── classificacao-dados.md
    │
    ├── conformidade/
    │   └── comum/
    │       ├── lgpd-rat.md
    │       ├── seguranca-dados.md         (promovido 🔴)
    │       ├── retencao-matriz.md          (NOVO)
    │       ├── fiscal.md
    │       ├── fiscal-contingencia.md      (NOVO)
    │       ├── pci-dss.md
    │       └── open-banking.md
    │   (compliance ISO 17025 fica em dominios/metrologia/modulos/calibracao/)
    │
    ├── governanca/
    │   ├── catalogo-auditores.md          (materializado)
    │   ├── auditor-seguranca-prompt.md    (NOVO)
    │   ├── auditor-qualidade-prompt.md    (NOVO)
    │   ├── auditor-produto-prompt.md      (NOVO)
    │   ├── limites-autonomia.md
    │   ├── status-semanal.md
    │   ├── auditoria-decisoes-autonomas.md (NOVO)
    │   ├── caminho-reclamacao.md
    │   ├── metricas-operacao-agentes.md
    │   ├── trilha-auditoria-agentes.md
    │   └── RACI-incidente-ai.md           (NOVO)
    │
    ├── operacao/
    │   ├── runbook.md, backup-restore.md, deploy.md
    │   ├── dr-plan.md (3 cenários)         (promovido 🔴)
    │   ├── observabilidade.md (SLO/módulo) (promovido 🔴)
    │   ├── go-live-checklist.md            (promovido 🔴)
    │   ├── acionamento-agente.md (NOVO 🔴)
    │   ├── incidente-postmortem.md (template, promovido 🔴)
    │   ├── capacity-planning.md (NOVO 🔴)
    │   ├── multi-tenant-ops.md (NOVO 🔴)
    │   ├── maintenance-windows.md (NOVO 🔴)
    │   ├── rotacao-credenciais.md ⚪
    │   └── provisionamento.md ⚪
    │
    ├── evolucao/                          (todos lazy/pós-deploy)
    │   ├── roadmap.md, backlog-priorizado.md, feedback-producao.md
    │   ├── releases-planejados.md
    │   └── kill-criteria.md (NOVO 🟡)
    │
    ├── externos/                          (todos lazy)
    │   ├── manual-cliente.md, onboarding-cliente.md
    │   └── marketing/
    │
    ├── tutoriais/
    │   └── dono/                          (NOVO — Diátaxis tutorial)
    │       ├── primeiro-pedido-ao-agente.md
    │       ├── ler-status-semanal.md
    │       └── aprovar-mudanca-irreversivel.md
    │
    └── CODEMAP.md ⚪
```

---

## Como este arquivo evolui

- Doc criado → ✅
- Doc descontinuado → ❌ + motivo
- Decisão fundadora alterada → ADR + atualizar tabela D1–D5
- Auditoria nova → seção "Síntese das auditorias" recebe revisão datada
- Escopo muda → atualizar banner ⚠️ e Famílias 2/6
- Discovery termina → atualizar `faseamento-modulos.md` + reescrever Rodadas 1+

Este arquivo é o índice mestre. Se sair daqui, deixa de existir pro projeto.
