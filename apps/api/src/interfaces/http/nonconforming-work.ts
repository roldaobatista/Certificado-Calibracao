import {
  nonconformingWorkCatalogSchema,
  type NonconformingWorkCatalog,
} from "@afere/contracts";
import type { FastifyInstance } from "fastify";
import { z } from "zod";

import { buildNonconformingWorkCatalog } from "../../domain/quality/nonconforming-work-scenarios.js";

const QuerySchema = z.object({
  scenario: z.string().min(1).optional(),
  case: z.string().min(1).optional(),
});

export async function registerNonconformingWorkRoutes(app: FastifyInstance) {
  app.get("/quality/nonconforming-work", async (request, reply) => {
    const query = QuerySchema.safeParse(request.query);
    if (!query.success) {
      return reply.code(400).send({ error: "invalid_query" });
    }

    const payload: NonconformingWorkCatalog = nonconformingWorkCatalogSchema.parse(
      buildNonconformingWorkCatalog(query.data.scenario, query.data.case),
    );

    return reply.code(200).send(payload);
  });
}
