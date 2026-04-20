---
id: R3
version: 1
status: active
owner: product-governance
rto: 2h
rpo: "depende do último backup offline"
dispatcher: product-governance
executor: operador de infra + db-schema
---

# R3 — Violação de WORM/object lock

## Trigger

Executar quando um gate ou auditoria detectar storage regulatório sem retenção imutável:

- `pnpm worm-check` falha em IaC;
- smoke pós-deploy detecta bucket sem object lock;
- configuração de provider mostra retenção desabilitada;
- objeto regulatório aparece alterado ou ausente sem evento auditável.

## Impacto

Certificados, checkpoints ou manifests armazenados no intervalo afetado podem ter sido modificados ou removidos. Releases e uploads regulatórios devem congelar até restaurar política imutável e auditar deltas.

## Papéis

- Dispatcher: `product-governance`.
- Executor: operador de infra e `db-schema`.
- Apoio: `lgpd-security` para retenção e incidente; `backend-api` para bloquear uploads; `legal-counsel` se cliente ou órgão regulador precisar ser notificado.

## Passos

1. Congelar pipeline de release e novos uploads regulatórios.
2. Gerar snapshot imediato dos objetos do bucket afetado com path, tamanho, etag e hash.
3. Comparar snapshot com último manifest assinado.
4. Reaplicar Object Lock, Bucket Lock ou Immutable Blob conforme provider.
5. Corrigir IaC para impedir drift recorrente.
6. Rodar `pnpm worm-check`.
7. Auditar objetos divergentes, ausentes ou alterados.
8. Restaurar objetos ausentes a partir de backup offline ou storage frio.
9. Assinar manifest consolidado do estado restaurado.
10. Revalidar amostra de certificados e checkpoints afetados.
11. Retomar releases apenas após validação e aprovação de dispatcher.

## Validação

1. Rodar `pnpm worm-check`.
2. Rodar `pnpm check:all`.
3. Verificar no provider que retenção imutável está ativa.
4. Comparar manifest restaurado com snapshot pós-correção.
5. Validar QR de amostra de certificados do intervalo afetado.

## Evidência

Arquivar em `compliance/runbooks/executions/<YYYY-MM-DD>-r3-worm-object-lock-violation/`:

- `summary.md` com bucket, janela afetada e decisão de retorno;
- snapshot pré-correção e pós-correção;
- saída de `pnpm worm-check`;
- manifest assinado restaurado;
- evidência do provider sem segredos;
- PR de IaC e ADR quando houver mudança de política.

## Drill

- Frequência: semestral.
- Ambiente: staging.
- Cenário: provisionar bucket regulatório sem lock, confirmar falha do gate, restaurar política e gerar evidência.
- Critério de sucesso: detecção em menos de 10 minutos e RTO de 2h respeitado.

## Revisão

Revisar após incidente real, troca de provider, mudança de IaC regulatório ou alteração na política de retenção. Mudança substantiva exige ADR.
