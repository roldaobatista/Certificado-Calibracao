# Finding — Testes de carga, concorrência e caos ausentes

## Status

Aberto.

## Contexto

Não há evidência de testes de carga (k6, Artillery), concorrência de emissão simultânea, caos de infraestrutura (indisponibilidade Redis/Postgres) ou simulação de expiração de sessão/rotação de KMS.

## Impacto

- Comportamento sob pressão desconhecido.
- Risco de corrupção de dados em concorrência (numeração, reemissão).
- Dificuldade para dimensionar infraestrutura.

## Correção recomendada

1. Criar suite de carga para emissão/reemissão (ex: 100 emissões/min).
2. Simular concorrência de numeração e assinatura simultânea.
3. Adicionar testes de caos/failover para Postgres e Redis.
4. Documentar SLIs/SLOs e runbooks de escalonamento.

## Rastreamento

- Área: `evals/`, `compliance/runbooks/`
