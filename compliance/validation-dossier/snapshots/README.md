# Snapshot-Diff Gate

Este diretorio contem os artefatos canonicos do Gate 7.

- `manifest.yaml` declara a politica, os perfis obrigatorios e o hash SHA-256 de cada baseline.
- `baseline/` contem o snapshot aprovado.
- `current/` contem a saida atual regenerada para comparacao byte-a-byte.

Mudanca legitima de baseline exige aprovacao de `regulator` e `product-governance`, com ADR explicando a diferenca metrologica.
