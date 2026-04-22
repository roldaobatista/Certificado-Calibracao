import assert from "node:assert/strict";
import { test } from "node:test";

import { organizationSettingsCatalogSchema } from "@afere/contracts";

import { loadOrganizationSettingsCatalog } from "./organization-settings-api.js";
import { buildOrganizationSettingsCatalogView } from "./organization-settings-scenarios.js";

const CATALOG_FIXTURE = organizationSettingsCatalogSchema.parse({
  selectedScenarioId: "renewal-attention",
  scenarios: [
    {
      id: "operational-ready",
      label: "Configuracao operacional controlada",
      description: "Sem bloqueios ativos.",
      summary: {
        status: "ready",
        organizationName: "Lab. Acme",
        organizationCode: "ACME",
        profileLabel: "Tipo A - RBC acreditado",
        accreditationLabel: "Cgcre CAL-1234 valida ate 30/09/2027",
        planLabel: "Enterprise",
        configuredSections: 10,
        attentionSections: 0,
        blockedSections: 0,
        recommendedAction: "Manter governanca.",
        blockers: [],
        warnings: [],
      },
      selectedSectionKey: "regulatory_profile",
      sections: [
        {
          key: "identity",
          title: "Identidade",
          status: "ready",
          detail: "Cadastro consistente.",
          ownerLabel: "Administracao",
          lastUpdatedLabel: "22/04/2026 09:10 UTC",
          actionLabel: "Revisar identidade",
        },
        {
          key: "regulatory_profile",
          title: "Perfil regulatorio",
          status: "ready",
          detail: "Perfil ativo.",
          ownerLabel: "Qualidade",
          lastUpdatedLabel: "22/04/2026 08:50 UTC",
          actionLabel: "Revisar perfil",
        },
      ],
      detail: {
        sectionKey: "regulatory_profile",
        title: "Perfil regulatorio",
        status: "ready",
        summary: "Perfil consistente.",
        evidenceLabel: "Historico auditado.",
        lastReviewedLabel: "22/04/2026 08:50 UTC",
        reviewModeLabel: "Mudancas com dupla aprovacao.",
        checklistItems: ["Perfil Tipo A confirmado."],
        blockers: [],
        warnings: [],
        links: {
          workspaceScenarioId: "baseline-ready",
          auditTrailScenarioId: "recent-emission",
        },
      },
    },
    {
      id: "renewal-attention",
      label: "Renovacao e governanca em atencao",
      description: "Renovacao precisa de acao preventiva.",
      summary: {
        status: "attention",
        organizationName: "Lab. Acme",
        organizationCode: "ACME",
        profileLabel: "Tipo A - RBC acreditado",
        accreditationLabel: "Cgcre CAL-1234 em renovacao ate 30/06/2026",
        planLabel: "Enterprise",
        configuredSections: 5,
        attentionSections: 5,
        blockedSections: 0,
        recommendedAction: "Concluir renovacao.",
        blockers: [],
        warnings: ["Acreditacao perto do vencimento."],
      },
      selectedSectionKey: "lgpd_dpo",
      sections: [
        {
          key: "regulatory_profile",
          title: "Perfil regulatorio",
          status: "attention",
          detail: "Renovacao preventiva aberta.",
          ownerLabel: "Qualidade",
          lastUpdatedLabel: "22/04/2026 08:35 UTC",
          actionLabel: "Renovar acreditacao",
        },
        {
          key: "lgpd_dpo",
          title: "LGPD / DPO",
          status: "attention",
          detail: "Revisao de privacidade pendente.",
          ownerLabel: "Privacidade",
          lastUpdatedLabel: "22/04/2026 08:20 UTC",
          actionLabel: "Atualizar DPO",
        },
      ],
      detail: {
        sectionKey: "lgpd_dpo",
        title: "LGPD / DPO",
        status: "attention",
        summary: "Privacidade precisa de revisao preventiva.",
        evidenceLabel: "Contato existe com revisao pendente.",
        lastReviewedLabel: "22/04/2026 08:20 UTC",
        reviewModeLabel: "Mudancas com rastreio auditavel.",
        checklistItems: ["Contato do DPO publicado."],
        blockers: [],
        warnings: ["Revisao anual ainda nao encerrada."],
        links: {
          workspaceScenarioId: "team-attention",
          auditTrailScenarioId: "reissue-attention",
        },
      },
    },
  ],
});

test("selects the active organization settings scenario and section from the backend catalog", () => {
  const view = buildOrganizationSettingsCatalogView(CATALOG_FIXTURE);

  assert.equal(view.selectedScenario.id, "renewal-attention");
  assert.equal(view.selectedScenario.selectedSection.key, "lgpd_dpo");
  assert.match(view.selectedScenario.summaryLabel, /secao\(oes\) em atencao/i);
});

test("loads and validates the organization settings catalog from the backend endpoint", async () => {
  const catalog = await loadOrganizationSettingsCatalog({
    scenarioId: "renewal-attention",
    sectionKey: "lgpd_dpo",
    fetchImpl: async (input) => {
      assert.equal(
        String(input),
        "http://127.0.0.1:3000/settings/organization?scenario=renewal-attention&section=lgpd_dpo",
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
  assert.equal(catalog.selectedScenarioId, "renewal-attention");
});

test("fails closed when the organization settings backend payload is invalid", async () => {
  const catalog = await loadOrganizationSettingsCatalog({
    fetchImpl: async () =>
      new Response(JSON.stringify({ selectedScenarioId: "renewal-attention", scenarios: [] }), {
        status: 200,
        headers: {
          "content-type": "application/json",
        },
      }),
  });

  assert.equal(catalog, null);
});
