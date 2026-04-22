import { z } from "zod";

export const onboardingBlockingReasonSchema = z.enum([
  "organization_profile_pending",
  "primary_signatory_pending",
  "certificate_numbering_pending",
  "scope_review_pending",
  "public_qr_pending",
]);
export type OnboardingBlockingReason = z.infer<typeof onboardingBlockingReasonSchema>;

export const onboardingReadinessResultSchema = z.object({
  completedWithinTarget: z.boolean(),
  canEmitFirstCertificate: z.boolean(),
  blockingReasons: z.array(onboardingBlockingReasonSchema),
});
export type OnboardingReadinessResult = z.infer<typeof onboardingReadinessResultSchema>;

export const onboardingWizardSummarySchema = z.object({
  status: z.enum(["ready", "blocked"]),
  title: z.string().min(1),
  timeTargetLabel: z.string().min(1),
  blockingSteps: z.array(z.string()),
});
export type OnboardingWizardSummary = z.infer<typeof onboardingWizardSummarySchema>;

export const onboardingScenarioIdSchema = z.enum(["ready", "blocked"]);
export type OnboardingScenarioId = z.infer<typeof onboardingScenarioIdSchema>;

export const onboardingScenarioSchema = z.object({
  id: onboardingScenarioIdSchema,
  label: z.string().min(1),
  description: z.string().min(1),
  result: onboardingReadinessResultSchema,
});
export type OnboardingScenario = z.infer<typeof onboardingScenarioSchema>;

export const onboardingCatalogSchema = z.object({
  selectedScenarioId: onboardingScenarioIdSchema,
  scenarios: z.array(onboardingScenarioSchema).min(1),
});
export type OnboardingCatalog = z.infer<typeof onboardingCatalogSchema>;
