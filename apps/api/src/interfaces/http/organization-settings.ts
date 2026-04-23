import {
  organizationSettingsCatalogSchema,
  type OrganizationSettingsCatalog,
} from "@afere/contracts";
import type { FastifyInstance } from "fastify";
import { z } from "zod";

import type { CorePersistence } from "../../domain/auth/core-persistence.js";
import type { ServiceOrderPersistence } from "../../domain/emission/service-order-persistence.js";
import {
  buildPersistedOrganizationSettingsCatalog,
} from "../../domain/settings/persisted-organization-settings.js";
import { buildOrganizationSettingsCatalog } from "../../domain/settings/organization-settings-scenarios.js";
import type { QualityPersistence } from "../../domain/quality/quality-persistence.js";
import { requireSettingsAccess, requireSettingsWriteAccess } from "./auth-session.js";
import {
  isConflictError,
  readRedirectTarget,
  toDate,
  toNumber,
  toOptionalString,
} from "./form-helpers.js";

const QuerySchema = z.object({
  scenario: z.string().min(1).optional(),
  section: z.string().min(1).optional(),
});

const SaveBodySchema = z.object({
  action: z.literal("save"),
  regulatoryProfile: z.preprocess(toOptionalString, z.string().min(1).optional()),
  organizationCode: z.string().min(2),
  planLabel: z.string().min(2),
  certificatePrefix: z.string().min(2),
  accreditationNumber: z.preprocess(toOptionalString, z.string().min(1).optional()),
  accreditationValidUntil: z.preprocess(toDate, z.date().optional()),
  scopeSummary: z.string().min(3),
  cmcSummary: z.string().min(3),
  scopeItemCount: z.preprocess(toNumber, z.number().int().nonnegative()),
  cmcItemCount: z.preprocess(toNumber, z.number().int().nonnegative()),
  legalOpinionStatus: z.string().min(3),
  legalOpinionReference: z.string().min(3),
  dpaReference: z.string().min(3),
  normativeGovernanceStatus: z.string().min(3),
  normativeGovernanceOwner: z.string().min(3),
  normativeGovernanceReference: z.string().min(3),
  releaseNormVersion: z.string().min(2),
  releaseNormStatus: z.string().min(2),
  lastReviewedAt: z.preprocess(toDate, z.date()),
  redirectTo: z.preprocess(toOptionalString, z.string().min(1).optional()),
});

export async function registerOrganizationSettingsRoutes(
  app: FastifyInstance,
  corePersistence: CorePersistence,
  qualityPersistence: QualityPersistence,
  serviceOrderPersistence: ServiceOrderPersistence,
) {
  app.get("/settings/organization", async (request, reply) => {
    const query = QuerySchema.safeParse(request.query);

    if (!query.success) {
      return reply.code(400).send({ error: "invalid_query" });
    }

    if (!query.data.scenario) {
      const context = await requireSettingsAccess(request, reply, corePersistence);
      if (!context) {
        return reply;
      }

      const [users, onboarding, serviceOrders, complianceProfile] = await Promise.all([
        corePersistence.listUsersByOrganization(context.user.organizationId),
        corePersistence.getOnboardingByOrganization(context.user.organizationId),
        serviceOrderPersistence.listServiceOrdersByOrganization(context.user.organizationId),
        qualityPersistence.getComplianceProfileByOrganization(context.user.organizationId),
      ]);

      const payload: OrganizationSettingsCatalog = organizationSettingsCatalogSchema.parse(
        buildPersistedOrganizationSettingsCatalog({
          organizationName: context.user.organizationName,
          organizationSlug: context.user.organizationSlug,
          users,
          onboarding,
          serviceOrders,
          complianceProfile,
          selectedSectionKey: query.data.section,
        }),
      );

      return reply.code(200).send(payload);
    }

    const payload: OrganizationSettingsCatalog = organizationSettingsCatalogSchema.parse(
      buildOrganizationSettingsCatalog(query.data.scenario, query.data.section),
    );

    return reply.code(200).send(payload);
  });

  app.post("/settings/organization/manage", async (request, reply) => {
    const context = await requireSettingsWriteAccess(request, reply, corePersistence);
    if (!context) {
      return reply;
    }

    const body = SaveBodySchema.safeParse(request.body);
    if (!body.success) {
      return reply.code(400).send({ error: "invalid_body" });
    }

    try {
      await qualityPersistence.saveComplianceProfile({
        organizationId: context.user.organizationId,
        regulatoryProfile: body.data.regulatoryProfile,
        organizationCode: body.data.organizationCode,
        planLabel: body.data.planLabel,
        certificatePrefix: body.data.certificatePrefix,
        accreditationNumber: body.data.accreditationNumber,
        accreditationValidUntil: body.data.accreditationValidUntil,
        scopeSummary: body.data.scopeSummary,
        cmcSummary: body.data.cmcSummary,
        scopeItemCount: body.data.scopeItemCount,
        cmcItemCount: body.data.cmcItemCount,
        legalOpinionStatus: body.data.legalOpinionStatus,
        legalOpinionReference: body.data.legalOpinionReference,
        dpaReference: body.data.dpaReference,
        normativeGovernanceStatus: body.data.normativeGovernanceStatus,
        normativeGovernanceOwner: body.data.normativeGovernanceOwner,
        normativeGovernanceReference: body.data.normativeGovernanceReference,
        releaseNormVersion: body.data.releaseNormVersion,
        releaseNormStatus: body.data.releaseNormStatus,
        lastReviewedAt: body.data.lastReviewedAt,
      });
    } catch (error) {
      if (
        isConflictError(error) ||
        (error instanceof Error && /mismatch|not_found|organization/i.test(error.message))
      ) {
        return reply.code(409).send({ error: "organization_settings_conflict" });
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
