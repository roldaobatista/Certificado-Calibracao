# MAPA DO DONO

> **Pra quê:** os **7 documentos que o Roldão precisa ler/aprovar** ao longo da vida do projeto. Resto fica marcado "uso interno dos agentes" — você não precisa abrir.
>
> Sem este mapa, repositório com ~100 arquivos vira sobrecarga e Roldão delega 100% (Auditor 2 alertou).

---

## Os 7 docs obrigatórios pra você

| # | Documento | Quando ler | Pra quê |
|---|-----------|------------|---------|
| **1** | `discovery/sintese-final.md` | Quando Discovery terminar | Aprovar: cliente ideal, MVP-1, modelo de negócio, stack. Decisão estratégica. |
| **2** | `prd.md` | Pós-discovery, antes de código | Aprovar: visão consolidada do produto + user stories do MVP-1 + non-goals. |
| **3** | `painel-do-dono.md` | Toda semana | Status atual: o que agente fez, o que travou, o que decidiu sozinho, o que precisa de você. |
| **4** | `governanca/status-semanal.md` | Toda semana | Auto-gerado. Topo: "essa semana o módulo X precisa de você por Y". Escolha forçada, não buffet. |
| **5** | `operacao/go-live-checklist.md` | Antes de cada deploy em produção | Checklist em PT-BR pra você dar OK final. |
| **6** | `governanca/caminho-reclamacao.md` | Sempre que cliente reclama | Caminho: reclamação → triagem → tarefa pro agente → resposta ao cliente. |
| **7** | `../CHANGELOG.md` | Toda semana | "O que mudou no produto essa semana", em PT-BR. Único lugar onde você lê mudanças sem abrir código. |

---

## Quando vai aparecer pop-up pedindo sua aprovação (CODEOWNERS — D5)

10 paths que **PARAM e pedem você** antes de mudar:

### 5 paths "anti-bypass de segurança"
- `.claude/hooks/` — desligar freio de comando destrutivo
- `.claude/settings.json` — mudar permissões
- `.specify/memory/constitution.md` — afrouxar princípio não-negociável
- `REGRAS-INEGOCIAVEIS.md` — afrouxar invariante/regra
- `docs/conformidade/` — afetar conformidade ISO/LGPD/fiscal

### 5 paths "núcleo financeiro de ERP" (vão existir como código pós-stack)
- `financeiro/` — código de NF-e, conciliação, fluxo de caixa
- `auth/` — autenticação/autorização (RBAC)
- `tenant/` — isolamento entre clientes (multi-tenant)
- `kms/` — gestão de chaves (AWS KMS)
- `migrations/` — mudanças de estrutura do banco

**Quando agente pedir aprovação:** vai aparecer no `painel-do-dono.md` aviso em PT-BR explicando **o que está sendo afrouxado** e **por que** o agente pediu. Você não precisa entender o código — só decidir se o motivo faz sentido.

---

## O que você NÃO precisa abrir

Tudo o que não está nos 7 docs acima e fora dos 10 paths CODEOWNERS é **uso interno dos agentes**. Lista parcial:
- `.claude/`, `.agent/`, `.specify/`, `.github/`
- `docs/INDEX.yaml`, `docs/CONVENCOES-DOC.md`, `docs/arquitetura/`
- `docs/dominios/*/*` (exceto `prd.md` do módulo)
- `docs/seguranca/`, `docs/operacao/` (exceto `go-live-checklist.md`)
- ADRs (decisões técnicas)

**Se você quiser entender algum desses** → peça pro agente traduzir em PT-BR claro. NUNCA tente ler código direto.

---

## Tutoriais pra te ensinar a usar o sistema

- `tutoriais/dono/primeiro-pedido-ao-agente.md`
- `tutoriais/dono/ler-status-semanal.md`
- `tutoriais/dono/aprovar-mudanca-irreversivel.md`
