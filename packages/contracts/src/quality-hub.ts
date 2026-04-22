import { z } from "zod";

import { auditTrailScenarioIdSchema } from "./audit-trail.js";
import { emissionWorkspaceScenarioIdSchema } from "./emission-workspace.js";
import { nonconformityRegistryScenarioIdSchema } from "./nonconformity-registry.js";
import { organizationSettingsScenarioIdSchema } from "./organization-settings.js";
import { registryOperationalStatusSchema } from "./registry-shared.js";

export const qualityHubScenarioIdSchema = z.enum([
  "operational-attention",
  "critical-response",
  "stable-baseline",
]);
export type QualityHubScenarioId = z.infer<typeof qualityHubScenarioIdSchema>;

export const qualityHubModuleKeySchema = z.enum([
  "nonconformities",
  "audit-trail",
  "complaints",
  "nonconforming-work",
  "internal-audit",
  "management-review",
  "risk-impartiality",
  "documents",
  "indicators",
]);
export type QualityHubModuleKey = z.infer<typeof qualityHubModuleKeySchema>;

export const qualityHubModuleAvailabilitySchema = z.enum(["implemented", "planned"]);
export type QualityHubModuleAvailability = z.infer<typeof qualityHubModuleAvailabilitySchema>;

export const qualityHubLinksSchema = z.object({
  workspaceScenarioId: emissionWorkspaceScenarioIdSchema.optional(),
  organizationSettingsScenarioId: organizationSettingsScenarioIdSchema.optional(),
  auditTrailScenarioId: auditTrailScenarioIdSchema.optional(),
  nonconformityScenarioId: nonconformityRegistryScenarioIdSchema.optional(),
});
export type QualityHubLinks = z.infer<typeof qualityHubLinksSchema>;

export const qualityHubModuleSchema = z.object({
  key: qualityHubModuleKeySchema,
  title: z.string().min(1),
  clauseLabel: z.string().min(1),
  metricLabel: z.string().min(1),
  summary: z.string().min(1),
  status: registryOperationalStatusSchema,
  availability: qualityHubModuleAvailabilitySchema,
  href: z.string().min(1).optional(),
  ctaLabel: z.string().min(1),
  nextStepLabel: z.string().min(1),
  blockers: z.array(z.string().min(1)),
  warnings: z.array(z.string().min(1)),
});
export type QualityHubModule = z.infer<typeof qualityHubModuleSchema>;

export const qualityHubSummarySchema = z.object({
  status: registryOperationalStatusSchema,
  organizationName: z.string().min(1),
  openNonconformities: z.number().int().nonnegative(),
  overdueActions: z.number().int().nonnegative(),
  auditProgramCount: z.number().int().nonnegative(),
  complaintCount: z.number().int().nonnegative(),
  activeRiskCount: z.number().int().nonnegative(),
  implementedModuleCount: z.number().int().nonnegative(),
  plannedModuleCount: z.number().int().nonnegative(),
  nextManagementReviewLabel: z.string().min(1),
  recommendedAction: z.string().min(1),
  blockers: z.array(z.string().min(1)),
  warnings: z.array(z.string().min(1)),
});
export type QualityHubSummary = z.infer<typeof qualityHubSummarySchema>;

export const qualityHubScenarioSchema = z.object({
  id: qualityHubScenarioIdSchema,
  label: z.string().min(1),
  description: z.string().min(1),
  selectedModuleKey: qualityHubModuleKeySchema,
  summary: qualityHubSummarySchema,
  links: qualityHubLinksSchema,
  modules: z.array(qualityHubModuleSchema).min(1),
});
export type QualityHubScenario = z.infer<typeof qualityHubScenarioSchema>;

export const qualityHubCatalogSchema = z.object({
  selectedScenarioId: qualityHubScenarioIdSchema,
  scenarios: z.array(qualityHubScenarioSchema).min(1),
});
export type QualityHubCatalog = z.infer<typeof qualityHubCatalogSchema>;
