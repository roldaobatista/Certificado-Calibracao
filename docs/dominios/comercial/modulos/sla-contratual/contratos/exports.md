---
owner: roldao
revisado_em: 2026-05-17
status: draft
diataxis: reference
audiencia: agente
relacionados:
  - docs/conformidade/comum/retencao-matriz.md
---

# Contratos de Export — Módulo SLA Contratual

> Saídas regulamentadas e operacionais. Relatório SLA é contrato com cliente — imutável após emissão.

---

## Exports

### Export 1: Relatório SLA mensal (PDF)

**Propósito:** evidência contratual periódica ao cliente; insumo de QBR e disputa.
**Formato:** PDF/A (longa retenção).
**Regulado?:** não (regulação INMETRO/ISO 17025); contratual sim.
**Validador externo:** N/A (validação por hash SHA-256 + assinatura quando configurada).
**Template/Schema:** `templates/sla/relatorio-sla.v1.html` (a criar pós ADR-0001).
**Campos obrigatórios:** identificação cliente, período, lista de chamados/OS com TR/TS/status, % cumprimento agregado, pausas justificadas com motivo, penalidades/bonificações calculadas, evidências (link/QR), hash do PDF.
**Campos opcionais:** logotipo cliente, observações qualitativas, gráficos de tendência.
**Assinatura digital:** opcional (A3 do responsável, via fluxo `dominios/calibracao/...` reaproveitando porta Signature).
**Imutabilidade pós-emissão:** sim — `INV-*` WORM.
**Retenção:** 5 anos (alinhado a contratos/fiscal); ver `../../../conformidade/comum/retencao-matriz.md`.

**Exemplo (snippet textual):**
```
RELATÓRIO DE SLA — MAIO/2026
Cliente: <razao social> | CNPJ: <...>
Contrato: <numero> | Perfil SLA: Ouro 24/7 v1
Período: 2026-05-01 a 2026-05-31

Resumo:
- Total de incidentes: 42
- SLAs cumpridos: 40 (95,2%)
- SLAs estourados: 2 (4,8%)
- Penalidade calculada: R$ 1.230,00
- Bonificação calculada: R$ 0,00

Detalhamento:
[tabela com chamado, abertura, TR_real, TS_real, status, pausas, evidência]

Hash: sha256:abc123...
Emitido em: 2026-06-01 10:00:00 -03:00
```

---

### Export 2: Trilha de eventos SLA (CSV/JSON)

**Propósito:** auditoria interna / cliente avançado / disputa.
**Formato:** CSV e JSON.
**Regulado?:** não.
**Campos:** evento_id, vinculo_id, referencia (chamado/OS), tipo_evento, timestamp, ator, dados.
**Filtros:** período, cliente, tipo evento.
**Imutabilidade:** export é snapshot; eventos-fonte são WORM.

---

### Export 3: Catálogo de perfis SLA (PDF/CSV)

**Propósito:** anexo a propostas comerciais.
**Formato:** PDF (comercial) + CSV (integração).
**Conteúdo:** perfil, versão, TR/TS, calendário, regras de penalidade/bonificação, motivos de pausa permitidos.

---

### Export 4: Comprovante individual de cumprimento de SLA

**Propósito:** anexar à OS/chamado quando cliente solicita evidência pontual.
**Formato:** PDF de 1 página.
**Conteúdo:** referência incidente, TR/TS configurado vs real, pausas, anexos.
**Hash + assinatura opcional.**

---

## Exports inter-módulos

- `RelatorioSLA` é referenciado por Comunicação Omnichannel no envio.
- Eventos `SLA.PenalidadeCalculada` e `SLA.BonificacaoCalculada` viram lançamentos no Financeiro (não export — integração inter-módulos; ver `../../../comum/integracoes-inter-modulos.md`).

---

## Versionamento de export

- Template do PDF versionado (`v1`, `v2`); relatórios antigos preservam template original (renderização determinística).
- Mudança de template → ADR + janela; nunca afeta hash de relatório já emitido.

---

## Como esta lista evolui

- Export novo → adicionar + (se regulado) validar contra schema oficial.
- Mudança em template → ADR + atualizar pipeline.
- Export descontinuado → `@deprecated`.
