import cors from "@fastify/cors";
import Fastify, { type FastifyInstance } from "fastify";

import type { Env } from "./config/env.js";
import {
  checkRuntimeReadiness,
  createRuntimeReadiness,
  type RuntimeReadiness,
} from "./infra/runtime-readiness.js";
import { registerAuditTrailRoutes } from "./interfaces/http/audit-trail.js";
import { registerCertificatePreviewRoutes } from "./interfaces/http/certificate-preview.js";
import { registerCustomerRegistryRoutes } from "./interfaces/http/customer-registry.js";
import { registerEmissionDryRunRoutes } from "./interfaces/http/emission-dry-run.js";
import { registerEmissionWorkspaceRoutes } from "./interfaces/http/emission-workspace.js";
import { registerEquipmentRegistryRoutes } from "./interfaces/http/equipment-registry.js";
import { registerNonconformityRoutes } from "./interfaces/http/nonconformities.js";
import { registerOfflineSyncRoutes } from "./interfaces/http/offline-sync.js";
import { registerOnboardingRoutes } from "./interfaces/http/onboarding.js";
import { registerOrganizationSettingsRoutes } from "./interfaces/http/organization-settings.js";
import { registerPortalCertificateRoutes } from "./interfaces/http/portal-certificate.js";
import { registerPortalDashboardRoutes } from "./interfaces/http/portal-dashboard.js";
import { registerPortalEquipmentRoutes } from "./interfaces/http/portal-equipment.js";
import { registerProcedureRegistryRoutes } from "./interfaces/http/procedure-registry.js";
import { registerPublicCertificateRoutes } from "./interfaces/http/public-certificate.js";
import { registerQualityHubRoutes } from "./interfaces/http/quality-hub.js";
import { registerReviewSignatureRoutes } from "./interfaces/http/review-signature.js";
import { registerSelfSignupRoutes } from "./interfaces/http/self-signup.js";
import { registerServiceOrderReviewRoutes } from "./interfaces/http/service-order-review.js";
import { registerSignatureQueueRoutes } from "./interfaces/http/signature-queue.js";
import { registerStandardRegistryRoutes } from "./interfaces/http/standard-registry.js";
import { registerUserDirectoryRoutes } from "./interfaces/http/user-directory.js";
import { trpcPlugin } from "./plugins/trpc.js";

export type BuildAppOptions = {
  env: Env;
  runtimeReadiness?: RuntimeReadiness;
};

export async function buildApp(options: BuildAppOptions): Promise<FastifyInstance> {
  const { env } = options;

  const app = Fastify({
    logger: {
      level: env.LOG_LEVEL,
      transport:
        env.NODE_ENV === "development"
          ? { target: "pino-pretty", options: { colorize: true, translateTime: "HH:MM:ss.l" } }
          : undefined,
    },
    genReqId: (req) => (req.headers["x-request-id"] as string | undefined) ?? crypto.randomUUID(),
  });

  const runtimeReadiness = options.runtimeReadiness ?? createRuntimeReadiness(env, {
    onRedisError: (error) => {
      app.log.warn({ err: error }, "redis readiness client error");
    },
  });

  app.addHook("onClose", async () => {
    await runtimeReadiness.close();
  });

  await app.register(cors, {
    origin: env.CORS_ORIGINS.length > 0 ? env.CORS_ORIGINS : false,
    credentials: true,
  });

  await app.register(trpcPlugin);
  await registerAuditTrailRoutes(app);
  await registerCertificatePreviewRoutes(app);
  await registerCustomerRegistryRoutes(app);
  await registerEmissionDryRunRoutes(app);
  await registerEmissionWorkspaceRoutes(app);
  await registerEquipmentRegistryRoutes(app);
  await registerNonconformityRoutes(app);
  await registerOfflineSyncRoutes(app);
  await registerQualityHubRoutes(app);
  await registerReviewSignatureRoutes(app);
  await registerServiceOrderReviewRoutes(app);
  await registerSignatureQueueRoutes(app);
  await registerStandardRegistryRoutes(app);
  await registerSelfSignupRoutes(app);
  await registerUserDirectoryRoutes(app);
  await registerOnboardingRoutes(app);
  await registerOrganizationSettingsRoutes(app);
  await registerPortalCertificateRoutes(app);
  await registerPortalDashboardRoutes(app);
  await registerPortalEquipmentRoutes(app);
  await registerProcedureRegistryRoutes(app);
  await registerPublicCertificateRoutes(app);

  app.get("/healthz", async () => ({
    status: "ok",
    version: "0.0.1",
    ts: new Date().toISOString(),
  }));

  app.get("/readyz", async (_req, reply) => {
    const readiness = await checkRuntimeReadiness(runtimeReadiness.probes);

    return reply.code(readiness.ok ? 200 : 503).send(readiness);
  });

  return app;
}
