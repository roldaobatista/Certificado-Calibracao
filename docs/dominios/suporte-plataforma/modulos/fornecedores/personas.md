---
owner: Roldão
revisado-em: 2026-05-17
status: draft
modulo: fornecedores
dominio: suporte-plataforma
---

# Personas — Módulo Fornecedores

> Específicas. Transversais em `../../personas.md`.

---

## Persona principal: Comprador / responsável de compras (P-SUP-03)

Toca este módulo:
- Cadastra e homologa fornecedor
- Cria cotação em paralelo
- Compara respostas + escolhe com justificativa
- Gera pedido de compra
- Avalia entrega após recebimento

**Frequência:** semanal (cotação), mensal (homologação), diária (consulta histórico).
**Device:** web desktop.

---

## Persona secundária: Almoxarife (P-SUP-01)

Toca este módulo:
- Registra recebimento físico (que dispara avaliação)
- Consulta dados do fornecedor pra contato em caso de problema

**Frequência:** diária (consulta), eventual (avaliação).

---

## Persona terciária: Dono / Gestor (P-COM-* ou equivalente)

Toca este módulo:
- Aprovação de pedido acima de teto financeiro
- Consulta dashboard de fornecedores (score, gasto total)

**Frequência:** semanal.

---

## Persona quaternária: Fornecedor externo (P-SUP-06 — V2 portal)

Toca este módulo via link de cotação:
- Recebe link único (e-mail / WhatsApp)
- Preenche resposta de cotação
- Sem login completo no Aferê (Wave C inicial)
- V3 talvez portal completo de fornecedor

**Frequência:** sob demanda.
**Device:** web (mobile-friendly).

---

## Anti-personas

- Tenant tentando criar pedido de compra sem cotação prévia em itens acima de teto → bloqueado (regra configurável).
- Fornecedor tentando alterar resposta após prazo → bloqueado (token expirado).
- Tenant tentando excluir fornecedor com pedido ativo → bloqueado (só inativa).

---

## Convenções

- Persona promovida pra `../../personas.md` se aparecer em ≥2 módulos com mesma responsabilidade.
