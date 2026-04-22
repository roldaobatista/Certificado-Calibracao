import assert from "node:assert/strict";
import { test } from "node:test";

import { portalDashboardCatalogSchema } from "@afere/contracts";

import { loadPortalDashboardCatalog } from "./portal-dashboard-api.js";
import { buildPortalDashboardCatalogView } from "./portal-dashboard-scenarios.js";

const CATALOG_FIXTURE = portalDashboardCatalogSchema.parse({
  selectedScenarioId: "expiring-soon",
  scenarios: [
    {
      id: "stable-portfolio",
      label: "Carteira estavel",
      description: "Sem vencimentos imediatos.",
      summary: {
        status: "ready",
        clientName: "Joao das Neves",
        organizationName: "Lab. Acme",
        equipmentCount: 23,
        certificateCount: 142,
        expiringSoonCount: 0,
        overdueCount: 0,
        recommendedAction: "Manter monitoramento.",
        blockers: [],
        warnings: [],
      },
      expiringEquipments: [],
      recentCertificates: [
        {
          certificateId: "cert-00142",
          certificateNumber: "CAL-1234/2026/00142",
          equipmentLabel: "BAL-007 Toledo Prix 3",
          issuedAtLabel: "19/04/2026",
          statusLabel: "Aprovado",
          verifyScenarioId: "authentic",
        },
      ],
    },
    {
      id: "expiring-soon",
      label: "Vencimentos proximos",
      description: "Equipamentos vencem em breve.",
      summary: {
        status: "attention",
        clientName: "Joao das Neves",
        organizationName: "Lab. Acme",
        equipmentCount: 23,
        certificateCount: 142,
        expiringSoonCount: 3,
        overdueCount: 0,
        recommendedAction: "Solicitar nova calibracao.",
        blockers: [],
        warnings: ["Tres equipamentos vencem em ate 30 dias."],
      },
      expiringEquipments: [
        {
          equipmentId: "equipment-bal-007",
          tag: "BAL-007",
          description: "Toledo Prix 3",
          locationLabel: "Sala 12",
          lastCalibrationLabel: "18/04/2026",
          dueAtLabel: "18/05/2026",
          status: "attention",
        },
      ],
      recentCertificates: [
        {
          certificateId: "cert-00142",
          certificateNumber: "CAL-1234/2026/00142",
          equipmentLabel: "BAL-007 Toledo Prix 3",
          issuedAtLabel: "19/04/2026",
          statusLabel: "Aprovado",
          verifyScenarioId: "authentic",
        },
      ],
    },
  ],
});

test("selects the active portal dashboard scenario from the backend catalog", () => {
  const view = buildPortalDashboardCatalogView(CATALOG_FIXTURE);

  assert.equal(view.selectedScenario.id, "expiring-soon");
  assert.match(view.selectedScenario.summaryLabel, /vencendo em breve/i);
});

test("loads and validates the portal dashboard catalog from the backend endpoint", async () => {
  const catalog = await loadPortalDashboardCatalog({
    scenarioId: "expiring-soon",
    fetchImpl: async (input) => {
      assert.equal(String(input), "http://127.0.0.1:3000/portal/dashboard?scenario=expiring-soon");

      return new Response(JSON.stringify(CATALOG_FIXTURE), {
        status: 200,
        headers: {
          "content-type": "application/json",
        },
      });
    },
  });

  assert.ok(catalog);
  assert.equal(catalog.selectedScenarioId, "expiring-soon");
});

test("fails closed when the portal dashboard backend payload is invalid", async () => {
  const catalog = await loadPortalDashboardCatalog({
    fetchImpl: async () =>
      new Response(JSON.stringify({ selectedScenarioId: "expiring-soon", scenarios: [] }), {
        status: 200,
        headers: {
          "content-type": "application/json",
        },
      }),
  });

  assert.equal(catalog, null);
});
