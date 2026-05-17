---
owner: roldao
revisado_em: 2026-05-17
status: draft
diataxis: reference
audiencia: agente
relacionados:
  - docs/conformidade/comum/fiscal.md
  - docs/conformidade/comum/retencao-matriz.md
  - docs/conformidade/comum/lgpd-rat.md
---

# Contratos de Export — Módulo Relatórios Financeiros

> Toda visão analítica é exportável. Anonimização de dados pessoais segue RBAC do solicitante.

---

## Exports

### Export 1: DRE gerencial (PDF / XLSX / CSV)

**Propósito:** gestor/dono envia ao sócio, banco, contador.
**Formato:** PDF (apresentação) / XLSX (manipulação) / CSV (integração).
**Regulado?:** não (não substitui DRE contábil oficial).
**Validador externo:** —
**Template:** `templates/relatorios/dre.html` (a criar quando F-A começar).
**Campos obrigatórios:** período, tenant, linhas do DRE (chave, descrição, valor), totalizadores, comparativo (se solicitado).
**Campos opcionais:** anotações, marca d'água "GERENCIAL — NÃO CONTÁBIL".
**Assinatura digital:** não.
**Imutabilidade pós-emissão:** não.
**Retenção:** 5 anos (uso interno).

---

### Export 2: Fluxo de caixa (realizado e projetado) (PDF / XLSX / CSV)

**Propósito:** apresentação de caixa para banco/sócio.
**Formato:** PDF / XLSX / CSV.
**Regulado?:** não.
**Campos obrigatórios:** período, série temporal (data, entradas, saídas, saldo), totalizadores. Projetado inclui flag "PROJEÇÃO".
**Assinatura digital:** não.
**Imutabilidade:** não.
**Retenção:** 5 anos.

---

### Export 3: Aging (PDF / XLSX / CSV)

**Propósito:** cobrança e renegociação.
**Formato:** PDF / XLSX / CSV.
**Regulado?:** não.
**Campos obrigatórios:** data-base, faixas, totais, detalhamento por cliente/fornecedor (quando RBAC permite).
**LGPD:** export agregado anonimiza CPF/CNPJ se solicitante não tem permissão de detalhe.

---

### Export 4: Centro de custo / Receitas e despesas / Resultado por dimensão (PDF / XLSX / CSV)

**Propósito:** análise gerencial.
**Formato:** PDF / XLSX / CSV.
**Regulado?:** não.
**Campos obrigatórios:** dimensão, valores, % do total, variação, totalizador.
**LGPD:** resultado por cliente — anonimização condicional (`SEC-LGPD-005`).

---

### Export 5: Pacote mensal para contador (ZIP)

**Propósito:** entregar mensalmente ao contador externo um conjunto fechado.
**Formato:** ZIP contendo: DRE (PDF + XLSX), fluxo realizado (XLSX), aging (XLSX), conciliações do mês (PDF), planilha de receitas/despesas por categoria (XLSX).
**Regulado?:** não substitui SPED; complementa.
**Assinatura digital:** opcional (assinatura A3 do responsável, ver ADR-0009).
**Imutabilidade pós-envio:** sim — versão enviada fica registrada em trilha WORM (`INV-001`).
**Retenção:** 5 anos + 90 dias (alinhado à matriz `docs/conformidade/comum/retencao-matriz.md` — base Receita CTN art. 173).

---

### Export 6: Conciliação concluída (PDF auditável)

**Propósito:** comprovar conciliação bancária de um período para auditor/contador.
**Formato:** PDF.
**Regulado?:** parcial — usado em auditoria.
**Campos obrigatórios:** conta bancária, período, hash do extrato original, totais conciliados, divergências resolvidas com motivo + autor + timestamp.
**Assinatura digital:** opcional A3 do responsável.
**Imutabilidade:** sim — `INV-001` (audit WORM).
**Retenção:** 5 anos + 90 dias (alinhado à matriz `docs/conformidade/comum/retencao-matriz.md`).

---

## Exports inter-módulos

- DRE/Fluxo/Aging exportados são fonte para apresentações fora do sistema; não há módulo interno consumindo arquivo.
- Pacote mensal pode ser arquivado pelo módulo `Documentos` (quando existir) com referência ao período.

Ver `../../../comum/integracoes-inter-modulos.md`.

## Versionamento de export regulado

- Para o pacote mensal, mudanças no conjunto de arquivos exigem ADR (contador externo pode estar acostumado).
- Layout dos PDFs pode evoluir; CHANGELOG seção "Modificado".

## Como esta lista evolui

- Export novo → adicionar.
- Mudança em formato → ADR se afetar integração externa.
- `@deprecated` → janela de migração 3 meses.
