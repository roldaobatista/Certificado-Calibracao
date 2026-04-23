import type { ServiceOrderListItemStatus } from "@afere/contracts";
import {
  reviewSignatureCatalogSchema,
  type ReviewSignatureCatalog,
  type ReviewSignatureScenario as ContractReviewSignatureScenario,
} from "@afere/contracts";
import type { FastifyInstance } from "fastify";
import { z } from "zod";

import type { CorePersistence } from "../../domain/auth/core-persistence.js";
import { buildPersistedReviewSignatureCatalog } from "../../domain/emission/persisted-emission-flow.js";
import {
  listReviewSignatureScenarios,
  resolveReviewSignatureScenario,
  type ReviewSignatureScenarioDefinition,
} from "../../domain/emission/review-signature-scenarios.js";
import type { ReviewDecision, ServiceOrderPersistence } from "../../domain/emission/service-order-persistence.js";
import {
  requireServiceOrderWriteAccess,
  requireWorkspaceAccess,
} from "./auth-session.js";
import { isConflictError, readRedirectTarget, toOptionalString } from "./form-helpers.js";

const QuerySchema = z.object({
  scenario: z.string().min(1).optional(),
  item: z.string().min(1).optional(),
});

const ManageWorkflowBodySchema = z.object({
  action: z.literal("review"),
  serviceOrderId: z.string().min(1),
  reviewerUserId: z.preprocess(toOptionalString, z.string().min(1).optional()),
  signatoryUserId: z.preprocess(toOptionalString, z.string().min(1).optional()),
  workflowStatus: z.enum([
    "in_execution",
    "awaiting_review",
    "awaiting_signature",
    "emitted",
    "blocked",
  ]) as z.ZodType<ServiceOrderListItemStatus>,
  reviewDecision: z.enum(["pending", "approved", "rejected"]) as z.ZodType<ReviewDecision>,
  reviewDecisionComment: z.string().default(""),
  reviewDeviceId: z.preprocess(toOptionalString, z.string().min(1).optional()),
  commentDraft: z.preprocess(toOptionalString, z.string().min(1).optional()),
  redirectTo: z.preprocess(toOptionalString, z.string().min(1).optional()),
});

export async function registerReviewSignatureRoutes(
  app: FastifyInstance,
  corePersistence: CorePersistence,
  serviceOrderPersistence: ServiceOrderPersistence,
) {
  app.get("/emission/review-signature", async (request, reply) => {
    const query = QuerySchema.safeParse(request.query);
    if (!query.success) {
      return reply.code(400).send({ error: "invalid_query" });
    }

    if (!query.data.scenario) {
      const context = await requireWorkspaceAccess(request, reply, corePersistence);
      if (!context) {
        return reply;
      }

      const [records, users, onboarding] = await Promise.all([
        serviceOrderPersistence.listServiceOrdersByOrganization(context.user.organizationId),
        corePersistence.listUsersByOrganization(context.user.organizationId),
        corePersistence.getOnboardingByOrganization(context.user.organizationId),
      ]);

      if (!onboarding) {
        return reply.code(409).send({ error: "onboarding_missing" });
      }

      if (records.length === 0) {
        return reply.code(404).send({ error: "service_order_registry_empty" });
      }

      const payload: ReviewSignatureCatalog = reviewSignatureCatalogSchema.parse(
        buildPersistedReviewSignatureCatalog({
          nowUtc: new Date().toISOString(),
          records,
          users,
          onboarding,
          selectedItemId: query.data.item,
        }),
      );

      return reply.code(200).send(payload);
    }

    const selectedScenario = resolveReviewSignatureScenario(query.data.scenario);
    const payload: ReviewSignatureCatalog = reviewSignatureCatalogSchema.parse({
      selectedScenarioId: selectedScenario.id,
      scenarios: listReviewSignatureScenarios().map(toContractScenario),
    });

    return reply.code(200).send(payload);
  });

  app.post("/emission/review-signature/manage", async (request, reply) => {
    const context = await requireServiceOrderWriteAccess(request, reply, corePersistence);
    if (!context) {
      return reply;
    }

    const body = ManageWorkflowBodySchema.safeParse(request.body);
    if (!body.success) {
      return reply.code(400).send({ error: "invalid_body" });
    }

    try {
      await serviceOrderPersistence.saveServiceOrderWorkflow({
        organizationId: context.user.organizationId,
        serviceOrderId: body.data.serviceOrderId,
        reviewerUserId: body.data.reviewerUserId,
        signatoryUserId: body.data.signatoryUserId,
        workflowStatus: body.data.workflowStatus,
        reviewDecision: body.data.reviewDecision,
        reviewDecisionComment: body.data.reviewDecisionComment,
        reviewDeviceId: body.data.reviewDeviceId,
        commentDraft: body.data.commentDraft,
      });
    } catch (error) {
      if (isConflictError(error)) {
        return reply.code(409).send({ error: "review_signature_conflict" });
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

function toContractScenario(
  scenario: ReviewSignatureScenarioDefinition,
): ContractReviewSignatureScenario {
  return {
    id: scenario.id,
    label: scenario.label,
    description: scenario.description,
    result: scenario.result,
  };
}
