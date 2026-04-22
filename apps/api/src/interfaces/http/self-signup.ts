import {
  selfSignupCatalogSchema,
  type SelfSignupCatalog,
  type SelfSignupScenario as ContractSelfSignupScenario,
} from "@afere/contracts";
import type { FastifyInstance } from "fastify";
import { z } from "zod";

import {
  listSelfSignupScenarios,
  resolveSelfSignupScenario,
  type SelfSignupScenario,
} from "../../domain/auth/self-signup-scenarios.js";

const QuerySchema = z.object({
  scenario: z.string().min(1).optional(),
});

export async function registerSelfSignupRoutes(app: FastifyInstance) {
  app.get("/auth/self-signup", async (request, reply) => {
    const query = QuerySchema.safeParse(request.query);
    if (!query.success) {
      return reply.code(400).send({ error: "invalid_query" });
    }

    const selectedScenario = resolveSelfSignupScenario(query.data.scenario);
    const payload: SelfSignupCatalog = selfSignupCatalogSchema.parse({
      selectedScenarioId: selectedScenario.id,
      scenarios: listSelfSignupScenarios().map(toContractScenario),
    });

    return reply.code(200).send(payload);
  });
}

function toContractScenario(scenario: SelfSignupScenario): ContractSelfSignupScenario {
  return {
    id: scenario.id,
    label: scenario.label,
    description: scenario.description,
    role: scenario.role,
    result: scenario.result,
  };
}
