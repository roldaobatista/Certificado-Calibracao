---
owner: Roldão
revisado-em: 2026-05-17
status: draft
modulo: caixa-tecnico
dominio: financeiro
---

# Contrato Exports — Caixa do Técnico

## Exports

| Export | Formato | Filtros | Audiência |
|---|---|---|---|
| Prestação de contas individual | PDF / XLSX | técnico + período | técnico / financeiro |
| Despesas do período (lote) | CSV / XLSX | período, técnico, categoria | financeiro |
| Despesas por OS | CSV | OS_id | financeiro / dono (custeio) |
| Despesas por categoria | CSV / PDF | período | dono |
| Fotos-comprovante (lote) | ZIP de imagens | período, técnico | financeiro / auditor |

## Schema CSV — Despesas do período

```
data,tecnico_nome,categoria,valor,os_numero,descricao,
status,validada_por,validada_em,gps_lat,gps_lng
```

UTF-8 BOM, `;`, `,` decimal.

## Schema CSV — Adiantamentos

```
data_solicitacao,tecnico,valor,motivo,os_referencia,
aprovado_por,entregue_em,meio
```

## PDF — Prestação de contas individual (layout)

- Cabeçalho: tenant + técnico + período + saldo final
- Bloco "Adiantamentos": lista com data + valor + meio
- Bloco "Despesas validadas": agrupada por categoria, com OS quando vinculada
- Total adiantado − total despesas = saldo
- Direção: "Você devolve R$ X" ou "Empresa reembolsa R$ Y"
- Assinatura técnico + financeiro (campo)
- Hash de autenticação + QR (V2)

## ZIP de fotos

- Estrutura: `<periodo>/<tecnico>/<despesa_id>__<categoria>__<data>.jpg`
- Metadata em `manifest.json` (valor, categoria, OS, hash, status)
- Audit log do download obrigatório (RAT-08 análogo — LGPD)
- Acesso só financeiro/dono/auditor com papel apropriado

## Privacidade / LGPD

- Despesas + GPS = dados pessoais do técnico + comportamentais.
- Bases legais: execução de contrato de trabalho.
- Consentimento explícito pra GPS.
- Retenção: 5 anos fiscal (`retencao-matriz.md`).
- Direito de acesso do técnico aos próprios dados.

## Wave B / V2

- Export pra folha de pagamento (V2)
- Integração com custeio OS (relatório margem OS) — Wave B
- Export pra Receita (eventual auditoria) — V2

## Limites

- PDF prestação individual: síncrono.
- ZIP fotos: assíncrono (job + link com expiração 72h).
- CSV até 100k linhas síncrono.

## Referências

- `docs/conformidade/comum/retencao-matriz.md`
- `docs/conformidade/comum/lgpd-rat.md`
- INV-008
