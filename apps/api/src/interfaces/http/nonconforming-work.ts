import {
  nonconformingWorkCatalogSchema,
  type NonconformingWorkCatalog,
} from "@afere/contracts";
import type { FastifyInstance } from "fastify";
import { z } from "zod";

import type { CorePersistence } from "../../domain/auth/core-persistence.js";
import { buildNonconformingWorkCatalog } from "../../domain/quality/nonconforming-work-scenarios.js";
import {
  buildPersistedNonconformingWorkCatalog,
} from "../../domain/quality/persisted-quality-catalogs.js";
import type { QualityPersistence } from "../../domain/quality/quality-persistence.js";
import { requireQualityAccess, requireQualityWriteAccess } from "./auth-session.js";
import { isConflictError, readRedirectTarget, toOptionalString, toStringArray } from "./form-helpers.js";

const QuerySchema = z.object({
  scenario: z.string().min(1).optional(),
  case: z.string().min(1).optional(),
});

const SaveBodySchema = z.object({
  action: z.literal("save"),
  caseId: z.preprocess(toOptionalString, z.string().min(1).optional()),
  serviceOrderId: z.preprocess(toOptionalString, z.string().min(1).optional()),
  nonconformityId: z.preprocess(toOptionalString, z.string().min(1).optional()),
  title: z.string().min(3),
  classificationLabel: z.string().min(3),
  originLabel: z.string().min(3),
  affectedEntityLabel: z.string().min(3),
  status: z.enum(["ready", "attention", "blocked"]),
  noticeLabel: z.string().min(3),
  containmentLabel: z.string().min(3),
  releaseRuleLabel: z.string().min(3),
  evidenceLabel: z.string().min(3),
  restorationLabel: z.string().min(3),
  blockers: z.preprocess(toStringArray, z.array(z.string()).default([])),
  warnings: z.preprocess(toStringArray, z.array(z.string()).default([])),
  redirectTo: z.preprocess(toOptionalString, z.string().min(1).optional()),
});

export async function registerNonconformingWorkRoutes(
  app: FastifyInstance,
  corePersistence: CorePersistence,
  qualityPersistence: QualityPersistence,
) {
  app.get("/quality/nonconforming-work", async (request, reply) => {
    const query = QuerySchema.safeParse(request.query);
    if (!query.success) {
      return reply.code(400).send({ error: "invalid_query" });
    }

    if (!query.data.scenario) {
      const context = await requireQualityAccess(request, reply, corePersistence);
      if (!context) {
        return reply;
      }

      const [records, nonconformities] = await Promise.all([
        qualityPersistence.listNonconformingWorkByOrganization(context.user.organizationId),
        qualityPersistence.listNonconformitiesByOrganization(context.user.organizationId),
      ]);
      if (records.length === 0) {
        return reply.code(404).send({ error: "quality_nonconforming_work_empty" });
      }

      const payload: NonconformingWorkCatalog = nonconformingWorkCatalogSchema.parse(
        buildPersistedNonconformingWorkCatalog({
          records,
          selectedCaseId: query.data.case,
          nonconformities,
        }),
      );

      return reply.code(200).send(payload);
    }

    const payload: NonconformingWorkCatalog = nonconformingWorkCatalogSchema.parse(
      buildNonconformingWorkCatalog(query.data.scenario, query.data.case),
    );

    return reply.code(200).send(payload);
  });

  app.post("/quality/nonconforming-work/manage", async (request, reply) => {
    const context = await requireQualityWriteAccess(request, reply, corePersistence);
    if (!context) {
      return reply;
    }

    const body = SaveBodySchema.safeParse(request.body);
    if (!body.success) {
      return reply.code(400).send({ error: "invalid_body" });
    }

    try {
      await qualityPersistence.saveNonconformingWork({
        organizationId: context.user.organizationId,
        caseId: body.data.caseId,
        serviceOrderId: body.data.serviceOrderId,
        nonconformityId: body.data.nonconformityId,
        title: body.data.title,
        classificationLabel: body.data.classificationLabel,
        originLabel: body.data.originLabel,
        affectedEntityLabel: body.data.affectedEntityLabel,
        status: body.data.status,
        noticeLabel: body.data.noticeLabel,
        containmentLabel: body.data.containmentLabel,
        releaseRuleLabel: body.data.releaseRuleLabel,
        evidenceLabel: body.data.evidenceLabel,
        restorationLabel: body.data.restorationLabel,
        blockers: body.data.blockers,
        warnings: body.data.warnings,
      });
    } catch (error) {
      if (
        isConflictError(error) ||
        (error instanceof Error && /mismatch|not_found|organization/i.test(error.message))
      ) {
        return reply.code(409).send({ error: "quality_nonconforming_work_conflict" });
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
