import { z } from "zod";

import { registryOperationalStatusSchema } from "./registry-shared.js";

export const managementReviewScenarioIdSchema = z.enum([
  "ordinary-ready",
  "agenda-attention",
  "extraordinary-response",
]);
export type ManagementReviewScenarioId = z.infer<typeof managementReviewScenarioIdSchema>;

export const managementReviewMeetingItemSchema = z.object({
  meetingId: z.string().min(1),
  dateLabel: z.string().min(1),
  titleLabel: z.string().min(1),
  outcomeLabel: z.string().min(1),
  status: registryOperationalStatusSchema,
});
export type ManagementReviewMeetingItem = z.infer<typeof managementReviewMeetingItemSchema>;

export const managementReviewAgendaItemSchema = z.object({
  key: z.string().min(1),
  label: z.string().min(1),
  status: registryOperationalStatusSchema,
});
export type ManagementReviewAgendaItem = z.infer<typeof managementReviewAgendaItemSchema>;

export const managementReviewAutomaticInputSchema = z.object({
  key: z.string().min(1),
  label: z.string().min(1),
  valueLabel: z.string().min(1),
  sourceLabel: z.string().min(1),
  status: registryOperationalStatusSchema,
  href: z.string().min(1).optional(),
});
export type ManagementReviewAutomaticInput = z.infer<typeof managementReviewAutomaticInputSchema>;

export const managementReviewDecisionItemSchema = z.object({
  key: z.string().min(1),
  label: z.string().min(1),
  ownerLabel: z.string().min(1),
  dueDateLabel: z.string().min(1),
  status: registryOperationalStatusSchema,
});
export type ManagementReviewDecisionItem = z.infer<typeof managementReviewDecisionItemSchema>;

export const managementReviewDetailSchema = z.object({
  meetingId: z.string().min(1),
  title: z.string().min(1),
  status: registryOperationalStatusSchema,
  noticeLabel: z.string().min(1),
  nextMeetingLabel: z.string().min(1),
  chairLabel: z.string().min(1),
  attendeesLabel: z.string().min(1),
  periodLabel: z.string().min(1),
  ataLabel: z.string().min(1),
  evidenceLabel: z.string().min(1),
  agendaItems: z.array(managementReviewAgendaItemSchema).min(1),
  automaticInputs: z.array(managementReviewAutomaticInputSchema).min(1),
  decisions: z.array(managementReviewDecisionItemSchema).min(1),
  blockers: z.array(z.string().min(1)),
  warnings: z.array(z.string().min(1)),
});
export type ManagementReviewDetail = z.infer<typeof managementReviewDetailSchema>;

export const managementReviewSummarySchema = z.object({
  status: registryOperationalStatusSchema,
  headline: z.string().min(1),
  nextMeetingLabel: z.string().min(1),
  agendaCount: z.number().int().nonnegative(),
  automaticInputCount: z.number().int().nonnegative(),
  openDecisionCount: z.number().int().nonnegative(),
  recommendedAction: z.string().min(1),
  blockers: z.array(z.string().min(1)),
  warnings: z.array(z.string().min(1)),
});
export type ManagementReviewSummary = z.infer<typeof managementReviewSummarySchema>;

export const managementReviewScenarioSchema = z.object({
  id: managementReviewScenarioIdSchema,
  label: z.string().min(1),
  description: z.string().min(1),
  summary: managementReviewSummarySchema,
  selectedMeetingId: z.string().min(1),
  meetings: z.array(managementReviewMeetingItemSchema).min(1),
  detail: managementReviewDetailSchema,
});
export type ManagementReviewScenario = z.infer<typeof managementReviewScenarioSchema>;

export const managementReviewCatalogSchema = z.object({
  selectedScenarioId: managementReviewScenarioIdSchema,
  scenarios: z.array(managementReviewScenarioSchema).min(1),
});
export type ManagementReviewCatalog = z.infer<typeof managementReviewCatalogSchema>;
