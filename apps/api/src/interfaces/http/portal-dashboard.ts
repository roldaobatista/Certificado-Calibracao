import { portalDashboardCatalogSchema, type PortalDashboardCatalog } from "@afere/contracts";
import type { FastifyInstance } from "fastify";
import { z } from "zod";

import type { CorePersistence } from "../../domain/auth/core-persistence.js";
import { type RegistryPersistence } from "../../domain/registry/registry-persistence.js";
import type { ServiceOrderPersistence } from "../../domain/emission/service-order-persistence.js";
import {
  buildPersistedPortalDashboardCatalog,
  resolvePortalCustomerByEmail,
} from "../../domain/portal/persisted-portal-catalogs.js";
import { buildPortalDashboardCatalog } from "../../domain/portal/portal-dashboard-scenarios.js";
import { requirePortalAccess } from "./auth-session.js";

const QuerySchema = z.object({
  scenario: z.string().min(1).optional(),
});

export async function registerPortalDashboardRoutes(
  app: FastifyInstance,
  corePersistence: CorePersistence,
  registryPersistence: RegistryPersistence,
  serviceOrderPersistence: ServiceOrderPersistence,
) {
  app.get("/portal/dashboard", async (request, reply) => {
    const query = QuerySchema.safeParse(request.query);

    if (!query.success) {
      return reply.code(400).send({ error: "invalid_query" });
    }

    if (!query.data.scenario) {
      const context = await requirePortalAccess(request, reply, corePersistence);
      if (!context) {
        return reply;
      }

      const [customers, equipment, publications] = await Promise.all([
        registryPersistence.listCustomersByOrganization(context.user.organizationId),
        registryPersistence.listEquipmentByOrganization(context.user.organizationId),
        serviceOrderPersistence.listCertificatePublicationsByOrganization(context.user.organizationId),
      ]);

      const customer = resolvePortalCustomerByEmail(
        {
          organizationName: context.user.organizationName,
          userEmail: context.user.email,
        },
        customers,
      );

      const payload: PortalDashboardCatalog = portalDashboardCatalogSchema.parse(
        buildPersistedPortalDashboardCatalog({
          nowUtc: new Date().toISOString(),
          organizationName: context.user.organizationName,
          customer,
          equipment,
          publications,
        }),
      );

      return reply.code(200).send(payload);
    }

    const payload: PortalDashboardCatalog = portalDashboardCatalogSchema.parse(
      buildPortalDashboardCatalog(query.data.scenario),
    );

    return reply.code(200).send(payload);
  });
}
