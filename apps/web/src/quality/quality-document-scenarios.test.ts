import assert from "node:assert/strict";
import { test } from "node:test";

import { qualityDocumentRegistryCatalogSchema } from "@afere/contracts";

import { loadQualityDocumentCatalog } from "./quality-document-api.js";
import { buildQualityDocumentCatalogView } from "./quality-document-scenarios.js";

const CATALOG_FIXTURE = qualityDocumentRegistryCatalogSchema.parse({
  selectedScenarioId: "revision-attention",
  scenarios: [
    {
      id: "revision-attention",
      label: "Documento com revisao preventiva em andamento",
      description: "PG-005 vigente, mas em revisao preventiva.",
      summary: {
        status: "attention",
        headline: "Carteira documental exige revisao preventiva da Qualidade",
        activeCount: 24,
        attentionCount: 1,
        obsoleteCount: 4,
        recommendedAction: "Concluir a revisao preventiva.",
        blockers: [],
        warnings: ["Revisao preventiva em andamento."],
      },
      selectedDocumentId: "document-pg005-r02",
      items: [
        {
          documentId: "document-pg005-r02",
          code: "PG-005",
          title: "Trabalho nao conforme",
          categoryLabel: "Gestao",
          revisionLabel: "02",
          effectiveSinceLabel: "09/2025",
          lifecycleLabel: "Vigente com revisao preventiva",
          ownerLabel: "Ana Costa",
          status: "attention",
        },
      ],
      detail: {
        documentId: "document-pg005-r02",
        title: "PG-005 rev.02 · Trabalho nao conforme",
        status: "attention",
        noticeLabel: "Documento vigente sob revisao preventiva da Qualidade.",
        categoryLabel: "Gestao",
        ownerLabel: "Ana Costa",
        approvalLabel: "Aprovado pela direcao em 09/2025",
        scopeLabel: "Fluxo de contencao e desbloqueio.",
        distributionLabel: "Qualidade e lideres operacionais.",
        revisionPolicyLabel: "Revisao semestral.",
        evidenceLabel: "Minuta de revisao preventiva.",
        relatedArtifacts: ["NC-015", "Checklist de contencao"],
        blockers: [],
        warnings: ["Revisao preventiva em andamento."],
        links: {
          organizationSettingsScenarioId: "renewal-attention",
        },
      },
    },
    {
      id: "obsolete-blocked",
      label: "Revisao obsoleta bloqueada para uso",
      description: "Revisao antiga mantida apenas para historico.",
      summary: {
        status: "blocked",
        headline: "Revisao obsoleta bloqueia o uso documental no recorte atual",
        activeCount: 23,
        attentionCount: 1,
        obsoleteCount: 5,
        recommendedAction: "Migrar para a revisao vigente.",
        blockers: ["Revisao obsoleta bloqueada."],
        warnings: ["Manter apenas para auditoria."],
      },
      selectedDocumentId: "document-pg005-r01",
      items: [
        {
          documentId: "document-pg005-r01",
          code: "PG-005",
          title: "Trabalho nao conforme",
          categoryLabel: "Gestao",
          revisionLabel: "01",
          effectiveSinceLabel: "01/2024",
          effectiveUntilLabel: "09/2025",
          lifecycleLabel: "Obsoleto",
          ownerLabel: "Ana Costa",
          status: "blocked",
        },
      ],
      detail: {
        documentId: "document-pg005-r01",
        title: "PG-005 rev.01 · Trabalho nao conforme",
        status: "blocked",
        noticeLabel: "Revisao obsoleta bloqueada para uso operacional atual.",
        categoryLabel: "Gestao",
        ownerLabel: "Ana Costa",
        approvalLabel: "Substituido pela rev.02 em 09/2025",
        scopeLabel: "Historico apenas.",
        distributionLabel: "Consulta restrita.",
        revisionPolicyLabel: "Historico somente.",
        evidenceLabel: "Ata de substituicao.",
        relatedArtifacts: ["Ata de substituicao da rev.02"],
        blockers: ["Revisao obsoleta nao pode sustentar tratativas novas."],
        warnings: ["Manter apenas para auditoria."],
        links: {
          organizationSettingsScenarioId: "profile-change-blocked",
        },
      },
    },
  ],
});

test("selects the active quality document scenario from the backend catalog", () => {
  const view = buildQualityDocumentCatalogView(CATALOG_FIXTURE);

  assert.equal(view.selectedScenario.id, "revision-attention");
  assert.equal(view.selectedScenario.selectedDocument.documentId, "document-pg005-r02");
  assert.match(view.selectedScenario.summaryLabel, /1 documento\(s\) em revisao/i);
});

test("loads and validates the quality document catalog from the backend endpoint", async () => {
  const catalog = await loadQualityDocumentCatalog({
    scenarioId: "revision-attention",
    documentId: "document-pg005-r02",
    apiBaseUrl: "http://127.0.0.1:3000",
    fetchImpl: async (input) => {
      assert.equal(
        String(input),
        "http://127.0.0.1:3000/quality/documents?scenario=revision-attention&document=document-pg005-r02",
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

test("fails closed when the quality document backend payload is invalid", async () => {
  const catalog = await loadQualityDocumentCatalog({
    fetchImpl: async () =>
      new Response(JSON.stringify({ selectedScenarioId: "revision-attention", scenarios: [] }), {
        status: 200,
        headers: {
          "content-type": "application/json",
        },
      }),
  });

  assert.equal(catalog, null);
});
