# .agent/CURRENT.md

> ≤40 linhas. Atualizado a cada fechamento de Fase/Marco/US.

**Fase:** SANEAMENTO da fundação F-A ANTES do Marco 2. Loop: auditar F-A →
corrigir cada frente (causa-raiz, ritual: design → review subagente →
implement → verde → commit) → reauditar F-A rodada 2 → F-B → Marco 2.
**Modo:** AUTÔNOMO.

## Onde paramos (2026-05-18 — sessão em andamento)

### Fechado, verde e commitado/pushado (origin/main)
- **FA-A4** (rede contra migration mentirosa) — `1fcbfff`.
- **FA-C1** (hash chain por-tenant + cadeia sistema + Q-02 + lock por-tenant)
  — `3b08bbb`. 225 passed. Testes T1-T8 + trigger anti-mutation corrigidos
  pro invariante real (policy USING(false) + tabela append-only imutável).
- **FA-A2** (template RLS único + fail-loud em clientes) — `2eb986a`.
  `multitenant/rls_templates.py` (fonte única, require_tenant_ctx + anti-
  injeção DDL) + `clientes/0014`. Review tech-lead R1-R5 absorvido. 238 passed.
- **FA-A1+FA-M2** (PII_HASH_KEY versionada + hardening prod) — `7243684`.
  Registry redatado (anti-vazamento diffsettings), verificar_pii_hash,
  ChavePIIIndisponivel, prod gate presença+entropia, colunas ip_hash →
  TextField (clientes/0015 + audit/0010), matriz retenção chave aposentada.
  Review tech-lead T1-T5 + advogado R1-R3 absorvido. **259 passed,
  cobertura 84.85%, hooks 113/113.**

### Próximo passo (retomar)
Loop F-A continua na ordem do consolidado:
1. **FA-A5 + FA-M1** (in_progress) — drill robusto (≥3 tenants intercalados +
   injeção de elo faltante + concorrência; fuzzing 50×1000; benchmark
   multi-tenant) + sincronizar números/status (AGENTS.md, CLAUDE.md,
   validar_f_a.py, drill-f-a-saida.md) com valores verificados.
2. **FA-M3** (higiene: limpar_contexto sem token, god-function
   registrar_auditoria, dedup template via FA-A2).
3. Tarefas #6 (drift migration clienteimportacaodeclaracao) + #7 (lint
   sweep RUF012/E402/UP017 pré-existente) — encaixar em FA-M3.
4. **Reauditar F-A rodada 2** (10 lentes). Loop até zero CRÍTICO/ALTO.
   Só então F-B.

## Fila de tarefas
Ver TaskList (#3 FA-A5+M1 in_progress; #5 FA-M3; #2 reauditoria; #6 drift;
#7 lint sweep). Consolidado: docs/faseamento/auditorias/F-A-CONSOLIDADO-rodada-1.md
