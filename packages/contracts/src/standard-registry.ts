import { z } from "zod";

import { emissionDryRunScenarioIdSchema } from "./emission-dry-run.js";
import { registryOperationalStatusSchema, registryScenarioIdSchema } from "./registry-shared.js";
import { serviceOrderReviewScenarioIdSchema } from "./service-order-review.js";

export const standardRegistryScenarioIdSchema = z.enum([
  "operational-ready",
  "expiration-attention",
  "expired-blocked",
]);
export type StandardRegistryScenarioId = z.infer<typeof standardRegistryScenarioIdSchema>;

export const standardExpirationMarkerSchema = z.object({
  standardId: z.string().min(1),
  label: z.string().min(1),
  dueInLabel: z.string().min(1),
  status: registryOperationalStatusSchema,
});
export type StandardExpirationMarker = z.infer<typeof standardExpirationMarkerSchema>;

export const standardListItemSchema = z.object({
  standardId: z.string().min(1),
  kindLabel: z.string().min(1),
  nominalClassLabel: z.string().min(1),
  sourceLabel: z.string().min(1),
  certificateLabel: z.string().min(1),
  validUntilLabel: z.string().min(1),
  status: registryOperationalStatusSchema,
});
export type StandardListItem = z.infer<typeof standardListItemSchema>;

export const standardCalibrationHistoryEntrySchema = z.object({
  calibratedAtLabel: z.string().min(1),
  laboratoryLabel: z.string().min(1),
  certificateLabel: z.string().min(1),
  sourceLabel: z.string().min(1),
  uncertaintyLabel: z.string().min(1),
  validUntilLabel: z.string().min(1),
});
export type StandardCalibrationHistoryEntry = z.infer<typeof standardCalibrationHistoryEntrySchema>;

export const standardRecentWorkOrderSchema = z.object({
  workOrderNumber: z.string().min(1),
  usedAtLabel: z.string().min(1),
});
export type StandardRecentWorkOrder = z.infer<typeof standardRecentWorkOrderSchema>;

export const standardDetailLinksSchema = z.object({
  registryScenarioId: registryScenarioIdSchema.optional(),
  selectedEquipmentId: z.string().min(1).optional(),
  serviceOrderScenarioId: serviceOrderReviewScenarioIdSchema.optional(),
  reviewItemId: z.string().min(1).optional(),
  dryRunScenarioId: emissionDryRunScenarioIdSchema.optional(),
});
export type StandardDetailLinks = z.infer<typeof standardDetailLinksSchema>;

export const standardDetailSchema = z.object({
  standardId: z.string().min(1),
  title: z.string().min(1),
  status: registryOperationalStatusSchema,
  noticeLabel: z.string().min(1),
  manufacturerLabel: z.string().min(1),
  modelLabel: z.string().min(1),
  serialNumberLabel: z.string().min(1),
  nominalValueLabel: z.string().min(1),
  classLabel: z.string().min(1),
  usageRangeLabel: z.string().min(1),
  uncertaintyLabel: z.string().min(1),
  correctionFactorLabel: z.string().min(1),
  history: z.array(standardCalibrationHistoryEntrySchema).min(1),
  recentWorkOrders: z.array(standardRecentWorkOrderSchema).min(1),
  blockers: z.array(z.string().min(1)),
  warnings: z.array(z.string().min(1)),
  links: standardDetailLinksSchema,
});
export type StandardDetail = z.infer<typeof standardDetailSchema>;

export const standardRegistrySummarySchema = z.object({
  status: registryOperationalStatusSchema,
  headline: z.string().min(1),
  activeCount: z.number().int().nonnegative(),
  expiringSoonCount: z.number().int().nonnegative(),
  expiredCount: z.number().int().nonnegative(),
  recommendedAction: z.string().min(1),
  blockers: z.array(z.string().min(1)),
  warnings: z.array(z.string().min(1)),
  expirationPanel: z.array(standardExpirationMarkerSchema).min(1),
});
export type StandardRegistrySummary = z.infer<typeof standardRegistrySummarySchema>;

export const standardRegistryScenarioSchema = z.object({
  id: standardRegistryScenarioIdSchema,
  label: z.string().min(1),
  description: z.string().min(1),
  summary: standardRegistrySummarySchema,
  selectedStandardId: z.string().min(1),
  items: z.array(standardListItemSchema).min(1),
  detail: standardDetailSchema,
});
export type StandardRegistryScenario = z.infer<typeof standardRegistryScenarioSchema>;

export const standardRegistryCatalogSchema = z.object({
  selectedScenarioId: standardRegistryScenarioIdSchema,
  scenarios: z.array(standardRegistryScenarioSchema).min(1),
});
export type StandardRegistryCatalog = z.infer<typeof standardRegistryCatalogSchema>;
