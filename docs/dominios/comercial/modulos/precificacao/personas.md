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

**Identidade:** dono ou gerente comercial/financeiro responsável por definir como a empresa precifica. Em empresa pequena, é o próprio dono (perfil P-COM-05); em média/grande, é função separada (controller, gerente comercial). Tem visão de margem e custo, conhece o mercado.

**Goals deste módulo:**
- Configurar regras de formação de preço (cost-plus, margem-alvo, fixo).
- Criar e versionar tabelas de preço (pública, por segmento, por contrato).
- Definir faixas de desconto autorizadas por papel.
- Acompanhar margem média realizada vs alvo.
- Identificar itens deficitários e renegociar com fornecedor ou subir preço.

**Frustrations específicas:**
- Vendedor dando desconto no olho e fechando com margem negativa.
- Não conseguir simular cenário "se subir 5% no preço, quanto perco em volume".
- Mudar tabela e o sistema "perder" o histórico do que era antes.

**Jornada típica:**
1. Abre dashboard de margem — vê que serviço X teve margem média 12% no mês (alvo era 25%).
2. Investiga histórico — vendedores deram desconto médio de 18%.
3. Aperta limite de desconto desse serviço de 20% para 10% (acima exige aprovação).
4. Publica nova versão da regra.

**Devices:** desktop.
**Frequência:** semanal.

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
