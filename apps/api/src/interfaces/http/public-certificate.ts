import {
  publicCertificateCatalogSchema,
  type PublicCertificateCatalog,
  type PublicCertificateScenario as ContractPublicCertificateScenario,
} from "@afere/contracts";
import type { FastifyInstance } from "fastify";
import { z } from "zod";

import {
  listPublicCertificateScenarios,
  resolvePublicCertificateScenario,
  type PublicCertificateScenario,
} from "../../domain/certificates/public-certificate-scenarios.js";

const QuerySchema = z.object({
  scenario: z.string().min(1).optional(),
});

export async function registerPublicCertificateRoutes(app: FastifyInstance) {
  app.get("/portal/verify", async (request, reply) => {
    const query = QuerySchema.safeParse(request.query);
    if (!query.success) {
      return reply.code(400).send({ error: "invalid_query" });
    }

    const selectedScenario = resolvePublicCertificateScenario(query.data.scenario);
    const payload: PublicCertificateCatalog = publicCertificateCatalogSchema.parse({
      selectedScenarioId: selectedScenario.id,
      scenarios: listPublicCertificateScenarios().map(toContractScenario),
    });

    return reply.code(200).send(payload);
  });
}

function toContractScenario(scenario: PublicCertificateScenario): ContractPublicCertificateScenario {
  return {
    id: scenario.id,
    label: scenario.label,
    description: scenario.description,
    result: scenario.result,
  };
}
