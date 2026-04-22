import assert from "node:assert/strict";
import { test } from "node:test";

import { qualityIndicatorRegistryCatalogSchema } from "@afere/contracts";

import { loadQualityIndicatorCatalog } from "./quality-indicator-api.js";
import { buildQualityIndicatorCatalogView } from "./quality-indicator-scenarios.js";

const CATALOG_FIXTURE = qualityIndicatorRegistryCatalogSchema.parse({
  selectedScenarioId: "action-sla-attention",
  scenarios: [
    {
      id: "action-sla-attention",
      label: "Indicadores com desvio preventivo",
      description: "SLA de CAPA abaixo da meta e taxa de NC em alta.",
      summary: {
        status: "attention",
        headline: "Painel aponta desvio preventivo em indicadores da qualidade",
        monthlyWindowLabel: "Ultimos 12 meses consolidados ate 04/2026",
        indicatorCount: 6,
        attentionCount: 2,
        blockedCount: 0,
        recommendedAction: "Recuperar o SLA de CAPA antes da proxima analise critica.",
        blockers: [],
        warnings: ["NC-014 ainda puxa o SLA para baixo da meta."],
      },
      selectedIndicatorId: "indicator-capa-sla",
      indicators: [
        {
          indicatorId: "indicator-capa-sla",
          title: "% acoes corretivas no prazo",
          currentLabel: "87,5%",
          targetLabel: "Meta >= 90,0%",
          trendLabel: "-2,5 p.p. abaixo da meta",
          ownerLabel: "Ana Costa",
          cadenceLabel: "Mensal",
          status: "attention",
        },
      ],
      detail: {
        indicatorId: "indicator-capa-sla",
        title: "% acoes corretivas no prazo",
        status: "attention",
        noticeLabel: "Indicador abaixo da meta, mas ainda em janela de correcao preventiva.",
        currentLabel: "87,5%",
        targetLabel: "Meta >= 90,0%",
        trendLabel: "-2,5 p.p. abaixo da meta",
        ownerLabel: "Ana Costa",
        cadenceLabel: "Mensal",
        periodLabel: "Ultimos 12 meses consolidados ate 04/2026",
        measurementDefinitionLabel: "Percentual de CAPA dentro do prazo.",
        evidenceLabel: "Consolidado de CAPA arquivado.",
        managementReviewLabel: "Levar o desvio para a analise critica.",
        snapshots: [
          { monthLabel: "03/2026", valueLabel: "87,7%", status: "attention" },
          { monthLabel: "04/2026", valueLabel: "87,5%", status: "attention" },
        ],
        relatedArtifacts: ["NC-014", "Plano CAPA"],
        blockers: [],
        warnings: ["NC-014 ainda puxa o SLA para baixo da meta."],
        links: {
          complaintScenarioId: "open-follow-up",
          complaintId: "recl-004",
          nonconformityScenarioId: "open-attention",
          nonconformityId: "nc-014",
        },
      },
    },
    {
      id: "critical-drift",
      label: "Indicadores em deriva critica",
      description: "Reemissao, CAPA e satisfacao do cliente em desvio material.",
      summary: {
        status: "blocked",
        headline: "Painel mostra deriva critica e exige resposta extraordinaria",
        monthlyWindowLabel: "Ultimos 12 meses consolidados ate 04/2026",
        indicatorCount: 6,
        attentionCount: 3,
        blockedCount: 3,
        recommendedAction: "Congelar o recorte afetado e registrar resposta extraordinaria.",
        blockers: ["A maioria das acoes corretivas ja estourou o prazo."],
        warnings: ["A reclamacao critica segue aberta."],
      },
      selectedIndicatorId: "indicator-reissue-free",
      indicators: [
        {
          indicatorId: "indicator-reissue-free",
          title: "% certificados sem reemissao",
          currentLabel: "96,1%",
          targetLabel: "Meta >= 98,0%",
          trendLabel: "-1,9 p.p. abaixo da meta",
          ownerLabel: "Ana Costa",
          cadenceLabel: "Mensal",
          status: "blocked",
        },
      ],
      detail: {
        indicatorId: "indicator-reissue-free",
        title: "% certificados sem reemissao",
        status: "blocked",
        noticeLabel: "Indicador em deriva critica e exigindo resposta extraordinaria da Qualidade.",
        currentLabel: "96,1%",
        targetLabel: "Meta >= 98,0%",
        trendLabel: "-1,9 p.p. abaixo da meta",
        ownerLabel: "Ana Costa",
        cadenceLabel: "Mensal",
        periodLabel: "Ultimos 12 meses consolidados ate 04/2026",
        measurementDefinitionLabel: "Percentual sem reemissao tecnica.",
        evidenceLabel: "Trilha de reemissao controlada arquivada.",
        managementReviewLabel: "Levar para reuniao extraordinaria.",
        snapshots: [
          { monthLabel: "03/2026", valueLabel: "96,2%", status: "blocked" },
          { monthLabel: "04/2026", valueLabel: "96,1%", status: "blocked" },
        ],
        relatedArtifacts: ["Reemissoes controladas", "Checklist de revisao"],
        blockers: ["O indice de reemissao ficou abaixo da meta."],
        warnings: ["A queda coincide com o caso critico aberto."],
        links: {
          complaintScenarioId: "critical-response",
          complaintId: "recl-007",
          nonconformityScenarioId: "critical-response",
          nonconformityId: "nc-015",
        },
      },
    },
  ],
});

test("selects the active quality indicator scenario from the backend catalog", () => {
  const view = buildQualityIndicatorCatalogView(CATALOG_FIXTURE);

  assert.equal(view.selectedScenario.id, "action-sla-attention");
  assert.equal(view.selectedScenario.selectedIndicator.indicatorId, "indicator-capa-sla");
  assert.match(view.selectedScenario.summaryLabel, /2 alerta\(s\) preventivo\(s\)/i);
});

test("loads and validates the quality indicator catalog from the backend endpoint", async () => {
  const catalog = await loadQualityIndicatorCatalog({
    scenarioId: "action-sla-attention",
    indicatorId: "indicator-capa-sla",
    apiBaseUrl: "http://127.0.0.1:3000",
    fetchImpl: async (input) => {
      assert.equal(
        String(input),
        "http://127.0.0.1:3000/quality/indicators?scenario=action-sla-attention&indicator=indicator-capa-sla",
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
  assert.equal(catalog.selectedScenarioId, "action-sla-attention");
  assert.equal(catalog.scenarios.length, 2);
});

test("fails closed when the quality indicator backend payload is invalid", async () => {
  const catalog = await loadQualityIndicatorCatalog({
    fetchImpl: async () =>
      new Response(JSON.stringify({ selectedScenarioId: "action-sla-attention", scenarios: [] }), {
        status: 200,
        headers: {
          "content-type": "application/json",
        },
      }),
  });

  assert.equal(catalog, null);
});
