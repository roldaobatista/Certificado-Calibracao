import { computeAuditHash } from "@afere/audit-log";
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
  portalCertificateCatalogSchema,
  portalDashboardCatalogSchema,
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
  type MembershipRole,
} from "@afere/contracts";

import type { Env } from "./config/env.js";
import { createMemoryCorePersistence } from "./domain/auth/core-persistence.js";
import { hashPassword } from "./domain/auth/password.js";
import { createMemoryServiceOrderPersistence } from "./domain/emission/service-order-persistence.js";
import { createMemoryQualityPersistence } from "./domain/quality/quality-persistence.js";
import { createMemoryRegistryPersistence } from "./domain/registry/registry-persistence.js";
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

test("serves the canonical offline sync review queue from the backend", async () => {
  const { runtimeReadiness } = createRuntimeReadinessStub();
  const app = await buildApp({ env: TEST_ENV, runtimeReadiness });

  try {
    const response = await app.inject({
      method: "GET",
      url: "/sync/review-queue?scenario=human-review-open&item=sync-os-2026-0047&conflict=conflict-c1-0047",
    });

    assert.equal(response.statusCode, 200);

    const payload = offlineSyncCatalogSchema.parse(response.json());
    const selectedScenario = payload.scenarios.find((scenario) => scenario.id === "human-review-open");

    assert.equal(payload.selectedScenarioId, "human-review-open");
    assert.equal(payload.scenarios.length, 3);
    assert.ok(selectedScenario);
    assert.equal(selectedScenario.summary.status, "attention");
    assert.equal(selectedScenario.detail.class, "C1");
    assert.equal(selectedScenario.detail.blockedForEmission, true);
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

test("creates a persisted session and exposes the authenticated tenant context", async () => {
  const { runtimeReadiness } = createRuntimeReadinessStub();
  const app = await buildApp({
    env: TEST_ENV,
    runtimeReadiness,
    corePersistence: createMemoryCorePersistence(createV1MemorySeed()),
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

    assert.equal(login.statusCode, 200);
    const setCookie = normalizeCookieHeader(login.headers["set-cookie"]);
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

test("allows admins to manage persisted users and v2 registry records", async () => {
  const { runtimeReadiness } = createRuntimeReadinessStub();
  const app = await buildApp({
    env: TEST_ENV,
    runtimeReadiness,
    corePersistence: createMemoryCorePersistence(createV1MemorySeed()),
    registryPersistence: createMemoryRegistryPersistence(createV2RegistrySeed()),
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

    const saveUser = await app.inject({
      method: "POST",
      url: "/auth/users/manage",
      headers: { cookie },
      payload: {
        action: "save",
        email: "tecnico2@afere.local",
        password: "Afere@2026!",
        displayName: "Teresa Tecnica",
        roles: ["technician"],
        status: "active",
        teamName: "Campo",
        mfaEnforced: false,
        mfaEnrolled: false,
        deviceCount: 1,
        competenciesText: "balanca|Tecnica de campo|2027-06-01",
      },
    });
    assert.equal(saveUser.statusCode, 204);

    const saveStandard = await app.inject({
      method: "POST",
      url: "/registry/standards/manage",
      headers: { cookie },
      payload: {
        action: "save",
        code: "PESO-050",
        title: "Peso padrao 50 kg",
        kindLabel: "Peso",
        nominalClassLabel: "50 kg · M1",
        sourceLabel: "RBC-5050",
        certificateLabel: "5050/26/001",
        manufacturerLabel: "Coelmatic",
        modelLabel: "M50K",
        serialNumberLabel: "50K-001",
        nominalValueLabel: "50,000 kg",
        classLabel: "M1",
        usageRangeLabel: "0 kg ate 50 kg",
        measurementValue: 50,
        applicableRangeMin: 0,
        applicableRangeMax: 50,
        uncertaintyLabel: "+/- 0,020 kg",
        correctionFactorLabel: "+0,001 kg",
        hasValidCertificate: true,
        certificateValidUntilUtc: "2027-04-23",
      },
    });
    assert.equal(saveStandard.statusCode, 204);

    const saveProcedure = await app.inject({
      method: "POST",
      url: "/registry/procedures/manage",
      headers: { cookie },
      payload: {
        action: "save",
        code: "PT-050",
        title: "Calibracao de plataforma pesada",
        typeLabel: "NAWI pesada",
        revisionLabel: "01",
        effectiveSinceUtc: "2026-04-23",
        lifecycleLabel: "Vigente",
        usageLabel: "Campo controlado",
        scopeLabel: "Balancas plataforma ate 500 kg.",
        environmentRangeLabel: "Temp 18C-26C",
        curvePolicyLabel: "5 pontos com subida e descida",
        standardsPolicyLabel: "Padrao de massa M1 vigente",
        approvalLabel: "Aprovado por Ana Administradora",
        relatedDocuments: ["IT-050", "FR-050"],
      },
    });
    assert.equal(saveProcedure.statusCode, 204);

    const standardsResponse = await app.inject({
      method: "GET",
      url: "/registry/standards",
      headers: { cookie },
    });
    const standardsPayload = standardRegistryCatalogSchema.parse(standardsResponse.json());
    const createdStandard = standardsPayload.scenarios[0]?.items.find(
      (item) => item.certificateLabel === "5050/26/001",
    );
    assert.ok(createdStandard);

    const proceduresResponse = await app.inject({
      method: "GET",
      url: "/registry/procedures",
      headers: { cookie },
    });
    const proceduresPayload = procedureRegistryCatalogSchema.parse(proceduresResponse.json());
    const createdProcedure = proceduresPayload.scenarios[0]?.items.find(
      (item) => item.code === "PT-050",
    );
    assert.ok(createdProcedure);

    const saveEquipment = await app.inject({
      method: "POST",
      url: "/registry/equipment/manage",
      headers: { cookie },
      payload: {
        action: "save",
        customerId: "customer-001",
        procedureId: createdProcedure?.procedureId,
        primaryStandardId: createdStandard?.standardId,
        code: "EQ-050",
        tagCode: "PLAT-050",
        serialNumber: "SN-050",
        typeModelLabel: "Balanca plataforma 500 kg",
        capacityClassLabel: "500 kg · 0,1 kg · III",
        supportingStandardCodes: ["PESO-001", "PESO-002"],
        addressLine1: "Rua da Calibracao, 500",
        addressCity: "Cuiaba",
        addressState: "MT",
        addressPostalCode: "78000-500",
        addressCountry: "Brasil",
        addressConditionsLabel: "Area coberta",
        lastCalibrationAtUtc: "2026-04-10",
        nextCalibrationAtUtc: "2026-10-10",
      },
    });
    assert.equal(saveEquipment.statusCode, 204);

    const saveCustomer = await app.inject({
      method: "POST",
      url: "/registry/customers/manage",
      headers: { cookie },
      payload: {
        action: "save",
        legalName: "Cliente Campo Ltda.",
        tradeName: "Cliente Campo",
        documentLabel: "55.555.555/0001-55",
        segmentLabel: "Industria",
        accountOwnerName: "Marta Operacoes",
        accountOwnerEmail: "marta@clientecampo.com.br",
        contractLabel: "Contrato vigente ate 12/2026",
        specialConditionsLabel: "Atendimento em janela noturna",
        contactName: "Marta Operacoes",
        contactRoleLabel: "Coordenadora",
        contactEmail: "marta@clientecampo.com.br",
        contactPhoneLabel: "(65) 99999-5050",
        addressLine1: "Distrito Industrial, 505",
        addressCity: "Cuiaba",
        addressState: "MT",
        addressPostalCode: "78010-505",
        addressCountry: "Brasil",
        addressConditionsLabel: "Acesso controlado",
      },
    });
    assert.equal(saveCustomer.statusCode, 204);

    const directoryResponse = await app.inject({
      method: "GET",
      url: "/auth/users",
      headers: { cookie },
    });
    const directoryPayload = userDirectoryCatalogSchema.parse(directoryResponse.json());
    assert.equal(
      directoryPayload.scenarios[0]?.users.some((user) => user.email === "tecnico2@afere.local"),
      true,
    );

    const customersResponse = await app.inject({
      method: "GET",
      url: "/registry/customers",
      headers: { cookie },
    });
    const customersPayload = customerRegistryCatalogSchema.parse(customersResponse.json());
    assert.equal(
      customersPayload.scenarios[0]?.customers.some((customer) => customer.tradeName === "Cliente Campo"),
      true,
    );

    const equipmentResponse = await app.inject({
      method: "GET",
      url: "/registry/equipment",
      headers: { cookie },
    });
    const equipmentPayload = equipmentRegistryCatalogSchema.parse(equipmentResponse.json());
    const createdEquipment = equipmentPayload.scenarios[0]?.items.find((item) => item.code === "EQ-050");
    assert.ok(createdEquipment);

    const archiveEquipment = await app.inject({
      method: "POST",
      url: "/registry/equipment/manage",
      headers: { cookie },
      payload: {
        action: "archive",
        equipmentId: createdEquipment?.equipmentId,
      },
    });
    assert.equal(archiveEquipment.statusCode, 204);

    const archivedEquipmentResponse = await app.inject({
      method: "GET",
      url: `/registry/equipment?equipment=${createdEquipment?.equipmentId}`,
      headers: { cookie },
    });
    const archivedEquipmentPayload = equipmentRegistryCatalogSchema.parse(
      archivedEquipmentResponse.json(),
    );
    assert.equal(archivedEquipmentPayload.scenarios[0]?.detail.status, "blocked");
  } finally {
    await app.close();
  }
});

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

    assert.equal(detailPayload.selectedScenarioId, "review-ready");
    assert.equal(detailPayload.scenarios[0]?.detail.itemId, createdItem?.itemId);
    assert.equal(detailPayload.scenarios[0]?.detail.status, "ready");
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

    const [dryRunResponse, reviewResponse, queueResponse, auditResponse] = await Promise.all([
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
    ]);

    assert.equal(dryRunResponse.statusCode, 200);
    assert.equal(reviewResponse.statusCode, 200);
    assert.equal(queueResponse.statusCode, 200);
    assert.equal(auditResponse.statusCode, 200);

    const dryRunPayload = emissionDryRunCatalogSchema.parse(dryRunResponse.json());
    const reviewPayload = reviewSignatureCatalogSchema.parse(reviewResponse.json());
    const queuePayload = signatureQueueCatalogSchema.parse(queueResponse.json());
    const auditPayload = auditTrailCatalogSchema.parse(auditResponse.json());

    assert.equal(dryRunPayload.scenarios.length, 3);
    assert.equal(reviewPayload.scenarios.length, 4);
    assert.equal(queuePayload.scenarios.length, 3);
    assert.equal(auditPayload.scenarios.length, 3);
  } finally {
    await app.close();
  }
});

test("approves and emits a persisted service order through the V3 workflow", async () => {
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

    const reviewResponse = await app.inject({
      method: "POST",
      url: "/emission/review-signature/manage",
      headers: { cookie },
      payload: {
        action: "review",
        serviceOrderId: "service-order-00142",
        reviewerUserId: "user-reviewer-1",
        signatoryUserId: "user-signatory-1",
        workflowStatus: "awaiting_signature",
        reviewDecision: "approved",
        reviewDecisionComment: "Revisao concluida sem ressalvas.",
        reviewDeviceId: "device-review-01",
      },
    });
    assert.equal(reviewResponse.statusCode, 204);

    const emitResponse = await app.inject({
      method: "POST",
      url: "/emission/signature-queue/manage",
      headers: { cookie },
      payload: {
        action: "emit",
        serviceOrderId: "service-order-00142",
        signatoryUserId: "user-signatory-1",
        signatureDeviceId: "device-sign-01",
      },
    });
    assert.equal(emitResponse.statusCode, 204);

    const queueResponse = await app.inject({
      method: "GET",
      url: "/emission/signature-queue?item=service-order-00142",
      headers: { cookie },
    });
    const auditResponse = await app.inject({
      method: "GET",
      url: "/quality/audit-trail?item=service-order-00142",
      headers: { cookie },
    });

    const queuePayload = signatureQueueCatalogSchema.parse(queueResponse.json());
    const auditPayload = auditTrailCatalogSchema.parse(auditResponse.json());

    assert.equal((queuePayload.scenarios[0]?.approval.documentHash?.length ?? 0) > 0, true);
    assert.match(queuePayload.scenarios[0]?.approval.compactPreview[3]?.value ?? "", /^LABPERSISTID/);
    assert.equal(auditPayload.selectedScenarioId, "recent-emission");
    assert.equal(auditPayload.scenarios[0]?.items.some((item) => item.actionLabel === "certificate.emitted"), true);
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
    const [adminLogin, portalLogin] = await Promise.all([
      app.inject({
        method: "POST",
        url: "/auth/login",
        payload: {
          email: "admin@afere.local",
          password: "Afere@2026!",
        },
      }),
      app.inject({
        method: "POST",
        url: "/auth/login",
        payload: {
          email: "marcia@paodoce.com.br",
          password: "Afere@2026!",
        },
      }),
    ]);

    const adminCookie = normalizeCookieHeader(adminLogin.headers["set-cookie"]);
    const portalCookie = normalizeCookieHeader(portalLogin.headers["set-cookie"]);
    assert.ok(adminCookie);
    assert.ok(portalCookie);

    const reissueResponse = await app.inject({
      method: "POST",
      url: "/emission/signature-queue/manage",
      headers: { cookie: adminCookie },
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

    const publications = await serviceOrderPersistence.listCertificatePublicationsByServiceOrder("service-order-00141");
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
    assert.equal((hubPayload.scenarios[0]?.summary.implementedModuleCount ?? 0) >= 6, true);
    assert.equal(settingsPayload.scenarios[0]?.summary.organizationCode, "AFERE");
  } finally {
    await app.close();
  }
});

test("updates persisted V5 nonconformity, indicator history and compliance profile through manage endpoints", async () => {
  const { runtimeReadiness } = createRuntimeReadinessStub();
  const qualityPersistence = createMemoryQualityPersistence(createV5QualitySeed());
  const app = await buildApp({
    env: TEST_ENV,
    runtimeReadiness,
    corePersistence: createMemoryCorePersistence(createV4CoreSeed()),
    registryPersistence: createMemoryRegistryPersistence(createV4RegistrySeed()),
    serviceOrderPersistence: createMemoryServiceOrderPersistence(createV4ServiceOrderSeed()),
    qualityPersistence,
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

    const [ncManage, indicatorManage, settingsManage] = await Promise.all([
      app.inject({
        method: "POST",
        url: "/quality/nonconformities/manage",
        headers: { cookie },
        payload: {
          action: "save",
          ncId: "nc-014",
          serviceOrderId: "service-order-00147",
          ownerUserId: "user-admin-1",
          title: "NC-014 · Segregacao revalidada",
          originLabel: "Revisao tecnica",
          severityLabel: "Moderada",
          status: "attention",
          noticeLabel: "A NC entrou em follow-up controlado.",
          rootCauseLabel: "Papéis regularizados e aguardando evidencia final.",
          containmentLabel: "Manter o bloqueio parcial ate anexar nova conferencia.",
          correctiveActionLabel: "Concluir checklist final e liberar revisao.",
          evidenceLabel: "Checklist final em andamento.",
          blockers: [],
          warnings: ["Ainda falta evidência final."],
          openedAt: "2026-04-23T13:20:00.000Z",
          dueAt: "2026-05-02T17:00:00.000Z",
        },
      }),
      app.inject({
        method: "POST",
        url: "/quality/indicators/manage",
        headers: { cookie },
        payload: {
          action: "save",
          indicatorId: "indicator-emission-completion",
          monthStart: "2026-05-01T00:00:00.000Z",
          valueNumeric: "78",
          targetNumeric: "85",
          status: "attention",
          sourceLabel: "Fechamento mensal 05/2026",
          evidenceLabel: "Consolidado gerencial aprovado para maio/2026.",
        },
      }),
      app.inject({
        method: "POST",
        url: "/settings/organization/manage",
        headers: { cookie },
        payload: {
          action: "save",
          regulatoryProfile: "type_a",
          organizationCode: "AFERE",
          planLabel: "Enterprise",
          certificatePrefix: "LABDEMO",
          accreditationNumber: "Cgcre CAL-1234",
          accreditationValidUntil: "2027-09-30T00:00:00.000Z",
          scopeSummary: "Escopo demo revisado.",
          cmcSummary: "CMC demo revisada.",
          scopeItemCount: "5",
          cmcItemCount: "5",
          legalOpinionStatus: "approved_reference",
          legalOpinionReference: "compliance/legal-opinions/2026-04-21-signature-auditability-opinion.md",
          dpaReference: "compliance/legal-opinions/dpa-template.md",
          normativeGovernanceStatus: "active",
          normativeGovernanceOwner: "product-governance",
          normativeGovernanceReference: "compliance/release-norm/pre-go-live-normative-governance.yaml",
          releaseNormVersion: "v5",
          releaseNormStatus: "local_pass",
          lastReviewedAt: "2026-04-23T21:00:00.000Z",
        },
      }),
    ]);

    assert.equal(ncManage.statusCode, 204);
    assert.equal(indicatorManage.statusCode, 204);
    assert.equal(settingsManage.statusCode, 204);

    const [ncResponse, indicatorResponse, settingsResponse] = await Promise.all([
      app.inject({ method: "GET", url: "/quality/nonconformities", headers: { cookie } }),
      app.inject({ method: "GET", url: "/quality/indicators?indicator=indicator-emission-completion", headers: { cookie } }),
      app.inject({ method: "GET", url: "/settings/organization", headers: { cookie } }),
    ]);

    const ncPayload = nonconformityRegistryCatalogSchema.parse(ncResponse.json());
    const indicatorPayload = qualityIndicatorRegistryCatalogSchema.parse(indicatorResponse.json());
    const settingsPayload = organizationSettingsCatalogSchema.parse(settingsResponse.json());

    assert.equal(ncPayload.scenarios[0]?.items[0]?.summary, "NC-014 · Segregacao revalidada");
    assert.match(
      indicatorPayload.scenarios.flatMap((scenario) => scenario.detail.snapshots.map((snapshot) => snapshot.monthLabel)).join(" "),
      /05\/2026/i,
    );
    assert.equal(
      settingsPayload.scenarios[0]?.summary.profileLabel.includes("Tipo A"),
      true,
    );
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

function normalizeCookieHeader(value: string | string[] | undefined) {
  if (Array.isArray(value)) {
    return value[0]?.split(";")[0] ?? "";
  }

  return value?.split(";")[0] ?? "";
}

function createV1MemorySeed() {
  return {
    users: [
      {
        userId: "user-admin-1",
        organizationId: "org-1",
        organizationName: "Laboratorio Persistido",
        organizationSlug: "lab-persistido",
        email: "admin@afere.local",
        passwordHash: hashPassword("Afere@2026!", "seed-admin"),
        displayName: "Ana Administradora",
        roles: ["admin", "quality_manager"] as MembershipRole[],
        status: "active" as const,
        teamName: "Gestao tecnica",
        mfaEnforced: true,
        mfaEnrolled: true,
        deviceCount: 2,
        competencies: [
          {
            instrumentType: "balanca",
            roleLabel: "Gestao",
            status: "authorized" as const,
            validUntilUtc: "2027-01-01T00:00:00.000Z",
          },
        ],
      },
      {
        userId: "user-reviewer-1",
        organizationId: "org-1",
        organizationName: "Laboratorio Persistido",
        organizationSlug: "lab-persistido",
        email: "revisora@afere.local",
        passwordHash: hashPassword("Afere@2026!", "seed-reviewer"),
        displayName: "Renata Revisora",
        roles: ["technical_reviewer"] as MembershipRole[],
        status: "active" as const,
        teamName: "Qualidade",
        mfaEnforced: true,
        mfaEnrolled: true,
        deviceCount: 1,
        competencies: [
          {
            instrumentType: "balanca",
            roleLabel: "Revisora tecnica",
            status: "authorized" as const,
            validUntilUtc: "2027-03-01T00:00:00.000Z",
          },
        ],
      },
      {
        userId: "user-signatory-1",
        organizationId: "org-1",
        organizationName: "Laboratorio Persistido",
        organizationSlug: "lab-persistido",
        email: "signatario@afere.local",
        passwordHash: hashPassword("Afere@2026!", "seed-signatory"),
        displayName: "Bruno Signatario",
        roles: ["signatory", "technical_reviewer"] as MembershipRole[],
        status: "active" as const,
        teamName: "Metrologia",
        mfaEnforced: true,
        mfaEnrolled: true,
        deviceCount: 1,
        competencies: [
          {
            instrumentType: "balanca",
            roleLabel: "Signatario",
            status: "authorized" as const,
            validUntilUtc: "2027-02-01T00:00:00.000Z",
          },
        ],
      },
    ],
    onboarding: [
      {
        organizationId: "org-1",
        organizationName: "Laboratorio Persistido",
        organizationSlug: "lab-persistido",
        regulatoryProfile: "type_b",
        normativePackageVersion: "2026-04-20-baseline-v0.1.0",
        startedAtUtc: "2026-04-23T12:00:00.000Z",
        organizationProfileCompleted: true,
        primarySignatoryReady: false,
        certificateNumberingConfigured: false,
        scopeReviewCompleted: false,
        publicQrConfigured: false,
      },
    ],
  };
}

function createV2RegistrySeed() {
  return {
    customers: [
      {
        customerId: "customer-001",
        organizationId: "org-1",
        legalName: "Lab. Acme Analises Ltda.",
        tradeName: "Lab. Acme",
        documentLabel: "12.345.678/0001-XX",
        segmentLabel: "Laboratorio clinico",
        accountOwnerName: "Joao das Neves",
        accountOwnerEmail: "joao@lab-acme.com.br",
        contractLabel: "Contrato vigente ate 31/12/2026",
        specialConditionsLabel: "Sala climatizada 21 +/- 2 C",
        contactName: "Joao das Neves",
        contactRoleLabel: "Responsavel tecnico",
        contactEmail: "joao@lab-acme.com.br",
        contactPhoneLabel: "(65) 99999-0001",
        addressLine1: "Rua da Calibracao, 100",
        addressCity: "Cuiaba",
        addressState: "MT",
        addressPostalCode: "78000-000",
        addressCountry: "Brasil",
        addressConditionsLabel: "Acesso controlado",
        createdAtUtc: "2026-04-10T12:00:00.000Z",
        updatedAtUtc: "2026-04-23T12:00:00.000Z",
      },
    ],
    standards: [
      {
        standardId: "standard-001",
        organizationId: "org-1",
        code: "PESO-001",
        title: "Peso padrao 1 kg",
        kindLabel: "Peso",
        nominalClassLabel: "1 kg · F1",
        sourceLabel: "RBC-1234",
        certificateLabel: "1234/25/081",
        manufacturerLabel: "Coelmatic",
        modelLabel: "M1K",
        serialNumberLabel: "9-22-101",
        nominalValueLabel: "1,000 kg",
        classLabel: "F1",
        usageRangeLabel: "0 kg ate 1 kg",
        measurementValue: 1,
        applicableRangeMin: 0,
        applicableRangeMax: 1,
        uncertaintyLabel: "+/- 8 mg",
        correctionFactorLabel: "+0,001 g",
        hasValidCertificate: true,
        certificateValidUntilUtc: "2026-08-12T00:00:00.000Z",
        createdAtUtc: "2026-04-10T12:00:00.000Z",
        updatedAtUtc: "2026-04-23T12:00:00.000Z",
        calibrations: [
          {
            calibratedAtUtc: "2025-08-12T00:00:00.000Z",
            laboratoryLabel: "Lab Cal-1234",
            certificateLabel: "1234/25/081",
            sourceLabel: "RBC",
            uncertaintyLabel: "+/- 8 mg",
            validUntilUtc: "2026-08-12T00:00:00.000Z",
          },
        ],
      },
    ],
    procedures: [
      {
        procedureId: "procedure-001",
        organizationId: "org-1",
        code: "PT-005",
        title: "Calibracao IPNA classe III campo",
        typeLabel: "NAWI III",
        revisionLabel: "04",
        effectiveSinceUtc: "2026-03-01T00:00:00.000Z",
        lifecycleLabel: "Vigente",
        usageLabel: "Campo controlado",
        scopeLabel: "Balancas IPNA classe III ate 300 kg.",
        environmentRangeLabel: "Temp 18C-25C · Umid 30%-70%",
        curvePolicyLabel: "5 pontos com subida e descida",
        standardsPolicyLabel: "Peso F1 ou M1 vigente",
        approvalLabel: "Aprovado por Ana Administradora",
        relatedDocuments: ["IT-005", "FR-021"],
        createdAtUtc: "2026-04-10T12:00:00.000Z",
        updatedAtUtc: "2026-04-23T12:00:00.000Z",
      },
    ],
    equipment: [
      {
        equipmentId: "equipment-001",
        organizationId: "org-1",
        customerId: "customer-001",
        procedureId: "procedure-001",
        primaryStandardId: "standard-001",
        code: "EQ-0007",
        tagCode: "BAL-007",
        serialNumber: "SN-300-01",
        typeModelLabel: "NAWI Toledo Prix 3",
        capacityClassLabel: "300 kg · 0,05 kg · III",
        supportingStandardCodes: ["PESO-001"],
        addressLine1: "Rua da Calibracao, 100",
        addressCity: "Cuiaba",
        addressState: "MT",
        addressPostalCode: "78000-000",
        addressCountry: "Brasil",
        addressConditionsLabel: "Sala climatizada",
        lastCalibrationAtUtc: "2026-04-18T00:00:00.000Z",
        nextCalibrationAtUtc: "2026-10-18T00:00:00.000Z",
        createdAtUtc: "2026-04-10T12:00:00.000Z",
        updatedAtUtc: "2026-04-23T12:00:00.000Z",
      },
    ],
    auditEvents: [
      {
        entityType: "customer" as const,
        entityId: "customer-001",
        action: "update",
        summary: "Cadastro do cliente Lab. Acme revisado na V2.",
        createdAtUtc: "2026-04-23T12:00:00.000Z",
      },
    ],
  };
}

function createV3CoreSeed() {
  const seed = createV1MemorySeed();
  return {
    ...seed,
    onboarding: seed.onboarding.map((record) => ({
      ...record,
      primarySignatoryReady: true,
      certificateNumberingConfigured: true,
      scopeReviewCompleted: true,
      publicQrConfigured: true,
    })),
  };
}

function createV3ServiceOrderSeed() {
  return {
    users: [
      {
        userId: "user-admin-1",
        organizationId: "org-1",
        displayName: "Ana Administradora",
        status: "active" as const,
      },
      {
        userId: "user-reviewer-1",
        organizationId: "org-1",
        displayName: "Renata Revisora",
        status: "active" as const,
      },
      {
        userId: "user-signatory-1",
        organizationId: "org-1",
        displayName: "Bruno Signatario",
        status: "active" as const,
      },
    ],
    customers: [
      {
        customerId: "customer-001",
        organizationId: "org-1",
        tradeName: "Lab. Acme",
        addressLine1: "Rua da Calibracao, 100",
        addressCity: "Cuiaba",
        addressState: "MT",
        addressPostalCode: "78000-000",
        addressCountry: "Brasil",
      },
    ],
    equipment: [
      {
        equipmentId: "equipment-001",
        organizationId: "org-1",
        customerId: "customer-001",
        procedureId: "procedure-001",
        primaryStandardId: "standard-001",
        code: "EQ-0007",
        tagCode: "BAL-007",
        serialNumber: "SN-300-01",
        typeModelLabel: "NAWI Toledo Prix 3",
      },
    ],
    procedures: [
      {
        procedureId: "procedure-001",
        organizationId: "org-1",
        code: "PT-005",
        revisionLabel: "04",
      },
    ],
    standards: [
      {
        standardId: "standard-001",
        organizationId: "org-1",
        code: "PESO-001",
        title: "Peso padrao 1 kg",
        sourceLabel: "RBC-1234",
        certificateLabel: "1234/25/081",
        hasValidCertificate: true,
        certificateValidUntilUtc: "2026-08-12T00:00:00.000Z",
        measurementValue: 1,
        applicableRangeMin: 0,
        applicableRangeMax: 1,
      },
    ],
    serviceOrders: [
      {
        serviceOrderId: "service-order-00142",
        organizationId: "org-1",
        customerId: "customer-001",
        customerName: "Lab. Acme",
        customerAddress: {
          line1: "Rua da Calibracao, 100",
          city: "Cuiaba",
          state: "MT",
          postalCode: "78000-000",
          country: "Brasil",
        },
        equipmentId: "equipment-001",
        equipmentLabel: "EQ-0007 · NAWI Toledo Prix 3",
        equipmentCode: "EQ-0007",
        equipmentTagCode: "BAL-007",
        equipmentSerialNumber: "SN-300-01",
        instrumentType: "balanca",
        procedureId: "procedure-001",
        procedureLabel: "PT-005 rev.04",
        primaryStandardId: "standard-001",
        standardsLabel: "PESO-001 · Peso padrao 1 kg",
        standardSource: "RBC" as const,
        standardCertificateReference: "1234/25/081",
        standardHasValidCertificate: true,
        standardCertificateValidUntilUtc: "2026-08-12T00:00:00.000Z",
        standardMeasurementValue: 1,
        standardApplicableRange: {
          minimum: 0,
          maximum: 1,
        },
        executorUserId: "user-admin-1",
        executorName: "Ana Administradora",
        reviewerUserId: "user-reviewer-1",
        reviewerName: "Renata Revisora",
        signatoryUserId: "user-signatory-1",
        signatoryName: "Bruno Signatario",
        workOrderNumber: "OS-2026-00142",
        workflowStatus: "awaiting_review" as const,
        environmentLabel: "22,1 C · 48% UR · pressao estavel",
        curvePointsLabel: "5 pontos (10% / 25% / 50% / 75% / 100%)",
        evidenceLabel: "12 evidencias anexadas",
        uncertaintyLabel: "U = 0,12 kg (k=2)",
        conformityLabel: "Aprovado com banda de guarda de 50%",
        measurementResultValue: 152.48,
        measurementExpandedUncertaintyValue: 0.12,
        measurementCoverageFactor: 2,
        measurementUnit: "kg",
        decisionRuleLabel: "ILAC G8 com banda de guarda",
        decisionOutcomeLabel: "Conforme",
        freeTextStatement: "Resultado dentro da faixa operacional declarada.",
        commentDraft: "Curva coerente com o historico do equipamento e pronta para revisao tecnica.",
        reviewDecision: "pending" as const,
        reviewDecisionComment: "",
        createdAtUtc: "2026-04-12T12:01:00.000Z",
        acceptedAtUtc: "2026-04-12T12:15:00.000Z",
        executionStartedAtUtc: "2026-04-19T14:00:00.000Z",
        executedAtUtc: "2026-04-19T17:22:00.000Z",
        reviewStartedAtUtc: "2026-04-23T11:30:00.000Z",
        updatedAtUtc: "2026-04-23T11:30:00.000Z",
      },
    ],
  };
}

function createV4CoreSeed() {
  const seed = createV3CoreSeed();

  return {
    ...seed,
    users: [
      ...seed.users,
      {
        userId: "user-external-client-1",
        organizationId: "org-1",
        organizationName: "Laboratorio Persistido",
        organizationSlug: "lab-persistido",
        email: "marcia@paodoce.com.br",
        passwordHash: hashPassword("Afere@2026!", "seed-external-client"),
        displayName: "Marcia Lima",
        roles: ["external_client"] as MembershipRole[],
        status: "active" as const,
        teamName: "Cliente",
        mfaEnforced: false,
        mfaEnrolled: false,
        deviceCount: 1,
        competencies: [],
      },
    ],
  };
}

function createV4RegistrySeed() {
  const seed = createV2RegistrySeed();

  return {
    ...seed,
    customers: [
      ...seed.customers,
      {
        customerId: "customer-002",
        organizationId: "org-1",
        legalName: "Padaria Pao Doce Comercio Ltda.",
        tradeName: "Padaria Pao Doce",
        documentLabel: "23.456.789/0001-YY",
        segmentLabel: "Panificacao",
        accountOwnerName: "Marcia Lima",
        accountOwnerEmail: "marcia@paodoce.com.br",
        contractLabel: "Contrato vigente ate 30/11/2026",
        specialConditionsLabel: "Atendimento antes da abertura da loja",
        contactName: "Marcia Lima",
        contactRoleLabel: "Responsavel administrativa",
        contactEmail: "marcia@paodoce.com.br",
        contactPhoneLabel: "(65) 99999-1101",
        addressLine1: "Avenida do Comercio, 45",
        addressCity: "Cuiaba",
        addressState: "MT",
        addressPostalCode: "78005-010",
        addressCountry: "Brasil",
        addressConditionsLabel: "Atendimento antes das 6h para nao interromper a producao.",
        createdAtUtc: "2026-04-10T12:00:00.000Z",
        updatedAtUtc: "2026-04-23T12:00:00.000Z",
      },
    ],
    equipment: [
      ...seed.equipment,
      {
        equipmentId: "equipment-00141",
        organizationId: "org-1",
        customerId: "customer-002",
        procedureId: "procedure-001",
        primaryStandardId: "standard-001",
        code: "EQ-00141",
        tagCode: "BAL-141",
        serialNumber: "SN-141-02",
        typeModelLabel: "Balanca Prix 4 Uno 30 kg",
        capacityClassLabel: "30 kg · 0,005 kg · III",
        supportingStandardCodes: ["PESO-001"],
        addressLine1: "Avenida do Comercio, 45",
        addressCity: "Cuiaba",
        addressState: "MT",
        addressPostalCode: "78005-010",
        addressCountry: "Brasil",
        addressConditionsLabel: "Atendimento antes da abertura.",
        lastCalibrationAtUtc: "2026-04-20T00:00:00.000Z",
        nextCalibrationAtUtc: "2026-10-20T00:00:00.000Z",
        createdAtUtc: "2026-04-10T12:00:00.000Z",
        updatedAtUtc: "2026-04-23T12:00:00.000Z",
      },
    ],
    auditEvents: [
      ...seed.auditEvents,
      {
        entityType: "equipment" as const,
        entityId: "equipment-00141",
        action: "update",
        summary: "Equipamento da carteira do portal vinculado ao cliente externo seed.",
        createdAtUtc: "2026-04-23T13:00:00.000Z",
      },
    ],
  };
}

function createV4ServiceOrderSeed() {
  const seed = createV3ServiceOrderSeed();

  return {
    ...seed,
    customers: [
      ...seed.customers,
      {
        customerId: "customer-002",
        organizationId: "org-1",
        tradeName: "Padaria Pao Doce",
        addressLine1: "Avenida do Comercio, 45",
        addressCity: "Cuiaba",
        addressState: "MT",
        addressPostalCode: "78005-010",
        addressCountry: "Brasil",
      },
    ],
    equipment: [
      ...seed.equipment,
      {
        equipmentId: "equipment-00141",
        organizationId: "org-1",
        customerId: "customer-002",
        procedureId: "procedure-001",
        primaryStandardId: "standard-001",
        code: "EQ-00141",
        tagCode: "BAL-141",
        serialNumber: "SN-141-02",
        typeModelLabel: "Balanca Prix 4 Uno 30 kg",
      },
    ],
    serviceOrders: [
      ...seed.serviceOrders,
      {
        serviceOrderId: "service-order-00141",
        organizationId: "org-1",
        customerId: "customer-002",
        customerName: "Padaria Pao Doce",
        customerAddress: {
          line1: "Avenida do Comercio, 45",
          city: "Cuiaba",
          state: "MT",
          postalCode: "78005-010",
          country: "Brasil",
        },
        equipmentId: "equipment-00141",
        equipmentLabel: "EQ-00141 · Balanca Prix 4 Uno 30 kg",
        equipmentCode: "EQ-00141",
        equipmentTagCode: "BAL-141",
        equipmentSerialNumber: "SN-141-02",
        instrumentType: "balanca",
        procedureId: "procedure-001",
        procedureLabel: "PT-005 rev.04",
        primaryStandardId: "standard-001",
        standardsLabel: "PESO-001 · Peso padrao 1 kg",
        standardSource: "RBC" as const,
        standardCertificateReference: "1234/25/081",
        standardHasValidCertificate: true,
        standardCertificateValidUntilUtc: "2026-08-12T00:00:00.000Z",
        standardMeasurementValue: 1,
        standardApplicableRange: {
          minimum: 0,
          maximum: 1,
        },
        executorUserId: "user-admin-1",
        executorName: "Ana Administradora",
        reviewerUserId: "user-reviewer-1",
        reviewerName: "Renata Revisora",
        signatoryUserId: "user-signatory-1",
        signatoryName: "Bruno Signatario",
        workOrderNumber: "OS-2026-00141",
        workflowStatus: "emitted" as const,
        environmentLabel: "23,0 C · 52% UR · atendimento antes da abertura",
        curvePointsLabel: "4 pontos com repetibilidade em 50%",
        evidenceLabel: "11 evidencias registradas",
        uncertaintyLabel: "U = 0,08 kg (k=2)",
        conformityLabel: "Aprovado sem restricoes adicionais",
        measurementResultValue: 29.998,
        measurementExpandedUncertaintyValue: 0.08,
        measurementCoverageFactor: 2,
        measurementUnit: "kg",
        decisionRuleLabel: "ILAC G8 sem banda de guarda adicional",
        decisionOutcomeLabel: "Conforme",
        freeTextStatement: "Certificado emitido com base em revisao tecnica concluida e assinatura valida.",
        commentDraft: "Historico estavel e repetibilidade dentro do criterio de aceitacao.",
        reviewDecision: "approved" as const,
        reviewDecisionComment: "Revisao aprovada e liberada para emissao oficial.",
        reviewDeviceId: "device-review-02",
        signatureDeviceId: "device-sign-02",
        signatureStatement: "Assinatura eletronica concluida por Bruno Signatario.",
        certificateNumber: "LABPERSISTID-000141",
        certificateRevision: "R0",
        publicVerificationToken: "pubtok-os141",
        documentHash: "1411411411411411411411411411411411411411411411411411411411411411",
        qrHost: "lab-persistido.afere.local",
        createdAtUtc: "2026-04-12T11:42:00.000Z",
        acceptedAtUtc: "2026-04-12T12:03:00.000Z",
        executionStartedAtUtc: "2026-04-19T13:10:00.000Z",
        executedAtUtc: "2026-04-19T15:40:00.000Z",
        reviewStartedAtUtc: "2026-04-20T08:40:00.000Z",
        reviewCompletedAtUtc: "2026-04-20T09:10:00.000Z",
        signatureStartedAtUtc: "2026-04-20T09:18:00.000Z",
        signedAtUtc: "2026-04-20T09:22:00.000Z",
        emittedAtUtc: "2026-04-20T09:23:00.000Z",
        updatedAtUtc: "2026-04-20T09:23:00.000Z",
      },
    ],
    certificatePublications: [
      {
        publicationId: "publication-00141-r0",
        organizationId: "org-1",
        serviceOrderId: "service-order-00141",
        customerId: "customer-002",
        customerName: "Padaria Pao Doce",
        equipmentId: "equipment-00141",
        equipmentLabel: "EQ-00141 · Balanca Prix 4 Uno 30 kg",
        equipmentTagCode: "BAL-141",
        equipmentSerialNumber: "SN-141-02",
        workOrderNumber: "OS-2026-00141",
        certificateNumber: "LABPERSISTID-000141",
        revision: "R0",
        publicVerificationToken: "pubtok-os141",
        documentHash: "1411411411411411411411411411411411411411411411411411411411411411",
        qrHost: "lab-persistido.afere.local",
        signedAtUtc: "2026-04-20T09:22:00.000Z",
        issuedAtUtc: "2026-04-20T09:23:00.000Z",
        createdAtUtc: "2026-04-20T09:23:00.000Z",
        updatedAtUtc: "2026-04-20T09:23:00.000Z",
      },
    ],
    emissionAuditEvents: buildSeedEmissionAuditTrail("service-order-00141", [
      {
        eventId: "audit-00141-0",
        action: "calibration.executed",
        actorUserId: "user-admin-1",
        actorLabel: "Ana Administradora",
        entityLabel: "OS-2026-00141",
        occurredAtUtc: "2026-04-19T15:40:00.000Z",
      },
      {
        eventId: "audit-00141-1",
        action: "technical_review.completed",
        actorUserId: "user-reviewer-1",
        actorLabel: "Renata Revisora",
        entityLabel: "OS-2026-00141",
        deviceId: "device-review-02",
        occurredAtUtc: "2026-04-20T09:10:00.000Z",
      },
      {
        eventId: "audit-00141-2",
        action: "certificate.signed",
        actorUserId: "user-signatory-1",
        actorLabel: "Bruno Signatario",
        entityLabel: "OS-2026-00141",
        deviceId: "device-sign-02",
        certificateNumber: "LABPERSISTID-000141",
        occurredAtUtc: "2026-04-20T09:22:00.000Z",
      },
      {
        eventId: "audit-00141-3",
        action: "certificate.emitted",
        actorUserId: "user-signatory-1",
        actorLabel: "Bruno Signatario",
        entityLabel: "OS-2026-00141",
        deviceId: "device-sign-02",
        certificateNumber: "LABPERSISTID-000141",
        occurredAtUtc: "2026-04-20T09:23:00.000Z",
      },
    ]),
  };
}

function createV5QualitySeed() {
  return {
    nonconformities: [
      {
        ncId: "nc-014",
        organizationId: "org-1",
        serviceOrderId: "service-order-00147",
        workOrderNumber: "OS-2026-00147",
        ownerUserId: "user-admin-1",
        ownerLabel: "Ana Administradora",
        title: "NC-014 · Revisor conflitado e padrao vencido na OS bloqueada",
        originLabel: "Revisao tecnica",
        severityLabel: "Critica",
        status: "blocked" as const,
        noticeLabel: "A OS permanece bloqueada ate segregar funcoes e regularizar o padrao principal.",
        rootCauseLabel: "Atribuicao inadequada de papeis somada a uso de padrao fora da validade.",
        containmentLabel: "Suspender qualquer liberacao da OS-2026-00147.",
        correctiveActionLabel: "Substituir o revisor, recalibrar o padrao e registrar nova conferencia.",
        evidenceLabel: "OS-2026-00147 e trilha append-only.",
        blockers: ["Segregacao de funcoes pendente", "Padrao principal vencido"],
        warnings: ["Nao emitir certificado ate fechar a NC."],
        openedAtUtc: "2026-04-23T13:20:00.000Z",
        dueAtUtc: "2026-04-30T17:00:00.000Z",
      },
    ],
    nonconformingWork: [
      {
        caseId: "ncw-014",
        organizationId: "org-1",
        serviceOrderId: "service-order-00147",
        workOrderNumber: "OS-2026-00147",
        nonconformityId: "nc-014",
        title: "NCW-014 · Contencao da OS-2026-00147",
        classificationLabel: "Contencao preventiva",
        originLabel: "OS bloqueada",
        affectedEntityLabel: "OS-2026-00147",
        status: "blocked" as const,
        noticeLabel: "Liberacao do fluxo bloqueada ate nova evidencia minima.",
        containmentLabel: "Manter a OS congelada.",
        releaseRuleLabel: "Somente liberar apos NC encerrada.",
        evidenceLabel: "Registro da NC-014 e trilha de revisao.",
        restorationLabel: "Retomar apenas com novo revisor e padrao valido.",
        blockers: ["NC-014 aberta"],
        warnings: ["Nao substituir a contencao por acordo verbal."],
        createdAtUtc: "2026-04-23T14:00:00.000Z",
        updatedAtUtc: "2026-04-23T14:10:00.000Z",
      },
    ],
    internalAuditCycles: [
      {
        cycleId: "audit-cycle-2026-q2",
        organizationId: "org-1",
        cycleLabel: "Programa 2026 · Ciclo 2",
        windowLabel: "Q2 2026",
        scopeLabel: "§7.8 Certificados | §7.10 Trabalho nao conforme",
        auditorLabel: "Ana Administradora",
        auditeeLabel: "Operacoes e Qualidade",
        periodLabel: "Abr-Jun 2026",
        reportLabel: "Relatorio parcial do ciclo 2 em follow-up",
        evidenceLabel: "Checklist do ciclo, NC-014 e trilha da OS-2026-00147.",
        nextReviewLabel: "05/05/2026 13:00 UTC",
        noticeLabel: "O ciclo permanece aberto ate concluir o follow-up da NC critica.",
        status: "attention" as const,
        checklist: [
          {
            key: "certificates",
            requirementLabel: "Certificados emitidos e bloqueados com evidencias rastreaveis",
            evidenceLabel: "service_orders + emission_audit_events",
            status: "attention" as const,
          },
          {
            key: "nonconforming-work",
            requirementLabel: "Contencao formal do trabalho nao conforme",
            evidenceLabel: "nonconforming_work_cases + NC-014",
            status: "blocked" as const,
          },
        ],
        findingRefs: ["nc-014"],
        blockers: ["NC critica ainda sem encerramento"],
        warnings: ["Nao abrir novo ciclo sem concluir o follow-up atual."],
        scheduledAtUtc: "2026-04-24T14:00:00.000Z",
      },
    ],
    managementReviewMeetings: [
      {
        meetingId: "review-2026-q2",
        organizationId: "org-1",
        titleLabel: "Analise critica Q2 2026",
        status: "attention" as const,
        dateLabel: "30/06/2026",
        outcomeLabel: "Pauta aberta com follow-up de Qualidade",
        noticeLabel: "A ata final depende do fechamento minimo da NC critica e do ciclo de auditoria.",
        nextMeetingLabel: "30/09/2026",
        chairLabel: "Ana Administradora",
        attendeesLabel: "Direcao, Qualidade e Metrologia",
        periodLabel: "Q2 2026",
        ataLabel: "Ata em preparacao",
        evidenceLabel: "Indicadores V5, NC-014, auditoria e perfil regulatorio persistido.",
        agendaItems: [
          { key: "agenda-nc", label: "NCs e trabalho nao conforme", status: "attention" as const },
          { key: "agenda-audit", label: "Follow-up da auditoria interna", status: "attention" as const },
        ],
        decisions: [
          {
            key: "decision-close-nc",
            label: "Encerrar NC-014 com evidencias minimas",
            ownerLabel: "Ana Administradora",
            dueDateLabel: "05/05/2026",
            status: "attention" as const,
          },
        ],
        blockers: [],
        warnings: ["A ata nao deve ser arquivada antes do follow-up minimo da NC."],
        scheduledForUtc: "2026-06-30T13:00:00.000Z",
      },
    ],
    qualityIndicatorSnapshots: buildV5IndicatorHistorySeed(),
    complianceProfiles: [
      {
        complianceProfileId: "compliance-profile-v5",
        organizationId: "org-1",
        organizationName: "Laboratorio Persistido",
        organizationSlug: "lab-persistido",
        regulatoryProfile: "type_b",
        normativePackageVersion: "2026-04-20-baseline-v0.1.0",
        organizationCode: "AFERE",
        planLabel: "Enterprise",
        certificatePrefix: "LABDEMO",
        accreditationNumber: "Cgcre CAL-1234",
        accreditationValidUntilUtc: "2027-09-30T00:00:00.000Z",
        scopeSummary: "Escopo demo controlado para balancas.",
        cmcSummary: "CMC demo revisada para o tenant persistido.",
        scopeItemCount: 4,
        cmcItemCount: 4,
        legalOpinionStatus: "approved_reference",
        legalOpinionReference: "compliance/legal-opinions/2026-04-21-signature-auditability-opinion.md",
        dpaReference: "compliance/legal-opinions/dpa-template.md",
        normativeGovernanceStatus: "active",
        normativeGovernanceOwner: "product-governance",
        normativeGovernanceReference: "compliance/release-norm/pre-go-live-normative-governance.yaml",
        releaseNormVersion: "v5",
        releaseNormStatus: "pending_local_validation",
        lastReviewedAtUtc: "2026-04-23T20:30:00.000Z",
      },
    ],
  };
}

function buildV5IndicatorHistorySeed() {
  return [
    ...buildIndicatorHistorySeed({
      indicatorId: "indicator-emission-completion",
      targetNumeric: 85,
      points: [
        ["2025-11-01T00:00:00.000Z", 62, "attention"],
        ["2025-12-01T00:00:00.000Z", 68, "attention"],
        ["2026-01-01T00:00:00.000Z", 72, "attention"],
        ["2026-02-01T00:00:00.000Z", 79, "attention"],
        ["2026-03-01T00:00:00.000Z", 81, "attention"],
        ["2026-04-01T00:00:00.000Z", 84, "attention"],
      ],
      sourcePrefix: "Fechamento mensal emissao",
      evidenceLabel: "Consolidado gerencial do fluxo emitido.",
    }),
    ...buildIndicatorHistorySeed({
      indicatorId: "indicator-open-nc-pressure",
      targetNumeric: 1,
      points: [
        ["2025-11-01T00:00:00.000Z", 3, "blocked"],
        ["2025-12-01T00:00:00.000Z", 3, "blocked"],
        ["2026-01-01T00:00:00.000Z", 2, "attention"],
        ["2026-02-01T00:00:00.000Z", 2, "attention"],
        ["2026-03-01T00:00:00.000Z", 1, "ready"],
        ["2026-04-01T00:00:00.000Z", 1, "ready"],
      ],
      sourcePrefix: "Fechamento mensal NC",
      evidenceLabel: "Consolidado mensal de nao conformidades.",
    }),
    ...buildIndicatorHistorySeed({
      indicatorId: "indicator-governance-follow-up",
      targetNumeric: 1,
      points: [
        ["2025-11-01T00:00:00.000Z", 4, "blocked"],
        ["2025-12-01T00:00:00.000Z", 3, "blocked"],
        ["2026-01-01T00:00:00.000Z", 3, "blocked"],
        ["2026-02-01T00:00:00.000Z", 2, "attention"],
        ["2026-03-01T00:00:00.000Z", 2, "attention"],
        ["2026-04-01T00:00:00.000Z", 1, "ready"],
      ],
      sourcePrefix: "Fechamento mensal follow-up",
      evidenceLabel: "Consolidado mensal de follow-up gerencial.",
    }),
  ];
}

function buildIndicatorHistorySeed(input: {
  indicatorId: string;
  targetNumeric: number;
  points: Array<[monthStartUtc: string, valueNumeric: number, status: "ready" | "attention" | "blocked"]>;
  sourcePrefix: string;
  evidenceLabel: string;
}) {
  return input.points.map(([monthStartUtc, valueNumeric, status], index) => ({
    snapshotId: `${input.indicatorId}-${monthStartUtc.slice(0, 7)}`,
    organizationId: "org-1",
    indicatorId: input.indicatorId,
    monthStartUtc,
    valueNumeric,
    targetNumeric: input.targetNumeric,
    status,
    sourceLabel: `${input.sourcePrefix} ${monthStartUtc.slice(5, 7)}/${monthStartUtc.slice(0, 4)}`,
    evidenceLabel: input.evidenceLabel,
    createdAtUtc: new Date(Date.parse(monthStartUtc) + 24 * 60 * 60 * 1000).toISOString(),
    updatedAtUtc: new Date(Date.parse(monthStartUtc) + (index + 2) * 24 * 60 * 60 * 1000).toISOString(),
  }));
}

function buildSeedEmissionAuditTrail(
  serviceOrderId: string,
  events: Array<{
    eventId: string;
    action: string;
    actorUserId?: string;
    actorLabel: string;
    entityLabel: string;
    deviceId?: string;
    certificateNumber?: string;
    occurredAtUtc: string;
  }>,
) {
  let prevHash = "0".repeat(64);

  return events.map((event) => {
    const hash = computeAuditHash(prevHash, {
      action: event.action,
      actorId: event.actorUserId,
      actorLabel: event.actorLabel,
      certificateId: serviceOrderId,
      certificateNumber: event.certificateNumber,
      entityLabel: event.entityLabel,
      timestampUtc: event.occurredAtUtc,
      deviceId: event.deviceId,
    });

    const row = {
      eventId: event.eventId,
      organizationId: "org-1",
      serviceOrderId,
      workOrderNumber: event.entityLabel,
      actorUserId: event.actorUserId,
      actorLabel: event.actorLabel,
      action: event.action,
      entityLabel: event.entityLabel,
      deviceId: event.deviceId,
      certificateNumber: event.certificateNumber,
      prevHash,
      hash,
      occurredAtUtc: event.occurredAtUtc,
    };

    prevHash = hash;
    return row;
  });
}
