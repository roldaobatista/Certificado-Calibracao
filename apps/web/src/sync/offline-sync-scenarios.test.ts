import assert from "node:assert/strict";
import { test } from "node:test";

import { offlineSyncCatalogSchema } from "@afere/contracts";

import { buildOfflineSyncCatalogView } from "./offline-sync-scenarios.js";

const OFFLINE_SYNC_CATALOG = offlineSyncCatalogSchema.parse({
  selectedScenarioId: "human-review-open",
  scenarios: [
    {
      id: "human-review-open",
      label: "Conflito humano aberto bloqueando emissao",
      description: "Dois dispositivos concorreram sobre o mesmo agregado.",
      summary: {
        status: "attention",
        headline: "Triagem humana pendente",
        queuedDevices: 2,
        queuedItems: 2,
        openConflictCount: 1,
        escalatedConflictCount: 0,
        blockedWorkOrders: 1,
        resolvedLast24h: 0,
        recommendedAction: "Comparar os eventos e registrar o vencedor.",
        blockers: ["OS-2026-0047 bloqueada para emissao."],
        warnings: [],
      },
      selectedOutboxItemId: "sync-os-2026-0047",
      selectedConflictId: "conflict-c1-0047",
      outboxItems: [
        {
          itemId: "sync-os-2026-0047",
          sessionId: "session-android-0047",
          workOrderId: "os-2026-0047",
          workOrderNumber: "OS-2026-0047",
          deviceId: "device-field-02",
          deviceLabel: "Android campo 02",
          certificateNumber: "AFR-000247",
          status: "attention",
          networkLabel: "Rede online, mas lote retido por conflito aberto.",
          storageLabel: "SQLCipher ativo com chave derivada por device.",
          queuedAtLabel: "22/04 09:02",
          lastAttemptLabel: "22/04 09:08",
          eventCount: 2,
          replayProtectedCount: 2,
          nextActionLabel: "Abrir a triagem humana.",
          pendingConflictClass: "C1",
          blockers: ["A OS nao pode emitir."],
          warnings: [],
          envelopes: [
            {
              eventId: "evt-c1-0047-a",
              clientEventId: "evt-c1-0047-a",
              aggregateLabel: "massa",
              eventKind: "edit",
              lamport: 1,
              payloadDigest: "sha256:evt-c1-0047-a",
              state: "uploaded",
              replayProtected: true,
            },
          ],
        },
      ],
      conflicts: [
        {
          conflictId: "conflict-c1-0047",
          workOrderId: "os-2026-0047",
          workOrderNumber: "OS-2026-0047",
          class: "C1",
          status: "open",
          openedAtLabel: "22/04 09:08",
          deadlineLabel: "23/04 09:08",
          responsibleLabel: "Renata Qualidade",
          summaryLabel: "Dois edits concorreram sobre o mesmo agregado.",
          recommendedAction: "Comparar os eventos e registrar o vencedor.",
          blockingScopeLabel: "Bloqueia emissao da OS selecionada.",
        },
      ],
      detail: {
        conflictId: "conflict-c1-0047",
        title: "OS-2026-0047 · conflito C1 aguardando triagem humana",
        status: "open",
        class: "C1",
        summary: "Os dispositivos editaram o mesmo agregado com Lamport identico.",
        decisionDeadlineLabel: "23/04 09:08",
        responsibleLabel: "Renata Qualidade",
        queueSlaLabel: "24h uteis para triagem inicial.",
        winningEventId: "evt-c1-0047-b",
        losingEventId: "evt-c1-0047-a",
        blockedForEmission: true,
        regulatorEscalationRequired: false,
        recommendedDecisionLabel: "Registrar o evento vencedor com justificativa.",
        rationaleTemplate: "Selecionar o evento vencedor com base na evidencia metrologica.",
        resolutionOptions: [
          {
            action: "accept_server_winner",
            label: "Manter vencedor do servidor",
            detail: "Aceitar o tiebreaker atual.",
            allowed: true,
          },
        ],
        auditRequirements: ["Registrar `resolver_id`."],
        blockers: ["A emissao permanece bloqueada."],
        warnings: [],
        links: {
          workspaceScenarioId: "release-blocked",
          serviceOrderScenarioId: "review-blocked",
          auditTrailScenarioId: "recent-emission",
        },
      },
    },
  ],
});

test("builds the selected outbox item and conflict from the canonical offline sync catalog", () => {
  const view = buildOfflineSyncCatalogView(OFFLINE_SYNC_CATALOG);

  assert.equal(view.selectedScenario.id, "human-review-open");
  assert.equal(view.selectedScenario.selectedOutboxItem.itemId, "sync-os-2026-0047");
  assert.equal(view.selectedScenario.selectedConflict.conflictId, "conflict-c1-0047");
  assert.match(view.selectedScenario.summaryLabel, /1 conflito\(s\) aberto\(s\)/i);
});

test("fails closed when the offline sync catalog loses its selected outbox item", () => {
  const scenario = OFFLINE_SYNC_CATALOG.scenarios[0];
  if (!scenario) {
    throw new Error("missing_offline_sync_scenarios_fixture");
  }

  assert.throws(
    () =>
      buildOfflineSyncCatalogView({
        ...OFFLINE_SYNC_CATALOG,
        scenarios: [
          {
            ...scenario,
            outboxItems: [],
          },
        ],
      }),
    /missing_offline_sync_outbox_items/,
  );
});
