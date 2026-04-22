import { z } from "zod";

import {
  emissionDryRunScenarioIdSchema,
  emissionDryRunStatusSchema,
  emissionDryRunArtifactsSchema,
} from "./emission-dry-run.js";
import { publicCertificateStatusSchema } from "./public-certificate.js";

export const certificatePreviewSectionKeySchema = z.enum([
  "header",
  "identification",
  "standards",
  "environment",
  "results",
  "decision",
  "authorization",
  "footer",
]);
export type CertificatePreviewSectionKey = z.infer<typeof certificatePreviewSectionKeySchema>;

export const certificatePreviewFieldSchema = z.object({
  label: z.string().min(1),
  value: z.string().min(1),
});
export type CertificatePreviewField = z.infer<typeof certificatePreviewFieldSchema>;

export const certificatePreviewSectionSchema = z.object({
  key: certificatePreviewSectionKeySchema,
  title: z.string().min(1),
  fields: z.array(certificatePreviewFieldSchema).min(1),
});
export type CertificatePreviewSection = z.infer<typeof certificatePreviewSectionSchema>;

export const emissionCertificatePreviewSchema = z.object({
  status: emissionDryRunStatusSchema,
  headline: z.string().min(1),
  templateId: emissionDryRunArtifactsSchema.shape.templateId,
  symbolPolicy: emissionDryRunArtifactsSchema.shape.symbolPolicy,
  certificateNumber: z.string().min(1).optional(),
  qrCodeUrl: z.string().url().optional(),
  qrVerificationStatus: publicCertificateStatusSchema.optional(),
  suggestedReturnStep: z.number().int().min(1).max(15).optional(),
  blockers: z.array(z.string().min(1)),
  warnings: z.array(z.string().min(1)),
  sections: z.array(certificatePreviewSectionSchema).min(1),
});
export type EmissionCertificatePreview = z.infer<typeof emissionCertificatePreviewSchema>;

export const certificatePreviewScenarioSchema = z.object({
  id: emissionDryRunScenarioIdSchema,
  label: z.string().min(1),
  description: z.string().min(1),
  result: emissionCertificatePreviewSchema,
});
export type CertificatePreviewScenario = z.infer<typeof certificatePreviewScenarioSchema>;

export const certificatePreviewCatalogSchema = z.object({
  selectedScenarioId: emissionDryRunScenarioIdSchema,
  scenarios: z.array(certificatePreviewScenarioSchema).min(1),
});
export type CertificatePreviewCatalog = z.infer<typeof certificatePreviewCatalogSchema>;
