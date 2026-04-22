import { customerRegistryCatalogSchema, type CustomerRegistryCatalog } from "@afere/contracts";
import type { FastifyInstance } from "fastify";
import { z } from "zod";

import { buildCustomerRegistryCatalog } from "../../domain/registry/customer-equipment-scenarios.js";

const QuerySchema = z.object({
  scenario: z.string().min(1).optional(),
  customer: z.string().min(1).optional(),
});

export async function registerCustomerRegistryRoutes(app: FastifyInstance) {
  app.get("/registry/customers", async (request, reply) => {
    const query = QuerySchema.safeParse(request.query);
    if (!query.success) {
      return reply.code(400).send({ error: "invalid_query" });
    }

    const payload: CustomerRegistryCatalog = customerRegistryCatalogSchema.parse(
      buildCustomerRegistryCatalog(query.data.scenario, query.data.customer),
    );

    return reply.code(200).send(payload);
  });
}
