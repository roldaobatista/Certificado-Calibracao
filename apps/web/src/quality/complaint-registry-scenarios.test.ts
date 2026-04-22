import assert from "node:assert/strict";
import { test } from "node:test";

import { complaintRegistryCatalogSchema } from "@afere/contracts";

import { loadComplaintCatalog } from "./complaint-registry-api.js";
import { buildComplaintCatalogView } from "./complaint-registry-scenarios.js";

const CATALOG_FIXTURE = complaintRegistryCatalogSchema.parse({
  selectedScenarioId: "critical-response",
  scenarios: [
    {
      id: "open-follow-up",
      label: "Reclamacao aberta em acompanhamento",
      description: "Resposta tecnica em preparo.",
      summary: {
        status: "attention",
        headline: "Reclamacao aberta exige resposta formal da Qualidade",
        openCount: 2,
        overdueCount: 0,
        reissuePendingCount: 0,
        resolvedLast30d: 1,
        recommendedAction: "Responder dentro do prazo.",
        blockers: [],
        warnings: ["Prazo de resposta vence em menos de 48h uteis."],
      },
      selectedComplaintId: "recl-004",
      items: [
        {
          complaintId: "recl-004",
          customerName: "Padaria Pao Doce",
          summary: "Cliente solicitou esclarecimento sobre a faixa usada.",
          channelLabel: "Portal do cliente",
          severityLabel: "Media",
          ownerLabel: "Ana Costa",
          receivedAtLabel: "15/04/2026 10:18",
          status: "attention",
        },
      ],
      detail: {
        complaintId: "recl-004",
        title: "RECL-004 · Cliente pede esclarecimento sobre faixa declarada",
        status: "attention",
        noticeLabel: "Reclamacao aberta em acompanhamento com resposta formal em preparo.",
        customerName: "Padaria Pao Doce",
        channelLabel: "Portal do cliente",
        ownerLabel: "Ana Costa",
        receivedAtLabel: "15/04/2026 10:18",
        responseDeadlineLabel: "17/04/2026 10:18",
        narrative: "Narrativa do cliente.",
        linkedNonconformityLabel: "Triagem inicial sem NC aberta.",
        evidenceLabel: "RECL-004 e minuta da resposta.",
        actions: [
          {
            key: "acknowledge",
            label: "Acuso de recebimento",
            status: "complete",
            detail: "Confirmado ao cliente.",
          },
        ],
        blockers: [],
        warnings: ["Prazo curto."],
        links: {
          workspaceScenarioId: "team-attention",
          auditTrailScenarioId: "recent-emission",
          serviceOrderScenarioId: "history-pending",
          reviewItemId: "os-2026-00141",
        },
      },
    },
    {
      id: "critical-response",
      label: "Reclamacao critica com reemissao pendente",
      description: "Erro cadastral com reemissao pendente.",
      summary: {
        status: "blocked",
        headline: "Reclamacao critica bloqueia o encerramento e exige reemissao",
        openCount: 2,
        overdueCount: 1,
        reissuePendingCount: 1,
        resolvedLast30d: 1,
        recommendedAction: "Iniciar a reemissao e responder o cliente.",
        blockers: ["Cliente sem resposta conclusiva."],
        warnings: [],
      },
      selectedComplaintId: "recl-007",
      items: [
        {
          complaintId: "recl-007",
          customerName: "Lab. Acme",
          summary: "Cliente reportou TAG incorreta.",
          channelLabel: "E-mail",
          severityLabel: "Alta",
          ownerLabel: "Joao Silva",
          receivedAtLabel: "17/04/2026 14:05",
          status: "blocked",
        },
      ],
      detail: {
        complaintId: "recl-007",
        title: "RECL-007 · Tag incorreta no certificado emitido",
        status: "blocked",
        noticeLabel: "Reclamacao critica aberta com impacto direto no fluxo e na resposta ao cliente.",
        customerName: "Lab. Acme",
        channelLabel: "E-mail",
        ownerLabel: "Joao Silva",
        receivedAtLabel: "17/04/2026 14:05",
        responseDeadlineLabel: "21/04/2026 14:05",
        narrative: "Narrativa do cliente.",
        linkedNonconformityLabel: "NC-015 aberta.",
        reissueReasonLabel: "DADO_CADASTRAL",
        evidenceLabel: "RECL-007 e checklist de reemissao.",
        actions: [
          {
            key: "start-reissue",
            label: "Iniciar fluxo de reemissao",
            status: "pending",
            detail: "Ainda pendente.",
          },
        ],
        blockers: ["Reemissao pendente."],
        warnings: [],
        links: {
          workspaceScenarioId: "release-blocked",
          auditTrailScenarioId: "reissue-attention",
          nonconformityScenarioId: "critical-response",
          nonconformityId: "nc-015",
          serviceOrderScenarioId: "review-blocked",
          reviewItemId: "os-2026-00147",
        },
      },
    },
  ],
});

test("selects the active complaint scenario from the backend catalog", () => {
  const view = buildComplaintCatalogView(CATALOG_FIXTURE);

  assert.equal(view.selectedScenario.id, "critical-response");
  assert.equal(view.selectedScenario.selectedComplaint.complaintId, "recl-007");
  assert.match(view.selectedScenario.summaryLabel, /1 reemissao\(oes\) pendente\(s\)/i);
});

test("loads and validates the complaint catalog from the backend endpoint", async () => {
  const catalog = await loadComplaintCatalog({
    scenarioId: "critical-response",
    complaintId: "recl-007",
    apiBaseUrl: "http://127.0.0.1:3000",
    fetchImpl: async (input) => {
      assert.equal(
        String(input),
        "http://127.0.0.1:3000/quality/complaints?scenario=critical-response&complaint=recl-007",
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

test("fails closed when the complaint backend payload is invalid", async () => {
  const catalog = await loadComplaintCatalog({
    fetchImpl: async () =>
      new Response(JSON.stringify({ selectedScenarioId: "critical-response", scenarios: [] }), {
        status: 200,
        headers: {
          "content-type": "application/json",
        },
      }),
  });

  assert.equal(catalog, null);
});
