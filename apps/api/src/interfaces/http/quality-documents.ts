import {
  qualityDocumentRegistryCatalogSchema,
  type QualityDocumentRegistryCatalog,
} from "@afere/contracts";
import type { FastifyInstance } from "fastify";
import { z } from "zod";

import { buildQualityDocumentCatalog } from "../../domain/quality/quality-document-scenarios.js";

const QuerySchema = z.object({
  scenario: z.string().min(1).optional(),
  document: z.string().min(1).optional(),
});

export async function registerQualityDocumentRoutes(app: FastifyInstance) {
  app.get("/quality/documents", async (request, reply) => {
    const query = QuerySchema.safeParse(request.query);
    if (!query.success) {
      return reply.code(400).send({ error: "invalid_query" });
    }

    const payload: QualityDocumentRegistryCatalog =
      qualityDocumentRegistryCatalogSchema.parse(
        buildQualityDocumentCatalog(query.data.scenario, query.data.document),
      );

    return reply.code(200).send(payload);
  });
}
