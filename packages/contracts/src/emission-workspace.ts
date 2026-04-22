import { z } from "zod";

import { emissionDryRunScenarioIdSchema } from "./emission-dry-run.js";
import { onboardingScenarioIdSchema } from "./onboarding.js";
import { reviewSignatureScenarioIdSchema } from "./review-signature.js";
import { selfSignupScenarioIdSchema } from "./self-signup.js";
import { userDirectoryScenarioIdSchema } from "./user-directory.js";

export const emissionWorkspaceStatusSchema = z.enum(["ready", "attention", "blocked"]);
export type EmissionWorkspaceStatus = z.infer<typeof emissionWorkspaceStatusSchema>;

export const emissionWorkspaceModuleKeySchema = z.enum([
  "auth",
  "onboarding",
  "team",
  "dry_run",
  "workflow",
]);
export type EmissionWorkspaceModuleKey = z.infer<typeof emissionWorkspaceModuleKeySchema>;

export const emissionWorkspaceModuleSchema = z.object({
  key: emissionWorkspaceModuleKeySchema,
  title: z.string().min(1),
  status: emissionWorkspaceStatusSchema,
  detail: z.string().min(1),
  href: z.string().min(1),
});
export type EmissionWorkspaceModule = z.infer<typeof emissionWorkspaceModuleSchema>;

export const emissionWorkspaceScenarioRefsSchema = z.object({
  selfSignupScenarioId: selfSignupScenarioIdSchema,
  onboardingScenarioId: onboardingScenarioIdSchema,
  userDirectoryScenarioId: userDirectoryScenarioIdSchema,
  dryRunScenarioId: emissionDryRunScenarioIdSchema,
  reviewSignatureScenarioId: reviewSignatureScenarioIdSchema,
});
export type EmissionWorkspaceScenarioRefs = z.infer<typeof emissionWorkspaceScenarioRefsSchema>;

export const emissionWorkspaceSummarySchema = z.object({
  status: emissionWorkspaceStatusSchema,
  headline: z.string().min(1),
  readyToEmit: z.boolean(),
  recommendedAction: z.string().min(1),
  readyModules: z.number().int().nonnegative(),
  attentionModules: z.number().int().nonnegative(),
  blockedModules: z.number().int().nonnegative(),
  blockers: z.array(z.string().min(1)),
  warnings: z.array(z.string().min(1)),
});
export type EmissionWorkspaceSummary = z.infer<typeof emissionWorkspaceSummarySchema>;

export const emissionWorkspaceScenarioIdSchema = z.enum([
  "baseline-ready",
  "team-attention",
  "release-blocked",
]);
export type EmissionWorkspaceScenarioId = z.infer<typeof emissionWorkspaceScenarioIdSchema>;

export const emissionWorkspaceScenarioSchema = z.object({
  id: emissionWorkspaceScenarioIdSchema,
  label: z.string().min(1),
  description: z.string().min(1),
  summary: emissionWorkspaceSummarySchema,
  modules: z.array(emissionWorkspaceModuleSchema).min(1),
  references: emissionWorkspaceScenarioRefsSchema,
  nextActions: z.array(z.string().min(1)).min(1),
});
export type EmissionWorkspaceScenario = z.infer<typeof emissionWorkspaceScenarioSchema>;

export const emissionWorkspaceCatalogSchema = z.object({
  selectedScenarioId: emissionWorkspaceScenarioIdSchema,
  scenarios: z.array(emissionWorkspaceScenarioSchema).min(1),
});
export type EmissionWorkspaceCatalog = z.infer<typeof emissionWorkspaceCatalogSchema>;
