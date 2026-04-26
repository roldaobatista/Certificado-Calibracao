import { customerRegistryCatalogSchema, type CustomerRegistryCatalog } from "@afere/contracts";
import type { FastifyInstance } from "fastify";
import { z } from "zod";

import type { CorePersistence } from "../../domain/auth/core-persistence.js";
import type { Env } from "../../config/env.js";
import {
  buildPersistedCustomerRegistryCatalog,
} from "../../domain/registry/persisted-registry-catalogs.js";
import type { RegistryPersistence } from "../../domain/registry/registry-persistence.js";
import { buildCustomerRegistryCatalog } from "../../domain/registry/customer-equipment-scenarios.js";
import { requireRegistryAccess, requireRegistryWriteAccess } from "./auth-session.js";
import { isConflictError, readRedirectTarget, toOptionalString } from "./form-helpers.js";

const QuerySchema = z.object({
  scenario: z.string().min(1).optional(),
  customer: z.string().min(1).optional(),
});

const SaveCustomerBodySchema = z.object({
  action: z.literal("save"),
  customerId: z.preprocess(toOptionalString, z.string().min(1).optional()),
  legalName: z.string().min(3),
  tradeName: z.string().min(2),
  documentLabel: z.string().min(3),
  segmentLabel: z.string().min(2),
  accountOwnerName: z.string().min(3),
  accountOwnerEmail: z.string().email(),
  contractLabel: z.string().min(3),
  specialConditionsLabel: z.string().min(3),
  contactName: z.string().min(3),
  contactRoleLabel: z.string().min(2),
  contactEmail: z.string().email(),
  contactPhoneLabel: z.preprocess(toOptionalString, z.string().min(1).optional()),
  addressLine1: z.string().min(3),
  addressCity: z.string().min(2),
  addressState: z.string().min(2),
  addressPostalCode: z.preprocess(toOptionalString, z.string().min(1).optional()),
  addressCountry: z.string().min(2),
  addressConditionsLabel: z.preprocess(toOptionalString, z.string().min(1).optional()),
  redirectTo: z.preprocess(toOptionalString, z.string().min(1).optional()),
});

const ToggleCustomerArchiveBodySchema = z.object({
  action: z.enum(["archive", "restore"]),
  customerId: z.string().min(1),
  redirectTo: z.preprocess(toOptionalString, z.string().min(1).optional()),
});

const ManageCustomerBodySchema = z.discriminatedUnion("action", [
  SaveCustomerBodySchema,
  ToggleCustomerArchiveBodySchema,
]);

export async function registerCustomerRegistryRoutes(
  app: FastifyInstance,
  corePersistence: CorePersistence,
  registryPersistence: RegistryPersistence,
  env: Env,
) {
  app.get("/registry/customers", async (request, reply) => {
    const query = QuerySchema.safeParse(request.query);
    if (!query.success) {
      return reply.code(400).send({ error: "invalid_query" });
    }

    if (query.data.scenario) {
      if (!env.ALLOW_SCENARIO_ROUTES) {
        return reply.code(403).send({ error: "scenario_not_allowed" });
      }
      const payload: CustomerRegistryCatalog = customerRegistryCatalogSchema.parse(
        buildCustomerRegistryCatalog(query.data.scenario, query.data.customer),
      );

      return reply.code(200).send(payload);
    }

    const context = await requireRegistryAccess(request, reply, corePersistence);
    if (!context) {
      return reply;
    }

    const customers = await registryPersistence.listCustomersByOrganization(context.user.organizationId);
    if (customers.length === 0) {
      return reply.code(404).send({ error: "customer_registry_empty" });
    }

    const equipment = await registryPersistence.listEquipmentByOrganization(context.user.organizationId);
    const selectedCustomerId = query.data.customer ?? customers[0]?.customerId;
    const auditEvents = selectedCustomerId
      ? await registryPersistence.listCustomerAuditEvents(
          context.user.organizationId,
          selectedCustomerId,
        )
      : [];

    const payload: CustomerRegistryCatalog = customerRegistryCatalogSchema.parse(
      buildPersistedCustomerRegistryCatalog({
        nowUtc: new Date().toISOString(),
        selectedCustomerId,
        customers,
        equipment,
        selectedCustomerAuditEvents: auditEvents,
      }),
    );

    return reply.code(200).send(payload);
  });

  app.post("/registry/customers/manage", async (request, reply) => {
    const context = await requireRegistryWriteAccess(request, reply, corePersistence);
    if (!context) {
      return reply;
    }

    const body = ManageCustomerBodySchema.safeParse(request.body);
    if (!body.success) {
      return reply.code(400).send({ error: "invalid_body" });
    }

    try {
      if (body.data.action === "save") {
        await registryPersistence.saveCustomer({
          organizationId: context.user.organizationId,
          customerId: body.data.customerId,
          actorUserId: context.user.userId,
          legalName: body.data.legalName,
          tradeName: body.data.tradeName,
          documentLabel: body.data.documentLabel,
          segmentLabel: body.data.segmentLabel,
          accountOwnerName: body.data.accountOwnerName,
          accountOwnerEmail: body.data.accountOwnerEmail,
          contractLabel: body.data.contractLabel,
          specialConditionsLabel: body.data.specialConditionsLabel,
          contactName: body.data.contactName,
          contactRoleLabel: body.data.contactRoleLabel,
          contactEmail: body.data.contactEmail,
          contactPhoneLabel: body.data.contactPhoneLabel,
          addressLine1: body.data.addressLine1,
          addressCity: body.data.addressCity,
          addressState: body.data.addressState,
          addressPostalCode: body.data.addressPostalCode,
          addressCountry: body.data.addressCountry,
          addressConditionsLabel: body.data.addressConditionsLabel,
        });
      } else {
        await registryPersistence.setCustomerArchived(
          context.user.organizationId,
          body.data.customerId,
          body.data.action === "archive",
          context.user.userId,
        );
      }
    } catch (error) {
      if (isConflictError(error)) {
        return reply.code(409).send({ error: "customer_registry_conflict" });
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
