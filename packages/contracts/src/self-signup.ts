import { z } from "zod";

export const selfSignupRoleSchema = z.enum(["admin", "signatory", "technician"]);
export type SelfSignupRole = z.infer<typeof selfSignupRoleSchema>;

export const selfSignupProviderSchema = z.enum([
  "email_password",
  "google",
  "microsoft",
  "apple",
]);
export type SelfSignupProvider = z.infer<typeof selfSignupProviderSchema>;

export const selfSignupChecklistViewModelSchema = z.object({
  status: z.enum(["ready", "blocked"]),
  visibleMethods: z.array(selfSignupProviderSchema),
  missingMethods: z.array(selfSignupProviderSchema),
  showMfaStep: z.boolean(),
});
export type SelfSignupChecklistViewModel = z.infer<typeof selfSignupChecklistViewModelSchema>;

export const selfSignupPolicyResultSchema = z.object({
  ok: z.boolean(),
  missingProviders: z.array(selfSignupProviderSchema),
  mfaRequired: z.boolean(),
  reason: z
    .enum(["missing_required_provider", "mfa_required_for_privileged_role"])
    .optional(),
});
export type SelfSignupPolicyResult = z.infer<typeof selfSignupPolicyResultSchema>;

export const selfSignupScenarioIdSchema = z.enum([
  "signatory-ready",
  "admin-guided",
  "technician-blocked",
]);
export type SelfSignupScenarioId = z.infer<typeof selfSignupScenarioIdSchema>;

export const selfSignupScenarioSchema = z.object({
  id: selfSignupScenarioIdSchema,
  label: z.string().min(1),
  description: z.string().min(1),
  role: selfSignupRoleSchema,
  result: selfSignupPolicyResultSchema,
});
export type SelfSignupScenario = z.infer<typeof selfSignupScenarioSchema>;

export const selfSignupCatalogSchema = z.object({
  selectedScenarioId: selfSignupScenarioIdSchema,
  scenarios: z.array(selfSignupScenarioSchema).min(1),
});
export type SelfSignupCatalog = z.infer<typeof selfSignupCatalogSchema>;
