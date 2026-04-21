import assert from "node:assert/strict";
import { test } from "node:test";

import type { Env } from "./config/env.js";
import { RuntimeReadinessError, type RuntimeReadiness } from "./infra/runtime-readiness.js";
import { buildApp } from "./app.js";

const TEST_ENV: Env = {
  NODE_ENV: "test",
  LOG_LEVEL: "fatal",
  HOST: "127.0.0.1",
  PORT: 3000,
  CORS_ORIGINS: [],
  DATABASE_URL: "postgresql://afere:afere@localhost:5432/afere?schema=public",
  REDIS_URL: "redis://localhost:6379",
};

test("keeps /healthz as process liveness even when runtime dependencies are not ready", async () => {
  const { runtimeReadiness } = createRuntimeReadinessStub({ postgresReason: "query_failed" });
  const app = await buildApp({ env: TEST_ENV, runtimeReadiness });

  try {
    const response = await app.inject({ method: "GET", url: "/healthz" });
    const payload = response.json() as Record<string, string>;
    const timestamp = payload.ts;

    assert.equal(response.statusCode, 200);
    assert.equal(payload.status, "ok");
    assert.equal(payload.version, "0.0.1");
    assert.equal(typeof timestamp, "string");
    assert.ok(timestamp);
    assert.match(timestamp, /^\d{4}-\d{2}-\d{2}T/);
  } finally {
    await app.close();
  }
});

test("returns 200 on /readyz only when Postgres and Redis checks succeed", async () => {
  const { runtimeReadiness, wasClosed } = createRuntimeReadinessStub();
  const app = await buildApp({ env: TEST_ENV, runtimeReadiness });

  try {
    const response = await app.inject({ method: "GET", url: "/readyz" });

    assert.equal(response.statusCode, 200);
    assert.deepEqual(response.json(), {
      ok: true,
      status: "ok",
      checks: {
        postgres: { ok: true },
        redis: { ok: true },
      },
    });
  } finally {
    await app.close();
  }

  assert.equal(wasClosed(), true);
});

test("returns 503 on /readyz when any runtime dependency fails closed", async () => {
  const { runtimeReadiness } = createRuntimeReadinessStub({ redisReason: "ping_failed" });
  const app = await buildApp({ env: TEST_ENV, runtimeReadiness });

  try {
    const response = await app.inject({ method: "GET", url: "/readyz" });

    assert.equal(response.statusCode, 503);
    assert.deepEqual(response.json(), {
      ok: false,
      status: "not_ready",
      checks: {
        postgres: { ok: true },
        redis: { ok: false, reason: "ping_failed" },
      },
    });
  } finally {
    await app.close();
  }
});

function createRuntimeReadinessStub(options: {
  postgresReason?: string;
  redisReason?: string;
} = {}): { runtimeReadiness: RuntimeReadiness; wasClosed: () => boolean } {
  let closed = false;

  return {
    runtimeReadiness: {
      probes: [
        {
          name: "postgres",
          async check() {
            if (options.postgresReason) {
              throw new RuntimeReadinessError("postgres", options.postgresReason);
            }
          },
        },
        {
          name: "redis",
          async check() {
            if (options.redisReason) {
              throw new RuntimeReadinessError("redis", options.redisReason);
            }
          },
        },
      ],
      async close() {
        closed = true;
      },
    },
    wasClosed: () => closed,
  };
}
