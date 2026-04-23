import {
  serviceOrderReviewCatalogSchema,
  type ServiceOrderListItemStatus,
  type ServiceOrderReviewCatalog,
} from "@afere/contracts";
import type { FastifyInstance } from "fastify";
import { z } from "zod";

import type { CorePersistence } from "../../domain/auth/core-persistence.js";
import { buildPersistedServiceOrderReviewCatalog } from "../../domain/emission/persisted-service-order-review.js";
import {
  type ServiceOrderPersistence,
} from "../../domain/emission/service-order-persistence.js";
import { buildServiceOrderReviewCatalog } from "../../domain/emission/service-order-review-scenarios.js";
import {
  requireServiceOrderWriteAccess,
  requireWorkspaceAccess,
} from "./auth-session.js";
import { isConflictError, readRedirectTarget, toNumber, toOptionalString } from "./form-helpers.js";

const QuerySchema = z.object({
  scenario: z.string().min(1).optional(),
  item: z.string().min(1).optional(),
});

const SaveServiceOrderBodySchema = z.object({
  action: z.literal("save"),
  serviceOrderId: z.preprocess(toOptionalString, z.string().min(1).optional()),
  customerId: z.string().min(1),
  equipmentId: z.string().min(1),
  procedureId: z.string().min(1),
  primaryStandardId: z.string().min(1),
  executorUserId: z.string().min(1),
  reviewerUserId: z.preprocess(toOptionalString, z.string().min(1).optional()),
  signatoryUserId: z.preprocess(toOptionalString, z.string().min(1).optional()),
  workOrderNumber: z.string().min(3),
  workflowStatus: z.enum([
    "in_execution",
    "awaiting_review",
    "awaiting_signature",
    "emitted",
    "blocked",
  ]) as z.ZodType<ServiceOrderListItemStatus>,
  environmentLabel: z.string().min(3),
  curvePointsLabel: z.string().min(3),
  evidenceLabel: z.string().min(3),
  uncertaintyLabel: z.string().min(3),
  conformityLabel: z.string().min(3),
  measurementResultValue: z.preprocess(toNumber, z.number().finite().optional()),
  measurementExpandedUncertaintyValue: z.preprocess(toNumber, z.number().finite().optional()),
  measurementCoverageFactor: z.preprocess(toNumber, z.number().finite().optional()),
  measurementUnit: z.preprocess(toOptionalString, z.string().min(1).optional()),
  decisionRuleLabel: z.preprocess(toOptionalString, z.string().min(1).optional()),
  decisionOutcomeLabel: z.preprocess(toOptionalString, z.string().min(1).optional()),
  freeTextStatement: z.preprocess(toOptionalString, z.string().min(1).optional()),
  commentDraft: z.string().default(""),
  redirectTo: z.preprocess(toOptionalString, z.string().min(1).optional()),
});

export async function registerServiceOrderReviewRoutes(
  app: FastifyInstance,
  corePersistence: CorePersistence,
  serviceOrderPersistence: ServiceOrderPersistence,
) {
  app.get("/emission/service-order-review", async (request, reply) => {
    const query = QuerySchema.safeParse(request.query);
    if (!query.success) {
      return reply.code(400).send({ error: "invalid_query" });
    }

    if (query.data.scenario) {
      const payload: ServiceOrderReviewCatalog = serviceOrderReviewCatalogSchema.parse(
        buildServiceOrderReviewCatalog(query.data.scenario, query.data.item),
      );

      return reply.code(200).send(payload);
    }

    const context = await requireWorkspaceAccess(request, reply, corePersistence);
    if (!context) {
      return reply;
    }

    const records = await serviceOrderPersistence.listServiceOrdersByOrganization(
      context.user.organizationId,
    );
    if (records.length === 0) {
      return reply.code(404).send({ error: "service_order_registry_empty" });
    }

    const payload: ServiceOrderReviewCatalog = serviceOrderReviewCatalogSchema.parse(
      buildPersistedServiceOrderReviewCatalog({
        nowUtc: new Date().toISOString(),
        records,
        selectedItemId: query.data.item,
      }),
    );

    return reply.code(200).send(payload);
  });

  app.post("/emission/service-order-review/manage", async (request, reply) => {
    const context = await requireServiceOrderWriteAccess(request, reply, corePersistence);
    if (!context) {
      return reply;
    }

    const body = SaveServiceOrderBodySchema.safeParse(request.body);
    if (!body.success) {
      return reply.code(400).send({ error: "invalid_body" });
    }

    try {
      await serviceOrderPersistence.saveServiceOrder({
        organizationId: context.user.organizationId,
        serviceOrderId: body.data.serviceOrderId,
        customerId: body.data.customerId,
        equipmentId: body.data.equipmentId,
        procedureId: body.data.procedureId,
        primaryStandardId: body.data.primaryStandardId,
        executorUserId: body.data.executorUserId,
        reviewerUserId: body.data.reviewerUserId,
        signatoryUserId: body.data.signatoryUserId,
        workOrderNumber: body.data.workOrderNumber,
        workflowStatus: body.data.workflowStatus,
        environmentLabel: body.data.environmentLabel,
        curvePointsLabel: body.data.curvePointsLabel,
        evidenceLabel: body.data.evidenceLabel,
        uncertaintyLabel: body.data.uncertaintyLabel,
        conformityLabel: body.data.conformityLabel,
        measurementResultValue: body.data.measurementResultValue,
        measurementExpandedUncertaintyValue: body.data.measurementExpandedUncertaintyValue,
        measurementCoverageFactor: body.data.measurementCoverageFactor,
        measurementUnit: body.data.measurementUnit,
        decisionRuleLabel: body.data.decisionRuleLabel,
        decisionOutcomeLabel: body.data.decisionOutcomeLabel,
        freeTextStatement: body.data.freeTextStatement,
        commentDraft: body.data.commentDraft,
      });
    } catch (error) {
      if (isConflictError(error)) {
        return reply.code(409).send({ error: "service_order_conflict" });
      }

      if (error instanceof Error && /not_found|mismatch|invalid/i.test(error.message)) {
        return reply.code(409).send({ error: error.message });
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
