import { z } from "zod";

import { portalDashboardScenarioIdSchema } from "./portal-dashboard.js";
import { publicCertificateScenarioIdSchema } from "./public-certificate.js";
import { registryOperationalStatusSchema } from "./registry-shared.js";

export const portalEquipmentScenarioIdSchema = portalDashboardScenarioIdSchema;
export type PortalEquipmentScenarioId = z.infer<typeof portalEquipmentScenarioIdSchema>;

export const portalEquipmentListItemSchema = z.object({
  equipmentId: z.string().min(1),
  tag: z.string().min(1),
  description: z.string().min(1),
  manufacturerModelLabel: z.string().min(1),
  locationLabel: z.string().min(1),
  lastCalibrationLabel: z.string().min(1),
  nextDueLabel: z.string().min(1),
  status: registryOperationalStatusSchema,
});
export type PortalEquipmentListItem = z.infer<typeof portalEquipmentListItemSchema>;

export const portalEquipmentCertificateHistoryItemSchema = z.object({
  certificateId: z.string().min(1),
  issuedAtLabel: z.string().min(1),
  certificateNumber: z.string().min(1),
  resultLabel: z.string().min(1),
  uncertaintyLabel: z.string().min(1),
  verifyScenarioId: publicCertificateScenarioIdSchema,
});
export type PortalEquipmentCertificateHistoryItem = z.infer<
  typeof portalEquipmentCertificateHistoryItemSchema
>;

export const portalEquipmentDetailSchema = z.object({
  equipmentId: z.string().min(1),
  title: z.string().min(1),
  status: registryOperationalStatusSchema,
  manufacturerLabel: z.string().min(1),
  modelLabel: z.string().min(1),
  serialLabel: z.string().min(1),
  capacityClassLabel: z.string().min(1),
  locationLabel: z.string().min(1),
  recommendedAction: z.string().min(1),
  blockers: z.array(z.string().min(1)),
  warnings: z.array(z.string().min(1)),
  certificateHistory: z.array(portalEquipmentCertificateHistoryItemSchema).min(1),
});
export type PortalEquipmentDetail = z.infer<typeof portalEquipmentDetailSchema>;

export const portalEquipmentSummarySchema = z.object({
  status: registryOperationalStatusSchema,
  headline: z.string().min(1),
  equipmentCount: z.number().int().nonnegative(),
  attentionCount: z.number().int().nonnegative(),
  blockedCount: z.number().int().nonnegative(),
  recommendedAction: z.string().min(1),
  blockers: z.array(z.string().min(1)),
  warnings: z.array(z.string().min(1)),
});
export type PortalEquipmentSummary = z.infer<typeof portalEquipmentSummarySchema>;

export const portalEquipmentScenarioSchema = z.object({
  id: portalEquipmentScenarioIdSchema,
  label: z.string().min(1),
  description: z.string().min(1),
  summary: portalEquipmentSummarySchema,
  selectedEquipmentId: z.string().min(1),
  items: z.array(portalEquipmentListItemSchema).min(1),
  detail: portalEquipmentDetailSchema,
});
export type PortalEquipmentScenario = z.infer<typeof portalEquipmentScenarioSchema>;

export const portalEquipmentCatalogSchema = z.object({
  selectedScenarioId: portalEquipmentScenarioIdSchema,
  scenarios: z.array(portalEquipmentScenarioSchema).min(1),
});
export type PortalEquipmentCatalog = z.infer<typeof portalEquipmentCatalogSchema>;
