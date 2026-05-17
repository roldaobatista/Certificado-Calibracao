---
owner: Roldão
revisado-em: 2026-05-17
status: draft
modulo: equipamentos
dominio: suporte-plataforma
---

# Contratos de Export — Equipamentos do cliente

## Exports

### Export 1: Etiqueta do equipamento (PDF)

**Propósito:** etiqueta física colada no instrumento, com QR.
**Formato:** PDF (tamanho A6 default; label 50x80mm opcional).
**Regulado:** não.
**Validador externo:** —
**Campos obrigatórios:** QR (URL assinada), TAG, NS, logo do tenant.
**Campos opcionais:** modelo, faixa, cliente.
**Assinatura digital:** não.
**Imutabilidade pós-emissão:** não (re-emissão revoga QR anterior).
**Retenção:** ver `../../../conformidade/comum/retencao-matriz.md`.

**Exemplo:** (mock)
```
+---------------+
|  [QR Code]    |
|  TAG: BAL-001 |
|  NS:  ABC123  |
|  [logo tenant]|
+---------------+
```

---

### Export 2: Ficha do equipamento (PDF para impressão/envio ao cliente)

**Propósito:** entregar ficha do equipamento ao cliente final.
**Formato:** PDF.
**Regulado:** não.
**Campos obrigatórios:** dados cadastrais + histórico de calibração (datas + nº certificado) + próxima calibração.
**Campos opcionais:** OS abertas, fotos do equipamento.
**Assinatura digital:** não (Wave futura — assinatura do RT).
**Retenção:** ver matriz.

---

### Export 3: Lista de equipamentos (CSV/XLSX)

**Propósito:** export operacional para auditoria interna ou migração.
**Formato:** CSV / XLSX.
**Regulado:** não.
**Campos:** TAG, NS, fabricante, modelo, faixa, classe, cliente, status, última calibração, próxima calibração.
**Filtros aplicáveis:** mesmos da Tela 1.

---

## Exports inter-módulos

- Lista de equipamentos consumida pelo módulo **Calibração** (Metrologia) ao iniciar OS — via API, não export.
- Lista de equipamentos do cliente consumida por **Cliente 360°** (Comercial) — via API.

## Versionamento

- Mudança de layout da etiqueta → bump CHANGELOG; etiquetas antigas continuam válidas (QR é estável).

## Como evolui

- Export novo → adicionar.
- Layout de etiqueta com QR → coordenar com módulo de impressão.
