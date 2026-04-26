import assert from "node:assert/strict";
import { test } from "node:test";

import {
  auditTrailCatalogSchema,
  authSessionSchema,
  certificatePreviewCatalogSchema,
  complaintRegistryCatalogSchema,
  customerRegistryCatalogSchema,
  emissionDryRunCatalogSchema,
  emissionWorkspaceCatalogSchema,
  managementReviewCatalogSchema,
  nonconformingWorkCatalogSchema,
  nonconformityRegistryCatalogSchema,
  offlineSyncCatalogSchema,
  equipmentRegistryCatalogSchema,
  internalAuditCatalogSchema,
  onboardingCatalogSchema,
  organizationSettingsCatalogSchema,
  portalDashboardCatalogSchema,
  portalCertificateCatalogSchema,
  portalEquipmentCatalogSchema,
  procedureRegistryCatalogSchema,
  publicCertificateCatalogSchema,
  qualityDocumentRegistryCatalogSchema,
  qualityHubCatalogSchema,
  qualityIndicatorRegistryCatalogSchema,
  riskRegisterCatalogSchema,
  reviewSignatureCatalogSchema,
  serviceOrderReviewCatalogSchema,
  selfSignupCatalogSchema,
  signatureQueueCatalogSchema,
  standardRegistryCatalogSchema,
  userDirectoryCatalogSchema,
} from "@afere/contracts";

import { buildApp } from "../../app.js";
import { createMemoryCorePersistence } from "../../domain/auth/core-persistence.js";
import { createMemoryServiceOrderPersistence } from "../../domain/emission/service-order-persistence.js";
import { createMemoryQualityPersistence } from "../../domain/quality/quality-persistence.js";
import { createMemoryRegistryPersistence } from "../../domain/registry/registry-persistence.js";

import {
  TEST_ENV,
  createRuntimeReadinessStub,
  normalizeCookieHeader,
  createV1MemorySeed,
  createV2RegistrySeed,
  createV3CoreSeed,
  createV3ServiceOrderSeed,
  createV4CoreSeed,
  createV4RegistrySeed,
  createV4ServiceOrderSeed,
  createV5QualitySeed,
  buildMeasurementRawDataFixture,
  buildEquipmentMetrologyProfileFixture,
  buildStandardMetrologyProfileFixture,
  buildSeedEmissionAuditTrail,
} from "./helpers.js";

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

