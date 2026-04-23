import {
  equipmentInstrumentKindSchema,
  equipmentMetrologyProfileSchema,
  equipmentNormativeClassSchema,
  equipmentRegistryCatalogSchema,
  type EquipmentMetrologyProfile,
  type EquipmentRegistryCatalog,
} from "@afere/contracts";
import type { FastifyInstance } from "fastify";
import { z } from "zod";

import type { CorePersistence } from "../../domain/auth/core-persistence.js";
import { buildPersistedEquipmentRegistryCatalog } from "../../domain/registry/persisted-registry-catalogs.js";
import type { RegistryPersistence } from "../../domain/registry/registry-persistence.js";
import { buildEquipmentRegistryCatalog } from "../../domain/registry/customer-equipment-scenarios.js";
import { requireRegistryAccess, requireRegistryWriteAccess } from "./auth-session.js";
import {
  isConflictError,
  readRedirectTarget,
  toNumber,
  toOptionalString,
  toStringArray,
} from "./form-helpers.js";

const QuerySchema = z.object({
  scenario: z.string().min(1).optional(),
  equipment: z.string().min(1).optional(),
});

const SaveEquipmentBodySchema = z.object({
  action: z.literal("save"),
  equipmentId: z.preprocess(toOptionalString, z.string().min(1).optional()),
  customerId: z.string().min(1),
  procedureId: z.preprocess(toOptionalString, z.string().min(1).optional()),
  primaryStandardId: z.preprocess(toOptionalString, z.string().min(1).optional()),
  code: z.string().min(2),
  tagCode: z.string().min(2),
  serialNumber: z.string().min(2),
  typeModelLabel: z.string().min(3),
  capacityClassLabel: z.string().min(3),
  instrumentKind: z.preprocess(toOptionalString, equipmentInstrumentKindSchema.optional()),
  measurementUnit: z.preprocess(toOptionalString, z.string().min(1).optional()),
  maximumCapacityValue: z.preprocess(toNumber, z.number().positive().optional()),
  readabilityValue: z.preprocess(toNumber, z.number().positive().optional()),
  verificationScaleIntervalValue: z.preprocess(toNumber, z.number().positive().optional()),
  normativeClass: z.preprocess(toOptionalString, equipmentNormativeClassSchema.optional()),
  minimumCapacityValue: z.preprocess(toNumber, z.number().nonnegative().optional()),
  minimumLoadValue: z.preprocess(toNumber, z.number().nonnegative().optional()),
  effectiveRangeMinValue: z.preprocess(toNumber, z.number().nonnegative().optional()),
  effectiveRangeMaxValue: z.preprocess(toNumber, z.number().positive().optional()),
  supportingStandardCodes: z.preprocess(toStringArray, z.array(z.string().min(1))),
  addressLine1: z.string().min(3),
  addressCity: z.string().min(2),
  addressState: z.string().min(2),
  addressPostalCode: z.preprocess(toOptionalString, z.string().min(1).optional()),
  addressCountry: z.string().min(2),
  addressConditionsLabel: z.preprocess(toOptionalString, z.string().min(1).optional()),
  lastCalibrationAtUtc: z.preprocess(toOptionalString, z.string().min(1).optional()),
  nextCalibrationAtUtc: z.preprocess(toOptionalString, z.string().min(1).optional()),
  redirectTo: z.preprocess(toOptionalString, z.string().min(1).optional()),
});
type SaveEquipmentBody = z.infer<typeof SaveEquipmentBodySchema>;

const ToggleEquipmentArchiveBodySchema = z.object({
  action: z.enum(["archive", "restore"]),
  equipmentId: z.string().min(1),
  redirectTo: z.preprocess(toOptionalString, z.string().min(1).optional()),
});

const ManageEquipmentBodySchema = z.discriminatedUnion("action", [
  SaveEquipmentBodySchema,
  ToggleEquipmentArchiveBodySchema,
]);

function buildEquipmentMetrologyProfile(body: SaveEquipmentBody): EquipmentMetrologyProfile | undefined | null {
  const candidate = {
    instrumentKind: body.instrumentKind,
    measurementUnit: body.measurementUnit,
    maximumCapacityValue: body.maximumCapacityValue,
    readabilityValue: body.readabilityValue,
    verificationScaleIntervalValue: body.verificationScaleIntervalValue,
    normativeClass: body.normativeClass,
    minimumCapacityValue: body.minimumCapacityValue,
    minimumLoadValue: body.minimumLoadValue,
    effectiveRangeMinValue: body.effectiveRangeMinValue,
    effectiveRangeMaxValue: body.effectiveRangeMaxValue,
  };

  if (!Object.values(candidate).some((value) => value !== undefined)) {
    return undefined;
  }

  const parsed = equipmentMetrologyProfileSchema.safeParse(candidate);
  return parsed.success ? parsed.data : null;
}

export async function registerEquipmentRegistryRoutes(
  app: FastifyInstance,
  corePersistence: CorePersistence,
  registryPersistence: RegistryPersistence,
) {
  app.get("/registry/equipment", async (request, reply) => {
    const query = QuerySchema.safeParse(request.query);
    if (!query.success) {
      return reply.code(400).send({ error: "invalid_query" });
    }

    if (query.data.scenario) {
      const payload: EquipmentRegistryCatalog = equipmentRegistryCatalogSchema.parse(
        buildEquipmentRegistryCatalog(query.data.scenario, query.data.equipment),
      );

      return reply.code(200).send(payload);
    }

    const context = await requireRegistryAccess(request, reply, corePersistence);
    if (!context) {
      return reply;
    }

    const [customers, standards, procedures, equipment] = await Promise.all([
      registryPersistence.listCustomersByOrganization(context.user.organizationId),
      registryPersistence.listStandardsByOrganization(context.user.organizationId),
      registryPersistence.listProceduresByOrganization(context.user.organizationId),
      registryPersistence.listEquipmentByOrganization(context.user.organizationId),
    ]);

    if (equipment.length === 0) {
      return reply.code(404).send({ error: "equipment_registry_empty" });
    }

    const payload: EquipmentRegistryCatalog = equipmentRegistryCatalogSchema.parse(
      buildPersistedEquipmentRegistryCatalog({
        nowUtc: new Date().toISOString(),
        selectedEquipmentId: query.data.equipment,
        customers,
        standards,
        procedures,
        equipment,
      }),
    );

    return reply.code(200).send(payload);
  });

  app.post("/registry/equipment/manage", async (request, reply) => {
    const context = await requireRegistryWriteAccess(request, reply, corePersistence);
    if (!context) {
      return reply;
    }

    const body = ManageEquipmentBodySchema.safeParse(request.body);
    if (!body.success) {
      return reply.code(400).send({ error: "invalid_body" });
    }

    const metrologyProfile =
      body.data.action === "save" ? buildEquipmentMetrologyProfile(body.data) : undefined;
    if (body.data.action === "save" && metrologyProfile === null) {
      return reply.code(400).send({ error: "invalid_equipment_metrology_profile" });
    }

    try {
      if (body.data.action === "save") {
        await registryPersistence.saveEquipment({
          organizationId: context.user.organizationId,
          equipmentId: body.data.equipmentId,
          actorUserId: context.user.userId,
          customerId: body.data.customerId,
          procedureId: body.data.procedureId,
          primaryStandardId: body.data.primaryStandardId,
          code: body.data.code,
          tagCode: body.data.tagCode,
          serialNumber: body.data.serialNumber,
          typeModelLabel: body.data.typeModelLabel,
          capacityClassLabel: body.data.capacityClassLabel,
          metrologyProfile: metrologyProfile ?? undefined,
          supportingStandardCodes: body.data.supportingStandardCodes,
          addressLine1: body.data.addressLine1,
          addressCity: body.data.addressCity,
          addressState: body.data.addressState,
          addressPostalCode: body.data.addressPostalCode,
          addressCountry: body.data.addressCountry,
          addressConditionsLabel: body.data.addressConditionsLabel,
          lastCalibrationAtUtc: body.data.lastCalibrationAtUtc,
          nextCalibrationAtUtc: body.data.nextCalibrationAtUtc,
        });
      } else {
        await registryPersistence.setEquipmentArchived(
          context.user.organizationId,
          body.data.equipmentId,
          body.data.action === "archive",
          context.user.userId,
        );
      }
    } catch (error) {
      if (isConflictError(error)) {
        return reply.code(409).send({ error: "equipment_registry_conflict" });
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
