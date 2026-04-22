import { z } from "zod";

import { nonconformityRegistryScenarioIdSchema } from "./nonconformity-registry.js";
import { registryOperationalStatusSchema } from "./registry-shared.js";

export const internalAuditScenarioIdSchema = z.enum([
  "program-on-track",
  "follow-up-attention",
  "extraordinary-escalation",
]);
export type InternalAuditScenarioId = z.infer<typeof internalAuditScenarioIdSchema>;

export const internalAuditCycleListItemSchema = z.object({
  cycleId: z.string().min(1),
  cycleLabel: z.string().min(1),
  windowLabel: z.string().min(1),
  scopeLabel: z.string().min(1),
  auditorLabel: z.string().min(1),
  findingsLabel: z.string().min(1),
  status: registryOperationalStatusSchema,
  statusLabel: z.string().min(1),
});
export type InternalAuditCycleListItem = z.infer<typeof internalAuditCycleListItemSchema>;

export const internalAuditChecklistItemSchema = z.object({
  key: z.string().min(1),
  requirementLabel: z.string().min(1),
  evidenceLabel: z.string().min(1),
  status: registryOperationalStatusSchema,
});
export type InternalAuditChecklistItem = z.infer<typeof internalAuditChecklistItemSchema>;

export const internalAuditFindingItemSchema = z.object({
  findingId: z.string().min(1),
  title: z.string().min(1),
  severityLabel: z.string().min(1),
  ownerLabel: z.string().min(1),
  dueDateLabel: z.string().min(1),
  status: registryOperationalStatusSchema,
  nonconformityId: z.string().min(1).optional(),
});
export type InternalAuditFindingItem = z.infer<typeof internalAuditFindingItemSchema>;

export const internalAuditDetailLinksSchema = z.object({
  nonconformityScenarioId: nonconformityRegistryScenarioIdSchema.optional(),
});
export type InternalAuditDetailLinks = z.infer<typeof internalAuditDetailLinksSchema>;

export const internalAuditDetailSchema = z.object({
  cycleId: z.string().min(1),
  title: z.string().min(1),
  status: registryOperationalStatusSchema,
  noticeLabel: z.string().min(1),
  auditorLabel: z.string().min(1),
  auditeeLabel: z.string().min(1),
  periodLabel: z.string().min(1),
  scopeLabel: z.string().min(1),
  reportLabel: z.string().min(1),
  evidenceLabel: z.string().min(1),
  nextReviewLabel: z.string().min(1),
  checklist: z.array(internalAuditChecklistItemSchema).min(1),
  findings: z.array(internalAuditFindingItemSchema).min(1),
  blockers: z.array(z.string().min(1)),
  warnings: z.array(z.string().min(1)),
  links: internalAuditDetailLinksSchema,
});
export type InternalAuditDetail = z.infer<typeof internalAuditDetailSchema>;

export const internalAuditSummarySchema = z.object({
  status: registryOperationalStatusSchema,
  headline: z.string().min(1),
  programLabel: z.string().min(1),
  plannedCycleCount: z.number().int().nonnegative(),
  completedCycleCount: z.number().int().nonnegative(),
  openFindingCount: z.number().int().nonnegative(),
  recommendedAction: z.string().min(1),
  blockers: z.array(z.string().min(1)),
  warnings: z.array(z.string().min(1)),
});
export type InternalAuditSummary = z.infer<typeof internalAuditSummarySchema>;

export const internalAuditScenarioSchema = z.object({
  id: internalAuditScenarioIdSchema,
  label: z.string().min(1),
  description: z.string().min(1),
  summary: internalAuditSummarySchema,
  selectedCycleId: z.string().min(1),
  cycles: z.array(internalAuditCycleListItemSchema).min(1),
  detail: internalAuditDetailSchema,
});
export type InternalAuditScenario = z.infer<typeof internalAuditScenarioSchema>;

export const internalAuditCatalogSchema = z.object({
  selectedScenarioId: internalAuditScenarioIdSchema,
  scenarios: z.array(internalAuditScenarioSchema).min(1),
});
export type InternalAuditCatalog = z.infer<typeof internalAuditCatalogSchema>;
