import {
  onboardingCatalogSchema,
  type OnboardingCatalog,
  type OnboardingScenario as ContractOnboardingScenario,
} from "@afere/contracts";
import type { FastifyInstance } from "fastify";
import { z } from "zod";

import {
  listOnboardingScenarios,
  resolveOnboardingScenario,
  type OnboardingScenario,
} from "../../domain/onboarding/onboarding-scenarios.js";

const QuerySchema = z.object({
  scenario: z.string().min(1).optional(),
});

export async function registerOnboardingRoutes(app: FastifyInstance) {
  app.get("/onboarding/readiness", async (request, reply) => {
    const query = QuerySchema.safeParse(request.query);
    if (!query.success) {
      return reply.code(400).send({ error: "invalid_query" });
    }

    const selectedScenario = resolveOnboardingScenario(query.data.scenario);
    const payload: OnboardingCatalog = onboardingCatalogSchema.parse({
      selectedScenarioId: selectedScenario.id,
      scenarios: listOnboardingScenarios().map(toContractScenario),
    });

    return reply.code(200).send(payload);
  });
}

function toContractScenario(scenario: OnboardingScenario): ContractOnboardingScenario {
  return {
    id: scenario.id,
    label: scenario.label,
    description: scenario.description,
    result: scenario.result,
  };
}
