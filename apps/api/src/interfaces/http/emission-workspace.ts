import {
  emissionWorkspaceCatalogSchema,
  type EmissionWorkspaceCatalog,
  type EmissionWorkspaceScenario as ContractEmissionWorkspaceScenario,
} from "@afere/contracts";
import type { FastifyInstance } from "fastify";
import { z } from "zod";

import {
  listEmissionWorkspaceScenarios,
  resolveEmissionWorkspaceScenario,
  type EmissionWorkspaceScenarioDefinitionView,
} from "../../domain/emission/emission-workspace-scenarios.js";

const QuerySchema = z.object({
  scenario: z.string().min(1).optional(),
});

export async function registerEmissionWorkspaceRoutes(app: FastifyInstance) {
  app.get("/emission/workspace", async (request, reply) => {
    const query = QuerySchema.safeParse(request.query);
    if (!query.success) {
      return reply.code(400).send({ error: "invalid_query" });
    }

    const selectedScenario = resolveEmissionWorkspaceScenario(query.data.scenario);
    const payload: EmissionWorkspaceCatalog = emissionWorkspaceCatalogSchema.parse({
      selectedScenarioId: selectedScenario.id,
      scenarios: listEmissionWorkspaceScenarios().map(toContractScenario),
    });

    return reply.code(200).send(payload);
  });
}

function toContractScenario(
  scenario: EmissionWorkspaceScenarioDefinitionView,
): ContractEmissionWorkspaceScenario {
  return {
    id: scenario.id,
    label: scenario.label,
    description: scenario.description,
    summary: scenario.summary,
    modules: scenario.modules,
    references: scenario.references,
    nextActions: scenario.nextActions,
  };
}
