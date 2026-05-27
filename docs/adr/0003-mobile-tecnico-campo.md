# ADR-0003 — Mobile do técnico de campo

> **Status:** **ACEITO** (2026-05-27 noite — auditoria 10 lentes pré-Wave A, Onda PRE-A.2). Decisão cravada: **Flutter offline-first** (alinhado com ADR-0001 candidata) + sync por atividade (ADR-0027 — aceita 2026-05-23) + assinatura A3 cliente-side via Web PKI Lacuna (ADR-0009 + ADR-0048).
> **Aceito-em:** 2026-05-27.
> **Decisões cravadas:**
> - **Framework:** Flutter (decidido em ADR-0001 candidata — sobrevive 3 portões). Razão: 1 codebase iOS+Android, offline-first nativo, suporte FFI pra Web PKI Lacuna.
> - **Offline-first:** sync por atividade ADR-0027 (LWW por `atividade_id` + IDEMP-001 + backlog visível ao técnico). Modelo NÃO é CRDT puro — é evento por atividade com idempotência.
> - **Captura em campo:** fotos com EXIF segregado (ADR-0029 §"FotoComExifSegregado") + GPS com consentimento `Colaborador.consente_gps_em` persistido (não payload) + assinatura touch (DPIA `dpia-assinatura-touch.md`).
> - **A3 cliente-side:** via Lacuna Web PKI no PC + FFI Flutter no mobile pra leitor token físico USB-C (ADR-0009 + ADR-0048). Mobile NÃO assina A3 in-app (limite Lacuna SDK).
> - **Distribuição:** Play Store + TestFlight (sideload Android pra desenvolvimento). Suporte mínimo iOS 14 / Android 9 (cobertura ~95% técnicos de campo BR).
> - **Bloqueio Wave A:** módulo `operacao/app-tecnico` consome esta ADR + ADR-0004 (sync) + ADR-0067 (perfil tenant — perfil A obriga A3; perfil D dispensa).

---

## Por que existe este stub

A ADR-0001 cravou Flutter como mobile da stack candidata. Esta ADR-0003 vai detalhar:
- **PWA vs React Native vs Flutter vs Capacitor** — comparação técnica e de custo
- **Offline-first** — modelo de sincronização (CRDT? event-sourcing? last-write-wins?)
- **Captura em campo** — fotos, GPS, assinatura A3 via Flutter FFI + Web PKI Lacuna
- **Distribuição** — Play Store / TestFlight / sideload
- **Suporte iOS x Android** — prioridade no MVP-1

## Origem

Auditor 3 da 2ª auditoria (16/05/2026) marcou ADR-0003 como obrigatória. Aud-22 da auditoria 12 agentes confirmou.

## Decisões dependentes

- ADR-0009 (onde A3 assina) já cravou: A3 sempre cliente-side via Web PKI Lacuna em desktop + Flutter FFI no celular/tablet.
- ADR-0002 (multi-tenancy) define `tenant_id` no token; mobile deve respeitar.

---

**Não preencher antes da hora.** Veja `AGENTS.md` seção 11 (ADRs ativas) e `docs/documentos-do-projeto.md`.
