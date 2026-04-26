import { offlineSyncCatalogSchema } from "@afere/contracts";
import type { FastifyInstance } from "fastify";
import { z } from "zod";

import type { CorePersistence } from "../../domain/auth/core-persistence.js";
import { requireWorkspaceAccess } from "./auth-session.js";
import { buildOfflineSyncCatalog } from "../../domain/sync/offline-sync-scenarios.js";

const QuerySchema = z.object({
  scenario: z.string().min(1).optional(),
  item: z.string().min(1).optional(),
  conflict: z.string().min(1).optional(),
});

export async function registerOfflineSyncRoutes(
  app: FastifyInstance,
  corePersistence: CorePersistence,
) {
  app.get("/sync/review-queue", async (request, reply) => {
    const context = await requireWorkspaceAccess(request, reply, corePersistence);
    if (!context) {
      return reply;
    }

    const query = QuerySchema.safeParse(request.query);
    if (!query.success) {
      return reply.code(400).send({ error: "invalid_query" });
    }

    const payload = offlineSyncCatalogSchema.parse(
      buildOfflineSyncCatalog(query.data.scenario, query.data.item, query.data.conflict),
    );

    return reply.code(200).send(payload);
  });
}
