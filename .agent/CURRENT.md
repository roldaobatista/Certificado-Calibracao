# .agent/CURRENT.md

> ≤40 linhas. Histórico expandido em `docs/faseamento/diario/`.

**Fase:** Foundation F-A+F-B FECHADAS · Marco 1 `clientes` FECHADO · Marco 2 `equipamentos` FECHADO · **Auditoria projeto-inteiro 10 lentes Onda 8 (2026-05-23 noite) — 147 achados RESOLVIDOS em 10 ondas paralelas.**
**Modo:** AUTÔNOMO.

## Estado da suíte (verificado 2026-05-23)

- `tests/test_equipamentos*.py + tests/regressao/`: **365/365 passed** em 141s.
- Suite completa: **621 passed em 37min** (OOM resolvido — `mem_limit: 12g` app / 4g db).
- Hooks `_test-runner.sh`: **207/207** verdes (25 hooks ativos).
- `makemigrations --check`: limpo · `ruff check`: zero issues.
- Drill `validar_m2_equipamentos`: **PASS** (18/18 verificações multi-tenant).

## Marcos fechados

- **Marco 1 `clientes`** — P5 10 auditores ZERO C/A/M. `docs/faseamento/M1-clientes/auditoria-familia5.md`.
- **Marco 2 `equipamentos`** — 65 T-EQP, 2ª passada P5 ZERO C/A/M (CVE-2025-68616 WeasyPrint mitigado). `docs/faseamento/M2-equipamentos/auditoria-familia5.md`.

## Auditoria 10 lentes OS+Cal+Cert — 2 rodadas RESOLVIDAS 2026-05-23

- **R1:** 179 achados → 128 resolvidos (71%) em 6 ondas; 51 GATEs Wave A.
- **R2 (pós-retrofit R1):** 80 achados → **52 resolvidos (65%)** em Onda 7 (5 sub-ondas); 28 GATEs Wave A.
- **Total: 34 CRÍTICOS = 100% fechados** (28 R1 + 6 R2). Marco 3 OS destravado P1 **e P4**.
- 6 ADRs novas (0024..0029) + 22 INVs em REGRAS + RIPD geo OS + DPIA biometria touch + texto AceiteAtividade v1.0 + 4-party DPA + ADR-0021 Zona D.
- Consolidados: `docs/faseamento/auditorias/OS-CAL-RESOLUCAO-rodada-{1,2}.md`.

## Onda de saneamento 2026-05-23 noite (Onda 8 — 10 resolvedores paralelos)

**147 achados** (25 C + 52 A + 50 M + 20 B) detectados por 10 auditores em paralelo (cada um cobrindo uma fatia: F-A, F-B, M1, M2, M3 pré-spec, M4 pré-PRD, Wave A regulatório, Wave A operacional, Wave B, costura transversal) → **TODOS endereçados em 10 ondas resolvedoras paralelas**.

**ADRs novas (23):** 0033-0055 — bus idempotência consumer, saga compensação, tenant suspenso readonly, replay determinismo, glossário PT-EN, família INV-AUTH, cliente exterior/MEI, padrão metrológico, OS concorrência atividades, OS cancelamento parcial, calibração faturamento+inadimplência, exportação ANVISA, cert recall/suspensão/errata, OCSP/CRL, TSA-ITI, A3 e-CPF RT, CT-e/NFC-e devolução, gateway PIX recorrente, propagação ADR-0023 modulos, PIX BCB-1071, SPED contábil, webhook out, marketplace sandbox.

**Módulos novos (PRDs esqueleto):** `metrologia/padroes`, `metrologia/procedimentos`, `seguranca/certificados-digitais`, `suporte-plataforma/webhook-out`, `suporte-plataforma/integracoes-externas`, `financeiro/contabilidade-export`, `comercial/marketplace`, `dados/bi` (atualizado).

**INVs novos (~70):** INV-BUS-001..003 + AUDIT/SCHEMA/REPLAY/TS, INV-SAGA-001..004, INV-LGPD-NOTIF-001..002, INV-DOM-GLOSS-001..002, INV-LGPD-KMS-001..003, INV-FA-001..003, INV-AUTH-001..005, INV-CLI-CONTATO/ENDERECO/SUCESSAO/REATIV, INV-EQP-MOV-001..002, INV-PAD-001..006, INV-OS-FAT/CONC/CAL-LINK/ANON/EQP/SUC/SYNC, INV-CAL-NC-PT/FIN, INV-CER-ANON/EXP/RECALL/SUSP/ERRATA/NUM-002, INV-PROC-001..003, INV-FIS-CR/REGIME/OCSP-CHAIN, INV-A3-RT/OCSP, INV-CER-LTV, INV-REG-AMPLIACAO/NC-CGCRE/REVISAO-5A, INV-ORC-EXP, INV-CHM-RAST, INV-AG-ADR0023, INV-APP-ADR0023/CANON/SESS/SYNC, INV-FIN-REATIV/INAD/GW, INV-BIL-PIX, INV-BPM-MIG, INV-BI-MRR, INV-MKT-SANDBOX, INV-WEBHOOK-001, INV-SPED-001.

**Migration nova:** `0007_seed_perfis_marco_3_4.py` (5 perfis: financeiro, metrologista_bancada, atendente, gerente_operacional, signatario).

**Código novo:** `TenantLifecycleEstado` enum (7 estados + transições) em VOs; fix `except Exception` engolido em event_helpers.py.

**Validação pós-Onda 8:** hooks `_test-runner.sh` **207/207 verdes**; 12 testes novos `TestTenantLifecycleEstado` passam.

## Onda de saneamento 2026-05-23 (10 ondas — auditoria projeto-inteiro rodada 1)

149 achados (42 C + 55 A + 52 M) → todos endereçados. Veja `docs/faseamento/auditorias/PROJETO-INTEIRO-CONSOLIDADO-rodada-1.md`.

**Entregue:**
- Onda 1: drift docs + CODEOWNERS retrofit (paths reais src/infrastructure/*)
- Onda 2: ADR-0030 vigência + ADR-0031 soft-delete + ADR-0032 FK anonimização + VOs (JanelaVigencia, ReferenciaPIIAnonimizavel, Telefone, UF, PaisISO3166, Dinheiro, Grandeza, FaixaMedicao, IncertezaExpandida, NumeroCertificado) + INV-VIG/SOFT/ANON/AUDIT/CER-NUM em REGRAS + testes
- Onda 3: bus envelope canônico v10 retrofit (event_helpers.py injeta event_id, _schema_version, occurred_at, correlation_id, actor) + bus-envelope-validator estendido (concern envelope v10 + bloqueio Cliente.Anonimizado)
- Onda 4: 7 hooks novos (vigencia-canonica, soft-delete-padrao, fk-pii-anonimizavel, biometria-key, os-conclusao-todas-terminais, frontmatter-revisado-em, spec-ac-binario) registrados em settings.json
- Onda 5: spec FORWARD M3 OS criado + fiscal/prd.md promovido stable com 7 US/AC binários BDD
- Onda 6: ADRs 0021, 0024, 0025, 0026, 0027 aceitas (frontmatter) — destrava Marco 4 calibração + Marco 3 OS
- Onda 7: 9 minutas LGPD (ToU, PoP, DPA cap, finalidades-lgpd estendido 12 entradas, subprocessadores, DPIA-OS/CAL/CERT, runbook-DPO) — TODAS REQUEREM VALIDAÇÃO OAB HUMANA
- Onda 8: ADR-0028 expandida 5→7 modalidades + planilha cotação + briefing + gates-seg + RC-RT-vendor-v2 — TODOS REQUEREM CORRETORA SUSEP HUMANA
- Onda 9: gates-wave-a-consolidado.md (85 GATEs categorizados, 75 abertos / 7 fechados / 3 em andamento)
- Onda 10: modelo-de-dominio-transversal.md (catálogo único — VOs, vigência, soft-delete, FK PII, timezone UTC + tz_lab, moeda BRL V1, idioma pt V1, UUIDv4 V1, cliente_canonico_id)

**Próximo passo (após Onda 8):**
1. **Marco 3 OS P1 spec FORWARD pode arrancar agora** — desbloqueado por ADRs 0041 (concorrência) + 0042 (cancelamento parcial) + sagas.md + 5 US novas (US-OS-011..015) + 7 INV-OS novos. Stub em `docs/faseamento/M3-os/spec.md`.
2. **Marco 4 calibração** — desbloqueado por ADRs 0043/0044/0045 + módulo `procedimentos` + módulo `padroes`. Pode arrancar após Marco 3 P4 começar.
3. **Roldão valida com OAB humano:** ToU, PoP, DPA — antes de 1º tenant externo pago.
4. **Roldão aciona corretora SUSEP humana:** GATE-SEG-BPT-1 EMERGENCIAL.
5. **Roldão designa DPO formal:** runbook-dpo-encarregado.md.

## Pendências rastreadas (não bloqueiam Marco 3)

- 51 GATEs Wave A em `OS-CAL-RESOLUCAO-rodada-1.md` (segurança apólices, ISO 17025 validação, observabilidade, drift cosmético).
- ADR-0018 (PWA QR scanner) + ADR-0019 Pilar 2 (apólice) pendentes (Marco 2 GATEs).
