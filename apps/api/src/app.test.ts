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
