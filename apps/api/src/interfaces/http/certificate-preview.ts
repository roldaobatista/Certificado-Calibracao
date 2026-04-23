import {
  certificatePreviewCatalogSchema,
  type CertificatePreviewCatalog,
  type CertificatePreviewScenario as ContractCertificatePreviewScenario,
} from "@afere/contracts";
import type { FastifyInstance } from "fastify";
import { z } from "zod";

import type { CorePersistence } from "../../domain/auth/core-persistence.js";
import { buildPersistedCertificatePreviewCatalog } from "../../domain/emission/persisted-emission-flow.js";
import {
  listCertificatePreviewScenarios,
  resolveCertificatePreviewScenario,
} from "../../domain/emission/certificate-preview-scenarios.js";
import type { ServiceOrderPersistence } from "../../domain/emission/service-order-persistence.js";
import { requireWorkspaceAccess } from "./auth-session.js";

const QuerySchema = z.object({
  scenario: z.string().min(1).optional(),
  item: z.string().min(1).optional(),
});

export async function registerCertificatePreviewRoutes(
  app: FastifyInstance,
  corePersistence: CorePersistence,
  serviceOrderPersistence: ServiceOrderPersistence,
) {
  app.get("/emission/certificate-preview", async (request, reply) => {
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

      const payload: CertificatePreviewCatalog = certificatePreviewCatalogSchema.parse(
        buildPersistedCertificatePreviewCatalog({
          nowUtc: new Date().toISOString(),
          records,
          users,
          onboarding,
          selectedItemId: query.data.item,
        }),
      );

      return reply.code(200).send(payload);
    }

    const selectedScenario = resolveCertificatePreviewScenario(query.data.scenario);
    const payload: CertificatePreviewCatalog = certificatePreviewCatalogSchema.parse({
      selectedScenarioId: selectedScenario.id,
      scenarios: listCertificatePreviewScenarios().map(toContractScenario),
    });

    return reply.code(200).send(payload);
  });
}

function toContractScenario(
  scenario: ReturnType<typeof resolveCertificatePreviewScenario>,
): ContractCertificatePreviewScenario {
  return {
    id: scenario.id,
    label: scenario.label,
    description: scenario.description,
    result: scenario.result,
  };
}
