---
owner: roldao
revisado_em: 2026-05-18
proximo_review: 2026-08-18
status: stable
diataxis: explanation
audiencia: agente
relacionados:
  - docs/governanca/ritual-orquestrador.md
  - .specify/memory/constitution.md
  - docs/faseamento-foundation-waves.md
---

# Débitos de ritual (Spec Kit) — entregas que não seguiram o ciclo

> **Pra quê:** registrar entregas feitas **antes** de Roldão exigir orquestração de verdade (2026-05-18). Cada item lista a entrega + o gap do ritual + a ação de regularização.
>
> O Auditor de Drift de Docs lê este arquivo pra não disparar alerta D1–D8 sobre o gap retroativo.

---

## Resumo

| Fase / Marco | Entregue em | Ritual seguido? | Regularização |
|---|---|---|---|
| **Foundation F-A** (8 marcos) | 2026-05-18 manhã | ❌ Não | Mapeado retroativo em `docs/faseamento/stories-f-a.md` (`US-FA-001..008`) |
| **Foundation F-B** (app authz) | 2026-05-18 tarde | ❌ Não | Mapeado retroativo em `docs/faseamento/stories-f-b.md` (`US-FB-001..007`) |
| **Wave A Marco 1 — clientes** | 2026-05-18 noite | ❌ Parcialmente | PRD já existia (US-CLI-001..005); só US-CLI-001 implementada **parcial** (sem aceite LGPD, sem evento `Cliente.Criado`, sem 409 com link de duplicada). US-002/003/004/005 NÃO implementadas. Regularização: completar todas as US do PRD seguindo ritual completo. |

---

## Foundation F-A — gap

**Entregue:** 8 marcos técnicos (gate, esqueleto Django, 4 tabelas-núcleo, multi-tenancy + RLS, audit trail + hash chain, 2 hooks novos, suite + fuzzing, convenções django, drill).

**Gap:**
- Sem PRD-equivalente formal por marco
- Sem Stories `US-FA-NNN` antes de codar
- Sem ACs binários explícitos por marco (havia critérios de saída na fase, mas não por marco)
- Sem revisão prévia por subagentes
- Sem auditores rodando pre-commit/pre-merge
- Commits citam "Marco N" mas não T-FA-NNN

**Compensação parcial:** drill `validar_f_a` executado verde (5/5 critérios automáveis + restore PG); ADRs 0001, 0002, 0007 formalizadas; testes 58 passing; hooks 103/103.

**Regularização:** `docs/faseamento/stories-f-a.md` mapeia retroativamente os 8 marcos em `US-FA-001..008` com ACs binários derivados dos critérios de saída. Auditores rodados retroativamente — output em `docs/governanca/trilha-auditoria-agentes.md`.

---

## Foundation F-B — gap

**Entregue:** App `authz` (porta + adapter Django + 3 tabelas + 4 perfis seed + MFA + DRF deny-by-default + 30 testes + drill).

**Gap:** mesmos itens de F-A.

**Compensação parcial:** drill `validar_f_b` executado verde (7/7 critérios automáveis); ADRs 0006 e 0012 promovidas a aceita; INVs AUTHZ-001/002/003 cravadas e testadas.

**Regularização:** `docs/faseamento/stories-f-b.md` mapeia em `US-FB-001..007` com ACs binários derivados. Auditores rodados retroativamente.

---

## Wave A Marco 1 — clientes (gap mais grave)

**O que existia no PRD desde 2026-05-17:**

| US | Resumo | Status implementação |
|---|---|---|
| US-CLI-001 | Cadastrar cliente PF em <1min | **PARCIAL** — falta aceite LGPD (RAT-03), evento `Cliente.Criado`, response 409 com link |
| US-CLI-002 | Ver visão 360° do cliente | **NÃO implementado** |
| US-CLI-003 | Importar planilha (1-clique) | **NÃO implementado** |
| US-CLI-004 | Bloqueio cliente inadimplente (manual + automático ADR-0015 fluxo 4) | **NÃO implementado** |
| US-CLI-005 | Dedup manual wizard | **NÃO implementado** (dedup automático via UNIQUE constraint sim) |

**O que implementei (sem mapeamento Spec Kit):**
- VOs CNPJ alfanumérico + CPF (não vinculado a US explícita)
- Modelo `Cliente` PF/PJ com dedup automático (cobre AC-CLI-001-1 parcial + AC-CLI-005-1 parcial)
- API CRUD `/api/v1/clientes/` (cobre AC-CLI-001-2 parcial)
- 4 perfis × 4 ações na matriz authz

**Gap mais grave:** **abri o PRD só DEPOIS de codar tudo.** O PRD com 5 Stories estava no repositório há mais de 24 horas e nunca consultei.

**Regularização:**
1. Completar US-CLI-001 com aceite LGPD + evento + response 409 estruturada
2. Implementar US-CLI-002, 003, 004, 005 conforme PRD
3. Auditores rodam após cada US
4. Commits citam T-CLI-NNN

---

## Lições aprendidas

1. **Leia o PRD do módulo ANTES de qualquer linha de código.** Constituição §1 (Documento = estado compartilhado): se existe doc no disco, é a verdade.
2. **MVP do meu MVP é violação ANTI-1.** Implementar 30% da Story sem documentar o restante não é "incremental" — é descarrilhar.
3. **Ritual orquestrador é mandatório, não decorativo.** Memória `feedback_ritual_orquestrador.md` salva isso.

---

## Histórico

| Data | Mudança |
|------|---------|
| 2026-05-18 | Criação após Roldão exigir orquestração de verdade. |
