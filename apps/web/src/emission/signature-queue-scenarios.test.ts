import assert from "node:assert/strict";
import { test } from "node:test";

import { signatureQueueCatalogSchema } from "@afere/contracts";

import { loadSignatureQueueCatalog } from "./signature-queue-api.js";
import { buildSignatureQueueCatalogView } from "./signature-queue-scenarios.js";

const CATALOG_FIXTURE = signatureQueueCatalogSchema.parse({
  selectedScenarioId: "attention-required",
  scenarios: [
    {
      id: "approved-ready",
      label: "Fila pronta para assinatura",
      description: "Fila verde.",
      summary: {
        status: "ready",
        headline: "Fila pronta para assinatura controlada",
        pendingCount: 2,
        readyCount: 2,
        attentionCount: 0,
        blockedCount: 0,
        batchReadyCount: 2,
        oldestPendingLabel: "2h 12min",
        recommendedAction: "Assinar os itens prontos.",
        blockers: [],
        warnings: [],
      },
      selectedItemId: "os-2026-00142",
      items: [
        {
          itemId: "os-2026-00142",
          workOrderNumber: "OS-2026-00142",
          customerName: "Lab. Acme",
          equipmentLabel: "Toledo Prix 3",
          instrumentType: "Balanca",
          waitingSinceLabel: "18 min",
          certificateNumber: "AFR-000124",
          status: "ready",
          previewScenarioId: "type-b-ready",
          reviewSignatureScenarioId: "approved-ready",
          validations: [
            {
              label: "Revisao tecnica",
              status: "passed",
              detail: "Revisao concluida.",
            },
          ],
          blockers: [],
          warnings: [],
        },
      ],
      approval: {
        itemId: "os-2026-00142",
        title: "OS-2026-00142 - assinatura final",
        status: "ready",
        signatoryDisplayName: "Carlos Signatario",
        authorizationLabel: "Signatario autorizado",
        statement: "Confirmo a emissao.",
        documentHash: "a3f9",
        canSign: true,
        actionLabel: "Assinar e emitir",
        blockers: [],
        warnings: [],
        authRequirements: [
          {
            factor: "password",
            label: "Senha",
            status: "configured",
            detail: "Obrigatoria.",
          },
        ],
        compactPreview: [
          {
            label: "Cliente",
            value: "Lab. Acme",
          },
        ],
      },
    },
    {
      id: "attention-required",
      label: "Fila com atencao regulatoria",
      description: "Fila com warning.",
      summary: {
        status: "attention",
        headline: "Fila exige conferencia final antes da assinatura",
        pendingCount: 2,
        readyCount: 1,
        attentionCount: 1,
        blockedCount: 0,
        batchReadyCount: 1,
        oldestPendingLabel: "5h 40min",
        recommendedAction: "Conferir warning antes de assinar.",
        blockers: [],
        warnings: ["Simbolo regulatorio suprimido."],
      },
      selectedItemId: "os-2026-00135",
      items: [
        {
          itemId: "os-2026-00135",
          workOrderNumber: "OS-2026-00135",
          customerName: "Industria XYZ",
          equipmentLabel: "Marte 50kg",
          instrumentType: "Balanca",
          waitingSinceLabel: "5h 40min",
          certificateNumber: "AFR-000129",
          status: "attention",
          previewScenarioId: "type-a-suppressed",
          reviewSignatureScenarioId: "approved-ready",
          validations: [
            {
              label: "Politica regulatoria",
              status: "warning",
              detail: "Simbolo suprimido.",
            },
          ],
          blockers: [],
          warnings: ["Simbolo regulatorio suprimido."],
        },
      ],
      approval: {
        itemId: "os-2026-00135",
        title: "OS-2026-00135 - assinatura final",
        status: "attention",
        signatoryDisplayName: "Carlos Signatario",
        authorizationLabel: "Signatario autorizado",
        statement: "Confirmo a emissao.",
        documentHash: "b7c1",
        canSign: true,
        actionLabel: "Assinar e emitir",
        blockers: [],
        warnings: ["Simbolo regulatorio suprimido."],
        authRequirements: [
          {
            factor: "password",
            label: "Senha",
            status: "configured",
            detail: "Obrigatoria.",
          },
        ],
        compactPreview: [
          {
            label: "Cliente",
            value: "Industria XYZ",
          },
        ],
      },
    },
  ],
});

test("selects the active signature queue scenario from the backend catalog", () => {
  const view = buildSignatureQueueCatalogView(CATALOG_FIXTURE);

  assert.equal(view.selectedScenario.id, "attention-required");
  assert.equal(view.selectedScenario.selectedItem.itemId, "os-2026-00135");
  assert.match(view.selectedScenario.summaryLabel, /1 item\(ns\) em atencao/i);
});

test("loads and validates the signature queue catalog from the backend endpoint", async () => {
  const catalog = await loadSignatureQueueCatalog({
    scenarioId: "approved-ready",
    itemId: "os-2026-00142",
    apiBaseUrl: "http://127.0.0.1:3000",
    fetchImpl: async (input) => {
      assert.equal(
        String(input),
        "http://127.0.0.1:3000/emission/signature-queue?scenario=approved-ready&item=os-2026-00142",
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
  assert.equal(catalog.selectedScenarioId, "attention-required");
  assert.equal(catalog.scenarios.length, 2);
});

test("fails closed when the signature queue backend payload is invalid", async () => {
  const catalog = await loadSignatureQueueCatalog({
    fetchImpl: async () =>
      new Response(JSON.stringify({ selectedScenarioId: "approved-ready", scenarios: [] }), {
        status: 200,
        headers: {
          "content-type": "application/json",
        },
      }),
  });

  assert.equal(catalog, null);
});
