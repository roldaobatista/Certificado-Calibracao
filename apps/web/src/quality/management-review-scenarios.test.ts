import assert from "node:assert/strict";
import { test } from "node:test";

import { managementReviewCatalogSchema } from "@afere/contracts";

import { loadManagementReviewCatalog } from "./management-review-api.js";
import { buildManagementReviewCatalogView } from "./management-review-scenarios.js";

const CATALOG_FIXTURE = managementReviewCatalogSchema.parse({
  selectedScenarioId: "agenda-attention",
  scenarios: [
    {
      id: "agenda-attention",
      label: "Pauta ordinaria com pendencias preventivas",
      description: "Reuniao ordinaria preparada, mas com follow-up pendente.",
      summary: {
        status: "attention",
        headline: "Pauta ordinaria pronta, mas ainda dependente de follow-up preventivo",
        nextMeetingLabel: "30/06/2026",
        agendaCount: 8,
        automaticInputCount: 6,
        openDecisionCount: 2,
        recommendedAction: "Fechar pendencias preventivas antes da ata final.",
        blockers: [],
        warnings: ["O SLA de CAPA segue abaixo da meta."],
      },
      selectedMeetingId: "review-2026-q2",
      meetings: [
        {
          meetingId: "review-2026-q2",
          dateLabel: "30/06/2026",
          titleLabel: "Analise critica Q2/2026",
          outcomeLabel: "Pauta automatica pronta com follow-up pendente",
          status: "attention",
        },
      ],
      detail: {
        meetingId: "review-2026-q2",
        title: "Analise critica Q2/2026",
        status: "attention",
        noticeLabel: "Reuniao ordinaria preparada, mas ainda dependente do fechamento preventivo.",
        nextMeetingLabel: "30/06/2026",
        scheduledForLabel: "30/06/2026, 13:00",
        chairLabel: "Direcao | Ana Costa",
        attendeesLabel: "Ana Costa, Carlos, Maria, Joao Silva",
        periodLabel: "Q2/2026",
        ataLabel: "Pauta automatica pronta para reuniao de 30/06/2026",
        evidenceLabel: "Consolidado trimestral anexado para a pauta ordinaria.",
        calendarExportHref: "/quality/management-review/calendar.ics?meeting=review-2026-q2&scenario=agenda-attention",
        calendar: {
          timezoneLabel: "UTC",
          nextScheduledLabel: "30/06/2026, 13:00",
          entries: [
            {
              meetingId: "review-2026-q2",
              titleLabel: "Analise critica Q2/2026",
              scheduledForLabel: "30/06/2026, 13:00",
              status: "attention",
              exportHref: "/quality/management-review/calendar.ics?meeting=review-2026-q2&scenario=agenda-attention",
            },
          ],
        },
        signature: {
          status: "blocked",
          statusLabel: "Assinatura bloqueada",
          signedByLabel: "Pendente",
          signedAtLabel: "Pendente",
          deviceLabel: "Pendente",
          statementLabel: "Assinatura eletronica da analise critica ainda nao registrada.",
          canSign: false,
          blockers: ["A reuniao ainda nao foi registrada como realizada, entao a ata segue sem assinatura."],
        },
        agendaItems: [
          { key: "corrective-actions", label: "Acoes corretivas", status: "attention" },
        ],
        automaticInputs: [
          {
            key: "indicators",
            label: "Indicadores de qualidade",
            valueLabel: "SLA CAPA 87,5% | 2 alertas preventivos",
            sourceLabel: "Indicadores",
            status: "attention",
            href: "/quality/indicators?scenario=action-sla-attention&indicator=indicator-capa-sla",
          },
        ],
        decisions: [
          {
            key: "decision-q2-01",
            label: "Fechar NC-013 e NC-014 antes da ata final",
            ownerLabel: "Ana Costa",
            dueDateLabel: "30/06/2026",
            status: "attention",
          },
        ],
        blockers: [],
        warnings: ["O SLA de CAPA segue abaixo da meta."],
      },
    },
    {
      id: "extraordinary-response",
      label: "Analise critica extraordinaria bloqueante",
      description: "Recorte critico exige reuniao extraordinaria.",
      summary: {
        status: "blocked",
        headline: "Analise critica extraordinaria bloqueia liberacao do recorte critico",
        nextMeetingLabel: "Hoje | extraordinaria",
        agendaCount: 6,
        automaticInputCount: 6,
        openDecisionCount: 3,
        recommendedAction: "Convocar a reuniao extraordinaria imediatamente.",
        blockers: ["A reuniao extraordinaria precisa ocorrer antes de liberar o caso."],
        warnings: ["Os indicadores e a auditoria extraordinaria precisam entrar na mesma ata."],
      },
      selectedMeetingId: "review-extra-2026-04",
      meetings: [
        {
          meetingId: "review-extra-2026-04",
          dateLabel: "Hoje | extraordinaria",
          titleLabel: "Analise critica extraordinaria 04/2026",
          outcomeLabel: "Deliberacao obrigatoria antes de liberar o caso critico",
          status: "blocked",
        },
      ],
      detail: {
        meetingId: "review-extra-2026-04",
        title: "Analise critica extraordinaria 04/2026",
        status: "blocked",
        noticeLabel: "Reuniao extraordinaria obrigatoria antes de qualquer reemissao ou liberacao.",
        nextMeetingLabel: "Hoje | extraordinaria",
        scheduledForLabel: "23/04/2026, 14:00",
        chairLabel: "Direcao | Ana Costa",
        attendeesLabel: "Direcao, Ana Costa, Carlos, Maria, Joao Silva",
        periodLabel: "Recorte extraordinario de 04/2026",
        ataLabel: "Ata extraordinaria ainda nao iniciada",
        evidenceLabel: "Dossie critico consolidado anexado.",
        calendarExportHref:
          "/quality/management-review/calendar.ics?meeting=review-extra-2026-04&scenario=extraordinary-response",
        calendar: {
          timezoneLabel: "UTC",
          nextScheduledLabel: "23/04/2026, 14:00",
          entries: [
            {
              meetingId: "review-extra-2026-04",
              titleLabel: "Analise critica extraordinaria 04/2026",
              scheduledForLabel: "23/04/2026, 14:00",
              status: "blocked",
              exportHref:
                "/quality/management-review/calendar.ics?meeting=review-extra-2026-04&scenario=extraordinary-response",
            },
          ],
        },
        signature: {
          status: "pending",
          statusLabel: "Pronta para assinatura",
          signedByLabel: "Pendente",
          signedAtLabel: "Pendente",
          deviceLabel: "Pendente",
          statementLabel: "Assinatura eletronica da analise critica ainda nao registrada.",
          canSign: true,
          blockers: [],
        },
        agendaItems: [
          { key: "critical-case", label: "Contencao do caso critico", status: "blocked" },
        ],
        automaticInputs: [
          {
            key: "audit-trail",
            label: "Integridade da trilha",
            valueLabel: "1 falha de hash-chain ativa",
            sourceLabel: "Trilha de auditoria",
            status: "blocked",
            href: "/quality/audit-trail?scenario=integrity-blocked&event=audit-9",
          },
        ],
        decisions: [
          {
            key: "decision-extra-01",
            label: "Manter o recorte bloqueado ate validar a hash-chain",
            ownerLabel: "Direcao",
            dueDateLabel: "Imediato",
            status: "blocked",
          },
        ],
        blockers: ["A reuniao extraordinaria precisa ocorrer antes de liberar o caso."],
        warnings: ["Os indicadores e a auditoria extraordinaria precisam entrar na mesma ata."],
      },
    },
  ],
});

test("selects the active management review scenario from the backend catalog", () => {
  const view = buildManagementReviewCatalogView(CATALOG_FIXTURE);

  assert.equal(view.selectedScenario.id, "agenda-attention");
  assert.equal(view.selectedScenario.selectedMeeting.meetingId, "review-2026-q2");
  assert.match(view.selectedScenario.summaryLabel, /2 decisao\(oes\) pendente\(s\)/i);
});

test("loads and validates the management review catalog from the backend endpoint", async () => {
  const catalog = await loadManagementReviewCatalog({
    scenarioId: "agenda-attention",
    meetingId: "review-2026-q2",
    apiBaseUrl: "http://127.0.0.1:3000",
    fetchImpl: async (input) => {
      assert.equal(
        String(input),
        "http://127.0.0.1:3000/quality/management-review?scenario=agenda-attention&meeting=review-2026-q2",
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
  assert.equal(catalog.selectedScenarioId, "agenda-attention");
  assert.equal(catalog.scenarios.length, 2);
});

test("fails closed when the management review backend payload is invalid", async () => {
  const catalog = await loadManagementReviewCatalog({
    fetchImpl: async () =>
      new Response(JSON.stringify({ selectedScenarioId: "agenda-attention", scenarios: [] }), {
        status: 200,
        headers: {
          "content-type": "application/json",
        },
      }),
  });

  assert.equal(catalog, null);
});
