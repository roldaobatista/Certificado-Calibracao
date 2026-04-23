import {
  managementReviewCatalogSchema,
  type ManagementReviewCatalog,
} from "@afere/contracts";
import type { FastifyInstance } from "fastify";
import { z } from "zod";

import type { CorePersistence } from "../../domain/auth/core-persistence.js";
import { buildManagementReviewCatalog } from "../../domain/quality/management-review-scenarios.js";
import {
  buildPersistedManagementReviewCatalog,
} from "../../domain/quality/persisted-quality-catalogs.js";
import type { QualityPersistence } from "../../domain/quality/quality-persistence.js";
import type { ServiceOrderPersistence } from "../../domain/emission/service-order-persistence.js";
import { requireQualityAccess, requireQualityWriteAccess } from "./auth-session.js";
import {
  isConflictError,
  readRedirectTarget,
  toAgendaItems,
  toDate,
  toDecisionItems,
  toOptionalString,
  toStringArray,
} from "./form-helpers.js";

const QuerySchema = z.object({
  scenario: z.string().min(1).optional(),
  meeting: z.string().min(1).optional(),
});

const SaveBodySchema = z.object({
  action: z.literal("save"),
  meetingId: z.preprocess(toOptionalString, z.string().min(1).optional()),
  titleLabel: z.string().min(3),
  status: z.enum(["ready", "attention", "blocked"]),
  dateLabel: z.string().min(3),
  outcomeLabel: z.string().min(3),
  noticeLabel: z.string().min(3),
  nextMeetingLabel: z.string().min(3),
  chairLabel: z.string().min(3),
  attendeesLabel: z.string().min(3),
  periodLabel: z.string().min(3),
  ataLabel: z.string().min(3),
  evidenceLabel: z.string().min(3),
  agendaItems: z.preprocess(toAgendaItems, z.array(z.object({
    key: z.string(),
    label: z.string(),
    status: z.enum(["ready", "attention", "blocked"]),
  })).default([])),
  decisions: z.preprocess(toDecisionItems, z.array(z.object({
    key: z.string(),
    label: z.string(),
    ownerLabel: z.string(),
    dueDateLabel: z.string(),
    status: z.enum(["ready", "attention", "blocked"]),
  })).default([])),
  blockers: z.preprocess(toStringArray, z.array(z.string()).default([])),
  warnings: z.preprocess(toStringArray, z.array(z.string()).default([])),
  scheduledFor: z.preprocess(toDate, z.date()),
  heldAt: z.preprocess(toDate, z.date().optional()),
  redirectTo: z.preprocess(toOptionalString, z.string().min(1).optional()),
});

export async function registerManagementReviewRoutes(
  app: FastifyInstance,
  corePersistence: CorePersistence,
  qualityPersistence: QualityPersistence,
  serviceOrderPersistence: ServiceOrderPersistence,
) {
  app.get("/quality/management-review", async (request, reply) => {
    const query = QuerySchema.safeParse(request.query);
    if (!query.success) {
      return reply.code(400).send({ error: "invalid_query" });
    }

    if (!query.data.scenario) {
      const context = await requireQualityAccess(request, reply, corePersistence);
      if (!context) {
        return reply;
      }

      const [meetings, serviceOrders, nonconformities, internalAuditCycles, complianceProfile] =
        await Promise.all([
          qualityPersistence.listManagementReviewMeetingsByOrganization(context.user.organizationId),
          serviceOrderPersistence.listServiceOrdersByOrganization(context.user.organizationId),
          qualityPersistence.listNonconformitiesByOrganization(context.user.organizationId),
          qualityPersistence.listInternalAuditCyclesByOrganization(context.user.organizationId),
          qualityPersistence.getComplianceProfileByOrganization(context.user.organizationId),
        ]);

      if (meetings.length === 0) {
        return reply.code(404).send({ error: "quality_management_review_empty" });
      }

      const payload: ManagementReviewCatalog = managementReviewCatalogSchema.parse(
        buildPersistedManagementReviewCatalog({
          meetings,
          serviceOrders,
          nonconformities,
          internalAuditCycles,
          complianceProfile,
          selectedMeetingId: query.data.meeting,
        }),
      );

      return reply.code(200).send(payload);
    }

    const payload: ManagementReviewCatalog = managementReviewCatalogSchema.parse(
      buildManagementReviewCatalog(query.data.scenario, query.data.meeting),
    );

    return reply.code(200).send(payload);
  });

  app.post("/quality/management-review/manage", async (request, reply) => {
    const context = await requireQualityWriteAccess(request, reply, corePersistence);
    if (!context) {
      return reply;
    }

    const body = SaveBodySchema.safeParse(request.body);
    if (!body.success) {
      return reply.code(400).send({ error: "invalid_body" });
    }

    try {
      await qualityPersistence.saveManagementReviewMeeting({
        organizationId: context.user.organizationId,
        meetingId: body.data.meetingId,
        titleLabel: body.data.titleLabel,
        status: body.data.status,
        dateLabel: body.data.dateLabel,
        outcomeLabel: body.data.outcomeLabel,
        noticeLabel: body.data.noticeLabel,
        nextMeetingLabel: body.data.nextMeetingLabel,
        chairLabel: body.data.chairLabel,
        attendeesLabel: body.data.attendeesLabel,
        periodLabel: body.data.periodLabel,
        ataLabel: body.data.ataLabel,
        evidenceLabel: body.data.evidenceLabel,
        agendaItems: body.data.agendaItems,
        decisions: body.data.decisions,
        blockers: body.data.blockers,
        warnings: body.data.warnings,
        scheduledFor: body.data.scheduledFor,
        heldAt: body.data.heldAt,
      });
    } catch (error) {
      if (
        isConflictError(error) ||
        (error instanceof Error && /mismatch|not_found|organization/i.test(error.message))
      ) {
        return reply.code(409).send({ error: "quality_management_review_conflict" });
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
