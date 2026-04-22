import assert from "node:assert/strict";
import { test } from "node:test";

import { onboardingCatalogSchema } from "@afere/contracts";

import { loadOnboardingCatalog } from "./onboarding-api.js";
import { buildOnboardingCatalogView } from "./onboarding-scenarios.js";

const CATALOG_FIXTURE = onboardingCatalogSchema.parse({
  selectedScenarioId: "blocked",
  scenarios: [
    {
      id: "ready",
      label: "Liberado para emissao",
      description: "Todos os prerequisitos foram concluidos.",
      result: {
        completedWithinTarget: true,
        canEmitFirstCertificate: true,
        blockingReasons: [],
      },
    },
    {
      id: "blocked",
      label: "Bloqueado por prerequisitos",
      description: "Ainda faltam passos obrigatorios.",
      result: {
        completedWithinTarget: false,
        canEmitFirstCertificate: false,
        blockingReasons: [
          "primary_signatory_pending",
          "certificate_numbering_pending",
          "scope_review_pending",
          "public_qr_pending",
        ],
      },
    },
  ],
});

test("selects the active onboarding scenario from the backend catalog", () => {
  const view = buildOnboardingCatalogView(CATALOG_FIXTURE);

  assert.equal(view.selectedScenario.id, "blocked");
  assert.equal(view.selectedScenario.summary.status, "blocked");
  assert.deepEqual(view.selectedScenario.summary.blockingSteps, [
    "Signatario principal",
    "Numeracao de certificado",
    "Escopo e CMC",
    "QR publico",
  ]);
});

test("loads and validates the onboarding catalog from the backend endpoint", async () => {
  const catalog = await loadOnboardingCatalog({
    scenarioId: "ready",
    apiBaseUrl: "http://127.0.0.1:3000",
    fetchImpl: async (input) => {
      assert.equal(
        String(input),
        "http://127.0.0.1:3000/onboarding/readiness?scenario=ready",
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
  assert.equal(catalog.selectedScenarioId, "blocked");
  assert.equal(catalog.scenarios.length, 2);
});

test("fails closed when the onboarding backend payload is invalid", async () => {
  const catalog = await loadOnboardingCatalog({
    fetchImpl: async () =>
      new Response(JSON.stringify({ selectedScenarioId: "ready", scenarios: [] }), {
        status: 200,
        headers: {
          "content-type": "application/json",
        },
      }),
  });

  assert.equal(catalog, null);
});
