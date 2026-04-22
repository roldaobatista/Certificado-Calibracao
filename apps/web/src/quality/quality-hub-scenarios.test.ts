import assert from "node:assert/strict";
import { test } from "node:test";

import { qualityHubCatalogSchema } from "@afere/contracts";

import { loadQualityHubCatalog } from "./quality-hub-api.js";
import { buildQualityHubCatalogView } from "./quality-hub-scenarios.js";

const CATALOG_FIXTURE = qualityHubCatalogSchema.parse({
  selectedScenarioId: "operational-attention",
  scenarios: [
    {
      id: "operational-attention",
      label: "Qualidade em acompanhamento preventivo",
      description: "Resumo da qualidade com backlog planejado explicito.",
      selectedModuleKey: "nonconformities",
      summary: {
        status: "attention",
        organizationName: "Lab. Acme",
        openNonconformities: 2,
        overdueActions: 1,
        auditProgramCount: 4,
        complaintCount: 1,
        activeRiskCount: 7,
        implementedModuleCount: 9,
        plannedModuleCount: 0,
        nextManagementReviewLabel: "30/06/2026",
        recommendedAction: "Fechar acao corretiva e acompanhar a reclamacao aberta.",
        blockers: [],
        warnings: ["Backlog planejado explicito."],
      },
      links: {
        workspaceScenarioId: "team-attention",
        organizationSettingsScenarioId: "renewal-attention",
        auditTrailScenarioId: "reissue-attention",
        nonconformityScenarioId: "open-attention",
      },
      modules: [
        {
          key: "nonconformities",
          title: "NC e acoes corretivas",
          clauseLabel: "ISO/IEC 17025 7.10 e 8.7",
          metricLabel: "2 NC abertas · 1 acao vencendo",
          summary: "Modulo ja implementado.",
          status: "attention",
          availability: "implemented",
          href: "/quality/nonconformities?scenario=open-attention&nc=nc-014",
          ctaLabel: "Abrir NCs",
          nextStepLabel: "Fechar a acao corretiva.",
          blockers: [],
          warnings: ["NC critica segue em paralelo."],
        },
        {
          key: "complaints",
          title: "Reclamacoes",
          clauseLabel: "ISO/IEC 17025 7.9",
          metricLabel: "1 reclamacao aberta",
          summary: "Modulo implementado para resposta formal e rastreabilidade.",
          status: "attention",
          availability: "implemented",
          href: "/quality/complaints?scenario=open-follow-up&complaint=recl-004",
          ctaLabel: "Abrir reclamacoes",
          nextStepLabel: "Responder a reclamacao dentro do prazo.",
          blockers: [],
          warnings: ["Uma reclamacao aberta segue aguardando resposta formal."],
        },
      ],
    },
    {
      id: "critical-response",
      label: "Qualidade em resposta critica",
      description: "Fail-closed por integridade.",
      selectedModuleKey: "audit-trail",
      summary: {
        status: "blocked",
        organizationName: "Lab. Acme",
        openNonconformities: 1,
        overdueActions: 2,
        auditProgramCount: 4,
        complaintCount: 2,
        activeRiskCount: 9,
        implementedModuleCount: 9,
        plannedModuleCount: 0,
        nextManagementReviewLabel: "Hoje · extraordinaria",
        recommendedAction: "Congelar o fluxo.",
        blockers: ["Falha de integridade."],
        warnings: [],
      },
      links: {
        workspaceScenarioId: "release-blocked",
        organizationSettingsScenarioId: "profile-change-blocked",
        auditTrailScenarioId: "integrity-blocked",
        nonconformityScenarioId: "critical-response",
      },
      modules: [
        {
          key: "audit-trail",
          title: "Trilha de auditoria",
          clauseLabel: "ISO/IEC 17025 7.5 e 8.4",
          metricLabel: "1 falha de integridade",
          summary: "Modulo implementado e bloqueante.",
          status: "blocked",
          availability: "implemented",
          href: "/quality/audit-trail?scenario=integrity-blocked&event=audit-9",
          ctaLabel: "Abrir trilha",
          nextStepLabel: "Investigar a hash-chain.",
          blockers: ["Hash-chain divergente."],
          warnings: [],
        },
      ],
    },
  ],
});

test("selects the active quality hub scenario from the backend catalog", () => {
  const view = buildQualityHubCatalogView(CATALOG_FIXTURE);

  assert.equal(view.selectedScenario.id, "operational-attention");
  assert.equal(view.selectedScenario.selectedModule.key, "nonconformities");
  assert.match(view.selectedScenario.summaryLabel, /2 NC\(s\) aberta\(s\)/i);
});

test("loads and validates the quality hub catalog from the backend endpoint", async () => {
  const catalog = await loadQualityHubCatalog({
    scenarioId: "critical-response",
    moduleKey: "audit-trail",
    apiBaseUrl: "http://127.0.0.1:3000",
    fetchImpl: async (input) => {
      assert.equal(
        String(input),
        "http://127.0.0.1:3000/quality?scenario=critical-response&module=audit-trail",
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
  assert.equal(catalog.selectedScenarioId, "operational-attention");
  assert.equal(catalog.scenarios.length, 2);
});

test("fails closed when the quality hub backend payload is invalid", async () => {
  const catalog = await loadQualityHubCatalog({
    fetchImpl: async () =>
      new Response(JSON.stringify({ selectedScenarioId: "operational-attention", scenarios: [] }), {
        status: 200,
        headers: {
          "content-type": "application/json",
        },
      }),
  });

  assert.equal(catalog, null);
});
