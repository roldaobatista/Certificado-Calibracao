import assert from "node:assert/strict";
import { test } from "node:test";

import { userDirectoryCatalogSchema } from "@afere/contracts";

import { loadUserDirectoryCatalog } from "./user-directory-api.js";
import { buildUserDirectoryCatalogView } from "./user-directory-scenarios.js";

const CATALOG_FIXTURE = userDirectoryCatalogSchema.parse({
  selectedScenarioId: "expiring-competencies",
  scenarios: [
    {
      id: "operational-team",
      label: "Equipe operacional",
      description: "Time pronto para operar.",
      summary: {
        status: "ready",
        organizationName: "Lab. Acme",
        activeUsers: 4,
        invitedUsers: 1,
        suspendedUsers: 0,
        expiringCompetencies: 0,
        expiredCompetencies: 0,
      },
      users: [
        {
          userId: "user-1",
          displayName: "Joao Admin",
          email: "joao@lab.com",
          roles: ["admin"],
          status: "active",
          deviceCount: 1,
          competencies: [],
        },
      ],
    },
    {
      id: "expiring-competencies",
      label: "Competencias expirando",
      description: "Equipe em atencao.",
      summary: {
        status: "attention",
        organizationName: "Lab. Acme",
        activeUsers: 4,
        invitedUsers: 0,
        suspendedUsers: 0,
        expiringCompetencies: 1,
        expiredCompetencies: 0,
      },
      users: [
        {
          userId: "user-2",
          displayName: "Carlos Signatario",
          email: "carlos@lab.com",
          roles: ["signatory"],
          status: "active",
          teamName: "Qualidade",
          lastLoginUtc: "2026-04-22T09:00:00Z",
          deviceCount: 1,
          competencies: [
            {
              instrumentType: "balanca",
              roleLabel: "Signatario autorizado",
              status: "expiring",
              validUntilUtc: "2026-05-15T00:00:00Z",
            },
          ],
        },
      ],
    },
  ],
});

test("selects the active user directory scenario from the backend catalog", () => {
  const view = buildUserDirectoryCatalogView(CATALOG_FIXTURE);

  assert.equal(view.selectedScenario.id, "expiring-competencies");
  assert.match(view.selectedScenario.summaryLabel, /1 competencia\(s\) expirando/i);
});

test("loads and validates the user directory catalog from the backend endpoint", async () => {
  const catalog = await loadUserDirectoryCatalog({
    scenarioId: "operational-team",
    apiBaseUrl: "http://127.0.0.1:3000",
    fetchImpl: async (input) => {
      assert.equal(String(input), "http://127.0.0.1:3000/auth/users?scenario=operational-team");

      return new Response(JSON.stringify(CATALOG_FIXTURE), {
        status: 200,
        headers: {
          "content-type": "application/json",
        },
      });
    },
  });

  assert.ok(catalog);
  assert.equal(catalog.selectedScenarioId, "expiring-competencies");
  assert.equal(catalog.scenarios.length, 2);
});

test("fails closed when the user directory backend payload is invalid", async () => {
  const catalog = await loadUserDirectoryCatalog({
    fetchImpl: async () =>
      new Response(JSON.stringify({ selectedScenarioId: "operational-team", scenarios: [] }), {
        status: 200,
        headers: {
          "content-type": "application/json",
        },
      }),
  });

  assert.equal(catalog, null);
});
