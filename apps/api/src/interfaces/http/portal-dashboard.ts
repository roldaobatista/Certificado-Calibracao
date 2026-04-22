import { portalDashboardCatalogSchema, type PortalDashboardCatalog } from "@afere/contracts";
import type { FastifyInstance } from "fastify";
import { z } from "zod";

import { buildPortalDashboardCatalog } from "../../domain/portal/portal-dashboard-scenarios.js";

const QuerySchema = z.object({
  scenario: z.string().min(1).optional(),
});

export async function registerPortalDashboardRoutes(app: FastifyInstance) {
  app.get("/portal/dashboard", async (request, reply) => {
    const query = QuerySchema.safeParse(request.query);

    if (!query.success) {
      return reply.code(400).send({ error: "invalid_query" });
    }

    const payload: PortalDashboardCatalog = portalDashboardCatalogSchema.parse(
      buildPortalDashboardCatalog(query.data.scenario),
    );

    return reply.code(200).send(payload);
  });
}
