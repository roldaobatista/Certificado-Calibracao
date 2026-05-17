# ADR-0003 — Mobile do técnico de campo

> **Status:** ⏳ **stub reservado** — ADR ainda não escrita.
> **Decisão prévia (ADR-0001 candidata, 17/05/2026):** Flutter offline-first como direção provisória.
> **Bloqueia:** especificação do módulo de Ordens de Serviço + Calibração em campo.
> **Quando escrever:** após sintese-final discovery sair de DRAFT v3 e PRD do MVP-1 definir se mobile entra na 1ª onda.

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
