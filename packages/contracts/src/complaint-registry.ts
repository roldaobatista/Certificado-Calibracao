import { z } from "zod";

import { auditTrailScenarioIdSchema } from "./audit-trail.js";
import { emissionWorkspaceScenarioIdSchema } from "./emission-workspace.js";
import { nonconformityRegistryScenarioIdSchema } from "./nonconformity-registry.js";
import { registryOperationalStatusSchema } from "./registry-shared.js";
import { serviceOrderReviewScenarioIdSchema } from "./service-order-review.js";

export const complaintRegistryScenarioIdSchema = z.enum([
  "open-follow-up",
  "critical-response",
  "resolved-history",
]);
export type ComplaintRegistryScenarioId = z.infer<typeof complaintRegistryScenarioIdSchema>;

export const complaintActionStatusSchema = z.enum(["complete", "pending", "blocked"]);
export type ComplaintActionStatus = z.infer<typeof complaintActionStatusSchema>;

export const complaintActionSchema = z.object({
  key: z.string().min(1),
  label: z.string().min(1),
  status: complaintActionStatusSchema,
  detail: z.string().min(1),
});
export type ComplaintAction = z.infer<typeof complaintActionSchema>;

export const complaintListItemSchema = z.object({
  complaintId: z.string().min(1),
  customerName: z.string().min(1),
  summary: z.string().min(1),
  channelLabel: z.string().min(1),
  severityLabel: z.string().min(1),
  ownerLabel: z.string().min(1),
  receivedAtLabel: z.string().min(1),
  status: registryOperationalStatusSchema,
});
export type ComplaintListItem = z.infer<typeof complaintListItemSchema>;

export const complaintDetailLinksSchema = z.object({
  workspaceScenarioId: emissionWorkspaceScenarioIdSchema.optional(),
  auditTrailScenarioId: auditTrailScenarioIdSchema.optional(),
  nonconformityScenarioId: nonconformityRegistryScenarioIdSchema.optional(),
  nonconformityId: z.string().min(1).optional(),
  serviceOrderScenarioId: serviceOrderReviewScenarioIdSchema.optional(),
  reviewItemId: z.string().min(1).optional(),
});
export type ComplaintDetailLinks = z.infer<typeof complaintDetailLinksSchema>;

export const complaintDetailSchema = z.object({
  complaintId: z.string().min(1),
  title: z.string().min(1),
  status: registryOperationalStatusSchema,
  noticeLabel: z.string().min(1),
  customerName: z.string().min(1),
  channelLabel: z.string().min(1),
  ownerLabel: z.string().min(1),
  receivedAtLabel: z.string().min(1),
  responseDeadlineLabel: z.string().min(1),
  narrative: z.string().min(1),
  linkedNonconformityLabel: z.string().min(1),
  reissueReasonLabel: z.string().min(1).optional(),
  evidenceLabel: z.string().min(1),
  actions: z.array(complaintActionSchema).min(1),
  blockers: z.array(z.string().min(1)),
  warnings: z.array(z.string().min(1)),
  links: complaintDetailLinksSchema,
});
export type ComplaintDetail = z.infer<typeof complaintDetailSchema>;

export const complaintRegistrySummarySchema = z.object({
  status: registryOperationalStatusSchema,
  headline: z.string().min(1),
  openCount: z.number().int().nonnegative(),
  overdueCount: z.number().int().nonnegative(),
  reissuePendingCount: z.number().int().nonnegative(),
  resolvedLast30d: z.number().int().nonnegative(),
  recommendedAction: z.string().min(1),
  blockers: z.array(z.string().min(1)),
  warnings: z.array(z.string().min(1)),
});
export type ComplaintRegistrySummary = z.infer<typeof complaintRegistrySummarySchema>;

export const complaintRegistryScenarioSchema = z.object({
  id: complaintRegistryScenarioIdSchema,
  label: z.string().min(1),
  description: z.string().min(1),
  summary: complaintRegistrySummarySchema,
  selectedComplaintId: z.string().min(1),
  items: z.array(complaintListItemSchema).min(1),
  detail: complaintDetailSchema,
});
export type ComplaintRegistryScenario = z.infer<typeof complaintRegistryScenarioSchema>;

export const complaintRegistryCatalogSchema = z.object({
  selectedScenarioId: complaintRegistryScenarioIdSchema,
  scenarios: z.array(complaintRegistryScenarioSchema).min(1),
});
export type ComplaintRegistryCatalog = z.infer<typeof complaintRegistryCatalogSchema>;
