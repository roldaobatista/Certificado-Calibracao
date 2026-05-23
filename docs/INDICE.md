# Índice geral — docs/

> **Sitemap humano** do projeto. Mapa pra agente novo, auditor humano, ou Roldão saber onde achar cada coisa.
>
> Para versão lida por agente (machine-readable com tokens estimados), ver `docs/INDEX.yaml`.
>
> **Atualizado v9 (2026-05-23 — pós Foundation F-A+F-B + Marco 1 + Marco 2 fechados, auditoria projeto-inteiro 10 lentes):** Foundation entregue; 30 ADRs ativas (0000..0032 com 3 novas Onda 1 saneamento); ~480 docs estruturais + Family 0 Discovery STABLE; 25 hooks ativos / 207 casos verdes; 10 auditores Família 5.

---

## Por audiência

| Audiência | Comece por | Depois |
|---|---|---|
| **Roldão (dono não-técnico)** | `painel-do-dono.md` | `MAPA-DO-DONO.md` → `tutoriais/dono/` |
| **Agente de IA (Claude/Codex)** | `../CLAUDE.md` | `../AGENTS.md` → `../REGRAS-INEGOCIAVEIS.md` → `INDEX.yaml` |
| **Auditor humano (CGCRE, cliente corporativo, advogado)** | `governanca/catalogo-auditores.md` | `conformidade/` → `plano-defesas-anti-erros-ia.md` |
| **Regulador (INMETRO/ANPD/Receita)** | `conformidade/comum/lgpd-rat.md` | `dominios/metrologia/modulos/calibracao/conformidade-iso-17025.md` (quando existir) |
| **Cliente final (usuário do produto)** | `externos/manual-cliente.md` (lazy) | — |

---

## Por tipo (Diátaxis)

### Tutorial — aprenda fazendo
- `tutoriais/dono/primeiro-pedido-ao-agente.md`
- `tutoriais/dono/ler-status-semanal.md`
- `tutoriais/dono/aprovar-mudanca-irreversivel.md`

### How-to — resolva tarefa específica
- `operacao/runbook.md` (a criar)
- `operacao/dr-plan.md` (a criar)
- `governanca/caminho-reclamacao.md` (a criar)

### Reference — consulte fato
- `INDICE.md` (este)
- `INDEX.yaml`
- `CONVENCOES-DOC.md`
- `MAPA-DO-DONO.md`
- `../REGRAS-INEGOCIAVEIS.md`
- `comum/glossario.md` (a criar)
- `comum/automacoes-catalogo.md` — 13 ações do engine de automação
- `adr/*.md` (**32 ADRs ativas — 0000 a 0032**; última batch Onda 1 saneamento 2026-05-23: ADR-0030 vigência temporal, ADR-0031 soft-delete em 3 padrões, ADR-0032 FK cross-módulo + ReferenciaPIIAnonimizavel)
- `orcamento-financeiro.md` — projeção ano 1/3/5
- `dominios/financeiro/modulos/billing-saas/calculadora-fatura.md` — algoritmo de fatura composicional + 30 casos

### Explanation — entenda o porquê
- `documentos-do-projeto.md` (este mapa)
- `plano-defesas-anti-erros-ia.md`
- `ambiente-claude-code.md`
- `comum/governanca-modelo-comum.md` (a criar)
- `roteamento-dual.md`

---

## Por família (ver `documentos-do-projeto.md` v5 pra detalhes)

| Família | Pasta | Status |
|---|---|---|
| 0 — Discovery | `discovery/` | ✅ STABLE v1.0 (sintese-final fechada 2026-05-17; Caminho A diferido pra V2) |
| 1 — Contrato dos agentes | `../CLAUDE.md`, `../AGENTS.md`, `../.claude/`, `roteamento-dual.md`, `orcamento-contexto.md`, `INDEX.yaml` | ✅ stable (25 hooks ativos, 10 auditores Família 5, 4 humano-substitutos) |
| 2 — Produto | `comum/`, `dominios/` (48 módulos com 8 docs cada), `prd.md` (stable), `glossario-roldao.md` | ✅ stable (PRD raiz stable 2026-05-23; 46/48 PRDs ainda draft preenchimento US/AC Onda 5) |
| 3 — Arquitetura + Segurança | `adr/` (30 ADRs), `arquitetura/`, `seguranca/`, `comum/integracoes-inter-modulos.md` v10 | ✅ stable (Foundation F-A+F-B fechadas; anti-corrosion-layer.md v3 com 18 portas) |
| 4 — Operação | `operacao/` | 🟡 parcial (setup-local.md ✅; runbook/dr-plan pendentes pré-Wave A produção) |
| 5 — Governança IA | `governanca/` (10 auditores Família 5 stable), `plano-defesas-anti-erros-ia.md`, `../.specify/memory/constitution.md` | ✅ stable |
| 6 — Conformidade | `conformidade/comum/` (LGPD-RAT, retenção, DPA modelo, transferência internacional, papéis multi-tenant, 4-party, finalidades, DPIA modelos), `dominios/metrologia/modulos/calibracao/` (conformidade-iso-17025, garantia-validade-7.7, validacao-software, registros-tecnicos-7.5, responsabilidade-tecnica) | 🟡 parcial (Onda 7 pré-1º tenant externo: ToU/PoP/DPO/DPAs sub-operadores) |
| 7 — Evolução pós-MVP | `evolucao/` | ⏳ lazy |
| 8 — Docs externos | `externos/` | ⏳ lazy |
| Extra — Sessão/handoff | `../.agent/CURRENT.md`, `../.github/CODEOWNERS` (D5 retrofit 2026-05-23), `tutoriais/dono/` | ✅ stable |

---

## Por domínio (sitemap — v8 com 48 módulos)

Cada módulo abaixo recebe os 8 docs padrão: `glossario.md`, `prd.md`, `personas.md`, `metricas.md`, `modelo-de-dominio.md`, `contratos/{ui,api,exports}.md`. **Negrito = adicionado na v8.**

### `dominios/comercial/`
- `clientes/`, `orcamentos/`, `crm/`, `contratos/`
- **`portal-cliente/`** — Wave A (MVP-1) — cliente externo consulta OS/certificado/financeiro
- **`marketplace/`** — V2/V3 — apps e parceiros
- **`precificacao/`** — Wave B — régua de preços e política comercial
- **`sla-contratual/`** — Wave B — cláusulas SLA por contrato/cliente
- **`comunicacao-omnichannel/`** — Wave B — WhatsApp/e-mail/SMS

### `dominios/operacao/`
- `os/`, `chamados/`, `agenda/`
- **`garantia/`** — Wave B
- **`projetos/`** — Wave B — instalação, retrofit, mudança de planta
- **`base-conhecimento/`** — Wave A (MVP-1, acoplado a OS/Chamados)
- **`capacity-planning-operacional/`** — Wave B — carga técnicos/laboratório
- **`app-tecnico/`** — Wave A (MVP-1) — app offline-first (ADR-0003 + ADR-0004)

### `dominios/financeiro/`
- `contas-receber/`, `contas-pagar/`, `comissoes/`, `caixa-tecnico/`, `fiscal/`
- **`billing-saas/`** — Bloqueador antes do 1º cliente externo pago
- **`custeio-real/`** — Wave B
- **`despesas/`** — Wave B
- **`relatorios-financeiros/`** — Wave B — DRE gerencial + fluxo de caixa

### `dominios/suporte-plataforma/`
- `equipamentos/`, `produtos-pecas-servicos/`, `estoque/`, `fornecedores/`
- **`onboarding/`** — Wave B — onboarding self-service de tenant
- **`configuracoes-sistema/`** — Wave B
- **`automacoes-bpm/`** — Wave B — motor BPM sobre ADR-0005
- **`engenharia-tecnica/`** — Wave B — procedimentos/padrões internos
- **`gestao-documental/`** — Wave B — DMS interno (link WORM)
- **`suporte-saas/`** — Wave B — tickets internos do Aferê
- **`release-management/`** — Wave B — changelog visível
- **`acesso-seguranca/`** — Wave A (MVP-1) — RBAC, MFA, audit log

### `dominios/metrologia/`
- `calibracao/` (PRD completado na v8)
- **`licencas-acreditacoes/`** — Wave B — RBC, NIT-DICLA, escopo acreditado
- **`certificados/`** — Wave A (MVP-1) — ciclo de vida do certificado, hoje embutido em `calibracao/`

### `dominios/rh-frota-qualidade/`
- `colaboradores/`, `frota/`, `qualidade/`
- **`seguranca-trabalho/`** — Wave B — SST/EPI/ASO/CIPA/NR-12/NR-35
- **`treinamentos/`** — Wave B — matriz competências, certificações
- **`auditoria-externa/`** — Wave B — suporte a auditorias RBC/ISO/fiscal/cliente

### `dominios/dados/` (NOVO v8)
- **`bi/`** — Wave B — analytics, dashboards, camada semântica, exports analíticos

---

## Templates

- `dominios/_TEMPLATE-dominio/` — estrutura padrão de domínio novo
- `dominios/_TEMPLATE-dominio/modulos/_TEMPLATE/` — estrutura padrão de módulo novo

---

## Convenções

Ver `CONVENCOES-DOC.md`.

## Como este índice evolui

Doc criado → adicionar entrada aqui. Doc descontinuado → remover. Manter linhas curtas (≤ 150 chars).
