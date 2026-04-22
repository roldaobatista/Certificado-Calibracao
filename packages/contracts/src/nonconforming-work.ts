import { z } from "zod";

import { auditTrailScenarioIdSchema } from "./audit-trail.js";
import { complaintRegistryScenarioIdSchema } from "./complaint-registry.js";
import { emissionWorkspaceScenarioIdSchema } from "./emission-workspace.js";
import { nonconformityRegistryScenarioIdSchema } from "./nonconformity-registry.js";
import { procedureRegistryScenarioIdSchema } from "./procedure-registry.js";
import { qualityDocumentRegistryScenarioIdSchema } from "./quality-document-registry.js";
import { registryOperationalStatusSchema } from "./registry-shared.js";
import { serviceOrderReviewScenarioIdSchema } from "./service-order-review.js";

export const nonconformingWorkScenarioIdSchema = z.enum([
  "contained-attention",
  "release-blocked",
  "archived-history",
]);
export type NonconformingWorkScenarioId = z.infer<typeof nonconformingWorkScenarioIdSchema>;

export const nonconformingWorkListItemSchema = z.object({
  caseId: z.string().min(1),
  titleLabel: z.string().min(1),
  affectedEntityLabel: z.string().min(1),
  originLabel: z.string().min(1),
  impactLabel: z.string().min(1),
  status: registryOperationalStatusSchema,
});
export type NonconformingWorkListItem = z.infer<typeof nonconformingWorkListItemSchema>;

export const nonconformingWorkDetailLinksSchema = z.object({
  workspaceScenarioId: emissionWorkspaceScenarioIdSchema.optional(),
  auditTrailScenarioId: auditTrailScenarioIdSchema.optional(),
  nonconformityScenarioId: nonconformityRegistryScenarioIdSchema.optional(),
  complaintScenarioId: complaintRegistryScenarioIdSchema.optional(),
  procedureScenarioId: procedureRegistryScenarioIdSchema.optional(),
  qualityDocumentScenarioId: qualityDocumentRegistryScenarioIdSchema.optional(),
  serviceOrderScenarioId: serviceOrderReviewScenarioIdSchema.optional(),
  reviewItemId: z.string().min(1).optional(),
  complaintId: z.string().min(1).optional(),
  documentId: z.string().min(1).optional(),
});
export type NonconformingWorkDetailLinks = z.infer<typeof nonconformingWorkDetailLinksSchema>;

export const nonconformingWorkDetailSchema = z.object({
  caseId: z.string().min(1),
  title: z.string().min(1),
  status: registryOperationalStatusSchema,
  noticeLabel: z.string().min(1),
  classificationLabel: z.string().min(1),
  originLabel: z.string().min(1),
  affectedEntityLabel: z.string().min(1),
  containmentLabel: z.string().min(1),
  releaseRuleLabel: z.string().min(1),
  evidenceLabel: z.string().min(1),
  restorationLabel: z.string().min(1),
  blockers: z.array(z.string().min(1)),
  warnings: z.array(z.string().min(1)),
  links: nonconformingWorkDetailLinksSchema,
});
export type NonconformingWorkDetail = z.infer<typeof nonconformingWorkDetailSchema>;

export const nonconformingWorkSummarySchema = z.object({
  status: registryOperationalStatusSchema,
  headline: z.string().min(1),
  openCaseCount: z.number().int().nonnegative(),
  blockedReleaseCount: z.number().int().nonnegative(),
  restoredCount: z.number().int().nonnegative(),
  recommendedAction: z.string().min(1),
  blockers: z.array(z.string().min(1)),
  warnings: z.array(z.string().min(1)),
});
export type NonconformingWorkSummary = z.infer<typeof nonconformingWorkSummarySchema>;

export const nonconformingWorkScenarioSchema = z.object({
  id: nonconformingWorkScenarioIdSchema,
  label: z.string().min(1),
  description: z.string().min(1),
  summary: nonconformingWorkSummarySchema,
  selectedCaseId: z.string().min(1),
  items: z.array(nonconformingWorkListItemSchema).min(1),
  detail: nonconformingWorkDetailSchema,
});
export type NonconformingWorkScenario = z.infer<typeof nonconformingWorkScenarioSchema>;

export const nonconformingWorkCatalogSchema = z.object({
  selectedScenarioId: nonconformingWorkScenarioIdSchema,
  scenarios: z.array(nonconformingWorkScenarioSchema).min(1),
});
export type NonconformingWorkCatalog = z.infer<typeof nonconformingWorkCatalogSchema>;
