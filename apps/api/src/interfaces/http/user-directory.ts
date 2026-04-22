import {
  userDirectoryCatalogSchema,
  type UserDirectoryCatalog,
  type UserDirectoryScenario as ContractUserDirectoryScenario,
} from "@afere/contracts";
import type { FastifyInstance } from "fastify";
import { z } from "zod";

import {
  listUserDirectoryScenarios,
  resolveUserDirectoryScenario,
  type UserDirectoryScenarioDefinition,
} from "../../domain/auth/user-directory-scenarios.js";

const QuerySchema = z.object({
  scenario: z.string().min(1).optional(),
});

export async function registerUserDirectoryRoutes(app: FastifyInstance) {
  app.get("/auth/users", async (request, reply) => {
    const query = QuerySchema.safeParse(request.query);
    if (!query.success) {
      return reply.code(400).send({ error: "invalid_query" });
    }

    const selectedScenario = resolveUserDirectoryScenario(query.data.scenario);
    const payload: UserDirectoryCatalog = userDirectoryCatalogSchema.parse({
      selectedScenarioId: selectedScenario.id,
      scenarios: listUserDirectoryScenarios().map(toContractScenario),
    });

    return reply.code(200).send(payload);
  });
}

function toContractScenario(
  scenario: UserDirectoryScenarioDefinition,
): ContractUserDirectoryScenario {
  return {
    id: scenario.id,
    label: scenario.label,
    description: scenario.description,
    summary: scenario.summary,
    users: scenario.users,
  };
}
