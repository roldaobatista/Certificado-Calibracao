import {
  publicCertificateCatalogSchema,
  type PublicCertificateCatalog,
  type PublicCertificateScenario as ContractPublicCertificateScenario,
} from "@afere/contracts";
import type { FastifyInstance } from "fastify";
import { z } from "zod";

import type { ServiceOrderPersistence } from "../../domain/emission/service-order-persistence.js";
import { buildPersistedPublicCertificateCatalog } from "../../domain/certificates/persisted-public-certificate-catalog.js";
import {
  listPublicCertificateScenarios,
  resolvePublicCertificateScenario,
  type PublicCertificateScenario,
} from "../../domain/certificates/public-certificate-scenarios.js";

const CERTIFICATE_ID_MAX_LEN = 64;
const TOKEN_MAX_LEN = 128;

const QuerySchema = z.object({
  scenario: z.string().min(1).optional(),
  certificate: z
    .string()
    .min(1)
    .max(CERTIFICATE_ID_MAX_LEN)
    .regex(/^[A-Za-z0-9\-_]+$/, "invalid_certificate_format")
    .optional(),
  token: z
    .string()
    .min(1)
    .max(TOKEN_MAX_LEN)
    .regex(/^[A-Za-z0-9\-_]+$/, "invalid_token_format")
    .optional(),
});

export async function registerPublicCertificateRoutes(
  app: FastifyInstance,
  serviceOrderPersistence: ServiceOrderPersistence,
) {
  app.get("/portal/verify", {
    config: { rateLimit: { max: 30, timeWindow: 60 * 1000 } },
    handler: async (request, reply) => {
      const query = QuerySchema.safeParse(request.query);
      if (!query.success) {
        return reply.code(400).send({ error: "invalid_query" });
      }

      if (!query.data.scenario) {
        const organizationId = query.data.certificate
          ? await serviceOrderPersistence.findOrganizationIdByServiceOrderId(query.data.certificate)
          : null;
        const publications = query.data.certificate && organizationId
          ? await serviceOrderPersistence.listCertificatePublicationsByServiceOrder(query.data.certificate, organizationId)
          : [];
        const auditEvents = query.data.certificate && organizationId
          ? await serviceOrderPersistence.listEmissionAuditEventsByServiceOrder(query.data.certificate, organizationId)
          : [];
        const payload: PublicCertificateCatalog = publicCertificateCatalogSchema.parse(
          buildPersistedPublicCertificateCatalog({
            serviceOrderId: query.data.certificate,
            token: query.data.token,
            publications,
            auditEvents,
          }),
        );

        return reply.code(200).send(payload);
      }

      const selectedScenario = resolvePublicCertificateScenario(query.data.scenario);
      const payload: PublicCertificateCatalog = publicCertificateCatalogSchema.parse({
        selectedScenarioId: selectedScenario.id,
        scenarios: listPublicCertificateScenarios().map(toContractScenario),
      });

      return reply.code(200).send(payload);
    },
  });
}

function toContractScenario(scenario: PublicCertificateScenario): ContractPublicCertificateScenario {
  return {
    id: scenario.id,
    label: scenario.label,
    description: scenario.description,
    result: scenario.result,
  };
}
