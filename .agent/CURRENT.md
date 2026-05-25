# .agent/CURRENT.md

> ≤40 linhas. Histórico expandido em `docs/faseamento/diario/`.

**Fase:** F-A+F-B + M1 + M2 + F-C1 + **M3 OS FECHADAS** (2026-05-25).
**Modo:** AUTÔNOMO.

## Estado da suíte (2026-05-25 pós M3 OS FECHADO)

- pytest geral: **905/0/0** em 26min.
- Suite M3 chave: **137/137 PASS** em ~7min (26 arquivos).
- Hooks `_test-runner.sh`: **312/312** verdes / **42 hooks ativos**.
- ruff/mypy: limpos nos paths novos.

## M3 OS — P5 ritual concluído (3 passadas)

| Passada | Resultado | Conserto |
|---|---|---|
| 1ª (2026-05-24) | 5 PASS / 5 FAIL — 40 achados C/A/M | 5 batches: drift / idempotência / qualidade / produto / segurança |
| 2ª (2026-05-25) | 3 PASS (seg/qual/idemp) + 2 FAIL (prod + drift) | ADR-0063 + predicate invocação real + sweep 309→312 |
| 3ª (2026-05-25) | Produto CONCERN→PASS + drift-docs FAIL→PASS | PRD 4 ACs disclaimer + AGENTS L126 + diário L52 |

**VEREDITO FINAL: 10/10 PASS ZERO C/A/M** (segurança, qualidade, produto, drift-docs, llm-correctness, performance, observabilidade, idempotência, supplychain, conformidade-lgpd).

## M3 OS — entregue

18 use cases + 4 query services + **18 endpoints REST** (11 batch 8 + 7 batch 4) + 4 jobs procrastinate + 7 consumers + 3 sagas + 22 regressões INV-OS (~70 testes) + 3 hooks novos + helper único `sanitizar_payload_evento_os`. ADR-0063 (RT competência fail-open M3 / bloqueio Marco 4). Detalhes: `docs/faseamento/M3-os/auditoria-familia5.md` §"Veredito FINAL" + `docs/faseamento/diario/2026-05-24-marco3-os-fases-1-10.md`.

## Próxima fatia (decisão Roldão)

Wave A pendente autorização: ADRs em proposta a aceitar (0003/0004/0008/0009/0010/0014/0015/0016/0018/0019/0021/0034/0035) + 70+ GATEs Wave A rastreados em AGENTS §status (GATE-OS-GRANDEZA-EM-ATIVIDADE prioritário pra ativar bloqueio efetivo predicate RT competência em Marco 4 calibracao).

## Pendências Wave A rastreadas

GATE-OS-PERF-1..5 + GATE-OS-BUS-BRIDGE-1 + GATE-OBS-LOG-EXTRA-1 + GATE-OBS-METRIC-OS-1 + GATE-IDEMP-HOOK-DETECT-ACTION (✅ fechado pelo batch 2) + GATE-OS-SYNC-WAVE-A + GATE-OS-SUCESSAO-EVIDENCIA + GATE-OS-ANON-RETRY-1 + GATE-OS-VALIDAR-DRILL + GATE-OS-CONSBIO-TEXTO-OAB + GATE-OS-DPIA-OAB + GATE-OS-GRANDEZA-EM-ATIVIDADE + GATE-OS-SANITIZER-HELPER-MIGRACAO + GATE-OS-REPO-GETTER-TENANT-ID + GATE-OS-DEFESA-PROFUNDIDADE-CONSUMERS + GATE-OS-BIOMETRIA-TRAJETORIA + GATE-OS-MATRIZ-P3-SWEEP + GATE-OS-COV + GATE-OS-TST-ATIV-004 + GATE-OS-TST-LITERAL-FIXO + GATE-OS-REST-SERIALIZER-POLISH.
