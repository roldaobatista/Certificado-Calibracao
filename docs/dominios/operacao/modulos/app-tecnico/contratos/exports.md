---
owner: roldao
revisado_em: 2026-05-17
status: draft
diataxis: reference
audiencia: agente
relacionados:
  - docs/conformidade/comum/fiscal.md
---

# Contratos de Export — Módulo App do Técnico

> Exports gerados pelo app (PDFs simples, CSVs locais). Exports REGULADOS (NF-e, certificado RBC) NÃO acontecem aqui.

---

## Exports

### Export 1: PDF de Aceite de Serviço
**Propósito:** comprovante de conclusão entregue ao cliente.
**Formato:** PDF.
**Regulado?:** não (aceite contratual). Para certificado ISO 17025 regulado, ver módulo Calibração.
**Validador externo:** —
**Template/Schema:** template HTML→PDF embarcado no app (geração offline).
**Campos obrigatórios:** número OS, cliente, CNPJ/CPF, endereço, equipamento, serviços executados, peças consumidas, técnico, data/hora início e fim, assinatura tátil do cliente, nome e CPF do signatário, foto opcional.
**Campos opcionais:** observações.
**Assinatura digital:** NÃO (assinatura é tátil — não tem valor ICP-Brasil — ver ADR-0009 pra A3).
**Imutabilidade pós-emissão:** sim — hash do PDF gravado no servidor pós-sync (`INV-001` — trilha WORM).
**Retenção:** ver `../../../conformidade/comum/retencao-matriz.md` (a criar).

**Exemplo (campos):**
```
OS Nº 2026-001234
Cliente: ACME Indústria Ltda. — CNPJ 12.345.678/0001-99
Endereço: Rua X, 123 — São Paulo/SP
Equipamento: Balança XYZ s/n 999
Serviços:
  - Calibração interna (2026-05-17 09:30–11:15)
  - Ajuste de zero
Peças:
  - Sensor 4-20mA — qtd 1
Técnico: João Silva
Assinado por: Cliente — Maria Souza — CPF 123.***.***-99
Hash SHA-256: a1b2c3...
```

---

### Export 2: PDF de Prestação de Contas
**Propósito:** acerto financeiro pós-viagem.
**Formato:** PDF.
**Regulado?:** não.
**Template:** template HTML→PDF embarcado.
**Campos obrigatórios:** técnico, viagem (período + roteiro), adiantamento total, lista de despesas (categoria, valor, foto-comprovante), saldo a receber/devolver, assinatura técnico, assinatura coordenador (pós-aprovação web).
**Assinatura digital:** opcional (A3 do coordenador se exigido por política interna).
**Imutabilidade:** sim, após aprovação no web.

---

### Export 3: Resumo do Dia (PDF/CSV local)
**Propósito:** técnico exporta resumo do que fez no dia (offline).
**Formato:** PDF ou CSV.
**Regulado?:** não.
**Campos:** OS atendidas, horas trabalhadas, peças consumidas, despesas, distância percorrida.

---

### Export 4: Fotos da OS (zip)
**Propósito:** entregar pacote de fotos ao cliente ou anexar a relatório.
**Formato:** ZIP de imagens.
**Regulado?:** não. EXIF preservado (timestamp, GPS).
**Onde gera:** sob demanda, no app ou no web.

---

## Exports inter-módulos

- PDF de Aceite → vinculado à OS no módulo OS (link em `os/contratos/exports.md`).
- Prestação de contas → consumida por Caixa do Técnico (Financeiro).
- Fotos → podem virar evidência em laudo do módulo Calibração quando aplicável.
Ver `../../../comum/integracoes-inter-modulos.md`.

## Versionamento de export regulado

- Não aplicável (este módulo não emite exports regulados).
- Se futuramente o aceite tiver validade jurídica (ICP-Brasil), promover a ADR.

## Como esta lista evolui

- Export novo → adicionar + se regulado, validar contra schema oficial.
- Mudança em template → bump CHANGELOG.
- Export descontinuado → `@deprecated`.
