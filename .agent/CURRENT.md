# .agent/CURRENT.md

> ≤40 linhas. Histórico expandido em `docs/faseamento/diario/`.

**Fase:** Foundation F-A+F-B FECHADAS · Marco 1 `clientes` FECHADO · Marco 2 `equipamentos` FECHADO · **Marco 3 `os`: P1+P2+P3 fechadas (2026-05-23) + P4 iniciada (T-OS-001+T-OS-002 entregues).**
**Modo:** AUTÔNOMO.

## Estado da suíte (verificado 2026-05-23 pós T-OS-001/002)

- Suite completa: **904 passed em 13min27s** (sem coverage). Zero regressão.
- Hooks `_test-runner.sh`: **207/207** verdes.
- ruff: All checks passed em `src/infrastructure/ordens_servico/`.
- makemigrations --check: limpo.
- migrate ordens_servico: 0001 + 0002 OK aplicadas.

## Marcos fechados

- **M1 `clientes`** — P5 10 auditores ZERO C/A/M. `docs/faseamento/M1-clientes/auditoria-familia5.md`.
- **M2 `equipamentos`** — 65 T-EQP, P5 2ª passada ZERO C/A/M (CVE-2025-68616 WeasyPrint mitigado). `docs/faseamento/M2-equipamentos/auditoria-familia5.md`.

## Marco 3 OS — P1+P2+P3 + P4 inicial entregues (2026-05-23)

- **P1 spec FORWARD stable** — 15 US, 10 entidades, 17 INVs, 14 eventos, 10 sagas, drill 24 verificações. `docs/faseamento/M3-os/spec.md`.
- **P2 4 reviews paralelos** — tech-lead (6) + advogado (7) + corretora (6) + RBC (8) = **27 achados** (6 BLOQ + 12 MÉD + 9 GATE/ACEITE). `docs/faseamento/M3-os/reviews/{tech-lead,advogado,corretora,rbc}.md` + `plan.md` ata.
- **P3 retrofit** absorvendo 6 BLOQ + 12 MÉD: ADR-0056 NOVA (numeração buracos aceitos), spec retrofit, REGRAS 5 INVs novos + 3 estendidos, PRD 10 ACs novos, ADR-0012 5 predicates novos, ADR-0028 rev 2 com 6 cláusulas seguráveis novas, matriz reconciliação zero conflito, 9 GATEs Wave A. `docs/faseamento/M3-os/matriz-reconciliacao.md`.
- **3 decisões Roldão tomadas:** D-M3-1 = (A) buracos aceitos, D-M3-2 = (A) 72h/15d watchdog, D-M3-3 = (A) BPT bloqueia produção.
- **P4 implementação iniciada:** tasks.md com 147 T-OS-NNN em 12 fases. T-OS-001 (app + models + sequence global + DEFAULT nextval; validado nextval=1) + T-OS-002 (8 RLS policies pattern v2; validadas em pg_policies). Fix lateral: drift QR_IP_RATELIMIT_SALT pré-existente em `test_fa_a1_pii_key_versionada.py` (commit d6ba200 não atualizou teste).

## Pendências rastreadas (não bloqueiam Marco 3 dogfooding)

- **T-OS-003..147** restantes em `docs/faseamento/M3-os/tasks.md` (12 fases).
- **51 GATEs Wave A** em `gates-wave-a-consolidado.md` + 9 GATEs novos do M3 (BPT, CONSBIO-OAB, ESCOPO-RBC, CAPA, FOTO-BLUR, SUCESSAO-EVIDENCIA, TENANT-SUSPENSO, INMETRO-PRAZO, CYBER-EO ampliados).
- **ADR-0018 PWA QR** + ADR-0019 Pilar 2 apólice (Marco 2 GATEs).

## Próximo passo

T-OS-003 ordem invertida — TipoAtividadeConfig + outras 8 entidades antes do unique partial index (que depende delas). Sequência: T-OS-010 (TipoAtividadeConfig com matriz tipo×concorrência), T-OS-003 reposicionado (unique partial index), depois Aceite/Consentimento/EvidenciaFoto/Dispensa/Evento/Checklist/SLA/NaoConformidade.
