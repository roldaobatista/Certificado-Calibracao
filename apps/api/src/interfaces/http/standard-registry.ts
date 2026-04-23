import {
  standardMetrologyProfileSchema,
  standardQuantityKindSchema,
  standardRegistryCatalogSchema,
  standardTraceabilitySourceSchema,
  type StandardMetrologyProfile,
  type StandardRegistryCatalog,
} from "@afere/contracts";
import type { FastifyInstance } from "fastify";
import { z } from "zod";

import type { CorePersistence } from "../../domain/auth/core-persistence.js";
import { buildPersistedStandardRegistryCatalog } from "../../domain/registry/persisted-registry-catalogs.js";
import type { RegistryPersistence } from "../../domain/registry/registry-persistence.js";
import { buildStandardRegistryCatalog } from "../../domain/registry/standard-registry-scenarios.js";
import { requireRegistryAccess, requireRegistryWriteAccess } from "./auth-session.js";
import {
  isConflictError,
  readRedirectTarget,
  toBoolean,
  toNumber,
  toOptionalString,
} from "./form-helpers.js";

const QuerySchema = z.object({
  scenario: z.string().min(1).optional(),
  standard: z.string().min(1).optional(),
});

const SaveStandardBodySchema = z.object({
  action: z.literal("save"),
  standardId: z.preprocess(toOptionalString, z.string().min(1).optional()),
  code: z.string().min(2),
  title: z.string().min(3),
  kindLabel: z.string().min(2),
  nominalClassLabel: z.string().min(2),
  sourceLabel: z.string().min(2),
  certificateLabel: z.string().min(2),
  manufacturerLabel: z.string().min(2),
  modelLabel: z.string().min(2),
  serialNumberLabel: z.string().min(2),
  nominalValueLabel: z.string().min(1),
  classLabel: z.string().min(1),
  usageRangeLabel: z.string().min(1),
  measurementValue: z.preprocess(toNumber, z.number()),
  applicableRangeMin: z.preprocess(toNumber, z.number()),
  applicableRangeMax: z.preprocess(toNumber, z.number()),
  uncertaintyLabel: z.string().min(1),
  correctionFactorLabel: z.string().min(1),
  quantityKind: z.preprocess(toOptionalString, standardQuantityKindSchema.optional()),
  measurementUnit: z.preprocess(toOptionalString, z.string().min(1).optional()),
  traceabilitySource: z.preprocess(toOptionalString, standardTraceabilitySourceSchema.optional()),
  certificateIssuer: z.preprocess(toOptionalString, z.string().min(1).optional()),
  conventionalMassErrorValue: z.preprocess(toNumber, z.number().optional()),
  expandedUncertaintyValue: z.preprocess(toNumber, z.number().nonnegative().optional()),
  coverageFactorK: z.preprocess(toNumber, z.number().positive().optional()),
  degreesOfFreedom: z.preprocess(toNumber, z.number().positive().optional()),
  densityKgPerM3: z.preprocess(toNumber, z.number().positive().optional()),
  driftLimitValue: z.preprocess(toNumber, z.number().nonnegative().optional()),
  hasValidCertificate: z.preprocess(toBoolean, z.boolean()),
  certificateValidUntilUtc: z.preprocess(toOptionalString, z.string().min(1).optional()),
  redirectTo: z.preprocess(toOptionalString, z.string().min(1).optional()),
});
type SaveStandardBody = z.infer<typeof SaveStandardBodySchema>;

const ToggleStandardArchiveBodySchema = z.object({
  action: z.enum(["archive", "restore"]),
  standardId: z.string().min(1),
  redirectTo: z.preprocess(toOptionalString, z.string().min(1).optional()),
});

const ManageStandardBodySchema = z.discriminatedUnion("action", [
  SaveStandardBodySchema,
  ToggleStandardArchiveBodySchema,
]);

function buildStandardMetrologyProfile(body: SaveStandardBody): StandardMetrologyProfile | undefined | null {
  const candidate = {
    quantityKind: body.quantityKind,
    measurementUnit: body.measurementUnit,
    traceabilitySource: body.traceabilitySource,
    certificateIssuer: body.certificateIssuer,
    conventionalMassErrorValue: body.conventionalMassErrorValue,
    expandedUncertaintyValue: body.expandedUncertaintyValue,
    coverageFactorK: body.coverageFactorK,
    degreesOfFreedom: body.degreesOfFreedom,
    densityKgPerM3: body.densityKgPerM3,
    driftLimitValue: body.driftLimitValue,
  };

  if (!Object.values(candidate).some((value) => value !== undefined)) {
    return undefined;
  }

  const parsed = standardMetrologyProfileSchema.safeParse(candidate);
  return parsed.success ? parsed.data : null;
}

export async function registerStandardRegistryRoutes(
  app: FastifyInstance,
  corePersistence: CorePersistence,
  registryPersistence: RegistryPersistence,
) {
  app.get("/registry/standards", async (request, reply) => {
    const query = QuerySchema.safeParse(request.query);
    if (!query.success) {
      return reply.code(400).send({ error: "invalid_query" });
    }

    if (query.data.scenario) {
      const payload: StandardRegistryCatalog = standardRegistryCatalogSchema.parse(
        buildStandardRegistryCatalog(query.data.scenario, query.data.standard),
      );

      return reply.code(200).send(payload);
    }

    const context = await requireRegistryAccess(request, reply, corePersistence);
    if (!context) {
      return reply;
    }

    const [standards, equipment] = await Promise.all([
      registryPersistence.listStandardsByOrganization(context.user.organizationId),
      registryPersistence.listEquipmentByOrganization(context.user.organizationId),
    ]);

    if (standards.length === 0) {
      return reply.code(404).send({ error: "standard_registry_empty" });
    }

    const payload: StandardRegistryCatalog = standardRegistryCatalogSchema.parse(
      buildPersistedStandardRegistryCatalog({
        nowUtc: new Date().toISOString(),
        selectedStandardId: query.data.standard,
        standards,
        equipment,
      }),
    );

    return reply.code(200).send(payload);
  });

  app.post("/registry/standards/manage", async (request, reply) => {
    const context = await requireRegistryWriteAccess(request, reply, corePersistence);
    if (!context) {
      return reply;
    }

    const body = ManageStandardBodySchema.safeParse(request.body);
    if (!body.success) {
      return reply.code(400).send({ error: "invalid_body" });
    }

    const metrologyProfile =
      body.data.action === "save" ? buildStandardMetrologyProfile(body.data) : undefined;
    if (body.data.action === "save" && metrologyProfile === null) {
      return reply.code(400).send({ error: "invalid_standard_metrology_profile" });
    }

    try {
      if (body.data.action === "save") {
        await registryPersistence.saveStandard({
          organizationId: context.user.organizationId,
          standardId: body.data.standardId,
          actorUserId: context.user.userId,
          code: body.data.code,
          title: body.data.title,
          kindLabel: body.data.kindLabel,
          nominalClassLabel: body.data.nominalClassLabel,
          sourceLabel: body.data.sourceLabel,
          certificateLabel: body.data.certificateLabel,
          manufacturerLabel: body.data.manufacturerLabel,
          modelLabel: body.data.modelLabel,
          serialNumberLabel: body.data.serialNumberLabel,
          nominalValueLabel: body.data.nominalValueLabel,
          classLabel: body.data.classLabel,
          usageRangeLabel: body.data.usageRangeLabel,
          measurementValue: body.data.measurementValue,
          applicableRangeMin: body.data.applicableRangeMin,
          applicableRangeMax: body.data.applicableRangeMax,
          uncertaintyLabel: body.data.uncertaintyLabel,
          correctionFactorLabel: body.data.correctionFactorLabel,
          metrologyProfile: metrologyProfile ?? undefined,
          hasValidCertificate: body.data.hasValidCertificate,
          certificateValidUntilUtc: body.data.certificateValidUntilUtc,
        });
      } else {
        await registryPersistence.setStandardArchived(
          context.user.organizationId,
          body.data.standardId,
          body.data.action === "archive",
          context.user.userId,
        );
      }
    } catch (error) {
      if (isConflictError(error)) {
        return reply.code(409).send({ error: "standard_registry_conflict" });
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
