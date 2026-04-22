import {
  signatureQueueCatalogSchema,
  type SignatureQueueCatalog,
} from "@afere/contracts";
import type { FastifyInstance } from "fastify";
import { z } from "zod";

import { buildSignatureQueueCatalog } from "../../domain/emission/signature-queue-scenarios.js";

const QuerySchema = z.object({
  scenario: z.string().min(1).optional(),
  item: z.string().min(1).optional(),
});

export async function registerSignatureQueueRoutes(app: FastifyInstance) {
  app.get("/emission/signature-queue", async (request, reply) => {
    const query = QuerySchema.safeParse(request.query);
    if (!query.success) {
      return reply.code(400).send({ error: "invalid_query" });
    }

    const payload: SignatureQueueCatalog = signatureQueueCatalogSchema.parse(
      buildSignatureQueueCatalog(query.data.scenario, query.data.item),
    );

    return reply.code(200).send(payload);
  });
}
