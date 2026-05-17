---
owner: roldao
revisado_em: 2026-05-17
proximo_review: 2026-08-17
status: draft
diataxis: reference
audiencia: agente
---

# Personas do módulo Precificação

> Personas específicas. Transversais em `../../personas.md` e `docs/comum/personas.md`.

---

## P-PRC-01: Gestor de pricing

**Fonte canônica:** `docs/comum/personas.md` P-COM-06 (promovida em 2026-05-17 — aparece em `comercial/precificacao`, `comercial/orcamentos`, `comercial/contratos`, `financeiro/comissoes`). Aqui apenas referência. O alias local `P-PRC-01` continua válido em PRD/UI/API deste módulo.

---

## P-PRC-02: Vendedor que aplica preço

**Identidade:** vendedor comercial ou pré-vendas que monta orçamentos. Não decide política de pricing — aplica o que o gestor configurou. Quer fechar negócio, então pede desconto sempre que pode.

**Goals deste módulo:**
- Ver preço sugerido e mínimo do item.
- Aplicar desconto dentro do limite autorizado.
- Ver impacto do desconto na própria comissão.
- Pedir aprovação rápida quando desconto excede limite.

**Frustrations específicas:**
- Sistema bloqueia desconto sem explicar limite.
- Aprovação demora dias e o cliente desiste.
- Não saber a margem do item (só vê preço).

**Jornada típica:**
1. Monta orçamento; cliente pede 15% de desconto.
2. Digita 15% no campo desconto; vê alerta "acima do limite 10% — exige aprovação".
3. Clica "solicitar aprovação"; gerente recebe notificação.
4. Em 30 min gerente aprova; orçamento libera para envio.

**Devices:** desktop + mobile (vendedor externo).
**Frequência:** diário.

---

## P-PRC-03: Aprovador de desconto

**Identidade:** gerente comercial, dono, ou sócio que tem alçada para aprovar desconto acima do limite do vendedor. Pode ser a mesma pessoa que o gestor de pricing (P-PRC-01) em empresa pequena.

**Goals deste módulo:**
- Receber notificação de pedido de desconto com contexto suficiente (cliente, valor, margem resultante).
- Aprovar ou negar em 1 clique.
- Ver histórico de quanto desconto cada vendedor pediu/recebeu.

**Frustrations específicas:**
- Notificação sem contexto ("aprovar 15%" — 15% de quê? em qual cliente?).
- Não conseguir ver margem RESULTANTE do desconto solicitado.
- Vendedor pedir aprovação no WhatsApp fora do sistema.

**Jornada típica:**
1. Recebe push/e-mail: "vendedor João pede 15% no orçamento #1234 — cliente VIP, margem resultante 14%".
2. Confere contexto na tela.
3. Aprova com observação "aprovado pelo histórico do cliente".

**Devices:** mobile (decide em movimento) + desktop.
**Frequência:** diário.

---

## Convenções

- Persona específica = papel com responsabilidade ÚNICA neste módulo.
- Se persona aparece em ≥2 módulos com mesma responsabilidade, promover para `../../personas.md`.
- Se aparece em ≥2 domínios, promover para `docs/comum/personas.md`.
