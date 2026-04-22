import { z } from "zod";

import { auditTrailScenarioIdSchema } from "./audit-trail.js";
import { emissionWorkspaceScenarioIdSchema } from "./emission-workspace.js";
import { registryOperationalStatusSchema } from "./registry-shared.js";
import { serviceOrderReviewScenarioIdSchema } from "./service-order-review.js";

export const offlineSyncScenarioIdSchema = z.enum([
  "stable-upload",
  "human-review-open",
  "regulator-escalated",
]);
export type OfflineSyncScenarioId = z.infer<typeof offlineSyncScenarioIdSchema>;

export const offlineSyncConflictClassSchema = z.enum([
  "C1",
  "C2",
  "C3",
  "C4",
  "C5",
  "C6",
  "C7",
  "C8",
]);
export type OfflineSyncConflictClass = z.infer<typeof offlineSyncConflictClassSchema>;

export const offlineSyncConflictStatusSchema = z.enum(["resolved", "open", "escalated"]);
export type OfflineSyncConflictStatus = z.infer<typeof offlineSyncConflictStatusSchema>;

export const offlineSyncEnvelopeStateSchema = z.enum([
  "queued",
  "uploaded",
  "deduplicated",
  "rejected",
]);
export type OfflineSyncEnvelopeState = z.infer<typeof offlineSyncEnvelopeStateSchema>;

export const offlineSyncEventKindSchema = z.enum(["edit", "sign", "reissue", "emit"]);
export type OfflineSyncEventKind = z.infer<typeof offlineSyncEventKindSchema>;

export const offlineSyncDecisionActionSchema = z.enum([
  "accept_server_winner",
  "accept_device_winner",
  "merge_fields",
  "escalate_to_regulator",
  "archive_resolution",
]);
export type OfflineSyncDecisionAction = z.infer<typeof offlineSyncDecisionActionSchema>;

export const offlineSyncEnvelopeSchema = z.object({
  eventId: z.string().min(1),
  clientEventId: z.string().min(1),
  aggregateLabel: z.string().min(1),
  eventKind: offlineSyncEventKindSchema,
  lamport: z.number().int().positive(),
  payloadDigest: z.string().min(1),
  state: offlineSyncEnvelopeStateSchema,
  replayProtected: z.boolean(),
});
export type OfflineSyncEnvelope = z.infer<typeof offlineSyncEnvelopeSchema>;

export const offlineSyncOutboxItemSchema = z.object({
  itemId: z.string().min(1),
  sessionId: z.string().min(1),
  workOrderId: z.string().min(1),
  workOrderNumber: z.string().min(1),
  deviceId: z.string().min(1),
  deviceLabel: z.string().min(1),
  certificateNumber: z.string().min(1),
  status: registryOperationalStatusSchema,
  networkLabel: z.string().min(1),
  storageLabel: z.string().min(1),
  queuedAtLabel: z.string().min(1),
  lastAttemptLabel: z.string().min(1),
  eventCount: z.number().int().positive(),
  replayProtectedCount: z.number().int().nonnegative(),
  nextActionLabel: z.string().min(1),
  pendingConflictClass: offlineSyncConflictClassSchema.optional(),
  blockers: z.array(z.string().min(1)),
  warnings: z.array(z.string().min(1)),
  envelopes: z.array(offlineSyncEnvelopeSchema).min(1),
});
export type OfflineSyncOutboxItem = z.infer<typeof offlineSyncOutboxItemSchema>;

export const offlineSyncConflictQueueItemSchema = z.object({
  conflictId: z.string().min(1),
  workOrderId: z.string().min(1),
  workOrderNumber: z.string().min(1),
  class: offlineSyncConflictClassSchema,
  status: offlineSyncConflictStatusSchema,
  openedAtLabel: z.string().min(1),
  deadlineLabel: z.string().min(1),
  responsibleLabel: z.string().min(1),
  summaryLabel: z.string().min(1),
  recommendedAction: z.string().min(1),
  blockingScopeLabel: z.string().min(1),
});
export type OfflineSyncConflictQueueItem = z.infer<typeof offlineSyncConflictQueueItemSchema>;

export const offlineSyncDecisionOptionSchema = z.object({
  action: offlineSyncDecisionActionSchema,
  label: z.string().min(1),
  detail: z.string().min(1),
  allowed: z.boolean(),
});
export type OfflineSyncDecisionOption = z.infer<typeof offlineSyncDecisionOptionSchema>;

export const offlineSyncDetailLinksSchema = z.object({
  workspaceScenarioId: emissionWorkspaceScenarioIdSchema,
  serviceOrderScenarioId: serviceOrderReviewScenarioIdSchema,
  auditTrailScenarioId: auditTrailScenarioIdSchema,
});
export type OfflineSyncDetailLinks = z.infer<typeof offlineSyncDetailLinksSchema>;

export const offlineSyncConflictDetailSchema = z.object({
  conflictId: z.string().min(1),
  title: z.string().min(1),
  status: offlineSyncConflictStatusSchema,
  class: offlineSyncConflictClassSchema,
  summary: z.string().min(1),
  decisionDeadlineLabel: z.string().min(1),
  responsibleLabel: z.string().min(1),
  queueSlaLabel: z.string().min(1),
  winningEventId: z.string().min(1).optional(),
  losingEventId: z.string().min(1).optional(),
  blockedForEmission: z.boolean(),
  regulatorEscalationRequired: z.boolean(),
  recommendedDecisionLabel: z.string().min(1),
  rationaleTemplate: z.string().min(1),
  resolutionOptions: z.array(offlineSyncDecisionOptionSchema).min(1),
  auditRequirements: z.array(z.string().min(1)).min(1),
  blockers: z.array(z.string().min(1)),
  warnings: z.array(z.string().min(1)),
  links: offlineSyncDetailLinksSchema,
});
export type OfflineSyncConflictDetail = z.infer<typeof offlineSyncConflictDetailSchema>;

export const offlineSyncSummarySchema = z.object({
  status: registryOperationalStatusSchema,
  headline: z.string().min(1),
  queuedDevices: z.number().int().nonnegative(),
  queuedItems: z.number().int().nonnegative(),
  openConflictCount: z.number().int().nonnegative(),
  escalatedConflictCount: z.number().int().nonnegative(),
  blockedWorkOrders: z.number().int().nonnegative(),
  resolvedLast24h: z.number().int().nonnegative(),
  recommendedAction: z.string().min(1),
  blockers: z.array(z.string().min(1)),
  warnings: z.array(z.string().min(1)),
});
export type OfflineSyncSummary = z.infer<typeof offlineSyncSummarySchema>;

export const offlineSyncScenarioSchema = z.object({
  id: offlineSyncScenarioIdSchema,
  label: z.string().min(1),
  description: z.string().min(1),
  summary: offlineSyncSummarySchema,
  selectedOutboxItemId: z.string().min(1),
  selectedConflictId: z.string().min(1),
  outboxItems: z.array(offlineSyncOutboxItemSchema).min(1),
  conflicts: z.array(offlineSyncConflictQueueItemSchema).min(1),
  detail: offlineSyncConflictDetailSchema,
});
export type OfflineSyncScenario = z.infer<typeof offlineSyncScenarioSchema>;

export const offlineSyncCatalogSchema = z.object({
  selectedScenarioId: offlineSyncScenarioIdSchema,
  scenarios: z.array(offlineSyncScenarioSchema).min(1),
});
export type OfflineSyncCatalog = z.infer<typeof offlineSyncCatalogSchema>;
