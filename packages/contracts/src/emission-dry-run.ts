import { z } from "zod";

import { publicCertificateStatusSchema } from "./public-certificate.js";

export const emissionDryRunProfileSchema = z.enum(["A", "B", "C"]);
export type EmissionDryRunProfile = z.infer<typeof emissionDryRunProfileSchema>;

export const emissionDryRunStatusSchema = z.enum(["ready", "blocked"]);
export type EmissionDryRunStatus = z.infer<typeof emissionDryRunStatusSchema>;

export const emissionDryRunCheckIdSchema = z.enum([
  "profile_policy",
  "equipment_registration",
  "standard_eligibility",
  "signatory_competence",
  "certificate_numbering",
  "measurement_declaration",
  "audit_trail",
  "qr_authenticity",
]);
export type EmissionDryRunCheckId = z.infer<typeof emissionDryRunCheckIdSchema>;

export const emissionDryRunCheckSchema = z.object({
  id: emissionDryRunCheckIdSchema,
  title: z.string().min(1),
  status: z.enum(["passed", "failed"]),
  detail: z.string().min(1),
});
export type EmissionDryRunCheck = z.infer<typeof emissionDryRunCheckSchema>;

export const emissionDryRunArtifactsSchema = z.object({
  templateId: z.enum(["template-a", "template-b", "template-c"]),
  symbolPolicy: z.enum(["allowed", "blocked", "suppressed"]),
  certificateNumber: z.string().min(1).optional(),
  declarationSummary: z.string().min(1).optional(),
  qrCodeUrl: z.string().url().optional(),
  qrVerificationStatus: publicCertificateStatusSchema.optional(),
  publicPreview: z.record(z.string(), z.string()),
});
export type EmissionDryRunArtifacts = z.infer<typeof emissionDryRunArtifactsSchema>;

export const emissionDryRunResultSchema = z.object({
  status: emissionDryRunStatusSchema,
  profile: emissionDryRunProfileSchema,
  summary: z.string().min(1),
  blockers: z.array(z.string().min(1)),
  warnings: z.array(z.string().min(1)),
  checks: z.array(emissionDryRunCheckSchema),
  artifacts: emissionDryRunArtifactsSchema,
});
export type EmissionDryRunResult = z.infer<typeof emissionDryRunResultSchema>;
