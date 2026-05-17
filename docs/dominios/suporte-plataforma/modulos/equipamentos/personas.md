---
owner: Roldão
revisado-em: 2026-05-17
status: draft
modulo: equipamentos
dominio: suporte-plataforma
---

# Personas — Módulo Equipamentos do cliente

> Específicas deste módulo. Transversais em `../../personas.md` e `docs/comum/personas.md`.

---

## Persona principal: Metrologista de bancada (P-OP-02)

Detalhes em `docs/dominios/operacao/personas.md`. Toca este módulo ao:
- Cadastrar equipamento novo recém-chegado pra calibrar
- Editar atributo descritivo (gera nova versão se já há certificado — INV-025)
- Conferir ficha 360° antes de iniciar calibração

**Frequência:** diária.
**Device:** web desktop principal; mobile para leitura QR.

---

## Persona secundária: Técnico de campo (P-OP-01)

Toca este módulo ao:
- Escanear QR no cliente para abrir ficha 360°
- Confirmar TAG e NS antes de iniciar trabalho em campo
- Registrar foto do equipamento ao receber/devolver

**Frequência:** diária.
**Device:** mobile (app/PWA — a definir ADR-0003).

---

## Persona terciária: Atendente/recepção (P-COM-01)

[INFERÊNCIA] Toca este módulo ao receber equipamento na recepção: confirma TAG, vincula a cliente, imprime etiqueta com QR.

**Frequência:** diária.
**Device:** web desktop.

---

## Anti-personas

- Cliente final querendo editar dados do próprio equipamento → não tem acesso (Wave futura).
- Tenant tentando alterar TAG/NS pós-certificado → bloqueado por INV-025.

---

## Convenções

- Persona promovida pra `../../personas.md` se aparecer em ≥2 módulos do domínio com mesma responsabilidade.
