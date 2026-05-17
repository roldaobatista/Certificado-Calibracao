---
owner: Roldão
revisado-em: 2026-05-17
status: draft
modulo: chamados
dominio: operacao
---

# Personas do módulo Chamados

> Detalhe transversal em `../personas.md`. Aqui o papel específico em Chamados.

---

## P-OP-03 (Atendente) — papel em Chamados — PRIMÁRIA

**Quem é:** 22-45 anos, recepção/atendimento. Triagem é o dia inteiro dela. Tem múltiplos canais abertos ao mesmo tempo (WhatsApp Web, telefone, sistema).

**Goals em Chamados:**
- Triagem em ≤ 30s (JTBD-008)
- Não copiar info do WhatsApp 3 vezes (JTBD-020) — colar e a triagem extrai
- Saber se já existe chamado igual (alerta duplicado) antes de criar
- Atender 30+ chamados/dia sem perder contexto

**Frustrations:**
- "Cliente liga, eu já abri 5 abas, perdi o contexto" (Dor #20)
- Reclamação porque eu agendei errado por causa de duplicado
- WhatsApp do cliente vem com nome diferente do CRM

**Jornada típica:**
1. Chamado entra (WhatsApp ou tel) → cola texto / fala com cliente
2. Sistema sugere cliente (busca por número/nome) → 1 tap aceita
3. Sistema sugere equipamento (último do cliente) → 1 tap aceita
4. Sistema mostra "duplicado?" se houve chamado parecido em 7 dias
5. Triagem: tipo + urgência (default = média) + texto livre
6. "Salvar" → SLA calculado automático → ou converte em OS ou fecha com orientação

**Devices:** web desktop (telefone/WhatsApp ao lado).
**Frequência:** todo o dia.

---

## P-OP-04 (Gerente operacional) — papel em Chamados

**Goals:**
- Mapa de SLA: ver chamados estourando antes de estourar
- Reatribuir chamado quando atendente saiu/falta
- Aprovar fechamento sem OS quando o atendente tem dúvida

**Devices:** web desktop + mobile (consulta SLA crítico).

---

## P-OP-05 (Cliente final) — papel em Chamados

**Goals:**
- Abrir chamado pelo WhatsApp em 1 clique (link curto)
- Ver status do chamado sem login complexo
- Receber resposta humana (não bot) em horário comercial

**Devices:** mobile (WhatsApp) + web (portal).

---

## Convenções

Papel que aparece em ≥2 módulos com mesma responsabilidade → promover pra `../personas.md`.
