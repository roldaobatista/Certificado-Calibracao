---
owner: roldao
revisado_em: 2026-05-16
status: draft
diataxis: reference
audiencia: agente
relacionados:
  - docs/conformidade/comum/fiscal.md
---

# Contratos de Export — Módulo [NOME] (TEMPLATE)

> Formatos de saída do módulo (PDF, XML, JSON, CSV, planilha). Inclui exports REGULADOS (NF-e, XML INMETRO, certificado RBC) que têm validador externo.

---

## Exports

### Export 1: [Nome do export — ex: "Certificado de Calibração PDF"]

**Propósito:** [1 linha — quem usa, pra quê]
**Formato:** PDF / XML / JSON / CSV / XLSX
**Regulado?:** sim — ISO 17025 cláusula 7.8 / não
**Validador externo:** [URL / ferramenta — ex: validador INMETRO XML]
**Template/Schema:** [path do template ou link pra schema oficial]
**Campos obrigatórios:** [lista citando glossário]
**Campos opcionais:** [lista]
**Assinatura digital:** sim (qual cert) / não
**Imutabilidade pós-emissão:** sim — `INV-NNN` / não
**Retenção:** ver `../../../conformidade/comum/retencao-matriz.md`

**Exemplo:**
```
(snippet do export — sem dado pessoal real)
```

---

### Export 2: ...

(mesmo formato)

---

## Exports inter-módulos

Quando export de um módulo serve de input pra outro:
- [Export A do módulo X] → consumido por [módulo Y] via [API ou arquivo compartilhado].
- Ver `../../../comum/integracoes-inter-modulos.md`.

## Versionamento de export regulado

- Mudança de schema oficial (ex: INMETRO publica nova versão XML) → janela de migração definida pelo regulador.
- Sistema deve suportar versões coexistentes durante janela.

## Como esta lista evolui

- Export novo → adicionar + validar contra schema oficial se regulado.
- Mudança em formato regulado → ADR + atualizar validador.
- Export descontinuado → marcar `@deprecated`.
