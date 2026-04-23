import { auditTrailCatalogSchema, type AuditTrailCatalog } from "@afere/contracts";
import type { FastifyInstance } from "fastify";
import { z } from "zod";

import { buildAuditTrailCatalog } from "../../domain/audit/audit-trail-scenarios.js";
import type { CorePersistence } from "../../domain/auth/core-persistence.js";
import { buildPersistedAuditTrailCatalog } from "../../domain/emission/persisted-emission-flow.js";
import type { ServiceOrderPersistence } from "../../domain/emission/service-order-persistence.js";
import { requireWorkspaceAccess } from "./auth-session.js";

const QuerySchema = z.object({
  scenario: z.string().min(1).optional(),
  event: z.string().min(1).optional(),
  item: z.string().min(1).optional(),
});

export async function registerAuditTrailRoutes(
  app: FastifyInstance,
  corePersistence: CorePersistence,
  serviceOrderPersistence: ServiceOrderPersistence,
) {
  app.get("/quality/audit-trail", async (request, reply) => {
    const query = QuerySchema.safeParse(request.query);
    if (!query.success) {
      return reply.code(400).send({ error: "invalid_query" });
    }

    if (!query.data.scenario) {
      const context = await requireWorkspaceAccess(request, reply, corePersistence);
      if (!context) {
        return reply;
      }

      const [records, users, onboarding, auditEvents] = await Promise.all([
        serviceOrderPersistence.listServiceOrdersByOrganization(context.user.organizationId),
        corePersistence.listUsersByOrganization(context.user.organizationId),
        corePersistence.getOnboardingByOrganization(context.user.organizationId),
        serviceOrderPersistence.listEmissionAuditEventsByOrganization(context.user.organizationId),
      ]);

      if (!onboarding) {
        return reply.code(409).send({ error: "onboarding_missing" });
      }

      if (records.length === 0) {
        return reply.code(404).send({ error: "service_order_registry_empty" });
      }

      const payload: AuditTrailCatalog = auditTrailCatalogSchema.parse(
        buildPersistedAuditTrailCatalog({
          nowUtc: new Date().toISOString(),
          records,
          users,
          onboarding,
          auditEvents,
          selectedItemId: query.data.item,
          selectedEventId: query.data.event,
        }),
      );

      return reply.code(200).send(payload);
    }

    const payload: AuditTrailCatalog = auditTrailCatalogSchema.parse(
      buildAuditTrailCatalog(query.data.scenario, query.data.event),
    );

    return reply.code(200).send(payload);
  });
}
