---
owner: Roldão
revisado-em: 2026-05-17
status: draft
modulo: estoque
dominio: suporte-plataforma
---

# Contratos de Export — Estoque

## Exports

### Export 1: Saldo atual (XLSX/CSV)

**Propósito:** snapshot operacional / auditoria.
**Formato:** XLSX preferencial / CSV.
**Regulado:** não.
**Campos obrigatórios:** item_código, item_nome, local, lote, validade, NS, saldo, reservado, em_trânsito, custo_médio (se V2).
**Filtros:** mesmos da Tela 1.

---

### Export 2: Kardex (CSV)

**Propósito:** rastreabilidade fiscal/auditoria (BIG-12 — selo INMETRO).
**Formato:** CSV.
**Regulado:** parcialmente (suporta auditoria CGCRE de padrão metrológico).
**Validador:** auditor CGCRE manual (P-SUP-05).
**Campos obrigatórios:** timestamp, tipo_movimento, item, local_origem, local_destino, quantidade, lote, NS, OS, usuário, foto_url (se transferência).

---

### Export 3: Inventário finalizado (PDF + XLSX)

**Propósito:** ata de inventário assinada.
**Formato:** PDF (com assinatura digital do responsável quando V2) + XLSX detalhado.
**Campos:** local, data, responsável, lista de itens com (contagem física, sistema, diferença, motivo do ajuste).
**Retenção:** ver `docs/conformidade/comum/retencao-matriz.md` — [INFERÊNCIA] 5 anos fiscal.

---

### Export 4: Relatório de transferências (XLSX)

**Propósito:** auditoria de transferências 2-etapas (BIG-12).
**Campos:** id, emissão_em, origem, destino, item, qtd, status, aceite_em, foto_url, recusa_motivo.
**Foto:** link assinado de curta duração (não embute binário no XLSX).

---

### Export 5: Relatório de lotes vencendo (CSV)

**Propósito:** alerta operacional.
**Filtros:** próximos 30/60/90 dias.

---

### Export 6: Rastreabilidade de padrão metrológico (PDF)

**Propósito:** documento para auditoria CGCRE (P-SUP-05).
**Conteúdo:** padrão (NS), certificado próprio, kardex completo, lista de calibrações que usaram este padrão (cruza com módulo Calibração).
**Regulado:** ISO 17025 cláusula 6.5.
**Assinatura digital:** sim (Wave futura — assinatura RT).

---

## Exports inter-módulos

- Saldo consumido por **OS** (Operação) — via API com `data_referencia` quando aplicável.
- Kardex de padrão consumido por **Calibração** (Metrologia) para conformidade ISO 17025.
- Movimentos alimentam **Financeiro** para CMP e custo da OS.

## Versionamento

- Mudança de colunas → bump CHANGELOG + janela 6 meses.

## Como evolui

- Export novo → adicionar + coordenar com Calibração/Financeiro se for rastreabilidade.
- Foto: garantir storage com link assinado, nunca embutir binário em XLSX/CSV.
