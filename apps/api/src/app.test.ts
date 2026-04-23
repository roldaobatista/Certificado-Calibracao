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
