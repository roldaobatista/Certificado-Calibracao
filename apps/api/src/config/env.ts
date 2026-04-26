import { z } from "zod";

const EnvSchema = z.object({
  NODE_ENV: z.enum(["development", "test", "production"]).default("development"),
  LOG_LEVEL: z.enum(["trace", "debug", "info", "warn", "error", "fatal"]).default("info"),
  HOST: z.string().default("0.0.0.0"),
  PORT: z.coerce.number().int().positive().default(3000),
  CORS_ORIGINS: z
    .string()
    .default("")
    .transform((s) => s.split(",").map((o) => o.trim()).filter(Boolean)),
  DATABASE_URL: z.string().url(),
  DATABASE_APP_URL: z.string().url().optional(),
  DATABASE_OWNER_URL: z.string().url().optional(),
  REDIS_URL: z.string().url(),
  ALLOW_SCENARIO_ROUTES: z
    .enum(["true", "false"])
    .default("false")
    .transform((v) => v === "true"),
  RATE_LIMIT_MAX: z.coerce.number().int().positive().default(100),
  RATE_LIMIT_WINDOW_MS: z.coerce.number().int().positive().default(60000),
  COOKIE_SECRET: z.string().min(32),
  REDIRECT_ALLOWLIST: z
    .string()
    .default("/auth/login,/auth/logout,/onboarding,/emission/workspace,/emission/review-signature,/emission/signature-queue,/dashboard")
    .transform((s) => s.split(",").map((o) => o.trim()).filter(Boolean)),
  BOOTSTRAP_ENABLED: z
    .enum(["true", "false"])
    .default("false")
    .transform((v) => v === "true"),
});

export type Env = z.infer<typeof EnvSchema>;

export function loadEnv(source: NodeJS.ProcessEnv = process.env): Env {
  const parsed = EnvSchema.safeParse(source);
  if (!parsed.success) {
    console.error(
      "[env] Variáveis de ambiente inválidas — fail-closed, abortando:",
      parsed.error.flatten().fieldErrors,
    );
    process.exit(1);
  }

  const data = parsed.data;

  if (data.NODE_ENV === "production") {
    const productionErrors: string[] = [];
    if (!data.COOKIE_SECRET || data.COOKIE_SECRET.length < 32) {
      productionErrors.push("COOKIE_SECRET deve ter pelo menos 32 caracteres em produção");
    }
    if (!data.DATABASE_APP_URL) {
      productionErrors.push("DATABASE_APP_URL é obrigatória em produção");
    }
    if (!data.DATABASE_OWNER_URL) {
      productionErrors.push("DATABASE_OWNER_URL é obrigatória em produção");
    }
    if (productionErrors.length > 0) {
      console.error(
        "[env] Configuração de produção inválida — fail-closed, abortando:",
        productionErrors,
      );
      process.exit(1);
    }
  }

  return data;
}
