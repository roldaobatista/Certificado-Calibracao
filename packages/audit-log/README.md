# packages/audit-log — Trilha imutável

**Co-owners:** `db-schema` + `lgpd-security`. Append-only, hash-chain, WORM checkpoints (Gates 3 e 4 em `harness/05-guardrails.md`).

## Gate 3 — hash-chain verifier

Comando local para artefato JSONL:

```bash
pnpm audit-chain:verify caminho/para/audit.jsonl
```

Formato de cada linha:

```json
{"id":"evt-1","prevHash":"000...000","payload":{"action":"certificate.created"},"hash":"..."}
```

O hash é `sha256(prevHash + canonicalJson(payload))`. Objetos de payload são canonicalizados com chaves ordenadas para manter reprodutibilidade.
