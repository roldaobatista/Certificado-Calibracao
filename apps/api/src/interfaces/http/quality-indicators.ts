import {
  qualityIndicatorRegistryCatalogSchema,
  type QualityIndicatorRegistryCatalog,
} from "@afere/contracts";
import type { FastifyInstance } from "fastify";
import { z } from "zod";

import { buildQualityIndicatorCatalog } from "../../domain/quality/quality-indicator-scenarios.js";

const QuerySchema = z.object({
  scenario: z.string().min(1).optional(),
  indicator: z.string().min(1).optional(),
});

export async function registerQualityIndicatorRoutes(app: FastifyInstance) {
  app.get("/quality/indicators", async (request, reply) => {
    const query = QuerySchema.safeParse(request.query);
    if (!query.success) {
      return reply.code(400).send({ error: "invalid_query" });
    }

    const payload: QualityIndicatorRegistryCatalog =
      qualityIndicatorRegistryCatalogSchema.parse(
        buildQualityIndicatorCatalog(query.data.scenario, query.data.indicator),
      );

    return reply.code(200).send(payload);
  });
}
