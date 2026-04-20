# 14 — Cascata de verificação (L0 → L5)

> **P0-10**: formaliza a malha de auditoria em cada nível de artefato — do épico até o release — com propagação bidirecional quando erro é descoberto.

## Racional

Um erro detectado no nível L3 (código) pode revelar que o erro real está em L1 (spec) ou até L0 (épico). Sem regra explícita de propagação, a correção fica local e o defeito volta.

## Os 6 níveis

### L0 — Épico
**O que é**: intenção ampla do PRD (ex.: "emissão Tipo A com CMC").
**Auditor**: `regulator` + `product-governance`.
**Gate obrigatório antes de quebrar em stories**:
- Normas aplicáveis listadas (com versão).
- Regras §9 do PRD potencialmente afetadas enumeradas.
- Risco LGPD avaliado por `lgpd-security`.
- Claim comercial impactado revisado por `copy-compliance`.
- ADR de épico criada em `adr/epics/<slug>.md`.
**Sem ADR de épico assinada → nenhuma story derivada pode entrar em backlog ativo.**

### L1 — Story / Spec
**O que é**: spec individual em `specs/NNNN-slug.md` com os 6 elementos.
**Auditor**: agente de domínio (ver matriz §03) + `qa-acceptance`.
**Gate automático (`spec-lint`)**:
- Todos os 6 elementos presentes e não vazios.
- Cada AC tem REQ-ID estável ligado em `requirements.yaml`.
- Cada AC é executável (tem verbo testável: "bloqueia", "emite", "gravar", "rejeitar").
- Escopo não conflita com spec já aprovada (busca semântica + override manual registrado em ADR).
- Épico-pai existe e está em L0 assinado.
**Gate humano**: agente de domínio co-assina antes do plan mode.

### L2 — Plano
**O que é**: plano gerado pelo orquestrador em *plan mode* antes de codar.
**Auditor**: humano + `plan-lint` automático.
**Gate `plan-lint`**:
- Paths tocados respeitam ownership de agente (§03).
- Budget estimado não excede cap por task (§11).
- Nenhuma dependência de spec em L1 `[Proposto]` não-assinado.
- Plano cita explicitamente os REQ-IDs que pretende cobrir.
- Reuso de código existente foi buscado (grep automatizado por utilitários relacionados).
**Gate humano**: aprovação obrigatória em plan mode; humano pode vetar mesmo com lint verde.

### L3 — Código
**O que é**: implementação efetiva.
**Auditor**: CODEOWNERS + gates CI (§05) + `qa-acceptance`.
**Gates**: todos os 6 de §05 + copy-lint §06 + simulator §08 quando aplicável.

### L4 — Integração
**O que é**: a mudança dentro do contexto completo do produto.
**Auditor**: `qa-acceptance` + `product-governance`.
**Gate obrigatório — full regression por área crítica**:

Áreas críticas (regra dura, não-negociável):
```
apps/api/src/domain/emission/**
apps/api/src/domain/audit/**
packages/engine-uncertainty/**
packages/normative-rules/**
packages/audit-log/**
```

Regra: **qualquer mudança** que toca essas áreas → CI roda **100% dos REQs da área**, não só os afetados pelo diff. Sem exceção.

Para áreas não-críticas: *impact analysis* determina subset + suite sentinela mínima (20% amostral rotativo).

**Snapshot-diff obrigatório**:
- Conjunto canônico de 30 certificados de referência (10 por perfil A/B/C).
- A cada merge em área crítica: gerar cada certificado e fazer diff byte-a-byte contra snapshot aprovado.
- Diff não-esperado = bloqueio + investigação forense. Mudança legítima exige novo snapshot aprovado por `regulator` + `product-governance`.

### L5 — Release
**O que é**: publicação da fatia vertical ou hotfix.
**Auditor principal**: `product-governance`.
**Auditores externos obrigatórios** (ver `16-agentes-auditores-externos.md`):
- `metrology-auditor` — parecer PASS em `compliance/audits/metrology/<release>.md`.
- `legal-counsel` — parecer PASS em `compliance/audits/legal/<release>.md`.
- `senior-reviewer` — parecer PASS em `compliance/audits/code/<release>.md`.
**Gate**: release-norm completo (§07) + pacote normativo vigente (§04) + todos os L0–L4 da fatia verdes + 3 pareceres de auditor PASS (ou explicitamente overridden via ADR + aprovação do usuário).
**Fail-closed em casos-limite**: se aplicável algum dos 5 casos-limite (§16), sistema pausa L5 e escala ao usuário com briefing pronto.

---

## Regra de propagação bidirecional

Correção não é local por padrão. Toda vez que uma correção é feita, o sistema pergunta: "este erro indica que o nível acima estava errado?"

### Propagação para cima (root-cause check)
Quando um L3 (código) revela defeito estrutural:
- Se o AC precisava mudar → reabrir L1 (spec).
- Se múltiplos L1 do mesmo épico tiveram o mesmo tipo de erro → reabrir L0 (épico).
- Se política foi incompleta → PR em `compliance/` atualizando + ADR.

**Gatilho automático**: se 3 correções consecutivas na mesma spec alteraram o AC ou seus REQs → `spec-review-flag` abre issue para re-auditoria do L1. Mesma regra no nível do épico.

### Propagação para baixo (re-audit)
Correção que altera artefato acima faz os abaixo **serem re-auditados**:
- L0 corrigido → toda story derivada é re-auditada em L1.
- L1 corrigido → plano e código ligados são re-auditados em L2 e L3.
- L2 corrigido → plano re-executado; implementação precedente é re-revisada.
- L3 corrigido → L4 roda *full regression* (não só o delta).

**Regra dura**: nenhuma correção em nível acima fecha sem re-auditoria dos níveis abaixo marcada como concluída.

### Registro
Cada propagação vira entrada em `compliance/verification-log/<REQ-id>.yaml`:

```yaml
- date: 2026-04-22
  trigger: L3 bug in emission flow
  propagated_up: [L1/REQ-§7.7-WIZARD, L0/EPIC-EMISSION-TIPO-A]
  propagated_down: [L1/REQ-§7.7-WIZARD, L3/apps/api/src/domain/emission/signature.ts]
  re_audits_completed:
    - L0/EPIC-EMISSION-TIPO-A: 2026-04-23 by regulator
    - L1/REQ-§7.7-WIZARD: 2026-04-23 by regulator + qa-acceptance
    - L3: 2026-04-24 via CI full regression
```

---

## Implementação bootstrap

- `tools/verification-cascade.ts` gera plano determinístico para arquivos alterados.
- `pnpm verification-cascade:plan -- --changed <arquivo>` identifica áreas críticas, full regression e snapshot-diff obrigatório.
- `pnpm exec tsx tools/verification-cascade.ts release-audits --release <versao>` valida os 3 pareceres L5 em `compliance/audits/metrology|legal|code/`.
- `compliance/verification-log/` é o diretório canônico para registros de propagação e re-auditoria.
- `pnpm verification-cascade:check` valida a presença do registro canônico e entra em `pnpm check:all`.

---

## Matriz resumida

| Nível | Auditor humano | Auditor automático | Bloqueia merge? |
|-------|----------------|---------------------|-----------------|
| L0 | regulator + product-governance | checklist CI | Sim (sem ADR → stories bloqueadas) |
| L1 | agente de domínio | `spec-lint` | Sim |
| L2 | humano em plan mode | `plan-lint` | Sim (no plan mode) |
| L3 | CODEOWNERS | gates §05 | Sim |
| L4 | product-governance | full regression + snapshot-diff | Sim |
| L5 | product-governance | release checklist §07 | Sim (sem release) |

## Não-objetivos

- Não adiciona camadas novas de processo humano — os auditores já existem na matriz §03.
- Não substitui ADR como mecanismo de decisão — apenas obriga ADR onde hoje é implícito (L0).
- Não implica retrabalho mecânico: re-auditoria em L0/L1 pode concluir em 15 min se a correção é menor.
