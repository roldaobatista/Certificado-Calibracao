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
  completeLogin,
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

test("creates a persisted session and exposes the authenticated tenant context", async () => {
  const { runtimeReadiness } = createRuntimeReadinessStub();
  const app = await buildApp({
    env: TEST_ENV,
    runtimeReadiness,
    corePersistence: createMemoryCorePersistence(createV1MemorySeed()),
  });

  try {
    const setCookie = await completeLogin(app, "admin@afere.local", "Afere@2026!");
    assert.ok(setCookie);

    const sessionResponse = await app.inject({
      method: "GET",
      url: "/auth/session",
      headers: {
        cookie: setCookie,
      },
    });

    assert.equal(sessionResponse.statusCode, 200);
    const payload = authSessionSchema.parse(sessionResponse.json());
    assert.equal(payload.authenticated, true);
    if (payload.authenticated) {
      assert.equal(payload.user.organizationName, "Laboratorio Persistido");
      assert.equal(payload.user.roles.includes("admin"), true);
    }
  } finally {
    await app.close();
  }
});


test("requires session and RBAC for the persisted user directory and onboarding routes", async () => {
  const { runtimeReadiness } = createRuntimeReadinessStub();
  const app = await buildApp({
    env: TEST_ENV,
    runtimeReadiness,
    corePersistence: createMemoryCorePersistence(createV1MemorySeed()),
  });

  try {
    const denied = await app.inject({
      method: "GET",
      url: "/auth/users",
    });
    assert.equal(denied.statusCode, 401);

    const cookie = await completeLogin(app, "admin@afere.local", "Afere@2026!");
    assert.ok(cookie);

    const userDirectory = await app.inject({
      method: "GET",
      url: "/auth/users",
      headers: {
        cookie,
      },
    });

    assert.equal(userDirectory.statusCode, 200);
    const directoryPayload = userDirectoryCatalogSchema.parse(userDirectory.json());
    assert.equal(directoryPayload.scenarios.length, 1);
    assert.equal(directoryPayload.scenarios[0]?.summary.organizationName, "Laboratorio Persistido");

    const update = await app.inject({
      method: "POST",
      url: "/onboarding/readiness",
      headers: {
        cookie,
      },
      payload: {
        organizationProfileCompleted: true,
        primarySignatoryReady: true,
        certificateNumberingConfigured: true,
        scopeReviewCompleted: true,
        publicQrConfigured: true,
      },
    });

    assert.equal(update.statusCode, 204);

    const onboarding = await app.inject({
      method: "GET",
      url: "/onboarding/readiness",
      headers: {
        cookie,
      },
    });

    assert.equal(onboarding.statusCode, 200);
    const onboardingPayload = onboardingCatalogSchema.parse(onboarding.json());
    assert.equal(onboardingPayload.selectedScenarioId, "ready");
    assert.equal(onboardingPayload.scenarios[0]?.checklist?.organizationProfileCompleted, true);
  } finally {
    await app.close();
  }
});

