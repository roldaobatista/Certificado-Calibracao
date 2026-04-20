# apps/api — Backend técnico

**Owner:** `backend-api` (P0-1).
- `src/domain/` — regras de negócio, emissão, workflows OS, audit.
- `src/infra/` — persistência, filas, assinatura, QR, sync.
- `src/interfaces/` — HTTP/tRPC/GraphQL.

**Regra dura:** regra de emissão só existe em `src/domain/emission/`. Web/Android consomem via `packages/contracts`.
