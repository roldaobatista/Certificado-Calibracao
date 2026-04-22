import {
  nonconformityRegistryCatalogSchema,
  type NonconformityRegistryCatalog,
} from "@afere/contracts";
import type { FastifyInstance } from "fastify";
import { z } from "zod";

import { buildNonconformityCatalog } from "../../domain/quality/nonconformity-scenarios.js";

const QuerySchema = z.object({
  scenario: z.string().min(1).optional(),
  nc: z.string().min(1).optional(),
});

export async function registerNonconformityRoutes(app: FastifyInstance) {
  app.get("/quality/nonconformities", async (request, reply) => {
    const query = QuerySchema.safeParse(request.query);
    if (!query.success) {
      return reply.code(400).send({ error: "invalid_query" });
    }

    const payload: NonconformityRegistryCatalog = nonconformityRegistryCatalogSchema.parse(
      buildNonconformityCatalog(query.data.scenario, query.data.nc),
    );

    return reply.code(200).send(payload);
  });
}
