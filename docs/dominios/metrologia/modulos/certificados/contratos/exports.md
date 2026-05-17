---
owner: roldao
revisado_em: 2026-05-17
status: draft
diataxis: reference
audiencia: agente
relacionados:
  - docs/conformidade/comum/fiscal.md
  - ../calibracao/controle-certificado-emitido.md
---

# Contratos de Export — Certificados

> Formatos de saída. Inclui exports REGULADOS (certificado ISO 17025) com validador externo.

---

## Exports

### Export 1: Certificado de Calibração PDF/A-1

**Propósito:** documento principal entregue ao cliente, atendendo ISO 17025 7.8.
**Formato:** PDF/A-1 (preservação ≥ 25 anos).
**Regulado?:** sim — ISO 17025 7.8 + NIT-DICLA + ICP-Brasil (assinatura).
**Validador externo:** verificadores PDF/A; verificador ICP-Brasil pra assinatura.
**Template/Schema:** template HTML do tenant + engine própria; estrutura mínima definida em `../calibracao/controle-certificado-emitido.md`.
**Campos obrigatórios:** identificação do laboratório (razão, CNPJ, endereço, número CGCRE se RBC), número certificado + versão + data emissão, identificação cliente (razão/CNPJ), identificação instrumento (descrição, fabricante, modelo, série, ID interno), padrões utilizados (descrição, certificado, validade), condições ambientais durante calibração, resultado das medições com incerteza expandida (k=2), declaração de conformidade + regra de decisão, validade recomendada de recalibração (se houver), assinatura digital A3 do RT, página/total páginas, hash SHA-256 visível no rodapé.
**Campos opcionais:** observações, anexos técnicos.
**Assinatura digital:** sim — A3 ICP-Brasil cliente-side (ADR-0009).
**Imutabilidade pós-emissão:** sim — `INV-014`, `INV-022`. Reemissão = nova versão.
**Retenção:** mínimo 25 anos (ISO 17025 8.4).

**Exemplo (snippet anonimizado):**
```
CERTIFICADO DE CALIBRAÇÃO Nº 1234/2026 — v1
Laboratório XPTO Ltda — CGCRE CRL-0123
Instrumento: Balança digital, marca Y, modelo Z, série 999
Validade recomendada: 12 meses
[tabela leituras + incerteza expandida U(k=2) = 0,05 g]
Decisão: Conforme — regra ILAC G8 (banda de guarda 30%)
Assinado digitalmente por: Fulano de Tal — CRQ XXX
Hash PDF: abc123...
```

---

### Export 2: Etiqueta de identificação (PDF + PNG)

**Propósito:** colar no instrumento, com QR Code linkando à página pública verificadora.
**Formato:** PDF (impressão A4 ou sticker) + PNG (impressão térmica).
**Regulado?:** parcial (etiqueta auxilia, não substitui certificado).
**Campos:** nº certificado + versão, validade recomendada, QR Code (URL pública /v/{token}), logo do laboratório.
**Sem PII do cliente na etiqueta.**
**Imutabilidade:** sim.
**Retenção:** mesma do certificado.

---

### Export 3: Relatório de Serviço PDF

**Propósito:** documento de serviço técnico (não-calibração).
**Formato:** PDF.
**Regulado?:** não (ISO 17025 não exige), mas pode ter assinatura A3.
**Campos:** OS, cliente, serviço executado, peças trocadas, técnico, datas, observações.

---

### Export 4: Relatório Fotográfico PDF

**Propósito:** comprovação fotográfica antes/depois.
**Formato:** PDF com fotos + EXIF preservado (timestamp + geolocalização).
**Campos por foto:** thumbnail, descrição, data/hora capturada, local (lat/long), hash SHA-256 da foto original.

---

### Export 5: Relatório de Não Conformidade PDF

**Propósito:** documento de NC pra auditoria de qualidade.
**Formato:** PDF.
**Campos:** nº NC, origem (calibração/serviço/auditoria), referência, descrição, ação imediata, ação corretiva, responsável, prazo, status, evidências.
**Retenção:** mínimo 25 anos (ISO 17025 8.7 + 8.4).

---

### Export 6: Laudo Técnico PDF

**Propósito:** parecer técnico avulso assinado pelo RT.
**Formato:** PDF + assinatura A3.

---

### Export 7: CSV de certificados emitidos (admin)

**Propósito:** consolidado pra contabilidade/gestão.
**Formato:** CSV UTF-8.
**Campos:** id, numero, ano, versao, tipo, cliente, data_emissao, status, valor_associado.

---

### Export 8: JSON de snapshot (auditoria/integração)

**Propósito:** snapshot completo dos dados do certificado pra integração externa ou auditoria.
**Formato:** JSON.
**Imutabilidade:** sim (snapshot).

---

## Exports inter-módulos

- Certificado PDF → consumido por **Portal do Cliente** (download).
- Snapshot JSON → consumido por **Fiscal** (gerar NF-e do serviço).
- NC → consumido por **Qualidade** (módulo de gestão da qualidade).
- Etiqueta + QR → consumido pelo **público externo** via `/v/{token}`.
- Ver `../../../comum/integracoes-inter-modulos.md`.

## Versionamento de export regulado

- Mudança em template visual → versão de template + snapshot preserva qual versão foi usada (não invalida certificados antigos).
- Mudança em estrutura mínima ISO 17025 (norma muda) → ADR + janela.
- PDF/A-1 vs PDF/A-3 (se migrar pra incluir anexos embedados) → ADR.

## Como esta lista evolui

- Export novo → adicionar + validar contra schema.
- Mudança em formato regulado → ADR + atualizar validador.
- Deprecado → `@deprecated`.
