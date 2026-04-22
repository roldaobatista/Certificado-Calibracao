import { z } from "zod";

import { complaintRegistryScenarioIdSchema } from "./complaint-registry.js";
import { nonconformityRegistryScenarioIdSchema } from "./nonconformity-registry.js";
import { organizationSettingsScenarioIdSchema } from "./organization-settings.js";
import { registryOperationalStatusSchema } from "./registry-shared.js";

export const riskRegisterScenarioIdSchema = z.enum([
  "annual-declarations",
  "commercial-pressure",
  "stable-monitoring",
]);
export type RiskRegisterScenarioId = z.infer<typeof riskRegisterScenarioIdSchema>;

export const riskActionStatusSchema = z.enum(["complete", "pending", "blocked"]);
export type RiskActionStatus = z.infer<typeof riskActionStatusSchema>;

export const riskActionSchema = z.object({
  key: z.string().min(1),
  label: z.string().min(1),
  status: riskActionStatusSchema,
  detail: z.string().min(1),
});
export type RiskAction = z.infer<typeof riskActionSchema>;

export const conflictDeclarationItemSchema = z.object({
  declarationId: z.string().min(1),
  actorName: z.string().min(1),
  dateLabel: z.string().min(1),
  summary: z.string().min(1),
  status: registryOperationalStatusSchema,
  statusLabel: z.string().min(1),
  documentLabel: z.string().min(1),
});
export type ConflictDeclarationItem = z.infer<typeof conflictDeclarationItemSchema>;

export const riskMatrixItemSchema = z.object({
  riskId: z.string().min(1),
  title: z.string().min(1),
  categoryLabel: z.string().min(1),
  probabilityLabel: z.string().min(1),
  impactLabel: z.string().min(1),
  ownerLabel: z.string().min(1),
  status: registryOperationalStatusSchema,
  statusLabel: z.string().min(1),
});
export type RiskMatrixItem = z.infer<typeof riskMatrixItemSchema>;

export const riskDetailLinksSchema = z.object({
  organizationSettingsScenarioId: organizationSettingsScenarioIdSchema.optional(),
  complaintScenarioId: complaintRegistryScenarioIdSchema.optional(),
  complaintId: z.string().min(1).optional(),
  nonconformityScenarioId: nonconformityRegistryScenarioIdSchema.optional(),
  nonconformityId: z.string().min(1).optional(),
});
export type RiskDetailLinks = z.infer<typeof riskDetailLinksSchema>;

export const riskDetailSchema = z.object({
  riskId: z.string().min(1),
  title: z.string().min(1),
  status: registryOperationalStatusSchema,
  noticeLabel: z.string().min(1),
  categoryLabel: z.string().min(1),
  probabilityLabel: z.string().min(1),
  impactLabel: z.string().min(1),
  ownerLabel: z.string().min(1),
  lastReviewedAtLabel: z.string().min(1),
  reviewCadenceLabel: z.string().min(1),
  description: z.string().min(1),
  mitigationPlanLabel: z.string().min(1),
  evidenceLabel: z.string().min(1),
  linkedDeclarationLabel: z.string().min(1),
  managementReviewLabel: z.string().min(1),
  actions: z.array(riskActionSchema).min(1),
  blockers: z.array(z.string().min(1)),
  warnings: z.array(z.string().min(1)),
  links: riskDetailLinksSchema,
});
export type RiskDetail = z.infer<typeof riskDetailSchema>;

export const riskRegisterSummarySchema = z.object({
  status: registryOperationalStatusSchema,
  headline: z.string().min(1),
  declarationCount: z.number().int().nonnegative(),
  pendingDeclarationCount: z.number().int().nonnegative(),
  conflictDeclarationCount: z.number().int().nonnegative(),
  activeRiskCount: z.number().int().nonnegative(),
  highImpactRiskCount: z.number().int().nonnegative(),
  recommendedAction: z.string().min(1),
  blockers: z.array(z.string().min(1)),
  warnings: z.array(z.string().min(1)),
});
export type RiskRegisterSummary = z.infer<typeof riskRegisterSummarySchema>;

export const riskRegisterScenarioSchema = z.object({
  id: riskRegisterScenarioIdSchema,
  label: z.string().min(1),
  description: z.string().min(1),
  summary: riskRegisterSummarySchema,
  selectedRiskId: z.string().min(1),
  declarations: z.array(conflictDeclarationItemSchema).min(1),
  risks: z.array(riskMatrixItemSchema).min(1),
  detail: riskDetailSchema,
});
export type RiskRegisterScenario = z.infer<typeof riskRegisterScenarioSchema>;

export const riskRegisterCatalogSchema = z.object({
  selectedScenarioId: riskRegisterScenarioIdSchema,
  scenarios: z.array(riskRegisterScenarioSchema).min(1),
});
export type RiskRegisterCatalog = z.infer<typeof riskRegisterCatalogSchema>;
