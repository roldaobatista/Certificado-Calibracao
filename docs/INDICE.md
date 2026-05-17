# Índice geral — docs/

> **Sitemap humano** do projeto. Mapa pra agente novo, auditor humano, ou Roldão saber onde achar cada coisa.
>
> Para versão lida por agente (machine-readable com tokens estimados), ver `docs/INDEX.yaml`.

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
- `adr/*.md` (a criar)

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
| 0 — Discovery | `discovery/` | ⏳ 15 cabeçalhos prontos pra preencher (Rodada 0) |
| 1 — Contrato dos agentes | `../CLAUDE.md`, `../AGENTS.md`, `../.claude/`, `roteamento-dual.md`, `orcamento-contexto.md`, `INDEX.yaml` | 🟡 parcial |
| 2 — Produto | `comum/`, `dominios/`, `prd.md` (a criar), `glossario.md` (a criar) | ⏳ pós-discovery |
| 3 — Arquitetura + Segurança | `adr/`, `arquitetura/`, `seguranca/`, `comum/integracoes-*` | ⏳ pós-discovery |
| 4 — Operação | `operacao/` | ⏳ pós-stack |
| 5 — Governança IA | `governanca/`, `plano-defesas-anti-erros-ia.md`, `../.specify/memory/constitution.md` | 🟡 parcial |
| 6 — Conformidade | `conformidade/comum/`, `dominios/metrologia/modulos/calibracao/` (a criar) | ⏳ |
| 7 — Evolução pós-MVP | `evolucao/` | ⏳ lazy |
| 8 — Docs externos | `externos/` | ⏳ lazy |
| Extra — Sessão/handoff | `../.agent/`, `../.github/`, `tutoriais/dono/` | 🟡 parcial |

---

## Templates

- `dominios/_TEMPLATE-dominio/` — estrutura padrão de domínio novo
- `dominios/_TEMPLATE-dominio/modulos/_TEMPLATE/` — estrutura padrão de módulo novo

---

## Convenções

Ver `CONVENCOES-DOC.md`.

## Como este índice evolui

Doc criado → adicionar entrada aqui. Doc descontinuado → remover. Manter linhas curtas (≤ 150 chars).
