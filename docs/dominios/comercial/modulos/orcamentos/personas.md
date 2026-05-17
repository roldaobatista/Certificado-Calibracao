---
owner: Roldão
revisado-em: 2026-05-17
status: draft
modulo: orcamentos
dominio: comercial
diataxis: reference
---

# Personas — Módulo Orçamentos

## P-ORC-01 — Vendedor (criador, persona dominante)

Referência: P-COM-02 do domínio. **Persona dominante** do módulo.

**Goals específicos:**
- Mandar orçamento em < 5 min (JTBD-041).
- Ver impacto do desconto na própria comissão ANTES de fechar (JTBD-075).
- Saber se cliente abriu o link (Wave B — JTBD-094).
- Não copiar dados 3x (chamado → orçamento → OS) — JTBD-020.

**Frustrations:**
- "Word travou e perdi o orçamento."
- "Mandei e o cliente sumiu — não sei se leu."
- "Dei 20% de desconto sem ver que minha comissão virou pó."

**Jornada típica:**
1. Cliente liga ou WhatsApp → atendente abre cliente → vendedor recebe
2. Vendedor abre `/orcamentos/novo?cliente_id=X`
3. Escolhe template "Calibração padrão" → preenche itens
4. Vê comissão prevista no rodapé
5. Envia → cliente recebe WhatsApp com link
6. Cliente aprova → OS rascunho aparece pra atendente abrir

**Devices:** desktop (criação), mobile (consulta + follow-up).
**Frequência:** múltiplas vezes/dia.

---

## P-ORC-02 — Cliente final (aprovador)

Referência: P-COM-03.

**Goals:**
- Aprovar em 1 clique sem instalar nada nem assinar caneta.
- Ver claramente o que está comprando (escopo + prazo + valor).
- Pedir ajuste sem ligar (comentário simples no link).

**Frustrations:**
- "Recebi PDF que não consigo aprovar."
- "Cadê o resumo? Só vejo 4 páginas com cláusula jurídica."

**Devices:** mobile (75%) + desktop (25%).
**Frequência:** raro (1-N vezes por relacionamento).

---

## P-ORC-03 — Atendente (apoio + conversão)

Referência: P-COM-01.

**Goals:**
- Quando orçamento aprovado, abrir OS automaticamente (sem redigitar).
- Acessar histórico de orçamentos do cliente na visão 360°.

**Frequência:** indireta — via cliente.

---

## P-ORC-04 — Dono (configurador + aprovador interno)

Referência: P-COM-05.

**Goals:**
- Configurar templates de orçamento por tipo de serviço.
- Definir limite de desconto autônomo do vendedor.
- Aprovar internamente orçamento que excede limite (Wave B).
- Ver pipeline de orçamentos abertos + valor previsto no MAPA-DO-DONO (JTBD-001).

**Frequência:** semanal.

---

## Anti-personas

- **Cliente que quer negociação multi-rodada com chat:** MVP-1 só tem comentário simples.
- **Vendedor que prefere Word + e-mail manual:** módulo NÃO oferece exportar editável; quem quer Word usa outro produto.

## Convenções

P-ORC-02 (Cliente final) = mesma persona transversal P-COM-03. Promover detalhamento futuro pra `../../personas.md` se duplicar entre módulos.
