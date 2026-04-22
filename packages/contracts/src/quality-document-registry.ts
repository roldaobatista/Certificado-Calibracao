import { z } from "zod";

import { organizationSettingsScenarioIdSchema } from "./organization-settings.js";
import { procedureRegistryScenarioIdSchema } from "./procedure-registry.js";
import { registryOperationalStatusSchema } from "./registry-shared.js";
import { riskRegisterScenarioIdSchema } from "./risk-register.js";

export const qualityDocumentRegistryScenarioIdSchema = z.enum([
  "operational-ready",
  "revision-attention",
  "obsolete-blocked",
]);
export type QualityDocumentRegistryScenarioId = z.infer<
  typeof qualityDocumentRegistryScenarioIdSchema
>;

export const qualityDocumentListItemSchema = z.object({
  documentId: z.string().min(1),
  code: z.string().min(1),
  title: z.string().min(1),
  categoryLabel: z.string().min(1),
  revisionLabel: z.string().min(1),
  effectiveSinceLabel: z.string().min(1),
  effectiveUntilLabel: z.string().min(1).optional(),
  lifecycleLabel: z.string().min(1),
  ownerLabel: z.string().min(1),
  status: registryOperationalStatusSchema,
});
export type QualityDocumentListItem = z.infer<typeof qualityDocumentListItemSchema>;

export const qualityDocumentDetailLinksSchema = z.object({
  organizationSettingsScenarioId: organizationSettingsScenarioIdSchema.optional(),
  procedureScenarioId: procedureRegistryScenarioIdSchema.optional(),
  procedureId: z.string().min(1).optional(),
  riskRegisterScenarioId: riskRegisterScenarioIdSchema.optional(),
  riskId: z.string().min(1).optional(),
});
export type QualityDocumentDetailLinks = z.infer<
  typeof qualityDocumentDetailLinksSchema
>;

export const qualityDocumentDetailSchema = z.object({
  documentId: z.string().min(1),
  title: z.string().min(1),
  status: registryOperationalStatusSchema,
  noticeLabel: z.string().min(1),
  categoryLabel: z.string().min(1),
  ownerLabel: z.string().min(1),
  approvalLabel: z.string().min(1),
  scopeLabel: z.string().min(1),
  distributionLabel: z.string().min(1),
  revisionPolicyLabel: z.string().min(1),
  evidenceLabel: z.string().min(1),
  relatedArtifacts: z.array(z.string().min(1)).min(1),
  blockers: z.array(z.string().min(1)),
  warnings: z.array(z.string().min(1)),
  links: qualityDocumentDetailLinksSchema,
});
export type QualityDocumentDetail = z.infer<typeof qualityDocumentDetailSchema>;

export const qualityDocumentRegistrySummarySchema = z.object({
  status: registryOperationalStatusSchema,
  headline: z.string().min(1),
  activeCount: z.number().int().nonnegative(),
  attentionCount: z.number().int().nonnegative(),
  obsoleteCount: z.number().int().nonnegative(),
  recommendedAction: z.string().min(1),
  blockers: z.array(z.string().min(1)),
  warnings: z.array(z.string().min(1)),
});
export type QualityDocumentRegistrySummary = z.infer<
  typeof qualityDocumentRegistrySummarySchema
>;

export const qualityDocumentRegistryScenarioSchema = z.object({
  id: qualityDocumentRegistryScenarioIdSchema,
  label: z.string().min(1),
  description: z.string().min(1),
  summary: qualityDocumentRegistrySummarySchema,
  selectedDocumentId: z.string().min(1),
  items: z.array(qualityDocumentListItemSchema).min(1),
  detail: qualityDocumentDetailSchema,
});
export type QualityDocumentRegistryScenario = z.infer<
  typeof qualityDocumentRegistryScenarioSchema
>;

export const qualityDocumentRegistryCatalogSchema = z.object({
  selectedScenarioId: qualityDocumentRegistryScenarioIdSchema,
  scenarios: z.array(qualityDocumentRegistryScenarioSchema).min(1),
});
export type QualityDocumentRegistryCatalog = z.infer<
  typeof qualityDocumentRegistryCatalogSchema
>;
