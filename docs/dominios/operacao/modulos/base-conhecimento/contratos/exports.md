---
owner: Roldão
revisado-em: 2026-05-17
status: draft
modulo: base-conhecimento
dominio: operacao
---

# Contratos Export — Base de Conhecimento

## Exports

### Export 1: Artigo em PDF
**Propósito:** leitor imprimir/anexar artigo em laudo interno.
**Formato:** PDF/A.
**Regulado:** não.
**Validador externo:** —
**Template:** `templates/bcn/artigo.pdf.j2` (a criar).
**Campos obrigatórios:** título, autor, versão, aprovador, data publicação, normas, corpo, anexos linkados.
**Assinatura digital:** opcional (config tenant).
**Imutabilidade:** sim — refere versão snapshot.
**Retenção:** ver `../../../conformidade/comum/retencao-matriz.md`.

**Exemplo:**
```
[Cabeçalho tenant]
Artigo #BCN-2026-00123 — versão 3 — publicado 2026-04-10
Aprovado por: <Responsável Técnico>
Normas: ISO 17025 7.7
Corpo: ...
```

---

### Export 2: Pacote da Base (CSV/XLSX)
**Propósito:** auditoria interna, migração entre tenants.
**Formato:** XLSX com abas (artigos, versões, aprovações, votos).
**Regulado:** não.
**Campos:** ids, títulos, status, contagens, datas.
**Limitação:** anexos não incluídos (links apenas).

---

### Export 3: Snapshot de Versão (JSON)
**Propósito:** integração com sistemas externos (intranet, portal cliente futuro).
**Formato:** JSON.
**Schema:**
```json
{"artigo_id":"...","versao":N,"titulo":"...","corpo_md":"...","categoria":{...},"publicado_em":"...","aprovador":"...","anexos":[{"url":"...","mime":"..."}]}
```
**Imutabilidade:** sim.

---

### Export 4: Relatório de Cobertura (PDF)
**Propósito:** gerência verifica equipamentos sem artigo.
**Formato:** PDF.
**Conteúdo:** tabela equipamento × nº artigos × idade última revisão; gráfico cobertura por marca.

---

## Exports inter-módulos

- Export 3 (Snapshot) é consumido por Chamados/OS pra anexar artigo aplicado ao histórico.
- Sugestões aceitas geram registro em Métricas (módulo Comum).

## Versionamento

Schema JSON v1. Mudança não-retrocompatível exige ADR.
