import { z } from "zod";

import { membershipRoleSchema } from "./review-signature.js";

export const authSessionUserSchema = z.object({
  userId: z.string().min(1),
  organizationId: z.string().min(1),
  organizationName: z.string().min(1),
  organizationSlug: z.string().min(1),
  email: z.string().email(),
  displayName: z.string().min(1),
  roles: z.array(membershipRoleSchema).min(1),
  mfaEnrolled: z.boolean(),
});
export type AuthSessionUser = z.infer<typeof authSessionUserSchema>;

export const authSessionSchema = z.discriminatedUnion("authenticated", [
  z.object({
    authenticated: z.literal(false),
  }),
  z.object({
    authenticated: z.literal(true),
    user: authSessionUserSchema,
    expiresAtUtc: z.string().min(1),
  }),
]);
export type AuthSession = z.infer<typeof authSessionSchema>;

export const authLoginResponseSchema = z.object({
  ok: z.boolean(),
  reason: z.enum(["invalid_credentials", "inactive_user", "mfa_required"]).optional(),
  session: authSessionSchema.optional(),
});
export type AuthLoginResponse = z.infer<typeof authLoginResponseSchema>;
