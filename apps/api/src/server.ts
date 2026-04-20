import "dotenv/config";
import Fastify from "fastify";
import cors from "@fastify/cors";
import { loadEnv } from "./config/env.js";
import { trpcPlugin } from "./plugins/trpc.js";

const env = loadEnv();

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

await app.register(cors, {
  origin: env.CORS_ORIGINS.length > 0 ? env.CORS_ORIGINS : false,
  credentials: true,
});

await app.register(trpcPlugin);

app.get("/healthz", async () => ({
  status: "ok",
  version: "0.0.1",
  ts: new Date().toISOString(),
}));

app.get("/readyz", async (_req, reply) => {
  // TODO(P0-1.next): checar conectividade com Postgres e Redis antes de reportar ready.
  return reply.send({ status: "ok" });
});

const shutdown = async (signal: string) => {
  app.log.info({ signal }, "shutdown iniciado");
  try {
    await app.close();
    process.exit(0);
  } catch (err) {
    app.log.error({ err }, "erro durante shutdown");
    process.exit(1);
  }
};

process.on("SIGINT", () => void shutdown("SIGINT"));
process.on("SIGTERM", () => void shutdown("SIGTERM"));

try {
  await app.listen({ host: env.HOST, port: env.PORT });
  app.log.info({ host: env.HOST, port: env.PORT }, "apps/api up");
} catch (err) {
  app.log.error({ err }, "falha ao subir apps/api");
  process.exit(1);
}
