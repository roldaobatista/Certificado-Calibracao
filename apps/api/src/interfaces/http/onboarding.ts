import {
  onboardingCatalogSchema,
  type OnboardingCatalog,
  type OnboardingScenario as ContractOnboardingScenario,
} from "@afere/contracts";
import type { FastifyInstance } from "fastify";
import { z } from "zod";

import type { CorePersistence } from "../../domain/auth/core-persistence.js";
import type { Env } from "../../config/env.js";
import { evaluateOnboardingReadiness } from "../../domain/onboarding/onboarding-readiness.js";
import {
  listOnboardingScenarios,
  resolveOnboardingScenario,
  type OnboardingScenario,
} from "../../domain/onboarding/onboarding-scenarios.js";
import { requireOnboardingAccess } from "./auth-session.js";

const QuerySchema = z.object({
  scenario: z.string().min(1).optional(),
});

const UpdateBodySchema = z.object({
  organizationProfileCompleted: z.preprocess(toBoolean, z.boolean()),
  primarySignatoryReady: z.preprocess(toBoolean, z.boolean()),
  certificateNumberingConfigured: z.preprocess(toBoolean, z.boolean()),
  scopeReviewCompleted: z.preprocess(toBoolean, z.boolean()),
  publicQrConfigured: z.preprocess(toBoolean, z.boolean()),
  redirectTo: z.string().min(1).optional(),
});

import { isRedirectAllowed } from "./redirect-helpers.js";

export async function registerOnboardingRoutes(
  app: FastifyInstance,
  persistence: CorePersistence,
  env: Env,
) {
  const redirectAllowlist = env.REDIRECT_ALLOWLIST;
  app.get("/onboarding/readiness", async (request, reply) => {
    const query = QuerySchema.safeParse(request.query);
    if (!query.success) {
      return reply.code(400).send({ error: "invalid_query" });
    }

    if (query.data.scenario && !env.ALLOW_SCENARIO_ROUTES) {
      return reply.code(403).send({ error: "scenario_not_allowed" });
    }

    if (!query.data.scenario) {
      const context = await requireOnboardingAccess(request, reply, persistence);
      if (!context) {
        return reply;
      }

      const record = await persistence.getOnboardingByOrganization(context.user.organizationId);
      if (!record) {
        return reply.code(404).send({ error: "onboarding_not_found" });
      }

      const readiness = evaluateOnboardingReadiness({
        startedAtUtc: record.startedAtUtc,
        completedAtUtc: record.completedAtUtc ?? new Date().toISOString(),
        prerequisites: {
          organizationProfileCompleted: record.organizationProfileCompleted,
          primarySignatoryReady: record.primarySignatoryReady,
          certificateNumberingConfigured: record.certificateNumberingConfigured,
          scopeReviewCompleted: record.scopeReviewCompleted,
          publicQrConfigured: record.publicQrConfigured,
        },
      });

      const selectedScenarioId = readiness.canEmitFirstCertificate ? "ready" : "blocked";
      const payload: OnboardingCatalog = onboardingCatalogSchema.parse({
        selectedScenarioId,
        scenarios: [
          {
            id: selectedScenarioId,
            label: readiness.canEmitFirstCertificate
              ? "Onboarding persistido liberado"
              : "Onboarding persistido bloqueado",
            description: readiness.canEmitFirstCertificate
              ? `Organizacao ${record.organizationName} pronta para a primeira emissao sobre dados reais.`
              : `Organizacao ${record.organizationName} ainda exige fechamento dos prerequisitos persistidos.`,
            result: readiness,
            checklist: {
              organizationName: record.organizationName,
              startedAtUtc: record.startedAtUtc,
              completedAtUtc: record.completedAtUtc,
              organizationProfileCompleted: record.organizationProfileCompleted,
              primarySignatoryReady: record.primarySignatoryReady,
              certificateNumberingConfigured: record.certificateNumberingConfigured,
              scopeReviewCompleted: record.scopeReviewCompleted,
              publicQrConfigured: record.publicQrConfigured,
            },
          },
        ],
      });

      return reply.code(200).send(payload);
    }

    const selectedScenario = resolveOnboardingScenario(query.data.scenario);
    const payload: OnboardingCatalog = onboardingCatalogSchema.parse({
      selectedScenarioId: selectedScenario.id,
      scenarios: listOnboardingScenarios().map(toContractScenario),
    });

    return reply.code(200).send(payload);
  });

  app.post("/onboarding/readiness", async (request, reply) => {
    const context = await requireOnboardingAccess(request, reply, persistence);
    if (!context) {
      return reply;
    }

    const body = UpdateBodySchema.safeParse(request.body);
    if (!body.success) {
      return reply.code(400).send({ error: "invalid_body" });
    }

    await persistence.updateOnboardingByOrganization(context.user.organizationId, {
      organizationProfileCompleted: body.data.organizationProfileCompleted,
      primarySignatoryReady: body.data.primarySignatoryReady,
      certificateNumberingConfigured: body.data.certificateNumberingConfigured,
      scopeReviewCompleted: body.data.scopeReviewCompleted,
      publicQrConfigured: body.data.publicQrConfigured,
    });

    if (body.data.redirectTo && isRedirectAllowed(body.data.redirectTo, redirectAllowlist)) {
      return reply.redirect(body.data.redirectTo);
    }

    return reply.code(204).send();
  });
}

function toContractScenario(scenario: OnboardingScenario): ContractOnboardingScenario {
  return {
    id: scenario.id,
    label: scenario.label,
    description: scenario.description,
    result: scenario.result,
  };
}

function toBoolean(value: unknown) {
  if (typeof value === "boolean") {
    return value;
  }

  if (typeof value === "string") {
    return value === "true" || value === "1" || value === "on";
  }

  return false;
}
