import { z } from "zod";

import { emissionWorkspaceScenarioIdSchema } from "./emission-workspace.js";
import { emissionDryRunScenarioIdSchema } from "./emission-dry-run.js";
import { reviewSignatureScenarioIdSchema } from "./review-signature.js";
import { signatureQueueScenarioIdSchema } from "./signature-queue.js";

export const serviceOrderReviewStatusSchema = z.enum(["ready", "attention", "blocked"]);
export type ServiceOrderReviewStatus = z.infer<typeof serviceOrderReviewStatusSchema>;

export const serviceOrderListItemStatusSchema = z.enum([
  "in_execution",
  "awaiting_review",
  "awaiting_signature",
  "emitted",
  "blocked",
]);
export type ServiceOrderListItemStatus = z.infer<typeof serviceOrderListItemStatusSchema>;

export const serviceOrderTimelineStepKeySchema = z.enum([
  "created",
  "accepted",
  "in_execution",
  "executed",
  "review",
  "signature",
  "emitted",
]);
export type ServiceOrderTimelineStepKey = z.infer<typeof serviceOrderTimelineStepKeySchema>;

export const serviceOrderTimelineStepStatusSchema = z.enum(["complete", "current", "pending"]);
export type ServiceOrderTimelineStepStatus = z.infer<typeof serviceOrderTimelineStepStatusSchema>;

export const serviceOrderReviewChecklistStatusSchema = z.enum(["passed", "pending", "failed"]);
export type ServiceOrderReviewChecklistStatus = z.infer<typeof serviceOrderReviewChecklistStatusSchema>;

export const serviceOrderReviewActionSchema = z.enum([
  "return_to_technician",
  "approve_review",
  "open_preview",
  "open_signature_queue",
]);
export type ServiceOrderReviewAction = z.infer<typeof serviceOrderReviewActionSchema>;

export const serviceOrderListItemSchema = z.object({
  itemId: z.string().min(1),
  workOrderNumber: z.string().min(1),
  customerName: z.string().min(1),
  equipmentLabel: z.string().min(1),
  status: serviceOrderListItemStatusSchema,
  technicianName: z.string().min(1),
  updatedAtLabel: z.string().min(1),
});
export type ServiceOrderListItem = z.infer<typeof serviceOrderListItemSchema>;

export const serviceOrderTimelineStepSchema = z.object({
  key: serviceOrderTimelineStepKeySchema,
  label: z.string().min(1),
  status: serviceOrderTimelineStepStatusSchema,
  timestampLabel: z.string().min(1),
});
export type ServiceOrderTimelineStep = z.infer<typeof serviceOrderTimelineStepSchema>;

export const serviceOrderExecutionMetricSchema = z.object({
  label: z.string().min(1),
  value: z.string().min(1),
  tone: z.enum(["ok", "warn", "neutral"]),
});
export type ServiceOrderExecutionMetric = z.infer<typeof serviceOrderExecutionMetricSchema>;

export const serviceOrderReviewChecklistItemSchema = z.object({
  label: z.string().min(1),
  status: serviceOrderReviewChecklistStatusSchema,
  detail: z.string().min(1),
});
export type ServiceOrderReviewChecklistItem = z.infer<typeof serviceOrderReviewChecklistItemSchema>;

export const serviceOrderReviewLinksSchema = z.object({
  workspaceScenarioId: emissionWorkspaceScenarioIdSchema,
  previewScenarioId: emissionDryRunScenarioIdSchema.optional(),
  reviewSignatureScenarioId: reviewSignatureScenarioIdSchema.optional(),
  signatureQueueScenarioId: signatureQueueScenarioIdSchema.optional(),
});
export type ServiceOrderReviewLinks = z.infer<typeof serviceOrderReviewLinksSchema>;

export const serviceOrderReviewDetailSchema = z.object({
  itemId: z.string().min(1),
  customerId: z.string().min(1).optional(),
  equipmentId: z.string().min(1).optional(),
  procedureId: z.string().min(1).optional(),
  primaryStandardId: z.string().min(1).optional(),
  executorUserId: z.string().min(1).optional(),
  reviewerUserId: z.string().min(1).optional(),
  signatoryUserId: z.string().min(1).optional(),
  title: z.string().min(1),
  status: serviceOrderReviewStatusSchema,
  statusLine: z.string().min(1),
  executorLabel: z.string().min(1),
  assignedReviewerLabel: z.string().min(1),
  assignedSignatoryLabel: z.string().min(1).optional(),
  procedureLabel: z.string().min(1),
  standardsLabel: z.string().min(1),
  environmentLabel: z.string().min(1),
  curvePointsLabel: z.string().min(1),
  evidenceLabel: z.string().min(1),
  uncertaintyLabel: z.string().min(1),
  conformityLabel: z.string().min(1),
  measurementResultValue: z.number().finite().optional(),
  measurementExpandedUncertaintyValue: z.number().finite().optional(),
  measurementCoverageFactor: z.number().finite().optional(),
  measurementUnit: z.string().min(1).optional(),
  decisionRuleLabel: z.string().min(1).optional(),
  decisionOutcomeLabel: z.string().min(1).optional(),
  freeTextStatement: z.string().min(1).optional(),
  reviewDecision: z.enum(["pending", "approved", "rejected"]).optional(),
  certificateNumber: z.string().min(1).optional(),
  documentHash: z.string().min(1).optional(),
  timeline: z.array(serviceOrderTimelineStepSchema).min(1),
  metrics: z.array(serviceOrderExecutionMetricSchema).min(1),
  checklist: z.array(serviceOrderReviewChecklistItemSchema).min(1),
  commentDraft: z.string(),
  allowedActions: z.array(serviceOrderReviewActionSchema),
  blockers: z.array(z.string().min(1)),
  warnings: z.array(z.string().min(1)),
  links: serviceOrderReviewLinksSchema,
});
export type ServiceOrderReviewDetail = z.infer<typeof serviceOrderReviewDetailSchema>;

export const serviceOrderReviewSummarySchema = z.object({
  status: serviceOrderReviewStatusSchema,
  headline: z.string().min(1),
  totalCount: z.number().int().nonnegative(),
  awaitingReviewCount: z.number().int().nonnegative(),
  awaitingSignatureCount: z.number().int().nonnegative(),
  inExecutionCount: z.number().int().nonnegative(),
  emittedCount: z.number().int().nonnegative(),
  blockedCount: z.number().int().nonnegative(),
  recommendedAction: z.string().min(1),
  blockers: z.array(z.string().min(1)),
  warnings: z.array(z.string().min(1)),
});
export type ServiceOrderReviewSummary = z.infer<typeof serviceOrderReviewSummarySchema>;

export const serviceOrderReviewScenarioIdSchema = z.enum([
  "review-ready",
  "history-pending",
  "review-blocked",
]);
export type ServiceOrderReviewScenarioId = z.infer<typeof serviceOrderReviewScenarioIdSchema>;

export const serviceOrderReviewScenarioSchema = z.object({
  id: serviceOrderReviewScenarioIdSchema,
  label: z.string().min(1),
  description: z.string().min(1),
  summary: serviceOrderReviewSummarySchema,
  selectedItemId: z.string().min(1),
  items: z.array(serviceOrderListItemSchema).min(1),
  detail: serviceOrderReviewDetailSchema,
});
export type ServiceOrderReviewScenario = z.infer<typeof serviceOrderReviewScenarioSchema>;

export const serviceOrderReviewCatalogSchema = z.object({
  selectedScenarioId: serviceOrderReviewScenarioIdSchema,
  scenarios: z.array(serviceOrderReviewScenarioSchema).min(1),
});
export type ServiceOrderReviewCatalog = z.infer<typeof serviceOrderReviewCatalogSchema>;
