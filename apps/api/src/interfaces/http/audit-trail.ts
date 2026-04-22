import { auditTrailCatalogSchema, type AuditTrailCatalog } from "@afere/contracts";
import type { FastifyInstance } from "fastify";
import { z } from "zod";

import { buildAuditTrailCatalog } from "../../domain/audit/audit-trail-scenarios.js";

const QuerySchema = z.object({
  scenario: z.string().min(1).optional(),
  event: z.string().min(1).optional(),
});

export async function registerAuditTrailRoutes(app: FastifyInstance) {
  app.get("/quality/audit-trail", async (request, reply) => {
    const query = QuerySchema.safeParse(request.query);
    if (!query.success) {
      return reply.code(400).send({ error: "invalid_query" });
    }

    const payload: AuditTrailCatalog = auditTrailCatalogSchema.parse(
      buildAuditTrailCatalog(query.data.scenario, query.data.event),
    );

    return reply.code(200).send(payload);
  });
}
