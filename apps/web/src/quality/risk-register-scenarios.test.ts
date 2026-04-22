import assert from "node:assert/strict";
import { test } from "node:test";

import { riskRegisterCatalogSchema } from "@afere/contracts";

import { loadRiskRegisterCatalog } from "./risk-register-api.js";
import { buildRiskRegisterCatalogView } from "./risk-register-scenarios.js";

const CATALOG_FIXTURE = riskRegisterCatalogSchema.parse({
  selectedScenarioId: "commercial-pressure",
  scenarios: [
    {
      id: "annual-declarations",
      label: "Rodada anual de declaracoes em acompanhamento",
      description: "Rodada ainda com uma assinatura pendente.",
      summary: {
        status: "attention",
        headline: "Declaracoes e riscos exigem acompanhamento da Qualidade",
        declarationCount: 3,
        pendingDeclarationCount: 1,
        conflictDeclarationCount: 1,
        activeRiskCount: 3,
        highImpactRiskCount: 2,
        recommendedAction: "Concluir a rodada anual.",
        blockers: ["Assinatura pendente."],
        warnings: ["Conflito declarado segue ativo."],
      },
      selectedRiskId: "risk-003",
      declarations: [
        {
          declarationId: "decl-joao-2026",
          actorName: "Joao Silva",
          dateLabel: "Sem retorno ate 20/04/2026",
          summary: "Nova declaracao anual ainda nao arquivada.",
          status: "blocked",
          statusLabel: "Nova rodada pendente",
          documentLabel: "Solicitacao reenviada em 20/04/2026",
        },
      ],
      risks: [
        {
          riskId: "risk-003",
          title: "Rodada anual de declaracoes de conflito incompleta",
          categoryLabel: "Imparcialidade",
          probabilityLabel: "Media",
          impactLabel: "Media",
          ownerLabel: "Ana Costa",
          status: "attention",
          statusLabel: "Rodada pendente",
        },
      ],
      detail: {
        riskId: "risk-003",
        title: "Rodada anual de declaracoes de conflito incompleta",
        status: "attention",
        noticeLabel: "Risco em acompanhamento pela Qualidade.",
        categoryLabel: "Imparcialidade",
        probabilityLabel: "Media",
        impactLabel: "Media",
        ownerLabel: "Ana Costa",
        lastReviewedAtLabel: "20/04/2026",
        reviewCadenceLabel: "Diario ate concluir",
        description: "Descricao do risco.",
        mitigationPlanLabel: "Mitigacao em curso.",
        evidenceLabel: "Controle de adesao.",
        linkedDeclarationLabel: "Joao Silva segue sem declaracao 2026 arquivada.",
        managementReviewLabel: "Levar pendencia para a proxima analise critica se necessario.",
        actions: [
          {
            key: "collect-signature",
            label: "Cobrar assinatura pendente",
            status: "pending",
            detail: "Aguardando retorno.",
          },
        ],
        blockers: ["Assinatura pendente."],
        warnings: ["Conflito declarado segue ativo."],
        links: {
          organizationSettingsScenarioId: "renewal-attention",
        },
      },
    },
    {
      id: "commercial-pressure",
      label: "Risco critico de pressao comercial escalado",
      description: "Caso critico com fail-closed.",
      summary: {
        status: "blocked",
        headline: "Risco critico exige decisao colegiada e fail-closed",
        declarationCount: 3,
        pendingDeclarationCount: 0,
        conflictDeclarationCount: 1,
        activeRiskCount: 2,
        highImpactRiskCount: 2,
        recommendedAction: "Registrar decisao colegiada.",
        blockers: ["Decisao da direcao pendente."],
        warnings: ["NC e reclamacao seguem abertas."],
      },
      selectedRiskId: "risk-001",
      declarations: [
        {
          declarationId: "decl-maria-2026",
          actorName: "Maria Souza",
          dateLabel: "12/01/2026",
          summary: "Conflito relatado: cliente ABC.",
          status: "attention",
          statusLabel: "Conflito declarado",
          documentLabel: "Declaracao 2026 com ressalva [PDF]",
        },
      ],
      risks: [
        {
          riskId: "risk-001",
          title: "Pressao comercial para acelerar reemissao antes da conclusao da NC",
          categoryLabel: "Imparcialidade",
          probabilityLabel: "Media",
          impactLabel: "Alta",
          ownerLabel: "Direcao",
          status: "blocked",
          statusLabel: "Escalado",
        },
      ],
      detail: {
        riskId: "risk-001",
        title: "Pressao comercial para acelerar reemissao antes da conclusao da NC",
        status: "blocked",
        noticeLabel: "Risco critico exige decisao colegiada.",
        categoryLabel: "Imparcialidade",
        probabilityLabel: "Media",
        impactLabel: "Alta",
        ownerLabel: "Direcao",
        lastReviewedAtLabel: "21/04/2026",
        reviewCadenceLabel: "Diario enquanto o caso estiver aberto",
        description: "Descricao do caso critico.",
        mitigationPlanLabel: "Manter fail-closed.",
        evidenceLabel: "E-mail e dossie da NC.",
        linkedDeclarationLabel: "Segregacao de papeis mantida enquanto a pressao segue ativa.",
        managementReviewLabel: "Exportacao extraordinaria pendente.",
        actions: [
          {
            key: "record-collegiate-decision",
            label: "Registrar decisao colegiada",
            status: "pending",
            detail: "Direcao ainda nao deliberou.",
          },
        ],
        blockers: ["Decisao da direcao pendente."],
        warnings: ["NC e reclamacao seguem abertas."],
        links: {
          organizationSettingsScenarioId: "profile-change-blocked",
          complaintScenarioId: "critical-response",
          complaintId: "recl-007",
          nonconformityScenarioId: "critical-response",
          nonconformityId: "nc-015",
        },
      },
    },
  ],
});

test("selects the active risk scenario from the backend catalog", () => {
  const view = buildRiskRegisterCatalogView(CATALOG_FIXTURE);

  assert.equal(view.selectedScenario.id, "commercial-pressure");
  assert.equal(view.selectedScenario.selectedRisk.riskId, "risk-001");
  assert.match(view.selectedScenario.summaryLabel, /2 risco\(s\) de alto impacto/i);
});

test("loads and validates the risk register catalog from the backend endpoint", async () => {
  const catalog = await loadRiskRegisterCatalog({
    scenarioId: "commercial-pressure",
    riskId: "risk-001",
    apiBaseUrl: "http://127.0.0.1:3000",
    fetchImpl: async (input) => {
      assert.equal(
        String(input),
        "http://127.0.0.1:3000/quality/risk-register?scenario=commercial-pressure&risk=risk-001",
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
  assert.equal(catalog.selectedScenarioId, "commercial-pressure");
  assert.equal(catalog.scenarios.length, 2);
});

test("fails closed when the risk register backend payload is invalid", async () => {
  const catalog = await loadRiskRegisterCatalog({
    fetchImpl: async () =>
      new Response(JSON.stringify({ selectedScenarioId: "commercial-pressure", scenarios: [] }), {
        status: 200,
        headers: {
          "content-type": "application/json",
        },
      }),
  });

  assert.equal(catalog, null);
});
