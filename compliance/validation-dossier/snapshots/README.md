# Snapshot-Diff Gate

Este diretorio contem os artefatos canonicos do Gate 7.

- `manifest.yaml` declara a politica, os perfis obrigatorios e o hash SHA-256 de cada baseline.
- `baseline/` contem os 30 PDFs canonicos aprovados (10 por perfil A/B/C).
- `current/` contem a saida atual regenerada para comparacao byte-a-byte.

Geracao local:

- `pnpm snapshot-diff:write-current` regenera `current/`.
- `pnpm snapshot-diff:sync` regenera `baseline/`, `current/` e `manifest.yaml`.

Mudanca legitima de baseline exige aprovacao de `regulator` e `product-governance`, com ADR explicando a diferenca metrologica.
