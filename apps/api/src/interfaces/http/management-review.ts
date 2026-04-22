import {
  managementReviewCatalogSchema,
  type ManagementReviewCatalog,
} from "@afere/contracts";
import type { FastifyInstance } from "fastify";
import { z } from "zod";

import { buildManagementReviewCatalog } from "../../domain/quality/management-review-scenarios.js";

const QuerySchema = z.object({
  scenario: z.string().min(1).optional(),
  meeting: z.string().min(1).optional(),
});

export async function registerManagementReviewRoutes(app: FastifyInstance) {
  app.get("/quality/management-review", async (request, reply) => {
    const query = QuerySchema.safeParse(request.query);
    if (!query.success) {
      return reply.code(400).send({ error: "invalid_query" });
    }

    const payload: ManagementReviewCatalog = managementReviewCatalogSchema.parse(
      buildManagementReviewCatalog(query.data.scenario, query.data.meeting),
    );

    return reply.code(200).send(payload);
  });
}
