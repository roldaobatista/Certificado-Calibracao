import "dotenv/config";
import { buildApp } from "./app.js";
import { loadEnv } from "./config/env.js";

const env = loadEnv();
const app = await buildApp({ env });

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
