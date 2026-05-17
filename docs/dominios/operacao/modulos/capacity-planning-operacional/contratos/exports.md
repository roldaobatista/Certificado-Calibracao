---
owner: Roldão
revisado-em: 2026-05-17
status: draft
modulo: capacity-planning-operacional
dominio: operacao
---

# Contratos Export — Capacity Planning Operacional

## Exports

### Export 1: Painel de Capacidade (PDF)
**Propósito:** apresentar à diretoria / reunião gerencial.
**Formato:** PDF.
**Regulado:** não.
**Template:** `templates/cpo/painel.pdf.j2` (a criar).
**Campos:** capa, KPIs do período, heatmap por equipe, lista de gargalos, indicações de contratação abertas.
**Imutabilidade:** snapshot data de geração.

**Exemplo:**
```
Capacidade Operacional — Semana 22/2026
Ocupação média: 72% | Gargalos: 2 | Sobrecargas: 0
[heatmap]
Indicações: +1 técnico mecânica em 8 semanas
```

---

### Export 2: Plano de Capacidade (XLSX)
**Propósito:** análise detalhada / integração com Excel da diretoria.
**Formato:** XLSX com abas (recursos, capacidade_semanal, ocupacao_semanal, gargalos, previsao_demanda, indicacoes).
**Regulado:** não.
**Campos:** ids, nomes, números brutos sem mascaramento (uso interno).

---

### Export 3: Plano de Contratação (PDF)
**Propósito:** documento formal pra RH/diretoria autorizar contratação.
**Formato:** PDF.
**Campos:** justificativa, FTE sugerido, horizonte, gráfico demanda × capacidade, custo estimado (quando integrado com RH).
**Imutabilidade:** snapshot.

---

### Export 4: CSV de Alocações
**Propósito:** integração com sistemas externos de RH / ponto.
**Formato:** CSV.
**Campos:** recurso, data_inicio, data_fim, os_id, horas, status.

---

### Export 5: Snapshot de Simulação (JSON)
**Propósito:** arquivar simulação aplicada pra auditoria de decisão.
**Formato:** JSON.
**Schema:**
```json
{"simulacao_id":"...","aplicada_em":"...","aplicada_por":"...","mudancas":[...],"resultado_antes":{...},"resultado_depois":{...}}
```
**Imutabilidade:** sim, após aplicada.

---

## Exports inter-módulos

- Indicação de Contratação (Export 3) é consumida por RH/Colaboradores como input de processo seletivo.
- CSV de Alocações é entrada potencial pra Folha/Ponto.

## Versionamento

JSON v1 estável. Mudança quebrante → ADR.
