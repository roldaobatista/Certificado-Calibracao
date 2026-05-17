---
owner: roldao
revisado_em: 2026-05-17
status: draft
diataxis: reference
audiencia: agente
relacionados:
  - docs/conformidade/comum/fiscal.md
  - docs/conformidade/comum/retencao-matriz.md
---

# Contratos de Export — Módulo Despesas

> Formatos de saída.

---

## Exports

### Export 1: Relatório de despesas (PDF)

**Propósito:** colaborador, gestor ou financeiro imprime/envia relatório de despesas com filtros.
**Formato:** PDF.
**Regulado?:** não.
**Validador externo:** —
**Template:** `templates/despesas/relatorio.html` (a criar quando F-A começar).
**Campos obrigatórios:** período, total geral, total por categoria, total por centro de custo, linhas com (data, descrição, valor, status, vínculo).
**Campos opcionais:** filtros aplicados, observação.
**Assinatura digital:** não.
**Imutabilidade pós-emissão:** não (relatório é fotografia momentânea).
**Retenção:** segue `retencao-matriz.md` — período fiscal de 5 anos para uso contábil.

**Exemplo:**
```
Relatório de Despesas — Tenant X — período 2026-05-01 a 2026-05-17
Total: R$ 4.812,30
  Combustível: R$ 2.140,00
  Alimentação: R$ 980,50
  ...
```

---

### Export 2: Despesas em CSV

**Propósito:** financeiro exporta para conciliação contábil ou ERP externo.
**Formato:** CSV (UTF-8, separador `;`).
**Regulado?:** não.
**Campos obrigatórios:** `id; data; colaborador_cpf_anonimizado_quando_agregado; valor; moeda; categoria; centro_custo; os_codigo; viagem_codigo; status; aprovado_em; reembolsado_em; pagamento_id`.
**Assinatura digital:** não.
**Imutabilidade:** não.
**Retenção:** 5 anos fiscal.

---

### Export 3: Comprovante original (download)

**Propósito:** colaborador, aprovador ou auditor baixa o arquivo original do comprovante.
**Formato:** mesmo do upload (JPG, PNG, PDF, XML).
**Regulado?:** parcial — comprovante fiscal (XML/cupom) tem regras de retenção próprias em `conformidade/comum/fiscal.md`.
**URL:** pré-assinada com validade ≤ 15 min.
**Imutabilidade pós-emissão:** sim — `INV-WORM-001`.
**Retenção:** ver `retencao-matriz.md` (mínimo 5 anos para fiscal; maior se vinculado a calibração ISO 17025).

---

### Export 4: Lote de reembolso para banco (CNAB / PIX)

**Propósito:** financeiro gera lote de pagamento das despesas aprovadas em `contas-pagar/`.
**Formato:** CNAB 240 / PIX em lote (consumido de `contas-pagar/`).
**Regulado?:** sim — banco valida layout CNAB.
**Validador externo:** banco recebedor.
**Imutabilidade:** sim após envio ao banco.

> Detalhe técnico do layout fica em `contas-pagar/contratos/exports.md`; este módulo apenas marca quais despesas entram no lote.

---

## Exports inter-módulos

- Lista de despesas aprovadas → consumido por `contas-pagar/` para gerar reembolso.
- Total por categoria/centro de custo → consumido por `relatorios-financeiros/` para DRE e despesas por período.
- Comprovante → opcionalmente referenciado por `fiscal/` quando crédito de imposto for aplicável.

Ver `../../../comum/integracoes-inter-modulos.md`.

## Versionamento de export regulado

- N/A para este módulo (relatórios são internos).
- Layout CNAB segue a versão suportada pelo banco contratado.

## Como esta lista evolui

- Export novo → adicionar.
- Mudança em formato → ADR se afetar integração externa.
- `@deprecated` → janela de migração 3 meses.
