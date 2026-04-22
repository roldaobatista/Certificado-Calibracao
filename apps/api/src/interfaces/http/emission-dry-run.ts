import {
  emissionDryRunCatalogSchema,
  type EmissionDryRunCatalog,
  type EmissionDryRunScenario as ContractEmissionDryRunScenario,
} from "@afere/contracts";
import type { FastifyInstance } from "fastify";
import { z } from "zod";

import {
  listEmissionDryRunScenarios,
  resolveEmissionDryRunScenario,
  type EmissionDryRunScenario,
} from "../../domain/emission/dry-run-scenarios.js";

const QuerySchema = z.object({
  scenario: z.string().min(1).optional(),
});

export async function registerEmissionDryRunRoutes(app: FastifyInstance) {
  app.get("/emission/dry-run", async (request, reply) => {
    const query = QuerySchema.safeParse(request.query);
    if (!query.success) {
      return reply.code(400).send({ error: "invalid_query" });
    }

    const selectedScenario = resolveEmissionDryRunScenario(query.data.scenario);
    const payload: EmissionDryRunCatalog = emissionDryRunCatalogSchema.parse({
      selectedScenarioId: selectedScenario.id,
      scenarios: listEmissionDryRunScenarios().map(toContractScenario),
    });

    return reply.code(200).send(payload);
  });
}

function toContractScenario(scenario: EmissionDryRunScenario): ContractEmissionDryRunScenario {
  return {
    id: scenario.id,
    label: scenario.label,
    description: scenario.description,
    profile: scenario.profile,
    result: scenario.result,
  };
}
