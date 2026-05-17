---
owner: roldao
revisado_em: 2026-05-17
status: draft
diataxis: reference
audiencia: agente
modulo: seguranca-trabalho
relacionados:
  - docs/conformidade/comum/retencao-matriz.md
---

# Contratos de Export — Módulo Segurança do Trabalho

> Formatos de saída. Inclui documentos que servem de prova jurídica em ação trabalhista / fiscalização MTE.

---

## Exports

### Export 1: Termo de Entrega de EPI (PDF)
**Propósito:** prova jurídica de entrega de EPI ao colaborador (NR-06 item 6.6.1).
**Formato:** PDF.
**Regulado?:** sim — NR-06.
**Validador externo:** não há validador automatizado MTE; é peça em ação trabalhista.
**Template:** template tenant configurável (logo, razão social, CNPJ).
**Campos obrigatórios:** identificação tenant (razão social + CNPJ), identificação colaborador (nome, CPF, função), EPI (nome, nº CA, validade CA, fornecedor), quantidade, data entrega, validade individual, assinatura do colaborador, assinatura do entregador, hash do documento.
**Assinatura digital:** sim — assinatura touch + hash + timestamp; opcionalmente carimbo ITI (`INV-017` em V2).
**Imutabilidade pós-emissão:** sim — `INV-001`.
**Retenção:** ≥5 anos após desligamento (Receita) + cobertura prescricional trabalhista (5 anos contados do término). Ver `retencao-matriz.md`.

---

### Export 2: Ficha de EPI por colaborador (PDF)
**Propósito:** histórico consolidado de EPIs entregues a um colaborador.
**Formato:** PDF.
**Regulado?:** boa prática NR-06.
**Campos:** dados colaborador + tabela cronológica de entregas (data, EPI, nº CA, qtd, validade, assinatura).
**Assinatura digital:** não (consolidado).
**Retenção:** mesma do Termo.

---

### Export 3: Relatório de Segurança (PDF + XLSX)
**Propósito:** consolidado periódico para gerência / auditoria interna.
**Formato:** PDF (visual) + XLSX (dados crus).
**Regulado?:** não (uso interno + opcional para auditoria MTE).
**Campos:** período, TF, TG, nº acidentes (por gravidade), nº quase-acidentes, EPIs entregues, ASOs realizados/válidos, treinamentos válidos/vencidos.

---

### Export 4: Permissão de Trabalho (PDF + QR code)
**Propósito:** documento físico/digital de PT para anexar à frente de serviço de risco.
**Formato:** PDF com QR code apontando para registro no sistema.
**Regulado?:** sim — NR-33 / NR-35 (modelo livre, conteúdo mínimo regulado).
**Campos:** identificação OS, tipo de risco, executante, emitente, descrição serviço, medidas de controle, EPIs exigidos, validade até, assinaturas.
**Imutabilidade pós-emissão:** sim — `INV-001`.
**Retenção:** ≥5 anos.

---

### Export 5: APR preenchida (PDF)
**Propósito:** anexo à OS como prova de análise prévia.
**Formato:** PDF.
**Regulado?:** boa prática SST.
**Campos:** identificação OS + template APR preenchido + assinatura do técnico.
**Imutabilidade pós-emissão:** sim — `INV-001`.
**Retenção:** vinculada à OS (5 anos mínimo).

---

### Export 6: Checklist de segurança preenchido (PDF)
**Propósito:** anexo à OS.
**Formato:** PDF.
**Regulado?:** boa prática.
**Campos:** template + respostas + observações + assinatura técnico + data/hora.
**Retenção:** vinculada à OS.

---

### Export 7: Registro de Acidente / Quase-Acidente (PDF)
**Propósito:** documento interno + base para futura CAT eletrônica eSocial (V2).
**Formato:** PDF.
**Regulado?:** uso interno; CAT formal é V2 (eSocial S-2210).
**Campos:** identificação tenant, tipo, data/hora, local, descrição, gravidade, colaboradores envolvidos, evidências fotográficas referenciadas, ação corretiva, responsável, status.
**Imutabilidade pós-emissão:** sim — adendos permitidos (`INV-001`).
**Retenção:** ≥20 anos (referência: prazo prescricional acidentário e CAT no INSS).

---

### Export 8: ASO consolidado (PDF — apenas para auditoria interna)
**Propósito:** lista de ASOs válidos da equipe; NÃO substitui ASO médico original.
**Formato:** PDF.
**Regulado?:** ASO original é o documento legal (do médico do trabalho); aqui é apenas consolidação interna.
**LGPD:** dado pessoal sensível (saúde) — acesso restrito por RBAC.

---

## Exports inter-módulos

- **Termo de Entrega EPI** → consumido por `colaboradores/` na ficha do colaborador.
- **Registro de Acidente** → consumido por `qualidade/` quando vira não-conformidade.
- **Checklist + APR + PT** → consumidos pela `operacao/ordens-de-servico` como anexos imutáveis da OS.

Ver `../../../comum/integracoes-inter-modulos.md`.

## Versionamento de export regulado

- NRs raramente mudam formato de termo. Quando MTE publica nova norma, abrir ADR + janela de migração.

## Como esta lista evolui

- Export novo → adicionar + validar contra norma se regulado.
