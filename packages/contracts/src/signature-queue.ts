import { z } from "zod";

import { certificatePreviewFieldSchema } from "./certificate-preview.js";
import { emissionDryRunScenarioIdSchema } from "./emission-dry-run.js";
import { reviewSignatureScenarioIdSchema } from "./review-signature.js";

export const signatureQueueStatusSchema = z.enum(["ready", "attention", "blocked"]);
export type SignatureQueueStatus = z.infer<typeof signatureQueueStatusSchema>;

export const signatureQueueValidationStatusSchema = z.enum(["passed", "warning", "failed"]);
export type SignatureQueueValidationStatus = z.infer<typeof signatureQueueValidationStatusSchema>;

export const signatureQueueValidationSchema = z.object({
  label: z.string().min(1),
  status: signatureQueueValidationStatusSchema,
  detail: z.string().min(1),
});
export type SignatureQueueValidation = z.infer<typeof signatureQueueValidationSchema>;

export const signatureQueueItemSchema = z.object({
  itemId: z.string().min(1),
  workOrderNumber: z.string().min(1),
  customerName: z.string().min(1),
  equipmentLabel: z.string().min(1),
  instrumentType: z.string().min(1),
  waitingSinceLabel: z.string().min(1),
  certificateNumber: z.string().min(1).optional(),
  status: signatureQueueStatusSchema,
  previewScenarioId: emissionDryRunScenarioIdSchema,
  reviewSignatureScenarioId: reviewSignatureScenarioIdSchema,
  validations: z.array(signatureQueueValidationSchema).min(1),
  blockers: z.array(z.string().min(1)),
  warnings: z.array(z.string().min(1)),
});
export type SignatureQueueItem = z.infer<typeof signatureQueueItemSchema>;

export const signatureQueueSummarySchema = z.object({
  status: signatureQueueStatusSchema,
  headline: z.string().min(1),
  pendingCount: z.number().int().nonnegative(),
  readyCount: z.number().int().nonnegative(),
  attentionCount: z.number().int().nonnegative(),
  blockedCount: z.number().int().nonnegative(),
  batchReadyCount: z.number().int().nonnegative(),
  oldestPendingLabel: z.string().min(1),
  recommendedAction: z.string().min(1),
  blockers: z.array(z.string().min(1)),
  warnings: z.array(z.string().min(1)),
});
export type SignatureQueueSummary = z.infer<typeof signatureQueueSummarySchema>;

export const signatureApprovalFactorSchema = z.enum(["password", "totp"]);
export type SignatureApprovalFactor = z.infer<typeof signatureApprovalFactorSchema>;

export const signatureApprovalFactorStatusSchema = z.enum(["configured", "missing"]);
export type SignatureApprovalFactorStatus = z.infer<typeof signatureApprovalFactorStatusSchema>;

export const signatureApprovalRequirementSchema = z.object({
  factor: signatureApprovalFactorSchema,
  label: z.string().min(1),
  status: signatureApprovalFactorStatusSchema,
  detail: z.string().min(1),
});
export type SignatureApprovalRequirement = z.infer<typeof signatureApprovalRequirementSchema>;

export const signatureApprovalPanelSchema = z.object({
  itemId: z.string().min(1),
  title: z.string().min(1),
  status: signatureQueueStatusSchema,
  signatoryDisplayName: z.string().min(1),
  authorizationLabel: z.string().min(1),
  statement: z.string().min(1),
  documentHash: z.string().min(1),
  canSign: z.boolean(),
  actionLabel: z.string().min(1),
  blockers: z.array(z.string().min(1)),
  warnings: z.array(z.string().min(1)),
  authRequirements: z.array(signatureApprovalRequirementSchema).min(1),
  compactPreview: z.array(certificatePreviewFieldSchema).min(1),
});
export type SignatureApprovalPanel = z.infer<typeof signatureApprovalPanelSchema>;

export const signatureQueueScenarioIdSchema = z.enum([
  "approved-ready",
  "attention-required",
  "mfa-blocked",
]);
export type SignatureQueueScenarioId = z.infer<typeof signatureQueueScenarioIdSchema>;

export const signatureQueueScenarioSchema = z.object({
  id: signatureQueueScenarioIdSchema,
  label: z.string().min(1),
  description: z.string().min(1),
  summary: signatureQueueSummarySchema,
  selectedItemId: z.string().min(1),
  items: z.array(signatureQueueItemSchema).min(1),
  approval: signatureApprovalPanelSchema,
});
export type SignatureQueueScenario = z.infer<typeof signatureQueueScenarioSchema>;

export const signatureQueueCatalogSchema = z.object({
  selectedScenarioId: signatureQueueScenarioIdSchema,
  scenarios: z.array(signatureQueueScenarioSchema).min(1),
});
export type SignatureQueueCatalog = z.infer<typeof signatureQueueCatalogSchema>;
