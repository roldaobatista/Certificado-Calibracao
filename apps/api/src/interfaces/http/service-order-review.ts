import {
  serviceOrderReviewCatalogSchema,
  type ServiceOrderReviewCatalog,
} from "@afere/contracts";
import type { FastifyInstance } from "fastify";
import { z } from "zod";

import { buildServiceOrderReviewCatalog } from "../../domain/emission/service-order-review-scenarios.js";

const QuerySchema = z.object({
  scenario: z.string().min(1).optional(),
  item: z.string().min(1).optional(),
});

export async function registerServiceOrderReviewRoutes(app: FastifyInstance) {
  app.get("/emission/service-order-review", async (request, reply) => {
    const query = QuerySchema.safeParse(request.query);
    if (!query.success) {
      return reply.code(400).send({ error: "invalid_query" });
    }

    const payload: ServiceOrderReviewCatalog = serviceOrderReviewCatalogSchema.parse(
      buildServiceOrderReviewCatalog(query.data.scenario, query.data.item),
    );

    return reply.code(200).send(payload);
  });
}
