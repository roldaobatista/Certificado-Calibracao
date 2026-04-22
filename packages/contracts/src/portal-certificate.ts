import { z } from "zod";

import { portalDashboardScenarioIdSchema } from "./portal-dashboard.js";
import { portalEquipmentScenarioIdSchema } from "./portal-equipment.js";
import { publicCertificateScenarioIdSchema } from "./public-certificate.js";
import { registryOperationalStatusSchema } from "./registry-shared.js";

export const portalCertificateScenarioIdSchema = z.enum([
  "current-valid",
  "reissued-history",
  "download-blocked",
]);
export type PortalCertificateScenarioId = z.infer<typeof portalCertificateScenarioIdSchema>;

export const portalCertificateActionKeySchema = z.enum([
  "download_pdf",
  "share_public_link",
  "print_certificate",
]);
export type PortalCertificateActionKey = z.infer<typeof portalCertificateActionKeySchema>;

export const portalCertificateActionSchema = z.object({
  key: portalCertificateActionKeySchema,
  label: z.string().min(1),
  status: registryOperationalStatusSchema,
});
export type PortalCertificateAction = z.infer<typeof portalCertificateActionSchema>;

export const portalCertificateMetadataFieldSchema = z.object({
  label: z.string().min(1),
  value: z.string().min(1),
});
export type PortalCertificateMetadataField = z.infer<typeof portalCertificateMetadataFieldSchema>;

export const portalCertificateListItemSchema = z.object({
  certificateId: z.string().min(1),
  certificateNumber: z.string().min(1),
  equipmentLabel: z.string().min(1),
  issuedAtLabel: z.string().min(1),
  statusLabel: z.string().min(1),
  verifyScenarioId: publicCertificateScenarioIdSchema,
  status: registryOperationalStatusSchema,
});
export type PortalCertificateListItem = z.infer<typeof portalCertificateListItemSchema>;

export const portalCertificateDetailSchema = z.object({
  certificateId: z.string().min(1),
  title: z.string().min(1),
  status: registryOperationalStatusSchema,
  hashLabel: z.string().min(1),
  signatureLabel: z.string().min(1),
  viewerLabel: z.string().min(1),
  publicLinkLabel: z.string().min(1),
  recommendedAction: z.string().min(1),
  metadataFields: z.array(portalCertificateMetadataFieldSchema).min(1),
  actions: z.array(portalCertificateActionSchema).min(1),
  verificationSteps: z.array(z.string().min(1)).min(1),
  blockers: z.array(z.string().min(1)),
  warnings: z.array(z.string().min(1)),
  equipmentId: z.string().min(1),
  equipmentScenarioId: portalEquipmentScenarioIdSchema,
  dashboardScenarioId: portalDashboardScenarioIdSchema,
  publicVerifyScenarioId: publicCertificateScenarioIdSchema,
});
export type PortalCertificateDetail = z.infer<typeof portalCertificateDetailSchema>;

export const portalCertificateSummarySchema = z.object({
  status: registryOperationalStatusSchema,
  headline: z.string().min(1),
  totalCertificates: z.number().int().nonnegative(),
  readyCount: z.number().int().nonnegative(),
  attentionCount: z.number().int().nonnegative(),
  blockedCount: z.number().int().nonnegative(),
  recommendedAction: z.string().min(1),
  blockers: z.array(z.string().min(1)),
  warnings: z.array(z.string().min(1)),
});
export type PortalCertificateSummary = z.infer<typeof portalCertificateSummarySchema>;

export const portalCertificateScenarioSchema = z.object({
  id: portalCertificateScenarioIdSchema,
  label: z.string().min(1),
  description: z.string().min(1),
  summary: portalCertificateSummarySchema,
  selectedCertificateId: z.string().min(1),
  items: z.array(portalCertificateListItemSchema).min(1),
  detail: portalCertificateDetailSchema,
});
export type PortalCertificateScenario = z.infer<typeof portalCertificateScenarioSchema>;

export const portalCertificateCatalogSchema = z.object({
  selectedScenarioId: portalCertificateScenarioIdSchema,
  scenarios: z.array(portalCertificateScenarioSchema).min(1),
});
export type PortalCertificateCatalog = z.infer<typeof portalCertificateCatalogSchema>;
