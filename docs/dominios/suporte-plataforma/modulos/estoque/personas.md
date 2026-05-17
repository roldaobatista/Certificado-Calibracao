---
owner: Roldão
revisado-em: 2026-05-17
status: draft
modulo: estoque
dominio: suporte-plataforma
---

# Personas — Módulo Estoque

> Específicas. Transversais em `../../personas.md`.

---

## Persona principal: Almoxarife (P-SUP-01)

Toca este módulo diariamente:
- Lança entrada de peça (com lote/validade/NS)
- Emite transferência pra veículo do técnico
- Roda inventário periódico
- Reage a alerta de mínimo

**Frequência:** diária / várias vezes ao dia.
**Device:** web desktop + tablet (inventário).

---

## Persona secundária: Técnico de campo (P-OP-01)

Toca este módulo ao:
- Aceitar transferência (etapa 2) + anexar foto do lacre (BIG-12 JTBD-104)
- Consumir peça ao concluir OS
- Recusar transferência (peça diferente da pedida)

**Frequência:** diária.
**Device:** mobile (app/PWA).

---

## Persona terciária: Metrologista de bancada (P-SUP-02)

Toca este módulo ao:
- Selecionar padrão (que é item de estoque com NS) pra calibração
- Receber alerta se padrão escolhido está vencido

**Frequência:** diária.
**Device:** web desktop.

---

## Persona quaternária: Auditor CGCRE (P-SUP-05, V2)

Toca este módulo (read-only) ao:
- Conferir rastreabilidade de padrão (kardex)
- Conferir transferências 2-etapas com fotos

**Frequência:** anual.
**Device:** web desktop.

---

## Anti-personas

- Tenant tentando saída sem OS associada → bloqueado por regra de negócio (JTBD-099).
- Tenant tentando "importar Excel direto" sem aceite 2-etapas → ANTI-12.
- Tenant tentando consumir lote vencido → bloqueado.

---

## Convenções

- Persona promovida pra `../../personas.md` se aparecer em ≥2 módulos com mesma responsabilidade.
