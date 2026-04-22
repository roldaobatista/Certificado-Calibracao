import { z } from "zod";

import { auditTrailScenarioIdSchema } from "./audit-trail.js";
import { emissionWorkspaceScenarioIdSchema } from "./emission-workspace.js";
import { procedureRegistryScenarioIdSchema } from "./procedure-registry.js";
import { registryOperationalStatusSchema } from "./registry-shared.js";
import { serviceOrderReviewScenarioIdSchema } from "./service-order-review.js";

export const nonconformityRegistryScenarioIdSchema = z.enum([
  "open-attention",
  "critical-response",
  "resolved-history",
]);
export type NonconformityRegistryScenarioId = z.infer<typeof nonconformityRegistryScenarioIdSchema>;

export const nonconformityListItemSchema = z.object({
  ncId: z.string().min(1),
  summary: z.string().min(1),
  originLabel: z.string().min(1),
  severityLabel: z.string().min(1),
  ownerLabel: z.string().min(1),
  ageLabel: z.string().min(1),
  status: registryOperationalStatusSchema,
});
export type NonconformityListItem = z.infer<typeof nonconformityListItemSchema>;

export const nonconformityDetailLinksSchema = z.object({
  workspaceScenarioId: emissionWorkspaceScenarioIdSchema.optional(),
  auditTrailScenarioId: auditTrailScenarioIdSchema.optional(),
  procedureScenarioId: procedureRegistryScenarioIdSchema.optional(),
  serviceOrderScenarioId: serviceOrderReviewScenarioIdSchema.optional(),
  reviewItemId: z.string().min(1).optional(),
});
export type NonconformityDetailLinks = z.infer<typeof nonconformityDetailLinksSchema>;

export const nonconformityDetailSchema = z.object({
  ncId: z.string().min(1),
  title: z.string().min(1),
  status: registryOperationalStatusSchema,
  noticeLabel: z.string().min(1),
  originLabel: z.string().min(1),
  severityLabel: z.string().min(1),
  ownerLabel: z.string().min(1),
  openedAtLabel: z.string().min(1),
  dueAtLabel: z.string().min(1),
  rootCauseLabel: z.string().min(1),
  containmentLabel: z.string().min(1),
  correctiveActionLabel: z.string().min(1),
  evidenceLabel: z.string().min(1),
  blockers: z.array(z.string().min(1)),
  warnings: z.array(z.string().min(1)),
  links: nonconformityDetailLinksSchema,
});
export type NonconformityDetail = z.infer<typeof nonconformityDetailSchema>;

export const nonconformityRegistrySummarySchema = z.object({
  status: registryOperationalStatusSchema,
  headline: z.string().min(1),
  openCount: z.number().int().nonnegative(),
  criticalCount: z.number().int().nonnegative(),
  closedCount: z.number().int().nonnegative(),
  recommendedAction: z.string().min(1),
  blockers: z.array(z.string().min(1)),
  warnings: z.array(z.string().min(1)),
});
export type NonconformityRegistrySummary = z.infer<typeof nonconformityRegistrySummarySchema>;

export const nonconformityRegistryScenarioSchema = z.object({
  id: nonconformityRegistryScenarioIdSchema,
  label: z.string().min(1),
  description: z.string().min(1),
  summary: nonconformityRegistrySummarySchema,
  selectedNcId: z.string().min(1),
  items: z.array(nonconformityListItemSchema).min(1),
  detail: nonconformityDetailSchema,
});
export type NonconformityRegistryScenario = z.infer<typeof nonconformityRegistryScenarioSchema>;

export const nonconformityRegistryCatalogSchema = z.object({
  selectedScenarioId: nonconformityRegistryScenarioIdSchema,
  scenarios: z.array(nonconformityRegistryScenarioSchema).min(1),
});
export type NonconformityRegistryCatalog = z.infer<typeof nonconformityRegistryCatalogSchema>;
