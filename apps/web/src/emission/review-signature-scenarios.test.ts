import assert from "node:assert/strict";
import { test } from "node:test";

import { reviewSignatureCatalogSchema } from "@afere/contracts";

import { loadReviewSignatureCatalog } from "./review-signature-api.js";
import { buildReviewSignatureCatalogView } from "./review-signature-scenarios.js";

const CATALOG_FIXTURE = reviewSignatureCatalogSchema.parse({
  selectedScenarioId: "signatory-mfa-blocked",
  scenarios: [
    {
      id: "segregated-ready",
      label: "Workflow segregado e pronto",
      description: "Fluxo liberado para revisao.",
      result: {
        status: "ready",
        stage: "in_review",
        summary: "Revisao tecnica liberada e assinatura futura preparada com segregacao valida.",
        blockers: [],
        warnings: [],
        allowedActions: ["review_certificate", "reject_to_executor"],
        reviewStep: {
          title: "Revisao tecnica",
          status: "ready",
          actorLabel: "Maria Revisora",
          detail: "A revisao tecnica pode seguir.",
        },
        signatureStep: {
          title: "Assinatura e emissao",
          status: "pending",
          actorLabel: "Carlos Signatario",
          detail: "Aguardando aprovacao da revisao.",
        },
        checks: [],
        assignments: {
          executor: {
            userId: "tech-1",
            displayName: "Joao Executor",
            roles: ["technician"],
            mfaEnabled: false,
            pendingAssignments: 0,
          },
          reviewer: {
            userId: "reviewer-1",
            displayName: "Maria Revisora",
            roles: ["technical_reviewer"],
            mfaEnabled: false,
            pendingAssignments: 1,
          },
          signatory: {
            userId: "signatory-1",
            displayName: "Carlos Signatario",
            roles: ["signatory"],
            mfaEnabled: true,
            pendingAssignments: 2,
          },
        },
        suggestions: {},
      },
    },
    {
      id: "signatory-mfa-blocked",
      label: "Assinatura bloqueada por MFA",
      description: "Emissao falha fechado sem MFA.",
      result: {
        status: "blocked",
        stage: "approved",
        summary: "Workflow bloqueado por autorizacao incompleta ou segregacao de funcoes invalida.",
        blockers: ["signatario sem MFA obrigatorio para concluir a emissao"],
        warnings: [],
        allowedActions: [],
        reviewStep: {
          title: "Revisao tecnica",
          status: "complete",
          actorLabel: "Maria Revisora",
          detail: "A revisao tecnica ja foi concluida.",
        },
        signatureStep: {
          title: "Assinatura e emissao",
          status: "blocked",
          actorLabel: "Paula Assinatura",
          detail: "A assinatura segue bloqueada.",
        },
        checks: [],
        assignments: {
          executor: {
            userId: "tech-1",
            displayName: "Joao Executor",
            roles: ["technician"],
            mfaEnabled: false,
            pendingAssignments: 0,
          },
          reviewer: {
            userId: "reviewer-1",
            displayName: "Maria Revisora",
            roles: ["technical_reviewer"],
            mfaEnabled: false,
            pendingAssignments: 1,
          },
          signatory: {
            userId: "signatory-1",
            displayName: "Carlos Signatario",
            roles: ["signatory"],
            mfaEnabled: false,
            pendingAssignments: 2,
          },
        },
        suggestions: {
          signatory: {
            userId: "signatory-2",
            displayName: "Paula Assinatura",
            rationale: "Menor fila entre signatarios elegiveis com MFA obrigatorio ativo.",
          },
        },
      },
    },
  ],
});

test("selects the active review/signature workflow scenario from the backend catalog", () => {
  const view = buildReviewSignatureCatalogView(CATALOG_FIXTURE);

  assert.equal(view.selectedScenario.id, "signatory-mfa-blocked");
  assert.equal(view.selectedScenario.summary.status, "blocked");
  assert.equal(view.selectedScenario.summary.headline, "Workflow bloqueado");
  assert.equal(view.selectedScenario.summary.signatureStatusLabel, "Assinatura: bloqueada");
});

test("loads and validates the review/signature catalog from the backend endpoint", async () => {
  const catalog = await loadReviewSignatureCatalog({
    scenarioId: "reviewer-conflict",
    apiBaseUrl: "http://127.0.0.1:3000",
    fetchImpl: async (input) => {
      assert.equal(
        String(input),
        "http://127.0.0.1:3000/emission/review-signature?scenario=reviewer-conflict",
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
  assert.equal(catalog.selectedScenarioId, "signatory-mfa-blocked");
  assert.equal(catalog.scenarios.length, 2);
});

test("fails closed when the review/signature backend payload is invalid", async () => {
  const catalog = await loadReviewSignatureCatalog({
    fetchImpl: async () =>
      new Response(JSON.stringify({ selectedScenarioId: "segregated-ready", scenarios: [] }), {
        status: 200,
        headers: {
          "content-type": "application/json",
        },
      }),
  });

  assert.equal(catalog, null);
});
