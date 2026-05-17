---
owner: roldao
revisado_em: 2026-05-17
proximo_review: 2026-08-17
status: draft
diataxis: reference
audiencia: agente
---

# Personas do módulo Despesas

> Personas específicas. Transversais em `../../personas.md` e `docs/comum/personas.md`.

---

## Persona 1: Colaborador solicitante

**Identidade:** Técnico, vendedor, administrativo ou gestor que gasta em nome da empresa e precisa registrar para ser reembolsado ou prestar conta de adiantamento. 22–60 anos. Acesso ao app mobile (técnico/vendedor em campo) ou web (administrativo).

**Goals deste módulo:**
- Lançar despesa rápido, do celular, com foto da nota.
- Saber em tempo real se foi aprovada ou rejeitada.
- Receber o reembolso sem cobrar várias vezes o financeiro.

**Frustrations específicas:**
- Perder o comprovante físico antes de chegar no escritório.
- Não saber se a despesa foi aprovada ou se está parada com alguém.
- Esperar semanas pelo reembolso sem rastreio.

**Jornada típica:**
1. Faz uma despesa (combustível, almoço em viagem, peça avulsa).
2. Tira foto do comprovante no app.
3. Preenche valor, categoria, vínculo com OS se for de campo.
4. Envia para aprovação.
5. Acompanha status; recebe notificação de aprovação ou rejeição.
6. Se aprovado e sem adiantamento → reembolso na conta.
7. Se aprovado e com adiantamento → abate saldo do caixa do técnico.

**Devices:** mobile + web.
**Frequência:** semanal (técnico/vendedor), mensal (administrativo).

---

## Persona 2: Aprovador por alçada

**Identidade:** Gestor (supervisor, coordenador, gerente, diretor) com limite de aprovação por valor definido em RBAC. 30–55 anos.

**Goals deste módulo:**
- Aprovar com confiança que o gasto é legítimo e tem comprovante.
- Rejeitar com motivo claro quando regra interna for quebrada.
- Não receber despesa fora da sua alçada.

**Frustrations específicas:**
- Aprovar “no escuro” sem ver o comprovante.
- Receber pressão pra aprovar valores acima da alçada.

**Jornada típica:**
1. Recebe notificação de despesa pendente.
2. Abre, vê comprovante, vínculo com OS, justificativa.
3. Aprova, rejeita com motivo, ou pede ajuste.

**Devices:** web (principal), mobile (push).
**Frequência:** diário.

---

## Persona 3: Analista financeiro de reembolso

**Identidade:** Profissional do financeiro responsável por transformar despesa aprovada em pagamento efetivo e compensar contra adiantamentos. 25–45 anos.

**Goals deste módulo:**
- Reembolsar lote de despesas aprovadas em pagamento único.
- Compensar despesa contra adiantamento existente automaticamente.
- Gerar relatório de despesas por centro de custo para fechamento mensal.

**Frustrations específicas:**
- Re-digitar dado da despesa no contas a pagar.
- Compensar manualmente despesa vs. adiantamento em planilha.

**Devices:** web desktop.
**Frequência:** diário / semanal (fechamento).

---

## Convenções

- Persona repetida em ≥2 módulos com mesma responsabilidade → promover para `../../personas.md`.
- Persona em ≥2 domínios → promover para `docs/comum/personas.md`.
