import {
  nonconformityRegistryCatalogSchema,
  type NonconformityRegistryCatalog,
} from "@afere/contracts";
import type { FastifyInstance } from "fastify";
import { z } from "zod";

import type { CorePersistence } from "../../domain/auth/core-persistence.js";
import { buildNonconformityCatalog } from "../../domain/quality/nonconformity-scenarios.js";
import {
  buildPersistedNonconformityCatalog,
} from "../../domain/quality/persisted-quality-catalogs.js";
import type { QualityPersistence } from "../../domain/quality/quality-persistence.js";
import { requireQualityAccess, requireQualityWriteAccess } from "./auth-session.js";
import {
  isConflictError,
  readRedirectTarget,
  toDate,
  toOptionalString,
  toStringArray,
} from "./form-helpers.js";

const QuerySchema = z.object({
  scenario: z.string().min(1).optional(),
  nc: z.string().min(1).optional(),
});

const SaveBodySchema = z.object({
  action: z.literal("save"),
  ncId: z.preprocess(toOptionalString, z.string().min(1).optional()),
  serviceOrderId: z.preprocess(toOptionalString, z.string().min(1).optional()),
  ownerUserId: z.preprocess(toOptionalString, z.string().min(1).optional()),
  title: z.string().min(3),
  originLabel: z.string().min(3),
  severityLabel: z.string().min(3),
  status: z.enum(["ready", "attention", "blocked"]),
  noticeLabel: z.string().min(3),
  rootCauseLabel: z.string().min(3),
  containmentLabel: z.string().min(3),
  correctiveActionLabel: z.string().min(3),
  evidenceLabel: z.string().min(3),
  blockers: z.preprocess(toStringArray, z.array(z.string()).default([])),
  warnings: z.preprocess(toStringArray, z.array(z.string()).default([])),
  openedAt: z.preprocess(toDate, z.date()),
  dueAt: z.preprocess(toDate, z.date()),
  resolvedAt: z.preprocess(toDate, z.date().optional()),
  redirectTo: z.preprocess(toOptionalString, z.string().min(1).optional()),
});

export async function registerNonconformityRoutes(
  app: FastifyInstance,
  corePersistence: CorePersistence,
  qualityPersistence: QualityPersistence,
) {
  app.get("/quality/nonconformities", async (request, reply) => {
    const query = QuerySchema.safeParse(request.query);
    if (!query.success) {
      return reply.code(400).send({ error: "invalid_query" });
    }

    if (!query.data.scenario) {
      const context = await requireQualityAccess(request, reply, corePersistence);
      if (!context) {
        return reply;
      }

      const records = await qualityPersistence.listNonconformitiesByOrganization(
        context.user.organizationId,
      );
      if (records.length === 0) {
        return reply.code(404).send({ error: "quality_nonconformities_empty" });
      }

      const payload: NonconformityRegistryCatalog = nonconformityRegistryCatalogSchema.parse(
        buildPersistedNonconformityCatalog({
          nowUtc: new Date().toISOString(),
          records,
          selectedNcId: query.data.nc,
        }),
      );

      return reply.code(200).send(payload);
    }

    const payload: NonconformityRegistryCatalog = nonconformityRegistryCatalogSchema.parse(
      buildNonconformityCatalog(query.data.scenario, query.data.nc),
    );

    return reply.code(200).send(payload);
  });

  app.post("/quality/nonconformities/manage", async (request, reply) => {
    const context = await requireQualityWriteAccess(request, reply, corePersistence);
    if (!context) {
      return reply;
    }

    const body = SaveBodySchema.safeParse(request.body);
    if (!body.success) {
      return reply.code(400).send({ error: "invalid_body" });
    }

    try {
      await qualityPersistence.saveNonconformity({
        organizationId: context.user.organizationId,
        ncId: body.data.ncId,
        serviceOrderId: body.data.serviceOrderId,
        ownerUserId: body.data.ownerUserId,
        title: body.data.title,
        originLabel: body.data.originLabel,
        severityLabel: body.data.severityLabel,
        status: body.data.status,
        noticeLabel: body.data.noticeLabel,
        rootCauseLabel: body.data.rootCauseLabel,
        containmentLabel: body.data.containmentLabel,
        correctiveActionLabel: body.data.correctiveActionLabel,
        evidenceLabel: body.data.evidenceLabel,
        blockers: body.data.blockers,
        warnings: body.data.warnings,
        openedAt: body.data.openedAt,
        dueAt: body.data.dueAt,
        resolvedAt: body.data.resolvedAt,
      });
    } catch (error) {
      if (
        isConflictError(error) ||
        (error instanceof Error && /mismatch|not_found|organization/i.test(error.message))
      ) {
        return reply.code(409).send({ error: "quality_nonconformity_conflict" });
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
