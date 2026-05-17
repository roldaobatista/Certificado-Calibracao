# Documentos do projeto Aferê (v8)

> **Pra que serve:** mapa de TODOS os documentos que o projeto precisa pra funcionar 100% tocado por agentes de IA, sem o Roldão precisar virar programador.
>
> **Status:** ✅ existe | ⏳ falta criar | 🟡 parcial | ❌ removido
> **Prioridade:** 🔴 MVP-obrigatório | 🟡 próximo | ⚪ lazy
>
> **Atualização:** 2026-05-17 noite+12h (v8 — incorpora **25 módulos adicionais** identificados em inventário paralelo (10 agentes Explore) confrontando `docs/novas funcionalidades.txt` × v7. Adições: 1 domínio novo (`dados/` com módulo `bi/`), 24 módulos novos distribuídos em domínios existentes (`comercial`, `operacao`, `financeiro`, `suporte-plataforma`, `metrologia`, `rh-frota-qualidade`), completar PRD do módulo `calibracao`. Cada módulo novo recebe 8 docs (~200 docs novos). Roldão autorizou criar TODOS — **nenhum corte**. Total projeto após v8: ~480 docs).
>
> **Atualização anterior:** 2026-05-17 (v7 — incorpora mapeamento de 25 módulos da lista funcional do Roldão. Adições: 5 OPs novas (OP13/14/15/16/17), 7 INVs novos (INV-021..027), 3 ADRs reservadas viraram reais (0004 sync mobile / 0005 engine automações / 0006 feature flags), 5 domínios novos (`comercial`, `operacao`, `financeiro`, `suporte-plataforma`, `rh-frota-qualidade`) com README + personas, 19 módulos novos com 8 docs cada (~152 docs novos). Nenhum corte de escopo aplicado).

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

**Auditoria 3 (sobre Portão 2 das decisões técnicas, 2026-05-17 noite):** 10 auditores. Recomendações: sobre-engenharia grave (cortar 60%), cronograma "fantasia" (5-7 meses reais vs 14 semanas), custo Mês 12 real (R$ 3.8-6.7k vs alegado R$ 1.5k). **Roldão aceitou 1 de 8 recomendações** (drills reduzidos pra 1 obrigatório). Os demais 7 mantidos conscientemente — trade-off documentado.

**Auditoria 4 (5 lentes paralelas sobre `ambiente-claude-code.md` + `documentos-do-projeto.md` v5, 2026-05-17):** 5 auditores independentes. Achados aplicados em v6:
- ✅ `@AGENTS.md` ativado no CLAUDE.md (estava como exemplo dentro de code block; canônico não era lido).
- ✅ CLAUDE.md "Estado do ambiente" reescrito (parou de mentir que stack/agentes ⏳).
- ✅ AGENTS.md saiu de placeholder (1137 bytes → ~200 linhas com stack, comandos, política).
- ✅ ADR-0003 criada como stub + 0004/0005/0006 stubs reservados (rastreabilidade do salto numérico 0003→0007).
- ✅ Modelo de subagentes decidido (catalogo-auditores: híbrido A+B; 4 substitutos coexistem com escopo distinto dos 3 auditores).
- ✅ Pegadinhas em ambiente-claude-code.md corrigidas (exemplo "TS+Electron"; defaultMode inválido).
- ✅ Status real atualizado neste doc (Família 0, 1, 2, 3, 5, extras).
- ❌ **NÃO aplicado:** Auditor 5 propôs rebaixar 25 itens 🔴→🟡. **Vetado pelo Roldão** ("não quero reduzir o que já tínhamos decidido"). Cortes só por veto item-por-item.

Ajustes incorporados na v5 (Auditoria 2):

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

### Família 0 — Discovery (NOVA na v3, EXPANDIDA na v5, ATUALIZADA na v6) 🟡 (síntese ainda DRAFT v3)

**17 artefatos** (15 originais + 2 adicionados em v6: validação externa documental + roteiro de próximos artefatos). Bloqueia todas as outras famílias do MVP até `sintese-final.md` virar STABLE.

| Artefato | Status | Prio | Quem produz | O que contém |
|---|---|---|---|---|
| `concorrentes.md` | ✅ | 🔴 | Agente | Bling, Tiny, Omie, Conta Azul, Granatum + nichos calibração. Feature matrix, preço, gaps. |
| `normas-e-regulacao.md` | ✅ | 🔴 | Agente | ISO 17025, RBC, NF-e/NFS-e por município, LGPD, open banking, PCI. |
| `treinamento-entrevista-roldao.md` | ✅ | 🔴 | Agente | Roteiro literal por persona, perguntas proibidas (sugestivas), template ata, gravação. Roldão treina em 2 entrevistas piloto antes de valer. |
| `entrevistas-clientes.md` | 🟡 | 🔴 | Roldão + Agente sintetiza | **3 ondas** (Auditor 6): onda 1 = 3 donos de OUTRAS empresas (problema), onda 2 = 6 operadores (3 perfis: atendente, técnico, financeiro), onda 3 = 3 entrevistas de validação de solução com protótipo de papel. Total 12, em 3 ciclos. Ondas ainda não executadas. |
| `dores-mapeadas.md` | ✅ | 🔴 | Agente | Métrica de priorização **expandida** (Auditor 6): agudez × frequência × disposição a pagar × **SOLVABILITY** (cara de resolver?) × **REACH** (quanto mercado tem essa dor?) × **evitabilidade** (workaround manual aceitável?). |
| `jobs-to-be-done.md` | ✅ | 🟡 | Agente | O que cada perfil "contrata" o software pra resolver. |
| `personas-detalhadas.md` | ✅ | 🔴 | Agente | Dono, atendente, técnico de campo, financeiro, vendedor, metrologista. Goals/frustrations/jornada. |
| `dominio-de-negocio.md` | ✅ | 🔴 | Agente | Como uma assistência técnica + laboratório funciona. **Base do glossário comum.** Mapeia também os N módulos prováveis e seus domínios. |
| `jornada-atual-sem-produto.md` | ✅ | 🔴 | Agente + Roldão | Como SUA empresa + outras resolvem HOJE (planilha? Bling+WhatsApp? caderno?). Mapeia status quo antes de propor solução. |
| `opportunity-solution-tree.md` | ✅ | 🔴 | Agente | Teresa Torres. Hierarquia outcome → opportunities → solutions → experiments. Sem isso, dores viram lista plana. |
| `assumption-map.md` | ✅ | 🔴 | Agente + Roldão | David Bland. 4 quadrantes (desejabilidade/viabilidade/factibilidade/ética) × confiança (sei/não sei). Destaca leap-of-faith. |
| `validacao-ativa.md` | ✅ | 🔴 | Roldão + Agente | Smoke test (fake-door landing), Willingness-to-Pay test, carta-de-intenção assinada de 3+ empresas. Auto-reportado em entrevista mente. |
| `validacao-externa-documental.md` + `validacao-externa/` (NOVO v6) | ✅ | 🔴 | Agente | 4 buckets de validação documental (sem entrevista) + estudo Calibre.Software + mystery shopping documental. Complementa `validacao-ativa.md` enquanto Roldão não fornece telefones. |
| `precificacao-mercado.md` | ✅ | 🟡 | Agente | Per-user / per-módulo / flat / %. Range por porte. |
| `spikes-tecnicos/` | ⏳ | 🟡 | Agente | POCs: emitir NF-e em município com padrão próprio, integração bancária, cálculo de incerteza, XML INMETRO, multi-tenant isolation. |
| `riscos.md` | ✅ | 🔴 | Agente + Roldão | Regulatório, técnico, mercado, time, **customização disfarçada** (founder is customer). |
| `proximos-artefatos.md` (NOVO v6, meta) | ✅ | ⚪ | Agente | Working doc temporário com roteiro dos próximos passos de discovery. Pode ser deletado quando síntese fechar. |
| `sintese-final.md` ⭐ | 🟡 (DRAFT v3) | 🔴 | Agente + Roldão | **Saídas:** cliente ideal, **N total de módulos**, plano de **faseamento** (qual MÓDULO-1, MÓDULO-2... entra em produção), modelo de negócio (SaaS multi-tenant vs on-prem), stack candidate, mobile sim/não. Trava critério de saída antes de começar (nº mín entrevistas, saturação documentada, leap-of-faith validados). |

---

### Família 1 — Contrato dos agentes ✅ (v6 — quase completa)

| Doc | Status | Prio | O que é |
|-----|--------|------|---------|
| `CLAUDE.md` | ✅ | 🔴 | Adendo do harness Claude Code com `@AGENTS.md` ativo. ≤ 150 linhas. |
| `AGENTS.md` | ✅ | 🔴 | Canônico de produto/arquitetura. ~200 linhas. Encorpado em 17/05 (v6). |
| `.claude/settings.json` | ✅ | 🔴 | Permissões + denylist robusta. |
| `.claude/hooks/` | 🟡 | 🔴 | block-destructive ✅, secrets-scanner ✅, _test-runner ✅. **Falta:** anti-mascaramento, context-budget, INV-checker, tenant-id-validator, paths-frontmatter-validator. |
| `.claude/agents/` | ✅ | 🔴 | 4 subagentes humanos-substitutos: tech-lead, advogado, corretora, RBC. + a criar: 3 auditores Família 5 (segurança, qualidade, produto). |
| `.claude/skills/` | ⏳ | ⚪ | Criar quando padrão repetir 3x. |
| `.claude/commands/` | ⏳ | ⚪ | Preferir skills. |
| `.claude/rules/` | ⏳ | 🟡 | `paths:` frontmatter validado por hook (a criar). |
| `.mcp.json` | 🟡 | 🔴 | github plugado; filesystem/playwright/postgres sob demanda. |
| `.claude/output-styles/pt-br-conciso.md` | ✅ | 🟡 | Estilo PT-BR sem jargão. |
| `docs/roteamento-dual.md` | ✅ | 🟡 | Fronteira AGENTS.md vs CLAUDE.md + roteamento Claude/Codex. |
| `docs/orcamento-contexto.md` | ✅ | 🔴 | Teto em tokens reais + hook tokenizador (hook ainda a criar). |
| `docs/INDEX.yaml` | ⏳ | 🔴 | Machine-readable: `{path, módulo, dominio, tokens_estimados, carrega_quando}`. Hook em SessionStart lê INDEX + CURRENT.md e injeta só subset necessário via `@path`. |

---

### Família 2 — Produto (híbrida 3 níveis: comum → domínio → módulo) ⏳

#### Comum (transversal)
| Doc | Status | Prio | Conteúdo |
|-----|--------|------|----------|
| `docs/comum/glossario-roldao.md` ⭐ | ✅ | 🔴 | Glossário POV do dono. Decidido v6: manter sufixo `-roldao` (sinaliza ponto de vista). Termos transversais (cliente, fatura, usuário, permissão, tenant) + coluna "se você vir isto na tela/log, significa…". |
| `docs/prd.md` | ⏳ | 🔴 | Visão consolidada do produto: o que é, pra quem, dor, escopo MVP-1 (saída discovery), non-goals. |
| `docs/comum/personas.md` | ⏳ | 🔴 | Personas transversais (dono, gerente). Específicas vão no módulo. (Personas detalhadas já existem em `discovery/personas-detalhadas.md` — consolidar comum aqui.) |
| `docs/painel-do-dono.md` | ✅ | 🔴 | Índice navegável pro Roldão. Aviso visual quando agente toca um dos 10 paths CODEOWNERS. |
| `docs/como-os-agentes-trabalham-pra-mim.md` | ✅ | 🔴 | 1 página PT-BR puro. |
| `docs/MAPA-DO-DONO.md` | ✅ | 🔴 | Lista numerada dos 7 docs obrigatórios pro Roldão. |
| `docs/comum/metricas-sucesso.md` | ⏳ | ⚪ | Lazy. |

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
| Doc | Status | Prio | O que é |
|-----|--------|------|---------|
| `REGRAS-INEGOCIAVEIS.md` | ✅ | 🔴 | **Fonte única de regras críticas.** Funde INVARIANTES + TESTES + SECURITY com IDs `INV-NNN`, `INV-TENANT-NNN`, `TST-NNN`, `SEC-NNN`, `INV-AGENT-NNN`. Outros docs **citam IDs, não duplicam texto**. |
| `CONTRIBUTING.md` | ✅ | 🟡 | Fluxo do agente. |
| `ARQUITETURA.md` | ✅ | 🟡 | 1 página apontando pra `docs/arquitetura/`. |

#### Arquitetura
| Doc | Status | Prio | O que é |
|-----|--------|------|---------|
| `docs/arquitetura/overview.md` | ⏳ | 🟡 | Code map, entry points, boundaries (Auditor 3). |
| `docs/arquitetura/anti-corrosion-layer.md` (NOVO v6) | ✅ | 🔴 | **9 portas** (Fiscal, Signature, LLM, Storage, Hosting, Auth, Queue, Sync, MultiTenant). Cross-cutting #9 não previsto no v5. |
| `docs/arquitetura/cross-cutting/erro.md` | ⏳ | 🟡 | Auditor 3 quebrou em 8. |
| `docs/arquitetura/cross-cutting/log.md` | ⏳ | 🟡 | |
| `docs/arquitetura/cross-cutting/retry.md` | ⏳ | 🟡 | |
| `docs/arquitetura/cross-cutting/timeout.md` | ⏳ | 🟡 | |
| `docs/arquitetura/cross-cutting/idempotencia.md` | ⏳ | 🟡 | |
| `docs/arquitetura/cross-cutting/transacao.md` | ⏳ | 🟡 | |
| `docs/arquitetura/cross-cutting/auth-rbac.md` | ⏳ | 🟡 | |
| `docs/arquitetura/cross-cutting/validacao.md` | ⏳ | 🟡 | |
| `docs/comum/integracoes-inter-modulos.md` | ⏳ | 🔴 | Auditor 3. Contratos entre domínios/módulos (eventos: `OSConcluida` → quem consome, schema versionado, idempotência, ordem). |
| `docs/comum/governanca-modelo-comum.md` | ✅ | 🔴 | Critério explícito de promoção/rebaixamento; processo de versionamento. |
| `docs/CODEMAP.md` | ⏳ | ⚪ | Lazy. |

#### ADRs
| Doc | Status | Prio | O que é |
|-----|--------|------|---------|
| `docs/adr/0000-uso-de-ia.md` | ✅ | 🔴 | Meta-ADR — uso de IA no projeto. |
| `docs/adr/0001-stack.md` ⭐ | 🟡 (candidata) | 🔴 | Django + Flutter + PostgreSQL. 3 portões. |
| `docs/adr/0002-multi-tenancy.md` | 🟡 (proposta) | 🔴 | Schema-shared + RLS + middleware tenant_id + roles NOBYPASSRLS. |
| `docs/adr/0003-mobile-tecnico-campo.md` | ⏳ stub | 🔴 | PWA vs React Native vs Flutter vs Capacitor. Stub criado v6. |
| `docs/adr/0004-reservado.md` | ⏳ stub | ⚪ | Slot reservado. |
| `docs/adr/0005-reservado.md` | ⏳ stub | ⚪ | Slot reservado. |
| `docs/adr/0006-reservado.md` | ⏳ stub | ⚪ | Slot reservado. |
| `docs/adr/0007-camada-dominio-gerador-spec.md` (NOVO v6) | 🟡 (proposta) | 🔴 | Pipeline spec PT → YAML → Django+Pydantic+OpenAPI+Dart. |
| `docs/adr/0008-fiscal-pluggable.md` (NOVO v6) | 🟡 (proposta) | 🔴 | Interface `FiscalProvider` agnóstica de país. PlugNotas 1ª impl + Focus NFe smoke trimestral. |
| `docs/adr/0009-onde-a3-assina.md` (NOVO v6) | 🟡 (proposta) | 🔴 | A3 sempre cliente-side via Web PKI Lacuna; A1 server-side com KMS. |
| `docs/adr/0010+.md` | ⏳ | 🟡 | 1 por decisão nova. |

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

### Família 5 — Governança IA 🟡 (catálogo + 5 docs ✅; 3 prompts auditor pendentes)

| Doc | Status | Prio | Conteúdo |
|-----|--------|------|----------|
| `docs/governanca/catalogo-auditores.md` | ✅ | 🔴 | Catálogo dos 3 auditores + decisão (v6) de onde vivem: híbrido A+B (subagents Claude Code + GitHub Actions). |
| `docs/governanca/auditor-seguranca-prompt.md` | ✅ | 🔴 | Prompt v1.0.0 — Auditor de Segurança (Sonnet, pre-commit). |
| `docs/governanca/auditor-qualidade-prompt.md` | ✅ | 🔴 | Prompt v1.0.0 — Auditor de Qualidade (Sonnet, pre-commit). |
| `docs/governanca/auditor-produto-prompt.md` | ✅ | 🔴 | Prompt v1.0.0 — Auditor de Produto (Opus, pre-merge). |
| `docs/governanca/limites-autonomia.md` | ✅ | 🔴 | 5 casos-limite + limites $/dados/SLA explícitos. |
| `docs/governanca/status-semanal.md` | ✅ | 🔴 | Auto-gerado. Topo: "essa semana o módulo X precisa de você por Y". |
| `docs/governanca/auditoria-decisoes-autonomas.md` | ✅ | 🔴 | Lista filtrada do que agentes decidiram SEM consultar Roldão. |
| `docs/governanca/caminho-reclamacao.md` | ⏳ | 🟡 | |
| `docs/governanca/metricas-operacao-agentes.md` | ⏳ | 🟡 | Tokens, retrabalho, tempo entrega. |
| `docs/governanca/trilha-auditoria-agentes.md` | ⏳ | 🔴 | Append-only, retenção 2 anos. Query padrão "quem tocou tenant Y entre HH:MM" testada em drill trimestral. |
| `docs/governanca/RACI-incidente-ai.md` | ✅ | 🔴 | Quem responde se agente vaza dado do tenant Y. Inclui cláusula DPA por provedor. |
| `docs/plano-defesas-anti-erros-ia.md` | ✅ | — | Anexo que referencia IDs de REGRAS-INEGOCIAVEIS. |
| `.specify/memory/constitution.md` | ✅ | 🔴 | 6 princípios + 5 decisões fundadoras. Cita IDs INV-, não duplica. |

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

| Doc | Status | Prio | O que é |
|-----|--------|------|---------|
| `.agent/SESSION.md` | ✅ | 🔴 | Histórico curto entre sessões. |
| `.agent/CURRENT.md` | ✅ | 🔴 | ≤10 linhas: US-ID + AC ativos + branch. Atualizado por hook session-start. |
| `.github/CODEOWNERS` | 🟡 | 🔴 | **D5 expandida.** 5 paths anti-bypass + `financeiro/`, `auth/`, `tenant/`, `kms/`, `migrations/`. Verificar conteúdo. |
| `.github/ISSUE_TEMPLATE/ai-task.md` | ⏳ | ⚪ | |
| `.devcontainer/` | ⏳ | 🟡 | Após ADR-0001 fechar. |
| `.env.example` | ⏳ | 🟡 | Após ADR-0001 fechar. |
| `README.md` | ✅ | 🔴 | Visão geral + mapa de navegação. |
| `LICENSE` | ⏳ | 🟡 | Antes do 1º release público. |
| `docs/INDICE.md` | ✅ | 🔴 | Sitemap humano com matriz Diátaxis × audiência. |
| `docs/CONVENCOES-DOC.md` | ✅ | 🔴 | Frontmatter obrigatório, regra comum-vs-módulo, sistema de IDs, convenção de linkagem. |
| `docs/tutoriais/dono/primeiro-pedido-ao-agente.md` | ✅ | 🔴 | Diátaxis tutorial pro Roldão. |
| `docs/tutoriais/dono/ler-status-semanal.md` | ✅ | 🔴 | |
| `docs/tutoriais/dono/aprovar-mudanca-irreversivel.md` | ✅ | 🔴 | |
| `docs/dominios/_TEMPLATE-dominio/modulos/_TEMPLATE/` (caminho corrigido em v6) | ✅ | 🔴 | Estrutura padrão dos 6 docs por módulo. Caminho real difere do v5 (que dizia `docs/modulos/_TEMPLATE/`). |
| `docs/faseamento-modulos.md` | ⏳ | 🔴 | Ordem em que os N módulos entram em produção. Saída da `sintese-final` do discovery. |

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

## O que mudou da v7 pra v8 (2026-05-17 noite +12h)

> v8 incorpora o resultado de **inventário paralelo de 10 agentes Explore** confrontando `docs/novas funcionalidades.txt` (lista pessoal do Roldão com 50+ funcionalidades) × o mapeamento da v7. Foram identificados **25 módulos adicionais** ainda NÃO previstos. Roldão autorizou criar **TODOS**, sem deletar nada do que já estava. 15 agentes em paralelo executam a criação enquanto este registra a expansão.

### 1 domínio novo

| Domínio | Módulos | Motivo |
|---|---|---|
| `dados/` | `bi/` | BI / analytics / dashboards transversais não pertence a nenhum domínio operacional. Concentra cubos, painéis gerenciais, exports analíticos e a futura camada semântica do produto. |

### 25 módulos novos por domínio (com 8 docs cada = ~200 docs)

| Domínio | Módulo novo | Wave de ativação | Observação |
|---|---|---|---|
| `comercial/` | `portal-cliente/` | **Wave A (MVP-1)** | Cliente externo acompanha OS/certificado/financeiro. Pré-requisito de qualquer 1º cliente externo. |
| `comercial/` | `marketplace/` | **V2/V3** | Aplicativos/extensões/parceiros. Adiado pra pós-MVP-2. |
| `comercial/` | `precificacao/` | Wave B | Régua de preços, tabelas, descontos sistêmicos, política comercial. |
| `comercial/` | `sla-contratual/` | Wave B | Cláusulas de SLA por contrato/cliente. Liga em Chamados + OS. |
| `comercial/` | `comunicacao-omnichannel/` | Wave B | WhatsApp Business, e-mail, SMS, central de mensagens. |
| `operacao/` | `garantia/` | Wave B | Controle de garantia de serviços/peças/equipamentos pós-OS. |
| `operacao/` | `projetos/` | Wave B | Gestão de projetos (instalação, retrofit, mudança de planta). |
| `operacao/` | `base-conhecimento/` | Wave A (MVP-1) acoplado | KB técnica interna; embutida nas OS e Chamados desde o MVP-1 (sem KB, técnico repete erro). |
| `operacao/` | `capacity-planning-operacional/` | Wave B | Planejamento de carga de técnicos/laboratório (diferente de `operacao/capacity-planning.md` que é infra). |
| `operacao/` | `app-tecnico/` | **Wave A (MVP-1)** | App offline-first do técnico de campo. Já tem ADR-0003 + ADR-0004 cobrindo. |
| `financeiro/` | `billing-saas/` | **Bloqueador antes do 1º cliente externo pago** | Faturamento recorrente do Aferê como SaaS (planos, ciclos, downgrade, dunning). Não confundir com `financeiro/contas-receber` (cliente da empresa-cliente). |
| `financeiro/` | `custeio-real/` | Wave B | Custeio real por OS/certificado/contrato. Rateios. |
| `financeiro/` | `despesas/` | Wave B | Despesas operacionais, reembolso, adiantamento. |
| `financeiro/` | `relatorios-financeiros/` | Wave B | DRE gerencial, fluxo de caixa, conciliação avançada. |
| `suporte-plataforma/` | `onboarding/` | Wave B | Onboarding self-service de novo tenant. |
| `suporte-plataforma/` | `configuracoes-sistema/` | Wave B | Configurações globais por tenant (temas, idioma, fuso). |
| `suporte-plataforma/` | `automacoes-bpm/` | Wave B | Motor BPM/workflow visual sobre engine de automações (ADR-0005). |
| `suporte-plataforma/` | `engenharia-tecnica/` | Wave B | Cadastros técnicos avançados (procedimentos, padrões internos). |
| `suporte-plataforma/` | `gestao-documental/` | Wave B | DMS interno (versões, controle de acesso, retenção, link com WORM). |
| `suporte-plataforma/` | `suporte-saas/` | Wave B | Suporte interno do Aferê pros tenants (tickets, knowledge base do produto). |
| `suporte-plataforma/` | `release-management/` | Wave B | Gestão de releases/changelog visível pro cliente final. |
| `suporte-plataforma/` | `acesso-seguranca/` | **Wave A (MVP-1)** | RBAC avançado, MFA, gestão de sessões, audit log de acesso. Pré-requisito de qualquer cliente externo. |
| `metrologia/` | `licencas-acreditacoes/` | Wave B | Controle de licenças RBC, validade, escopo acreditado, NIT-DICLA. |
| `metrologia/` | `certificados/` | **Wave A (MVP-1)** | Módulo dedicado a ciclo de vida do certificado (numeração, controle, reemissão, revisão). Hoje embutido em `calibracao/` — separar. |
| `rh-frota-qualidade/` | `seguranca-trabalho/` | Wave B | SST: EPI, ASO, CIPA, NR-12/NR-35. |
| `rh-frota-qualidade/` | `treinamentos/` | Wave B | Plano de treinamento por colaborador, matriz de competências, certificações. |
| `rh-frota-qualidade/` | `auditoria-externa/` | Wave B | Suporte a auditorias externas (RBC, ISO, cliente corporativo, fiscal). |

### Completar PRD do módulo `calibracao`

`docs/dominios/metrologia/modulos/calibracao/prd.md` estava parcial na v7 — v8 completa com user stories `US-CAL-NNN` cobrindo emissão, revisão, controle de validade, cliente do certificado, padrão usado, comparações interlaboratoriais.

### Estrutura final v8 (domínios × módulos)

| Domínio | Módulos | Total |
|---|---|---|
| `comercial/` | clientes, orcamentos, crm, contratos, **portal-cliente**, **marketplace**, **precificacao**, **sla-contratual**, **comunicacao-omnichannel** | 9 |
| `operacao/` | os, chamados, agenda, **garantia**, **projetos**, **base-conhecimento**, **capacity-planning-operacional**, **app-tecnico** | 8 |
| `financeiro/` | contas-receber, contas-pagar, comissoes, caixa-tecnico, fiscal, **billing-saas**, **custeio-real**, **despesas**, **relatorios-financeiros** | 9 |
| `suporte-plataforma/` | equipamentos, produtos-pecas-servicos, estoque, fornecedores, **onboarding**, **configuracoes-sistema**, **automacoes-bpm**, **engenharia-tecnica**, **gestao-documental**, **suporte-saas**, **release-management**, **acesso-seguranca** | 12 |
| `metrologia/` | calibracao, **licencas-acreditacoes**, **certificados** | 3 |
| `rh-frota-qualidade/` | colaboradores, frota, qualidade, **seguranca-trabalho**, **treinamentos**, **auditoria-externa** | 6 |
| `dados/` (NOVO) | **bi** | 1 |
| **TOTAL** | | **48 módulos × 8 docs cada** |

(Negrito = novo na v8.)

### Wave de ativação consolidada (v8)

| Wave | Módulos |
|---|---|
| **Wave A (MVP-1)** | (já em v7) + `portal-cliente`, `app-tecnico`, `certificados`, `acesso-seguranca`, `base-conhecimento` |
| **Bloqueador antes do 1º cliente externo pago** | `billing-saas` |
| **Wave B** | `precificacao`, `sla-contratual`, `comunicacao-omnichannel`, `garantia`, `projetos`, `capacity-planning-operacional`, `custeio-real`, `despesas`, `relatorios-financeiros`, `onboarding`, `configuracoes-sistema`, `automacoes-bpm`, `engenharia-tecnica`, `gestao-documental`, `suporte-saas`, `release-management`, `licencas-acreditacoes`, `seguranca-trabalho`, `treinamentos`, `auditoria-externa`, `bi` |
| **V2/V3** | `marketplace` |

### Conta total de docs no projeto após v8

| Categoria | v7 | v8 (adiciona) | v8 total |
|---|---|---|---|
| Raiz canônica | 9 | — | 9 |
| Discovery | 17 | — | 17 |
| Conformidade | 9 | — | 9 |
| Segurança | 3 | — | 3 |
| Arquitetura | 10 | — | 10 |
| Operação | 13 | — | 13 |
| Governança | 13 | — | 13 |
| Família 6 calibração | 5 | — | 5 |
| Família 2 comum | 6 | — | 6 |
| Domínios (READMEs + personas) | 10 | +2 (`dados/`) | 12 |
| Módulos (docs por módulo × 8) | 152 (19 × 8) | +200 (25 × 8) | 352 (44 × 8 — exclui 4 docs já contados em metrologia/calibracao v7) |
| ADRs | 10 | — | 10 |
| Tutoriais dono | 3 | — | 3 |
| Templates | 9 | — | 9 |
| Outros | 10 | — | 10 |
| **TOTAL aproximado** | **~270** | **+~210** | **~480 docs** |

### O que NÃO foi feito em v8 (intencional)

- **Specs por feature** (`specs/<NNN-feature>/{spec,plan,tasks}.md`) dentro dos novos módulos — só criar quando feature entrar em desenvolvimento
- **ADRs específicas dos novos módulos** (`modulos/<mod>/adr/`) — só conforme decisões surgem
- **Novas OPs/INVs** — escopo da v8 é estrutural (módulos + 8 docs); regras invariantes vêm conforme os módulos forem detalhados
- **Repriorização das waves de v7** — Wave A original mantida; novos módulos Wave A são ADIÇÃO, não substituição
- **Reorganizar histórico v7** — esta atualização é estritamente aditiva

---

## O que mudou da v6 pra v7 (2026-05-17, noite +6h)

> v7 incorpora o **mapeamento de 25 módulos da lista funcional do Roldão**. Confronto entre lista funcional × docs existentes feito por 5 agentes Explore em paralelo. Resultados aplicados — **nenhum corte de escopo**. Adições estruturais grandes.

### Estrutura de domínios (NOVA — 5 domínios + 19 módulos)

| Domínio | Módulos | Status |
|---|---|---|
| `comercial/` | clientes, orcamentos, crm, contratos | ✅ README + personas + 4 × 8 docs |
| `operacao/` | os, chamados, agenda | ✅ README + personas + 3 × 8 docs |
| `financeiro/` | contas-receber, contas-pagar, comissoes, caixa-tecnico, fiscal | ✅ README + personas + 5 × 8 docs |
| `suporte-plataforma/` | equipamentos, produtos-pecas-servicos, estoque, fornecedores | ✅ README + personas + 4 × 8 docs |
| `rh-frota-qualidade/` | colaboradores, frota, qualidade | ✅ README + personas + 3 × 8 docs |
| `metrologia/` (existia v6) | calibracao | ✅ 5 docs especializados (cláusulas ISO) |

Cada módulo tem 8 docs: `glossario.md`, `prd.md`, `personas.md`, `metricas.md`, `modelo-de-dominio.md`, `contratos/{ui,api,exports}.md`.

### OPs novas (`opportunity-solution-tree.md` v?)

| ID | Tema | Wave | Motivo |
|----|------|------|--------|
| OP13 | Agenda gerencial completa | **MVP-1 Wave A** | Módulo 10 da lista; destrava OP3/OP1/OP15/OP16 |
| OP14 | Fornecedores + Compras | Wave C | Módulo 6 — gap total no discovery |
| OP15 | Orçamentos formal | Wave A (15.1, 15.4) + Wave B (15.2, 15.3) | Módulo 7 — antes só OP8 luz-fraca |
| OP16 | Chamados/Helpdesk dedicado | MVP-1 Wave B | Módulo 8 — antes embutido em OP3 |
| OP17 | Equipamentos master | MVP-1 Wave A | Módulo 4 — suporta OP2 certificado |

Total: 12 + 5 = **17 OPs**.

### INVs novos (`REGRAS-INEGOCIAVEIS.md`)

| ID | Tema |
|----|------|
| INV-021 | Pesos padrão com classe ISO 16834 + certificado próprio + validade |
| INV-022 | Verificação intermediária de padrão em uso ≤ intervalo de re-calibração |
| INV-023 | Comparação interlaboratorial (PT) registrado em perfil A |
| INV-024 | Cliente não pode ser duplicado dentro do tenant (dedup CPF/CNPJ) |
| INV-025 | Equipamento imutável em campos críticos pós-emissão de certificado |
| INV-026 | Preço de serviço não retroage a certificados emitidos |
| INV-027 | OS com máquina de estados não-reversível (transições explícitas) |

Total: 20 + 7 = **27 INVs**.

### ADRs reservadas viram reais

| ID | Antes | Agora |
|----|-------|-------|
| ADR-0004 | reservado | Sync mobile offline-first (regras conflito por entidade) |
| ADR-0005 | reservado | Engine de automações (caseiro sobre procrastinate + DSL fechada) |
| ADR-0006 | reservado | Feature flags (django-waffle + tabela tenant_features) |

Stubs `0004-reservado.md`, `0005-reservado.md`, `0006-reservado.md` removidos.

### Atualizações de status

Família 5 governança 100% materializada; Família 6 conformidade com fiscal + fiscal-contingencia ✅; Família 4 operação 11 docs criados; arquitetura cross-cutting 8 docs criados + anti-corrosion + integracoes-inter-modulos; integracoes-externas 7 parceiros documentados.

### Conta total de docs no projeto após v7

| Categoria | Aprox |
|---|---|
| Raiz canônica | 9 |
| Discovery | 17 |
| Conformidade | 9 |
| Segurança | 3 |
| Arquitetura | 10 (overview + 8 cross-cutting + anti-corrosion) |
| Operação | 13 |
| Governança | 13 |
| Família 6 calibração | 5 |
| Família 2 comum | 6 |
| Domínios novos (5 × README + personas) | 10 |
| Módulos (19 × 8 docs) | 152 |
| ADRs | 10 |
| Tutoriais dono | 3 |
| Templates | 9 |
| Outros (INDEX, INDICE, MAPA, CONVENCOES, painel, etc.) | 10 |
| **TOTAL aproximado** | **~270 docs** |

### O que NÃO foi feito em v7 (intencional)

- **Specs por feature (`specs/<NNN-feature>/{spec,plan,tasks}.md`)** dentro de cada módulo — só criar quando feature específica entrar em desenvolvimento
- **ADRs específicas de módulo** (`modulos/<mod>/adr/`) — só criar conforme decisões surgem
- **URS/IQ/OQ/PQ do módulo calibração** — só Wave A começar (`validacao-software.md` já indica)

---

## O que mudou da v5 pra v6 (2026-05-17)

> v6 é **atualização de status, não corte de escopo**. Nenhum doc foi removido ou rebaixado. O Roldão vetou explicitamente os cortes propostos pelo Auditor 5.

| Mudança | Tipo | Vindo de |
|---|---|---|
| Família 0: 15/15 artefatos marcados ✅ (estavam todos ⏳ no v5) | status real | inventário |
| Família 0: +2 artefatos novos (validacao-externa-documental, proximos-artefatos) | adição | trabalho 17/05 |
| Família 1: AGENTS.md ✅ encorpado (era ⏳ no v5) | gap fechado | Auditoria 4 lente 1+3 |
| Família 1: roteamento-dual ✅, orcamento-contexto ✅, output-styles ✅ | status real | inventário |
| Família 2: glossario-roldao.md (nome com sufixo decidido) | reconciliação | Auditoria 4 lente 2 |
| Família 2: painel-do-dono, como-os-agentes, MAPA ✅ | status real | inventário |
| Família 3 Arquitetura: anti-corrosion-layer.md como cross-cutting #9 ✅ | adição | trabalho 17/05 |
| Família 3 ADRs: 0007/0008/0009 incluídas (não previstas no v5) | adição | Portão 2 ADR-0001 |
| Família 3 ADRs: 0003 criada como stub + 0004/0005/0006 stubs reservados | reconciliação | Auditoria 4 lente 2+4 |
| Família 5: catálogo + 5 docs ✅; decisão "onde os auditores vivem" cravada (híbrido A+B) | gap fechado | Auditoria 4 lente 3 |
| Extras: INDICE, CONVENCOES, MAPA, tutoriais (3), .agent/, .specify/, README ✅ | status real | inventário |
| Caminho `_TEMPLATE/` corrigido (`docs/dominios/_TEMPLATE-dominio/modulos/_TEMPLATE/`) | reconciliação | Auditoria 4 lente 2 |
| Síntese das auditorias: adicionadas Auditorias 3 e 4 | histórico | sessões 16-17/05 |

**O que continua pendente como gap 🔴 prioritário (janela atual = dogfooding Balanças Solution):**
- ✅ `docs/prd.md` + `docs/faseamento-modulos.md` (criados 2026-05-17)
- ✅ Base de conformidade MVP-1 (`lgpd-rat`, `seguranca-dados`, `isolamento-multi-tenant`, `retencao-matriz`)
- ✅ 3 prompts de auditor (`auditor-{seguranca,qualidade,produto}-prompt.md`) + descritores em `.claude/agents/`
- ✅ Família 4 (Operação) inteira — 11 docs
- ✅ 5 hooks adicionais (anti-mascaramento, context-budget, INV-checker, tenant-id-validator, paths-frontmatter-validator)
- ✅ INDEX.yaml v2 atualizado
- ✅ 3 GitHub Actions (auditor-seguranca, auditor-qualidade, auditor-produto) — pendem secret `ANTHROPIC_API_KEY`
- ⏳ Família 6 calibração (`docs/dominios/metrologia/modulos/calibracao/conformidade-iso-17025.md` etc.)
- ⏳ Foundation F-A (4-6 semanas) com critérios da ADR-0001 Portão 3 — destrava Wave A. Sem spike descartável ([[nao-construir-codigo-descartavel]]).
- ⏳ Síntese final discovery: sair de DRAFT v3 → STABLE via **caminho B** (dogfooding)

**Diferidos pra V2 (decidido Roldão 2026-05-17 — ver [[sem-cliente-externo-na-janela-atual]]):**
- Cliente externo pago sob NDA / 3 cartas de intenção / Portão 1 ADR-0001 / R-001 ≤ 9
- Apólice cyber + RC profissional + DPO formal
- DPA-modelo + Termos de Uso público
- Dossiê de validação ISO 17025 do software por consultor RBC
- Pricing público em landing + trial self-service 30 dias

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
