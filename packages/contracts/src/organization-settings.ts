import { z } from "zod";

import { auditTrailScenarioIdSchema } from "./audit-trail.js";
import { emissionWorkspaceScenarioIdSchema } from "./emission-workspace.js";
import { onboardingScenarioIdSchema } from "./onboarding.js";
import { procedureRegistryScenarioIdSchema } from "./procedure-registry.js";
import { registryOperationalStatusSchema } from "./registry-shared.js";
import { selfSignupScenarioIdSchema } from "./self-signup.js";
import { standardRegistryScenarioIdSchema } from "./standard-registry.js";
import { userDirectoryScenarioIdSchema } from "./user-directory.js";

export const organizationSettingsScenarioIdSchema = z.enum([
  "operational-ready",
  "renewal-attention",
  "profile-change-blocked",
]);
export type OrganizationSettingsScenarioId = z.infer<typeof organizationSettingsScenarioIdSchema>;

export const organizationSettingsSectionKeySchema = z.enum([
  "identity",
  "branding",
  "regulatory_profile",
  "numbering",
  "plan",
  "integrations",
  "security",
  "sso_saml",
  "notifications",
  "lgpd_dpo",
]);
export type OrganizationSettingsSectionKey = z.infer<typeof organizationSettingsSectionKeySchema>;

export const organizationSettingsSectionSchema = z.object({
  key: organizationSettingsSectionKeySchema,
  title: z.string().min(1),
  status: registryOperationalStatusSchema,
  detail: z.string().min(1),
  ownerLabel: z.string().min(1),
  lastUpdatedLabel: z.string().min(1),
  actionLabel: z.string().min(1),
});
export type OrganizationSettingsSection = z.infer<typeof organizationSettingsSectionSchema>;

export const organizationSettingsDetailLinksSchema = z.object({
  onboardingScenarioId: onboardingScenarioIdSchema.optional(),
  selfSignupScenarioId: selfSignupScenarioIdSchema.optional(),
  userDirectoryScenarioId: userDirectoryScenarioIdSchema.optional(),
  workspaceScenarioId: emissionWorkspaceScenarioIdSchema.optional(),
  auditTrailScenarioId: auditTrailScenarioIdSchema.optional(),
  standardScenarioId: standardRegistryScenarioIdSchema.optional(),
  procedureScenarioId: procedureRegistryScenarioIdSchema.optional(),
});
export type OrganizationSettingsDetailLinks = z.infer<typeof organizationSettingsDetailLinksSchema>;

export const organizationSettingsDetailSchema = z.object({
  sectionKey: organizationSettingsSectionKeySchema,
  title: z.string().min(1),
  status: registryOperationalStatusSchema,
  summary: z.string().min(1),
  evidenceLabel: z.string().min(1),
  lastReviewedLabel: z.string().min(1),
  reviewModeLabel: z.string().min(1),
  checklistItems: z.array(z.string().min(1)).min(1),
  blockers: z.array(z.string().min(1)),
  warnings: z.array(z.string().min(1)),
  links: organizationSettingsDetailLinksSchema,
});
export type OrganizationSettingsDetail = z.infer<typeof organizationSettingsDetailSchema>;

export const organizationSettingsSummarySchema = z.object({
  status: registryOperationalStatusSchema,
  organizationName: z.string().min(1),
  organizationCode: z.string().min(1),
  profileLabel: z.string().min(1),
  accreditationLabel: z.string().min(1),
  planLabel: z.string().min(1),
  configuredSections: z.number().int().nonnegative(),
  attentionSections: z.number().int().nonnegative(),
  blockedSections: z.number().int().nonnegative(),
  recommendedAction: z.string().min(1),
  blockers: z.array(z.string().min(1)),
  warnings: z.array(z.string().min(1)),
});
export type OrganizationSettingsSummary = z.infer<typeof organizationSettingsSummarySchema>;

export const organizationSettingsScenarioSchema = z.object({
  id: organizationSettingsScenarioIdSchema,
  label: z.string().min(1),
  description: z.string().min(1),
  summary: organizationSettingsSummarySchema,
  selectedSectionKey: organizationSettingsSectionKeySchema,
  sections: z.array(organizationSettingsSectionSchema).min(1),
  detail: organizationSettingsDetailSchema,
});
export type OrganizationSettingsScenario = z.infer<typeof organizationSettingsScenarioSchema>;

export const organizationSettingsCatalogSchema = z.object({
  selectedScenarioId: organizationSettingsScenarioIdSchema,
  scenarios: z.array(organizationSettingsScenarioSchema).min(1),
});
export type OrganizationSettingsCatalog = z.infer<typeof organizationSettingsCatalogSchema>;
