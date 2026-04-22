import assert from "node:assert/strict";
import { test } from "node:test";

import { portalCertificateCatalogSchema } from "@afere/contracts";

import { loadPortalCertificateCatalog } from "./portal-certificate-api.js";
import { buildPortalCertificateCatalogView } from "./portal-certificate-scenarios.js";

const CATALOG_FIXTURE = portalCertificateCatalogSchema.parse({
  selectedScenarioId: "reissued-history",
  scenarios: [
    {
      id: "current-valid",
      label: "Certificado valido",
      description: "Viewer autenticado pronto.",
      summary: {
        status: "ready",
        headline: "Viewer pronto",
        totalCertificates: 2,
        readyCount: 1,
        attentionCount: 1,
        blockedCount: 0,
        recommendedAction: "Usar viewer.",
        blockers: [],
        warnings: [],
      },
      selectedCertificateId: "cert-00142",
      items: [
        {
          certificateId: "cert-00142",
          certificateNumber: "CAL-1234/2026/00142",
          equipmentLabel: "BAL-007 Toledo Prix 3",
          issuedAtLabel: "19/04/2026",
          statusLabel: "Valido",
          verifyScenarioId: "authentic",
          status: "ready",
        },
      ],
      detail: {
        certificateId: "cert-00142",
        title: "CAL-1234/2026/00142 - BAL-007 Toledo Prix 3",
        status: "ready",
        hashLabel: "a3f9c12d...",
        signatureLabel: "Assinatura verificada",
        viewerLabel: "Previa integral disponivel.",
        publicLinkLabel: "verifica.afere.com.br/c/a3f9c12d",
        recommendedAction: "Usar viewer.",
        metadataFields: [{ label: "Status", value: "Valido" }],
        actions: [{ key: "download_pdf", label: "Baixar PDF", status: "ready" }],
        verificationSteps: ["Conferir o QR."],
        blockers: [],
        warnings: [],
        equipmentId: "equipment-bal-007",
        equipmentScenarioId: "stable-portfolio",
        dashboardScenarioId: "stable-portfolio",
        publicVerifyScenarioId: "authentic",
      },
    },
    {
      id: "reissued-history",
      label: "Reemissao rastreada",
      description: "Viewer com indicacao de reemissao.",
      summary: {
        status: "attention",
        headline: "Reemissao rastreada",
        totalCertificates: 2,
        readyCount: 1,
        attentionCount: 1,
        blockedCount: 0,
        recommendedAction: "Conferir revisao vigente.",
        blockers: [],
        warnings: ["Ha uma revisao anterior preservada apenas como historico."],
      },
      selectedCertificateId: "cert-00135-r1",
      items: [
        {
          certificateId: "cert-00135-r1",
          certificateNumber: "CAL-1234/2026/00135-R1",
          equipmentLabel: "BAL-019 Toledo Prix 15",
          issuedAtLabel: "14/04/2026",
          statusLabel: "Reemitido",
          verifyScenarioId: "reissued",
          status: "attention",
        },
      ],
      detail: {
        certificateId: "cert-00135-r1",
        title: "CAL-1234/2026/00135-R1 - BAL-019 Toledo Prix 15",
        status: "attention",
        hashLabel: "d44bc871...",
        signatureLabel: "Assinatura verificada com rastreio de reemissao",
        viewerLabel: "Previa integral disponivel.",
        publicLinkLabel: "verifica.afere.com.br/c/d44bc871",
        recommendedAction: "Conferir revisao vigente.",
        metadataFields: [{ label: "Status", value: "Reemitido" }],
        actions: [{ key: "download_pdf", label: "Baixar PDF", status: "attention" }],
        verificationSteps: ["Conferir a ultima revisao."],
        blockers: [],
        warnings: ["Ha uma revisao anterior preservada apenas como historico."],
        equipmentId: "equipment-bal-019",
        equipmentScenarioId: "overdue-blocked",
        dashboardScenarioId: "overdue-blocked",
        publicVerifyScenarioId: "reissued",
      },
    },
  ],
});

test("selects the active portal certificate scenario and detail from the backend catalog", () => {
  const view = buildPortalCertificateCatalogView(CATALOG_FIXTURE);

  assert.equal(view.selectedScenario.id, "reissued-history");
  assert.equal(view.selectedScenario.selectedCertificate.certificateId, "cert-00135-r1");
  assert.match(view.selectedScenario.summaryLabel, /reemissao rastreada/i);
});

test("loads and validates the portal certificate catalog from the backend endpoint", async () => {
  const catalog = await loadPortalCertificateCatalog({
    scenarioId: "reissued-history",
    certificateId: "cert-00135-r1",
    fetchImpl: async (input) => {
      assert.equal(
        String(input),
        "http://127.0.0.1:3000/portal/certificate?scenario=reissued-history&certificate=cert-00135-r1",
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
  assert.equal(catalog.selectedScenarioId, "reissued-history");
});

test("fails closed when the portal certificate backend payload is invalid", async () => {
  const catalog = await loadPortalCertificateCatalog({
    fetchImpl: async () =>
      new Response(JSON.stringify({ selectedScenarioId: "reissued-history", scenarios: [] }), {
        status: 200,
        headers: {
          "content-type": "application/json",
        },
      }),
  });

  assert.equal(catalog, null);
});
