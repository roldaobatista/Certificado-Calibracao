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
      6,
    );
  } finally {
    await app.close();
  }
});


test("serves the canonical audit trail catalog from the backend", async () => {
  const { runtimeReadiness } = createRuntimeReadinessStub();
  const app = await buildApp({ env: TEST_ENV, runtimeReadiness });

  try {
    const response = await app.inject({
      method: "GET",
      url: "/quality/audit-trail?scenario=integrity-blocked",
    });

    assert.equal(response.statusCode, 200);

    const payload = auditTrailCatalogSchema.parse(response.json());
    const blockedScenario = payload.scenarios.find((scenario) => scenario.id === "integrity-blocked");

    assert.equal(payload.selectedScenarioId, "integrity-blocked");
    assert.equal(payload.scenarios.length, 3);
    assert.ok(blockedScenario);
    assert.equal(blockedScenario.detail.status, "blocked");
    assert.match(blockedScenario.detail.blockers.join(" "), /Hash-chain divergente/i);
  } finally {
    await app.close();
  }
});


test("serves the canonical complaint registry catalog from the backend", async () => {
  const { runtimeReadiness } = createRuntimeReadinessStub();
  const app = await buildApp({ env: TEST_ENV, runtimeReadiness });

  try {
    const response = await app.inject({
      method: "GET",
      url: "/quality/complaints?scenario=critical-response&complaint=recl-007",
    });

    assert.equal(response.statusCode, 200);

    const payload = complaintRegistryCatalogSchema.parse(response.json());
    const blockedScenario = payload.scenarios.find((scenario) => scenario.id === "critical-response");

    assert.equal(payload.selectedScenarioId, "critical-response");
    assert.equal(payload.scenarios.length, 3);
    assert.ok(blockedScenario);
    assert.equal(blockedScenario.detail.status, "blocked");
    assert.match(blockedScenario.detail.blockers.join(" "), /reemissao|cliente/i);
  } finally {
    await app.close();
  }
});


test("serves the canonical risk register catalog from the backend", async () => {
  const { runtimeReadiness } = createRuntimeReadinessStub();
  const app = await buildApp({ env: TEST_ENV, runtimeReadiness });

  try {
    const response = await app.inject({
      method: "GET",
      url: "/quality/risk-register?scenario=commercial-pressure&risk=risk-001",
    });

    assert.equal(response.statusCode, 200);

    const payload = riskRegisterCatalogSchema.parse(response.json());
    const blockedScenario = payload.scenarios.find((scenario) => scenario.id === "commercial-pressure");

    assert.equal(payload.selectedScenarioId, "commercial-pressure");
    assert.equal(payload.scenarios.length, 3);
    assert.ok(blockedScenario);
    assert.equal(blockedScenario.detail.status, "blocked");
    assert.match(blockedScenario.detail.blockers.join(" "), /direcao|NC-015|reclamacao/i);
  } finally {
    await app.close();
  }
});


test("serves the canonical quality document catalog from the backend", async () => {
  const { runtimeReadiness } = createRuntimeReadinessStub();
  const app = await buildApp({ env: TEST_ENV, runtimeReadiness });

  try {
    const response = await app.inject({
      method: "GET",
      url: "/quality/documents?scenario=obsolete-blocked&document=document-pg005-r01",
    });

    assert.equal(response.statusCode, 200);

    const payload = qualityDocumentRegistryCatalogSchema.parse(response.json());
    const blockedScenario = payload.scenarios.find((scenario) => scenario.id === "obsolete-blocked");

    assert.equal(payload.selectedScenarioId, "obsolete-blocked");
    assert.equal(payload.scenarios.length, 3);
    assert.ok(blockedScenario);
    assert.equal(blockedScenario.detail.status, "blocked");
    assert.match(blockedScenario.detail.blockers.join(" "), /obsoleta|operacional/i);
  } finally {
    await app.close();
  }
});


test("serves the canonical quality indicator catalog from the backend", async () => {
  const { runtimeReadiness } = createRuntimeReadinessStub();
  const app = await buildApp({ env: TEST_ENV, runtimeReadiness });

  try {
    const response = await app.inject({
      method: "GET",
      url: "/quality/indicators?scenario=critical-drift&indicator=indicator-capa-effectiveness",
    });

    assert.equal(response.statusCode, 200);

    const payload = qualityIndicatorRegistryCatalogSchema.parse(response.json());
    const blockedScenario = payload.scenarios.find((scenario) => scenario.id === "critical-drift");

    assert.equal(payload.selectedScenarioId, "critical-drift");
    assert.equal(payload.scenarios.length, 3);
    assert.ok(blockedScenario);
    assert.equal(blockedScenario.detail.status, "blocked");
    assert.match(blockedScenario.detail.blockers.join(" "), /eficacia|reincidencia|critica/i);
  } finally {
    await app.close();
  }
});


test("serves the canonical customer registry catalog from the backend", async () => {
  const { runtimeReadiness } = createRuntimeReadinessStub();
  const app = await buildApp({ env: TEST_ENV, runtimeReadiness });

  try {
    const response = await app.inject({
      method: "GET",
      url: "/registry/customers?scenario=registration-blocked",
    });

    assert.equal(response.statusCode, 200);

    const payload = customerRegistryCatalogSchema.parse(response.json());
    const blockedScenario = payload.scenarios.find((scenario) => scenario.id === "registration-blocked");

    assert.equal(payload.selectedScenarioId, "registration-blocked");
    assert.equal(payload.scenarios.length, 3);
    assert.ok(blockedScenario);
    assert.equal(blockedScenario.detail.status, "blocked");
    assert.match(blockedScenario.detail.blockers.join(" "), /CEP validado|Campos ausentes/i);
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


test("serves the canonical equipment registry catalog from the backend", async () => {
  const { runtimeReadiness } = createRuntimeReadinessStub();
  const app = await buildApp({ env: TEST_ENV, runtimeReadiness });

  try {
    const response = await app.inject({
      method: "GET",
      url: "/registry/equipment?scenario=certificate-attention",
    });

    assert.equal(response.statusCode, 200);

    const payload = equipmentRegistryCatalogSchema.parse(response.json());
    const attentionScenario = payload.scenarios.find((scenario) => scenario.id === "certificate-attention");

    assert.equal(payload.selectedScenarioId, "certificate-attention");
    assert.equal(payload.scenarios.length, 3);
    assert.ok(attentionScenario);
    assert.equal(attentionScenario.detail.status, "attention");
    assert.match(attentionScenario.detail.warnings.join(" "), /janela critica de vencimento/i);
  } finally {
    await app.close();
  }
});


test("serves the canonical internal audit catalog from the backend", async () => {
  const { runtimeReadiness } = createRuntimeReadinessStub();
  const app = await buildApp({ env: TEST_ENV, runtimeReadiness });

  try {
    const response = await app.inject({
      method: "GET",
      url: "/quality/internal-audit?scenario=extraordinary-escalation&cycle=audit-cycle-extra-2026",
    });

    assert.equal(response.statusCode, 200);

    const payload = internalAuditCatalogSchema.parse(response.json());
    const blockedScenario = payload.scenarios.find(
      (scenario) => scenario.id === "extraordinary-escalation",
    );

    assert.equal(payload.selectedScenarioId, "extraordinary-escalation");
    assert.equal(payload.scenarios.length, 3);
    assert.ok(blockedScenario);
    assert.equal(blockedScenario.detail.status, "blocked");
    assert.match(blockedScenario.detail.blockers.join(" "), /extraordinaria|trilha|liberacao/i);
  } finally {
    await app.close();
  }
});


test("serves the canonical management review catalog from the backend", async () => {
  const { runtimeReadiness } = createRuntimeReadinessStub();
  const app = await buildApp({ env: TEST_ENV, runtimeReadiness });

  try {
    const response = await app.inject({
      method: "GET",
      url: "/quality/management-review?scenario=extraordinary-response&meeting=review-extra-2026-04",
    });

    assert.equal(response.statusCode, 200);

    const payload = managementReviewCatalogSchema.parse(response.json());
    const blockedScenario = payload.scenarios.find(
      (scenario) => scenario.id === "extraordinary-response",
    );

    assert.equal(payload.selectedScenarioId, "extraordinary-response");
    assert.equal(payload.scenarios.length, 3);
    assert.ok(blockedScenario);
    assert.equal(blockedScenario.detail.status, "blocked");
    assert.match(blockedScenario.detail.scheduledForLabel, /23\/04\/2026|04\/2026/i);
    assert.match(blockedScenario.detail.calendarExportHref, /calendar\.ics/i);
    assert.equal(blockedScenario.detail.calendar.entries.length >= 2, true);
    assert.equal(blockedScenario.detail.signature.canSign, true);
    assert.equal(blockedScenario.detail.signature.status, "pending");
    assert.match(blockedScenario.detail.blockers.join(" "), /extraordinaria|liberacao|trilha/i);
  } finally {
    await app.close();
  }
});


test("serves the canonical nonconforming work catalog from the backend", async () => {
  const { runtimeReadiness } = createRuntimeReadinessStub();
  const app = await buildApp({ env: TEST_ENV, runtimeReadiness });

  try {
    const response = await app.inject({
      method: "GET",
      url: "/quality/nonconforming-work?scenario=release-blocked&case=ncw-015",
    });

    assert.equal(response.statusCode, 200);

    const payload = nonconformingWorkCatalogSchema.parse(response.json());
    const blockedScenario = payload.scenarios.find(
      (scenario) => scenario.id === "release-blocked",
    );

    assert.equal(payload.selectedScenarioId, "release-blocked");
    assert.equal(payload.scenarios.length, 3);
    assert.ok(blockedScenario);
    assert.equal(blockedScenario.detail.status, "blocked");
    assert.match(blockedScenario.detail.releaseRuleLabel, /nova OS|reemissao|leitura bruta/i);
  } finally {
    await app.close();
  }
});


test("serves the canonical standard registry catalog from the backend", async () => {
  const { runtimeReadiness } = createRuntimeReadinessStub();
  const app = await buildApp({ env: TEST_ENV, runtimeReadiness });

  try {
    const response = await app.inject({
      method: "GET",
      url: "/registry/standards?scenario=expired-blocked",
    });

    assert.equal(response.statusCode, 200);

    const payload = standardRegistryCatalogSchema.parse(response.json());
    const blockedScenario = payload.scenarios.find((scenario) => scenario.id === "expired-blocked");

    assert.equal(payload.selectedScenarioId, "expired-blocked");
    assert.equal(payload.scenarios.length, 3);
    assert.ok(blockedScenario);
    assert.equal(blockedScenario.detail.status, "blocked");
    assert.match(blockedScenario.detail.blockers.join(" "), /vencido/i);
  } finally {
    await app.close();
  }
});


test("serves the canonical procedure registry catalog from the backend", async () => {
  const { runtimeReadiness } = createRuntimeReadinessStub();
  const app = await buildApp({ env: TEST_ENV, runtimeReadiness });

  try {
    const response = await app.inject({
      method: "GET",
      url: "/registry/procedures?scenario=obsolete-visible",
    });

    assert.equal(response.statusCode, 200);

    const payload = procedureRegistryCatalogSchema.parse(response.json());
    const blockedScenario = payload.scenarios.find((scenario) => scenario.id === "obsolete-visible");

    assert.equal(payload.selectedScenarioId, "obsolete-visible");
    assert.equal(payload.scenarios.length, 3);
    assert.ok(blockedScenario);
    assert.equal(blockedScenario.detail.status, "blocked");
    assert.match(blockedScenario.detail.blockers.join(" "), /obsoleta|novas OS/i);
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


test("serves the canonical nonconformity registry catalog from the backend", async () => {
  const { runtimeReadiness } = createRuntimeReadinessStub();
  const app = await buildApp({ env: TEST_ENV, runtimeReadiness });

  try {
    const response = await app.inject({
      method: "GET",
      url: "/quality/nonconformities?scenario=critical-response",
    });

    assert.equal(response.statusCode, 200);

    const payload = nonconformityRegistryCatalogSchema.parse(response.json());
    const blockedScenario = payload.scenarios.find((scenario) => scenario.id === "critical-response");

    assert.equal(payload.selectedScenarioId, "critical-response");
    assert.equal(payload.scenarios.length, 3);
    assert.ok(blockedScenario);
    assert.equal(blockedScenario.detail.status, "blocked");
    assert.match(blockedScenario.detail.blockers.join(" "), /critica aberta/i);
  } finally {
    await app.close();
  }
});


test("serves the canonical quality hub catalog from the backend", async () => {
  const { runtimeReadiness } = createRuntimeReadinessStub();
  const app = await buildApp({ env: TEST_ENV, runtimeReadiness });

  try {
    const response = await app.inject({
      method: "GET",
      url: "/quality?scenario=critical-response&module=audit-trail",
    });

    assert.equal(response.statusCode, 200);

    const payload = qualityHubCatalogSchema.parse(response.json());
    const blockedScenario = payload.scenarios.find((scenario) => scenario.id === "critical-response");

    assert.equal(payload.selectedScenarioId, "critical-response");
    assert.equal(payload.scenarios.length, 3);
    assert.ok(blockedScenario);
    assert.equal(blockedScenario.selectedModuleKey, "audit-trail");
    assert.equal(blockedScenario.summary.status, "blocked");
    assert.match(blockedScenario.summary.blockers.join(" "), /integridade|NC critica/i);
  } finally {
    await app.close();
  }
});


test("serves the canonical organization settings catalog from the backend", async () => {
  const { runtimeReadiness } = createRuntimeReadinessStub();
  const app = await buildApp({ env: TEST_ENV, runtimeReadiness });

  try {
    const response = await app.inject({
      method: "GET",
      url: "/settings/organization?scenario=profile-change-blocked&section=regulatory_profile",
    });

    assert.equal(response.statusCode, 200);

    const payload = organizationSettingsCatalogSchema.parse(response.json());
    const blockedScenario = payload.scenarios.find((scenario) => scenario.id === "profile-change-blocked");

    assert.equal(payload.selectedScenarioId, "profile-change-blocked");
    assert.equal(payload.scenarios.length, 3);
    assert.ok(blockedScenario);
    assert.equal(blockedScenario.selectedSectionKey, "regulatory_profile");
    assert.equal(blockedScenario.detail.status, "blocked");
    assert.match(blockedScenario.detail.blockers.join(" "), /dupla aprovacao|serie acreditada/i);
  } finally {
    await app.close();
  }
});


test("serves the canonical portal dashboard catalog from the backend", async () => {
  const { runtimeReadiness } = createRuntimeReadinessStub();
  const app = await buildApp({ env: TEST_ENV, runtimeReadiness });

  try {
    const response = await app.inject({
      method: "GET",
      url: "/portal/dashboard?scenario=overdue-blocked",
    });

    assert.equal(response.statusCode, 200);

    const payload = portalDashboardCatalogSchema.parse(response.json());
    const blockedScenario = payload.scenarios.find((scenario) => scenario.id === "overdue-blocked");

    assert.equal(payload.selectedScenarioId, "overdue-blocked");
    assert.equal(payload.scenarios.length, 3);
    assert.ok(blockedScenario);
    assert.equal(blockedScenario.summary.status, "blocked");
    assert.match(blockedScenario.summary.blockers.join(" "), /BAL-019/i);
  } finally {
    await app.close();
  }
});


test("serves the canonical portal certificate catalog from the backend", async () => {
  const { runtimeReadiness } = createRuntimeReadinessStub();
  const app = await buildApp({ env: TEST_ENV, runtimeReadiness });

  try {
    const response = await app.inject({
      method: "GET",
      url: "/portal/certificate?scenario=download-blocked&certificate=cert-00128",
    });

    assert.equal(response.statusCode, 200);

    const payload = portalCertificateCatalogSchema.parse(response.json());
    const blockedScenario = payload.scenarios.find((scenario) => scenario.id === "download-blocked");

    assert.equal(payload.selectedScenarioId, "download-blocked");
    assert.equal(payload.scenarios.length, 3);
    assert.ok(blockedScenario);
    assert.equal(blockedScenario.detail.status, "blocked");
    assert.match(blockedScenario.detail.blockers.join(" "), /viewer integral/i);
  } finally {
    await app.close();
  }
});


test("serves the canonical portal equipment catalog from the backend", async () => {
  const { runtimeReadiness } = createRuntimeReadinessStub();
  const app = await buildApp({ env: TEST_ENV, runtimeReadiness });

  try {
    const response = await app.inject({
      method: "GET",
      url: "/portal/equipment?scenario=overdue-blocked&equipment=equipment-bal-019",
    });

    assert.equal(response.statusCode, 200);

    const payload = portalEquipmentCatalogSchema.parse(response.json());
    const blockedScenario = payload.scenarios.find((scenario) => scenario.id === "overdue-blocked");

    assert.equal(payload.selectedScenarioId, "overdue-blocked");
    assert.equal(payload.scenarios.length, 3);
    assert.ok(blockedScenario);
    assert.equal(blockedScenario.detail.status, "blocked");
    assert.match(blockedScenario.detail.blockers.join(" "), /calibracao valida/i);
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


test("serves the canonical service-order review catalog from the backend", async () => {
  const { runtimeReadiness } = createRuntimeReadinessStub();
  const app = await buildApp({ env: TEST_ENV, runtimeReadiness });

  try {
    const response = await app.inject({
      method: "GET",
      url: "/emission/service-order-review?scenario=review-blocked",
    });

    assert.equal(response.statusCode, 200);

    const payload = serviceOrderReviewCatalogSchema.parse(response.json());
    const blockedScenario = payload.scenarios.find((scenario) => scenario.id === "review-blocked");

    assert.equal(payload.selectedScenarioId, "review-blocked");
    assert.equal(payload.scenarios.length, 3);
    assert.ok(blockedScenario);
    assert.equal(blockedScenario.detail.status, "blocked");
    assert.equal(blockedScenario.detail.allowedActions.includes("approve_review"), false);
    assert.match(blockedScenario.detail.blockers.join(" "), /Revisor atual coincide com o executor/i);
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


test("requires session and exposes the persisted v2 registry catalogs", async () => {
  const { runtimeReadiness } = createRuntimeReadinessStub();
  const app = await buildApp({
    env: TEST_ENV,
    runtimeReadiness,
    corePersistence: createMemoryCorePersistence(createV1MemorySeed()),
    registryPersistence: createMemoryRegistryPersistence(createV2RegistrySeed()),
  });

  try {
    const denied = await app.inject({
      method: "GET",
      url: "/registry/customers",
    });
    assert.equal(denied.statusCode, 401);

    const cookie = await completeLogin(app, "admin@afere.local", "Afere@2026!");
    assert.ok(cookie);

    const customers = await app.inject({
      method: "GET",
      url: "/registry/customers",
      headers: { cookie },
    });
    assert.equal(customers.statusCode, 200);
    const customerPayload = customerRegistryCatalogSchema.parse(customers.json());
    assert.equal(customerPayload.scenarios.length, 1);
    assert.equal(customerPayload.scenarios[0]?.detail.history.length! > 0, true);

    const equipment = await app.inject({
      method: "GET",
      url: "/registry/equipment",
      headers: { cookie },
    });
    assert.equal(equipment.statusCode, 200);
    const equipmentPayload = equipmentRegistryCatalogSchema.parse(equipment.json());
    assert.equal(equipmentPayload.scenarios.length, 1);
    assert.equal(equipmentPayload.scenarios[0]?.items.length! >= 1, true);

    const standards = await app.inject({
      method: "GET",
      url: "/registry/standards",
      headers: { cookie },
    });
    assert.equal(standards.statusCode, 200);
    const standardPayload = standardRegistryCatalogSchema.parse(standards.json());
    assert.equal(standardPayload.scenarios.length, 1);
    assert.equal(standardPayload.scenarios[0]?.detail.history.length! >= 1, true);

    const procedures = await app.inject({
      method: "GET",
      url: "/registry/procedures",
      headers: { cookie },
    });
    assert.equal(procedures.statusCode, 200);
    const procedurePayload = procedureRegistryCatalogSchema.parse(procedures.json());
    assert.equal(procedurePayload.scenarios.length, 1);
    assert.equal(procedurePayload.scenarios[0]?.detail.relatedDocuments.length! >= 1, true);
  } finally {
    await app.close();
  }
});


test("derives execution labels from raw measurement data when manual labels are omitted", async () => {
  const { runtimeReadiness } = createRuntimeReadinessStub();
  const app = await buildApp({
    env: TEST_ENV,
    runtimeReadiness,
    corePersistence: createMemoryCorePersistence(createV3CoreSeed()),
    registryPersistence: createMemoryRegistryPersistence(createV2RegistrySeed()),
    serviceOrderPersistence: createMemoryServiceOrderPersistence(createV3ServiceOrderSeed()),
  });

  try {
    const cookie = await completeLogin(app, "admin@afere.local", "Afere@2026!");
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
        reviewerUserId: "user-reviewer-1",
        signatoryUserId: "user-signatory-1",
        workOrderNumber: "OS-2026-0203",
        workflowStatus: "awaiting_review",
        measurementRawData: buildMeasurementRawDataFixture("kg", 20),
        commentDraft: "OS criada com labels derivados do bruto.",
      },
    });
    assert.equal(createResponse.statusCode, 204);

    const detailResponse = await app.inject({
      method: "GET",
      url: "/emission/service-order-review",
      headers: { cookie },
    });
    const payload = serviceOrderReviewCatalogSchema.parse(detailResponse.json());
    const created = payload.scenarios
      .flatMap((scenario) => scenario.items)
      .find((item) => item.workOrderNumber === "OS-2026-0203");

    assert.ok(created);

    const createdDetailResponse = await app.inject({
      method: "GET",
      url: `/emission/service-order-review?item=${created?.itemId}`,
      headers: { cookie },
    });
    const createdPayload = serviceOrderReviewCatalogSchema.parse(createdDetailResponse.json());
    const selectedScenario = createdPayload.scenarios.find(
      (scenario) => scenario.id === createdPayload.selectedScenarioId,
    );
    assert.ok(selectedScenario);
    const detail = selectedScenario.detail;

    assert.match(detail.environmentLabel, /22,1 C -> 22,3 C/);
    assert.match(detail.curvePointsLabel, /repetitividade/i);
    assert.match(detail.evidenceLabel, /evidencia\(s\) estruturada\(s\)/i);
    assert.match(detail.conformityLabel, /Bruto estruturado apto para revisao/i);
    assert.match(detail.uncertaintyLabel, /U preliminar = ±/i);
    assert.equal(Number((detail.measurementExpandedUncertaintyValue ?? 0).toFixed(6)), 0.057859);
    assert.equal(detail.measurementCoverageFactor, 2);
    assert.equal(detail.measurementUnit, "kg");
  } finally {
    await app.close();
  }
});


test("serves the persisted V3 emission catalogs for the authenticated tenant", async () => {
  const { runtimeReadiness } = createRuntimeReadinessStub();
  const app = await buildApp({
    env: TEST_ENV,
    runtimeReadiness,
    corePersistence: createMemoryCorePersistence(createV3CoreSeed()),
    registryPersistence: createMemoryRegistryPersistence(createV2RegistrySeed()),
    serviceOrderPersistence: createMemoryServiceOrderPersistence(createV3ServiceOrderSeed()),
  });

  try {
    const cookie = await completeLogin(app, "admin@afere.local", "Afere@2026!");
    assert.ok(cookie);

    const [dryRunResponse, reviewResponse, queueResponse, auditResponse, serviceOrderResponse] =
      await Promise.all([
      app.inject({
        method: "GET",
        url: "/emission/dry-run?item=service-order-00142",
        headers: { cookie },
      }),
      app.inject({
        method: "GET",
        url: "/emission/review-signature?item=service-order-00142",
        headers: { cookie },
      }),
      app.inject({
        method: "GET",
        url: "/emission/signature-queue?item=service-order-00142",
        headers: { cookie },
      }),
      app.inject({
        method: "GET",
        url: "/quality/audit-trail?item=service-order-00142",
        headers: { cookie },
      }),
      app.inject({
        method: "GET",
        url: "/emission/service-order-review?item=service-order-00142",
        headers: { cookie },
      }),
    ]);

    assert.equal(dryRunResponse.statusCode, 200);
    assert.equal(reviewResponse.statusCode, 200);
    assert.equal(queueResponse.statusCode, 200);
    assert.equal(auditResponse.statusCode, 200);
    assert.equal(serviceOrderResponse.statusCode, 200);

    const dryRunPayload = emissionDryRunCatalogSchema.parse(dryRunResponse.json());
    const reviewPayload = reviewSignatureCatalogSchema.parse(reviewResponse.json());
    const queuePayload = signatureQueueCatalogSchema.parse(queueResponse.json());
    const auditPayload = auditTrailCatalogSchema.parse(auditResponse.json());
    const serviceOrderPayload = serviceOrderReviewCatalogSchema.parse(serviceOrderResponse.json());

    assert.equal(dryRunPayload.scenarios.length, 3);
    assert.equal(reviewPayload.scenarios.length, 4);
    assert.equal(queuePayload.scenarios.length, 3);
    assert.equal(auditPayload.scenarios.length, 3);
    assert.equal(
      dryRunPayload.scenarios[0]?.result.checks.some((check) => check.id === "raw_measurement_capture"),
      true,
    );
    assert.equal(
      serviceOrderPayload.scenarios[0]?.detail.metrics.some((metric) => metric.label === "Repetitividade"),
      true,
    );
  } finally {
    await app.close();
  }
});


test("serves the persisted V4 portal and public QR catalogs for the authenticated customer", async () => {
  const { runtimeReadiness } = createRuntimeReadinessStub();
  const app = await buildApp({
    env: TEST_ENV,
    runtimeReadiness,
    corePersistence: createMemoryCorePersistence(createV4CoreSeed()),
    registryPersistence: createMemoryRegistryPersistence(createV4RegistrySeed()),
    serviceOrderPersistence: createMemoryServiceOrderPersistence(createV4ServiceOrderSeed()),
  });

  try {
    const login = await app.inject({
      method: "POST",
      url: "/auth/login",
      payload: {
        email: "marcia@paodoce.com.br",
        password: "Afere@2026!",
      },
    });
    const cookie = normalizeCookieHeader(login.headers["set-cookie"]);
    assert.ok(cookie);

    const [dashboardResponse, equipmentResponse, certificateResponse, verifyResponse] = await Promise.all([
      app.inject({
        method: "GET",
        url: "/portal/dashboard",
        headers: { cookie },
      }),
      app.inject({
        method: "GET",
        url: "/portal/equipment?equipment=equipment-00141",
        headers: { cookie },
      }),
      app.inject({
        method: "GET",
        url: "/portal/certificate?certificate=publication-00141-r0",
        headers: { cookie },
      }),
      app.inject({
        method: "GET",
        url: "/portal/verify?certificate=service-order-00141&token=pubtok-os141",
      }),
    ]);

    assert.equal(dashboardResponse.statusCode, 200);
    assert.equal(equipmentResponse.statusCode, 200);
    assert.equal(certificateResponse.statusCode, 200);
    assert.equal(verifyResponse.statusCode, 200);

    const dashboardPayload = portalDashboardCatalogSchema.parse(dashboardResponse.json());
    const equipmentPayload = portalEquipmentCatalogSchema.parse(equipmentResponse.json());
    const certificatePayload = portalCertificateCatalogSchema.parse(certificateResponse.json());
    const verifyPayload = publicCertificateCatalogSchema.parse(verifyResponse.json());

    assert.equal(dashboardPayload.scenarios[0]?.summary.clientName, "Marcia Lima");
    assert.equal(dashboardPayload.scenarios[0]?.recentCertificates[0]?.certificateId, "publication-00141-r0");
    assert.equal(equipmentPayload.scenarios[0]?.detail.certificateHistory[0]?.certificateId, "publication-00141-r0");
    assert.equal(certificatePayload.scenarios[0]?.detail.metadataFields.some((field) => field.value === "R0"), true);
    assert.equal(verifyPayload.scenarios[0]?.result.ok, true);
    assert.equal(verifyPayload.scenarios[0]?.result.status, "authentic");
  } finally {
    await app.close();
  }
});


test("serves the persisted V5 quality and governance catalogs for the authenticated tenant", async () => {
  const { runtimeReadiness } = createRuntimeReadinessStub();
  const app = await buildApp({
    env: TEST_ENV,
    runtimeReadiness,
    corePersistence: createMemoryCorePersistence(createV4CoreSeed()),
    registryPersistence: createMemoryRegistryPersistence(createV4RegistrySeed()),
    serviceOrderPersistence: createMemoryServiceOrderPersistence(createV4ServiceOrderSeed()),
    qualityPersistence: createMemoryQualityPersistence(createV5QualitySeed()),
  });

  try {
    const cookie = await completeLogin(app, "admin@afere.local", "Afere@2026!");
    assert.ok(cookie);

    const [ncResponse, workResponse, auditResponse, indicatorResponse, reviewResponse, hubResponse, settingsResponse] =
      await Promise.all([
        app.inject({ method: "GET", url: "/quality/nonconformities", headers: { cookie } }),
        app.inject({ method: "GET", url: "/quality/nonconforming-work", headers: { cookie } }),
        app.inject({ method: "GET", url: "/quality/internal-audit", headers: { cookie } }),
        app.inject({ method: "GET", url: "/quality/indicators", headers: { cookie } }),
        app.inject({ method: "GET", url: "/quality/management-review", headers: { cookie } }),
        app.inject({ method: "GET", url: "/quality", headers: { cookie } }),
        app.inject({ method: "GET", url: "/settings/organization", headers: { cookie } }),
      ]);

    assert.equal(ncResponse.statusCode, 200);
    assert.equal(workResponse.statusCode, 200);
    assert.equal(auditResponse.statusCode, 200);
    assert.equal(indicatorResponse.statusCode, 200);
    assert.equal(reviewResponse.statusCode, 200);
    assert.equal(hubResponse.statusCode, 200);
    assert.equal(settingsResponse.statusCode, 200);

    const ncPayload = nonconformityRegistryCatalogSchema.parse(ncResponse.json());
    const auditPayload = internalAuditCatalogSchema.parse(auditResponse.json());
    const indicatorPayload = qualityIndicatorRegistryCatalogSchema.parse(indicatorResponse.json());
    const reviewPayload = managementReviewCatalogSchema.parse(reviewResponse.json());
    const hubPayload = qualityHubCatalogSchema.parse(hubResponse.json());
    const settingsPayload = organizationSettingsCatalogSchema.parse(settingsResponse.json());

    assert.equal(ncPayload.scenarios[0]?.items[0]?.ncId, "nc-014");
    assert.equal(auditPayload.scenarios[0]?.cycles[0]?.cycleId, "audit-cycle-2026-q2");
    assert.equal((indicatorPayload.scenarios[0]?.indicators.length ?? 0) >= 3, true);
    assert.match(indicatorPayload.scenarios[0]?.summary.monthlyWindowLabel ?? "", /11\/2025|04\/2026/i);
    assert.equal((indicatorPayload.scenarios[0]?.detail.snapshots.length ?? 0) >= 6, true);
    assert.equal(reviewPayload.scenarios[0]?.meetings[0]?.meetingId, "review-2026-q2");
    assert.match(reviewPayload.scenarios[0]?.detail.calendarExportHref ?? "", /calendar\.ics/i);
    assert.equal((reviewPayload.scenarios[0]?.detail.calendar.entries.length ?? 0) >= 1, true);
    assert.equal(reviewPayload.scenarios[0]?.detail.signature.canSign, true);
    assert.equal(reviewPayload.scenarios[0]?.detail.signature.status, "pending");
    assert.equal((hubPayload.scenarios[0]?.summary.implementedModuleCount ?? 0) >= 6, true);
    assert.equal(settingsPayload.scenarios[0]?.summary.organizationCode, "AFERE");
  } finally {
    await app.close();
  }
});

