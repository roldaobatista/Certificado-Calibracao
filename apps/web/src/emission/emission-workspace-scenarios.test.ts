import assert from "node:assert/strict";
import { test } from "node:test";

import { emissionWorkspaceCatalogSchema } from "@afere/contracts";

import { loadEmissionWorkspaceCatalog } from "./emission-workspace-api.js";
import { buildEmissionWorkspaceCatalogView } from "./emission-workspace-scenarios.js";

const CATALOG_FIXTURE = emissionWorkspaceCatalogSchema.parse({
  selectedScenarioId: "team-attention",
  scenarios: [
    {
      id: "baseline-ready",
      label: "Baseline operacional pronta",
      description: "Tudo alinhado para seguir.",
      summary: {
        status: "ready",
        headline: "Operacao pronta para seguir com revisao e assinatura",
        readyToEmit: false,
        recommendedAction: "Concluir a revisao tecnica da OS atual para liberar a assinatura.",
        readyModules: 5,
        attentionModules: 0,
        blockedModules: 0,
        blockers: [],
        warnings: [],
      },
      modules: [
        {
          key: "auth",
          title: "Auth e auto-cadastro",
          status: "ready",
          detail: "Signatario pronto com provedores obrigatorios ativos e MFA prevista.",
          href: "/auth/self-signup?scenario=signatory-ready",
        },
      ],
      references: {
        selfSignupScenarioId: "signatory-ready",
        onboardingScenarioId: "ready",
        userDirectoryScenarioId: "operational-team",
        dryRunScenarioId: "type-b-ready",
        reviewSignatureScenarioId: "segregated-ready",
      },
      nextActions: ["Concluir a revisao tecnica da OS corrente."],
    },
    {
      id: "team-attention",
      label: "Equipe em atencao preventiva",
      description: "Competencias proximas do vencimento.",
      summary: {
        status: "attention",
        headline: "Operacao exige acao preventiva antes da assinatura",
        readyToEmit: false,
        recommendedAction: "Renovar as competencias que estao expirando antes da proxima janela de emissao.",
        readyModules: 4,
        attentionModules: 1,
        blockedModules: 0,
        blockers: [],
        warnings: ["Equipe com 1 competencia(s) expirando."],
      },
      modules: [
        {
          key: "team",
          title: "Equipe e competencias",
          status: "attention",
          detail: "Equipe em atencao preventiva: 1 competencia expirando para 4 usuarios ativos.",
          href: "/auth/users?scenario=expiring-competencies",
        },
      ],
      references: {
        selfSignupScenarioId: "admin-guided",
        onboardingScenarioId: "ready",
        userDirectoryScenarioId: "expiring-competencies",
        dryRunScenarioId: "type-b-ready",
        reviewSignatureScenarioId: "segregated-ready",
      },
      nextActions: ["Renovar a autorizacao do signatario antes do vencimento."],
    },
  ],
});

test("selects the active emission workspace scenario from the backend catalog", () => {
  const view = buildEmissionWorkspaceCatalogView(CATALOG_FIXTURE);

  assert.equal(view.selectedScenario.id, "team-attention");
  assert.match(view.selectedScenario.summaryLabel, /1 modulo\(s\) em atencao preventiva/i);
});

test("loads and validates the emission workspace catalog from the backend endpoint", async () => {
  const catalog = await loadEmissionWorkspaceCatalog({
    scenarioId: "baseline-ready",
    apiBaseUrl: "http://127.0.0.1:3000",
    fetchImpl: async (input) => {
      assert.equal(String(input), "http://127.0.0.1:3000/emission/workspace?scenario=baseline-ready");

      return new Response(JSON.stringify(CATALOG_FIXTURE), {
        status: 200,
        headers: {
          "content-type": "application/json",
        },
      });
    },
  });

  assert.ok(catalog);
  assert.equal(catalog.selectedScenarioId, "team-attention");
  assert.equal(catalog.scenarios.length, 2);
});

test("fails closed when the emission workspace backend payload is invalid", async () => {
  const catalog = await loadEmissionWorkspaceCatalog({
    fetchImpl: async () =>
      new Response(JSON.stringify({ selectedScenarioId: "baseline-ready", scenarios: [] }), {
        status: 200,
        headers: {
          "content-type": "application/json",
        },
      }),
  });

  assert.equal(catalog, null);
});
