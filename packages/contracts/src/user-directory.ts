import { z } from "zod";

import { membershipRoleSchema } from "./review-signature.js";

export const userLifecycleStatusSchema = z.enum(["invited", "active", "suspended"]);
export type UserLifecycleStatus = z.infer<typeof userLifecycleStatusSchema>;

export const competencyStatusSchema = z.enum(["authorized", "expiring", "expired"]);
export type CompetencyStatus = z.infer<typeof competencyStatusSchema>;

export const userCompetencySchema = z.object({
  instrumentType: z.string().min(1),
  roleLabel: z.string().min(1),
  status: competencyStatusSchema,
  validUntilUtc: z.string().min(1),
});
export type UserCompetency = z.infer<typeof userCompetencySchema>;

export const directoryUserSchema = z.object({
  userId: z.string().min(1),
  displayName: z.string().min(1),
  email: z.string().email(),
  roles: z.array(membershipRoleSchema).min(1),
  status: userLifecycleStatusSchema,
  teamName: z.string().min(1).optional(),
  lastLoginUtc: z.string().min(1).optional(),
  deviceCount: z.number().int().nonnegative(),
  competencies: z.array(userCompetencySchema),
});
export type DirectoryUser = z.infer<typeof directoryUserSchema>;

export const userDirectorySummarySchema = z.object({
  status: z.enum(["ready", "attention"]),
  organizationName: z.string().min(1),
  activeUsers: z.number().int().nonnegative(),
  invitedUsers: z.number().int().nonnegative(),
  suspendedUsers: z.number().int().nonnegative(),
  expiringCompetencies: z.number().int().nonnegative(),
  expiredCompetencies: z.number().int().nonnegative(),
});
export type UserDirectorySummary = z.infer<typeof userDirectorySummarySchema>;

export const userDirectoryScenarioIdSchema = z.enum([
  "operational-team",
  "expiring-competencies",
  "suspended-access",
]);
export type UserDirectoryScenarioId = z.infer<typeof userDirectoryScenarioIdSchema>;

export const userDirectoryScenarioSchema = z.object({
  id: userDirectoryScenarioIdSchema,
  label: z.string().min(1),
  description: z.string().min(1),
  summary: userDirectorySummarySchema,
  users: z.array(directoryUserSchema).min(1),
});
export type UserDirectoryScenario = z.infer<typeof userDirectoryScenarioSchema>;

export const userDirectoryCatalogSchema = z.object({
  selectedScenarioId: userDirectoryScenarioIdSchema,
  scenarios: z.array(userDirectoryScenarioSchema).min(1),
});
export type UserDirectoryCatalog = z.infer<typeof userDirectoryCatalogSchema>;
