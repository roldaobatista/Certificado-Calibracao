import assert from "node:assert/strict";
import { test } from "node:test";

import { nonconformityRegistryCatalogSchema } from "@afere/contracts";

import { loadNonconformityCatalog } from "./nonconformity-api.js";
import { buildNonconformityCatalogView } from "./nonconformity-scenarios.js";

const CATALOG_FIXTURE = nonconformityRegistryCatalogSchema.parse({
  selectedScenarioId: "critical-response",
  scenarios: [
    {
      id: "open-attention",
      label: "NC aberta em acompanhamento",
      description: "Acompanhamento.",
      summary: {
        status: "attention",
        headline: "NC aberta exige acompanhamento da qualidade",
        openCount: 2,
        criticalCount: 1,
        closedCount: 1,
        recommendedAction: "Concluir acao corretiva.",
        blockers: [],
        warnings: ["Acao corretiva vence em 2 dias e ainda depende de evidência complementar."],
      },
      selectedNcId: "nc-014",
      items: [
        {
          ncId: "nc-014",
          summary: "Padrao usado proximo ao vencimento em janela operacional critica.",
          originLabel: "Auditoria interna",
          severityLabel: "Media",
          ownerLabel: "Maria Souza",
          ageLabel: "12d",
          status: "attention",
        },
      ],
      detail: {
        ncId: "nc-014",
        title: "NC-014 · Padrao usado proximo ao vencimento",
        status: "attention",
        noticeLabel: "NC aberta sob acompanhamento e ação corretiva.",
        originLabel: "Auditoria interna",
        severityLabel: "Media",
        ownerLabel: "Maria Souza",
        openedAtLabel: "10/04/2026",
        dueAtLabel: "24/04/2026",
        rootCauseLabel: "Planejamento preventivo tardio.",
        containmentLabel: "Dupla conferencia.",
        correctiveActionLabel: "Antecipar recalibracao.",
        evidenceLabel: "NC-014 e FR-030.",
        blockers: [],
        warnings: ["Acao corretiva vence em 2 dias e ainda depende de evidência complementar."],
        links: {
          workspaceScenarioId: "team-attention",
          auditTrailScenarioId: "reissue-attention",
          procedureScenarioId: "revision-attention",
          serviceOrderScenarioId: "history-pending",
          reviewItemId: "os-2026-00141",
        },
      },
    },
    {
      id: "critical-response",
      label: "NC critica bloqueante",
      description: "Resposta critica.",
      summary: {
        status: "blocked",
        headline: "NC critica bloqueia o fluxo operacional relacionado",
        openCount: 2,
        criticalCount: 1,
        closedCount: 1,
        recommendedAction: "Priorizar investigacao.",
        blockers: ["NC critica aberta com impacto direto no fluxo de emissao."],
        warnings: ["Cliente aguarda posicionamento formal da investigacao."],
      },
      selectedNcId: "nc-015",
      items: [
        {
          ncId: "nc-015",
          summary: "Divergencia reportada pelo cliente com impacto potencial em emissao ja concluida.",
          originLabel: "Reclamacao de cliente",
          severityLabel: "Alta",
          ownerLabel: "Joao Silva",
          ageLabel: "3d",
          status: "blocked",
        },
      ],
      detail: {
        ncId: "nc-015",
        title: "NC-015 · Cliente reportou divergencia de valor",
        status: "blocked",
        noticeLabel: "NC crítica aberta com impacto bloqueante na operação.",
        originLabel: "Reclamacao de cliente",
        severityLabel: "Alta",
        ownerLabel: "Joao Silva",
        openedAtLabel: "19/04/2026",
        dueAtLabel: "22/04/2026",
        rootCauseLabel: "Suspeita de inconsistência.",
        containmentLabel: "Fluxo congelado.",
        correctiveActionLabel: "Executar investigacao.",
        evidenceLabel: "Reclamacao formal.",
        blockers: ["NC critica aberta com impacto direto no fluxo de emissao."],
        warnings: ["Cliente aguarda posicionamento formal da investigacao."],
        links: {
          workspaceScenarioId: "release-blocked",
          auditTrailScenarioId: "integrity-blocked",
          procedureScenarioId: "revision-attention",
          serviceOrderScenarioId: "review-blocked",
          reviewItemId: "os-2026-00147",
        },
      },
    },
  ],
});

test("selects the active nonconformity scenario from the backend catalog", () => {
  const view = buildNonconformityCatalogView(CATALOG_FIXTURE);

  assert.equal(view.selectedScenario.id, "critical-response");
  assert.equal(view.selectedScenario.selectedNc.ncId, "nc-015");
  assert.match(view.selectedScenario.summaryLabel, /1 NC\(s\) critica\(s\)/i);
});

test("loads and validates the nonconformity catalog from the backend endpoint", async () => {
  const catalog = await loadNonconformityCatalog({
    scenarioId: "open-attention",
    ncId: "nc-014",
    apiBaseUrl: "http://127.0.0.1:3000",
    fetchImpl: async (input) => {
      assert.equal(
        String(input),
        "http://127.0.0.1:3000/quality/nonconformities?scenario=open-attention&nc=nc-014",
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
  assert.equal(catalog.selectedScenarioId, "critical-response");
  assert.equal(catalog.scenarios.length, 2);
});

test("fails closed when the nonconformity backend payload is invalid", async () => {
  const catalog = await loadNonconformityCatalog({
    fetchImpl: async () =>
      new Response(JSON.stringify({ selectedScenarioId: "open-attention", scenarios: [] }), {
        status: 200,
        headers: {
          "content-type": "application/json",
        },
      }),
  });

  assert.equal(catalog, null);
});
