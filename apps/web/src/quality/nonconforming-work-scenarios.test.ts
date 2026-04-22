import assert from "node:assert/strict";
import { test } from "node:test";

import { nonconformingWorkCatalogSchema } from "@afere/contracts";

import { loadNonconformingWorkCatalog } from "./nonconforming-work-api.js";
import { buildNonconformingWorkCatalogView } from "./nonconforming-work-scenarios.js";

const CATALOG_FIXTURE = nonconformingWorkCatalogSchema.parse({
  selectedScenarioId: "contained-attention",
  scenarios: [
    {
      id: "contained-attention",
      label: "Contencao preventiva em acompanhamento",
      description: "A acao imediata de 7.10 ja foi registrada.",
      summary: {
        status: "attention",
        headline: "Contencao preventiva ativa para trabalho nao conforme",
        openCaseCount: 1,
        blockedReleaseCount: 0,
        restoredCount: 0,
        recommendedAction: "Manter a suspensao preventiva ate a evidencia minima.",
        blockers: [],
        warnings: ["A liberacao ainda depende da revisao documental controlada."],
      },
      selectedCaseId: "ncw-014",
      items: [
        {
          caseId: "ncw-014",
          titleLabel: "PT-005/PT-006/PT-008 sob suspensao preventiva",
          affectedEntityLabel: "PT-005, PT-006 e PT-008",
          originLabel: "Auditoria 2026/Ciclo 1",
          impactLabel: "3 procedimento(s) suspenso(s) para novas OS",
          status: "attention",
        },
      ],
      detail: {
        caseId: "ncw-014",
        title: "Trabalho nao conforme em contencao preventiva",
        status: "attention",
        noticeLabel: "A acao imediata de 7.10 ja foi aplicada.",
        classificationLabel: "Suspensao preventiva de procedimento",
        originLabel: "Auditoria 2026/Ciclo 1",
        affectedEntityLabel: "PT-005, PT-006 e PT-008",
        containmentLabel: "Suspender o uso dos procedimentos ate o balanco completo.",
        releaseRuleLabel: "Liberar somente apos revisar a documentacao correspondente.",
        evidenceLabel: "Comunicado interno e referencias do SGQ arquivados.",
        restorationLabel: "Retornar ao uso apenas com registro formal da revisao.",
        blockers: [],
        warnings: ["A liberacao ainda depende da revisao documental controlada."],
        links: {
          workspaceScenarioId: "team-attention",
          nonconformityScenarioId: "open-attention",
          procedureScenarioId: "revision-attention",
          qualityDocumentScenarioId: "revision-attention",
          documentId: "document-pg005-r02",
        },
      },
    },
    {
      id: "release-blocked",
      label: "Liberacao bloqueada por trabalho nao conforme",
      description: "O recorte critico exige contencao formal.",
      summary: {
        status: "blocked",
        headline: "Trabalho nao conforme bloqueia liberacao e reemissao do recorte critico",
        openCaseCount: 1,
        blockedReleaseCount: 1,
        restoredCount: 0,
        recommendedAction: "Manter a OS congelada e abrir nova OS se o recorte mudou.",
        blockers: ["A liberacao do caso continua vedada."],
        warnings: ["A resposta ao cliente precisa seguir o mesmo parecer formal."],
      },
      selectedCaseId: "ncw-015",
      items: [
        {
          caseId: "ncw-015",
          titleLabel: "OS-2026-00147 congelada e sem liberacao para reemissao",
          affectedEntityLabel: "OS-2026-00147 e certificado vinculado",
          originLabel: "Reclamacao critica + trilha divergente",
          impactLabel: "1 OS congelada e 1 liberacao de certificado bloqueada",
          status: "blocked",
        },
      ],
      detail: {
        caseId: "ncw-015",
        title: "Trabalho nao conforme bloqueia liberacao do recorte critico",
        status: "blocked",
        noticeLabel: "O recorte critico exige contencao explicita.",
        classificationLabel: "Bloqueio de liberacao e reemissao",
        originLabel: "Reclamacao critica + trilha divergente",
        affectedEntityLabel: "OS-2026-00147 e certificado vinculado",
        containmentLabel: "Congelar a OS ate validacao conjunta.",
        releaseRuleLabel: "Se alterar leitura bruta, padrao ou ambiente, exige nova OS.",
        evidenceLabel: "RECL-007, trilha divergente e parecer preliminar.",
        restorationLabel: "Liberar apenas apos decisao formal da Qualidade.",
        blockers: ["A liberacao do caso continua vedada."],
        warnings: ["A resposta ao cliente precisa seguir o mesmo parecer formal."],
        links: {
          workspaceScenarioId: "release-blocked",
          auditTrailScenarioId: "integrity-blocked",
          nonconformityScenarioId: "critical-response",
          complaintScenarioId: "critical-response",
          serviceOrderScenarioId: "review-blocked",
          reviewItemId: "os-2026-00147",
          complaintId: "recl-007",
        },
      },
    },
  ],
});

test("selects the active nonconforming work scenario from the backend catalog", () => {
  const view = buildNonconformingWorkCatalogView(CATALOG_FIXTURE);

  assert.equal(view.selectedScenario.id, "contained-attention");
  assert.equal(view.selectedScenario.selectedCase.caseId, "ncw-014");
  assert.match(view.selectedScenario.summaryLabel, /Contencao preventiva/i);
});

test("loads and validates the nonconforming work catalog from the backend endpoint", async () => {
  const catalog = await loadNonconformingWorkCatalog({
    scenarioId: "contained-attention",
    caseId: "ncw-014",
    apiBaseUrl: "http://127.0.0.1:3000",
    fetchImpl: async (input) => {
      assert.equal(
        String(input),
        "http://127.0.0.1:3000/quality/nonconforming-work?scenario=contained-attention&case=ncw-014",
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
  assert.equal(catalog.selectedScenarioId, "contained-attention");
  assert.equal(catalog.scenarios.length, 2);
});

test("fails closed when the nonconforming work backend payload is invalid", async () => {
  const catalog = await loadNonconformingWorkCatalog({
    fetchImpl: async () =>
      new Response(JSON.stringify({ selectedScenarioId: "contained-attention", scenarios: [] }), {
        status: 200,
        headers: {
          "content-type": "application/json",
        },
      }),
  });

  assert.equal(catalog, null);
});
