import {
  qualityHubCatalogSchema,
  type QualityHubCatalog,
  type QualityHubModuleKey,
} from "@afere/contracts";
import type { FastifyInstance } from "fastify";
import { z } from "zod";

import type { CorePersistence } from "../../domain/auth/core-persistence.js";
import type { ServiceOrderPersistence } from "../../domain/emission/service-order-persistence.js";
import {
  buildPersistedQualityHubCatalog,
} from "../../domain/quality/persisted-quality-catalogs.js";
import type { QualityPersistence } from "../../domain/quality/quality-persistence.js";
import { buildQualityHubCatalog } from "../../domain/quality/quality-hub-scenarios.js";
import { requireQualityAccess } from "./auth-session.js";

const QuerySchema = z.object({
  scenario: z.string().min(1).optional(),
  module: z.string().min(1).optional(),
});

export async function registerQualityHubRoutes(
  app: FastifyInstance,
  corePersistence: CorePersistence,
  qualityPersistence: QualityPersistence,
  serviceOrderPersistence: ServiceOrderPersistence,
) {
  app.get("/quality", async (request, reply) => {
    const query = QuerySchema.safeParse(request.query);
    if (!query.success) {
      return reply.code(400).send({ error: "invalid_query" });
    }

    if (!query.data.scenario) {
      const context = await requireQualityAccess(request, reply, corePersistence);
      if (!context) {
        return reply;
      }

      const [serviceOrders, nonconformities, nonconformingWork, internalAuditCycles, meetings, complianceProfile] =
        await Promise.all([
          serviceOrderPersistence.listServiceOrdersByOrganization(context.user.organizationId),
          qualityPersistence.listNonconformitiesByOrganization(context.user.organizationId),
          qualityPersistence.listNonconformingWorkByOrganization(context.user.organizationId),
          qualityPersistence.listInternalAuditCyclesByOrganization(context.user.organizationId),
          qualityPersistence.listManagementReviewMeetingsByOrganization(context.user.organizationId),
          qualityPersistence.getComplianceProfileByOrganization(context.user.organizationId),
        ]);

      const payload: QualityHubCatalog = qualityHubCatalogSchema.parse(
        buildPersistedQualityHubCatalog({
          serviceOrders,
          nonconformities,
          nonconformingWork,
          internalAuditCycles,
          managementReviewMeetings: meetings,
          complianceProfile,
          selectedModuleKey: query.data.module as QualityHubModuleKey | undefined,
        }),
      );

      return reply.code(200).send(payload);
    }

    const payload: QualityHubCatalog = qualityHubCatalogSchema.parse(
      buildQualityHubCatalog(query.data.scenario, query.data.module),
    );

    return reply.code(200).send(payload);
  });
}
