import cookie from "@fastify/cookie";
import cors from "@fastify/cors";
import csrfProtection from "@fastify/csrf-protection";
import formbody from "@fastify/formbody";
import helmet from "@fastify/helmet";
import rateLimit from "@fastify/rate-limit";
import { createPrismaClient } from "@afere/db";
import Fastify, { type FastifyInstance } from "fastify";

import type { Env } from "./config/env.js";
import { createPrismaCorePersistence, type CorePersistence } from "./domain/auth/core-persistence.js";
import {
  createPrismaServiceOrderPersistence,
  type ServiceOrderPersistence,
} from "./domain/emission/service-order-persistence.js";
import {
  createMemoryQualityPersistence,
  createPrismaQualityPersistence,
  type QualityPersistence,
} from "./domain/quality/quality-persistence.js";
import {
  createPrismaRegistryPersistence,
  type RegistryPersistence,
} from "./domain/registry/registry-persistence.js";
import {
  checkRuntimeReadiness,
  createRuntimeReadiness,
  type RuntimeReadiness,
} from "./infra/runtime-readiness.js";
import { registerAuditTrailRoutes } from "./interfaces/http/audit-trail.js";
import { registerCertificatePreviewRoutes } from "./interfaces/http/certificate-preview.js";
import { registerComplaintRoutes } from "./interfaces/http/complaints.js";
import { registerCustomerRegistryRoutes } from "./interfaces/http/customer-registry.js";
import { registerAuthSessionRoutes } from "./interfaces/http/auth-session.js";
import { registerEmissionDryRunRoutes } from "./interfaces/http/emission-dry-run.js";
import { registerEmissionWorkspaceRoutes } from "./interfaces/http/emission-workspace.js";
import { registerEquipmentRegistryRoutes } from "./interfaces/http/equipment-registry.js";
import { registerInternalAuditRoutes } from "./interfaces/http/internal-audit.js";
import { registerManagementReviewRoutes } from "./interfaces/http/management-review.js";
import { registerNonconformingWorkRoutes } from "./interfaces/http/nonconforming-work.js";
import { registerNonconformityRoutes } from "./interfaces/http/nonconformities.js";
import { registerOfflineSyncRoutes } from "./interfaces/http/offline-sync.js";
import { registerOnboardingRoutes } from "./interfaces/http/onboarding.js";
import { registerOrganizationSettingsRoutes } from "./interfaces/http/organization-settings.js";
import { registerPortalCertificateRoutes } from "./interfaces/http/portal-certificate.js";
import { registerPortalDashboardRoutes } from "./interfaces/http/portal-dashboard.js";
import { registerPortalEquipmentRoutes } from "./interfaces/http/portal-equipment.js";
import { registerProcedureRegistryRoutes } from "./interfaces/http/procedure-registry.js";
import { registerPublicCertificateRoutes } from "./interfaces/http/public-certificate.js";
import { registerQualityDocumentRoutes } from "./interfaces/http/quality-documents.js";
import { registerQualityHubRoutes } from "./interfaces/http/quality-hub.js";
import { registerQualityIndicatorRoutes } from "./interfaces/http/quality-indicators.js";
import { registerRiskRegisterRoutes } from "./interfaces/http/risk-register.js";
import { registerReviewSignatureRoutes } from "./interfaces/http/review-signature.js";
import { registerSelfSignupRoutes } from "./interfaces/http/self-signup.js";
import { registerServiceOrderReviewRoutes } from "./interfaces/http/service-order-review.js";
import { registerSignatureQueueRoutes } from "./interfaces/http/signature-queue.js";
import { registerStandardRegistryRoutes } from "./interfaces/http/standard-registry.js";
import { registerUserDirectoryRoutes } from "./interfaces/http/user-directory.js";
import { registerRouteAuthorizationHook } from "./domain/auth/route-authorization.js";
import { trpcPlugin } from "./plugins/trpc.js";

export type BuildAppOptions = {
  env: Env;
  runtimeReadiness?: RuntimeReadiness;
  corePersistence?: CorePersistence;
  registryPersistence?: RegistryPersistence;
  serviceOrderPersistence?: ServiceOrderPersistence;
  qualityPersistence?: QualityPersistence;
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

  const useMemory =
    options.corePersistence && options.registryPersistence && options.serviceOrderPersistence;

  const prismaAuth = useMemory
    ? null
    : createPrismaClient(env.DATABASE_OWNER_URL ?? env.DATABASE_URL);
  const prismaApp = useMemory
    ? null
    : createPrismaClient(env.DATABASE_APP_URL ?? env.DATABASE_URL);

  const corePersistence =
    options.corePersistence ?? createPrismaCorePersistence(
      prismaAuth ?? createPrismaClient(env.DATABASE_URL),
      prismaApp ?? undefined,
    );
  const registryPersistence =
    options.registryPersistence ??
    createPrismaRegistryPersistence(prismaApp ?? createPrismaClient(env.DATABASE_URL));
  const serviceOrderPersistence =
    options.serviceOrderPersistence ??
    createPrismaServiceOrderPersistence(
      prismaApp ?? createPrismaClient(env.DATABASE_URL),
      prismaAuth ?? undefined,
    );
  const qualityPersistence =
    options.qualityPersistence ??
    (useMemory
      ? createMemoryQualityPersistence()
      : createPrismaQualityPersistence(prismaApp ?? createPrismaClient(env.DATABASE_URL)));

  if (prismaAuth) {
    app.addHook("onClose", async () => {
      await prismaAuth.$disconnect();
    });
  }
  if (prismaApp) {
    app.addHook("onClose", async () => {
      await prismaApp.$disconnect();
    });
  }

  await app.register(helmet);
  await app.register(cors, {
    origin: env.CORS_ORIGINS.length > 0 ? env.CORS_ORIGINS : false,
    credentials: true,
  });
  await app.register(cookie, {
    secret: env.COOKIE_SECRET,
    parseOptions: {
      httpOnly: true,
      sameSite: "strict",
      secure: env.NODE_ENV === "production",
    },
  });
  await app.register(csrfProtection, {
    cookieOpts: { signed: true },
    getToken: (req) => {
      return (req.headers["x-csrf-token"] as string | undefined) ?? "";
    },
  });
  await app.register(formbody);
  await app.register(rateLimit, {
    max: env.RATE_LIMIT_MAX,
    timeWindow: env.RATE_LIMIT_WINDOW_MS,
    errorResponseBuilder: (_req, context) => ({
      statusCode: 429,
      error: "Too Many Requests",
      message: `Rate limit exceeded. Retry in ${context.after}`,
    }),
  });

  await app.register(trpcPlugin);
  registerRouteAuthorizationHook(app, corePersistence);
  await registerAuthSessionRoutes(app, corePersistence, env);
  await registerAuditTrailRoutes(app, corePersistence, serviceOrderPersistence);
  await registerCertificatePreviewRoutes(app, corePersistence, serviceOrderPersistence);
  await registerComplaintRoutes(app);
  await registerCustomerRegistryRoutes(app, corePersistence, registryPersistence);
  await registerEmissionDryRunRoutes(app, corePersistence, serviceOrderPersistence);
  await registerEmissionWorkspaceRoutes(app, corePersistence, env);
  await registerEquipmentRegistryRoutes(app, corePersistence, registryPersistence);
  await registerInternalAuditRoutes(app, corePersistence, qualityPersistence);
  await registerManagementReviewRoutes(app, corePersistence, qualityPersistence, serviceOrderPersistence);
  await registerNonconformingWorkRoutes(app, corePersistence, qualityPersistence);
  await registerNonconformityRoutes(app, corePersistence, qualityPersistence);
  await registerOfflineSyncRoutes(app);
  await registerQualityDocumentRoutes(app);
  await registerQualityHubRoutes(app, corePersistence, qualityPersistence, serviceOrderPersistence);
  await registerQualityIndicatorRoutes(app, corePersistence, qualityPersistence, serviceOrderPersistence);
  await registerRiskRegisterRoutes(app);
  await registerReviewSignatureRoutes(app, corePersistence, serviceOrderPersistence, env);
  await registerServiceOrderReviewRoutes(app, corePersistence, serviceOrderPersistence);
  await registerSignatureQueueRoutes(app, corePersistence, serviceOrderPersistence, env);
  await registerStandardRegistryRoutes(app, corePersistence, registryPersistence);
  await registerSelfSignupRoutes(app);
  await registerUserDirectoryRoutes(app, corePersistence);
  await registerOnboardingRoutes(app, corePersistence, env);
  await registerOrganizationSettingsRoutes(app, corePersistence, qualityPersistence, serviceOrderPersistence);
  await registerPortalCertificateRoutes(app, corePersistence, registryPersistence, serviceOrderPersistence);
  await registerPortalDashboardRoutes(app, corePersistence, registryPersistence, serviceOrderPersistence);
  await registerPortalEquipmentRoutes(app, corePersistence, registryPersistence, serviceOrderPersistence);
  await registerProcedureRegistryRoutes(app, corePersistence, registryPersistence);
  await registerPublicCertificateRoutes(app, serviceOrderPersistence);

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
