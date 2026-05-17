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

# Contratos Export — Módulo Gestão Documental

---

## Exports

### Export 1: Trilha de Auditoria de Documento (CSV)

**Propósito:** Auditor externo precisa de evidência dos acessos a um documento.
**Formato:** CSV (UTF-8 com BOM).
**Regulado?:** parcialmente — atende ISO 9001 4.2.4, ISO 17025 8.4, LGPD art. 37.
**Validador externo:** auditor humano.
**Campos:** `documento_id`, `tenant_id`, `usuario`, `acao`, `timestamp_iso8601`, `ip`, `user_agent`, `versao_id`.
**Assinatura digital:** não no CSV (a planilha em si não); a trilha em si é gravada com hash encadeado conforme `INV-001`.
**Imutabilidade:** trilha origem é imutável (`INV-001`); export é snapshot.
**Retenção:** ver `../../../../conformidade/comum/retencao-matriz.md`.

**Exemplo:**
```csv
documento_id,tenant_id,usuario,acao,timestamp_iso8601,ip,user_agent,versao_id
uuid-1,tenant-A,user@x,visualizou,2026-05-17T10:23:45Z,1.2.3.4,Mozilla/5.0,uuid-v2
```

---

### Export 2: Backup Bundle de Documento (ZIP)

**Propósito:** Exportar documento + todas as versões + trilha + metadados.
**Formato:** ZIP contendo:
- `metadados.json` (todos campos + hashes)
- `versoes/v1.pdf`, `versoes/v2.pdf`, ...
- `trilha.csv`
- `assinaturas.json`

**Regulado?:** não diretamente; serve a portabilidade LGPD (art. 18 V).
**Imutabilidade:** snapshot.

---

### Export 3: Catálogo de Documentos do Tenant (XLSX)

**Propósito:** Visão gerencial — todos os documentos com status, validade, responsável.
**Formato:** XLSX.
**Campos:** id, título, tipo, entidade, status, data_criacao, data_validade, responsavel, tamanho.
**Regulado?:** não.
**Uso:** dashboards gerenciais, reuniões de gestão.

---

### Export 4: Pacote de Resposta LGPD (ZIP)

**Propósito:** Atender solicitação de titular (art. 18 LGPD) — todos os documentos onde aparece dado pessoal do titular.
**Formato:** ZIP.
**Conteúdo:** documentos identificados via busca + relatório de critérios usados + trilha do atendimento.
**Regulado?:** sim — LGPD art. 18.
**Validador:** DPO do tenant aprova antes do envio.
**Retenção:** 5 anos do registro do atendimento.

---

### Export 5: Documento Individual com Selo de Tempo (PDF)

**Propósito:** Versão vigente baixada com selo de tempo embutido (data de emissão + hash).
**Formato:** PDF/A (preferível para arquivamento longo).
**Assinatura digital:** opcional (A3 via Lacuna conforme ADR-0009 quando solicitada).
**Imutabilidade:** PDF gerado é snapshot da versão vigente; alterações exigem nova versão.

---

## Exports inter-módulos

- Trilha de auditoria → módulo `comum/auditoria/` (eventos consolidados).
- Documentos vinculados a OS → módulo `operacao/ordens-servico/` consome listagem via API.
- Documentos de calibração → módulo `metrologia/certificacao/` referencia mas mantém WORM próprio.

## Versionamento de export regulado

Pacote LGPD: schema versionado; mudança na lei → nova versão do template.

## Como esta lista evolui

Export novo → adicionar + validar contra padrão. Mudança regulada → ADR. Descontinuação → `@deprecated`.
