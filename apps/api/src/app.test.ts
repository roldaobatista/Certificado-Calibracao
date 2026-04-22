import assert from "node:assert/strict";
import { test } from "node:test";

import {
  certificatePreviewCatalogSchema,
  emissionDryRunCatalogSchema,
  emissionWorkspaceCatalogSchema,
  onboardingCatalogSchema,
  publicCertificateCatalogSchema,
  reviewSignatureCatalogSchema,
  selfSignupCatalogSchema,
  signatureQueueCatalogSchema,
  userDirectoryCatalogSchema,
} from "@afere/contracts";

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

test("serves the canonical emission dry-run catalog from the backend", async () => {
  const { runtimeReadiness } = createRuntimeReadinessStub();
  const app = await buildApp({ env: TEST_ENV, runtimeReadiness });

  try {
    const response = await app.inject({
      method: "GET",
      url: "/emission/dry-run?scenario=type-c-blocked",
    });

    assert.equal(response.statusCode, 200);

    const payload = emissionDryRunCatalogSchema.parse(response.json());
    const blockedScenario = payload.scenarios.find((scenario) => scenario.id === "type-c-blocked");

    assert.equal(payload.selectedScenarioId, "type-c-blocked");
    assert.equal(payload.scenarios.length, 3);
    assert.ok(blockedScenario);
    assert.equal(blockedScenario.result.status, "blocked");
    assert.equal(
      blockedScenario.result.checks.filter((check) => check.status === "failed").length,
      5,
    );
  } finally {
    await app.close();
  }
});

test("serves the canonical certificate preview catalog from the backend", async () => {
  const { runtimeReadiness } = createRuntimeReadinessStub();
  const app = await buildApp({ env: TEST_ENV, runtimeReadiness });

  try {
    const response = await app.inject({
      method: "GET",
      url: "/emission/certificate-preview?scenario=type-c-blocked",
    });

    assert.equal(response.statusCode, 200);

    const payload = certificatePreviewCatalogSchema.parse(response.json());
    const blockedScenario = payload.scenarios.find((scenario) => scenario.id === "type-c-blocked");

    assert.equal(payload.selectedScenarioId, "type-c-blocked");
    assert.equal(payload.scenarios.length, 3);
    assert.ok(blockedScenario);
    assert.equal(blockedScenario.result.status, "blocked");
    assert.equal(blockedScenario.result.suggestedReturnStep, 2);
    assert.equal(blockedScenario.result.sections.length, 8);
  } finally {
    await app.close();
  }
});

test("serves the canonical emission workspace catalog from the backend", async () => {
  const { runtimeReadiness } = createRuntimeReadinessStub();
  const app = await buildApp({ env: TEST_ENV, runtimeReadiness });

  try {
    const response = await app.inject({
      method: "GET",
      url: "/emission/workspace?scenario=release-blocked",
    });

    assert.equal(response.statusCode, 200);

    const payload = emissionWorkspaceCatalogSchema.parse(response.json());
    const blockedScenario = payload.scenarios.find((scenario) => scenario.id === "release-blocked");

    assert.equal(payload.selectedScenarioId, "release-blocked");
    assert.equal(payload.scenarios.length, 3);
    assert.ok(blockedScenario);
    assert.equal(blockedScenario.summary.status, "blocked");
    assert.equal(blockedScenario.modules.some((module) => module.key === "workflow"), true);
    assert.match(blockedScenario.summary.blockers.join(" "), /MFA/i);
  } finally {
    await app.close();
  }
});

test("serves the canonical signature queue catalog from the backend", async () => {
  const { runtimeReadiness } = createRuntimeReadinessStub();
  const app = await buildApp({ env: TEST_ENV, runtimeReadiness });

  try {
    const response = await app.inject({
      method: "GET",
      url: "/emission/signature-queue?scenario=mfa-blocked",
    });

    assert.equal(response.statusCode, 200);

    const payload = signatureQueueCatalogSchema.parse(response.json());
    const blockedScenario = payload.scenarios.find((scenario) => scenario.id === "mfa-blocked");

    assert.equal(payload.selectedScenarioId, "mfa-blocked");
    assert.equal(payload.scenarios.length, 3);
    assert.ok(blockedScenario);
    assert.equal(blockedScenario.summary.status, "blocked");
    assert.equal(blockedScenario.approval.canSign, false);
    assert.match(blockedScenario.approval.blockers.join(" "), /MFA/i);
  } finally {
    await app.close();
  }
});

test("serves the canonical self-signup catalog from the backend", async () => {
  const { runtimeReadiness } = createRuntimeReadinessStub();
  const app = await buildApp({ env: TEST_ENV, runtimeReadiness });

  try {
    const response = await app.inject({
      method: "GET",
      url: "/auth/self-signup?scenario=technician-blocked",
    });

    assert.equal(response.statusCode, 200);

    const payload = selfSignupCatalogSchema.parse(response.json());
    const blockedScenario = payload.scenarios.find((scenario) => scenario.id === "technician-blocked");

    assert.equal(payload.selectedScenarioId, "technician-blocked");
    assert.equal(payload.scenarios.length, 3);
    assert.ok(blockedScenario);
    assert.equal(blockedScenario.result.ok, false);
    assert.deepEqual(blockedScenario.result.missingProviders, ["microsoft", "apple"]);
  } finally {
    await app.close();
  }
});

test("serves the canonical onboarding catalog from the backend", async () => {
  const { runtimeReadiness } = createRuntimeReadinessStub();
  const app = await buildApp({ env: TEST_ENV, runtimeReadiness });

  try {
    const response = await app.inject({
      method: "GET",
      url: "/onboarding/readiness?scenario=blocked",
    });

    assert.equal(response.statusCode, 200);

    const payload = onboardingCatalogSchema.parse(response.json());
    const blockedScenario = payload.scenarios.find((scenario) => scenario.id === "blocked");

    assert.equal(payload.selectedScenarioId, "blocked");
    assert.equal(payload.scenarios.length, 2);
    assert.ok(blockedScenario);
    assert.equal(blockedScenario.result.canEmitFirstCertificate, false);
    assert.deepEqual(blockedScenario.result.blockingReasons, [
      "primary_signatory_pending",
      "certificate_numbering_pending",
      "scope_review_pending",
      "public_qr_pending",
    ]);
  } finally {
    await app.close();
  }
});

test("serves the canonical public certificate catalog from the backend", async () => {
  const { runtimeReadiness } = createRuntimeReadinessStub();
  const app = await buildApp({ env: TEST_ENV, runtimeReadiness });

  try {
    const response = await app.inject({
      method: "GET",
      url: "/portal/verify?scenario=reissued",
    });

    assert.equal(response.statusCode, 200);

    const payload = publicCertificateCatalogSchema.parse(response.json());
    const reissuedScenario = payload.scenarios.find((scenario) => scenario.id === "reissued");

    assert.equal(payload.selectedScenarioId, "reissued");
    assert.equal(payload.scenarios.length, 3);
    assert.ok(reissuedScenario);
    assert.equal(reissuedScenario.result.status, "reissued");
    assert.equal(reissuedScenario.result.ok, true);
    if (reissuedScenario.result.ok) {
      assert.equal("actorId" in reissuedScenario.result.certificate, false);
    }
  } finally {
    await app.close();
  }
});

test("serves the canonical review/signature workflow catalog from the backend", async () => {
  const { runtimeReadiness } = createRuntimeReadinessStub();
  const app = await buildApp({ env: TEST_ENV, runtimeReadiness });

  try {
    const response = await app.inject({
      method: "GET",
      url: "/emission/review-signature?scenario=reviewer-conflict",
    });

    assert.equal(response.statusCode, 200);

    const payload = reviewSignatureCatalogSchema.parse(response.json());
    const blockedScenario = payload.scenarios.find((scenario) => scenario.id === "reviewer-conflict");

    assert.equal(payload.selectedScenarioId, "reviewer-conflict");
    assert.equal(payload.scenarios.length, 4);
    assert.ok(blockedScenario);
    assert.equal(blockedScenario.result.status, "blocked");
    assert.equal(blockedScenario.result.reviewStep.status, "blocked");
    assert.equal(blockedScenario.result.suggestions.reviewer?.displayName, "Renata Qualidade");
  } finally {
    await app.close();
  }
});

test("serves the canonical user directory catalog from the backend", async () => {
  const { runtimeReadiness } = createRuntimeReadinessStub();
  const app = await buildApp({ env: TEST_ENV, runtimeReadiness });

  try {
    const response = await app.inject({
      method: "GET",
      url: "/auth/users?scenario=expiring-competencies",
    });

    assert.equal(response.statusCode, 200);

    const payload = userDirectoryCatalogSchema.parse(response.json());
    const attentionScenario = payload.scenarios.find((scenario) => scenario.id === "expiring-competencies");

    assert.equal(payload.selectedScenarioId, "expiring-competencies");
    assert.equal(payload.scenarios.length, 3);
    assert.ok(attentionScenario);
    assert.equal(attentionScenario.summary.status, "attention");
    assert.equal(attentionScenario.summary.expiringCompetencies, 1);
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
