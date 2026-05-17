---
owner: Roldão
revisado-em: 2026-05-17
status: draft
modulo: contas-pagar
dominio: financeiro
---

# Personas — Contas a Pagar

> Wave C — discovery rigoroso ainda não feito. Esboço inicial pra ancorar entrevistas futuras.

## P-FIN-01 — Responsável financeiro (primária)

**Quem é:** mesmo perfil de Contas a Receber.

**Jornada esperada:**
1. Recebe boleto/NF do fornecedor (email, papel, WhatsApp)
2. Cadastra lançamento + anexa documento
3. Categoriza (plano de contas + centro de custo)
4. Se valor > alçada, escala pra dono
5. No vencimento, paga via banco e marca baixa
6. Concilia OFX no fim do mês

**Frustrations hipotéticas (validar):**
- "Pago 100 boletos por mês e não sei quanto gastei com aluguel vs equipamento"
- "Dono quer aprovar tudo > R$ 5k e me liga atrasando o pagamento"
- "Não sei se já paguei o aluguel — pago de novo por garantia"

**Permissões:** lançar, baixar próprios, conciliar; aprovação conforme alçada.

## P-FIN-02 — Dono

**Toca o módulo:**
- Aprovar lançamentos > alçada
- Ver "quanto vou pagar mês que vem" (fluxo projetado — vem do OP12)
- Decidir adiantar / postergar pagamento conforme caixa

**Permissões:** ver tudo + aprovar.

## P-GER — Gerente de área (hipótese a validar)

**Quem é:** gerente operacional do setor (oficina, comercial, suporte). Pode ter alçada limitada pra aprovar despesa do seu centro de custo.

**Toca o módulo:** aprovação primária antes do financeiro.

**Decisão de discovery:** existe esse papel no tenant médio Aferê? Ou financeiro+dono cobrem tudo? Validar em entrevistas.

## P-CONT — Contador externo (V2)

**Toca o módulo:** consome export pra apuração mensal. Não opera lançamento dentro do Aferê (continua usando ERP próprio dele).

## Anti-personas

- Fornecedor pedindo acesso direto pra ver status do próprio título — não permitido (canal externo).
- Auditor fiscal externo pedindo modificar lançamento — só leitura.

## Próximos passos discovery

- Entrevistar 5 tenants sobre "como você paga seus fornecedores hoje?"
- Validar existência do papel Gerente de área
- Mapear regimes de alçada usados na prática
