import { createHash, randomBytes } from "node:crypto";

import {
  signatureQueueCatalogSchema,
  type SignatureQueueCatalog,
} from "@afere/contracts";
import { reserveSequentialCertificateNumber } from "@afere/db";
import type { FastifyInstance } from "fastify";
import { z } from "zod";

import type { CorePersistence } from "../../domain/auth/core-persistence.js";
import type { Env } from "../../config/env.js";
import { buildPersistedSignatureQueueCatalog } from "../../domain/emission/persisted-emission-flow.js";
import { buildSignatureQueueCatalog } from "../../domain/emission/signature-queue-scenarios.js";
import type { ServiceOrderPersistence } from "../../domain/emission/service-order-persistence.js";
import {
  requireServiceOrderWriteAccess,
  requireWorkspaceAccess,
} from "./auth-session.js";
import { isConflictError, readRedirectTarget, toOptionalString } from "./form-helpers.js";

function isRedirectAllowed(target: string, allowlist: readonly string[]): boolean {
  if (target.startsWith("/")) {
    return allowlist.some((allowed) => target === allowed || target.startsWith(`${allowed}/`));
  }
  try {
    const url = new URL(target);
    return allowlist.includes(url.pathname) || allowlist.some((allowed) => url.pathname.startsWith(`${allowed}/`));
  } catch {
    return false;
  }
}

const QuerySchema = z.object({
  scenario: z.string().min(1).optional(),
  item: z.string().min(1).optional(),
});

const EmitBodySchema = z.object({
  action: z.literal("emit"),
  serviceOrderId: z.string().min(1),
  signatoryUserId: z.preprocess(toOptionalString, z.string().min(1).optional()),
  signatureDeviceId: z.string().min(3),
  redirectTo: z.preprocess(toOptionalString, z.string().min(1).optional()),
});

const ReissueBodySchema = z.object({
  action: z.literal("reissue"),
  serviceOrderId: z.string().min(1),
  approvalActorUserIdOne: z.string().min(1),
  approvalActorUserIdTwo: z.string().min(1),
  signatoryUserId: z.preprocess(toOptionalString, z.string().min(1).optional()),
  reason: z.string().min(3),
  notificationRecipient: z.string().email(),
  signatureDeviceId: z.string().min(3),
  redirectTo: z.preprocess(toOptionalString, z.string().min(1).optional()),
});

export async function registerSignatureQueueRoutes(
  app: FastifyInstance,
  corePersistence: CorePersistence,
  serviceOrderPersistence: ServiceOrderPersistence,
  env: Env,
) {
  const redirectAllowlist = env.REDIRECT_ALLOWLIST;
  app.get("/emission/signature-queue", async (request, reply) => {
    const query = QuerySchema.safeParse(request.query);
    if (!query.success) {
      return reply.code(400).send({ error: "invalid_query" });
    }

    if (query.data.scenario && !env.ALLOW_SCENARIO_ROUTES) {
      return reply.code(403).send({ error: "scenario_not_allowed" });
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

      const payload: SignatureQueueCatalog = signatureQueueCatalogSchema.parse(
        buildPersistedSignatureQueueCatalog({
          nowUtc: new Date().toISOString(),
          records,
          users,
          onboarding,
          selectedItemId: query.data.item,
        }),
      );

      return reply.code(200).send(payload);
    }

    const payload: SignatureQueueCatalog = signatureQueueCatalogSchema.parse(
      buildSignatureQueueCatalog(query.data.scenario, query.data.item),
    );

    return reply.code(200).send(payload);
  });

  app.post("/emission/signature-queue/manage", async (request, reply) => {
    const context = await requireServiceOrderWriteAccess(request, reply, corePersistence);
    if (!context) {
      return reply;
    }

    const body = z.discriminatedUnion("action", [EmitBodySchema, ReissueBodySchema]).safeParse(
      request.body,
    );
    if (!body.success) {
      return reply.code(400).send({ error: "invalid_body" });
    }

    const [records, users, onboarding] = await Promise.all([
      serviceOrderPersistence.listServiceOrdersByOrganization(context.user.organizationId),
      corePersistence.listUsersByOrganization(context.user.organizationId),
      corePersistence.getOnboardingByOrganization(context.user.organizationId),
    ]);

    if (!onboarding) {
      return reply.code(409).send({ error: "onboarding_missing" });
    }

    const record = records.find((item) => item.serviceOrderId === body.data.serviceOrderId);
    if (!record) {
      return reply.code(404).send({ error: "service_order_not_found" });
    }

    const signatoryId = body.data.signatoryUserId ?? record.signatoryUserId;
    const signatory = users.find((user) => user.userId === signatoryId);
    if (!signatory || !signatory.roles.includes("signatory") || !signatory.mfaEnrolled) {
      return reply.code(409).send({ error: "signatory_not_ready" });
    }

    if (!onboarding.certificateNumberingConfigured || !onboarding.publicQrConfigured) {
      return reply.code(409).send({ error: "emission_prerequisites_missing" });
    }

    const occurredAt = new Date();

    try {
      if (body.data.action === "emit") {
        if (record.reviewDecision !== "approved" && record.workflowStatus !== "emitted") {
          return reply.code(409).send({ error: "review_not_approved" });
        }

        if (record.workflowStatus === "emitted" && record.certificateNumber) {
          return reply.code(409).send({ error: "service_order_already_emitted" });
        }

        const numbering = reserveSequentialCertificateNumber({
          organizationId: context.user.organizationId,
          organizationCode: deriveOrganizationCode(onboarding.organizationSlug),
          issuedNumbers: records
            .filter((item) => item.certificateNumber)
            .map((item) => ({
              organizationId: item.organizationId,
              certificateNumber: item.certificateNumber!,
            })),
        });

        if (!numbering.ok || !numbering.certificateNumber) {
          return reply
            .code(409)
            .send({ error: "certificate_numbering_failed", detail: numbering.errors });
        }

        const documentHash = createHash("sha256")
          .update(
            [
              record.workOrderNumber,
              record.customerName,
              record.equipmentLabel,
              numbering.certificateNumber,
              record.measurementResultValue ?? "",
              record.measurementExpandedUncertaintyValue ?? "",
            ].join("|"),
          )
          .digest("hex");

        await serviceOrderPersistence.emitServiceOrder({
          organizationId: context.user.organizationId,
          serviceOrderId: body.data.serviceOrderId,
          signatoryUserId: signatory.userId,
          certificateNumber: numbering.certificateNumber,
          certificateRevision: record.certificateRevision ?? "R0",
          publicVerificationToken: randomBytes(12).toString("hex"),
          documentHash,
          qrHost: `${onboarding.organizationSlug}.afere.local`,
          signatureStatement: `Assinatura eletrônica concluída por ${signatory.displayName}.`,
          signatureDeviceId: body.data.signatureDeviceId.trim(),
          occurredAt,
        });
      } else {
        if (record.workflowStatus !== "emitted" || !record.certificateNumber || !record.documentHash) {
          return reply.code(409).send({ error: "service_order_not_emitted" });
        }

        const nextRevision = incrementRevision(record.certificateRevision ?? "R0");
        const documentHash = createHash("sha256")
          .update(
            [
              record.workOrderNumber,
              record.customerName,
              record.equipmentLabel,
              record.certificateNumber,
              nextRevision,
              body.data.reason,
              occurredAt.toISOString(),
            ].join("|"),
          )
          .digest("hex");

        await serviceOrderPersistence.reissueServiceOrder({
          organizationId: context.user.organizationId,
          serviceOrderId: body.data.serviceOrderId,
          approvalActorUserIds: [body.data.approvalActorUserIdOne, body.data.approvalActorUserIdTwo],
          signatoryUserId: signatory.userId,
          reason: body.data.reason,
          notificationRecipient: body.data.notificationRecipient,
          publicVerificationToken: randomBytes(12).toString("hex"),
          documentHash,
          qrHost: `${onboarding.organizationSlug}.afere.local`,
          signatureStatement: `Reemissão controlada assinada por ${signatory.displayName}.`,
          signatureDeviceId: body.data.signatureDeviceId.trim(),
          occurredAt,
        });
      }
    } catch (error) {
      if (isConflictError(error)) {
        return reply.code(409).send({ error: "signature_queue_conflict" });
      }

      if (
        error instanceof Error &&
        /review_not_approved|official_decision_required|official_decision_divergence_justification_required|service_order_already_emitted|service_order_not_emitted|signatory_not_found|reissue_distinct_approvals_required|reissue_approver_not_found/i.test(
          error.message,
        )
      ) {
        return reply.code(409).send({ error: error.message });
      }

      throw error;
    }

    const redirectTo = readRedirectTarget(request.body);
    if (redirectTo && isRedirectAllowed(redirectTo, redirectAllowlist)) {
      return reply.redirect(redirectTo);
    }

    return reply.code(204).send();
  });
}

function deriveOrganizationCode(slug: string) {
  const normalized = slug.replace(/[^a-z0-9]/gi, "").toUpperCase();
  return (normalized || "AFERE").slice(0, 12);
}

function incrementRevision(revision: string) {
  const match = /^R(\d+)$/i.exec(revision.trim());
  const current = match ? Number(match[1]) : 0;
  return `R${current + 1}`;
}
