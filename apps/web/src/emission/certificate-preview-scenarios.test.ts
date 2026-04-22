import assert from "node:assert/strict";
import { test } from "node:test";

import { certificatePreviewCatalogSchema } from "@afere/contracts";

import { loadCertificatePreviewCatalog } from "./certificate-preview-api.js";
import { buildCertificatePreviewCatalogView } from "./certificate-preview-scenarios.js";

const CATALOG_FIXTURE = certificatePreviewCatalogSchema.parse({
  selectedScenarioId: "type-c-blocked",
  scenarios: [
    {
      id: "type-b-ready",
      label: "Tipo B pronto",
      description: "Preview liberada.",
      result: {
        status: "ready",
        headline: "Previa integral pronta para conferencia",
        templateId: "template-b",
        symbolPolicy: "blocked",
        certificateNumber: "AFR-000124",
        qrCodeUrl: "https://portal.afere.local/verify?certificate=cert-dry-b-001&token=token-b-001",
        qrVerificationStatus: "authentic",
        blockers: [],
        warnings: [],
        sections: [
          {
            key: "header",
            title: "Cabecalho",
            fields: [{ label: "Organizacao emissora", value: "Lab. Acme" }],
          },
        ],
      },
    },
    {
      id: "type-c-blocked",
      label: "Tipo C bloqueado",
      description: "Preview em fail-closed.",
      result: {
        status: "blocked",
        headline: "Previa bloqueada antes da assinatura",
        templateId: "template-c",
        symbolPolicy: "blocked",
        suggestedReturnStep: 2,
        blockers: ["Cadastro do equipamento", "QR publico"],
        warnings: ["Campo livre com termos proibidos."],
        sections: [
          {
            key: "header",
            title: "Cabecalho",
            fields: [{ label: "Organizacao emissora", value: "Metrologia Campo Sul" }],
          },
        ],
      },
    },
  ],
});

test("selects the active certificate preview scenario from the backend catalog", () => {
  const view = buildCertificatePreviewCatalogView(CATALOG_FIXTURE);

  assert.equal(view.selectedScenario.id, "type-c-blocked");
  assert.match(view.selectedScenario.summaryLabel, /2 bloqueio\(s\) ativos/i);
  assert.equal(view.selectedScenario.returnStepLabel, "Voltar ao passo 2");
});

test("loads and validates the certificate preview catalog from the backend endpoint", async () => {
  const catalog = await loadCertificatePreviewCatalog({
    scenarioId: "type-b-ready",
    apiBaseUrl: "http://127.0.0.1:3000",
    fetchImpl: async (input) => {
      assert.equal(
        String(input),
        "http://127.0.0.1:3000/emission/certificate-preview?scenario=type-b-ready",
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

test("fails closed when the certificate preview backend payload is invalid", async () => {
  const catalog = await loadCertificatePreviewCatalog({
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
