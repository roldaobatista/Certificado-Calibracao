# syntax=docker/dockerfile:1.7

# Aferê apps/api — Dockerfile multi-stage
# Build: pnpm install no root (workspace) + build de contracts, db, api.
# Runtime: imagem slim apenas com dist + node_modules de produção.

# --- base ---------------------------------------------------------------
FROM node:20-alpine AS base
ENV PNPM_HOME=/pnpm
ENV PATH=$PNPM_HOME:$PATH
RUN corepack enable && corepack prepare pnpm@9.15.4 --activate
WORKDIR /repo

# --- deps (instala deps do workspace inteiro) ---------------------------
FROM base AS deps
COPY package.json pnpm-workspace.yaml pnpm-lock.yaml* .npmrc tsconfig.base.json ./
COPY packages/contracts/package.json packages/contracts/
COPY packages/db/package.json packages/db/
COPY apps/api/package.json apps/api/
RUN --mount=type=cache,id=pnpm,target=/pnpm/store \
    pnpm install --frozen-lockfile || pnpm install

# --- build (gera dist e prisma client) ----------------------------------
FROM deps AS build
COPY packages/contracts packages/contracts
COPY packages/db packages/db
COPY apps/api apps/api
RUN pnpm --filter @afere/db run prisma:generate \
 && pnpm --filter @afere/contracts run build \
 && pnpm --filter @afere/db run build \
 && pnpm --filter @afere/api run build
# pruna devDeps para imagem final
RUN pnpm --filter @afere/api deploy --prod /out/api \
 && cp -r packages/db/node_modules/.prisma /out/api/node_modules/.prisma 2>/dev/null || true

# --- runtime ------------------------------------------------------------
FROM node:20-alpine AS runtime
ENV NODE_ENV=production
WORKDIR /app
# Usuário não-root
RUN addgroup -S afere && adduser -S afere -G afere
COPY --from=build --chown=afere:afere /out/api /app
USER afere
EXPOSE 3000
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD node -e "fetch('http://localhost:3000/healthz').then(r => process.exit(r.ok ? 0 : 1)).catch(() => process.exit(1))"
CMD ["node", "dist/server.js"]
