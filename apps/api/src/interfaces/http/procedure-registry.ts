import { procedureRegistryCatalogSchema, type ProcedureRegistryCatalog } from "@afere/contracts";
import type { FastifyInstance } from "fastify";
import { z } from "zod";

import type { CorePersistence } from "../../domain/auth/core-persistence.js";
import { buildPersistedProcedureRegistryCatalog } from "../../domain/registry/persisted-registry-catalogs.js";
import type { RegistryPersistence } from "../../domain/registry/registry-persistence.js";
import { buildProcedureRegistryCatalog } from "../../domain/registry/procedure-registry-scenarios.js";
import { requireRegistryAccess, requireRegistryWriteAccess } from "./auth-session.js";
import {
  isConflictError,
  readRedirectTarget,
  toOptionalString,
  toStringArray,
} from "./form-helpers.js";

const QuerySchema = z.object({
  scenario: z.string().min(1).optional(),
  procedure: z.string().min(1).optional(),
});

const SaveProcedureBodySchema = z.object({
  action: z.literal("save"),
  procedureId: z.preprocess(toOptionalString, z.string().min(1).optional()),
  code: z.string().min(2),
  title: z.string().min(3),
  typeLabel: z.string().min(2),
  revisionLabel: z.string().min(1),
  effectiveSinceUtc: z.string().min(1),
  effectiveUntilUtc: z.preprocess(toOptionalString, z.string().min(1).optional()),
  lifecycleLabel: z.string().min(2),
  usageLabel: z.string().min(2),
  scopeLabel: z.string().min(3),
  environmentRangeLabel: z.string().min(2),
  curvePolicyLabel: z.string().min(2),
  standardsPolicyLabel: z.string().min(2),
  approvalLabel: z.string().min(2),
  relatedDocuments: z.preprocess(toStringArray, z.array(z.string().min(1))),
  redirectTo: z.preprocess(toOptionalString, z.string().min(1).optional()),
});

const ToggleProcedureArchiveBodySchema = z.object({
  action: z.enum(["archive", "restore"]),
  procedureId: z.string().min(1),
  redirectTo: z.preprocess(toOptionalString, z.string().min(1).optional()),
});

const ManageProcedureBodySchema = z.discriminatedUnion("action", [
  SaveProcedureBodySchema,
  ToggleProcedureArchiveBodySchema,
]);

export async function registerProcedureRegistryRoutes(
  app: FastifyInstance,
  corePersistence: CorePersistence,
  registryPersistence: RegistryPersistence,
) {
  app.get("/registry/procedures", async (request, reply) => {
    const query = QuerySchema.safeParse(request.query);
    if (!query.success) {
      return reply.code(400).send({ error: "invalid_query" });
    }

    if (query.data.scenario) {
      const payload: ProcedureRegistryCatalog = procedureRegistryCatalogSchema.parse(
        buildProcedureRegistryCatalog(query.data.scenario, query.data.procedure),
      );

      return reply.code(200).send(payload);
    }

    const context = await requireRegistryAccess(request, reply, corePersistence);
    if (!context) {
      return reply;
    }

    const [procedures, equipment] = await Promise.all([
      registryPersistence.listProceduresByOrganization(context.user.organizationId),
      registryPersistence.listEquipmentByOrganization(context.user.organizationId),
    ]);

    if (procedures.length === 0) {
      return reply.code(404).send({ error: "procedure_registry_empty" });
    }

    const payload: ProcedureRegistryCatalog = procedureRegistryCatalogSchema.parse(
      buildPersistedProcedureRegistryCatalog({
        nowUtc: new Date().toISOString(),
        selectedProcedureId: query.data.procedure,
        procedures,
        equipment,
      }),
    );

    return reply.code(200).send(payload);
  });

  app.post("/registry/procedures/manage", async (request, reply) => {
    const context = await requireRegistryWriteAccess(request, reply, corePersistence);
    if (!context) {
      return reply;
    }

    const body = ManageProcedureBodySchema.safeParse(request.body);
    if (!body.success) {
      return reply.code(400).send({ error: "invalid_body" });
    }

    try {
      if (body.data.action === "save") {
        await registryPersistence.saveProcedure({
          organizationId: context.user.organizationId,
          procedureId: body.data.procedureId,
          actorUserId: context.user.userId,
          code: body.data.code,
          title: body.data.title,
          typeLabel: body.data.typeLabel,
          revisionLabel: body.data.revisionLabel,
          effectiveSinceUtc: body.data.effectiveSinceUtc,
          effectiveUntilUtc: body.data.effectiveUntilUtc,
          lifecycleLabel: body.data.lifecycleLabel,
          usageLabel: body.data.usageLabel,
          scopeLabel: body.data.scopeLabel,
          environmentRangeLabel: body.data.environmentRangeLabel,
          curvePolicyLabel: body.data.curvePolicyLabel,
          standardsPolicyLabel: body.data.standardsPolicyLabel,
          approvalLabel: body.data.approvalLabel,
          relatedDocuments: body.data.relatedDocuments,
        });
      } else {
        await registryPersistence.setProcedureArchived(
          context.user.organizationId,
          body.data.procedureId,
          body.data.action === "archive",
          context.user.userId,
        );
      }
    } catch (error) {
      if (isConflictError(error)) {
        return reply.code(409).send({ error: "procedure_registry_conflict" });
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
