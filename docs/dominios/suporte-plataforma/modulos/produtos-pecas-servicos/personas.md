---
owner: Roldão
revisado-em: 2026-05-17
status: draft
modulo: produtos-pecas-servicos
dominio: suporte-plataforma
---

# Personas — Módulo Catálogo

> Específicas. Transversais em `../../personas.md`.

---

## Persona principal: Comprador (P-SUP-03)

Toca este módulo ao:
- Cadastrar peça nova quando fornecedor traz item novo.
- Atualizar preço quando fornecedor reajusta.
- Inativar peça obsoleta.

**Frequência:** semanal.
**Device:** web desktop.

---

## Persona secundária: Almoxarife (P-SUP-01)

Toca este módulo ao:
- Cadastrar peça quando recebe nota de entrada com item desconhecido.
- Conferir UM e categoria.

**Frequência:** diária (consulta), semanal (cadastro).

---

## Persona terciária: Atendente / Recepção (P-COM-01)

Toca este módulo ao:
- Cadastrar serviço novo (ex: "calibração de balança 50kg").
- Criar kit de pacote comercial.

**Frequência:** mensal.

---

## Persona quaternária: Técnico de campo (P-OP-01)

Toca este módulo somente para **consulta** (descrição da peça antes de pedir).

**Permissões:** read-only.

---

## Anti-personas

- Tenant tentando alterar preço retroativamente em OS já fechadas → bloqueado por INV-026.
- Tenant tentando deletar item com histórico → bloqueado (só inativa).

---

## Convenções

- Persona promovida pra `../../personas.md` se aparecer em ≥2 módulos do domínio com mesma responsabilidade.
