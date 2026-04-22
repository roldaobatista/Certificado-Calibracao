import { standardRegistryCatalogSchema, type StandardRegistryCatalog } from "@afere/contracts";
import type { FastifyInstance } from "fastify";
import { z } from "zod";

import { buildStandardRegistryCatalog } from "../../domain/registry/standard-registry-scenarios.js";

const QuerySchema = z.object({
  scenario: z.string().min(1).optional(),
  standard: z.string().min(1).optional(),
});

export async function registerStandardRegistryRoutes(app: FastifyInstance) {
  app.get("/registry/standards", async (request, reply) => {
    const query = QuerySchema.safeParse(request.query);
    if (!query.success) {
      return reply.code(400).send({ error: "invalid_query" });
    }

    const payload: StandardRegistryCatalog = standardRegistryCatalogSchema.parse(
      buildStandardRegistryCatalog(query.data.scenario, query.data.standard),
    );

    return reply.code(200).send(payload);
  });
}
