---
owner: Roldão
revisado-em: 2026-05-17
status: draft
modulo: fiscal
dominio: financeiro
---

# Contrato Exports — Fiscal

## Exports

| Export | Formato | Filtros | Audiência |
|---|---|---|---|
| Lista de NFs do período | CSV / XLSX | tipo, status, período, cliente | financeiro |
| XMLs originais (lote) | ZIP | período | financeiro / contador / auditor |
| PDFs DANFSe/DANFE (lote) | ZIP | período | financeiro / cliente |
| Audit fiscal | CSV | período, actor | auditor segurança |
| Numeração / inutilizações | CSV | período | financeiro / contador |
| SPED Fiscal (V2) | TXT | período | contador externo |

## Schema CSV — Lista de NFs

```
tipo,numero,serie,emissao,cliente_nome,cliente_doc,municipio,valor_servico,
codigo_lc116,status,modo,protocolo,cancelada_em,cancelamento_razao
```

UTF-8 BOM, `;`, `,` decimal, `DD/MM/YYYY`.

## Schema CSV — Audit fiscal

```
ts,actor_id,actor_nome,tenant_id,documento_id,acao,
mfa_validado,modo,protocolo,observacao
```

## ZIP de XMLs originais

- Estrutura: `<periodo>/<tipo>/<numero>__<cliente_doc>__<data>.xml`
- Metadata `manifest.json`: hash + status + protocolo + modo
- Hashes preservados (verificável contra WORM)
- Audit log download obrigatório (RAT-08)

## PDF — DANFSe / DANFE

- Layout padrão do município/UF
- Gerado pelo BaaS; Aferê apenas redistribui
- 2ª via via link expira em 72h

## SPED Fiscal (V2 — non-goal MVP-1)

Layout TXT padrão da Receita. Geração assíncrona. Audiência: contador externo.

## Privacidade / LGPD

- NFs contêm CPF/CNPJ + valor → sensíveis (RAT-05)
- Audit log obrigatório de cada download
- Acesso só com papel financeiro+ ou auditor read-only externo (V2)
- Cliente final acessa apenas suas próprias NFs via portal (Wave B)

## Retenção 5 anos (Receita)

- XMLs em WORM (Backblaze B2) — preservação 5 anos
- Verificação periódica de integridade (hash)
- Export de evidência pra auditor fiscal (V2 — acesso controlado)

## Limites

- CSV até 100k linhas síncrono.
- ZIP de XMLs: assíncrono se > 500 NFs; link expira 72h.
- SPED (V2): sempre assíncrono.

## Wave B / V2

- Export pra ERP contábil externo (Domínio/Alterdata/Contabilizei)
- API pra contador externo consumir (com audit reforçado)
- Relatório "evidência pra auditor fiscal" estruturado

## Referências

- `docs/conformidade/comum/fiscal.md`
- `docs/conformidade/comum/retencao-matriz.md`
- `docs/conformidade/comum/lgpd-rat.md` RAT-05, RAT-08
- INV-008
