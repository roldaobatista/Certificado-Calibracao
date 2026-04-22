import { z } from "zod";

import { publicCertificateScenarioIdSchema } from "./public-certificate.js";
import { registryOperationalStatusSchema } from "./registry-shared.js";

export const portalDashboardScenarioIdSchema = z.enum([
  "stable-portfolio",
  "expiring-soon",
  "overdue-blocked",
]);
export type PortalDashboardScenarioId = z.infer<typeof portalDashboardScenarioIdSchema>;

export const portalDashboardEquipmentItemSchema = z.object({
  equipmentId: z.string().min(1),
  tag: z.string().min(1),
  description: z.string().min(1),
  locationLabel: z.string().min(1),
  lastCalibrationLabel: z.string().min(1),
  dueAtLabel: z.string().min(1),
  status: registryOperationalStatusSchema,
});
export type PortalDashboardEquipmentItem = z.infer<typeof portalDashboardEquipmentItemSchema>;

export const portalDashboardCertificateItemSchema = z.object({
  certificateId: z.string().min(1),
  certificateNumber: z.string().min(1),
  equipmentLabel: z.string().min(1),
  issuedAtLabel: z.string().min(1),
  statusLabel: z.string().min(1),
  verifyScenarioId: publicCertificateScenarioIdSchema,
});
export type PortalDashboardCertificateItem = z.infer<typeof portalDashboardCertificateItemSchema>;

export const portalDashboardSummarySchema = z.object({
  status: registryOperationalStatusSchema,
  clientName: z.string().min(1),
  organizationName: z.string().min(1),
  equipmentCount: z.number().int().nonnegative(),
  certificateCount: z.number().int().nonnegative(),
  expiringSoonCount: z.number().int().nonnegative(),
  overdueCount: z.number().int().nonnegative(),
  recommendedAction: z.string().min(1),
  blockers: z.array(z.string().min(1)),
  warnings: z.array(z.string().min(1)),
});
export type PortalDashboardSummary = z.infer<typeof portalDashboardSummarySchema>;

export const portalDashboardScenarioSchema = z.object({
  id: portalDashboardScenarioIdSchema,
  label: z.string().min(1),
  description: z.string().min(1),
  summary: portalDashboardSummarySchema,
  expiringEquipments: z.array(portalDashboardEquipmentItemSchema),
  recentCertificates: z.array(portalDashboardCertificateItemSchema).min(1),
});
export type PortalDashboardScenario = z.infer<typeof portalDashboardScenarioSchema>;

export const portalDashboardCatalogSchema = z.object({
  selectedScenarioId: portalDashboardScenarioIdSchema,
  scenarios: z.array(portalDashboardScenarioSchema).min(1),
});
export type PortalDashboardCatalog = z.infer<typeof portalDashboardCatalogSchema>;
