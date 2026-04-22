import {
  organizationSettingsCatalogSchema,
  type OrganizationSettingsCatalog,
} from "@afere/contracts";
import type { FastifyInstance } from "fastify";
import { z } from "zod";

import { buildOrganizationSettingsCatalog } from "../../domain/settings/organization-settings-scenarios.js";

const QuerySchema = z.object({
  scenario: z.string().min(1).optional(),
  section: z.string().min(1).optional(),
});

export async function registerOrganizationSettingsRoutes(app: FastifyInstance) {
  app.get("/settings/organization", async (request, reply) => {
    const query = QuerySchema.safeParse(request.query);

    if (!query.success) {
      return reply.code(400).send({ error: "invalid_query" });
    }

    const payload: OrganizationSettingsCatalog = organizationSettingsCatalogSchema.parse(
      buildOrganizationSettingsCatalog(query.data.scenario, query.data.section),
    );

    return reply.code(200).send(payload);
  });
}
