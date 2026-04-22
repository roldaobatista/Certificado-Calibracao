import { router } from "./trpc.js";
import { healthRouter } from "./routers/health.js";

export const appRouter = router({
  health: healthRouter,
});

export type AppRouter = typeof appRouter;

export { createCallerFactory, type AppContext } from "./trpc.js";
export * from "./audit-trail.js";
export * from "./certificate-preview.js";
export * from "./customer-registry.js";
export * from "./equipment-registry.js";
export { HealthStatus } from "./routers/health.js";
export * from "./emission-workspace.js";
export * from "./emission-dry-run.js";
export * from "./mobile-offline-calibration.js";
export * from "./offline-sync.js";
export * from "./nonconformity-registry.js";
export * from "./onboarding.js";
export * from "./organization-settings.js";
export * from "./portal-dashboard.js";
export * from "./portal-certificate.js";
export * from "./portal-equipment.js";
export * from "./procedure-registry.js";
export * from "./public-certificate.js";
export * from "./registry-shared.js";
export * from "./review-signature.js";
export * from "./service-order-review.js";
export * from "./self-signup.js";
export * from "./signature-queue.js";
export * from "./standard-registry.js";
export * from "./user-directory.js";
