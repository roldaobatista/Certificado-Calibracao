import {
  certificatePreviewCatalogSchema,
  type CertificatePreviewCatalog,
  type CertificatePreviewScenario as ContractCertificatePreviewScenario,
} from "@afere/contracts";
import type { FastifyInstance } from "fastify";
import { z } from "zod";

import {
  listCertificatePreviewScenarios,
  resolveCertificatePreviewScenario,
} from "../../domain/emission/certificate-preview-scenarios.js";

const QuerySchema = z.object({
  scenario: z.string().min(1).optional(),
});

export async function registerCertificatePreviewRoutes(app: FastifyInstance) {
  app.get("/emission/certificate-preview", async (request, reply) => {
    const query = QuerySchema.safeParse(request.query);
    if (!query.success) {
      return reply.code(400).send({ error: "invalid_query" });
    }

    const selectedScenario = resolveCertificatePreviewScenario(query.data.scenario);
    const payload: CertificatePreviewCatalog = certificatePreviewCatalogSchema.parse({
      selectedScenarioId: selectedScenario.id,
      scenarios: listCertificatePreviewScenarios().map(toContractScenario),
    });

    return reply.code(200).send(payload);
  });
}

function toContractScenario(
  scenario: ReturnType<typeof resolveCertificatePreviewScenario>,
): ContractCertificatePreviewScenario {
  return {
    id: scenario.id,
    label: scenario.label,
    description: scenario.description,
    result: scenario.result,
  };
}
