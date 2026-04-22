import { z } from "zod";

import { complaintRegistryScenarioIdSchema } from "./complaint-registry.js";
import { nonconformityRegistryScenarioIdSchema } from "./nonconformity-registry.js";
import { registryOperationalStatusSchema } from "./registry-shared.js";
import { riskRegisterScenarioIdSchema } from "./risk-register.js";

export const qualityIndicatorScenarioIdSchema = z.enum([
  "baseline-ready",
  "action-sla-attention",
  "critical-drift",
]);
export type QualityIndicatorScenarioId = z.infer<typeof qualityIndicatorScenarioIdSchema>;

export const qualityIndicatorSnapshotSchema = z.object({
  monthLabel: z.string().min(1),
  valueLabel: z.string().min(1),
  status: registryOperationalStatusSchema,
});
export type QualityIndicatorSnapshot = z.infer<typeof qualityIndicatorSnapshotSchema>;

export const qualityIndicatorCardSchema = z.object({
  indicatorId: z.string().min(1),
  title: z.string().min(1),
  currentLabel: z.string().min(1),
  targetLabel: z.string().min(1),
  trendLabel: z.string().min(1),
  ownerLabel: z.string().min(1),
  cadenceLabel: z.string().min(1),
  status: registryOperationalStatusSchema,
});
export type QualityIndicatorCard = z.infer<typeof qualityIndicatorCardSchema>;

export const qualityIndicatorDetailLinksSchema = z.object({
  complaintScenarioId: complaintRegistryScenarioIdSchema.optional(),
  complaintId: z.string().min(1).optional(),
  nonconformityScenarioId: nonconformityRegistryScenarioIdSchema.optional(),
  nonconformityId: z.string().min(1).optional(),
  riskRegisterScenarioId: riskRegisterScenarioIdSchema.optional(),
  riskId: z.string().min(1).optional(),
});
export type QualityIndicatorDetailLinks = z.infer<typeof qualityIndicatorDetailLinksSchema>;

export const qualityIndicatorDetailSchema = z.object({
  indicatorId: z.string().min(1),
  title: z.string().min(1),
  status: registryOperationalStatusSchema,
  noticeLabel: z.string().min(1),
  currentLabel: z.string().min(1),
  targetLabel: z.string().min(1),
  trendLabel: z.string().min(1),
  ownerLabel: z.string().min(1),
  cadenceLabel: z.string().min(1),
  periodLabel: z.string().min(1),
  measurementDefinitionLabel: z.string().min(1),
  evidenceLabel: z.string().min(1),
  managementReviewLabel: z.string().min(1),
  snapshots: z.array(qualityIndicatorSnapshotSchema).min(1),
  relatedArtifacts: z.array(z.string().min(1)).min(1),
  blockers: z.array(z.string().min(1)),
  warnings: z.array(z.string().min(1)),
  links: qualityIndicatorDetailLinksSchema,
});
export type QualityIndicatorDetail = z.infer<typeof qualityIndicatorDetailSchema>;

export const qualityIndicatorRegistrySummarySchema = z.object({
  status: registryOperationalStatusSchema,
  headline: z.string().min(1),
  monthlyWindowLabel: z.string().min(1),
  indicatorCount: z.number().int().nonnegative(),
  attentionCount: z.number().int().nonnegative(),
  blockedCount: z.number().int().nonnegative(),
  recommendedAction: z.string().min(1),
  blockers: z.array(z.string().min(1)),
  warnings: z.array(z.string().min(1)),
});
export type QualityIndicatorRegistrySummary = z.infer<
  typeof qualityIndicatorRegistrySummarySchema
>;

export const qualityIndicatorRegistryScenarioSchema = z.object({
  id: qualityIndicatorScenarioIdSchema,
  label: z.string().min(1),
  description: z.string().min(1),
  summary: qualityIndicatorRegistrySummarySchema,
  selectedIndicatorId: z.string().min(1),
  indicators: z.array(qualityIndicatorCardSchema).min(1),
  detail: qualityIndicatorDetailSchema,
});
export type QualityIndicatorRegistryScenario = z.infer<
  typeof qualityIndicatorRegistryScenarioSchema
>;

export const qualityIndicatorRegistryCatalogSchema = z.object({
  selectedScenarioId: qualityIndicatorScenarioIdSchema,
  scenarios: z.array(qualityIndicatorRegistryScenarioSchema).min(1),
});
export type QualityIndicatorRegistryCatalog = z.infer<
  typeof qualityIndicatorRegistryCatalogSchema
>;
