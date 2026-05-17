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

# Contratos de Export — Módulo Engenharia Técnica

> Formatos de saída. Inclui artefatos potencialmente entregues ao cliente final ou usados em auditoria técnica (ABNT, CREA).

---

## Exports

### Export 1: Memorial Descritivo (PDF)

**Propósito:** documento técnico entregue ao cliente final ou anexado em contrato/projeto.
**Formato:** PDF (template do tenant, com logo, CREA do responsável).
**Regulado?:** parcial — segue norma técnica aplicável (NBR depende do projeto); CREA exige ART em alguns casos (decisão por projeto).
**Validador externo:** não há validador automatizado oficial; revisão é humana (Engenheiro Responsável).
**Template/Schema:** template HTML/CSS do tenant em `docs/dominios/suporte-plataforma/modulos/engenharia-tecnica/templates/memorial.html` (pendente — criar quando UI estiver pronta).
**Campos obrigatórios:** título, código projeto, cliente, data emissão, revisão (letra), engenheiro responsável (nome + CREA), escopo, premissas, soluções, normas aplicáveis, considerações finais, assinatura.
**Campos opcionais:** logo cliente, número ART, anexos referenciados.
**Assinatura digital:** sim — interna (registro nome+CREA+timestamp+IP+hash) OU ICP-Brasil A3 (quando política do tenant exige). Decisão final em ADR de assinatura.
**Imutabilidade pós-emissão:** sim — revisão aprovada é imutável. Re-emissão exige nova revisão (`INV-NNN`).
**Retenção:** mínima 10 anos (alinhada à responsabilidade técnica civil); detalhe em `../../../conformidade/comum/retencao-matriz.md`.

**Exemplo:**
```
MEMORIAL DESCRITIVO — Projeto PRJ-2026-0042 — Revisão B
Cliente: [redigido]
Engenheiro Responsável: [nome] — CREA-SP 1234567
Data: 2026-05-17
...
```

---

### Export 2: Folha de Desenho (PDF anotado)

**Propósito:** desenho técnico renderizado em PDF para impressão/distribuição.
**Formato:** PDF.
**Regulado?:** não diretamente; segue convenções ABNT (formato A0/A1/A2/A3/A4, selo, escalas).
**Conteúdo:** desenho original (rasterizado ou nativo) + selo padrão (código projeto, revisão, escala, data, responsável).
**Assinatura:** mesma da revisão.
**Imutabilidade:** sim.
**Retenção:** mínima 10 anos.

---

### Export 3: BOM (CSV / XLSX)

**Propósito:** consumir lista técnica de materiais em planilha externa OU integrar com Orçamentos/Estoque.
**Formato:** CSV (separador `;`, encoding UTF-8) + XLSX.
**Regulado?:** não.
**Campos:** posição, componente (fabricante/modelo), descrição, quantidade, unidade, ref desenho, observação.
**Versionamento:** schema v1 do CSV documentado.

---

### Export 4: Projeto Completo (ZIP)

**Propósito:** backup, transferência ao cliente, transferência inter-tenant manual.
**Formato:** ZIP contendo:
- `projeto.json` (metadados estruturados).
- `revisoes/<letra>/` (uma pasta por revisão).
- `revisoes/<letra>/memorial.pdf`, `bom.csv`, `especificacoes.json`, `calculos/`, `desenhos/`, `anexos/`.
- `manifest.json` (hash de cada arquivo + assinatura).
**Imutabilidade:** snapshot da revisão.

---

### Export 5: Datasheet do Componente (PDF original do fabricante)

**Propósito:** download do datasheet anexado ao componente da biblioteca.
**Formato:** PDF original.
**Regulado?:** não.

---

### Export 6: Histórico de Alterações (PDF / CSV)

**Propósito:** relatório de auditoria.
**Formato:** PDF (relatório formatado) ou CSV.
**Campos:** timestamp, autor, ação, entidade, motivo, hash referência.

---

## Exports inter-módulos

- **Evento `Engenharia.BOMAtualizada`** → consumido por Orçamentos (atualiza orçamento vinculado) e Estoque (alerta se quantidade nova excede saldo).
- **Evento `Engenharia.RevisaoAprovada`** → consumido por OS (alerta técnico de revisão nova disponível), CRM (cliente pode ser notificado).
- **Memorial PDF** → pode virar anexo de Orçamento ou Contrato (via referência ao Anexo).

Ver `../../../comum/integracoes-inter-modulos.md`.

## Versionamento

- Schema de `projeto.json` e `manifest.json` versionado (`v1`, `v2`).
- Template de memorial PDF versionado por tenant (mudança gera novo template_version; PDFs já emitidos preservam template_version usado).
- Quebra → ADR + janela 6 meses.

## Como esta lista evolui

- Export novo → adicionar + definir schema.
- Mudança em template regulado → ADR.
- Export descontinuado → `@deprecated`.
