import assert from "node:assert/strict";
import { test } from "node:test";

import { auditTrailCatalogSchema } from "@afere/contracts";

import { loadAuditTrailCatalog } from "./audit-trail-api.js";
import { buildAuditTrailCatalogView } from "./audit-trail-scenarios.js";

const CATALOG_FIXTURE = auditTrailCatalogSchema.parse({
  selectedScenarioId: "reissue-attention",
  scenarios: [
    {
      id: "recent-emission",
      label: "Emissao recente com hash-chain integra",
      description: "Tudo verde.",
      summary: {
        status: "ready",
        headline: "Trilha de auditoria integra e pronta para consulta",
        totalEvents: 4,
        criticalEvents: 4,
        reissueEvents: 0,
        integrityFailures: 0,
        recommendedAction: "Seguir operacao.",
        blockers: [],
        warnings: [],
      },
      selectedEventId: "audit-4",
      items: [
        {
          eventId: "audit-4",
          occurredAtLabel: "2026-04-19 14:22:45 UTC",
          actorLabel: "Sistema",
          actionLabel: "certificate.emitted",
          entityLabel: "CERT-AFR-000124",
          hashLabel: "a3f9.",
          status: "ready",
        },
      ],
      detail: {
        chainId: "OS-2026-00142",
        title: "OS-2026-00142 · Todas",
        status: "ready",
        noticeLabel: "Trilha integra e pronta para consulta.",
        selectedWindowLabel: "Ultimos 7 dias",
        selectedActorLabel: "Todos",
        selectedEntityLabel: "OS-2026-00142",
        selectedActionLabel: "Todas",
        chainStatusLabel: "Hash-chain integra e criterios criticos satisfeitos",
        exportLabel: "Exportacao pronta para auditoria",
        coveredActions: [
          "calibration.executed",
          "technical_review.completed",
          "certificate.signed",
          "certificate.emitted",
        ],
        selectedEventContextFields: [],
        missingActions: [],
        blockers: [],
        warnings: [],
        links: {
          workspaceScenarioId: "baseline-ready",
          serviceOrderScenarioId: "review-ready",
          reviewItemId: "os-2026-00142",
          dryRunScenarioId: "type-b-ready",
          publicCertificateScenarioId: "authentic",
        },
      },
    },
    {
      id: "reissue-attention",
      label: "Reemissao controlada em evidencia",
      description: "Atencao operacional.",
      summary: {
        status: "attention",
        headline: "Trilha integra com reemissao controlada em destaque",
        totalEvents: 8,
        criticalEvents: 5,
        reissueEvents: 3,
        integrityFailures: 0,
        recommendedAction: "Conferir notificacao.",
        blockers: [],
        warnings: ["Cadeia contem reemissao controlada ja notificada ao cliente."],
      },
      selectedEventId: "audit-7",
      items: [
        {
          eventId: "audit-7",
          occurredAtLabel: "2026-04-21 08:08:00 UTC",
          actorLabel: "Sistema",
          actionLabel: "certificate.reissued",
          entityLabel: "CERT-AFR-000118-R1",
          hashLabel: "b21c.",
          status: "attention",
        },
      ],
      detail: {
        chainId: "CERT-AFR-000118",
        title: "CERT-AFR-000118 · Reemissao",
        status: "attention",
        noticeLabel: "Trilha integra, mas com evento sensivel que exige leitura cuidadosa.",
        selectedWindowLabel: "Ultimos 30 dias",
        selectedActorLabel: "Todos",
        selectedEntityLabel: "CERT-AFR-000118",
        selectedActionLabel: "Reemissao",
        chainStatusLabel: "Hash-chain integra e criterios criticos satisfeitos",
        exportLabel: "Exportacao liberada com ressalva de revisao",
        coveredActions: [
          "calibration.executed",
          "technical_review.completed",
          "certificate.signed",
          "certificate.emitted",
          "certificate.reissue.approved",
          "certificate.reissued",
          "certificate.reissue.notified",
        ],
        selectedEventContextFields: [],
        missingActions: [],
        blockers: [],
        warnings: ["Cadeia contem reemissao controlada ja notificada ao cliente."],
        links: {
          workspaceScenarioId: "team-attention",
          serviceOrderScenarioId: "history-pending",
          reviewItemId: "os-2026-00141",
          dryRunScenarioId: "type-b-ready",
          publicCertificateScenarioId: "reissued",
        },
      },
    },
  ],
});

test("selects the active audit trail scenario from the backend catalog", () => {
  const view = buildAuditTrailCatalogView(CATALOG_FIXTURE);

  assert.equal(view.selectedScenario.id, "reissue-attention");
  assert.equal(view.selectedScenario.selectedEvent.eventId, "audit-7");
  assert.match(view.selectedScenario.summaryLabel, /3 evento\(s\) de reemissao/i);
});

test("loads and validates the audit trail catalog from the backend endpoint", async () => {
  const catalog = await loadAuditTrailCatalog({
    scenarioId: "recent-emission",
    eventId: "audit-4",
    apiBaseUrl: "http://127.0.0.1:3000",
    fetchImpl: async (input) => {
      assert.equal(
        String(input),
        "http://127.0.0.1:3000/quality/audit-trail?scenario=recent-emission&event=audit-4",
      );

      return new Response(JSON.stringify(CATALOG_FIXTURE), {
        status: 200,
        headers: {
          "content-type": "application/json",
        },
      });
    },
  });

  assert.ok(catalog);
  assert.equal(catalog.selectedScenarioId, "reissue-attention");
  assert.equal(catalog.scenarios.length, 2);
});

test("fails closed when the audit trail backend payload is invalid", async () => {
  const catalog = await loadAuditTrailCatalog({
    fetchImpl: async () =>
      new Response(JSON.stringify({ selectedScenarioId: "recent-emission", scenarios: [] }), {
        status: 200,
        headers: {
          "content-type": "application/json",
        },
      }),
  });

  assert.equal(catalog, null);
});
