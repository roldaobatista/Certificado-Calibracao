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
import { requireQualityAccess, requireQualityWriteAccess } from "./auth-session.js";
import {
  isConflictError,
  readRedirectTarget,
  toDate,
  toNumber,
  toOptionalString,
} from "./form-helpers.js";

const QuerySchema = z.object({
  scenario: z.string().min(1).optional(),
  indicator: z.string().min(1).optional(),
});

const SaveBodySchema = z.object({
  action: z.literal("save"),
  snapshotId: z.preprocess(toOptionalString, z.string().min(1).optional()),
  indicatorId: z.string().min(3),
  monthStart: z.preprocess(toDate, z.date()),
  valueNumeric: z.preprocess(toNumber, z.number().finite()),
  targetNumeric: z.preprocess(toNumber, z.number().finite().optional()),
  status: z.enum(["ready", "attention", "blocked"]),
  sourceLabel: z.string().min(3),
  evidenceLabel: z.string().min(3),
  redirectTo: z.preprocess(toOptionalString, z.string().min(1).optional()),
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

      const [serviceOrders, nonconformities, nonconformingWork, internalAuditCycles, meetings, indicatorSnapshots] =
        await Promise.all([
          serviceOrderPersistence.listServiceOrdersByOrganization(context.user.organizationId),
          qualityPersistence.listNonconformitiesByOrganization(context.user.organizationId),
          qualityPersistence.listNonconformingWorkByOrganization(context.user.organizationId),
          qualityPersistence.listInternalAuditCyclesByOrganization(context.user.organizationId),
          qualityPersistence.listManagementReviewMeetingsByOrganization(context.user.organizationId),
          qualityPersistence.listQualityIndicatorSnapshotsByOrganization(context.user.organizationId),
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
            indicatorSnapshots,
            selectedIndicatorId: query.data.indicator,
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

  app.post("/quality/indicators/manage", async (request, reply) => {
    const context = await requireQualityWriteAccess(request, reply, corePersistence);
    if (!context) {
      return reply;
    }

    const body = SaveBodySchema.safeParse(request.body);
    if (!body.success) {
      return reply.code(400).send({ error: "invalid_body" });
    }

    try {
      await qualityPersistence.saveQualityIndicatorSnapshot({
        organizationId: context.user.organizationId,
        snapshotId: body.data.snapshotId,
        indicatorId: body.data.indicatorId,
        monthStart: body.data.monthStart,
        valueNumeric: body.data.valueNumeric,
        targetNumeric: body.data.targetNumeric,
        status: body.data.status,
        sourceLabel: body.data.sourceLabel,
        evidenceLabel: body.data.evidenceLabel,
      });
    } catch (error) {
      if (
        isConflictError(error) ||
        (error instanceof Error && /mismatch|not_found|organization/i.test(error.message))
      ) {
        return reply.code(409).send({ error: "quality_indicator_snapshot_conflict" });
      }

      throw error;
    }

    const redirectTo = readRedirectTarget(request.body);
    if (redirectTo) {
      return reply.redirect(redirectTo);
    }

    return reply.code(204).send();
  });
}
