---
owner: roldao
revisado_em: 2026-05-23
proximo_review: 2026-08-23
status: stable
diataxis: reference
audiencia: agente
marco: Wave A Marco 2 — equipamentos
tipo: pip-audit-retroativo
relacionados:
  - docs/seguranca/supply-chain.md
  - docs/faseamento/M2-equipamentos/auditoria-familia5.md
  - pyproject.toml
---

# pip-audit retroativo — Marco 2 `equipamentos`

> **Origem:** MEDIO-1 supplychain identificado pelo `auditor-supplychain`
> na 1ª passada P5 Marco 2 (2026-05-22) — marker `pip-audit:` ausente em
> commits que introduziram as 4 dependências novas Marco 2. Conserto
> retroativo realizado em 2026-05-23 sob INV-RITUAL-001.

## Dependências novas Marco 2

| Pacote | Versão Pin | Finalidade | T-EQP |
|---|---|---|---|
| weasyprint | `^62.3` | Etiqueta PDF (60×40mm) | T-EQP-002 |
| pydyf | `<0.11` | Backend PDF do WeasyPrint (pin obrigatório com 62.x) | T-EQP-002 |
| qrcode[pil] | `^7.4.2` | Renderização PNG base64 do hash QR | T-EQP-002 |
| workalendar | `^17.0.0` | Cálculo SLA em dias úteis BR (feriados móveis) | T-EQP-019 |

## Resultado pip-audit (2026-05-23)

Executado via `docker compose exec app pip-audit --strict`:

| Pacote | Versão | CVE | Aplicabilidade | Resolução |
|---|---|---|---|---|
| **weasyprint** | 62.3 | **CVE-2025-68616** (SSRF via HTTP redirect — CVSS 7.5) | Aplicável em teoria — mitigado em prática pelo template inline | Mitigação aplicada em `services_etiqueta.py`: `url_fetcher` custom recusa qualquer URL não-`data:`; **GATE-EQP-DEP-WEASYPRINT-UPGRADE** Wave A pra upgrade 62→68 (rompe pin pydyf<0.11) |
| pydyf | <0.11 | (nenhum) | — | — |
| qrcode | 7.4.2 | (nenhum) | — | — |
| workalendar | 17.0.0 | (nenhum) | — | — |

### Outros achados (não-Marco 2)

`pip-audit` também listou vulnerabilidades em deps base do container Docker
ou de dev — sem ação Marco 2; rastreadas em `docs/seguranca/supply-chain.md`:

- `pip` 25.0.1 → 4 CVEs (Docker base; sob GATE-DEP-001).
- `poetry` 1.8.3 → 2 CVEs (Docker base; sob GATE-DEP-001).
- `pytest` 8.4.2 → 1 CVE (dev; upgrade pendente Wave A).
- `starlette` 1.0.0 → 1 CVE (dep indireta; upgrade pendente Wave A).

## Mitigação CVE-2025-68616 (WeasyPrint SSRF)

### Vetor

WeasyPrint <68.0 segue redirects HTTP em `default_url_fetcher` sem
re-validar a URL pós-redirect — permite que HTML/CSS com `<img src="ext">`
ou `@import url(...)` exfiltre dados via redirect controlado pelo atacante
até endpoint interno (metadata cloud, localhost:8080/admin, etc.).

### Aplicabilidade no Aferê (Marco 2)

Atualmente o template `equipamentos/etiqueta_qr.html` recebe APENAS:

- `tag`/`numero_serie`/`fabricante`/`modelo`: campos validados anti-PII
  (`validar_localizacao_fisica`/`validar_motivo_detalhe` + escape Django).
- `tenant_nome`: do snapshot `Tenant.nome_fantasia`.
- `qr_png_base64`: PNG embutido inline (data: URI).

Nenhum input controlado por usuário externo chega como URL crua. Vetor
direto **não-explorável** com o template atual.

### Defesa em profundidade (aplicada 2026-05-23)

`services_etiqueta.py:gerar_etiqueta_pdf` agora passa `url_fetcher=_url_fetcher_recusa_tudo`
ao `HTML(...)`. O fetcher:

1. Permite `data:` URIs (necessário pro QR PNG inline).
2. **Recusa qualquer outra URL** (http/https/file/ftp/etc.) com
   `RuntimeError` — impede redirect, fetch externo e ataque SSRF mesmo
   se o template evoluir.

### GATE Wave A

- **GATE-EQP-DEP-WEASYPRINT-UPGRADE**: upgrade WeasyPrint `^62.3 → ^68.0`.
  Bloqueado por pin `pydyf<0.11` (62.x não funciona com pydyf 0.11+).
  Tarefa Wave A: subir minor de ambos (`weasyprint ^68.0` + `pydyf ^0.11`)
  e validar PDF da etiqueta via teste de bytes (`gerar_etiqueta_pdf` produz
  PDF válido, ≥3KB, com marca `%PDF-1.`).

## Marker pip-audit nos commits

A partir de 2026-05-23, todo commit que toca `pyproject.toml`/`poetry.lock`
deve incluir trailer no corpo da mensagem:

```
pip-audit: PASS — <pacote@versão> sem CVE conhecida
```

ou, em caso de CVE aceito com mitigação:

```
pip-audit: <CVE-ID> — mitigado em <arquivo:linha> + GATE Wave A <id>
```

Hook futuro `pip-audit-marker-check` (Wave A) faz cumprimento mecânico.
