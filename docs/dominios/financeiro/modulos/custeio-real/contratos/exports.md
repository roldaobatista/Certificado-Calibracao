---
owner: roldao
revisado_em: 2026-05-17
status: draft
diataxis: reference
audiencia: agente
relacionados:
  - docs/conformidade/comum/fiscal.md
---

# Contratos de Export — Módulo Custeio Real

> Saídas: relatórios, planilhas e payloads pra contabilidade gerencial. Nenhum export REGULADO neste módulo (não emite documento fiscal).

---

## Exports

### Export 1: Apuração detalhada da OS (PDF)

**Propósito:** documento para análise interna ou apresentação a sócio/contador.
**Formato:** PDF.
**Regulado?:** não.
**Template:** `templates/custeio-real/apuracao-os.html` (a criar pós ADR-0001).
**Campos:** número OS, cliente, técnico, datas, receita, tabela previsto×realizado por categoria, margem, observação.
**Imutabilidade:** o PDF é gerado on-demand; conteúdo reflete a VERSÃO ativa da apuração.

---

### Export 2: Ranking de margem por dimensão (CSV/XLSX)

**Propósito:** análise gerencial em planilha externa.
**Formato:** CSV (UTF-8 BOM) e XLSX.
**Campos:** dimensão (cliente/técnico/vendedor/serviço), nome, receita período, custo total, margem R$, margem %, count OS, count deficitárias, % retrabalho (quando aplicável), % garantia (quando aplicável).
**Filtros:** dimensão, período.
**RBAC:** ranking por técnico/vendedor exige `gestor_operacional`/`dono`.

---

### Export 3: Lista de OSs deficitárias (CSV/XLSX)

**Propósito:** input para reunião de revisão operacional.
**Campos:** OS, cliente, técnico, vendedor, tipo serviço, receita, custo, margem R$, margem %, encerrada em, status alerta.

---

### Export 4: Comparativo previsto × realizado por categoria (XLSX)

**Propósito:** acompanhar estouros e calibrar orçamentos.
**Formato:** XLSX (uma aba por categoria de custo).
**Campos:** OS, cliente, previsto, realizado, variação R$, variação %.

---

### Export 5: Payload para contabilidade gerencial (JSON)

**Propósito:** consumo por módulo de contabilidade (quando existir) ou ferramenta externa do contador.
**Formato:** JSON.
**Schema:** por OS, com linhas de custo categorizadas.
**Disparo:** sob demanda ou periódico (configurável).

---

### Export 6: Trilha de mudanças em parâmetros de custeio (CSV)

**Propósito:** auditoria interna de quem mudou hora-base, custo/km, threshold.
**Campos:** quando, quem, chave, escopo, de_valor, para_valor, motivo.
**Origem:** log de auditoria.
**Retenção:** alinhada com matriz LGPD/Receita em `docs/conformidade/comum/retencao-matriz.md`.

---

## Exports inter-módulos

- `CusteioReal.CustoApurado` → contabilidade gerencial (quando existir), dashboards.
- `CusteioReal.AlertaDeficitarioCriado` → notificações (push/email/in-app gestor).
- Ver `../../../comum/integracoes-inter-modulos.md`.

## Versionamento de export regulado

Não aplicável — módulo não emite documento regulado.

## Como esta lista evolui

- Export novo → adicionar + ligar a US se houver.
- Dimensão nova em rankings → atualizar Export 2.
