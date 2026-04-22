import { portalCertificateCatalogSchema, type PortalCertificateCatalog } from "@afere/contracts";
import type { FastifyInstance } from "fastify";
import { z } from "zod";

import { buildPortalCertificateCatalog } from "../../domain/portal/portal-certificate-scenarios.js";

const QuerySchema = z.object({
  scenario: z.string().min(1).optional(),
  certificate: z.string().min(1).optional(),
});

export async function registerPortalCertificateRoutes(app: FastifyInstance) {
  app.get("/portal/certificate", async (request, reply) => {
    const query = QuerySchema.safeParse(request.query);

    if (!query.success) {
      return reply.code(400).send({ error: "invalid_query" });
    }

    const payload: PortalCertificateCatalog = portalCertificateCatalogSchema.parse(
      buildPortalCertificateCatalog(query.data.scenario, query.data.certificate),
    );

    return reply.code(200).send(payload);
  });
}
