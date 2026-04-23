import {
  internalAuditCatalogSchema,
  type InternalAuditCatalog,
} from "@afere/contracts";
import type { FastifyInstance } from "fastify";
import { z } from "zod";

import type { CorePersistence } from "../../domain/auth/core-persistence.js";
import { buildInternalAuditCatalog } from "../../domain/quality/internal-audit-scenarios.js";
import {
  buildPersistedInternalAuditCatalog,
} from "../../domain/quality/persisted-quality-catalogs.js";
import type { QualityPersistence } from "../../domain/quality/quality-persistence.js";
import { requireQualityAccess, requireQualityWriteAccess } from "./auth-session.js";
import {
  isConflictError,
  readRedirectTarget,
  toChecklistItems,
  toDate,
  toOptionalString,
  toStringArray,
} from "./form-helpers.js";

const QuerySchema = z.object({
  scenario: z.string().min(1).optional(),
  cycle: z.string().min(1).optional(),
});

const SaveBodySchema = z.object({
  action: z.literal("save"),
  cycleId: z.preprocess(toOptionalString, z.string().min(1).optional()),
  cycleLabel: z.string().min(3),
  windowLabel: z.string().min(3),
  scopeLabel: z.string().min(3),
  auditorLabel: z.string().min(3),
  auditeeLabel: z.string().min(3),
  periodLabel: z.string().min(3),
  reportLabel: z.string().min(3),
  evidenceLabel: z.string().min(3),
  nextReviewLabel: z.string().min(3),
  noticeLabel: z.string().min(3),
  status: z.enum(["ready", "attention", "blocked"]),
  checklist: z.preprocess(toChecklistItems, z.array(z.object({
    key: z.string(),
    requirementLabel: z.string(),
    evidenceLabel: z.string(),
    status: z.enum(["ready", "attention", "blocked"]),
  })).default([])),
  findingRefs: z.preprocess(toStringArray, z.array(z.string()).default([])),
  blockers: z.preprocess(toStringArray, z.array(z.string()).default([])),
  warnings: z.preprocess(toStringArray, z.array(z.string()).default([])),
  scheduledAt: z.preprocess(toDate, z.date()),
  completedAt: z.preprocess(toDate, z.date().optional()),
  redirectTo: z.preprocess(toOptionalString, z.string().min(1).optional()),
});

export async function registerInternalAuditRoutes(
  app: FastifyInstance,
  corePersistence: CorePersistence,
  qualityPersistence: QualityPersistence,
) {
  app.get("/quality/internal-audit", async (request, reply) => {
    const query = QuerySchema.safeParse(request.query);
    if (!query.success) {
      return reply.code(400).send({ error: "invalid_query" });
    }

    if (!query.data.scenario) {
      const context = await requireQualityAccess(request, reply, corePersistence);
      if (!context) {
        return reply;
      }

      const [cycles, nonconformities] = await Promise.all([
        qualityPersistence.listInternalAuditCyclesByOrganization(context.user.organizationId),
        qualityPersistence.listNonconformitiesByOrganization(context.user.organizationId),
      ]);
      if (cycles.length === 0) {
        return reply.code(404).send({ error: "quality_internal_audit_empty" });
      }

      const payload: InternalAuditCatalog = internalAuditCatalogSchema.parse(
        buildPersistedInternalAuditCatalog({
          cycles,
          nonconformities,
          selectedCycleId: query.data.cycle,
        }),
      );

      return reply.code(200).send(payload);
    }

    const payload: InternalAuditCatalog = internalAuditCatalogSchema.parse(
      buildInternalAuditCatalog(query.data.scenario, query.data.cycle),
    );

    return reply.code(200).send(payload);
  });

  app.post("/quality/internal-audit/manage", async (request, reply) => {
    const context = await requireQualityWriteAccess(request, reply, corePersistence);
    if (!context) {
      return reply;
    }

    const body = SaveBodySchema.safeParse(request.body);
    if (!body.success) {
      return reply.code(400).send({ error: "invalid_body" });
    }

    try {
      await qualityPersistence.saveInternalAuditCycle({
        organizationId: context.user.organizationId,
        cycleId: body.data.cycleId,
        cycleLabel: body.data.cycleLabel,
        windowLabel: body.data.windowLabel,
        scopeLabel: body.data.scopeLabel,
        auditorLabel: body.data.auditorLabel,
        auditeeLabel: body.data.auditeeLabel,
        periodLabel: body.data.periodLabel,
        reportLabel: body.data.reportLabel,
        evidenceLabel: body.data.evidenceLabel,
        nextReviewLabel: body.data.nextReviewLabel,
        noticeLabel: body.data.noticeLabel,
        status: body.data.status,
        checklist: body.data.checklist,
        findingRefs: body.data.findingRefs,
        blockers: body.data.blockers,
        warnings: body.data.warnings,
        scheduledAt: body.data.scheduledAt,
        completedAt: body.data.completedAt,
      });
    } catch (error) {
      if (
        isConflictError(error) ||
        (error instanceof Error && /mismatch|not_found|organization/i.test(error.message))
      ) {
        return reply.code(409).send({ error: "quality_internal_audit_conflict" });
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
