---
owner: Roldão
revisado-em: 2026-05-17
proximo_review: 2026-08-17
status: draft
diataxis: reference
audiencia: agente
modulo: projetos
dominio: operacao
relacionados:
  - docs/conformidade/comum/fiscal.md
---

# Contratos de Export — Módulo Gestão de Projetos

> Formatos de saída. Nenhum export é regulado fiscal (Fiscal/Financeiro cuida).

---

## Exports

### Export 1: Cronograma do Projeto (PDF)

**Propósito:** apresentação ao cliente / arquivo do projeto.
**Formato:** PDF (PDF/UA — `INV-016`).
**Regulado?:** não.
**Validador:** validador interno PDF/UA.
**Template:** `templates/projetos/cronograma.html` (a criar).
**Campos obrigatórios:** projeto (código, nome, cliente, responsável, datas), etapas (ordem, nome, datas previstas, datas reais, % concluído), marcos, aditivos consolidados.
**Assinatura digital:** opcional (carimbo do tempo).
**Imutável:** snapshot — toda emissão gera nova versão.
**Retenção:** ver `../../../conformidade/comum/retencao-matriz.md`.

---

### Export 2: Relatório Financeiro do Projeto (XLSX)

**Propósito:** análise interna previsto vs realizado.
**Formato:** XLSX.
**Campos:** projeto, categoria, descrição, valor_previsto, valor_realizado, % consumido, margem.
**Abas:** Resumo, Por etapa, Por categoria, Detalhe (linha por OS/Compra/Estoque).
**Assinatura:** não.
**Imutável:** não — replicável on-demand.

---

### Export 3: Aceite de Etapa (PDF)

**Propósito:** documento legal de aceite formal.
**Formato:** PDF/UA.
**Regulado?:** não (boa prática contratual).
**Campos obrigatórios:** projeto, etapa, descrição entregue, representante do cliente (nome+CPF), data, observações, assinatura+timestamp (quando aplicável), hash.
**Assinatura digital:** quando disponível, A1/A3 via Lacuna (`INV-017` análogo).
**Imutável pós-emissão:** sim (`INV-001`).
**Retenção:** 5 anos mínimos (CDC + defesa contratual).

**Exemplo (snippet):**
```
TERMO DE ACEITE — Etapa 3 de 5
Projeto: PRJ-2026-001 — Instalação Balança Rodoviária Fazenda X
Cliente: ACME Agro S.A.  |  Representante: João da Silva (CPF ***.***.***-)
Data: 2026-07-15
Entregue: estrutura mecânica + plataforma de pesagem instalada
Hash: sha256:abc...
```

---

### Export 4: Diário de Execução Consolidado (PDF)

**Propósito:** evidência cronológica.
**Formato:** PDF.
**Campos:** projeto + todas entradas do diário em ordem cronológica + anexos referenciados.
**Imutável:** snapshot a cada emissão.
**Retenção:** acompanha retenção do projeto.

---

### Export 5: Matriz de Risco (XLSX)

**Propósito:** análise de risco do portfolio ou projeto.
**Campos:** risco, descrição, probabilidade, impacto, nível, plano_mitigacao, responsável, prazo, status.
**Imutável:** não.

---

### Export 6: Contrato Consolidado com Aditivos (PDF)

**Propósito:** mostrar contrato original + aditivos somados em documento único.
**Formato:** PDF/UA.
**Campos:** contrato original + cada aditivo aprovado (versão, motivo, alteração, data, aprovador) + totais atualizados.
**Assinatura digital:** quando contrato base assinado, exportar com selo.
**Imutável:** snapshot por versão.
**Retenção:** 5 anos mínimos.

---

## Exports inter-módulos

- Aceite (Export 3) → consumido pelo Financeiro pra liberar emissão de NF da etapa.
- Cronograma (Export 1) e Contrato Consolidado (Export 6) → consumidos pelo Portal-do-Cliente.
- Relatório Financeiro (Export 2) → consumido pelo módulo Financeiro pra DRE por projeto.

Ver `../../../comum/integracoes-inter-modulos.md`.

## Versionamento

Templates versionados; mudança em layout do Aceite ou Contrato Consolidado → ADR (impacto legal).

## Como evolui

Export novo → adicionar + validar PDF/UA quando documento legal.
