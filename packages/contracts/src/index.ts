import { router } from "./trpc.js";
import { healthRouter } from "./routers/health.js";

export const appRouter = router({
  health: healthRouter,
});

export type AppRouter = typeof appRouter;

export { createCallerFactory, type AppContext } from "./trpc.js";
export { HealthStatus } from "./routers/health.js";
export * from "./emission-workspace.js";
export * from "./emission-dry-run.js";
export * from "./mobile-offline-calibration.js";
export * from "./onboarding.js";
export * from "./public-certificate.js";
export * from "./review-signature.js";
export * from "./self-signup.js";
export * from "./user-directory.js";
