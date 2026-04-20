# compliance/runbooks/executions/ — Evidências de runbooks

Cada subdiretório registra uma execução real ou drill:

```text
<YYYY-MM-DD>-<runbook-id>-<slug>/
```

Conteúdo mínimo:

- `summary.md`
- logs dos comandos executados
- decisões de dispatcher
- responsáveis
- horários de início/fim
- resultado final
- links para incidentes, PRs, ADRs e notificações aplicáveis

Não versionar segredos, chaves privadas, tokens, dumps com dados pessoais ou PDFs completos de cliente final.
