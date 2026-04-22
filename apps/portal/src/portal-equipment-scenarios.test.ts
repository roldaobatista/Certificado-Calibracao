import assert from "node:assert/strict";
import { test } from "node:test";

import { portalEquipmentCatalogSchema } from "@afere/contracts";

import { loadPortalEquipmentCatalog } from "./portal-equipment-api.js";
import { buildPortalEquipmentCatalogView } from "./portal-equipment-scenarios.js";

const CATALOG_FIXTURE = portalEquipmentCatalogSchema.parse({
  selectedScenarioId: "expiring-soon",
  scenarios: [
    {
      id: "stable-portfolio",
      label: "Carteira estavel",
      description: "Sem alertas imediatos.",
      summary: {
        status: "ready",
        headline: "Carteira pronta",
        equipmentCount: 3,
        attentionCount: 0,
        blockedCount: 0,
        recommendedAction: "Manter monitoramento.",
        blockers: [],
        warnings: [],
      },
      selectedEquipmentId: "equipment-bal-007",
      items: [
        {
          equipmentId: "equipment-bal-007",
          tag: "BAL-007",
          description: "Toledo Prix 3",
          manufacturerModelLabel: "Toledo Prix 3",
          locationLabel: "Sala 12",
          lastCalibrationLabel: "18/04/2026",
          nextDueLabel: "18/10/2026",
          status: "ready",
        },
      ],
      detail: {
        equipmentId: "equipment-bal-007",
        title: "BAL-007 - Toledo Prix 3",
        status: "ready",
        manufacturerLabel: "Toledo",
        modelLabel: "Prix 3",
        serialLabel: "9087654",
        capacityClassLabel: "3 kg / 0,5 g / Classe III",
        locationLabel: "Sala 12 - Sao Paulo",
        recommendedAction: "Acompanhar carteira.",
        blockers: [],
        warnings: [],
        certificateHistory: [
          {
            certificateId: "cert-00142",
            issuedAtLabel: "19/04/2026",
            certificateNumber: "CAL-1234/2026/00142",
            resultLabel: "Aprovado",
            uncertaintyLabel: "+/-0,15 g",
            verifyScenarioId: "authentic",
          },
        ],
      },
    },
    {
      id: "expiring-soon",
      label: "Vencimentos proximos",
      description: "Itens vencem em breve.",
      summary: {
        status: "attention",
        headline: "Carteira em atencao",
        equipmentCount: 3,
        attentionCount: 3,
        blockedCount: 0,
        recommendedAction: "Solicitar nova calibracao.",
        blockers: [],
        warnings: ["Tres equipamentos vencem em ate 30 dias."],
      },
      selectedEquipmentId: "equipment-bal-012",
      items: [
        {
          equipmentId: "equipment-bal-007",
          tag: "BAL-007",
          description: "Toledo Prix 3",
          manufacturerModelLabel: "Toledo Prix 3",
          locationLabel: "Sala 12",
          lastCalibrationLabel: "18/04/2026",
          nextDueLabel: "18/05/2026",
          status: "attention",
        },
        {
          equipmentId: "equipment-bal-012",
          tag: "BAL-012",
          description: "Filizola 15 kg",
          manufacturerModelLabel: "Filizola 15 kg",
          locationLabel: "Setor C",
          lastCalibrationLabel: "24/02/2026",
          nextDueLabel: "24/05/2026",
          status: "attention",
        },
      ],
      detail: {
        equipmentId: "equipment-bal-012",
        title: "BAL-012 - Filizola 15 kg",
        status: "attention",
        manufacturerLabel: "Filizola",
        modelLabel: "15 kg",
        serialLabel: "FZ150221",
        capacityClassLabel: "15 kg / 5 g / Classe III",
        locationLabel: "Setor C - Sao Paulo",
        recommendedAction: "Agendar coleta preventiva.",
        blockers: [],
        warnings: ["Vence em menos de 30 dias."],
        certificateHistory: [
          {
            certificateId: "cert-00084",
            issuedAtLabel: "24/02/2026",
            certificateNumber: "CAL-1234/2026/00084",
            resultLabel: "Aprovado",
            uncertaintyLabel: "+/-0,50 g",
            verifyScenarioId: "authentic",
          },
        ],
      },
    },
  ],
});

test("selects the active portal equipment scenario and detail from the backend catalog", () => {
  const view = buildPortalEquipmentCatalogView(CATALOG_FIXTURE);

  assert.equal(view.selectedScenario.id, "expiring-soon");
  assert.equal(view.selectedScenario.selectedEquipment.equipmentId, "equipment-bal-012");
  assert.match(view.selectedScenario.summaryLabel, /equipamento\(s\) em atencao/i);
});

test("loads and validates the portal equipment catalog from the backend endpoint", async () => {
  const catalog = await loadPortalEquipmentCatalog({
    scenarioId: "expiring-soon",
    equipmentId: "equipment-bal-012",
    fetchImpl: async (input) => {
      assert.equal(
        String(input),
        "http://127.0.0.1:3000/portal/equipment?scenario=expiring-soon&equipment=equipment-bal-012",
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
  assert.equal(catalog.selectedScenarioId, "expiring-soon");
});

test("fails closed when the portal equipment backend payload is invalid", async () => {
  const catalog = await loadPortalEquipmentCatalog({
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
