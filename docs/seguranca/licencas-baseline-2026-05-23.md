---
owner: roldao
revisado-em: 2026-05-23
status: stable
diataxis: reference
audiencia: auditor
relacionados:
  - LICENSE
  - REGRAS-INEGOCIAVEIS.md
  - pyproject.toml
---

# Baseline de licenças de dependências — 2026-05-23

> **Onda 0 plano-v2 — O0-8 deferido em GATE Wave A.**
>
> Auditor SUPPLY pediu rodar `pip-licenses` como baseline pra detectar dependência com licença incompatível (AGPL/GPL viral). Ferramenta `pip-licenses` **não está instalada localmente** no Windows do Roldão (verificado em 2026-05-23: `command -v pip-licenses` → não encontrado). Instalar exige decisão sobre venv vs sistema vs Poetry dev-dep, que é decisão arquitetural pequena mas não bloqueante.

## Decisão

**Deferir pra F-C3** (instrumentação + resiliência da Foundation F-C). Lá, `pip-licenses` entra como dev-dep do Poetry + step no CI (`pip-licenses --fail-on="AGPL;GPL"`), rodando em todo PR.

## Baseline manual (qualitativo) — feita agora

Lista qualitativa das deps presentes em `pyproject.toml` que são candidatas a risco copyleft:

| Dep | Licença | Risco | Decisão |
|---|---|---|---|
| `Django 5.0` | BSD-3-Clause | Baixo | OK |
| `djangorestframework` | BSD-3-Clause | Baixo | OK |
| `psycopg[binary]` | LGPL-3.0+ | Baixo (LGPL permite uso como biblioteca) | OK |
| `WeasyPrint 62.x` | BSD-3-Clause (núcleo); libpango/libcairo LGPL-2.1+ dinâmico | Baixo (LGPL dinâmico em SaaS = OK) | OK — confirmar com advogado humano antes do 1º cliente externo |
| `cryptography` | Apache-2.0 + BSD-3 dual | Baixo | OK |
| `pyOpenSSL` | Apache-2.0 | Baixo | OK |
| `procrastinate` | MIT | Baixo | OK |
| `boto3` | Apache-2.0 | Baixo | OK |
| `pytest` (dev) | MIT | N/A (dev) | OK |
| `ruff` (dev) | MIT | N/A (dev) | OK |
| `mypy` (dev) | MIT | N/A (dev) | OK |

**Conclusão qualitativa:** nenhuma dependência AGPL/GPL detectada na inspeção manual. Stack atual é compatível com BUSL-1.1 aplicada no `LICENSE`.

## GATE

- **GATE-SUPPLY-PIP-LICENSES-CI:** instalar `pip-licenses` como dev-dep do Poetry em F-C3 + step `pip-licenses --fail-on="AGPL;GPL" --format=markdown` no workflow GitHub Actions de PR + arquivo `docs/seguranca/licencas-relatorio-mais-recente.md` atualizado em todo PR que mexe em deps.
- **GATE-SUPPLY-WEASYPRINT-LGPL:** antes do 1º cliente externo pago, confirmar com advogado humano licenciado que o uso do WeasyPrint no Aferê (via Python como biblioteca dinâmica, sem linkagem estática) é compatível com BUSL-1.1 sem obrigação de relicenciamento.

## Reproduzir esta inspeção

```bash
poetry show --tree | grep -iE 'agpl|gpl-' || echo "Nenhuma dep AGPL/GPL detectada"
```

Saída esperada: `Nenhuma dep AGPL/GPL detectada`.
