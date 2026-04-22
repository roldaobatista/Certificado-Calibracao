import {
  reviewSignatureCatalogSchema,
  type ReviewSignatureCatalog,
  type ReviewSignatureScenario as ContractReviewSignatureScenario,
} from "@afere/contracts";
import type { FastifyInstance } from "fastify";
import { z } from "zod";

import {
  listReviewSignatureScenarios,
  resolveReviewSignatureScenario,
  type ReviewSignatureScenarioDefinition,
} from "../../domain/emission/review-signature-scenarios.js";

const QuerySchema = z.object({
  scenario: z.string().min(1).optional(),
});

export async function registerReviewSignatureRoutes(app: FastifyInstance) {
  app.get("/emission/review-signature", async (request, reply) => {
    const query = QuerySchema.safeParse(request.query);
    if (!query.success) {
      return reply.code(400).send({ error: "invalid_query" });
    }

    const selectedScenario = resolveReviewSignatureScenario(query.data.scenario);
    const payload: ReviewSignatureCatalog = reviewSignatureCatalogSchema.parse({
      selectedScenarioId: selectedScenario.id,
      scenarios: listReviewSignatureScenarios().map(toContractScenario),
    });

    return reply.code(200).send(payload);
  });
}

function toContractScenario(
  scenario: ReviewSignatureScenarioDefinition,
): ContractReviewSignatureScenario {
  return {
    id: scenario.id,
    label: scenario.label,
    description: scenario.description,
    result: scenario.result,
  };
}
