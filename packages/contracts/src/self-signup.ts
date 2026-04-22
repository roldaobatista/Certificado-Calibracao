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
