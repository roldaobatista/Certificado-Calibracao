---
owner: claude-code
revisado_em: 2026-05-18
proximo_review: 2026-08-18
status: stable
diataxis: reference
audiencia: agente
relacionados:
  - docs/adr/0000-uso-de-ia.md
  - docs/adr/0019-responsabilidade-codigo-agente-ia.md
  - REGRAS-INEGOCIAVEIS.md
---

# Controles compensatórios — código gerado por agentes IA

> **Pra quê:** apresentar a subscritor (RC profissional / cyber) + auditor LGPD/CGCRE + investidor a lista concreta de controles automatizados que substituem a "revisão linha-por-linha por humano". Cumpre Pilar 2 da ADR-0019. Sem este doc, modelo 100% agentes IA vira causa de exclusão clássica de apólice.
>
> **Origem:** parecer subagente `corretora-seguros-saas` durante auditoria PRD `equipamentos` (2026-05-18 manhã) + reforço pelo tech-lead US-EQP-005 R4 (2026-05-18 noite).

---

## Princípio

Cada commit gerado por agente IA passa por **8 controles automatizados** + **3 auditores Família 5** antes de mergear. Falha em qualquer controle BLOQUEIA o merge (sem `--no-verify`, sem `--skip-*`). Evidências de execução são preservadas em audit append-only.

---

## Os 8 controles

### Controle 1 — Hooks Claude Code pre-commit + pre-merge

**Localização:** `.claude/hooks/*.sh`

**Inventário (2026-05-18 noite, atualizado a cada Marco):**
- `block-destructive` — bloqueia rm -rf, drop table, git reset --hard, git push --force, no-verify
- `secrets-scanner` — varre o diff por API keys, tokens, credenciais
- `_test-runner` — executa 113+ casos de regressão nos demais hooks
- `INV-checker` — bloqueia migration/código que toca tabela com INV-NNN sem teste correspondente (TST-004)
- `tenant-id-validator` — toda query SQL/ORM tem `tenant_id` no WHERE (INV-TENANT-001)
- `anti-mascaramento` — bloqueia `skip()`, `xit()`, `@Disabled`, `assertTrue(true)`, `eslint-disable` sem justificativa
- `context-budget` — bloqueia bloat de docs
- `paths-frontmatter-validator` — rules em `.claude/rules/` exigem `paths:` no frontmatter
- `bus-envelope-validator` — eventos publicados com envelope mínimo
- `authz-check` — view nova exige `AuthorizationProvider.can()` (INV-AUTHZ-001)
- `provisioning-checkpoint-check` — módulo aceita request do tenant só após `BillingSaas.AssinaturaPronta` (INV-INT-007)
- `mock-in-production` — bloqueia `Mock*` em `settings.production`
- `migration-rls-check` — INV-TENANT-003 + INV-TENANT-004 (RLS ativa + policy explícita por tabela com `tenant_id`)
- `audit-immutability-check` — bloqueia DROP TRIGGER `auditoria_anti_*`, ALTER TABLE auditoria DISABLE RLS, TRUNCATE/DELETE em `auditoria`
- `pyproject-validator` — PEP 440 + Poetry extras
- `policy-test-coverage` — migration que cria policy RLS exige `# tests-coverage:` apontando happy+unhappy
- `audit-pii-salt-check` — hash de PII em audit obriga salt por tenant (anti-regressão FAIL Auditor Segurança Marco 1)
- **Wave A Marco 2 (a criar):** `equipamento-imutabilidade-check`, `qr-hmac-check`, `port-binding-validator`, `recebimento-provisorio-fk-check`

**Evidência:** `bash .claude/hooks/_test-runner.sh` deve retornar `113 ok, 0 falhas` (count atualiza a cada hook novo). Suite roda pre-commit + pre-merge.

### Controle 2 — Suite anti-regressão de invariantes (TST-004)

**Localização:** `tests/regressao/inv_*.py` (a criar Wave A — Marco 1 já tem cobertura embutida em `tests/clientes/`).

**Regra:** todo `INV-NNN` cravado em `REGRAS-INEGOCIAVEIS.md` exige ≥1 teste cujo nome cita o ID (`def test_inv_025_imutavel_pos_cert(...)`).

**Validação:** linter CI varre `REGRAS-INEGOCIAVEIS.md` + grepa `INV-NNN` em `tests/`. Falta de teste = build vermelho.

### Controle 3 — Auditores Família 5 pre-merge de Marco

**Localização:** `.claude/agents/auditor-{seguranca,qualidade,produto,drift-docs}.md` + prompts em `docs/governanca/auditor-*-prompt.md`.

**Quando:** ao fechar cada Marco. Cada auditor lê o diff completo + suite de testes + dossiê do Marco e devolve PASS/CONCERN/FAIL com justificativa.

**FAIL bloqueia fechamento.** CONCERN bloqueia só se gravidade crítica.

**Evidência:** trilha em `docs/governanca/trilha-auditoria-agentes.md`. Marco 1 clientes: 3 auditores aprovaram com 2 CONCERNs cosméticos endereçados + 1 FAIL crítico (hash de PII sem salt) endereçado.

### Controle 4 — Hook `INV-checker` integrado a code review

Bloqueia em pre-commit qualquer código que toca tabela cravada em `REGRAS-INEGOCIAVEIS.md` sem teste citando o INV-NNN.

**Evidência:** integrado a `.claude/hooks/INV-checker.sh` (já existe Marco 1).

### Controle 5 — Suite obrigatória para invariantes críticos com hooks dedicados

Quando uma invariante toca campo imutável regulado (ex: INV-025 imutabilidade pós-cert), hook dedicado bloqueia migration que altere o campo sem trigger PG correspondente + sem `# tests-coverage` apontando happy+unhappy.

**Exemplos atuais:**
- `migration-rls-check` (INV-TENANT-003)
- `policy-test-coverage` (genérico — exigência de teste happy+unhappy ao criar policy RLS)
- `audit-immutability-check` (INV-001 + auditoria_anti_*)
- **A criar Wave A Marco 2:** `equipamento-imutabilidade-check` (INV-025)

### Controle 6 — Trilha de auditoria por subagente

Cada parecer de subagente (`tech-lead-saas-regulado`, `advogado-saas-regulado`, `corretora-seguros-saas`, `consultor-rbc-iso17025`) é preservado no repositório em `docs/dominios/.../revisoes/*.md`. Imutável após merge (auditoria de drift).

**Evidência atual:** Marco 1 clientes tem 10 pareceres (5 US × 2 subagentes). Marco 2 equipamentos tem 16 pareceres (4 PRD + 12 US).

### Controle 7 — Documentação de gravidade por parecer

Cada parecer Família 5 explicita gravidade: PASS / CONCERN cosmético / CONCERN crítico / FAIL. FAIL bloqueia mergee no pre-merge do Marco.

**Padrão:** ver pareceres já em `docs/governanca/trilha-auditoria-agentes.md`.

### Controle 8 — Auditoria humana obrigatória em 5 casos-limite (Pilar 3 ADR-0019)

Humano licenciado com responsabilidade pessoal entra em:
1. Apólice SUSEP (corretora humana).
2. Parecer OAB (advogado humano com inscrição ativa).
3. Dossiê CGCRE (consultor humano credenciado).
4. Migração destrutiva em dados de produção do tenant.
5. Rotação manual de chaves KMS.

Marco 2 do `equipamentos` documenta dívidas regulatórias pendentes pra advogado humano em `docs/dominios/.../equipamentos/transferencia-aceite-presencial-marco2.md` + textos UX do scan público + termo de transferência v1.0-2026-05-18 antes do go-live.

---

## Evidências de execução nos últimos 90 dias (atualizar a cada Marco)

| Período | Marcos fechados | Hooks PASS | FAILs detectados | CONCERNs cosméticos | Auditores PASS |
|---|---|---|---|---|---|
| 2026-04-XX a 2026-05-17 | F-A + F-B | 88/88 (F-A) + 103/103 (F-B) | 8 (F-A drill 2026-05-18 — todos endereçados) | 0 | 3/3 PASS em ambos |
| 2026-05-18 | Wave A Marco 1 `clientes` | 113/113 | 1 (hash PII sem salt — endereçado) | 2 (mypy ignores + cobertura import 77%) | 3/3 PASS pós-endereçamento |
| Em curso | Wave A Marco 2 `equipamentos` | 113/113 (planejamento) | — | — | — |

---

## Como apresentar a um subscritor de seguro

1. Imprimir esta página + ADR-0019 + lista de hooks com count atual.
2. Mostrar repositório público com pareceres em `docs/dominios/.../revisoes/*.md`.
3. Demonstrar drill ao vivo: rodar `bash .claude/hooks/_test-runner.sh` na frente do subscritor (≤30s) + abrir `docs/governanca/trilha-auditoria-agentes.md`.
4. Apresentar `controles-compensatorios-codigo-ia.md` (este doc) como evidência de "due diligence + insurability".
5. Cláusula contratual de equiparação (ADR-0019 Pilar 1) anexa.

**Desconto esperado em prêmio (corretora-saas estimou):** 20-30% sobre baseline. Em capital R$ 1-3M RC + R$ 500k-2M cyber → R$ 2-7k/ano economizados.

---

## Como esta página evolui

- A cada novo hook ativo → adicionar linha em Controle 1 + bump count total.
- A cada Marco fechado → linha nova na tabela de evidências (Controles 1–8 + count auditores).
- A cada FAIL → registrar na tabela + endereçamento em commit atômico.
- A cada apólice cotada → registrar prêmio efetivo + desconto medido (validação retroativa do que `corretora-saas` estimou).
- Mudança nos 8 controles → ADR.
