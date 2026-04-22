import cors from "@fastify/cors";
import Fastify, { type FastifyInstance } from "fastify";

import type { Env } from "./config/env.js";
import {
  checkRuntimeReadiness,
  createRuntimeReadiness,
  type RuntimeReadiness,
} from "./infra/runtime-readiness.js";
import { registerCertificatePreviewRoutes } from "./interfaces/http/certificate-preview.js";
import { registerEmissionDryRunRoutes } from "./interfaces/http/emission-dry-run.js";
import { registerEmissionWorkspaceRoutes } from "./interfaces/http/emission-workspace.js";
import { registerOnboardingRoutes } from "./interfaces/http/onboarding.js";
import { registerPublicCertificateRoutes } from "./interfaces/http/public-certificate.js";
import { registerReviewSignatureRoutes } from "./interfaces/http/review-signature.js";
import { registerSelfSignupRoutes } from "./interfaces/http/self-signup.js";
import { registerSignatureQueueRoutes } from "./interfaces/http/signature-queue.js";
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
  await registerCertificatePreviewRoutes(app);
  await registerEmissionDryRunRoutes(app);
  await registerEmissionWorkspaceRoutes(app);
  await registerReviewSignatureRoutes(app);
  await registerSignatureQueueRoutes(app);
  await registerSelfSignupRoutes(app);
  await registerUserDirectoryRoutes(app);
  await registerOnboardingRoutes(app);
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
