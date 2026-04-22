import { equipmentRegistryCatalogSchema, type EquipmentRegistryCatalog } from "@afere/contracts";
import type { FastifyInstance } from "fastify";
import { z } from "zod";

import { buildEquipmentRegistryCatalog } from "../../domain/registry/customer-equipment-scenarios.js";

const QuerySchema = z.object({
  scenario: z.string().min(1).optional(),
  equipment: z.string().min(1).optional(),
});

export async function registerEquipmentRegistryRoutes(app: FastifyInstance) {
  app.get("/registry/equipment", async (request, reply) => {
    const query = QuerySchema.safeParse(request.query);
    if (!query.success) {
      return reply.code(400).send({ error: "invalid_query" });
    }

    const payload: EquipmentRegistryCatalog = equipmentRegistryCatalogSchema.parse(
      buildEquipmentRegistryCatalog(query.data.scenario, query.data.equipment),
    );

    return reply.code(200).send(payload);
  });
}
