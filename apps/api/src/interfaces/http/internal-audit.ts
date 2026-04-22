import {
  internalAuditCatalogSchema,
  type InternalAuditCatalog,
} from "@afere/contracts";
import type { FastifyInstance } from "fastify";
import { z } from "zod";

import { buildInternalAuditCatalog } from "../../domain/quality/internal-audit-scenarios.js";

const QuerySchema = z.object({
  scenario: z.string().min(1).optional(),
  cycle: z.string().min(1).optional(),
});

export async function registerInternalAuditRoutes(app: FastifyInstance) {
  app.get("/quality/internal-audit", async (request, reply) => {
    const query = QuerySchema.safeParse(request.query);
    if (!query.success) {
      return reply.code(400).send({ error: "invalid_query" });
    }

    const payload: InternalAuditCatalog = internalAuditCatalogSchema.parse(
      buildInternalAuditCatalog(query.data.scenario, query.data.cycle),
    );

    return reply.code(200).send(payload);
  });
}
