# Flake Log

Registro canônico de falhas intermitentes detectadas pelo flake gate noturno.

Cada execução com falha deve criar `YYYY-MM-DD.yaml` neste diretório contendo:

- suite afetada;
- run entre 1 e 10;
- comando executado;
- classificação `flake` ou `infra`;
- owner responsável;
- issue ou PR de correção;
- evidência arquivada no dossiê quando aplicável.

Falha em área `blocker` bloqueia release até investigação registrada.
