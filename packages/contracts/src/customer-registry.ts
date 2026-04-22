import { z } from "zod";

import { emissionDryRunScenarioIdSchema } from "./emission-dry-run.js";
import { registryOperationalStatusSchema, registryScenarioIdSchema } from "./registry-shared.js";
import { serviceOrderReviewScenarioIdSchema } from "./service-order-review.js";

export const customerListItemSchema = z.object({
  customerId: z.string().min(1),
  legalName: z.string().min(1),
  tradeName: z.string().min(1),
  documentLabel: z.string().min(1),
  segmentLabel: z.string().min(1),
  equipmentCount: z.number().int().nonnegative(),
  certificatesThisMonth: z.number().int().nonnegative(),
  nextDueLabel: z.string().min(1),
  status: registryOperationalStatusSchema,
});
export type CustomerListItem = z.infer<typeof customerListItemSchema>;

export const customerDetailTabKeySchema = z.enum([
  "data",
  "contacts",
  "addresses",
  "equipment",
  "certificates",
  "attachments",
  "history",
]);
export type CustomerDetailTabKey = z.infer<typeof customerDetailTabKeySchema>;

export const customerDetailTabSchema = z.object({
  key: customerDetailTabKeySchema,
  label: z.string().min(1),
  countLabel: z.string().min(1).optional(),
});
export type CustomerDetailTab = z.infer<typeof customerDetailTabSchema>;

export const customerContactSchema = z.object({
  name: z.string().min(1),
  roleLabel: z.string().min(1),
  email: z.string().min(1),
  phoneLabel: z.string().min(1).optional(),
  primary: z.boolean(),
});
export type CustomerContact = z.infer<typeof customerContactSchema>;

export const customerAddressSchema = z.object({
  label: z.string().min(1),
  line1: z.string().min(1),
  cityStateLabel: z.string().min(1),
  postalCodeLabel: z.string().min(1),
  countryLabel: z.string().min(1),
  conditionsLabel: z.string().min(1).optional(),
});
export type CustomerAddress = z.infer<typeof customerAddressSchema>;

export const customerEquipmentHighlightSchema = z.object({
  equipmentId: z.string().min(1),
  code: z.string().min(1),
  tagCode: z.string().min(1),
  typeModelLabel: z.string().min(1),
  nextDueLabel: z.string().min(1),
  status: registryOperationalStatusSchema,
});
export type CustomerEquipmentHighlight = z.infer<typeof customerEquipmentHighlightSchema>;

export const customerCertificateHighlightSchema = z.object({
  certificateNumber: z.string().min(1),
  workOrderNumber: z.string().min(1),
  issuedAtLabel: z.string().min(1),
  revisionLabel: z.string().min(1),
  statusLabel: z.string().min(1),
});
export type CustomerCertificateHighlight = z.infer<typeof customerCertificateHighlightSchema>;

export const customerAttachmentSchema = z.object({
  label: z.string().min(1),
  statusLabel: z.string().min(1),
});
export type CustomerAttachment = z.infer<typeof customerAttachmentSchema>;

export const customerHistoryItemSchema = z.object({
  label: z.string().min(1),
  timestampLabel: z.string().min(1),
});
export type CustomerHistoryItem = z.infer<typeof customerHistoryItemSchema>;

export const customerDetailLinksSchema = z.object({
  equipmentScenarioId: registryScenarioIdSchema,
  selectedEquipmentId: z.string().min(1).optional(),
  serviceOrderScenarioId: serviceOrderReviewScenarioIdSchema.optional(),
  reviewItemId: z.string().min(1).optional(),
  dryRunScenarioId: emissionDryRunScenarioIdSchema.optional(),
});
export type CustomerDetailLinks = z.infer<typeof customerDetailLinksSchema>;

export const customerDetailSchema = z.object({
  customerId: z.string().min(1),
  title: z.string().min(1),
  status: registryOperationalStatusSchema,
  statusLine: z.string().min(1),
  accountOwnerLabel: z.string().min(1),
  contractLabel: z.string().min(1),
  specialConditionsLabel: z.string().min(1),
  tabs: z.array(customerDetailTabSchema).min(1),
  contacts: z.array(customerContactSchema).min(1),
  addresses: z.array(customerAddressSchema).min(1),
  equipmentHighlights: z.array(customerEquipmentHighlightSchema).min(1),
  certificateHighlights: z.array(customerCertificateHighlightSchema).min(1),
  attachments: z.array(customerAttachmentSchema).min(1),
  history: z.array(customerHistoryItemSchema).min(1),
  blockers: z.array(z.string().min(1)),
  warnings: z.array(z.string().min(1)),
  links: customerDetailLinksSchema,
});
export type CustomerDetail = z.infer<typeof customerDetailSchema>;

export const customerRegistrySummarySchema = z.object({
  status: registryOperationalStatusSchema,
  headline: z.string().min(1),
  activeCustomers: z.number().int().nonnegative(),
  attentionCustomers: z.number().int().nonnegative(),
  blockedCustomers: z.number().int().nonnegative(),
  totalEquipment: z.number().int().nonnegative(),
  certificatesThisMonth: z.number().int().nonnegative(),
  dueSoonCount: z.number().int().nonnegative(),
  recommendedAction: z.string().min(1),
  blockers: z.array(z.string().min(1)),
  warnings: z.array(z.string().min(1)),
});
export type CustomerRegistrySummary = z.infer<typeof customerRegistrySummarySchema>;

export const customerRegistryScenarioSchema = z.object({
  id: registryScenarioIdSchema,
  label: z.string().min(1),
  description: z.string().min(1),
  summary: customerRegistrySummarySchema,
  selectedCustomerId: z.string().min(1),
  customers: z.array(customerListItemSchema).min(1),
  detail: customerDetailSchema,
});
export type CustomerRegistryScenario = z.infer<typeof customerRegistryScenarioSchema>;

export const customerRegistryCatalogSchema = z.object({
  selectedScenarioId: registryScenarioIdSchema,
  scenarios: z.array(customerRegistryScenarioSchema).min(1),
});
export type CustomerRegistryCatalog = z.infer<typeof customerRegistryCatalogSchema>;
