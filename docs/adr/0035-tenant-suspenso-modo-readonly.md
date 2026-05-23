---
adr: 0035
titulo: Tenant suspenso — matriz módulos param/continuam + direitos LGPD preservados
owner: roldao
revisado-em: 2026-05-22
status: proposta
proposto-por: agente (auditoria projeto-inteiro 10 lentes — Onda 1 transversal, C-INT-02)
revisado-por: tech-lead-saas-regulado + advogado-saas-regulado
bloqueia-fase: Wave A Marco 3 + 1º caso real de inadimplência pós-cliente externo
depende-de: ADR-0015 (lifecycle tenant — INV-INT-009), ADR-0021 (anonimização vs retenção)
---

# ADR-0035 — Tenant suspenso: matriz "param/continuam"

## O QUE

Quando tenant entra em estado `suspenso` (inadimplência D+90 — ADR-0015 fluxo 3), módulos **não** param uniformemente. Esta ADR crava **matriz vinculante** de quais módulos:

1. **Parar** (bloqueio total — usuário do tenant nem lê).
2. **Continuar em leitura** (somente-leitura — usuário lê o que já existe, nada novo).
3. **Continuar normal** (cumprimento de obrigação legal — independe de pagar).

E nomeia evento canônico `BillingSaas.TenantSuspenso` com `modo: read_only|bloqueado_total` (refina INV-INT-009).

## PORQUE

- LGPD art. 18 garante ao **titular** (cliente final do tenant) direito de acesso, retificação, eliminação. Esses direitos **não** dependem de o tenant ter pagado. Bloquear export LGPD por inadimplência = infração ANPD.
- LGPD art. 9º + 18 §4º — operador (Aferê) responde solidariamente quando bloqueia atendimento de direito por motivo comercial.
- ISO 17025 cl. 8.4 — registros do laboratório (tenant) não podem ser apagados nem ficar inacessíveis pelo período de retenção, independente de o tenant ter pagado.
- Receita Federal — NF-e emitida tem trilha imutável de 5 anos; tenant suspenso não pode quebrar isso.
- Auditoria Onda 1 C-INT-02 detectou: ausência de matriz; cada módulo decidindo isolado vira drift garantido.

## COMO

### Matriz vinculante

| Módulo | Tenant `read_only` | Tenant `bloqueado_total` | Justificativa |
|---|---|---|---|
| **acesso-seguranca (login operador)** | Login OK, banner "Tenant suspenso — leitura apenas" | Login bloqueado | Comercial |
| **portal-cliente (titular LGPD)** | Continua normal | Continua normal | LGPD art. 18 — direito do titular independe de pagar |
| **export LGPD** (titular pede dados) | Continua normal | Continua normal | LGPD art. 18 II — não bloqueável |
| **audit trail** (gravação) | Continua normal | Continua normal | LGPD art. 37 + ISO 17025 cl. 8.4 |
| **leitura de cert/OS/NF emitido** | Continua normal | Continua normal | Receita 5a + ISO 17025 cl. 8.4 |
| **emissão NF-e nova** | Bloqueada | Bloqueada | Comercial |
| **emissão certificado novo** | Bloqueada | Bloqueada | Comercial |
| **criação OS nova** | Bloqueada | Bloqueada | Comercial |
| **edição cadastro cliente** | Bloqueada | Bloqueada | Comercial |
| **resposta a incidente ANPD** | Continua normal | Continua normal | LGPD obrigação legal + Res. ANPD 15/2024 |
| **fiscal — CC-e em NF já emitida** | Permitida (janela 24h) | Permitida (janela 24h) | Receita — correção de NF emitida não é "nova emissão" |
| **comunicacao-omnichannel** | Bloqueada | Bloqueada | Comercial; canal "cobrança" continua via régua billing-saas |
| **billing-saas — pagamento de fatura aberta** | Continua normal | Continua normal | Único caminho de reativação |
| **dashboard tenant (operador)** | Read-only com banner | Sem acesso | UX honesto |

### Reativação automática

- `ContasReceber.Pago` da última fatura vencida → `BillingSaas.TenantReativado` em ≤5 min.
- Ordem de reativação cravada (saga em ADR-0034):
  1. `billing-saas` publica `TenantReativado`.
  2. `acesso-seguranca` libera login + cache invalidado.
  3. `feature-flags` re-ativa features do plano.
  4. Módulos comerciais (OS, certificados, fiscal, comunicação) consomem `Features.Sincronizado` e voltam ao normal.

### Sagas em vôo na suspensão

- **NF-e em meio de emissão (saga ainda em `aguardando_sefaz`)** — termina a saga já iniciada (Receita não aceita "meia emissão"); novas NFs bloqueadas.
- **Certificado em meio de assinatura A3** — termina (cliente já viu o pré-cert); novos bloqueados.
- **OS em execução** — pausa em `aguardando_pagamento_tenant`; técnico vê banner; conclusão exige tenant reativado.

## ID

- **INV-BUS-TS-001** — `BillingSaas.TenantSuspenso` exige campo `modo: read_only|bloqueado_total` no payload (estende INV-INT-009).
- **INV-BUS-TS-002** — direitos LGPD do titular (portal-cliente, export, audit) **nunca** bloqueiam por suspensão de tenant — hook em endpoint valida `if tenant.suspenso and not endpoint_in_allowlist_lgpd: 451 Tenant Suspenso`.
- **INV-BUS-TS-003** — reativação em ≤5 min após `ContasReceber.Pago` (SLA + métrica observabilidade).

## NON-GOAL

- **Não** define janela de tolerância (grace period) — ADR-0015 cobre régua D+30/60/89.
- **Não** trata exclusão definitiva de tenant inadimplente (cancelamento contratual completo) — V2 ADR específica + retenção LGPD/Receita aplicável.
- **Não** redefine matriz de retenção — apenas crava que retenção continua independente de suspensão.

## Consequências

**Boas:** advogado pode auditar que LGPD não é violada em suspensão; auditor de produto bate matriz contra implementação; cliente final (titular) preservado independente de comercial; PR de qualquer módulo passa a citar esta matriz.

**Ruins:** matriz tem ~14 entries — manutenção a cada novo módulo (procedimento: adicionar linha + atualizar testes E2E de suspensão).

## Referências cruzadas

- ADR-0015 fluxo 3 (lifecycle tenant — origem) + INV-INT-009
- ADR-0021 (anonimização vs retenção — Zona A/B/C aplicada também aqui)
- LGPD art. 9º, 18 + Res. ANPD 15/2024
- ISO 17025 cl. 8.4
