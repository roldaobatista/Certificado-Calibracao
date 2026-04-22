import {
  riskRegisterCatalogSchema,
  type RiskRegisterCatalog,
} from "@afere/contracts";
import type { FastifyInstance } from "fastify";
import { z } from "zod";

import { buildRiskRegisterCatalog } from "../../domain/quality/risk-register-scenarios.js";

const QuerySchema = z.object({
  scenario: z.string().min(1).optional(),
  risk: z.string().min(1).optional(),
});

export async function registerRiskRegisterRoutes(app: FastifyInstance) {
  app.get("/quality/risk-register", async (request, reply) => {
    const query = QuerySchema.safeParse(request.query);
    if (!query.success) {
      return reply.code(400).send({ error: "invalid_query" });
    }

    const payload: RiskRegisterCatalog = riskRegisterCatalogSchema.parse(
      buildRiskRegisterCatalog(query.data.scenario, query.data.risk),
    );

    return reply.code(200).send(payload);
  });
}
