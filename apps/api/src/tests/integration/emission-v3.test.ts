import { Prisma } from "@prisma/client";
import assert from "node:assert/strict";
import { test } from "node:test";

import { computeAuditHash } from "@afere/audit-log";
import { hashPassword } from "../../domain/auth/password.js";

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

test("exports the canonical management review meeting as .ics", async () => {
  const { runtimeReadiness } = createRuntimeReadinessStub();
  const app = await buildApp({ env: TEST_ENV, runtimeReadiness });

  try {
    const response = await app.inject({
      method: "GET",
      url: "/quality/management-review/calendar.ics?scenario=extraordinary-response&meeting=review-extra-2026-04",
    });

    assert.equal(response.statusCode, 200);
    assert.match(String(response.headers["content-type"] ?? ""), /text\/calendar/i);
    assert.match(response.body, /BEGIN:VCALENDAR/);
    assert.match(response.body, /SUMMARY:Analise critica extraordinaria 04\/2026/);
    assert.match(response.body, /DTSTART:20260423T140000Z/);
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


test("renders the preliminary uncertainty budget in persisted review and preview", async () => {
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

    const [reviewResponse, previewResponse] = await Promise.all([
      app.inject({
        method: "GET",
        url: "/emission/service-order-review?item=service-order-00142",
        headers: { cookie },
      }),
      app.inject({
        method: "GET",
        url: "/emission/certificate-preview?item=service-order-00142",
        headers: { cookie },
      }),
    ]);

    assert.equal(reviewResponse.statusCode, 200);
    assert.equal(previewResponse.statusCode, 200);

    const reviewPayload = serviceOrderReviewCatalogSchema.parse(reviewResponse.json());
    const previewPayload = certificatePreviewCatalogSchema.parse(previewResponse.json());
    const reviewScenario = reviewPayload.scenarios.find(
      (scenario) => scenario.id === reviewPayload.selectedScenarioId,
    );
    const previewScenario = previewPayload.scenarios.find(
      (scenario) => scenario.id === previewPayload.selectedScenarioId,
    );

    assert.ok(reviewScenario);
    assert.ok(previewScenario);
    assert.equal(
      reviewScenario.detail.checklist.some(
        (item) =>
          item.label === "Orcamento preliminar de incerteza" &&
          item.status === "passed",
      ),
      true,
    );
    assert.equal(
      reviewScenario.detail.metrics.some(
        (metric) => metric.label === "Pre-calculo U" && /kg/i.test(metric.value),
      ),
      true,
    );
    assert.equal(
      reviewScenario.detail.metrics.some(
        (metric) => metric.label === "EMA indicativo" && /EMA/i.test(metric.value),
      ),
      true,
    );
    assert.equal(
      reviewScenario.detail.metrics.some(
        (metric) => metric.label === "Decisao indicativa" && /Decisao indicativa/i.test(metric.value),
      ),
      true,
    );
    assert.equal(
      reviewScenario.detail.checklist.some(
        (item) =>
          item.label === "EMA indicativo Portaria 157/2022" &&
          item.status === "passed",
      ),
      true,
    );

    const resultsSection = previewScenario.result.sections.find(
      (section) => section.key === "results",
    );
    assert.ok(resultsSection);
    assert.equal(
      resultsSection.fields.some((field) => field.label === "Uc preliminar"),
      true,
    );
    assert.equal(
      resultsSection.fields.some((field) => field.label === "U preliminar"),
      true,
    );
    assert.equal(
      resultsSection.fields.some((field) => field.label === "EMA 157/2022"),
      true,
    );
    const decisionSection = previewScenario.result.sections.find(
      (section) => section.key === "decision",
    );
    assert.ok(decisionSection);
    assert.equal(
      decisionSection.fields.some(
        (field) =>
          field.label === "Decisao indicativa" &&
          /Decisao indicativa/i.test(field.value),
      ),
      true,
    );
    assert.equal(
      decisionSection.fields.some((field) => field.label === "Assistencia decisoria"),
      true,
    );
    assert.equal(
      resultsSection.fields.some(
        (field) =>
          field.label === "Orcamento preliminar" &&
          /U preliminar=/i.test(field.value),
      ),
      true,
    );
  } finally {
    await app.close();
  }
});


test("blocks persisted review approval without an explicit official decision", async () => {
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
      url: "/emission/review-signature/manage",
      headers: { cookie },
      payload: {
        action: "review",
        serviceOrderId: "service-order-00142",
        reviewerUserId: "user-reviewer-1",
        signatoryUserId: "user-signatory-1",
        workflowStatus: "awaiting_signature",
        reviewDecision: "approved",
        reviewDecisionComment: "Revisao concluida.",
        reviewDeviceId: "device-review-01",
      },
    });

    assert.equal(response.statusCode, 409);
    assert.equal(response.json().error, "official_decision_required");
  } finally {
    await app.close();
  }
});


test("requires justification when the official decision diverges from the indicative evaluation", async () => {
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
      url: "/emission/review-signature/manage",
      headers: { cookie },
      payload: {
        action: "review",
        serviceOrderId: "service-order-00142",
        reviewerUserId: "user-reviewer-1",
        signatoryUserId: "user-signatory-1",
        workflowStatus: "awaiting_signature",
        reviewDecision: "approved",
        reviewDecisionComment: "Revisao concluida com ressalva.",
        decisionOutcomeLabel: "Nao conforme",
        reviewDeviceId: "device-review-01",
      },
    });

    assert.equal(response.statusCode, 409);
    assert.equal(
      response.json().error,
      "official_decision_divergence_justification_required",
    );
  } finally {
    await app.close();
  }
});


test("blocks direct emission when the persisted review lacks an official decision", async () => {
  const { runtimeReadiness } = createRuntimeReadinessStub();
  const seed = createV3ServiceOrderSeed();
  type SeedServiceOrders = NonNullable<typeof seed.serviceOrders>;
  const serviceOrders = structuredClone(seed.serviceOrders ?? []) as SeedServiceOrders;
  seed.serviceOrders = serviceOrders.map((record: SeedServiceOrders[number]) =>
    record.serviceOrderId === "service-order-00142"
      ? {
          ...record,
          workflowStatus: "awaiting_signature" as const,
          reviewDecision: "approved" as const,
          decisionOutcomeLabel: undefined,
          officialDecisionDivergesFromIndicative: false,
          officialDecisionJustification: undefined,
        }
      : record,
  ) as SeedServiceOrders;
  const app = await buildApp({
    env: TEST_ENV,
    runtimeReadiness,
    corePersistence: createMemoryCorePersistence(createV3CoreSeed()),
    registryPersistence: createMemoryRegistryPersistence(createV2RegistrySeed()),
    serviceOrderPersistence: createMemoryServiceOrderPersistence(seed),
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
      url: "/emission/signature-queue/manage",
      headers: { cookie },
      payload: {
        action: "emit",
        serviceOrderId: "service-order-00142",
        signatoryUserId: "user-signatory-1",
        signatureDeviceId: "device-sign-01",
      },
    });

    assert.equal(response.statusCode, 409);
    assert.equal(response.json().error, "official_decision_required");
  } finally {
    await app.close();
  }
});


test("blocks direct emission when a divergent official decision has no justification", async () => {
  const { runtimeReadiness } = createRuntimeReadinessStub();
  const seed = createV3ServiceOrderSeed();
  type SeedServiceOrders = NonNullable<typeof seed.serviceOrders>;
  const serviceOrders = structuredClone(seed.serviceOrders ?? []) as SeedServiceOrders;
  seed.serviceOrders = serviceOrders.map((record: SeedServiceOrders[number]) =>
    record.serviceOrderId === "service-order-00142"
      ? {
          ...record,
          workflowStatus: "awaiting_signature" as const,
          reviewDecision: "approved" as const,
          decisionOutcomeLabel: "Nao conforme",
          officialDecisionDivergesFromIndicative: true,
          officialDecisionJustification: undefined,
        }
      : record,
  ) as SeedServiceOrders;
  const app = await buildApp({
    env: TEST_ENV,
    runtimeReadiness,
    corePersistence: createMemoryCorePersistence(createV3CoreSeed()),
    registryPersistence: createMemoryRegistryPersistence(createV2RegistrySeed()),
    serviceOrderPersistence: createMemoryServiceOrderPersistence(seed),
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
      url: "/emission/signature-queue/manage",
      headers: { cookie },
      payload: {
        action: "emit",
        serviceOrderId: "service-order-00142",
        signatoryUserId: "user-signatory-1",
        signatureDeviceId: "device-sign-01",
      },
    });

    assert.equal(response.statusCode, 409);
    assert.equal(
      response.json().error,
      "official_decision_divergence_justification_required",
    );
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
        decisionOutcomeLabel: "Inconclusiva",
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
    const previewResponse = await app.inject({
      method: "GET",
      url: "/emission/certificate-preview?item=service-order-00142",
      headers: { cookie },
    });
    const auditResponse = await app.inject({
      method: "GET",
      url: "/quality/audit-trail?item=service-order-00142",
      headers: { cookie },
    });

    const queuePayload = signatureQueueCatalogSchema.parse(queueResponse.json());
    const previewPayload = certificatePreviewCatalogSchema.parse(previewResponse.json());
    const auditPayload = auditTrailCatalogSchema.parse(auditResponse.json());
    const queueScenario = queuePayload.scenarios.find(
      (scenario) => scenario.id === queuePayload.selectedScenarioId,
    );
    const previewScenario = previewPayload.scenarios.find(
      (scenario) => scenario.id === previewPayload.selectedScenarioId,
    );
    assert.ok(queueScenario);
    assert.ok(previewScenario);
    const decisionSection = previewScenario.result.sections.find(
      (section) => section.key === "decision",
    );
    assert.ok(decisionSection);
    assert.equal(
      decisionSection.fields.some(
        (field) =>
          field.label === "Assistencia decisoria" && /alinhada/i.test(field.value),
      ),
      true,
    );

    assert.equal((queueScenario.approval.documentHash?.length ?? 0) > 0, true);
    assert.match(queueScenario.approval.compactPreview[3]?.value ?? "", /^LABPERSISTID/);
    assert.equal(queueScenario.approval.decisionAssistance?.officialDecisionLabel, "Inconclusiva");
    assert.equal(
      queueScenario.approval.decisionAssistance?.indicativeDecision?.summaryLabel.includes(
        "Decisao indicativa",
      ),
      true,
    );
    assert.equal(auditPayload.selectedScenarioId, "recent-emission");
    assert.equal(auditPayload.scenarios[0]?.items.some((item) => item.actionLabel === "certificate.emitted"), true);

    const reviewEvent = auditPayload.scenarios[0]?.items.find(
      (item) => item.actionLabel === "technical_review.completed",
    );
    assert.ok(reviewEvent);

    const auditDetailResponse = await app.inject({
      method: "GET",
      url: `/quality/audit-trail?item=service-order-00142&event=${reviewEvent.eventId}`,
      headers: { cookie },
    });
    const auditDetailPayload = auditTrailCatalogSchema.parse(auditDetailResponse.json());
    const auditDetailScenario = auditDetailPayload.scenarios.find(
      (scenario) => scenario.id === auditDetailPayload.selectedScenarioId,
    );
    assert.ok(auditDetailScenario);
    assert.equal(
      auditDetailScenario.detail.selectedEventContextFields.some(
        (field) => field.label === "Decisao oficial" && field.value === "Inconclusiva",
      ),
      true,
    );
    assert.equal(
      auditDetailScenario.detail.selectedEventContextFields.some(
        (field) => field.label === "Decisao indicativa" && /Decisao indicativa/i.test(field.value),
      ),
      true,
    );
  } finally {
    await app.close();
  }
});


test("exports the persisted management review meeting as .ics only for the authenticated tenant", async () => {
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
    const anonymousResponse = await app.inject({
      method: "GET",
      url: "/quality/management-review/calendar.ics?meeting=review-2026-q2",
    });
    assert.equal(anonymousResponse.statusCode, 401);

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
      url: "/quality/management-review/calendar.ics?meeting=review-2026-q2",
      headers: { cookie },
    });

    assert.equal(response.statusCode, 200);
    assert.match(String(response.headers["content-type"] ?? ""), /text\/calendar/i);
    assert.match(response.body, /BEGIN:VEVENT/);
    assert.match(response.body, /SUMMARY:Analise critica Q2(\/| )2026/);
  } finally {
    await app.close();
  }
});


test("updates persisted V5 nonconformity, indicator history, management review signature and compliance profile through manage endpoints", async () => {
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

    const [ncManage, indicatorManage, reviewManage, settingsManage] = await Promise.all([
      app.inject({
        method: "POST",
        url: "/quality/nonconformities/manage",
        headers: { cookie },
        payload: {
          action: "save",
          ncId: "nc-014",
          serviceOrderId: "service-order-00147",
          ownerUserId: "user-admin-1",
          title: "NC-014 Â· Segregacao revalidada",
          originLabel: "Revisao tecnica",
          severityLabel: "Moderada",
          status: "attention",
          noticeLabel: "A NC entrou em follow-up controlado.",
          rootCauseLabel: "PapÃ©is regularizados e aguardando evidencia final.",
          containmentLabel: "Manter o bloqueio parcial ate anexar nova conferencia.",
          correctiveActionLabel: "Concluir checklist final e liberar revisao.",
          evidenceLabel: "Checklist final em andamento.",
          blockers: [],
          warnings: ["Ainda falta evidÃªncia final."],
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
        url: "/quality/management-review/manage",
        headers: { cookie },
        payload: {
          action: "sign",
          meetingId: "review-2026-q2",
          signatureDeviceId: "device-quality-02",
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
    assert.equal(reviewManage.statusCode, 204);
    assert.equal(settingsManage.statusCode, 204);

    const [ncResponse, indicatorResponse, reviewResponse, settingsResponse] = await Promise.all([
      app.inject({ method: "GET", url: "/quality/nonconformities", headers: { cookie } }),
      app.inject({ method: "GET", url: "/quality/indicators?indicator=indicator-emission-completion", headers: { cookie } }),
      app.inject({ method: "GET", url: "/quality/management-review", headers: { cookie } }),
      app.inject({ method: "GET", url: "/settings/organization", headers: { cookie } }),
    ]);

    const ncPayload = nonconformityRegistryCatalogSchema.parse(ncResponse.json());
    const indicatorPayload = qualityIndicatorRegistryCatalogSchema.parse(indicatorResponse.json());
    const reviewPayload = managementReviewCatalogSchema.parse(reviewResponse.json());
    const settingsPayload = organizationSettingsCatalogSchema.parse(settingsResponse.json());

    assert.equal(ncPayload.scenarios[0]?.items[0]?.summary, "NC-014 Â· Segregacao revalidada");
    assert.match(
      indicatorPayload.scenarios.flatMap((scenario) => scenario.detail.snapshots.map((snapshot) => snapshot.monthLabel)).join(" "),
      /05\/2026/i,
    );
    assert.equal(reviewPayload.scenarios[0]?.detail.signature.status, "signed");
    assert.equal(reviewPayload.scenarios[0]?.detail.signature.signedByLabel, "Ana Administradora");
    assert.equal(reviewPayload.scenarios[0]?.detail.signature.deviceLabel, "device-quality-02");
    assert.equal(
      settingsPayload.scenarios[0]?.summary.profileLabel.includes("Tipo A"),
      true,
    );
  } finally {
    await app.close();
  }
});

