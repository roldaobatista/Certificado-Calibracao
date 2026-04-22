import { procedureRegistryCatalogSchema, type ProcedureRegistryCatalog } from "@afere/contracts";
import type { FastifyInstance } from "fastify";
import { z } from "zod";

import { buildProcedureRegistryCatalog } from "../../domain/registry/procedure-registry-scenarios.js";

const QuerySchema = z.object({
  scenario: z.string().min(1).optional(),
  procedure: z.string().min(1).optional(),
});

export async function registerProcedureRegistryRoutes(app: FastifyInstance) {
  app.get("/registry/procedures", async (request, reply) => {
    const query = QuerySchema.safeParse(request.query);
    if (!query.success) {
      return reply.code(400).send({ error: "invalid_query" });
    }

    const payload: ProcedureRegistryCatalog = procedureRegistryCatalogSchema.parse(
      buildProcedureRegistryCatalog(query.data.scenario, query.data.procedure),
    );

    return reply.code(200).send(payload);
  });
}
