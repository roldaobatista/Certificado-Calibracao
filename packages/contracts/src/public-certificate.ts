import { z } from "zod";

export const publicCertificateStatusSchema = z.enum(["authentic", "reissued", "not_found"]);
export type PublicCertificateStatus = z.infer<typeof publicCertificateStatusSchema>;

export const publicCertificateQrFailureReasonSchema = z.enum([
  "invalid_qr_url",
  "certificate_not_found",
  "token_mismatch",
  "invalid_audit_trail",
  "missing_emission_event",
  "missing_reissue_evidence",
]);
export type PublicCertificateQrFailureReason = z.infer<typeof publicCertificateQrFailureReasonSchema>;

export const publicCertificateRecordSchema = z
  .object({
    certificateId: z.string().min(1).optional(),
    certificateNumber: z.string().min(1),
    publicVerificationToken: z.string().min(1).optional(),
    issuedAtUtc: z.string().datetime().optional(),
    reissuedAtUtc: z.string().datetime().optional(),
    replacementCertificateNumber: z.string().min(1).optional(),
    revision: z.string().min(1).optional(),
    instrumentDescription: z.string().min(1).optional(),
    serialNumber: z.string().min(1).optional(),
  })
  .catchall(z.unknown());
export type PublicCertificateRecord = z.infer<typeof publicCertificateRecordSchema>;

export const publicCertificateQrVerificationResultSchema = z.discriminatedUnion("status", [
  z.object({
    ok: z.literal(true),
    status: z.literal("authentic"),
    certificate: publicCertificateRecordSchema,
  }),
  z.object({
    ok: z.literal(true),
    status: z.literal("reissued"),
    certificate: publicCertificateRecordSchema,
  }),
  z.object({
    ok: z.literal(false),
    status: z.literal("not_found"),
    reason: publicCertificateQrFailureReasonSchema,
  }),
]);
export type PublicCertificateQrVerificationResult = z.infer<
  typeof publicCertificateQrVerificationResultSchema
>;

export const publicCertificatePageModelSchema = z.object({
  status: publicCertificateStatusSchema,
  title: z.string().min(1),
  publicMetadata: z.record(z.string(), z.string()),
});
export type PublicCertificatePageModel = z.infer<typeof publicCertificatePageModelSchema>;

export const publicCertificateScenarioIdSchema = z.enum([
  "authentic",
  "reissued",
  "not-found",
]);
export type PublicCertificateScenarioId = z.infer<typeof publicCertificateScenarioIdSchema>;

export const publicCertificateScenarioSchema = z.object({
  id: publicCertificateScenarioIdSchema,
  label: z.string().min(1),
  description: z.string().min(1),
  result: publicCertificateQrVerificationResultSchema,
});
export type PublicCertificateScenario = z.infer<typeof publicCertificateScenarioSchema>;

export const publicCertificateCatalogSchema = z.object({
  selectedScenarioId: publicCertificateScenarioIdSchema,
  scenarios: z.array(publicCertificateScenarioSchema).min(1),
});
export type PublicCertificateCatalog = z.infer<typeof publicCertificateCatalogSchema>;
