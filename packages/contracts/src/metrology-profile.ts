import { z } from "zod";

export const standardQuantityKindSchema = z.enum([
  "mass",
  "temperature",
  "humidity",
  "pressure",
  "auxiliary",
]);
export type StandardQuantityKind = z.infer<typeof standardQuantityKindSchema>;

export const standardTraceabilitySourceSchema = z.enum([
  "rbc",
  "internal",
  "third_party",
  "untraced",
]);
export type StandardTraceabilitySource = z.infer<typeof standardTraceabilitySourceSchema>;

export const standardMetrologyProfileSchema = z.object({
  quantityKind: standardQuantityKindSchema,
  measurementUnit: z.string().min(1),
  traceabilitySource: standardTraceabilitySourceSchema,
  certificateIssuer: z.string().min(1),
  expandedUncertaintyValue: z.number().nonnegative(),
  coverageFactorK: z.number().positive(),
  conventionalMassErrorValue: z.number().optional(),
  degreesOfFreedom: z.number().positive().optional(),
  densityKgPerM3: z.number().positive().optional(),
  driftLimitValue: z.number().nonnegative().optional(),
});
export type StandardMetrologyProfile = z.infer<typeof standardMetrologyProfileSchema>;

export const equipmentInstrumentKindSchema = z.enum([
  "nawi",
  "analytical_balance",
  "precision_balance",
  "platform_scale",
  "vehicle_scale",
]);
export type EquipmentInstrumentKind = z.infer<typeof equipmentInstrumentKindSchema>;

export const equipmentNormativeClassSchema = z.enum(["i", "ii", "iii", "iiii"]);
export type EquipmentNormativeClass = z.infer<typeof equipmentNormativeClassSchema>;

export const equipmentMetrologyProfileSchema = z.object({
  instrumentKind: equipmentInstrumentKindSchema,
  measurementUnit: z.string().min(1),
  maximumCapacityValue: z.number().positive(),
  readabilityValue: z.number().positive(),
  verificationScaleIntervalValue: z.number().positive(),
  normativeClass: equipmentNormativeClassSchema.optional(),
  minimumCapacityValue: z.number().nonnegative().optional(),
  minimumLoadValue: z.number().nonnegative().optional(),
  effectiveRangeMinValue: z.number().nonnegative().optional(),
  effectiveRangeMaxValue: z.number().positive().optional(),
});
export type EquipmentMetrologyProfile = z.infer<typeof equipmentMetrologyProfileSchema>;
