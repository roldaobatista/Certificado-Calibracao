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
  getCsrfToken,
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

test("reissues a persisted certificate and preserves the public QR history", async () => {
  const { runtimeReadiness } = createRuntimeReadinessStub();
  const serviceOrderPersistence = createMemoryServiceOrderPersistence(createV4ServiceOrderSeed());
  const app = await buildApp({
    env: TEST_ENV,
    runtimeReadiness,
    corePersistence: createMemoryCorePersistence(createV4CoreSeed()),
    registryPersistence: createMemoryRegistryPersistence(createV4RegistrySeed()),
    serviceOrderPersistence,
  });

  try {
    const adminCookie = await completeLogin(app, "admin@afere.local", "Afere@2026!");
    const adminCsrf = await getCsrfToken(app, adminCookie);

    const portalLogin = await app.inject({
      method: "POST",
      url: "/auth/login",
      payload: {
        email: "marcia@paodoce.com.br",
        password: "Afere@2026!",
      },
    });
    const portalCookie = normalizeCookieHeader(portalLogin.headers["set-cookie"]);
    assert.ok(adminCookie);
    assert.ok(portalCookie);

    const reissueResponse = await app.inject({
      method: "POST",
      url: "/emission/signature-queue/manage",
      headers: { cookie: adminCookie, "X-CSRF-Token": adminCsrf },
      payload: {
        action: "reissue",
        serviceOrderId: "service-order-00141",
        approvalActorUserIdOne: "user-admin-1",
        approvalActorUserIdTwo: "user-reviewer-1",
        signatoryUserId: "user-signatory-1",
        reason: "Correcao de identificacao do certificado.",
        notificationRecipient: "marcia@paodoce.com.br",
        signatureDeviceId: "device-sign-09",
      },
    });
    assert.equal(reissueResponse.statusCode, 204);

    const publications = await serviceOrderPersistence.listCertificatePublicationsByServiceOrder("service-order-00141", "org-1");
    const currentPublication = publications.find((item) => !item.supersededAtUtc);
    assert.ok(currentPublication);
    assert.equal(currentPublication?.revision, "R1");

    const [oldVerifyResponse, newVerifyResponse, certificateResponse] = await Promise.all([
      app.inject({
        method: "GET",
        url: "/portal/verify?certificate=service-order-00141&token=pubtok-os141",
      }),
      app.inject({
        method: "GET",
        url: `/portal/verify?certificate=service-order-00141&token=${currentPublication?.publicVerificationToken}`,
      }),
      app.inject({
        method: "GET",
        url: `/portal/certificate?certificate=${currentPublication?.publicationId}`,
        headers: { cookie: portalCookie },
      }),
    ]);

    assert.equal(oldVerifyResponse.statusCode, 200);
    assert.equal(newVerifyResponse.statusCode, 200);
    assert.equal(certificateResponse.statusCode, 200);

    const oldVerifyPayload = publicCertificateCatalogSchema.parse(oldVerifyResponse.json());
    const newVerifyPayload = publicCertificateCatalogSchema.parse(newVerifyResponse.json());
    const certificatePayload = portalCertificateCatalogSchema.parse(certificateResponse.json());

    assert.equal(oldVerifyPayload.scenarios[0]?.result.ok, true);
    assert.equal(oldVerifyPayload.scenarios[0]?.result.status, "reissued");
    assert.equal(newVerifyPayload.scenarios[0]?.result.ok, true);
    assert.equal(newVerifyPayload.scenarios[0]?.result.status, "authentic");
    assert.equal(certificatePayload.selectedScenarioId, "reissued-history");
    assert.equal(certificatePayload.scenarios[0]?.detail.metadataFields.some((field) => field.value === "R1"), true);
  } finally {
    await app.close();
  }
});

