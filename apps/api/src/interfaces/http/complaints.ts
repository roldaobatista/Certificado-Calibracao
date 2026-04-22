import {
  complaintRegistryCatalogSchema,
  type ComplaintRegistryCatalog,
} from "@afere/contracts";
import type { FastifyInstance } from "fastify";
import { z } from "zod";

import { buildComplaintCatalog } from "../../domain/quality/complaint-registry-scenarios.js";

const QuerySchema = z.object({
  scenario: z.string().min(1).optional(),
  complaint: z.string().min(1).optional(),
});

export async function registerComplaintRoutes(app: FastifyInstance) {
  app.get("/quality/complaints", async (request, reply) => {
    const query = QuerySchema.safeParse(request.query);
    if (!query.success) {
      return reply.code(400).send({ error: "invalid_query" });
    }

    const payload: ComplaintRegistryCatalog = complaintRegistryCatalogSchema.parse(
      buildComplaintCatalog(query.data.scenario, query.data.complaint),
    );

    return reply.code(200).send(payload);
  });
}
