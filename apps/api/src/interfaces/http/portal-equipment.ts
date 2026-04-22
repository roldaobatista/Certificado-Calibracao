import { portalEquipmentCatalogSchema, type PortalEquipmentCatalog } from "@afere/contracts";
import type { FastifyInstance } from "fastify";
import { z } from "zod";

import { buildPortalEquipmentCatalog } from "../../domain/portal/portal-equipment-scenarios.js";

const QuerySchema = z.object({
  scenario: z.string().min(1).optional(),
  equipment: z.string().min(1).optional(),
});

export async function registerPortalEquipmentRoutes(app: FastifyInstance) {
  app.get("/portal/equipment", async (request, reply) => {
    const query = QuerySchema.safeParse(request.query);

    if (!query.success) {
      return reply.code(400).send({ error: "invalid_query" });
    }

    const payload: PortalEquipmentCatalog = portalEquipmentCatalogSchema.parse(
      buildPortalEquipmentCatalog(query.data.scenario, query.data.equipment),
    );

    return reply.code(200).send(payload);
  });
}
