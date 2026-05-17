---
owner: Roldão
revisado-em: 2026-05-17
status: draft
modulo: orcamentos
dominio: comercial
diataxis: reference
---

# Contratos Export — Módulo Orçamentos

## Exports

### 1. Orçamento PDF — visão cliente
**Propósito:** cliente baixa pelo link público + envio anexo WhatsApp/e-mail.
**Formato:** PDF (template configurável pelo tenant).
**Campos:** logo tenant + dados tenant + dados cliente + número do orçamento + versão + validade + tabela de itens (descrição, qtd, preço, desconto, total) + totais + condições de pagamento + texto rodapé/jurídico.
**Sem:** comissão, custo, margem (dados internos do tenant — separar visão).
**Permissão pública:** sim (acessível pelo token do link).
**Assinatura digital:** não no MVP-1 (V2 considera ICP-Br).
**Imutabilidade pós-aprovação:** sim — INV-026 (preço da versão aprovada é snapshot).
**Retenção:** 5 anos (alinhado a retenção fiscal — ver `docs/conformidade/comum/retencao-matriz.md`).

### 2. Orçamento PDF — visão interna
**Propósito:** vendedor/dono imprime versão com dados internos.
**Diferença:** inclui comissão prevista, margem (se config ativa), custo.
**Permissão:** vendedor responsável + dono (RBAC).

### 3. Lista de orçamentos — CSV/XLSX
**Propósito:** dono baixa pipeline pra análise.
**Campos:** número, cliente, responsável, estado, valor, criado_em, validade, lido_em, aprovado_em, motivo_recusa.
**Permissão:** dono, vendedor (filtrado pelo próprio).

### 4. Funil de conversão — XLSX
**Propósito:** análise mensal (criado → enviado → lido → aprovado → convertido).
**Campos:** período, coorte, taxas de conversão em cada etapa, ticket médio, tempo médio.
**Permissão:** dono.

### 5. Comparação de versões — PDF (Wave B)
**Propósito:** anexo para cliente quando há revisão.
**Formato:** PDF com diff visual destacando mudanças entre versões.

### 6. Link público "Pedir orçamento por WhatsApp" — payload de mensagem
**Propósito:** template de mensagem WhatsApp aprovado pela Meta.
**Formato:** texto + link + variáveis ({{nome_cliente}}, {{numero_orcamento}}, {{validade}}).
**Regulado:** sim — exige aprovação Meta BSP (RAT-06 LGPD).

## Exports inter-módulos

- `Orcamento.Aprovado` (evento) → módulo `operacao/os` cria OS rascunho com snapshot dos itens.
- Lista de orçamentos aprovados → módulo `financeiro/contas-receber` (após OS concluída).

## Versionamento de export

- Template PDF é configurável pelo tenant. Mudança no schema interno (campos) requer ADR + janela 6 meses.
- Payload WhatsApp regulado pela Meta — mudança requer reaprovação template.

## Imutabilidade

Versão aprovada do orçamento gera PDF idêntico mesmo após X anos. Mudança no template PDF do tenant **não afeta** PDFs já emitidos (snapshot do HTML/CSS do template no momento da emissão — INFERÊNCIA implementacional, confirmar com ADR).

## Como evolui

Export novo → adicionar + validar permissão.
