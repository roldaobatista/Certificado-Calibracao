import assert from "node:assert/strict";
import { test } from "node:test";

import { serviceOrderReviewCatalogSchema } from "@afere/contracts";

import { loadServiceOrderReviewCatalog } from "./service-order-review-api.js";
import { buildServiceOrderReviewCatalogView } from "./service-order-review-scenarios.js";

const CATALOG_FIXTURE = serviceOrderReviewCatalogSchema.parse({
  selectedScenarioId: "review-blocked",
  scenarios: [
    {
      id: "review-ready",
      label: "OS pronta para revisao",
      description: "Tudo consistente.",
      summary: {
        status: "ready",
        headline: "OS pronta para concluir a revisao tecnica",
        totalCount: 4,
        awaitingReviewCount: 1,
        awaitingSignatureCount: 1,
        inExecutionCount: 1,
        emittedCount: 1,
        blockedCount: 0,
        recommendedAction: "Aprovar a revisao.",
        blockers: [],
        warnings: [],
      },
      selectedItemId: "os-2026-00142",
      items: [
        {
          itemId: "os-2026-00142",
          workOrderNumber: "OS-2026-00142",
          customerName: "Industria Horizonte",
          equipmentLabel: "Balanca IPNA 300 kg | Prix 3 | Toledo",
          status: "awaiting_review",
          technicianName: "Joao Executor",
          updatedAtLabel: "14:22",
        },
      ],
      detail: {
        itemId: "os-2026-00142",
        title: "OS-2026-00142 · Industria Horizonte · Balanca IPNA 300 kg | Prix 3 | Toledo",
        status: "ready",
        statusLine: "Aguardando revisao.",
        executorLabel: "Joao Executor",
        assignedReviewerLabel: "Maria Revisora",
        procedureLabel: "PT-005 rev.04",
        standardsLabel: "PESO-001 / PESO-002 / TH-003",
        environmentLabel: "22.4 C",
        curvePointsLabel: "5 pontos",
        evidenceLabel: "12 evidencias",
        uncertaintyLabel: "0.05 kg",
        conformityLabel: "Aprovado",
        timeline: [
          {
            key: "created",
            label: "Criada",
            status: "complete",
            timestampLabel: "12/04 09:01",
          },
        ],
        metrics: [
          {
            label: "Repetibilidade",
            value: "sigma = 0,058 kg",
            tone: "ok",
          },
        ],
        checklist: [
          {
            label: "Padroes validos",
            status: "passed",
            detail: "Ok",
          },
        ],
        commentDraft: "Revisao liberada.",
        allowedActions: ["approve_review", "open_preview"],
        blockers: [],
        warnings: [],
        links: {
          workspaceScenarioId: "baseline-ready",
          previewScenarioId: "type-b-ready",
          reviewSignatureScenarioId: "segregated-ready",
        },
      },
    },
    {
      id: "review-blocked",
      label: "OS bloqueada na revisao",
      description: "Conflito de atribuicao.",
      summary: {
        status: "blocked",
        headline: "OS bloqueada antes da aprovacao tecnica",
        totalCount: 4,
        awaitingReviewCount: 0,
        awaitingSignatureCount: 1,
        inExecutionCount: 1,
        emittedCount: 1,
        blockedCount: 1,
        recommendedAction: "Regularizar o revisor.",
        blockers: ["Revisor atual coincide com o executor desta OS."],
        warnings: ["Campo livre inadequado."],
      },
      selectedItemId: "os-2026-00147",
      items: [
        {
          itemId: "os-2026-00147",
          workOrderNumber: "OS-2026-00147",
          customerName: "Cliente sem cadastro completo",
          equipmentLabel: "Balanca plataforma 500 kg | Plataforma 500 | Marte",
          status: "blocked",
          technicianName: "Joao Executor",
          updatedAtLabel: "42 min",
        },
      ],
      detail: {
        itemId: "os-2026-00147",
        title: "OS-2026-00147 · Cliente sem cadastro completo · Balanca plataforma 500 kg | Plataforma 500 | Marte",
        status: "blocked",
        statusLine: "Revisao bloqueada.",
        executorLabel: "Joao Executor",
        assignedReviewerLabel: "Renata Qualidade",
        procedureLabel: "PT-009 rev.02",
        standardsLabel: "PESO-009 / TH-404",
        environmentLabel: "28.1 C",
        curvePointsLabel: "4 pontos preliminares",
        evidenceLabel: "5 evidencias",
        uncertaintyLabel: "0.12 kg",
        conformityLabel: "Indeterminada",
        timeline: [
          {
            key: "review",
            label: "Revisao",
            status: "current",
            timestampLabel: "Bloqueada",
          },
        ],
        metrics: [
          {
            label: "Segregacao",
            value: "Conflito",
            tone: "warn",
          },
        ],
        checklist: [
          {
            label: "Segregacao do revisor",
            status: "failed",
            detail: "Revisor coincide com executor.",
          },
        ],
        commentDraft: "Revisao bloqueada.",
        allowedActions: ["return_to_technician", "open_preview"],
        blockers: ["Revisor atual coincide com o executor desta OS."],
        warnings: ["Campo livre inadequado."],
        links: {
          workspaceScenarioId: "release-blocked",
          previewScenarioId: "type-c-blocked",
          reviewSignatureScenarioId: "reviewer-conflict",
        },
      },
    },
  ],
});

test("selects the active service-order review scenario from the backend catalog", () => {
  const view = buildServiceOrderReviewCatalogView(CATALOG_FIXTURE);

  assert.equal(view.selectedScenario.id, "review-blocked");
  assert.equal(view.selectedScenario.selectedItem.itemId, "os-2026-00147");
  assert.match(view.selectedScenario.summaryLabel, /1 OS bloqueada\(s\)/i);
});

test("loads and validates the service-order review catalog from the backend endpoint", async () => {
  const catalog = await loadServiceOrderReviewCatalog({
    scenarioId: "review-ready",
    itemId: "os-2026-00142",
    apiBaseUrl: "http://127.0.0.1:3000",
    fetchImpl: async (input) => {
      assert.equal(
        String(input),
        "http://127.0.0.1:3000/emission/service-order-review?scenario=review-ready&item=os-2026-00142",
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
  assert.equal(catalog.selectedScenarioId, "review-blocked");
  assert.equal(catalog.scenarios.length, 2);
});

test("fails closed when the service-order review backend payload is invalid", async () => {
  const catalog = await loadServiceOrderReviewCatalog({
    fetchImpl: async () =>
      new Response(JSON.stringify({ selectedScenarioId: "review-ready", scenarios: [] }), {
        status: 200,
        headers: {
          "content-type": "application/json",
        },
      }),
  });

  assert.equal(catalog, null);
});
