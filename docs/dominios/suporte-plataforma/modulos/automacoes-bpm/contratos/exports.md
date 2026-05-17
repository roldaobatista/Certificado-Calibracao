---
owner: roldao
revisado_em: 2026-05-17
status: draft
diataxis: reference
audiencia: agente
relacionados:
  - docs/conformidade/comum/fiscal.md
---

# Contratos de Export — Módulo Automações & BPM

> Formatos de saída do módulo. Nenhum export deste módulo é regulado por norma externa (LGPD/ISO/INMETRO/Receita) — todos são internos ou de relatório operacional.

---

## Exports

### Export 1: Definição de Fluxo (YAML/JSON)

**Propósito:** backup, versionamento externo, transferência entre tenants (manual).
**Formato:** YAML (preferencial) + JSON (alternativo).
**Regulado?:** não.
**Validador externo:** não.
**Template/Schema:** schema interno (a publicar em `docs/comum/schemas/fluxo-v1.yaml`).
**Campos obrigatórios:** `nome`, `descricao`, `etapas[]`, `transicoes[]`, `versao`.
**Assinatura digital:** não.
**Imutabilidade:** o export é snapshot da versão publicada — imutável por definição.
**Retenção:** segue retenção do tenant (`../../../conformidade/comum/retencao-matriz.md`).

**Exemplo:**
```yaml
nome: Aprovação Orçamento Desconto Alto
versao: 3
modo: ativo
etapas:
  - id: e1
    tipo: inicio
  - id: e2
    tipo: decisao_humana
    sla_horas: 24
    responsavel:
      tipo: grupo
      id: gerentes-comerciais
transicoes:
  - de: e1
    para: e2
    condicao: "payload.desconto > 0.15"
```

---

### Export 2: Definição de Regra (YAML/JSON)

**Propósito:** análogo a Fluxo.
**Formato:** YAML/JSON.
**Campos obrigatórios:** `evento`, `condicao`, `acao`, `modo`, `versao`.

---

### Export 3: Relatório de Aprovações (PDF/CSV)

**Propósito:** relatório operacional gerencial; auditoria interna.
**Formato:** PDF (impressão) + CSV (análise).
**Regulado?:** não, mas pode ser usado em auditoria interna do tenant.
**Campos:** período, fluxo, instância, pendência, aprovador efetivo, decisão, comentário, SLA cumprido (S/N).

---

### Export 4: Log de Execuções (CSV / JSON Lines)

**Propósito:** análise externa (Excel, BI), troubleshooting offline.
**Formato:** CSV (1 linha por execução) + JSON Lines (com payload completo).
**Campos:** timestamp, regra_id, versao_regra, payload_entrada, condicao_resultado, acao_resultado, erro, reprocessamento_de.

---

### Export 5: Catálogo (JSON)

**Propósito:** consumo por agentes/scripts externos (documentação automática).
**Formato:** JSON.
**Endpoints:** eventos, condições, ações pré-aprovadas.

---

## Exports inter-módulos

- **Evento `BPM.AprovacaoConcedida`** → consumido por Orçamentos, OS, NF, Contratos. Não é "export" em arquivo, mas é saída inter-módulo via barramento. Ver `../../../comum/integracoes-inter-modulos.md`.
- **Log de execução** → consumido por módulo de Auditoria (Família 5) em batch noturno.

## Versionamento

- Schema de YAML/JSON de fluxo/regra versionado (`v1`, `v2`).
- Quebra de schema exige ADR + script de migração + janela de 6 meses suportando ambos.

## Como esta lista evolui

- Export novo → adicionar + validar schema interno.
- Mudança em schema → ADR + script de migração.
- Export descontinuado → `@deprecated`.
