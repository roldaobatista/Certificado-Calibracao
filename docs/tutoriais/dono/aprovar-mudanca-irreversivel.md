# Tutorial — aprovar mudança em paths irreversíveis (CODEOWNERS)

> Tutorial Diátaxis. Audiência: Roldão na primeira vez vendo pop-up "este PR mexe em path crítico — sua aprovação necessária".

---

## Por quê esse pop-up existe

Você tem 10 pastas/arquivos que são **a saída de emergência do sistema** — se alterados sem cuidado, abrem caminho pra:
- Desligar hooks de segurança (o agente pode rodar `rm -rf`)
- Afrouxar regras invioláveis (certificado emitido vira editável)
- Vazar dados entre clientes (multi-tenant quebrado)
- Comprometer conformidade fiscal/ISO

Por isso CODEOWNERS exige sua aprovação **mecânica** — mesmo que você não entenda 100% do código, o ato de clicar "aprovo" já é o valor (audit trail diz "humano viu").

---

## Os 10 paths protegidos

### Paths "anti-bypass de segurança":
| Path | O que protege |
|---|---|
| `.claude/hooks/` | Hooks que bloqueiam `rm -rf`, scanner de segredos. Desligar = abrir porta pra acidente sério. |
| `.claude/settings.json` | Permissões do Claude Code (o que pode fazer sem perguntar). |
| `.specify/memory/constitution.md` | Princípios não-negociáveis. Afrouxar = mudar o trilho. |
| `REGRAS-INEGOCIAVEIS.md` | Invariantes (INV-), regras de teste (TST-), segurança (SEC-). |
| `docs/conformidade/` | Conformidade ISO/LGPD/fiscal. Mudar afeta auditoria do CGCRE/ANPD/Receita. |

### Paths "núcleo financeiro de ERP":
| Path | O que protege |
|---|---|
| `financeiro/` | Código de NF-e, conciliação, fluxo de caixa. Bug aqui = problema fiscal real. |
| `auth/` | Login, RBAC. Bug aqui = vazamento entre usuários. |
| `tenant/` | Isolamento entre clientes (multi-tenant). Bug aqui = vazamento entre empresas. |
| `kms/` | Chaves criptográficas (AWS KMS). Bug aqui = perda de acesso a dados criptografados. |
| `migrations/` | Mudanças de estrutura do banco. Bug aqui = perda de dados ou corrupção. |

---

## Como o pop-up aparece

### No terminal do Claude Code:
Agente diz:
> "Pra completar essa tarefa preciso mexer em `REGRAS-INEGOCIAVEIS.md` (path protegido). Vou abrir PR e ele vai pausar esperando sua aprovação no GitHub."

### No GitHub:
PR fica em status `Awaiting review from @roldao`. GitHub bloqueia merge.

### No `painel-do-dono.md`:
Aparece seção 🚨 em vermelho:
> "Agente quer mudar `REGRAS-INEGOCIAVEIS.md`. Razão: adicionar nova invariante INV-012 ('toda emissão de certificado exige assinatura digital do signatário técnico'). Risco: nenhum — só ADICIONA regra mais restritiva."

---

## Como avaliar (mesmo sem ser técnico)

3 perguntas:

### 1. Está ADICIONANDO regra ou AFROUXANDO?
- **Adicionando** (ex: novo INV, novo TST) → geralmente seguro, pode aprovar.
- **Afrouxando** (ex: remover INV, relaxar hook, desligar bloqueio) → 🔴 DESCONFIE. Pergunte por quê.

### 2. O agente explicou em PT-BR claro o motivo?
- Sim, faz sentido → aprovar.
- Sim, mas não entendi → pedir reformulação ("explica de novo, mais simples").
- Não → exigir explicação ANTES de aprovar.

### 3. Algum dos 3 auditores-agentes vetou ou levantou CONCERNS?
- Se algum vetou → 🔴 NÃO aprovar sem entender o veto.
- Se levantaram CONCERNS → ler os CONCERNS, decidir.

---

## Quando dizer NÃO

- Você não entendeu o motivo.
- Auditor de segurança vetou.
- Mudança remove proteção sem ganho claro.
- Você suspeita que agente foi prompt-injected (input estranho de fora).

**Dizer NÃO nunca causa dano** — agente apenas não completa a tarefa. Você pode pedir abordagem alternativa.

---

## Como dizer "sim" / "não"

### No GitHub:
- "Sim" → clica em "Approve" e "Merge pull request"
- "Não" → clica em "Request changes" e comenta em PT explicando por quê

### No Claude Code (alternativo):
- "Pode aprovar PR #42"
- "Não aprovo PR #42; razão: [...]; faz de outro jeito"

---

## Próximos passos

- Você já leu os 3 tutoriais. Está pronto pra autorizar Rodada 0 Discovery.
- Volte pro `painel-do-dono.md` pra ver o que precisa de você agora.
