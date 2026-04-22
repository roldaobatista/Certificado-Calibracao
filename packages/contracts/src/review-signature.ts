import { z } from "zod";

export const membershipRoleSchema = z.enum([
  "admin",
  "quality_manager",
  "signatory",
  "technical_reviewer",
  "technician",
  "auditor_readonly",
  "external_client",
]);
export type MembershipRole = z.infer<typeof membershipRoleSchema>;

export const reviewSignatureStageSchema = z.enum(["in_review", "approved", "emitted"]);
export type ReviewSignatureStage = z.infer<typeof reviewSignatureStageSchema>;

export const reviewSignatureStatusSchema = z.enum(["ready", "blocked"]);
export type ReviewSignatureStatus = z.infer<typeof reviewSignatureStatusSchema>;

export const reviewSignatureStepStatusSchema = z.enum(["pending", "ready", "blocked", "complete"]);
export type ReviewSignatureStepStatus = z.infer<typeof reviewSignatureStepStatusSchema>;

export const reviewSignatureActionSchema = z.enum([
  "review_certificate",
  "reject_to_executor",
  "sign_certificate",
  "archive_workflow",
]);
export type ReviewSignatureAction = z.infer<typeof reviewSignatureActionSchema>;

export const reviewSignatureCheckIdSchema = z.enum([
  "executor_membership",
  "reviewer_membership",
  "reviewer_segregation",
  "reviewer_competence",
  "signatory_membership",
  "signatory_segregation",
  "signatory_competence",
  "signatory_mfa",
]);
export type ReviewSignatureCheckId = z.infer<typeof reviewSignatureCheckIdSchema>;

export const workflowActorSchema = z.object({
  userId: z.string().min(1),
  displayName: z.string().min(1),
  roles: z.array(membershipRoleSchema).min(1),
  mfaEnabled: z.boolean(),
  pendingAssignments: z.number().int().nonnegative(),
});
export type WorkflowActor = z.infer<typeof workflowActorSchema>;

export const workflowSuggestionSchema = z.object({
  userId: z.string().min(1),
  displayName: z.string().min(1),
  rationale: z.string().min(1),
});
export type WorkflowSuggestion = z.infer<typeof workflowSuggestionSchema>;

export const reviewSignatureStepSchema = z.object({
  title: z.string().min(1),
  status: reviewSignatureStepStatusSchema,
  actorLabel: z.string().min(1),
  detail: z.string().min(1),
});
export type ReviewSignatureStep = z.infer<typeof reviewSignatureStepSchema>;

export const reviewSignatureCheckSchema = z.object({
  id: reviewSignatureCheckIdSchema,
  title: z.string().min(1),
  status: z.enum(["passed", "failed"]),
  detail: z.string().min(1),
});
export type ReviewSignatureCheck = z.infer<typeof reviewSignatureCheckSchema>;

export const reviewSignatureAssignmentsSchema = z.object({
  executor: workflowActorSchema,
  reviewer: workflowActorSchema.optional(),
  signatory: workflowActorSchema.optional(),
});
export type ReviewSignatureAssignments = z.infer<typeof reviewSignatureAssignmentsSchema>;

export const reviewSignatureSuggestionsSchema = z.object({
  reviewer: workflowSuggestionSchema.optional(),
  signatory: workflowSuggestionSchema.optional(),
});
export type ReviewSignatureSuggestions = z.infer<typeof reviewSignatureSuggestionsSchema>;

export const reviewSignatureWorkflowResultSchema = z.object({
  status: reviewSignatureStatusSchema,
  stage: reviewSignatureStageSchema,
  summary: z.string().min(1),
  blockers: z.array(z.string().min(1)),
  warnings: z.array(z.string().min(1)),
  allowedActions: z.array(reviewSignatureActionSchema),
  reviewStep: reviewSignatureStepSchema,
  signatureStep: reviewSignatureStepSchema,
  checks: z.array(reviewSignatureCheckSchema),
  assignments: reviewSignatureAssignmentsSchema,
  suggestions: reviewSignatureSuggestionsSchema,
});
export type ReviewSignatureWorkflowResult = z.infer<typeof reviewSignatureWorkflowResultSchema>;

export const reviewSignatureScenarioIdSchema = z.enum([
  "segregated-ready",
  "reviewer-conflict",
  "signatory-mfa-blocked",
]);
export type ReviewSignatureScenarioId = z.infer<typeof reviewSignatureScenarioIdSchema>;

export const reviewSignatureScenarioSchema = z.object({
  id: reviewSignatureScenarioIdSchema,
  label: z.string().min(1),
  description: z.string().min(1),
  result: reviewSignatureWorkflowResultSchema,
});
export type ReviewSignatureScenario = z.infer<typeof reviewSignatureScenarioSchema>;

export const reviewSignatureCatalogSchema = z.object({
  selectedScenarioId: reviewSignatureScenarioIdSchema,
  scenarios: z.array(reviewSignatureScenarioSchema).min(1),
});
export type ReviewSignatureCatalog = z.infer<typeof reviewSignatureCatalogSchema>;
