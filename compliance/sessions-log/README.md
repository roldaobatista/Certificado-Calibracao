# compliance/sessions-log/ — Log de sessões de agentes

**Owner:** `product-governance` + agente executor da sessão.

Cada sessão relevante deve deixar um handoff para `/resume` em:

```text
compliance/sessions-log/<YYYY-MM-DD>/<tool>-<session-id>.jsonl
```

## Regra de encerramento

Antes de encerrar a sessão, o agente deve registrar:

- branch atual e remoto;
- commits criados e enviados;
- verificações executadas;
- estado de `git status`;
- decisões tomadas;
- limitações honestas;
- próximos passos recomendados, em ordem.

O arquivo é JSONL: uma entrada JSON por linha. Quando não houver ID real de sessão disponível, usar um slug estável como `codex-handoff`.
