---
owner: roldao
revisado_em: 2026-05-17
status: draft
diataxis: reference
audiencia: agente
relacionados:
  - docs/conformidade/comum/fiscal.md
  - ./controle-certificado-emitido.md
  - ../certificados/contratos/exports.md
---

# Contratos de Export — Calibração

> Formatos de saída do módulo. Note que o **certificado PDF final** está em `../certificados/contratos/exports.md` (módulo Certificados). Aqui estão exports auxiliares do processo de calibração.

---

## Exports

### Export 1: Snapshot da calibração JSON

**Propósito:** payload completo (config + padrões snapshots + leituras + condições + orçamento incerteza + avaliação + revisões) enviado ao módulo Certificados para gerar o cert.
**Formato:** JSON.
**Regulado?:** indiretamente (entrada do cert ISO 17025).
**Imutabilidade:** sim após APROVADA (`INV-014`).
**Retenção:** mínimo 25 anos (ISO 17025 8.4).

---

### Export 2: Tabela de Orçamento de Incerteza (PDF auxiliar)

**Propósito:** anexo técnico opcional ao certificado, expande detalhamento do orçamento.
**Formato:** PDF.
**Campos:** componente, símbolo, distribuição, divisor, contribuição, % do total, grau de liberdade.
**Inclui:** versão do motor de cálculo + data do cálculo.
**Imutabilidade:** sim após emissão.

---

### Export 3: Etiqueta interna do laboratório (PDF/PNG)

**Propósito:** etiqueta colada no instrumento durante permanência no laboratório (≠ etiqueta externa do certificado, que é módulo Certificados).
**Formato:** PDF/PNG (impressão térmica).
**Campos:** ID interno, cliente, data entrada, QR linkando ao registro interno.
**Sem PII na etiqueta externa visível** (apenas ID + QR opaco).

---

### Export 4: Relatório de Ensaio Complementar (PDF auxiliar)

**Propósito:** detalhamento de linearidade, repetibilidade, excentricidade — anexo técnico ao certificado.
**Formato:** PDF.
**Campos:** método, dados brutos, gráficos, conclusão.

---

### Export 5: Histórico de Calibrações do Instrumento (PDF/CSV)

**Propósito:** entrega ao cliente histórico consolidado.
**Formato:** PDF (visual) ou CSV (dados).
**Campos:** data, certificado, decisão, U expandida, drift observado.

---

### Export 6: Certificado de Padrão (anexo PDF original)

**Propósito:** disponibilizar cópia do cert externo dos padrões (vinculados à calibração) para auditoria.
**Formato:** PDF (original do laboratório externo).
**Regulado?:** sim (evidência de rastreabilidade ISO 17025 6.5).
**Retenção:** ≥ 25 anos.

---

### Export 7: Relatório de Verificação Intermediária (PDF)

**Propósito:** evidência da verificação intermediária do padrão para auditoria.
**Formato:** PDF.
**Campos:** padrão, data, critério aceitação, resultado, executor.

---

### Export 8: Relatório de Participação em Ensaio de Proficiência (anexo PDF)

**Propósito:** relatório do provedor + nossa análise.
**Formato:** PDF (original do provedor + parecer interno).
**Retenção:** ≥ 25 anos.

---

### Export 9: Escopo de Acreditação Vigente (PDF/CSV)

**Propósito:** publicar/disponibilizar escopo vigente.
**Formato:** PDF (exibição) ou CSV (integração).
**Versionado:** cada versão preservada.

---

## Exports inter-módulos

- Snapshot JSON (Export 1) → consumido por **Certificados** (US-CER-001) pra gerar certificado.
- Etiqueta interna (Export 3) → uso interno do lab.
- Documentos auxiliares (Exports 2, 4) → anexados ao certificado pelo módulo Certificados.
- Histórico (Export 5) → portal do cliente (módulo Certificados também serve essa view).
- Ver `../../../comum/integracoes-inter-modulos.md`.

## Versionamento de export regulado

- Motor de cálculo mudou → snapshot preserva versão usada (calibrações antigas não mudam de resultado).
- Mudança no escopo CGCRE → versão nova; auditoria diferencia.

## Como esta lista evolui

- Export novo → adicionar + validar.
- Mudança em formato regulado → ADR + validador.
- Deprecado → `@deprecated`.
