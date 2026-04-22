import assert from "node:assert/strict";
import { test } from "node:test";

import { publicCertificateCatalogSchema } from "@afere/contracts";

import { loadPublicCertificateCatalog } from "./public-certificate-api.js";
import { buildPublicCertificateCatalogView } from "./public-certificate-scenarios.js";

const CATALOG_FIXTURE = publicCertificateCatalogSchema.parse({
  selectedScenarioId: "authentic",
  scenarios: [
    {
      id: "authentic",
      label: "Certificado autentico",
      description: "Mostra o recorte minimo de metadados para um certificado valido.",
      result: {
        ok: true,
        status: "authentic",
        certificate: {
          certificateNumber: "AFR-000123",
          issuedAtUtc: "2026-04-21T14:00:00Z",
          revision: "R0",
          instrumentDescription: "Balanca IPNA 300 kg",
          serialNumber: "SN-42",
        },
      },
    },
    {
      id: "not-found",
      label: "Nao localizado",
      description: "Fluxo fail-closed.",
      result: {
        ok: false,
        status: "not_found",
        reason: "certificate_not_found",
      },
    },
  ],
});

test("selects the active public certificate scenario from the backend catalog", () => {
  const view = buildPublicCertificateCatalogView(CATALOG_FIXTURE);

  assert.equal(view.selectedScenario.id, "authentic");
  assert.equal(view.selectedScenario.page.status, "authentic");
  assert.equal(view.selectedScenario.page.publicMetadata.certificateNumber, "AFR-000123");
});

test("loads and validates the public certificate catalog from the backend endpoint", async () => {
  const catalog = await loadPublicCertificateCatalog({
    scenarioId: "reissued",
    apiBaseUrl: "http://127.0.0.1:3000",
    fetchImpl: async (input) => {
      assert.equal(String(input), "http://127.0.0.1:3000/portal/verify?scenario=reissued");

      return new Response(JSON.stringify(CATALOG_FIXTURE), {
        status: 200,
        headers: {
          "content-type": "application/json",
        },
      });
    },
  });

  assert.ok(catalog);
  assert.equal(catalog.selectedScenarioId, "authentic");
  assert.equal(catalog.scenarios.length, 2);
});

test("fails closed when the public certificate backend payload is invalid", async () => {
  const catalog = await loadPublicCertificateCatalog({
    fetchImpl: async () =>
      new Response(JSON.stringify({ selectedScenarioId: "authentic", scenarios: [] }), {
        status: 200,
        headers: {
          "content-type": "application/json",
        },
      }),
  });

  assert.equal(catalog, null);
});
