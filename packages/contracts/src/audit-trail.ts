import { z } from "zod";

import { emissionDryRunScenarioIdSchema } from "./emission-dry-run.js";
import { emissionWorkspaceScenarioIdSchema } from "./emission-workspace.js";
import { publicCertificateScenarioIdSchema } from "./public-certificate.js";
import { registryOperationalStatusSchema } from "./registry-shared.js";
import { serviceOrderReviewScenarioIdSchema } from "./service-order-review.js";

export const auditTrailScenarioIdSchema = z.enum([
  "recent-emission",
  "reissue-attention",
  "integrity-blocked",
]);
export type AuditTrailScenarioId = z.infer<typeof auditTrailScenarioIdSchema>;

export const auditTrailEventItemSchema = z.object({
  eventId: z.string().min(1),
  occurredAtLabel: z.string().min(1),
  actorLabel: z.string().min(1),
  actionLabel: z.string().min(1),
  entityLabel: z.string().min(1),
  hashLabel: z.string().min(1),
  status: registryOperationalStatusSchema,
});
export type AuditTrailEventItem = z.infer<typeof auditTrailEventItemSchema>;

export const auditTrailDetailLinksSchema = z.object({
  workspaceScenarioId: emissionWorkspaceScenarioIdSchema.optional(),
  serviceOrderScenarioId: serviceOrderReviewScenarioIdSchema.optional(),
  reviewItemId: z.string().min(1).optional(),
  dryRunScenarioId: emissionDryRunScenarioIdSchema.optional(),
  publicCertificateScenarioId: publicCertificateScenarioIdSchema.optional(),
});
export type AuditTrailDetailLinks = z.infer<typeof auditTrailDetailLinksSchema>;

export const auditTrailDetailSchema = z.object({
  chainId: z.string().min(1),
  title: z.string().min(1),
  status: registryOperationalStatusSchema,
  noticeLabel: z.string().min(1),
  selectedWindowLabel: z.string().min(1),
  selectedActorLabel: z.string().min(1),
  selectedEntityLabel: z.string().min(1),
  selectedActionLabel: z.string().min(1),
  chainStatusLabel: z.string().min(1),
  exportLabel: z.string().min(1),
  coveredActions: z.array(z.string().min(1)).min(1),
  missingActions: z.array(z.string().min(1)),
  blockers: z.array(z.string().min(1)),
  warnings: z.array(z.string().min(1)),
  links: auditTrailDetailLinksSchema,
});
export type AuditTrailDetail = z.infer<typeof auditTrailDetailSchema>;

export const auditTrailSummarySchema = z.object({
  status: registryOperationalStatusSchema,
  headline: z.string().min(1),
  totalEvents: z.number().int().nonnegative(),
  criticalEvents: z.number().int().nonnegative(),
  reissueEvents: z.number().int().nonnegative(),
  integrityFailures: z.number().int().nonnegative(),
  recommendedAction: z.string().min(1),
  blockers: z.array(z.string().min(1)),
  warnings: z.array(z.string().min(1)),
});
export type AuditTrailSummary = z.infer<typeof auditTrailSummarySchema>;

export const auditTrailScenarioSchema = z.object({
  id: auditTrailScenarioIdSchema,
  label: z.string().min(1),
  description: z.string().min(1),
  summary: auditTrailSummarySchema,
  selectedEventId: z.string().min(1),
  items: z.array(auditTrailEventItemSchema).min(1),
  detail: auditTrailDetailSchema,
});
export type AuditTrailScenario = z.infer<typeof auditTrailScenarioSchema>;

export const auditTrailCatalogSchema = z.object({
  selectedScenarioId: auditTrailScenarioIdSchema,
  scenarios: z.array(auditTrailScenarioSchema).min(1),
});
export type AuditTrailCatalog = z.infer<typeof auditTrailCatalogSchema>;
