import { PrismaClient } from "@prisma/client";
import { createClient } from "redis";

import type { Env } from "../config/env.js";

export type RuntimeDependencyName = "postgres" | "redis";

export type RuntimeDependencyCheck = {
  ok: boolean;
  reason?: string;
};

export type RuntimeReadinessReport = {
  ok: boolean;
  status: "ok" | "not_ready";
  checks: Record<RuntimeDependencyName, RuntimeDependencyCheck>;
};

export type RuntimeDependencyProbe = {
  name: RuntimeDependencyName;
  check: () => Promise<void>;
};

export type RuntimeReadiness = {
  probes: RuntimeDependencyProbe[];
  close: () => Promise<void>;
};

export type RedisReadinessClient = {
  readonly isOpen: boolean;
  connect: () => Promise<unknown>;
  ping: () => Promise<string>;
  quit: () => Promise<unknown>;
  on: (event: "error", listener: (error: unknown) => void) => unknown;
};

export type PostgresReadinessClient = {
  $queryRawUnsafe: (query: string, ...values: unknown[]) => Promise<unknown>;
};

export class RuntimeReadinessError extends Error {
  readonly dependency: RuntimeDependencyName;
  readonly reason: string;

  constructor(dependency: RuntimeDependencyName, reason: string, cause?: unknown) {
    super(`${dependency}:${reason}`, { cause });
    this.name = "RuntimeReadinessError";
    this.dependency = dependency;
    this.reason = reason;
  }
}

export function createPostgresReadinessProbe(
  prisma: PostgresReadinessClient,
): RuntimeDependencyProbe {
  return {
    name: "postgres",
    async check() {
      try {
        await prisma.$queryRawUnsafe("SELECT 1");
      } catch (error) {
        throw new RuntimeReadinessError("postgres", "query_failed", error);
      }
    },
  };
}

export function createRedisReadinessProbe(redis: RedisReadinessClient): RuntimeDependencyProbe {
  let connectPromise: Promise<void> | null = null;

  const ensureConnected = async () => {
    if (redis.isOpen) return;

    if (!connectPromise) {
      connectPromise = Promise.resolve(redis.connect())
        .then(() => undefined)
        .finally(() => {
          connectPromise = null;
        });
    }

    await connectPromise;
  };

  return {
    name: "redis",
    async check() {
      try {
        await ensureConnected();
        const response = await redis.ping();

        if (response !== "PONG") {
          throw new RuntimeReadinessError("redis", "unexpected_ping_response");
        }
      } catch (error) {
        if (error instanceof RuntimeReadinessError) throw error;
        throw new RuntimeReadinessError("redis", "ping_failed", error);
      }
    },
  };
}

export async function checkRuntimeReadiness(
  probes: RuntimeDependencyProbe[],
): Promise<RuntimeReadinessReport> {
  const checks = Object.fromEntries(
    await Promise.all(
      probes.map(async (probe) => {
        try {
          await probe.check();
          return [probe.name, { ok: true }];
        } catch (error) {
          const reason = error instanceof RuntimeReadinessError
            ? error.reason
            : "unknown_failure";

          return [probe.name, { ok: false, reason }];
        }
      }),
    ),
  ) as Record<RuntimeDependencyName, RuntimeDependencyCheck>;

  const ok = Object.values(checks).every((check) => check.ok);

  return {
    ok,
    status: ok ? "ok" : "not_ready",
    checks,
  };
}

export function createRuntimeReadiness(
  env: Pick<Env, "DATABASE_URL" | "REDIS_URL">,
  options: { onRedisError?: (error: unknown) => void } = {},
): RuntimeReadiness {
  const prisma = new PrismaClient({
    datasources: { db: { url: env.DATABASE_URL } },
    log: [
      { level: "warn", emit: "stdout" },
      { level: "error", emit: "stdout" },
    ],
  });
  const redis = createClient({ url: env.REDIS_URL });

  redis.on("error", (error) => {
    options.onRedisError?.(error);
  });

  return {
    probes: [
      createPostgresReadinessProbe(prisma),
      createRedisReadinessProbe(redis),
    ],
    async close() {
      await prisma.$disconnect();

      if (redis.isOpen) {
        await redis.quit();
      }
    },
  };
}
