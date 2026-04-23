import {
  qualityIndicatorRegistryCatalogSchema,
  type QualityIndicatorRegistryCatalog,
} from "@afere/contracts";
import type { FastifyInstance } from "fastify";
import { z } from "zod";

import type { CorePersistence } from "../../domain/auth/core-persistence.js";
import { buildQualityIndicatorCatalog } from "../../domain/quality/quality-indicator-scenarios.js";
import {
  buildPersistedQualityIndicatorCatalog,
} from "../../domain/quality/persisted-quality-catalogs.js";
import type { QualityPersistence } from "../../domain/quality/quality-persistence.js";
import type { ServiceOrderPersistence } from "../../domain/emission/service-order-persistence.js";
import { requireQualityAccess } from "./auth-session.js";

const QuerySchema = z.object({
  scenario: z.string().min(1).optional(),
  indicator: z.string().min(1).optional(),
});

export async function registerQualityIndicatorRoutes(
  app: FastifyInstance,
  corePersistence: CorePersistence,
  qualityPersistence: QualityPersistence,
  serviceOrderPersistence: ServiceOrderPersistence,
) {
  app.get("/quality/indicators", async (request, reply) => {
    const query = QuerySchema.safeParse(request.query);
    if (!query.success) {
      return reply.code(400).send({ error: "invalid_query" });
    }

    if (!query.data.scenario) {
      const context = await requireQualityAccess(request, reply, corePersistence);
      if (!context) {
        return reply;
      }

      const [serviceOrders, nonconformities, nonconformingWork, internalAuditCycles, meetings] =
        await Promise.all([
          serviceOrderPersistence.listServiceOrdersByOrganization(context.user.organizationId),
          qualityPersistence.listNonconformitiesByOrganization(context.user.organizationId),
          qualityPersistence.listNonconformingWorkByOrganization(context.user.organizationId),
          qualityPersistence.listInternalAuditCyclesByOrganization(context.user.organizationId),
          qualityPersistence.listManagementReviewMeetingsByOrganization(context.user.organizationId),
        ]);

      const payload: QualityIndicatorRegistryCatalog =
        qualityIndicatorRegistryCatalogSchema.parse(
          buildPersistedQualityIndicatorCatalog({
            nowUtc: new Date().toISOString(),
            serviceOrders,
            nonconformities,
            nonconformingWork,
            internalAuditCycles,
            managementReviewMeetings: meetings,
          }),
        );

      return reply.code(200).send(payload);
    }

    const payload: QualityIndicatorRegistryCatalog =
      qualityIndicatorRegistryCatalogSchema.parse(
        buildQualityIndicatorCatalog(query.data.scenario, query.data.indicator),
      );

    return reply.code(200).send(payload);
  });
}
