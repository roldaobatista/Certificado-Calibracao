import assert from "node:assert/strict";
import { test } from "node:test";

import { emissionDryRunCatalogSchema } from "@afere/contracts";

import { loadEmissionDryRunCatalog } from "./emission-dry-run-api.js";
import { buildEmissionDryRunCatalogView } from "./emission-dry-run-scenarios.js";

const CATALOG_FIXTURE = emissionDryRunCatalogSchema.parse({
  selectedScenarioId: "type-c-blocked",
  scenarios: [
    {
      id: "type-b-ready",
      label: "Tipo B pronto",
      description: "Todos os gates passam.",
      profile: "B",
      result: {
        status: "ready",
        profile: "B",
        summary: "Dry-run pronto para emissao controlada no perfil B.",
        blockers: [],
        warnings: [],
        checks: [
          {
            id: "profile_policy",
            title: "Politica regulatoria",
            status: "passed",
            detail: "Perfil B compativel com template-b.",
          },
          {
            id: "qr_authenticity",
            title: "QR publico",
            status: "passed",
            detail: "QR autenticado em dry-run com status authentic.",
          },
        ],
        artifacts: {
          templateId: "template-b",
          symbolPolicy: "blocked",
          certificateNumber: "AFR-000124",
          declarationSummary: "Resultado: 149.98 kg | U: +/-0.05 kg | k=2",
          qrCodeUrl: "https://portal.afere.local/verify?certificate=cert-dry-b-001&token=token-b-001",
          qrVerificationStatus: "authentic",
          publicPreview: {
            certificateNumber: "AFR-000124",
          },
        },
      },
    },
    {
      id: "type-c-blocked",
      label: "Tipo C bloqueado",
      description: "Alguns gates falham.",
      profile: "C",
      result: {
        status: "blocked",
        profile: "C",
        summary: "Dry-run bloqueado por 5 verificacoes no perfil C.",
        blockers: ["Politica regulatoria do perfil", "QR publico"],
        warnings: [],
        checks: [
          {
            id: "profile_policy",
            title: "Politica regulatoria",
            status: "failed",
            detail: "Bloqueios de politica regulatoria.",
          },
          {
            id: "qr_authenticity",
            title: "QR publico",
            status: "failed",
            detail: "Campos obrigatorios do QR ausentes.",
          },
        ],
        artifacts: {
          templateId: "template-c",
          symbolPolicy: "blocked",
          declarationSummary: "Resultado: 449.2 kg | U: +/-0.12 kg | k=2",
          publicPreview: {},
        },
      },
    },
  ],
});

test("selects the active dry-run scenario from the backend catalog", () => {
  const view = buildEmissionDryRunCatalogView(CATALOG_FIXTURE);

  assert.equal(view.selectedScenario.id, "type-c-blocked");
  assert.equal(view.selectedScenario.summary.status, "blocked");
  assert.equal(view.selectedScenario.summary.failedChecks, 2);
  assert.deepEqual(view.selectedScenario.summary.blockers, [
    "Politica regulatoria do perfil",
    "QR publico",
  ]);
});

test("loads and validates the dry-run catalog from the backend endpoint", async () => {
  const catalog = await loadEmissionDryRunCatalog({
    scenarioId: "type-a-suppressed",
    apiBaseUrl: "http://127.0.0.1:3000",
    fetchImpl: async (input) => {
      assert.equal(
        String(input),
        "http://127.0.0.1:3000/emission/dry-run?scenario=type-a-suppressed",
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
  assert.equal(catalog.selectedScenarioId, "type-c-blocked");
  assert.equal(catalog.scenarios.length, 2);
});

test("fails closed when the backend payload is invalid", async () => {
  const catalog = await loadEmissionDryRunCatalog({
    fetchImpl: async () =>
      new Response(JSON.stringify({ selectedScenarioId: "type-b-ready", scenarios: [] }), {
        status: 200,
        headers: {
          "content-type": "application/json",
        },
      }),
  });

  assert.equal(catalog, null);
});
