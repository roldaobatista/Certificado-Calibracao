import { z } from "zod";
import { publicProcedure, router } from "../trpc.js";

export const HealthStatus = z.object({
  status: z.enum(["ok", "degraded", "down"]),
  version: z.string(),
  ts: z.string().datetime(),
});
export type HealthStatus = z.infer<typeof HealthStatus>;

export const healthRouter = router({
  ping: publicProcedure.output(HealthStatus).query(() => ({
    status: "ok" as const,
    version: "0.0.1",
    ts: new Date().toISOString(),
  })),
});
