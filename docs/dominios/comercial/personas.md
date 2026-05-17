---
owner: Roldão
revisado-em: 2026-05-17
status: draft
---

# Personas do domínio Comercial

> Detalhe rico em `docs/discovery/personas-detalhadas.md` (16 personas). Aqui ficam só as **comerciais**.

---

## P-COM-01 — Atendente / recepcionista

**Quem é:** 20-35 anos, primeiro contato com cliente. Cadastra, agenda, abre OS, responde telefone/WhatsApp/e-mail.

**Goals no domínio Comercial:**
- Cadastrar cliente em < 1 min sem duplicar
- Encontrar histórico do cliente rápido (visão 360°)
- Não perder mensagem WhatsApp / e-mail
- Saber em < 5s se cliente tem inadimplência ou está bloqueado

**Frustrations:**
- Cadastro duplicado entre sistemas (Dor #01)
- "Cadê o cadastro do Sr. Silva?" 10x/dia
- Sistemas que exigem 8 cliques pra abrir OS

**Permissões:** Atendente — CRM completo + cadastro cliente + criar OS + ver agenda + ver inadimplência (read-only).

---

## P-COM-02 — Vendedor / consultor comercial

**Quem é:** 25-45 anos. Pode ser interno (B-to-B) ou externo (visita campo). Trabalha com pipeline + meta + comissão sobre o que recebido.

**Goals:**
- Saber pipeline + previsão de fechamento + comissão prevista
- Mandar proposta profissional em < 5 min (JTBD-041)
- Acompanhar leitura/aceitação do orçamento pelo cliente
- Não esquecer de fazer follow-up

**Frustrations:**
- "Pipeline em planilha que ninguém olha"
- Cliente lê WhatsApp e não responde
- Comissão calculada errado / atrasada

**Permissões:** Vendedor — CRM (próprio funil), orçamentos (criar/editar próprio), ver oportunidade própria, demonstrativo de comissão próprio.

---

## P-COM-03 — Cliente final do tenant

**Quem é:** decisor do laboratório cliente (dono ou metrologista responsável) que vai usar o Aferê via Portal do Cliente.

**Goals no domínio Comercial:**
- Aprovar/rejeitar orçamento em 1 clique
- Ver histórico de serviços contratados
- Pedir reagendamento sem ligar
- Baixar contrato / certificados sem pedir

**Frustrations (do mundo atual):**
- "Tenho que ligar pra saber se eu tenho que renovar"
- Boletos que chegam tarde + cobrança intrusiva
- Email com proposta que eu não consigo aprovar (PDF + assinatura na caneta)

**Permissões:** Cliente externo — portal restrito (só seus próprios dados via RLS).

---

## P-COM-04 — Diego (Consultor RBC) — canal de indicação

**Quem é:** Persona 15 do discovery. Consultor de acreditação que orienta labs no caminho D→A da CGCRE. **Canal #1 de aquisição de novos tenants Aferê (decisão Roldão).**

**Goals:**
- Recomendar Aferê pra clientes labs sem queimar reputação dele
- Saber se Aferê atende perfil do cliente que ele atende
- Ganhar incentivo claro pela indicação (sem ser comissão suja)

**Frustrations:**
- Recomendar software ruim derrete reputação
- Não saber em que pé está o cliente que indicou

**Permissões:** Parceiro de canal — dashboard básico + programa de indicação (V2 quando ativar).

---

## P-COM-05 — Dono / sócio (decisor de compra)

**Quem é:** Persona 1 transversal. Aparece no Comercial principalmente como **decisor de novo cliente** (B2B B2B) e como **leitor do MAPA-DO-DONO** (status comercial + NPS + pipeline + churn).

Goals/frustrations: ver `docs/comum/personas.md` §P1.

---

## Anti-personas (quem NÃO é foco)

- **Vendedor "hardcore" de SaaS:** Aferê não compete em mercado de software genérico — foco é nicho calibração/AT
- **Cliente que paga R$ 50/mês:** abaixo do perfil mínimo (perfil D R$ 300-500)
- **Tenant que paga + revende como white-label:** não permitido pelo modelo de negócio (anti-customização ANTI-11)

---

## Referências

- `docs/discovery/personas-detalhadas.md` (16 personas detalhadas)
- `docs/comum/personas.md` (5 transversais)
- `docs/discovery/jobs-to-be-done.md` (BIG-07, BIG-10, BIG-11)
