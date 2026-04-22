import assert from "node:assert/strict";
import { test } from "node:test";

import { standardRegistryCatalogSchema } from "@afere/contracts";

import { loadStandardRegistryCatalog } from "./standard-registry-api.js";
import { buildStandardRegistryCatalogView } from "./standard-registry-scenarios.js";

const CATALOG_FIXTURE = standardRegistryCatalogSchema.parse({
  selectedScenarioId: "expiration-attention",
  scenarios: [
    {
      id: "operational-ready",
      label: "Padroes ativos e consistentes",
      description: "Tudo verde.",
      summary: {
        status: "ready",
        headline: "Padroes validos e disponiveis para reserva",
        activeCount: 4,
        expiringSoonCount: 0,
        expiredCount: 0,
        recommendedAction: "Seguir operacao.",
        blockers: [],
        warnings: [],
        expirationPanel: [
          {
            standardId: "standard-001",
            label: "PESO-001",
            dueInLabel: "112d",
            status: "ready",
          },
        ],
      },
      selectedStandardId: "standard-001",
      items: [
        {
          standardId: "standard-001",
          kindLabel: "Peso",
          nominalClassLabel: "1 kg · F1",
          sourceLabel: "RBC-1234",
          certificateLabel: "1234/25/081",
          validUntilLabel: "2026-08-12",
          status: "ready",
        },
      ],
      detail: {
        standardId: "standard-001",
        title: "PESO-001 · Peso padrao 1 kg · classe F1",
        status: "ready",
        noticeLabel: "Padrao valido e liberado para uso no recorte atual.",
        manufacturerLabel: "Coelmatic",
        modelLabel: "M1K",
        serialNumberLabel: "9-22-101",
        nominalValueLabel: "1,000 kg",
        classLabel: "F1",
        usageRangeLabel: "Cargas ate 1 kg",
        uncertaintyLabel: "+/- 8 mg",
        correctionFactorLabel: "+0,001 g",
        history: [
          {
            calibratedAtLabel: "12/08/2025",
            laboratoryLabel: "Lab Cal-1234",
            certificateLabel: "1234/25/081",
            sourceLabel: "RBC",
            uncertaintyLabel: "+/- 8 mg",
            validUntilLabel: "12/08/2026",
          },
        ],
        recentWorkOrders: [{ workOrderNumber: "OS-2026-00142", usedAtLabel: "19/04" }],
        blockers: [],
        warnings: [],
        links: {
          registryScenarioId: "operational-ready",
          selectedEquipmentId: "equipment-001",
          serviceOrderScenarioId: "review-ready",
          reviewItemId: "os-2026-00142",
          dryRunScenarioId: "type-b-ready",
        },
      },
    },
    {
      id: "expiration-attention",
      label: "Padrao entrando em janela critica",
      description: "Atencao preventiva.",
      summary: {
        status: "attention",
        headline: "Padrao em janela critica de vencimento",
        activeCount: 4,
        expiringSoonCount: 1,
        expiredCount: 0,
        recommendedAction: "Solicitar nova calibracao.",
        blockers: [],
        warnings: ["Padrao vence em 2 dias e deve ser retirado da agenda seguinte."],
        expirationPanel: [
          {
            standardId: "standard-005",
            label: "PESO-005",
            dueInLabel: "2d",
            status: "attention",
          },
        ],
      },
      selectedStandardId: "standard-005",
      items: [
        {
          standardId: "standard-005",
          kindLabel: "Peso",
          nominalClassLabel: "5 kg · M1",
          sourceLabel: "RBC-1234",
          certificateLabel: "1234/25/088",
          validUntilLabel: "2026-04-24",
          status: "attention",
        },
      ],
      detail: {
        standardId: "standard-005",
        title: "PESO-005 · Peso padrao 5 kg · classe M1",
        status: "attention",
        noticeLabel: "Este padrao vence em 2 dia(s).",
        manufacturerLabel: "Coelmatic",
        modelLabel: "M5K",
        serialNumberLabel: "9-22-115",
        nominalValueLabel: "5,000 kg",
        classLabel: "M1",
        usageRangeLabel: "Cargas ate 5 kg",
        uncertaintyLabel: "+/- 12 mg",
        correctionFactorLabel: "+0,003 g",
        history: [
          {
            calibratedAtLabel: "24/04/2025",
            laboratoryLabel: "Lab Cal-1234",
            certificateLabel: "1234/25/088",
            sourceLabel: "RBC",
            uncertaintyLabel: "+/- 12 mg",
            validUntilLabel: "24/04/2026",
          },
        ],
        recentWorkOrders: [{ workOrderNumber: "OS-2026-00141", usedAtLabel: "19/04" }],
        blockers: [],
        warnings: ["Padrao vence em 2 dias e deve ser retirado da agenda seguinte."],
        links: {
          registryScenarioId: "certificate-attention",
          selectedEquipmentId: "equipment-003",
          serviceOrderScenarioId: "history-pending",
          reviewItemId: "os-2026-00141",
          dryRunScenarioId: "type-b-ready",
        },
      },
    },
  ],
});

test("selects the active standard registry scenario from the backend catalog", () => {
  const view = buildStandardRegistryCatalogView(CATALOG_FIXTURE);

  assert.equal(view.selectedScenario.id, "expiration-attention");
  assert.equal(view.selectedScenario.selectedStandard.standardId, "standard-005");
  assert.match(view.selectedScenario.summaryLabel, /1 padrao\(es\) em atencao/i);
});

test("loads and validates the standard registry catalog from the backend endpoint", async () => {
  const catalog = await loadStandardRegistryCatalog({
    scenarioId: "operational-ready",
    standardId: "standard-001",
    apiBaseUrl: "http://127.0.0.1:3000",
    fetchImpl: async (input) => {
      assert.equal(
        String(input),
        "http://127.0.0.1:3000/registry/standards?scenario=operational-ready&standard=standard-001",
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
  assert.equal(catalog.selectedScenarioId, "expiration-attention");
  assert.equal(catalog.scenarios.length, 2);
});

test("fails closed when the standard registry backend payload is invalid", async () => {
  const catalog = await loadStandardRegistryCatalog({
    fetchImpl: async () =>
      new Response(JSON.stringify({ selectedScenarioId: "operational-ready", scenarios: [] }), {
        status: 200,
        headers: {
          "content-type": "application/json",
        },
      }),
  });

  assert.equal(catalog, null);
});
