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

test("serves persisted service orders when the tenant is authenticated", async () => {
  const { runtimeReadiness } = createRuntimeReadinessStub();
  const app = await buildApp({
    env: TEST_ENV,
    runtimeReadiness,
    corePersistence: createMemoryCorePersistence(createV1MemorySeed()),
    registryPersistence: createMemoryRegistryPersistence(createV2RegistrySeed()),
    serviceOrderPersistence: createMemoryServiceOrderPersistence(createV3ServiceOrderSeed()),
  });

  try {
    const login = await app.inject({
      method: "POST",
      url: "/auth/login",
      payload: {
        email: "admin@afere.local",
        password: "Afere@2026!",
      },
    });
    const cookie = normalizeCookieHeader(login.headers["set-cookie"]);
    assert.ok(cookie);

    const response = await app.inject({
      method: "GET",
      url: "/emission/service-order-review",
      headers: { cookie },
    });

    assert.equal(response.statusCode, 200);
    const payload = serviceOrderReviewCatalogSchema.parse(response.json());

    assert.equal(payload.selectedScenarioId, "review-ready");
    assert.equal(payload.scenarios.length, 3);
    assert.equal(
      payload.scenarios[0]?.items.some((item) => item.workOrderNumber === "OS-2026-00142"),
      true,
    );
    assert.equal(payload.scenarios[0]?.detail.customerId, "customer-001");
  } finally {
    await app.close();
  }
});


test("creates and updates persisted service orders through the manage route", async () => {
  const { runtimeReadiness } = createRuntimeReadinessStub();
  const app = await buildApp({
    env: TEST_ENV,
    runtimeReadiness,
    corePersistence: createMemoryCorePersistence(createV1MemorySeed()),
    registryPersistence: createMemoryRegistryPersistence(createV2RegistrySeed()),
    serviceOrderPersistence: createMemoryServiceOrderPersistence(createV3ServiceOrderSeed()),
  });

  try {
    const login = await app.inject({
      method: "POST",
      url: "/auth/login",
      payload: {
        email: "admin@afere.local",
        password: "Afere@2026!",
      },
    });
    const cookie = normalizeCookieHeader(login.headers["set-cookie"]);
    assert.ok(cookie);

    const createResponse = await app.inject({
      method: "POST",
      url: "/emission/service-order-review/manage",
      headers: { cookie },
      payload: {
        action: "save",
        customerId: "customer-001",
        equipmentId: "equipment-001",
        procedureId: "procedure-001",
        primaryStandardId: "standard-001",
        executorUserId: "user-admin-1",
        reviewerUserId: "user-signatory-1",
        workOrderNumber: "OS-2026-0201",
        workflowStatus: "in_execution",
        environmentLabel: "22,3 C · 47% UR",
        curvePointsLabel: "3 pontos iniciais",
        evidenceLabel: "3 evidencias coletadas",
        uncertaintyLabel: "U = 0,20 kg (k=2)",
        conformityLabel: "Execucao em andamento",
        measurementRawData: buildMeasurementRawDataFixture("kg", 15),
        commentDraft: "OS aberta para atendimento em campo.",
      },
    });
    assert.equal(createResponse.statusCode, 204);

    const listResponse = await app.inject({
      method: "GET",
      url: "/emission/service-order-review",
      headers: { cookie },
    });
    const listPayload = serviceOrderReviewCatalogSchema.parse(listResponse.json());
    const createdItem = listPayload.scenarios[1]?.items.find(
      (item) => item.workOrderNumber === "OS-2026-0201",
    );
    assert.ok(createdItem);

    const updateResponse = await app.inject({
      method: "POST",
      url: "/emission/service-order-review/manage",
      headers: { cookie },
      payload: {
        action: "save",
        serviceOrderId: createdItem?.itemId,
        customerId: "customer-001",
        equipmentId: "equipment-001",
        procedureId: "procedure-001",
        primaryStandardId: "standard-001",
        executorUserId: "user-admin-1",
        reviewerUserId: "user-signatory-1",
        workOrderNumber: "OS-2026-0201",
        workflowStatus: "awaiting_review",
        environmentLabel: "22,3 C · 47% UR",
        curvePointsLabel: "5 pontos concluidos",
        evidenceLabel: "9 evidencias anexadas",
        uncertaintyLabel: "U = 0,14 kg (k=2)",
        conformityLabel: "Pronta para revisao",
        measurementRawData: buildMeasurementRawDataFixture("kg", 30),
        commentDraft: "Execucao concluida e pronta para revisao tecnica.",
      },
    });
    assert.equal(updateResponse.statusCode, 204);

    const detailResponse = await app.inject({
      method: "GET",
      url: `/emission/service-order-review?item=${createdItem?.itemId}`,
      headers: { cookie },
    });
    const detailPayload = serviceOrderReviewCatalogSchema.parse(detailResponse.json());

    assert.equal(detailPayload.selectedScenarioId, "history-pending");
    const selectedDetailScenario = detailPayload.scenarios.find(
      (scenario) => scenario.id === detailPayload.selectedScenarioId,
    );
    assert.ok(selectedDetailScenario);
    assert.equal(selectedDetailScenario.detail.itemId, createdItem?.itemId);
    assert.equal(selectedDetailScenario.detail.status, "attention");
    assert.equal(selectedDetailScenario.detail.measurementRawData?.linearityPoints.length, 1);
    assert.equal(
      selectedDetailScenario.detail.equipmentMetrologySnapshot?.verificationScaleIntervalValue,
      0.05,
    );
    assert.equal(
      selectedDetailScenario.detail.standardMetrologySnapshot?.coverageFactorK,
      2,
    );
  } finally {
    await app.close();
  }
});


test("rejects invalid raw measurement JSON when saving a service order", async () => {
  const { runtimeReadiness } = createRuntimeReadinessStub();
  const app = await buildApp({
    env: TEST_ENV,
    runtimeReadiness,
    corePersistence: createMemoryCorePersistence(createV3CoreSeed()),
    registryPersistence: createMemoryRegistryPersistence(createV2RegistrySeed()),
    serviceOrderPersistence: createMemoryServiceOrderPersistence(createV3ServiceOrderSeed()),
  });

  try {
    const login = await app.inject({
      method: "POST",
      url: "/auth/login",
      payload: {
        email: "admin@afere.local",
        password: "Afere@2026!",
      },
    });
    const cookie = normalizeCookieHeader(login.headers["set-cookie"]);
    assert.ok(cookie);

    const response = await app.inject({
      method: "POST",
      url: "/emission/service-order-review/manage",
      headers: { cookie },
      payload: {
        action: "save",
        customerId: "customer-001",
        equipmentId: "equipment-001",
        procedureId: "procedure-001",
        primaryStandardId: "standard-001",
        executorUserId: "user-admin-1",
        reviewerUserId: "user-signatory-1",
        workOrderNumber: "OS-2026-0202",
        workflowStatus: "in_execution",
        environmentLabel: "22,3 C · 47% UR",
        curvePointsLabel: "3 pontos iniciais",
        evidenceLabel: "3 evidencias coletadas",
        uncertaintyLabel: "U = 0,20 kg (k=2)",
        conformityLabel: "Execucao em andamento",
        measurementRawData: "{invalid-json",
        commentDraft: "OS aberta para atendimento em campo.",
      },
    });

    assert.equal(response.statusCode, 400);
  } finally {
    await app.close();
  }
});

