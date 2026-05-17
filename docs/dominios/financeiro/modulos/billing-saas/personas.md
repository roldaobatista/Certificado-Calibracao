---
owner: roldao
revisado_em: 2026-05-17
proximo_review: 2026-08-17
status: draft
diataxis: reference
audiencia: agente
---

# Personas do módulo Billing SaaS

> Personas específicas do módulo. Transversais ficam em `../../personas.md` e `docs/comum/personas.md`.

---

## Persona 1: Administrador-Dono do tenant (cliente do Aferê)

**Identidade:** dono ou sócio-administrador da empresa cliente (assistência técnica/calibração). Não é técnico em TI; conhece operação e financeiro do próprio negócio.

**Goals deste módulo:**
- Saber exatamente quanto paga pelo Aferê e por quê.
- Mudar de plano sem precisar abrir suporte.
- Aplicar cupom recebido em campanha.
- Ver consumo (usuários, módulos) vs limite.
- Regularizar inadimplência rapidamente.

**Frustrations específicas:**
- "Não sei se vale a pena fazer upgrade — quero ver meu consumo."
- "Recebi um cupom mas não acho onde aplicar."
- "Esqueci de pagar e fui bloqueado sem aviso."

**Jornada típica:**
1. Recebe alerta de uso em 80% do limite.
2. Abre painel de billing, compara planos.
3. Faz upgrade — confirma proporcionalização.
4. Vê fatura nova já com novos limites liberados.

**Devices:** web desktop principal; email/mobile para alertas.
**Frequência:** mensal (fatura) + sob demanda (upgrade/cupom).

---

## Persona 2: Operador comercial do Aferê (interno — equipe do Roldão)

**Identidade:** pessoa da equipe Aferê que dá suporte comercial: cria cupons, configura planos, isenta cobrança em casos específicos, acompanha churn.

**Goals deste módulo:**
- Criar/gerenciar cupons e campanhas.
- Ver dashboard de MRR, churn, inadimplência.
- Estornar/conceder crédito em casos pontuais (com trilha).
- Mover tenant entre planos manualmente quando negociado.

**Frustrations específicas:**
- "Cliente VIP precisa de desconto fora da tabela — não pode ser feito sem código."
- "Quero entender por que esse tenant cancelou."

**Jornada típica:**
1. Acessa painel admin do Billing SaaS.
2. Cria cupom "PARCEIRO2026" — 20% por 3 ciclos.
3. Monitora aplicação semanal.

**Devices:** web desktop.
**Frequência:** diária.

---

## Persona 3: Sistema (job automatizado)

**Identidade:** worker em fila procrastinate rodando jobs de billing (cobrança, alerta, bloqueio progressivo).

**Goals deste módulo:**
- Cobrar faturas vencidas sem duplicar.
- Disparar alertas de trial/vencimento na janela correta.
- Aplicar bloqueio progressivo (D+3 warning, D+7 read-only, D+15 suspensão).
- Reagir a webhooks de gateway (Stripe/PagSeguro).

**Frustrations específicas:** (não aplicável — é sistema)

**Devices:** servidor backend.
**Frequência:** contínua (jobs cron).

---

## Convenções

- Persona específica = papel com responsabilidade ÚNICA neste módulo.
- "Administrador-Dono do tenant" aparece em vários módulos — manter aqui apenas o recorte específico do Billing; aspectos transversais vão pra `../../personas.md`.
