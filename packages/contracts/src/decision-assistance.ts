import { z } from "zod";

export const indicativeDecisionModeSchema = z.enum([
  "simple_tolerance",
  "guard_band",
]);
export type IndicativeDecisionMode = z.infer<typeof indicativeDecisionModeSchema>;

export const indicativeDecisionVerdictSchema = z.enum([
  "conforming",
  "non_conforming",
  "inconclusive",
]);
export type IndicativeDecisionVerdict = z.infer<typeof indicativeDecisionVerdictSchema>;

export const indicativeDecisionSnapshotSchema = z.object({
  mode: indicativeDecisionModeSchema.optional(),
  verdict: indicativeDecisionVerdictSchema.optional(),
  readyForIndicativeUse: z.boolean(),
  summaryLabel: z.string().min(1),
  pointCount: z.number().int().nonnegative(),
  unit: z.string().min(1).optional(),
  expandedUncertaintyValue: z.number().finite().optional(),
  recordedAtUtc: z.string().min(1),
});
export type IndicativeDecisionSnapshot = z.infer<typeof indicativeDecisionSnapshotSchema>;

export const decisionAssistanceAlignmentSchema = z.enum([
  "pending",
  "aligned",
  "divergent",
]);
export type DecisionAssistanceAlignment = z.infer<typeof decisionAssistanceAlignmentSchema>;

export const decisionAssistanceSummarySchema = z.object({
  indicativeDecision: indicativeDecisionSnapshotSchema.optional(),
  officialDecisionLabel: z.string().min(1).optional(),
  officialDecisionDivergesFromIndicative: z.boolean(),
  alignment: decisionAssistanceAlignmentSchema,
  alignmentLabel: z.string().min(1),
  justificationRequired: z.boolean(),
  officialDecisionJustification: z.string().min(1).optional(),
});
export type DecisionAssistanceSummary = z.infer<typeof decisionAssistanceSummarySchema>;
