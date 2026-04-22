import assert from "node:assert/strict";
import { test } from "node:test";

import { procedureRegistryCatalogSchema } from "@afere/contracts";

import { loadProcedureRegistryCatalog } from "./procedure-registry-api.js";
import { buildProcedureRegistryCatalogView } from "./procedure-registry-scenarios.js";

const CATALOG_FIXTURE = procedureRegistryCatalogSchema.parse({
  selectedScenarioId: "revision-attention",
  scenarios: [
    {
      id: "operational-ready",
      label: "Procedimentos vigentes prontos para uso",
      description: "Tudo verde.",
      summary: {
        status: "ready",
        headline: "Procedimentos vigentes prontos para sustentar a operacao",
        activeCount: 3,
        attentionCount: 1,
        obsoleteCount: 1,
        recommendedAction: "Seguir operacao.",
        blockers: [],
        warnings: [],
      },
      selectedProcedureId: "procedure-pt005-r04",
      items: [
        {
          procedureId: "procedure-pt005-r04",
          code: "PT-005",
          title: "Calibracao IPNA classe III campo",
          typeLabel: "NAWI III",
          revisionLabel: "04",
          effectiveSinceLabel: "desde 03/24",
          lifecycleLabel: "Vigente",
          usageLabel: "Campo controlado",
          status: "ready",
        },
      ],
      detail: {
        procedureId: "procedure-pt005-r04",
        title: "PT-005 rev.04 · Calibracao IPNA classe III campo",
        status: "ready",
        noticeLabel: "Vigente e liberado para uso no recorte atual.",
        scopeLabel: "Balanças IPNA classe III.",
        environmentRangeLabel: "Temp 18C-25C · Umid 30%-70%",
        curvePolicyLabel: "5 pontos.",
        standardsPolicyLabel: "Padrao F1/M1.",
        approvalLabel: "Aprovado por Ana Costa.",
        relatedDocuments: ["IT-005-1"],
        blockers: [],
        warnings: [],
        links: {
          workspaceScenarioId: "baseline-ready",
          serviceOrderScenarioId: "review-ready",
          reviewItemId: "os-2026-00142",
          dryRunScenarioId: "type-b-ready",
        },
      },
    },
    {
      id: "revision-attention",
      label: "Procedimento com revisao proxima",
      description: "Atencao preventiva.",
      summary: {
        status: "attention",
        headline: "Procedimento vigente exige revisao preventiva",
        activeCount: 3,
        attentionCount: 1,
        obsoleteCount: 1,
        recommendedAction: "Concluir revisao.",
        blockers: [],
        warnings: ["Revisao da qualidade agendada para 30/04/2026."],
      },
      selectedProcedureId: "procedure-pt009-r02",
      items: [
        {
          procedureId: "procedure-pt009-r02",
          code: "PT-009",
          title: "Calibracao IPNA ambiente ampliado",
          typeLabel: "NAWI III especial",
          revisionLabel: "02",
          effectiveSinceLabel: "desde 02/24",
          lifecycleLabel: "Vigente com revisao pendente",
          usageLabel: "Campo com condicoes variaveis",
          status: "attention",
        },
      ],
      detail: {
        procedureId: "procedure-pt009-r02",
        title: "PT-009 rev.02 · Calibracao IPNA ambiente ampliado",
        status: "attention",
        noticeLabel: "Vigente com revisao pendente.",
        scopeLabel: "Balanças IPNA classe III especiais.",
        environmentRangeLabel: "Temp 18C-25C · Umid 30%-70%",
        curvePolicyLabel: "5 pontos com conferencia historica.",
        standardsPolicyLabel: "Padroes M1 vigentes.",
        approvalLabel: "Revisao de qualidade aberta.",
        relatedDocuments: ["FR-030", "NC-014"],
        blockers: [],
        warnings: ["Revisao da qualidade agendada para 30/04/2026."],
        links: {
          workspaceScenarioId: "team-attention",
          serviceOrderScenarioId: "review-blocked",
          reviewItemId: "os-2026-00147",
          dryRunScenarioId: "type-c-blocked",
        },
      },
    },
  ],
});

test("selects the active procedure registry scenario from the backend catalog", () => {
  const view = buildProcedureRegistryCatalogView(CATALOG_FIXTURE);

  assert.equal(view.selectedScenario.id, "revision-attention");
  assert.equal(view.selectedScenario.selectedProcedure.procedureId, "procedure-pt009-r02");
  assert.match(view.selectedScenario.summaryLabel, /1 procedimento\(s\) em atencao/i);
});

test("loads and validates the procedure registry catalog from the backend endpoint", async () => {
  const catalog = await loadProcedureRegistryCatalog({
    scenarioId: "operational-ready",
    procedureId: "procedure-pt005-r04",
    apiBaseUrl: "http://127.0.0.1:3000",
    fetchImpl: async (input) => {
      assert.equal(
        String(input),
        "http://127.0.0.1:3000/registry/procedures?scenario=operational-ready&procedure=procedure-pt005-r04",
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
  assert.equal(catalog.selectedScenarioId, "revision-attention");
  assert.equal(catalog.scenarios.length, 2);
});

test("fails closed when the procedure registry backend payload is invalid", async () => {
  const catalog = await loadProcedureRegistryCatalog({
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
