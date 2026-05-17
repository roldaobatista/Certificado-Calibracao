---
owner: Roldão
revisado-em: 2026-05-17
status: draft
modulo: crm
dominio: comercial
diataxis: reference
---

# Contratos Export — Módulo CRM

## Exports

### 1. Pipeline atual — XLSX
**Propósito:** dono baixa snapshot do funil + projeção.
**Campos:** oportunidade, cliente, valor, etapa, vendedor, idade na etapa, probabilidade, prevista_fechar.
**Permissão:** dono, gerente, vendedor (filtrado pelo próprio).

### 2. Funil de conversão — XLSX
**Propósito:** análise mensal (criado → ganho).
**Campos:** período, coorte, criadas, qualificadas, orçadas, ganhas, perdidas, taxa por etapa, motivos top de perda.
**Permissão:** dono, gerente.

### 3. Histórico NPS — CSV
**Propósito:** auditoria + análise de comentários.
**Campos:** data, cliente, nota, categoria, comentário, OS_relacionada, vendedor_responsavel, ação_tomada.
**Permissão:** dono, gerente.
**LGPD:** comentários podem ter dado pessoal — controle de acesso forte.

### 4. Execuções de automação — CSV
**Propósito:** auditoria (quem foi afetado por qual automação).
**Campos:** automação, executada_em, clientes_afetados[], mensagens_enviadas, custo_estimado.
**Permissão:** dono.
**Regulado parcial:** LGPD (mostra quem recebeu comunicação).

### 5. Carteira do vendedor — XLSX
**Propósito:** vendedor baixa próprios clientes + sinais + última interação.
**Campos:** cliente, último contato, próximo lembrete, oportunidades abertas, valor previsto, NPS, status.

### 6. Motivos de perda — XLSX
**Propósito:** análise gerencial.
**Campos:** motivo, ocorrências, valor_perdido, vendedores_envolvidos, periodo.

### 7. Mensagens transacionais enviadas — CSV
**Propósito:** auditoria LGPD (RAT-06 WhatsApp).
**Campos:** cliente, canal, template_id, conteúdo (com variáveis), enviado_em, status_entrega, automação_origem.
**Permissão:** DPO + dono.
**Retenção:** 5 anos (LGPD + auditoria Meta BSP).

## Exports inter-módulos

- `NPS.Respondido` → módulo `clientes` (timeline 360°) + módulo `contratos` (renovação considera NPS).
- `Oportunidade.Ganha` → módulo `orcamentos` (já vinculada) + `financeiro` (forecast).
- Carteira vendedor → módulo `financeiro/comissoes` (cálculo de comissão).

## Mensagens WhatsApp (templates regulados Meta BSP)

| Template | Variáveis | Aprovação Meta | Categoria |
|---|---|---|---|
| `lembrete_recalibracao` | nome, equipamento, vencimento_em | obrigatória | utilidade |
| `nps_solicitar` | nome, os_numero | obrigatória | atendimento_cliente |
| `tarefa_followup_interno` | (uso interno — não cliente) | n/a | n/a |

**Regulado:** sim — Meta BSP. Mudança em conteúdo requer reaprovação. RAT-06.

## Versionamento

- Templates WhatsApp seguem ciclo da Meta (janela depende deles).
- Exports XLSX/CSV — mudança schema interna requer CHANGELOG.

## Como evolui

Export novo → adicionar + RBAC. Template WhatsApp novo → submeter Meta + ADR.
