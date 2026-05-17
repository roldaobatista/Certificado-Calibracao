---
owner: roldao
revisado_em: 2026-05-17
status: draft
diataxis: reference
audiencia: agente
relacionados:
  - docs/conformidade/comum/fiscal.md
---

# Contratos de Export — Módulo Marketplace

> Formatos de saída específicos do módulo.

---

## Exports

### Export 1: Comprovante de solicitação (PDF)

**Propósito:** dar ao cliente um comprovante PDF do pedido de orçamento enviado.
**Formato:** PDF.
**Regulado?:** não.
**Validador externo:** —
**Template/Schema:** template HTML+CSS renderizado para PDF (engine a definir após ADR-0001).
**Campos obrigatórios:** protocolo, data, dados de contato (nome + e-mail + telefone, sem CNPJ/CPF se omitidos), itens (nome, qtd, preço snapshot ou "a consultar"), observações, termo LGPD aceito em.
**Campos opcionais:** logo do tenant, observações internas (não exibidas ao cliente).
**Assinatura digital:** não.
**Imutabilidade pós-emissão:** sim — snapshot do momento do envio (INV-026 aplicável aos preços).
**Retenção:** ver `../../../../conformidade/comum/retencao-matriz.md`.

---

### Export 2: Relatório de funil (CSV/XLSX)

**Propósito:** análise externa de conversão (Excel, BI).
**Formato:** CSV + XLSX.
**Regulado?:** não.
**Campos obrigatórios:** data, etapa do funil, qtd, taxa de conversão, utm_source/medium/campaign, valor estimado.
**Campos opcionais:** segmento, região.
**Anonimização:** SEM PII — só sessões e agregações (RAT-04).
**Retenção:** 24 meses online; histórico em WORM Backblaze.

---

### Export 3: Lista de carrinhos abandonados (CSV)

**Propósito:** ação comercial de recuperação (envio manual de WhatsApp/e-mail pelo vendedor).
**Formato:** CSV.
**Campos obrigatórios:** data carrinho, itens, valor estimado, canal de origem.
**Campos opcionais:** dados de contato (SE o visitante chegou a preencher mas não enviou — exige base legal LGPD; ver `docs/conformidade/`).
**Retenção:** 90 dias.

---

### Export 4: Histórico do cliente (PDF — área do cliente)

**Propósito:** cliente baixar histórico próprio para arquivo.
**Formato:** PDF.
**Campos obrigatórios:** dados do cliente, solicitações, orçamentos, OS, contratos, faturas (resumo).
**Auth:** só o próprio cliente (e dentro do escopo de visão).
**Retenção:** gerado sob demanda.

---

## Exports inter-módulos

- `SolicitacaoOrcamento` → consumido por `orcamentos` (cria rascunho) e `crm` (cria lead). Ver `../../../../comum/integracoes-inter-modulos.md`.
- `EventoConversao` → consumido por `analytics` para alimentar dashboards.

## Versionamento de export

- Mudança em layout do PDF de comprovante → bump CHANGELOG seção "Modificado".
- Mudança em colunas de CSV → ADR (quebra de integração externa).

## Como esta lista evolui

- Export novo → adicionar.
- Mudança em formato → ADR.
- Export descontinuado → `@deprecated`.
