---
owner: Roldão
revisado-em: 2026-05-17
status: draft
modulo: clientes
dominio: comercial
diataxis: reference
---

# Contratos Export — Módulo Clientes

## Exports

### 1. Lista de clientes — CSV/XLSX
**Propósito:** dono/vendedor baixa carteira para análise externa.
**Formato:** CSV (UTF-8 BOM) + XLSX.
**Campos:** id, tipo, documento, nome_ou_razao, telefones, emails, segmentos, rating, limite_credito, uso_credito, bloqueado, criado_em, ultima_os_em.
**Permissão:** dono, vendedor (filtrado pelo próprio).
**Regulado:** não.
**Retenção:** download imediato; sem persistência.

### 2. Visão 360° — PDF
**Propósito:** imprimir/enviar ficha completa para auditoria interna ou cliente.
**Formato:** PDF (template configurável pelo tenant).
**Campos:** cabeçalho (cliente + tenant), dados cadastrais, lista de OS últimos 12 meses, certificados vigentes, financeiro (resumo), NPS.
**Permissão:** atendente, vendedor, dono.
**Assinatura digital:** não (uso interno).

### 3. Portabilidade LGPD — JSON
**Propósito:** atender pedido LGPD art. 18 (titular pede seus dados).
**Formato:** JSON estruturado.
**Conteúdo:** TODOS os dados pessoais do cliente + histórico de consentimentos + lista de eventos timeline.
**Permissão:** DPO do tenant + auditoria registrada.
**Regulado:** sim — LGPD art. 18.
**Retenção:** download imediato + log da geração (RAT-03).
**Referência:** `docs/conformidade/comum/lgpd-rat.md` RAT-03.

### 4. Relatório de duplicatas detectadas — CSV
**Propósito:** dono auditar dedup automático antes/depois.
**Campos:** par de clientes (master + perdedor), score, ação tomada (auto/manual), data, por.
**Permissão:** dono.

### 5. Lista de inadimplentes/bloqueados — XLSX
**Propósito:** financeiro recebe semanalmente lista de bloqueados + motivo + dias bloqueado.
**Campos:** cliente, documento, motivo, dias_bloqueado, divida_atual, vendedor_responsavel.
**Permissão:** financeiro, dono.

### 6. Importação template — XLSX (download)
**Propósito:** baixar template padrão para importação 1-clique.
**Formato:** XLSX com cabeçalhos + 1 linha de exemplo + aba "instruções".
**Permissão:** atendente, dono.

## Exports inter-módulos

- Lista de clientes (export 1) é consumida por:
  - Módulo **crm** para criar segmentos manuais.
  - Módulo **financeiro** para análise de carteira.
- Ver `../../../comum/integracoes-inter-modulos.md`.

## Versionamento

Schema de export PDF é configurável pelo tenant (template). Mudança em schema **regulado** (LGPD portabilidade) requer ADR.

## Como evolui

Export novo → adicionar + validar permissão. Mudança em formato → CHANGELOG.
