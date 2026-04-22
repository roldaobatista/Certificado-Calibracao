import { z } from "zod";

import { emissionDryRunScenarioIdSchema } from "./emission-dry-run.js";
import { emissionWorkspaceScenarioIdSchema } from "./emission-workspace.js";
import { registryOperationalStatusSchema } from "./registry-shared.js";
import { serviceOrderReviewScenarioIdSchema } from "./service-order-review.js";

export const procedureRegistryScenarioIdSchema = z.enum([
  "operational-ready",
  "revision-attention",
  "obsolete-visible",
]);
export type ProcedureRegistryScenarioId = z.infer<typeof procedureRegistryScenarioIdSchema>;

export const procedureListItemSchema = z.object({
  procedureId: z.string().min(1),
  code: z.string().min(1),
  title: z.string().min(1),
  typeLabel: z.string().min(1),
  revisionLabel: z.string().min(1),
  effectiveSinceLabel: z.string().min(1),
  effectiveUntilLabel: z.string().min(1).optional(),
  lifecycleLabel: z.string().min(1),
  usageLabel: z.string().min(1),
  status: registryOperationalStatusSchema,
});
export type ProcedureListItem = z.infer<typeof procedureListItemSchema>;

export const procedureDetailLinksSchema = z.object({
  workspaceScenarioId: emissionWorkspaceScenarioIdSchema.optional(),
  serviceOrderScenarioId: serviceOrderReviewScenarioIdSchema.optional(),
  reviewItemId: z.string().min(1).optional(),
  dryRunScenarioId: emissionDryRunScenarioIdSchema.optional(),
});
export type ProcedureDetailLinks = z.infer<typeof procedureDetailLinksSchema>;

export const procedureDetailSchema = z.object({
  procedureId: z.string().min(1),
  title: z.string().min(1),
  status: registryOperationalStatusSchema,
  noticeLabel: z.string().min(1),
  scopeLabel: z.string().min(1),
  environmentRangeLabel: z.string().min(1),
  curvePolicyLabel: z.string().min(1),
  standardsPolicyLabel: z.string().min(1),
  approvalLabel: z.string().min(1),
  relatedDocuments: z.array(z.string().min(1)).min(1),
  blockers: z.array(z.string().min(1)),
  warnings: z.array(z.string().min(1)),
  links: procedureDetailLinksSchema,
});
export type ProcedureDetail = z.infer<typeof procedureDetailSchema>;

export const procedureRegistrySummarySchema = z.object({
  status: registryOperationalStatusSchema,
  headline: z.string().min(1),
  activeCount: z.number().int().nonnegative(),
  attentionCount: z.number().int().nonnegative(),
  obsoleteCount: z.number().int().nonnegative(),
  recommendedAction: z.string().min(1),
  blockers: z.array(z.string().min(1)),
  warnings: z.array(z.string().min(1)),
});
export type ProcedureRegistrySummary = z.infer<typeof procedureRegistrySummarySchema>;

export const procedureRegistryScenarioSchema = z.object({
  id: procedureRegistryScenarioIdSchema,
  label: z.string().min(1),
  description: z.string().min(1),
  summary: procedureRegistrySummarySchema,
  selectedProcedureId: z.string().min(1),
  items: z.array(procedureListItemSchema).min(1),
  detail: procedureDetailSchema,
});
export type ProcedureRegistryScenario = z.infer<typeof procedureRegistryScenarioSchema>;

export const procedureRegistryCatalogSchema = z.object({
  selectedScenarioId: procedureRegistryScenarioIdSchema,
  scenarios: z.array(procedureRegistryScenarioSchema).min(1),
});
export type ProcedureRegistryCatalog = z.infer<typeof procedureRegistryCatalogSchema>;
