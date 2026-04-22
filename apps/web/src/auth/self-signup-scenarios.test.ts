import assert from "node:assert/strict";
import { test } from "node:test";

import { selfSignupCatalogSchema } from "@afere/contracts";

import { loadSelfSignupCatalog } from "./self-signup-api.js";
import { buildSelfSignupCatalogView } from "./self-signup-scenarios.js";

const CATALOG_FIXTURE = selfSignupCatalogSchema.parse({
  selectedScenarioId: "technician-blocked",
  scenarios: [
    {
      id: "signatory-ready",
      label: "Signatario pronto",
      description: "Todos os provedores estao habilitados.",
      role: "signatory",
      result: {
        ok: true,
        missingProviders: [],
        mfaRequired: true,
      },
    },
    {
      id: "technician-blocked",
      label: "Tecnico bloqueado",
      description: "Faltam provedores obrigatorios.",
      role: "technician",
      result: {
        ok: false,
        missingProviders: ["microsoft", "apple"],
        mfaRequired: false,
        reason: "missing_required_provider",
      },
    },
  ],
});

test("selects the active self-signup scenario from the backend catalog", () => {
  const view = buildSelfSignupCatalogView(CATALOG_FIXTURE);

  assert.equal(view.selectedScenario.id, "technician-blocked");
  assert.equal(view.selectedScenario.viewModel.status, "blocked");
  assert.deepEqual(view.selectedScenario.viewModel.visibleMethods, ["email_password", "google"]);
  assert.deepEqual(view.selectedScenario.viewModel.missingMethods, ["microsoft", "apple"]);
});

test("loads and validates the self-signup catalog from the backend endpoint", async () => {
  const catalog = await loadSelfSignupCatalog({
    scenarioId: "signatory-ready",
    apiBaseUrl: "http://127.0.0.1:3000",
    fetchImpl: async (input) => {
      assert.equal(
        String(input),
        "http://127.0.0.1:3000/auth/self-signup?scenario=signatory-ready",
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
  assert.equal(catalog.selectedScenarioId, "technician-blocked");
  assert.equal(catalog.scenarios.length, 2);
});

test("fails closed when the self-signup backend payload is invalid", async () => {
  const catalog = await loadSelfSignupCatalog({
    fetchImpl: async () =>
      new Response(JSON.stringify({ selectedScenarioId: "signatory-ready", scenarios: [] }), {
        status: 200,
        headers: {
          "content-type": "application/json",
        },
      }),
  });

  assert.equal(catalog, null);
});
