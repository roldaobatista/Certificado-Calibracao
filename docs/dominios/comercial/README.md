---
owner: Roldão
revisado-em: 2026-05-17
status: draft
---

# Domínio: Comercial

## O que é este domínio

Comercial agrupa **tudo da relação pré-venda + pós-venda comercial com cliente**: captura/prospecção, cadastro do cliente, oportunidades, orçamentos/propostas, contratos recorrentes, CRM, follow-up, NPS. Inclui também as interfaces externas voltadas ao cliente final (portal, comunicação WhatsApp, lembrete de recalibração).

## Fronteiras com outros domínios

- **Entra:** lead, cliente cadastrado, oportunidade, orçamento, contrato recorrente, comunicação ativa com cliente, indicação/NPS, segmentação, limite de crédito (comercial).
- **NÃO entra (vai pra Operação):** abertura de OS, atribuição de técnico, execução de serviço em campo/lab.
- **NÃO entra (vai pra Financeiro):** cobrança, emissão de NFS-e, conciliação, comissão liquidada.
- **NÃO entra (vai pra Suporte-Plataforma):** equipamento do cliente (cadastro técnico), peça consumida, produto/serviço de catálogo.

## Módulos deste domínio

| Módulo | Status | Pasta | Cobertura discovery |
|---|---|---|---|
| Clientes | ⏳ a especificar | `modulos/clientes/` | F-C (Foundation) + BIG-07; OP-Cliente proposta |
| Orçamentos | ⏳ a especificar | `modulos/orcamentos/` | OP14 (nova) |
| CRM | ⏳ a especificar | `modulos/crm/` | OP5 + BIG-10 + BIG-11 |
| Contratos | ⏳ a especificar | `modulos/contratos/` | OP1 (recorrência) |

## Personas que tocam este domínio

Ver `personas.md` deste domínio. Núcleo:
- **Dono / sócio** (decisor de compra)
- **Atendente / recepcionista** (CRM diário)
- **Vendedor** (orçamento + follow-up)
- **Cliente final do tenant** (portal + WhatsApp)
- **Diego — Consultor RBC** (canal indicação — Persona 15 do discovery)

## Compliance específico

- LGPD: ver `../../conformidade/comum/lgpd-rat.md` (RAT-03 Cadastro cliente final, RAT-06 Lembrete WhatsApp)
- Direitos do titular (LGPD art. 18): Aferê é operador; controlador (tenant) decide.
- Anti-fidelidade abusiva: princípio fundador do produto (`prd.md` §6).

## Integrações com outros domínios

Ver `../../comum/integracoes-inter-modulos.md`. Eventos típicos:
- Comercial → Operação: `OrcamentoAprovado` → cria rascunho de OS
- Comercial → Financeiro: contrato aprovado dispara cobrança recorrente
- Operação → Comercial: `OSConcluida` alimenta timeline 360° + dispara pesquisa NPS
- Comercial → Externo: `LembreteRecalibracaoEnviado` (WhatsApp BSP)

## ADRs específicos do domínio

A criar conforme módulos amadurecem (não há ADR comercial-específica hoje).

## Status do domínio

🟡 **Discovery alta + especificação baixa.** BIGs e OPs mapeados; especificações de módulo (campos, fluxos, máquina de estados) pendentes. Módulo Clientes provavelmente entra em Wave A (F-C cliente master); demais em Wave B.
