# HARNESS_PATCHPLAN — Correções ao HARNESS_DESIGN.md

> **Propósito:** lista executável de correções ao `HARNESS_DESIGN.md` a partir da análise crítica consolidada com o PRD v1.8. Cada item é uma task com racional, critério de aceite e referência à seção do PRD que motiva a correção.
>
> **Política:** não reescrever o `HARNESS_DESIGN.md` antes de cada P0 ser revisado e aprovado. Este arquivo é o plano de intervenção; o design original permanece como histórico auditável.
>
> **Prioridades:**
> - **P0** — hard blocker de *go-live* regulatório. Sem isso, o harness gera dívida jurídica/técnica grave.
> - **P1** — estrutural, mas tolera uma iteração após o bootstrap.
> - **P2** — refinamento de consistência e ergonomia.

---

## P0 — Correções obrigatórias antes de usar o harness

### P0-1 · Formalizar o backend como peça de primeira classe

**Problema.** O monorepo no §2.4 do `HARNESS_DESIGN.md` lista `apps/web`, `apps/android`, `apps/portal` e `packages/*`, mas não tem `apps/api`. O PRD §6.2 exige "backend técnico" como dono de autenticação, RBAC, regras de negócio, cálculo consolidado, emissão oficial e APIs. Sem esse componente formalizado, regra normativa vaza para web e Android.

**Correção.**
- Adicionar em `apps/` um serviço `api` (ou `services/backend`) com ownership explícito.
- Criar agente **`backend-api`** (9º agente) em `.claude/agents/` com escopo: auth, RBAC, workflows de OS, emissão oficial, assinatura/QR, reemissão, sync server-side.
- Mover regras normativas atualmente implícitas em `packages/normative-rules` para execução no backend; o pacote fica como *library* consumida pelo `apps/api` — não por `apps/web` nem `apps/android` diretamente.
- Atualizar a tabela de subagentes (§2.3) para refletir o novo owner.

**Aceite.**
- Diagrama do monorepo atualizado inclui `apps/api` com owner `backend-api`.
- Tabela de agentes lista 9 papéis (não 8) e nenhum outro agente tem permissão de escrita em `apps/api/src/domain/**`.
- `CLAUDE.md` raiz proíbe que web/Android repliquem regra de emissão — consumo só via contratos em `packages/contracts`.

**Referências PRD:** §6.2, §6.3, §7.1, §7.7, §7.10.

---

### P0-2 · Pipeline de *normative package* versionado e assinado

**Problema.** O PRD §16 exige que cada certificado grave o "normative package" vigente (DOQ-CGCRE, NIT-DICLA, Portaria 157/2022, RTM, ILAC G8 etc.) com reprodutibilidade histórica. No harness atual, isso aparece só como eval e como escopo tangencial do `regulator`. Falta o *pipeline* de criação → revisão → aprovação → diff → assinatura → release do pacote.

**Correção.** Criar, dentro de `/compliance/normative-packages/`, o fluxo formal:
1. `drafts/<YYYY-MM-DD>-<slug>.yaml` — proposta de alteração normativa.
2. `/spec-norm-diff <draft>` — slash-command que gera diff semântico contra o pacote vigente e impacto em §9 (regras de bloqueio).
3. Revisão obrigatória por 2 aprovadores humanos (PR template dedicado).
4. Assinatura do pacote com chave em KMS; hash publicado em `releases/`.
5. `apps/api` só carrega pacotes assinados e válidos; agente `backend-api` bloqueia consumo de pacote unsigned.
6. Cada certificado grava `normative_package.hash` + `version` + `effective_date`.

**Aceite.**
- Tentativa de deploy com pacote não assinado falha no CI.
- Teste de reprodutibilidade: recarregar um certificado antigo reaplica o pacote da época (não o atual).
- ADR registra a política de versionamento e o SLA de atualização (comitê, watchlist, janela de revalidação).

**Referências PRD:** §16.1, §16.2, §16.3, §11.8.

---

### P0-3 · Dossiê formal de validação contínua

**Problema.** O §4 do `HARNESS_DESIGN.md` fala em "eval harness" com cenários regulatórios, mas isso é *testing*, não *validação regulatória*. O PRD exige, para o MVP, protocolo formal, rastreabilidade requisito → teste, evidências arquivadas, revalidação por mudança relevante.

**Correção.** Criar `/compliance/validation-dossier/` com estrutura:
- `requirements.yaml` — fonte única de cada requisito (PRD §13, §16, normativo) com ID estável (ex.: `REQ-§9.3-BLOCK-PADRAO-VENCIDO`).
- `traceability-matrix.yaml` — mapeamento `requirement_id → spec_id → test_id → evidence_path`. Gerado automaticamente e versionado.
- `evidence/<req_id>/<run_timestamp>/` — artefatos de cada execução de AC (logs, PDFs, screenshots, hashes de banco).
- `revalidation-triggers.md` — política formal: quando uma mudança exige revalidação (ex.: alteração no pacote normativo, nova versão da engine de incerteza, mudança em template regulatório).
- Agente `qa-acceptance` passa a ter responsabilidade **dupla**: rodar testes **e** arquivar evidências no dossiê.

**Aceite.**
- Todo requisito do PRD §13 tem entrada em `requirements.yaml` com ao menos 1 teste ligado.
- PR que altera código em `packages/engine-uncertainty` ou `packages/normative-rules` é bloqueado sem atualização da matriz.
- Relatório de cobertura regulatória é gerado por CI a cada merge.

**Referências PRD:** §11.6, §13, §16.

---

### P0-4 · Hard gates de multitenancy e trilha imutável

**Problema.** O PRD §6.6, §7.10 e §11.3 exigem RLS, testes anti-vazamento, linter contra SQL sem `organization_id`, hardening fail-closed, fuzz semanal, audit log com hash chain e storage WORM com checkpoints assinados. No harness atual, isso é eval genérica — não é *guardrail* de pipeline.

**Correção.** Promover a hard blockers de PR (hooks `PreToolUse` + CI):
- **Tenant-safe SQL linter**: regra customizada que quebra build em qualquer query ou policy sem `organization_id`. Owner: `db-schema`.
- **RLS policy tests**: suite obrigatória em `evals/tenancy/` rodada em CI com 2+ tenants sintéticos; falha se qualquer linha vazar.
- **Audit log hash-chain verifier**: job diário que recomputa a cadeia e bloqueia release se houver divergência.
- **WORM storage check**: fail-closed se o *bucket* de audit perder configuração de retenção/*object lock*.
- **Fuzz semanal**: pipeline agendada que injeta payloads cross-tenant e falha se isolation quebrar.

**Aceite.**
- Abrir PR com query sem `organization_id` → CI falha com mensagem específica.
- Dry-run de alteração em audit log gera erro de hash-chain quebrada.
- Documentação desses gates fica em `/compliance/guardrails.md`.

**Referências PRD:** §6.6, §7.10, §11.3, §11.6.

---

### P0-5 · Copy-lint regulatório (claims comerciais)

**Problema.** O PRD proíbe explicitamente claims como "passa em qualquer auditoria" e "100% conforme"; ainda assim, o wireframe da home no próprio PRD contém a frase proibida. Sem um linter automático, esse risco se propaga para site, e-mails, onboarding e portal.

**Correção.** Criar `packages/copy-lint/` com:
- Lista de termos proibidos + padrões regex (ex.: `/\bpassa(?:m)? em qualquer auditoria\b/i`, `/100\s*%\s*conforme/i`, `/garantimos? (ISO|acreditação)/i`).
- Hook `PreToolUse` e CI step que varrem: `apps/web/**/*.{tsx,md,mdx}`, `apps/portal/**`, `apps/api/templates/emails/**`, `/compliance/**`, `README.md`, `ideia.md`, `PRD.md`.
- Agente novo ou escopo no `docs`: **`copy-compliance`** — revisa e sugere alternativas dentro do claim-set aprovado.
- Claim-set aprovado vive em `/compliance/approved-claims.md` com revisão jurídica datada.

**Aceite.**
- CI falha ao detectar claim proibido em qualquer dos paths acima.
- PR de copy novo exige aprovação do agente `copy-compliance` + revisor humano.
- O wireframe do PRD é corrigido como primeira aplicação do linter (teste de fogo).

**Referências PRD:** §1.2, §2.3, §7.15 (site), §14 (riscos), análise consolidada C2.

---

### P0-6 · Agente `product-governance` (gate de merge regulatório)

**Problema.** Nenhum dos 8 agentes atuais tem mandato transversal para bloquear merge por violação de política regulatória, ausência de rastreabilidade ou claim comercial arriscado. O `qa-acceptance` só checa testes; o `regulator` interpreta normas mas não governa release.

**Correção.** Criar **`product-governance`** (10º agente, contando `backend-api`) com:
- **Sem permissão de escrita em código**. Só escreve em `/compliance/**` e em PR reviews.
- Checklist obrigatório por PR: matriz requisito→spec→teste→evidência atualizada? Pacote normativo impactado? Copy-lint verde? Guardrails de multitenancy verdes? Release notes regulatórias preenchidas?
- Autoridade de *hard block* via GitHub CODEOWNERS em `/compliance/**` e em arquivos-chave de `apps/api/src/domain/emission/**`.

**Aceite.**
- PR sem aprovação do `product-governance` em áreas protegidas é mergeado → CI falha.
- Checklist é gerado automaticamente no corpo do PR.
- Agente registra em `/compliance/release-norm/<version>.md` o veredito de cada release.

**Referências PRD:** §7.10, §11.6, §13, §16.

---

## P1 — Estrutural, tolera 1 iteração pós-bootstrap

### P1-1 · Simulador determinístico de sync/conflito offline

**Problema.** O harness menciona "10k eventos offline + perda de rede + idempotência", mas o PRD exige event sourcing por OS, idempotência por `(device_id, client_event_id)`, *optimistic locking* por agregado, lock exclusivo por OS na assinatura e matriz formal de conflitos.

**Correção.** Criar `evals/sync-simulator/`:
- Motor determinístico (seed fixo) que gera traces de N dispositivos concorrentes.
- Matriz de conflito explícita: mesmo OS editada em 2 dispositivos; assinatura em 1 dispositivo enquanto outro edita; reemissão vs nova emissão.
- Propriedades verificadas: convergência, não-divergência de hash-chain, respeito a lock de assinatura.
- Rodado em CI com seeds canônicos + seeds aleatórios semanais.

**Aceite.** 100% dos cenários da matriz são cobertos; falha determinística reproduz com o seed salvo.

**Referências PRD:** §7.7, §10 (sync_events), §11.3.

---

### P1-2 · Política formal de Tier 3 (cloud agents)

**Problema.** O harness propõe cloud agents (Claude Code Web, Copilot Coding Agent, Jules) para drain overnight. Em domínio LGPD com dados de laboratório/clientes, isso exige restrição dura.

**Correção.** Criar `/compliance/cloud-agents-policy.md` com:
- **Allowlist de paths** que cloud agents podem tocar: `apps/web/ui/**` (componentes puros), `docs/**`, `tests/unit/**`.
- **Blocklist absoluta**: `apps/api/**`, `packages/engine-uncertainty/**`, `packages/normative-rules/**`, `packages/db/**`, `/compliance/**`, qualquer seed com dados reais.
- Cloud agent só atua sobre *fixtures* sintéticas; hook que bloqueia push se fixture contiver CPF/CNPJ reais ou nome de cliente conhecido.
- Auditoria: todo PR de cloud agent leva label `cloud-agent` e exige review humano + `product-governance`.

**Aceite.** Tentativa de cloud agent editar path bloqueado falha no *pre-receive* hook do repo.

**Referências PRD:** §11.3, §11.4.

---

### P1-3 · Diretório `/compliance/` como artefato primeiro

**Problema.** Hoje compliance está misturado com `evals/` e `adr/`. Precisa ser camada explícita e separada de "código que implementa".

**Correção.** Estrutura canônica:
```
/compliance/
├─ normative-packages/       # P0-2
├─ validation-dossier/       # P0-3
├─ release-norm/             # veredito por release (P0-6)
├─ legal-opinions/           # pareceres datados
├─ approved-claims.md        # P0-5
├─ cloud-agents-policy.md    # P1-2
└─ guardrails.md             # P0-4
```

**Aceite.** Árvore criada e referenciada em `CLAUDE.md` raiz como leitura obrigatória para agentes `regulator`, `product-governance`, `lgpd-security`, `copy-compliance`.

---

### P1-4 · Roadmap por fatias verticais auditáveis

**Problema.** O roadmap de 4 semanas é otimista demais para o escopo do PRD.

**Correção.** Substituir por sequência de fatias verticais, cada uma com dossiê de validação fechado antes da próxima:

| Fatia | Escopo | Gate de saída |
|-------|--------|----------------|
| V1 | Emissão **Tipo B ou C** em ambiente controlado (sem sync, sem Tipo A) | Dossiê V1 fechado; 100% AC §13 do Tipo B/C verdes |
| V2 | Sync offline-first robusto (simulador P1-1 verde) | Matriz de conflitos 100% coberta |
| V3 | **Tipo A** com escopo/CMC e selo Cgcre/RBC | `regulator` aprova; `product-governance` libera |
| V4 | Reemissão controlada (§7.10 + ISO 17025 §7.8.8) | Hash-chain preservada; testes de imutabilidade verdes |
| V5 | Módulo Qualidade completo (§7.9) | Auditoria interna dry-run aprovada |

**Aceite.** Nenhuma fatia inicia sem gate de saída da anterior documentado em `/compliance/release-norm/`.

---

## P2 — Refinamento

### P2-1 · Alinhar nomenclatura de agentes
Revisar `.claude/agents/*.md` para que cada agente declare explicitamente: specs que lê, paths que escreve, paths bloqueados, tools permitidos. Evita deriva de escopo.

### P2-2 · Slash-commands regulatórios
Adicionar: `/spec-norm-diff`, `/ac-evidence <req_id>`, `/claim-check <file>`, `/tenant-fuzz`, `/emit-cert-dry <org_profile>`.

### P2-3 · Observabilidade do harness
Dashboard simples (pode ser Markdown gerado por CI) com: cobertura de requirements, PRs abertos por agente, taxa de violação de copy-lint, tempo entre draft e release de pacote normativo.

### P2-4 · Atualizar tabela de Tier 3 no §2.1
Remover "drain de backlog overnight" sem qualificação — substituir por "tarefas *low-risk* aprovadas pela política P1-2".

---

## Ordem recomendada de execução

1. **P0-1** (backend) — destrava todo o resto; sem owner formal, outros P0 não têm endereço.
2. **P0-4** (multitenancy/audit) — é a base técnica da imutabilidade que o restante usa.
3. **P0-2** (normative package) — depende de P0-1 para ter onde carregar.
4. **P0-3** (dossiê) — ancora o que foi feito em evidência.
5. **P0-6** (`product-governance`) — fecha o ciclo de release.
6. **P0-5** (copy-lint) — rápido, alto impacto, pode rodar em paralelo com os outros.
7. **P1-1 → P1-4** — conforme fatia vertical correspondente.
8. **P2-*** — em qualquer momento pós-estabilização.

---

## Não-objetivos deste patchplan

- Substituir o `HARNESS_DESIGN.md` — ele fica como histórico.
- Reabrir decisões já consolidadas (stack Next.js/Android/Postgres, tier model, spec-driven).
- Definir *tooling* específico de cada guardrail (fica para spec de implementação de cada P0).

---

## Fontes da análise crítica

- `PRD.md` §6.2, §6.6, §7.7, §7.10, §9, §11.3, §11.6, §13, §16.1–16.3.
- `ANALISE_CONSOLIDADA_PRD.md` C2 (claim de conformidade absoluta), C3 (reconciliação offline), C4 (LGPD/assinatura), C7 (audit log hardening).
- `HARNESS_DESIGN.md` §2.3, §2.4, §3, §4, §5, §6.
