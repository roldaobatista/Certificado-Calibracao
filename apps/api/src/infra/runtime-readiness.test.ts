import assert from "node:assert/strict";
import { test } from "node:test";

import {
  RuntimeReadinessError,
  checkRuntimeReadiness,
  createPostgresReadinessProbe,
  createRedisReadinessProbe,
  type PostgresReadinessClient,
  type RedisReadinessClient,
  type RuntimeDependencyProbe,
} from "./runtime-readiness.js";

test("reports runtime as ready when all dependency probes succeed", async () => {
  const report = await checkRuntimeReadiness([
    createOkProbe("postgres"),
    createOkProbe("redis"),
  ]);

  assert.deepEqual(report, {
    ok: true,
    status: "ok",
    checks: {
      postgres: { ok: true },
      redis: { ok: true },
    },
  });
});

test("reports dependency-specific readiness failures without masking healthy dependencies", async () => {
  const report = await checkRuntimeReadiness([
    createFailingProbe("postgres", "query_failed"),
    createOkProbe("redis"),
  ]);

  assert.deepEqual(report, {
    ok: false,
    status: "not_ready",
    checks: {
      postgres: { ok: false, reason: "query_failed" },
      redis: { ok: true },
    },
  });
});

test("postgres readiness probe executes a real ping query through Prisma", async () => {
  const executedQueries: string[] = [];
  const probe = createPostgresReadinessProbe({
    async $queryRawUnsafe(query: string) {
      executedQueries.push(query);
      return [{ value: 1 }];
    },
  } satisfies PostgresReadinessClient);

  await probe.check();

  assert.deepEqual(executedQueries, ["SELECT 1"]);
});

test("redis readiness probe connects lazily, reuses the open connection and requires PONG", async () => {
  let isOpen = false;
  let connectCalls = 0;
  let pingCalls = 0;

  const redis: RedisReadinessClient = {
    get isOpen() {
      return isOpen;
    },
    async connect() {
      connectCalls += 1;
      isOpen = true;
    },
    async ping() {
      pingCalls += 1;
      return "PONG";
    },
    async quit() {
      isOpen = false;
    },
    on() {
      return undefined;
    },
  };

  const probe = createRedisReadinessProbe(redis);

  await probe.check();
  await probe.check();

  assert.equal(connectCalls, 1);
  assert.equal(pingCalls, 2);
});

test("redis readiness probe fails closed when ping does not return PONG", async () => {
  const redis: RedisReadinessClient = {
    get isOpen() {
      return true;
    },
    async connect() {
      return undefined;
    },
    async ping() {
      return "NOPE";
    },
    async quit() {
      return undefined;
    },
    on() {
      return undefined;
    },
  };

  const probe = createRedisReadinessProbe(redis);

  await assert.rejects(
    () => probe.check(),
    (error: unknown) =>
      error instanceof RuntimeReadinessError &&
      error.dependency === "redis" &&
      error.reason === "unexpected_ping_response",
  );
});

function createOkProbe(name: "postgres" | "redis"): RuntimeDependencyProbe {
  return {
    name,
    async check() {
      return undefined;
    },
  };
}

function createFailingProbe(
  name: "postgres" | "redis",
  reason: string,
): RuntimeDependencyProbe {
  return {
    name,
    async check() {
      throw new RuntimeReadinessError(name, reason);
    },
  };
}
