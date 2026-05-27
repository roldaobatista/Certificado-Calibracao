---
owner: claude-code
revisado-em: 2026-05-27
status: aceito
superseded-by: 0028
aceito-em: 2026-05-27
---

# ADR-0019 — Responsabilidade civil + segurabilidade de código gerado por agentes IA

> **Status:** **ACEITO + SUPERSEDED-BY ADR-0028** (2026-05-27 — auditoria 10 lentes pré-Wave A, Onda PRE-A.2). Conteúdo desta ADR foi integrado na ADR-0028 (mapa coberturas Wave A) que é mais ampla (7 modalidades). Mantida como referência histórica + base conceitual de "cláusula afirmativa IA-affirmative coverage" que vai pra DPA-modelo-cap-responsabilidade.md cláusula 11. Ações concretas (apólice + minutas) ficam DIFERIDAS até produção real (memória `project_sem_contratacoes_externas_ate_producao`).
> **Autor:** Claude Code (orquestrador) + parecer subagente `corretora-seguros-saas`
> **Origem:** auditoria PRD `equipamentos` Wave A Marco 2 — parecer corretora B2: "modelo 100% agentes IA é diferencial mas vira **causa de exclusão clássica em RC profissional** se for tratado como atos dolosos do segurado. Seguradora pode argumentar 'ausência de revisão humana = neglect' e negar sinistro."
> **Depende de:** ADR-0000 (uso de IA)
> **Bloqueia:** contratação de apólice RC profissional E&O + cyber (não é bloqueante do MVP-1 dogfooding; é pré-condição do 1º tenant externo pago)
> **Relacionado:** ADR-0007 (camada domínio + gerador spec→código), `REGRAS-INEGOCIAVEIS.md` INV-001..051

---

## Glossário rápido (pra Roldão)

| Termo técnico | O que é, na prática |
|---|---|
| **RC profissional / E&O** | Seguro que cobre se o software do Aferê causar prejuízo ao cliente (erro técnico, omissão). É o seguro que segura o Aferê. |
| **Cyber insurance** | Seguro que cobre vazamento de dado, ataque hacker, incidente LGPD. |
| **Exclusão de cobertura** | Pretexto da seguradora pra não pagar — geralmente quando o "segurado fez algo que não devia". |
| **Equiparar a código humano** | Tratar código gerado por IA exatamente como código escrito por um funcionário. Mesma responsabilidade, mesma cobertura. |
| **Suite anti-regressão de invariantes** | Bateria de testes automatizados que garante que nenhum agente IA "esqueça" das regras críticas (INV-025, INV-049, etc) ao mexer no código. |

---

## Contexto

O Aferê opera com **modelo 100% agentes IA** (ADR-0000, memória `project_no_human_consultants`):
- 4 subagentes humanos-substitutos (`tech-lead-saas-regulado`, `advogado-saas-regulado`, `corretora-seguros-saas`, `consultor-rbc-iso17025`)
- 3 auditores Família 5 (Segurança, Qualidade, Produto)
- 1 orquestrador (Claude Code)
- Humano contratado apenas em 5 casos-limite (apólice SUSEP, parecer OAB, dossiê CGCRE, etc.)

Risco identificado pela corretora (R-099, R-100 da auditoria PRD `equipamentos`):

1. **Bug introduzido por agente IA viola INV-025** (imutabilidade pós-cert) → tenant emite cert com dados alterados → CGCRE supervisiona → tenant é autuado → tenant aciona Aferê.
2. **Seguradora E&O recebe sinistro** e argumenta: "Aferê não tem código revisado por humano; ausência de revisão humana caracteriza neglect; cláusula de exclusão aplicável; sinistro negado."
3. Aferê fica solidário (R-018) sem cobertura efetiva.

Este risco **não existe** se seguradora aceitar de antemão que código de agente IA é equiparado a código humano para fins contratuais e securitários — desde que **controles compensatórios** estejam em vigor.

---

## Decisão

Adotar **3 pilares** para garantir segurabilidade do código gerado por agentes IA + responsabilizar o Aferê como editor do software:

### Pilar 1 — Declaração contratual de equiparação

Adicionar **cláusula padrão** nos contratos Aferê↔tenant (DPA + ToS + addendum) e na proposta apresentada a seguradoras:

> **Cláusula — Código gerado por agentes de IA.**
> Código gerado por agentes de inteligência artificial operados pelo Aferê é equiparado, para todos os efeitos contratuais, regulatórios e securitários, a código escrito por funcionário humano do Aferê. Bugs, omissões ou erros técnicos introduzidos por agentes de IA seguem o mesmo regime de Responsabilidade Civil Profissional (Errors & Omissions) e Cyber Risk. O Aferê reconhece-se como **editor do software** independente da forma de geração do código.

### Pilar 2 — Controles compensatórios automatizados (substituem "revisão humana de cada linha")

Para neutralizar o argumento "ausência de revisão humana = neglect":

| Controle | Onde mora | Quando ativa |
|---|---|---|
| **Hooks Claude Code** | `.claude/hooks/*.sh` (hoje 15 ativos, 103/103 testes) | Pre-commit + pre-merge + pre-push |
| **Auditores Família 5** | `.claude/agents/auditor-{seguranca,qualidade,produto,drift-docs}.md` | Pré-merge + a cada fechamento de Marco |
| **Suite anti-regressão de invariantes** | `tests/regressao/inv_*.py` | CI a cada commit |
| **Hook `INV-checker`** | `.claude/hooks/INV-checker.sh` | Pre-commit — bloqueia código que toca tabela com INV-NNN sem teste correspondente |
| **TST-004** (já cravado em `REGRAS-INEGOCIAVEIS.md`) | Linter CI | Todo INV-NNN crítico exige ≥1 teste cujo nome cita o ID |
| **Suite obrigatória pra invariantes críticos pós-cert** | A criar — hook `equipamento-imutabilidade-check.sh` análogo a `migration-rls-check.sh` | Pre-merge em qualquer migration tocando tabela `equipamento*` |
| **Trilha de auditoria por subagente** | `docs/governanca/trilha-auditoria-agentes.md` | A cada parecer subagente |
| **Documentação de gravidade (PASS/CONCERN/FAIL)** | Cada parecer Família 5 explicita | Imutável pós-merge |

Doc visível ao subscritor: `docs/governanca/controles-compensatorios-codigo-ia.md` (a criar — cataloga os 8 controles acima + evidências de execução nos últimos 90 dias).

### Pilar 3 — Auditoria humana obrigatória em 5 casos-limite

Mantém o que memória `project_no_human_consultants` já estabelece, mas torna **público em contrato**:

1. Apólice SUSEP (corretora humana licenciada).
2. Parecer OAB (advogado humano com inscrição ativa) — emissão de notificações jurídicas, defesa em processos.
3. Dossiê CGCRE (consultor humano credenciado) — antes de submissão à acreditação RBC.
4. Migração destrutiva em dados de produção do tenant (DROP COLUMN/TRUNCATE/recriação de schema) — assinatura A3 do Roldão obrigatória.
5. Rotação manual de chaves KMS (operação direta no console AWS).

---

## Trade-offs

- ✅ Permite contratação de apólice E&O + cyber sem cláusula de exclusão por "ausência de revisão humana".
- ✅ Mantém modelo 100% agentes IA — controles compensatórios são automatizados, não exigem time de devs humanos.
- ✅ Documenta evidência para auditoria (subscritor, CGCRE, ANPD) — não fica "palavra contra palavra".
- ❌ Custo adicional de manter `controles-compensatorios-codigo-ia.md` atualizado a cada release.
- ❌ Subscritor pode pedir prêmio mais alto inicialmente (sem precedente no mercado BR) — mitigação corretora indica desconto de 20-30% pelos controles, líquido pode ser flat ou abaixo do baseline.

---

## Non-goals

- NÃO abolir a categoria "5 casos-limite" — humano licenciado continua obrigatório nesses casos.
- NÃO substituir auditores Família 5 por subscritor humano externo — Família 5 é interna ao Aferê.
- NÃO declarar que código de IA é "perfeito" ou "isento de bugs" — exatamente o oposto: declara que está **coberto pelos mesmos seguros que código humano**.

---

## Critérios de validação

1. Cláusula do Pilar 1 incorporada a `docs/conformidade/comum/dpa-modelo.md` antes do 1º tenant externo.
2. Doc `docs/governanca/controles-compensatorios-codigo-ia.md` criado com lista dos 8 controles + procedimento de captura de evidência.
3. Hook `equipamento-imutabilidade-check.sh` criado quando Wave A Marco 2 começar a codar (análogo a `migration-rls-check.sh`).
4. Suite anti-regressão `tests/regressao/inv_*.py` ganha cobertura ≥80% sobre INVs cravadas em `REGRAS-INEGOCIAVEIS.md` antes do 1º tenant externo.
5. Briefing pra corretora (Marsh/AON Tech/Howden Brasil — recomendação subagente `corretora-seguros-saas`) inclui apresentação desses 3 pilares.

---

## Riscos / Mitigações

| Risco | Mitigação |
|---|---|
| Seguradora recusa apesar dos 3 pilares | Trocar de seguradora; mercado BR tem 5+ subscritores especializados em Tech E&O |
| Cliente externo se sentir desconfortável com "100% IA" | Cláusula contratual transparente + showcase dos controles compensatórios |
| Subscritor pede revisão humana de algumas categorias críticas (financeiro, fiscal) | Aceitar — `.claude/CODEOWNERS` já marca esses paths; Pilar 3 expande pra 6+ casos-limite |
| Bug real entra em produção mesmo com 8 controles | Apólice cobre (esse é o ponto); audit trail + RIPD + comunicação ANPD/cliente seguem fluxo padrão |

---

## Como evolui

- Sempre que novo INV crítico for cravado em `REGRAS-INEGOCIAVEIS.md`, suite anti-regressão ganha teste correspondente automaticamente (TST-004).
- Sempre que hook novo for adicionado, `controles-compensatorios-codigo-ia.md` ganha linha + bumps na lista de evidências.
- Revisão anual da apólice avalia se algum controle precisa fortalecer (com base em sinistros próprios ou de mercado).
