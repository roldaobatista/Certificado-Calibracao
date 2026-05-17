---
owner: roldao
revisado_em: 2026-05-17
status: draft
diataxis: reference
audiencia: agente
---

# Contratos de UI — Módulo Billing SaaS

> Telas do módulo. Wireframe textual; stack final pós ADR-0001.

---

## Telas

### Tela 1: Catálogo de Planos (contratação inicial)

**Propósito:** novo tenant escolhe plano ao criar conta.
**Persona principal:** Administrador-Dono do tenant.
**US relacionadas:** `US-BIL-001`.
**Acessível por:** onboarding pós-cadastro / botão "Mudar Plano" no painel.

**Elementos:**
- Cards lado a lado dos planos A/B/C/D com preço mensal/anual, limites, módulos liberados.
- Toggle "mensal/anual" (anual mostra economia %).
- Botão "Escolher" por plano.
- Selo "MAIS POPULAR" no plano destacado.
- Link "Comparar todos os recursos" → modal com tabela completa.

**Estados:**
- Vazio: não aplicável (catálogo sempre tem ≥1 plano).
- Carregando: skeleton dos cards.
- Erro: "Não foi possível carregar os planos. Tente novamente."
- Sucesso (após escolher): redireciona pra Tela 2.

**Acessibilidade:** WCAG AA; navegação por teclado; tab order coerente; cada card com `aria-label` completo.
**Mobile:** responsivo (cards empilham).

---

### Tela 2: Confirmação de contratação + método de pagamento

**Propósito:** tenant confirma plano e cadastra método de pagamento (ou inicia trial).
**Persona principal:** Administrador-Dono.
**US:** `US-BIL-001`, `US-BIL-005`.

**Elementos:**
- Resumo: plano escolhido, valor, ciclo.
- Campo cupom (opcional) → botão "Aplicar".
- Bloco método de pagamento: cartão (iframe do gateway — Aferê não toca dado de cartão por `SEC-NNN`), boleto, PIX.
- Se plano tem trial: aviso "Você não será cobrado nos próximos N dias."
- Botão "Confirmar contratação".
- Checkbox aceite termos (link pra contrato/política).

**Estados:**
- Erro cupom inválido: "Cupom expirado ou já utilizado."
- Erro gateway: "Não foi possível validar o cartão. Verifique os dados."
- Sucesso: redireciona pro painel principal com banner "Bem-vindo! Assinatura ativa."

---

### Tela 3: Painel da minha assinatura

**Propósito:** tenant vê estado atual + ações (upgrade, cupom, cancelar).
**Persona principal:** Administrador-Dono.
**US:** `US-BIL-004`, `US-BIL-006`, `US-BIL-007`.

**Elementos:**
- Card "Plano atual": nome, valor, próximo vencimento, status.
- Card "Uso vs limites": barras de progresso (usuários X/Y, módulos ativos, volume).
  - Alerta amarelo se >80%; vermelho se >95%.
- Botão "Mudar de plano" → modal upgrade/downgrade.
- Bloco "Cupons ativos".
- Bloco "Próxima fatura" (preview).
- Link "Histórico de faturas".
- Link "Cancelar assinatura" (rodapé, discreto — pede confirmação dupla).

**Estados:**
- Trial: banner persistente "Trial expira em N dias. [Configurar pagamento]".
- Inadimplente warning: banner amarelo "Fatura vencida há X dias. [Regularizar]".
- Read-only: banner laranja "Acesso limitado por inadimplência."
- Suspensa: tela única de regularização (apenas pagar/atualizar método).

---

### Tela 4: Histórico de faturas

**Propósito:** consulta de faturas anteriores; download PDF.
**US:** `US-BIL-002`.

**Elementos:**
- Tabela: data emissão, número, valor, status (paga/aberta/falhou), ação (baixar PDF / pagar agora).
- Filtros: período, status.
- Paginação.

---

### Tela 5: Painel admin Aferê (interno — operador comercial)

**Propósito:** equipe Aferê gerencia planos, cupons, assinaturas anômalas.
**Persona principal:** Operador comercial do Aferê.

**Elementos:**
- Sub-abas: Planos, Cupons, Assinaturas, Métricas.
- "Planos": CRUD de planos (criar novo, versionar).
- "Cupons": criar/listar cupons, ver usos.
- "Assinaturas": busca por tenant, ver detalhes, ação "Forçar reativação" (com motivo obrigatório → trilha).
- "Métricas": MRR, churn, conversão trial (dashboard).

**Acessível por:** apenas papel "operador_comercial_afere" (RBAC).

---

## Componentes reutilizáveis

- Card de plano (compartilhado com landing).
- Iframe gateway (envolve Stripe Elements / PagSeguro tokenização).
- Barra de progresso com alertas — compartilhado com `../../comissoes/` e outros.

## Como esta lista evolui

- Tela nova → adicionar + ligar a US.
- Mudança UX em fluxo de pagamento → ADR (sensibilidade segurança).
