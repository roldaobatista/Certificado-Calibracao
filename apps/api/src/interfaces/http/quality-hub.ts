import { qualityHubCatalogSchema, type QualityHubCatalog } from "@afere/contracts";
import type { FastifyInstance } from "fastify";
import { z } from "zod";

import { buildQualityHubCatalog } from "../../domain/quality/quality-hub-scenarios.js";

const QuerySchema = z.object({
  scenario: z.string().min(1).optional(),
  module: z.string().min(1).optional(),
});

export async function registerQualityHubRoutes(app: FastifyInstance) {
  app.get("/quality", async (request, reply) => {
    const query = QuerySchema.safeParse(request.query);
    if (!query.success) {
      return reply.code(400).send({ error: "invalid_query" });
    }

    const payload: QualityHubCatalog = qualityHubCatalogSchema.parse(
      buildQualityHubCatalog(query.data.scenario, query.data.module),
    );

    return reply.code(200).send(payload);
  });
}
