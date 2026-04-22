import { z } from "zod";

import { emissionDryRunScenarioIdSchema } from "./emission-dry-run.js";
import { registryOperationalStatusSchema, registryScenarioIdSchema } from "./registry-shared.js";
import { serviceOrderReviewScenarioIdSchema } from "./service-order-review.js";

export const equipmentListItemSchema = z.object({
  equipmentId: z.string().min(1),
  customerId: z.string().min(1),
  customerName: z.string().min(1),
  code: z.string().min(1),
  tagCode: z.string().min(1),
  serialNumber: z.string().min(1),
  typeModelLabel: z.string().min(1),
  capacityClassLabel: z.string().min(1),
  lastCalibrationLabel: z.string().min(1),
  nextCalibrationLabel: z.string().min(1),
  registrationStatusLabel: z.string().min(1),
  status: registryOperationalStatusSchema,
  missingFields: z.array(z.string().min(1)),
  dryRunScenarioId: emissionDryRunScenarioIdSchema.optional(),
});
export type EquipmentListItem = z.infer<typeof equipmentListItemSchema>;

export const equipmentDetailLinksSchema = z.object({
  customerScenarioId: registryScenarioIdSchema,
  customerId: z.string().min(1),
  serviceOrderScenarioId: serviceOrderReviewScenarioIdSchema.optional(),
  reviewItemId: z.string().min(1).optional(),
  dryRunScenarioId: emissionDryRunScenarioIdSchema.optional(),
});
export type EquipmentDetailLinks = z.infer<typeof equipmentDetailLinksSchema>;

export const equipmentDetailSchema = z.object({
  equipmentId: z.string().min(1),
  title: z.string().min(1),
  status: registryOperationalStatusSchema,
  statusLine: z.string().min(1),
  customerLabel: z.string().min(1),
  addressLabel: z.string().min(1),
  standardSetLabel: z.string().min(1),
  lastServiceOrderLabel: z.string().min(1),
  nextCalibrationLabel: z.string().min(1),
  blockers: z.array(z.string().min(1)),
  warnings: z.array(z.string().min(1)),
  links: equipmentDetailLinksSchema,
});
export type EquipmentDetail = z.infer<typeof equipmentDetailSchema>;

export const equipmentRegistrySummarySchema = z.object({
  status: registryOperationalStatusSchema,
  headline: z.string().min(1),
  totalEquipment: z.number().int().nonnegative(),
  readyCount: z.number().int().nonnegative(),
  attentionCount: z.number().int().nonnegative(),
  blockedCount: z.number().int().nonnegative(),
  dueSoonCount: z.number().int().nonnegative(),
  recommendedAction: z.string().min(1),
  blockers: z.array(z.string().min(1)),
  warnings: z.array(z.string().min(1)),
});
export type EquipmentRegistrySummary = z.infer<typeof equipmentRegistrySummarySchema>;

export const equipmentRegistryScenarioSchema = z.object({
  id: registryScenarioIdSchema,
  label: z.string().min(1),
  description: z.string().min(1),
  summary: equipmentRegistrySummarySchema,
  selectedEquipmentId: z.string().min(1),
  items: z.array(equipmentListItemSchema).min(1),
  detail: equipmentDetailSchema,
});
export type EquipmentRegistryScenario = z.infer<typeof equipmentRegistryScenarioSchema>;

export const equipmentRegistryCatalogSchema = z.object({
  selectedScenarioId: registryScenarioIdSchema,
  scenarios: z.array(equipmentRegistryScenarioSchema).min(1),
});
export type EquipmentRegistryCatalog = z.infer<typeof equipmentRegistryCatalogSchema>;
